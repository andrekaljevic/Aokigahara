#!/usr/bin/env python3
"""Photo-derived PBR material packs for the Aokigahara reconstruction.

Every material is cut from ONE region of ONE photograph supplied by the repository
owner (construction_inputs/uhd_photos/), delit, made toroidally seamless and turned
into a PBR set at a 4096-px master resolution, then downsampled to 2k and 1k.

Honesty statement (also written into the manifest):
  * albedo comes from the photograph after removing the low-frequency lighting;
  * height, normal, roughness and ambient occlusion are single-image HEURISTIC
    estimates from luminance (not photogrammetry, not measured);
  * physical scale is estimated from objects in the frame, not measured;
  * the photographs arrived at 2000 x 983 px, so the 4k and 2k tiers are
    interpolated above the native resolution recorded per material.

Deterministic: no randomness, no timestamps. Only numpy, pillow and scipy.

Usage (from the repository root):
  python3 construction_code_v3/extract_uhd_materials.py
  python3 construction_code_v3/extract_uhd_materials.py --spec construction_code_v3/uhd_extraction_spec.json --only moss_uhd
"""
import argparse, hashlib, json, os, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'construction_code_v2'))
from gen_textures import height_to_normal  # noqa: E402  (module main is guarded)

Image.MAX_IMAGE_PIXELS = None
PHOTOS = ROOT / 'construction_inputs/uhd_photos'
TIERS = {'4k': ROOT / 'asset_packs/materials_uhd_4k', '2k': ROOT / 'asset_packs/materials_uhd_2k', '1k': ROOT / 'viewer/assets/materials_uhd'}
PREVIEW_DIR = ROOT / 'renders/assets'
MASTER_FACTOR = 4                      # master = 1k tile size x 4
STAMP = '2026-09-22'

SLOT_PARAMS = {  # normal strength at 1k, roughness base
    'moss': (12, 0.92), 'root': (12, 0.90), 'rock': (22, 0.80), 'litter': (10, 0.88), 'trail': (8, 0.90),
    'understorey': (12, 0.75), 'bark': (14, 0.86), 'deadwood': (12, 0.84),
}
RUNTIME_SLOT_SCALE_M = {'moss': 1.0, 'rock': 1.5, 'litter': 0.8, 'trail': 1.0}
COUNTERPART = {  # exposure targets: (file relative to repo root, multiplier)
    'moss': ('viewer/assets/materials_v2/moss_diff_1k.jpg', 1.0), 'root': ('viewer/assets/materials_v2/moss_diff_1k.jpg', 1.0),
    'understorey': ('viewer/assets/materials_v2/moss_diff_1k.jpg', 1.0), 'rock': ('viewer/assets/materials_v2/basalt_diff_1k.jpg', 1.0),
    'litter': ('viewer/assets/materials_v2/litter_diff_1k.jpg', 1.0), 'deadwood': ('viewer/assets/materials_v2/litter_diff_1k.jpg', 0.9),
    'trail': ('viewer/assets/materials_v2/trail_diff_1k.jpg', 1.0), 'bark': ('viewer/assets/materials/japanese_cedar_bark_diff_1k.jpg', 0.8),
}

# ----------------------------------------------------------------------------- colour helpers
def srgb_to_lin(x):
    x = x.astype(np.float32) / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)

def lin_to_srgb8(x):
    x = np.clip(x, 0, 1)
    s = np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)
    return np.clip(np.round(s * 255), 0, 255).astype(np.uint8)

def luma(rgb):
    return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]).astype(np.float32)

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def gauss(a, sigma, mode='wrap'):
    return ndimage.gaussian_filter(a, sigma, mode=mode, truncate=3.0).astype(np.float32)

def resize_f32(a, size):
    """Lanczos resize of a float32 (H,W) or (H,W,C) array to (w,h)."""
    if a.ndim == 2:
        return np.asarray(Image.fromarray(a, mode='F').resize(size, Image.LANCZOS), dtype=np.float32)
    return np.stack([resize_f32(a[..., c], size) for c in range(a.shape[-1])], -1)

# ----------------------------------------------------------------------------- 1. crop (with rotation)
def crop_region(img_lin, rect, rotation_deg, core=None):
    """rect = [x0,y0,x1,y1] in photo pixels. If rotation_deg != 0 the photo is rotated about the rect
    centre (positive = counter-clockwise as displayed) and the central `core` [w,h] of the rotated
    rect is returned (core defaults to the rect size)."""
    x0, y0, x1, y1 = rect
    if not rotation_deg:
        return img_lin[y0:y1, x0:x1]
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    w, h = x1 - x0, y1 - y0
    r = int(np.ceil(np.hypot(w, h) / 2)) + 4
    H, W = img_lin.shape[:2]
    ya, yb, xa, xb = int(cy) - r, int(cy) + r, int(cx) - r, int(cx) + r
    pad = ((max(0, -ya), max(0, yb - H)), (max(0, -xa), max(0, xb - W)), (0, 0))
    sub = img_lin[max(0, ya):min(H, yb), max(0, xa):min(W, xb)]
    sub = np.pad(sub, pad, mode='reflect')
    rot = ndimage.rotate(sub, rotation_deg, reshape=False, order=1, mode='reflect').astype(np.float32)
    cw, ch = core or (w, h)
    c = rot.shape[0] // 2
    return rot[c - ch // 2:c - ch // 2 + ch, c - cw // 2:c - cw // 2 + cw]

# ----------------------------------------------------------------------------- 2-3. mask + delight + inpaint
def build_mask(crop_lin):
    """True = usable. Excludes clipped highlights (sun dapples) and pixels that are black relative
    to the crop (deep clefts), never ordinary shadow: these photographs are dark overall."""
    srgb = lin_to_srgb8(crop_lin)
    clipped = (srgb.max(-1) >= 245)
    clipped = ndimage.binary_dilation(clipped, iterations=6)
    Y = luma(crop_lin)
    black = Y < min(0.0015, 0.03 * float(np.median(Y)))
    black = ndimage.binary_dilation(black, iterations=1)
    return ~(clipped | black)

def normalised_blur(a, m, sigma):
    num = gauss(a * m, sigma, mode='reflect')
    den = gauss(m.astype(np.float32), sigma, mode='reflect')
    return num / np.maximum(den, 1e-4)

def delight(crop_lin, mask, target_mean, chroma=1.0):
    h, w = mask.shape
    Y = luma(crop_lin)
    m = mask.astype(np.float32)
    illum = normalised_blur(Y, m, 0.12 * min(h, w))
    gain = target_mean / np.maximum(illum, 1e-5)
    g_med = float(np.median(gain[mask])) if mask.any() else float(np.median(gain))
    gain = np.clip(gain, g_med / 2.5, g_med * 2.5)      # bound the lift relative to the crop's own exposure
    alb = crop_lin * gain[..., None]
    # pixels lifted well above the median gain are noise-dominated shadow: pull their chroma back
    # towards grey in proportion, and apply the material's chroma factor (phone HDR frames oversaturate)
    Yl = luma(alb)[..., None]
    chroma_scale = np.sqrt(np.clip(g_med / np.maximum(gain, 1e-6), 0.0, 1.0))[..., None] * chroma
    alb = Yl + (alb - Yl) * chroma_scale
    # fill excluded pixels from their surroundings (normalised convolution, three scales)
    filled = alb.copy()
    hole = ~mask
    if hole.any():
        for s in (3, 9, 27):
            est = np.stack([normalised_blur(alb[..., c], m, s) for c in range(3)], -1)
            filled[hole] = est[hole]
    # bring the overall mean exactly onto the target (gain clamps can shift it)
    filled *= target_mean / max(float(luma(filled).mean()), 1e-4)
    return np.clip(filled, 0, 1).astype(np.float32)

# ----------------------------------------------------------------------------- 4. seamless: periodic component + toroidal min-cut quilting
def periodic_component(u):
    """Moisan (2011) periodic-plus-smooth decomposition; returns the periodic part p."""
    u = u.astype(np.float32)
    H, W = u.shape
    v = np.zeros_like(u)
    d = u[0] - u[-1]; v[0] += d; v[-1] -= d
    d = u[:, 0] - u[:, -1]; v[:, 0] += d; v[:, -1] -= d
    fy = np.fft.fftfreq(H)[:, None]; fx = np.fft.fftfreq(W)[None, :]
    denom = (2 * np.cos(2 * np.pi * fy) + 2 * np.cos(2 * np.pi * fx) - 4).astype(np.float32)
    denom[0, 0] = 1.0
    vf = np.fft.fft2(v) / denom
    vf[0, 0] = 0.0
    s = np.real(np.fft.ifft2(vf)).astype(np.float32)
    return u - s

def min_cut_vertical(cost):
    """Dynamic-programming vertical seam through a (rows, k) cost band. Returns column index per row."""
    R, K = cost.shape
    D = cost.copy(); back = np.zeros((R, K), dtype=np.int8)
    for i in range(1, R):
        prev = D[i - 1]
        left = np.concatenate(([np.inf], prev[:-1])); right = np.concatenate((prev[1:], [np.inf]))
        stack = np.stack([left, prev, right])
        arg = stack.argmin(0)
        D[i] = cost[i] + stack[arg, np.arange(K)]
        back[i] = arg - 1
    seam = np.zeros(R, dtype=np.int64); seam[-1] = int(D[-1].argmin())
    for i in range(R - 1, 0, -1):
        seam[i - 1] = seam[i] + back[i, seam[i]]
    return seam

def paste_min_cut(base, patch, y0, x0, band):
    """Paste `patch` onto `base` at (y0,x0) with minimum-error boundary cuts inside a band of `band`
    pixels along each patch edge. Returns the composite and the boolean mask of patch pixels used."""
    ph, pw = patch.shape[:2]
    region = base[y0:y0 + ph, x0:x0 + pw]
    diff = ((region - patch) ** 2).sum(-1).astype(np.float32)
    rows = np.arange(ph)[:, None]; cols = np.arange(pw)[None, :]
    lseam = min_cut_vertical(diff[:, :band])                 # patch used right of it
    rseam = min_cut_vertical(diff[:, pw - band:]) + pw - band
    tseam = min_cut_vertical(diff[:band, :].T)               # patch used below it
    bseam = min_cut_vertical(diff[ph - band:, :].T) + ph - band
    use = (cols > lseam[:, None]) & (cols < rseam[:, None]) & (rows > tseam[None, :]) & (rows < bseam[None, :])
    # feather the cut over a few pixels so the residual mismatch is not a hard edge
    m = ndimage.gaussian_filter(use.astype(np.float32), 2.0, mode='constant')[..., None]
    out = base.copy()
    out[y0:y0 + ph, x0:x0 + pw] = region * (1 - m) + patch * m
    return out, use

def make_seamless(img, band):
    """img: (H,W,C) float32. Returns a toroidally seamless version of the same size."""
    H, W = img.shape[:2]
    p = np.stack([periodic_component(img[..., c]) for c in range(img.shape[-1])], -1)
    b = band
    # pass 1: interior patch of the (seamless-inside) periodic image over its half-rolled copy
    B = np.roll(p, (H // 2, W // 2), axis=(0, 1))
    t, _ = paste_min_cut(B, p[b:H - b, b:W - b], b, b, band)
    # the only seams left are four stubs of length <= b at the tile edges (the old cross where it
    # meets the border). Bring each pair to the centre and cover it with a seam-free patch.
    S = min(2 * b + 96, H - 2 * b, W - 2 * b)
    for axis in (0, 1):
        shift = (H // 2, 0) if axis == 0 else (0, W // 2)
        t = np.roll(t, shift, axis=(0, 1))
        cy, cx = H // 2, W // 2
        # a seam-free interior source patch, offset a quarter tile away from the stubs, kept inside the tile
        sy = int(np.clip(H // 4 - S // 2, 0, H - S)); sx = int(np.clip(W // 4 - S // 2, 0, W - S))
        src = t[sy:sy + S, sx:sx + S]
        t, _ = paste_min_cut(t, src, cy - S // 2, cx - S // 2, max(4, min(band // 2, S // 4)))
        t = np.roll(t, (-shift[0], -shift[1]), axis=(0, 1))
    return t.astype(np.float32)

# ----------------------------------------------------------------------------- 5-8. derived maps
def normalise01(a, lo=0.5, hi=99.5):
    a = a.astype(np.float32)
    l, h = np.percentile(a, [lo, hi])
    return np.clip((a - l) / max(h - l, 1e-6), 0, 1).astype(np.float32)

def zscore(a):
    return ((a - a.mean()) / max(float(a.std()), 1e-6)).astype(np.float32)

def derive_maps(alb, slot, height_mode, k):
    """alb: seamless linear albedo (H,W,3) at master resolution; k = master / 1k scale factor."""
    Y = luma(alb)
    hp = 0.5 * zscore(Y - gauss(Y, 2 * k)) + 0.3 * zscore(Y - gauss(Y, 6 * k)) + 0.2 * zscore(Y - gauss(Y, 18 * k))
    if slot in ('moss', 'understorey', 'root'):
        chroma = alb[..., 1] - 0.5 * (alb[..., 0] + alb[..., 2])
        hp = hp + 0.25 * zscore(chroma - gauss(chroma, 18 * k))
    if height_mode == 'dark_is_high':
        hp = -hp
    height = normalise01(hp)
    strength, rbase = SLOT_PARAMS[slot]
    normal = height_to_normal(height * strength * k, 1.0)          # k: gradient per pixel is k x smaller at master
    hp_s = zscore(Y - gauss(Y, 4 * k))
    rough = np.clip(rbase - 0.10 * np.clip(hp_s, -1, 1) * 0.5 + 0.05 * (height - 0.5), 0.45, 1.0).astype(np.float32)
    ao = np.clip(1.0 - 1.2 * np.clip(gauss(height, 14 * k) - height, 0, 1), 0.3, 1.0).astype(np.float32)
    return height, normal, rough, ao

# ----------------------------------------------------------------------------- metrics
def seam_score(a):
    a = a.astype(np.float32)
    if a.ndim == 2:
        a = a[..., None]
    edge = np.abs(a[0] - a[-1]).mean() + np.abs(a[:, 0] - a[:, -1]).mean()
    interior = np.abs(np.diff(a, axis=0)).mean() + np.abs(np.diff(a, axis=1)).mean()
    return float(edge / max(interior, 1e-6))

def tier_metrics(files):
    rgb8 = np.asarray(Image.open(files['diff']).convert('RGB'))
    lin = srgb_to_lin(rgb8); Y = luma(lin)
    m = {'seam_diff': round(seam_score(rgb8), 3), 'mean_linear_luma': round(float(Y.mean()), 4),
         'residual_clipped_fraction': round(float((Y > 0.9).mean()), 5),
         'lowfreq_gradient': round(float(ndimage.uniform_filter(Y, 64, mode='wrap').std() / max(Y.mean(), 1e-6)), 4)}
    for k in ('nor_gl', 'height', 'rough', 'ao'):
        arr = np.asarray(Image.open(files[k]).convert('RGB' if k == 'nor_gl' else 'L'))
        m[f'seam_{k}'] = round(seam_score(arr), 3)
    n = np.asarray(Image.open(files['nor_gl']).convert('RGB')).astype(np.float32) / 255 * 2 - 1
    m['normal_mean'] = [round(float(v), 4) for v in n.reshape(-1, 3).mean(0)]
    return m

# ----------------------------------------------------------------------------- output
def save_jpg(arr8, path, quality, subsampling=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr8).save(path, quality=quality, subsampling=subsampling)

def write_tiers(mid, alb_lin, height, normal8, rough, ao, master_size):
    """Write 4k masters and Lanczos-downsampled 2k / 1k tiers. Returns {tier: {map: path}}."""
    out = {}
    nvec = normal8.astype(np.float32) / 255 * 2 - 1
    tiers = (('4k', 1), ('2k', 2), ('1k', 4)) if MASTER_FACTOR == 4 else (('1k', 1),)
    for tier, div in tiers:
        size = (master_size[0] // div, master_size[1] // div)
        if div == 1:
            a, h, nv, r, o = alb_lin, height, nvec, rough, ao
        else:
            a = resize_f32(alb_lin, size); h = resize_f32(height, size); r = resize_f32(rough, size); o = resize_f32(ao, size)
            nv = resize_f32(nvec, size); nv /= np.maximum(np.linalg.norm(nv, axis=-1, keepdims=True), 1e-6)
        d = TIERS[tier]; suffix = f'_{tier}.jpg'
        files = {'diff': d / f'{mid}_diff{suffix}', 'nor_gl': d / f'{mid}_nor_gl{suffix}', 'rough': d / f'{mid}_rough{suffix}',
                 'height': d / f'{mid}_height{suffix}', 'ao': d / f'{mid}_ao{suffix}', 'orm': d / f'{mid}_orm{suffix}'}
        q_diff, q_other = (90, 88) if tier == '4k' else (90, 92 if tier == '1k' else 90)
        save_jpg(lin_to_srgb8(a), files['diff'], q_diff)
        save_jpg(np.clip(np.round((nv * 0.5 + 0.5) * 255), 0, 255).astype(np.uint8), files['nor_gl'], q_other)
        g8 = lambda x: np.clip(np.round(x * 255), 0, 255).astype(np.uint8)
        Image.fromarray(g8(r)).save(files['rough'], quality=88)
        Image.fromarray(g8(h)).save(files['height'], quality=90)
        Image.fromarray(g8(o)).save(files['ao'], quality=88)
        orm = np.stack([g8(o), g8(r), np.zeros_like(g8(r))], -1)
        save_jpg(orm, files['orm'], 88)
        out[tier] = files
    return out

def preview(mid, src_crop_lin, files1k, scratch_dir=None):
    """Per-material preview: row 1 = source crop | albedo tiled 2x2; row 2 = normal | height | rough | ao."""
    cell = 400
    def fit(im):
        im = im.convert('RGB'); im.thumbnail((cell, cell), Image.LANCZOS)
        canvas = Image.new('RGB', (cell, cell), (24, 24, 24)); canvas.paste(im, ((cell - im.width) // 2, (cell - im.height) // 2)); return canvas
    src = Image.fromarray(lin_to_srgb8(np.clip(src_crop_lin * (0.18 / max(float(luma(src_crop_lin).mean()), 1e-4)), 0, 1)))
    alb = Image.open(files1k['diff']).convert('RGB'); t = alb.resize((cell // 2 * 2, cell // 2 * 2)); half = t.resize((cell // 2, cell // 2))
    tiled = Image.new('RGB', (cell, cell))
    for i in range(2):
        for j in range(2):
            tiled.paste(half, (i * cell // 2, j * cell // 2))
    row1 = [fit(src), fit(Image.open(files1k['diff'])), tiled, fit(Image.open(files1k['orm']))]
    row2 = [fit(Image.open(files1k[k])) for k in ('nor_gl', 'height', 'rough', 'ao')]
    sheet = Image.new('RGB', (cell * 4, cell * 2), (24, 24, 24))
    for i, im in enumerate(row1):
        sheet.paste(im, (i * cell, 0))
    for i, im in enumerate(row2):
        sheet.paste(im, (i * cell, cell))
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW_DIR / f'materials_uhd_{mid}_preview.jpg', quality=85)
    if scratch_dir:
        Path(scratch_dir).mkdir(parents=True, exist_ok=True)
        sheet.resize((1000, 500), Image.LANCZOS).save(Path(scratch_dir) / f'{mid}_preview.jpg', quality=85)

def contact_sheet(ids):
    cell = 480
    cols = 4; rows = (len(ids) + cols - 1) // cols
    sheet = Image.new('RGB', (cell * cols, cell * rows), (24, 24, 24))
    for n, mid in enumerate(ids):
        p = TIERS['1k'] / f'{mid}_diff_1k.jpg'
        if not p.exists():
            continue
        im = Image.open(p).convert('RGB'); im.thumbnail((cell // 2, cell // 2), Image.LANCZOS)
        tile = Image.new('RGB', (cell, cell))
        for i in range(2):
            for j in range(2):
                tile.paste(im, (i * cell // 2, j * cell // 2))
        sheet.paste(tile, ((n % cols) * cell, (n // cols) * cell))
    sheet.save(PREVIEW_DIR / 'materials_uhd_preview.jpg', quality=85)

# ----------------------------------------------------------------------------- driver
def process(mat, spec, photo_cache, scratch_dir=None):
    mid, slot = mat['id'], mat['slot']
    photo_path = PHOTOS / mat['photo']
    if photo_path not in photo_cache:
        photo_cache.clear()
        photo_cache[photo_path] = srgb_to_lin(np.asarray(Image.open(photo_path).convert('RGB')))
    img = photo_cache[photo_path]
    crop = crop_region(img, mat['rect'], mat.get('rotation_deg', 0), mat.get('core'))
    ch, cw = crop.shape[:2]
    tile_w, tile_h = mat['tile_px']
    master = (tile_w * MASTER_FACTOR, tile_h * MASTER_FACTOR)
    # light denoise at source resolution: 8-bit WebP shadows carry block noise that the delight gain
    # and the upsample would otherwise magnify
    crop = np.stack([gauss(crop[..., c], 0.6, mode='reflect') for c in range(3)], -1)
    mask = build_mask(crop)
    cp_file, mult = COUNTERPART[slot]
    target = float(luma(srgb_to_lin(np.asarray(Image.open(ROOT / cp_file).convert('RGB')))).mean()) * mult
    alb = delight(crop, mask, target, float(mat.get('chroma', 1.0)))
    alb = resize_f32(alb, master)
    upsample = master[0] / cw if tile_w >= tile_h else master[1] / ch
    up_x, up_y = master[0] / cw, master[1] / ch
    radius = float(np.clip(1.0 * min(up_x, up_y), 1.0, 5.0))
    blur = np.stack([gauss(alb[..., c], radius, mode='wrap') for c in range(3)], -1)
    alb = np.clip(alb + 0.35 * (alb - blur), 0, 1)
    band = max(24, min(master) // 8)     # wide band: the cut can follow low-contrast paths
    alb = np.clip(make_seamless(alb, band), 0, 1)
    k = MASTER_FACTOR
    height, normal8, rough, ao = derive_maps(alb, slot, mat['height_mode'], k)
    files = write_tiers(mid, alb, height, normal8, rough, ao, master)
    preview(mid, crop, files['1k'], scratch_dir)
    # ---- manifest entry
    maps = {}
    for tier, fs in files.items():
        maps[tier] = {k: {'file': str(v.relative_to(ROOT)), 'bytes': v.stat().st_size, 'sha256': sha256(v)} for k, v in fs.items()}
    metrics = {tier: tier_metrics(files[tier]) for tier in files}
    metrics['masked_fraction'] = round(float((~mask).mean()), 5)
    metrics['counterpart'] = cp_file; metrics['counterpart_mean_linear_luma_x_mult'] = round(target, 4)
    native = min(cw, ch)
    entry = {
        'id': mid, 'slot': slot, 'primary_for_slot': bool(mat.get('primary_for_slot', False)), 'photo': mat['photo'],
        'rect': mat['rect'], 'rotation_deg': mat.get('rotation_deg', 0), 'core': mat.get('core'),
        'source_crop_px': [cw, ch], 'native_source_px': native, 'tile_px_1k': [tile_w, tile_h], 'master_px': list(master),
        'upsample_factor': round(float(min(up_x, up_y)), 2), 'anisotropic_stretch_y_over_x': round(float(up_y / up_x), 2),
        'physical_scale_m': mat['physical_scale_m'], 'scale_basis': mat.get('scale_basis', ''),
        'runtime_slot_scale_m': RUNTIME_SLOT_SCALE_M.get(slot), 'height_mode': mat['height_mode'],
        'normal_strength_1k': SLOT_PARAMS[slot][0], 'maps': maps, 'metrics': metrics, 'notes': mat.get('notes', ''),
        'status': ('photo-derived single-image heuristic maps: albedo from the photograph after delighting; height, normal, '
                   'roughness and ao ESTIMATED from luminance; not photogrammetry; physical scale estimated; the 4k and 2k '
                   f'tiers are interpolated {min(up_x, up_y):.1f}x above the native source resolution ({native} px on the short side)'
                   + ('; the region was rectified by an anisotropic stretch (foreshortened ground plane), so along-view detail is interpolated' if abs(up_y / up_x - 1) > 0.3 else '')),
    }
    return entry

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--spec', default=str(ROOT / 'construction_code_v3/uhd_extraction_spec.json'))
    ap.add_argument('--only', action='append', help='material id to (re)build; default all')
    ap.add_argument('--scratch', default=None, help='directory for 1000-px preview copies')
    ap.add_argument('--master-factor', type=int, default=4, help='master = 1k tile x this (4 = 4096 masters; 1 = quick 1k-only preview run)')
    a = ap.parse_args()
    global MASTER_FACTOR
    MASTER_FACTOR = a.master_factor
    spec = json.load(open(a.spec))
    mats = [m for m in spec['materials'] if not a.only or m['id'] in a.only]
    for d in TIERS.values():
        d.mkdir(parents=True, exist_ok=True)
    manifest_path = TIERS['1k'] / 'MATERIALS_UHD_MANIFEST.json'
    manifest = json.load(open(manifest_path)) if (a.only and manifest_path.exists()) else {'materials': []}
    entries = {m['id']: m for m in manifest.get('materials', [])}
    photo_cache = {}
    for m in mats:
        print('building', m['id'], m['slot'], m['photo'], m['rect'], flush=True)
        entries[m['id']] = process(m, spec, photo_cache, a.scratch)
        print('   ', json.dumps(entries[m['id']]['metrics']['1k']), flush=True)
    order = [m['id'] for m in spec['materials'] if m['id'] in entries]
    sources = []
    for ph in sorted({m['photo'] for m in spec['materials']}):
        p = PHOTOS / ph
        with Image.open(p) as im:
            w, h = im.size
        sources.append({'file': f'construction_inputs/uhd_photos/{ph}', 'bytes': p.stat().st_size, 'sha256': sha256(p), 'width': w, 'height': h,
                        'provenance': 'photograph supplied by the repository owner (chat attachment or Google Drive); licence, photographer, capture date and native capture resolution not recorded'})
    primaries = {e['slot']: e['id'] for e in entries.values() if e['primary_for_slot'] and e['slot'] in RUNTIME_SLOT_SCALE_M}
    totals = {tier: sum(mp['bytes'] for e in entries.values() for mp in e['maps'].get(tier, {}).values()) for tier in TIERS}
    manifest = {
        'generator': 'construction_code_v3/extract_uhd_materials.py', 'stamp': STAMP, 'spec': str(Path(a.spec).resolve().relative_to(ROOT)) if str(a.spec).startswith(str(ROOT)) else a.spec,
        'status': ('PHOTO-DERIVED representatives cut from photographs supplied by the repository owner. Albedo is the delit '
                   'photograph; height, normal, roughness and ambient occlusion are single-image heuristic estimates; physical '
                   'scale is estimated from objects in frame; nothing here is photogrammetry or a survey. The 4k masters and 2k '
                   'tier are interpolated above each material\'s native_source_px.'),
        'tiers': {t: str(d.relative_to(ROOT)) for t, d in TIERS.items()}, 'tier_total_bytes': totals,
        'runtime_slots': primaries, 'runtime_slot_scale_m': RUNTIME_SLOT_SCALE_M,
        'not_consumed_by_runtime': [e['id'] for e in entries.values() if not (e['primary_for_slot'] and e['slot'] in RUNTIME_SLOT_SCALE_M)],
        'sources': sources, 'materials': [entries[i] for i in order],
        'map_conventions': {'diff': 'sRGB base colour', 'nor_gl': 'OpenGL tangent-space normal (+Y up), same convention as materials_v2',
                            'rough': 'grey roughness', 'height': 'grey height 0..1 (bright = high)', 'ao': 'grey ambient occlusion',
                            'orm': 'packed R = ao, G = roughness, B = metallic (0)'},
    }
    manifest_path.write_text(json.dumps(manifest, indent=1))
    (ROOT / 'asset_packs/MATERIALS_UHD_MANIFEST.json').write_text(json.dumps(manifest, indent=1))
    contact_sheet(order)
    print('tiers (MB):', {t: round(v / 1e6, 1) for t, v in totals.items()})
    print('runtime slots:', primaries)

if __name__ == '__main__':
    main()
