#!/usr/bin/env python3
"""Photo-derived 4K asset packs for the Aokigahara reconstruction.

Each pack is built from ONE reference photograph listed in asset_packs_config.json and contains, as
far as that photograph supports it:

  bark/ greenery/ ground/   4096 x 4096 tileable PBR sets in the repository's existing map layout:
                            <id>_diff_4k.jpg   sRGB albedo, large-scale illumination flattened
                            <id>_nor_gl_4k.jpg OpenGL tangent-space normal (same convention as
                                               construction_code_v2/gen_textures.py)
                            <id>_rough_4k.jpg  roughness (heuristic per material class)
                            <id>_height_4k.jpg height proxy derived from luminance bands
  sky/                      4096 x 2048 equirectangular sky dome rendered with a NumPy port of the
                            viewer's own Preetham shader (viewer/vendor/addons/objects/Sky.js) using
                            parameters fitted to the photograph's visible sky, plus sky.json
  lighting/                 a daylight preset in the exact shape of PRESETS in viewer/app.js,
                            with every measurement and assumption that produced it
  mood/                     dominant palette, tonal statistics, and a 33^3 .cube colour grade
  <id>_sheet_4k.jpg         a 4096-wide contact sheet of everything above
  <id>_manifest.json        provenance: source, colour handling, regions, parameters, checksums

What is measured, what is inferred and what is invented is stated in every manifest. Nothing here
is a photogrammetric capture of Aokigahara. Deterministic: fixed seeds, no network, no ML models.

Usage:
  python3 construction_code_v2/gen_asset_packs.py                 # every pack, 4K
  python3 construction_code_v2/gen_asset_packs.py --pack oak_lichen_evening --size 1024
  python3 construction_code_v2/gen_asset_packs.py --preview        # region check sheets only
  python3 construction_code_v2/gen_asset_packs.py --include-withheld --source-dir DIR
"""
import argparse, hashlib, io, json, math, time
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, ImageCms, ImageDraw, ImageFont
from scipy import ndimage, optimize
from scipy import fft as sfft

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path(__file__).with_name('asset_packs_config.json')
OUT_ROOT = ROOT / 'asset_packs'
SRC_DIR = OUT_ROOT / '_sources'
SKY_SHADER = ROOT / 'viewer/vendor/addons/objects/Sky.js'
GRADE_DEMO_RENDER = ROOT / 'renders/after_p4/C1_start_corridor.png'
GENERATOR = 'construction_code_v2/gen_asset_packs.py'

# Copied from viewer/app.js PRESETS: the calibration targets for the photo -> preset mapping.
VIEWER_PRESETS = {
    'overcast': dict(sun=.55, hemi=1.9, turb=20, ray=.25, mie=.08),
    'soft': dict(sun=2.0, hemi=1.35, turb=6, ray=1.2, mie=.006),
    'clear': dict(sun=3.3, hemi=.9, turb=2.8, ray=1.4, mie=.0035),
}
VIEWER_SUN_AZIMUTH_DEG = 155.0        # app.js setSun(): setFromSphericalCoords(1, 90-angle, 155)
VIEWER_MIE_G = 0.82

# Per-class heuristics for the derived maps. Roughness values are conventional PBR starting points,
# not measurements. Height weights mix three luminance bands (fine / mid / coarse, see derive_maps).
# tile_m is the physical width the 4K tile should represent for its intended use; the source is
# upscaled towards that (never more than UPSCALE_CAP) before synthesis.
CLASS_PARAMS = {
    'bark':      dict(rough=0.88, rough_mod=0.10, bands=(0.45, 0.35, 0.20), normal=6.0, tile_m=2.0),
    'mosslog':   dict(rough=0.93, rough_mod=0.06, bands=(0.40, 0.40, 0.20), normal=5.0, tile_m=1.5),
    'moss':      dict(rough=0.93, rough_mod=0.06, bands=(0.35, 0.45, 0.20), normal=5.0, tile_m=1.5),
    'leaves':    dict(rough=0.70, rough_mod=0.15, bands=(0.50, 0.35, 0.15), normal=4.0, tile_m=3.0),
    'needles':   dict(rough=0.76, rough_mod=0.12, bands=(0.50, 0.35, 0.15), normal=4.0, tile_m=2.5),
    'grass':     dict(rough=0.82, rough_mod=0.10, bands=(0.50, 0.35, 0.15), normal=4.0, tile_m=2.0),
    'dry_grass': dict(rough=0.85, rough_mod=0.08, bands=(0.50, 0.35, 0.15), normal=3.0, tile_m=3.0),
    'litter':    dict(rough=0.90, rough_mod=0.08, bands=(0.45, 0.35, 0.20), normal=5.0, tile_m=2.0),
    'trail':     dict(rough=0.92, rough_mod=0.06, bands=(0.45, 0.35, 0.20), normal=3.0, tile_m=2.0),
}
UPSCALE_CAP = 3.0            # never enlarge a source region more than this before synthesis
MAX_SOURCE_MEGAPIXELS = 6.0  # keeps the exhaustive FFT search tractable
GRAIN_AMOUNT = 0.03          # synthetic micro-grain when the source was enlarged (documented in the manifest)

# ----------------------------------------------------------------------------- colour helpers
def srgb_to_lin(x):
    x = np.asarray(x, np.float32)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)

def lin_to_srgb(x):
    x = np.clip(np.asarray(x, np.float32), 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055).astype(np.float32)

def luma(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722

def to_hex(srgb, prefix='0x'):
    r, g, b = [int(round(float(np.clip(c, 0, 1)) * 255)) for c in srgb]
    return f'{prefix}{r:02x}{g:02x}{b:02x}'

def with_luma(srgb, target):
    """Scale an sRGB colour so its (sRGB-space) luma equals target; keeps the tint."""
    srgb = np.asarray(srgb, np.float64)
    l = float(luma(srgb))
    return np.clip(srgb * (target / max(l, 1e-6)), 0, 1)

def cct_mccamy(lin):
    r, g, b = [float(v) for v in lin]
    X = 0.4124 * r + 0.3576 * g + 0.1805 * b
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Z = 0.0193 * r + 0.1192 * g + 0.9505 * b
    s = X + Y + Z
    if s <= 0:
        return None
    x, y = X / s, Y / s
    n = (x - 0.3320) / (0.1858 - y)
    return float(449 * n ** 3 + 3525 * n ** 2 + 6823.3 * n + 5520.33)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def r3(x):
    return float(f'{float(x):.4g}')

# ----------------------------------------------------------------------------- source loading
def load_source(path):
    im = Image.open(path)
    icc = im.info.get('icc_profile')
    im = ImageOps.exif_transpose(im)
    record = {'file': path.name, 'bytes': path.stat().st_size, 'sha256': sha256_file(path),
              'pixels': [im.width, im.height], 'embedded_profile': None,
              'colour_handling': 'no embedded ICC profile: pixel values taken as sRGB'}
    if icc:
        prof = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        desc = ImageCms.getProfileDescription(prof).strip()
        im = ImageCms.profileToProfile(im.convert('RGB'), prof, ImageCms.createProfile('sRGB'),
                                       renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC, outputMode='RGB')
        record['embedded_profile'] = desc
        record['colour_handling'] = f'embedded profile "{desc}" converted to sRGB with LittleCMS (relative colorimetric)'
    else:
        im = im.convert('RGB')
    arr = np.asarray(im).astype(np.float32) / 255.0
    return arr, record

# ----------------------------------------------------------------------------- geometry
def homography(src, dst):
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.asarray(A, float))
    Hm = vt[-1].reshape(3, 3)
    return Hm / Hm[2, 2]

UNIT_SQUARE = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)

def quad_px(quad, W, H):
    return np.asarray(quad, float) * np.array([W, H], float)

def region_size(quad, W, H, upscale=1.0, stretch_y=1.0, cylinder=False, cyl_max_deg=78.0):
    q = quad_px(quad, W, H)
    top, bottom = np.linalg.norm(q[1] - q[0]), np.linalg.norm(q[2] - q[3])
    left, right = np.linalg.norm(q[3] - q[0]), np.linalg.norm(q[2] - q[1])
    w = max(top, bottom) * upscale
    h = max(left, right) * upscale * stretch_y
    if cylinder:
        w *= math.radians(cyl_max_deg)
    return int(round(w)), int(round(h)), [float(max(top, bottom)), float(max(left, right))]

def rectify(img, quad, out_w, out_h, cylinder=False, cyl_max_deg=78.0, order=3):
    """Perspective-rectify a quad (TL,TR,BR,BL, normalised) to out_w x out_h. With cylinder=True the
    quad's left/right edges are treated as the silhouette of a cylinder and the output x axis is the
    unwrapped surface angle over +-cyl_max_deg."""
    H_, W_ = img.shape[:2]
    Hm = homography(UNIT_SQUARE, quad_px(quad, W_, H_))
    u = (np.arange(out_w) + 0.5) / out_w
    v = (np.arange(out_h) + 0.5) / out_h
    if cylinder:
        tmax = math.radians(cyl_max_deg)
        u = (np.sin((u * 2 - 1) * tmax) + 1) * 0.5
    uu, vv = np.meshgrid(u, v)
    P = np.stack([uu.ravel(), vv.ravel(), np.ones(uu.size)], 0)
    Q = Hm @ P
    xs, ys = Q[0] / Q[2], Q[1] / Q[2]
    out = np.stack([ndimage.map_coordinates(img[..., c], [ys, xs], order=order, mode='nearest') for c in range(3)], -1)
    return np.clip(out.reshape(out_h, out_w, 3), 0, 1).astype(np.float32)

def poly_mask(quad, W, H):
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in quad_px(quad, W, H)], fill=255)
    return np.asarray(m) > 0

def rect_mask(rects, W, H):
    m = np.zeros((H, W), bool)
    for x0, y0, x1, y1 in rects or []:
        m[int(y0 * H):int(math.ceil(y1 * H)), int(x0 * W):int(math.ceil(x1 * W))] = True
    return m

# ----------------------------------------------------------------------------- illumination flattening
def delight(srgb, sigma_frac, strength=1.0):
    """Divide each channel by its own large-scale mean so slow shading and colour drift (sun side vs
    shade side, vignetting) are removed while texture-scale variation is kept."""
    lin = srgb_to_lin(srgb)
    h, w = lin.shape[:2]
    sigma = max(2.0, sigma_frac * min(h, w))
    low = np.stack([ndimage.gaussian_filter(lin[..., c], sigma, mode='reflect') for c in range(3)], -1)
    mean = lin.reshape(-1, 3).mean(0)
    ratio = np.power(mean / np.maximum(low, 1e-4), strength)
    return lin_to_srgb(np.clip(lin * ratio, 0, 1)), float(sigma)

# ----------------------------------------------------------------------------- image quilting (torus-seamless)
def _cut_vertical(err, lo=None, hi=None):
    """Minimum-cost top-to-bottom seam through err (h, w): returns the seam column per row.
    lo / hi (length h) bound the seam per row, inclusive; both derive from a neighbouring seam, so a
    feasible path always exists."""
    h, w = err.shape
    cost = err.astype(np.float64).copy()
    if lo is not None or hi is not None:
        idx = np.arange(w)[None, :]
        if hi is not None:
            cost[idx > np.asarray(hi)[:, None]] = 1e12
        if lo is not None:
            cost[idx < np.asarray(lo)[:, None]] = 1e12
    back = np.zeros((h, w), np.int8)
    idx = np.arange(w)
    for r in range(1, h):
        prev = cost[r - 1]
        left = np.concatenate([[np.inf], prev[:-1]])
        right = np.concatenate([prev[1:], [np.inf]])
        stack = np.stack([left, prev, right])
        k = stack.argmin(0)
        cost[r] += stack[k, idx]
        back[r] = k - 1
    seam = np.zeros(h, int)
    seam[-1] = int(cost[-1].argmin())
    for r in range(h - 1, 0, -1):
        seam[r - 1] = seam[r] + back[r, seam[r]]
    return seam

FFT_WORKERS = -1   # scipy.fft: use every core

class Correlator:
    """Overlap-SSD search over every window position of a source, through cached spectra.

    SSD(pos) = sum(M * S_pos^2) - 2 sum(M * T * S_pos) + sum(M * T^2). The source spectra are
    computed once (single precision, multithreaded); per query the caller transforms the small
    template once and the three channels are summed in the frequency domain, so one inverse
    transform gives the cross term for every position. The first term depends only on the mask
    and is cached per mask."""
    def __init__(self, src, patch, fs):
        self.H, self.W = src.shape[:2]
        self.patch = patch
        self.fs = fs
        src = src.astype(np.float32)
        self.F = [sfft.rfft2(src[..., c], fs, workers=FFT_WORKERS) for c in range(3)]
        self.F2 = sfft.rfft2((src ** 2).sum(-1), fs, workers=FFT_WORKERS)
        self.cache = {}

    def _valid(self, full):
        p = self.patch
        return full[p - 1:self.H, p - 1:self.W]

    def term1(self, m):
        key = m.tobytes()
        if key not in self.cache:
            Fm = sfft.rfft2(m[::-1, ::-1].astype(np.float32), self.fs, workers=FFT_WORKERS)
            self.cache[key] = self._valid(sfft.irfft2(self.F2 * Fm, self.fs, workers=FFT_WORKERS)).copy()
        return self.cache[key]

    def term2(self, Ft):
        acc = self.F[0] * Ft[0] + self.F[1] * Ft[1] + self.F[2] * Ft[2]
        return self._valid(sfft.irfft2(acc, self.fs, workers=FFT_WORKERS))

def template_spectra(m, T, fs):
    return [sfft.rfft2((m * T[..., c])[::-1, ::-1].astype(np.float32), fs, workers=FFT_WORKERS) for c in range(3)]

def quilt(src, size, patch, overlap, rng, tol=0.15, min_candidates=30, mirror=True, reuse_penalty=0.6):
    """Efros-Freeman image quilting on a torus: the result tiles seamlessly in both directions.
    src: (H, W, 3) float32 in [0, 1]. Exhaustive overlap-SSD search through FFT correlation over the
    source and (mirror=True) its horizontal mirror. Each patch is drawn at random from every
    candidate within tol of the best error, or from the best min_candidates, whichever is larger,
    and source positions close to recently used ones carry a decaying penalty, so a small source
    does not repeat one dominant patch in a lattice."""
    H, W = src.shape[:2]
    step = patch - overlap
    n = size // step
    assert n * step == size, 'size must be a multiple of patch-overlap'
    assert H >= patch and W >= patch, 'source smaller than patch'
    ov = overlap
    canvas = np.zeros((size + ov, size + ov, 3), np.float32)
    pool = [src] + ([src[:, ::-1].copy()] if mirror else [])
    fs = [sfft.next_fast_len(n + patch - 1, real=True) for n in (H, W)]
    corr = [Correlator(q, patch, fs) for q in pool]
    vh, vw = H - patch + 1, W - patch + 1
    penalty = [np.zeros((vh, vw), np.float32) for _ in pool]
    rad = patch // 2
    # Corner consistency. A patch pastes its top-right corner below its own top seam; the next patch
    # along the row must not keep the old canvas on both sides of that fresh corner, or a straight
    # vertical edge survives at the end of the overlap band. So in the corner columns a top cut may
    # not run below the left neighbour's top cut, and a bottom cut (torus wrap row) may not run
    # above the left neighbour's bottom cut; the last column applies the same to the first patch of
    # its row, whose content it wraps onto.
    top_seam, bot_seam = {}, {}
    for i in range(n):
        for j in range(n):
            y0, x0 = i * step, j * step
            last_r, last_c = i == n - 1, j == n - 1
            if last_c:
                canvas[y0:y0 + patch, size:size + ov] = canvas[y0:y0 + patch, 0:ov]
            if last_r:
                canvas[size:size + ov, x0:x0 + patch] = canvas[0:ov, x0:x0 + patch]
            if last_r and last_c:
                canvas[size:size + ov, size:size + ov] = canvas[0:ov, 0:ov]
            m = np.zeros((patch, patch), np.float64)
            if j > 0: m[:, :ov] = 1
            if i > 0: m[:ov, :] = 1
            if last_c: m[:, -ov:] = 1
            if last_r: m[-ov:, :] = 1
            T = canvas[y0:y0 + patch, x0:x0 + patch].astype(np.float64)
            if m.sum() == 0:
                q = int(rng.integers(len(pool)))
                y, x = int(rng.integers(vh)), int(rng.integers(vw))
            else:
                errs = []
                term3 = float((m[..., None] * T ** 2).sum())
                Ft = template_spectra(m, T, fs)
                for cr in corr:
                    errs.append(np.maximum(cr.term1(m) - 2 * cr.term2(Ft) + term3, 0).ravel())
                err = np.concatenate(errs) * (1.0 + np.concatenate([pn.ravel() for pn in penalty]))
                emin = float(err.min())
                cand = np.flatnonzero(err <= emin * (1 + tol) + 1e-9)
                if len(cand) < min_candidates:
                    cand = np.argpartition(err, min(min_candidates, len(err) - 1))[:min_candidates]
                k = int(rng.choice(cand))
                q, k = divmod(k, vh * vw)
                y, x = divmod(k, vw)
            for pn in penalty:
                pn *= 0.97
            penalty[q][max(0, y - rad):y + rad, max(0, x - rad):x + rad] += reuse_penalty
            P = pool[q][y:y + patch, x:x + patch]
            d = ((P.astype(np.float64) - T) ** 2).sum(-1)
            use = np.ones((patch, patch), bool)
            cols = np.arange(ov)[None, :]
            if j > 0:
                use[:, :ov] &= cols > _cut_vertical(d[:, :ov])[:, None]
            if last_c:
                use[:, -ov:] &= cols < _cut_vertical(d[:, -ov:])[:, None]
            if i > 0:
                hi = np.full(patch, ov - 1)
                if j > 0:
                    hi[:ov] = np.minimum(hi[:ov], top_seam[(i, j - 1)][step:patch])
                if last_c:
                    hi[step:] = np.minimum(hi[step:], top_seam[(i, 0)][:ov])
                st = _cut_vertical(d[:ov, :].T, hi=hi)
                top_seam[(i, j)] = st
                use[:ov, :] &= (cols > st[:, None]).T
            if last_r:
                lo = np.zeros(patch, int)
                if j > 0:
                    lo[:ov] = np.maximum(lo[:ov], bot_seam[(i, j - 1)][step:patch])
                if last_c:
                    lo[step:] = np.maximum(lo[step:], bot_seam[(i, 0)][:ov])
                sb = _cut_vertical(d[-ov:, :].T, lo=lo)
                bot_seam[(i, j)] = sb
                use[-ov:, :] &= (cols < sb[:, None]).T
            canvas[y0:y0 + patch, x0:x0 + patch] = np.where(use[..., None], P, T.astype(np.float32))
            if last_c:
                canvas[y0:y0 + patch, 0:ov] = canvas[y0:y0 + patch, size:size + ov]
            if last_r:
                canvas[0:ov, x0:x0 + patch] = canvas[size:size + ov, x0:x0 + patch]
            if last_r and last_c:
                canvas[0:ov, 0:ov] = canvas[size:size + ov, size:size + ov]
    return canvas[:size, :size]

def choose_quilt_params(src_h, src_w, size):
    """Patch grid from the source size: step must divide size; the source must hold the patch with room."""
    m = min(src_h, src_w)
    step = 256 if m >= 1100 else 128
    if size < 2048:
        step = min(step, 128)
    ov = step // 2
    patch = step + ov
    extra = 1.0
    if m < patch + 64:
        extra = (patch + 64) / m
    return step, patch, ov, extra

# ----------------------------------------------------------------------------- derived PBR maps
def blur_wrap(a, sigma):
    if sigma <= 12:
        return ndimage.gaussian_filter(a, sigma, mode='wrap')
    f = 1 << int(math.log2(max(1.0, sigma / 6.0)))
    h, w = a.shape
    small = a.reshape(h // f, f, w // f, f).mean((1, 3))
    small = ndimage.gaussian_filter(small, sigma / f, mode='wrap')
    return ndimage.zoom(small, f, order=1, mode='grid-wrap')

def height_to_normal(h, strength):
    """Same convention as construction_code_v2/gen_textures.py (OpenGL, +Y up in tangent space),
    with periodic differences so the normal map tiles."""
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    nx, ny, nz = -gx * strength, -gy * strength, np.ones_like(h)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / l, -ny / l, nz / l], -1)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)

def tileable_grain(size, rng):
    """Two octaves of blurred white noise (periodic), zero mean, unit std."""
    n = rng.standard_normal((size, size)).astype(np.float32)
    g = ndimage.gaussian_filter(n, 1.0, mode='wrap') + 0.6 * ndimage.gaussian_filter(n, 2.2, mode='wrap')
    return (g / (g.std() + 1e-6)).astype(np.float32)

def add_grain(tile_srgb, amount, rng):
    lin = srgb_to_lin(tile_srgb)
    g = tileable_grain(tile_srgb.shape[0], rng)
    return lin_to_srgb(np.clip(lin * (1.0 + amount * g)[..., None], 0, 1))

def derive_maps(tile_srgb, cls, size):
    """Height proxy from three luminance bands (sigma 1.5/6/24 px at 1K, scaled with size); the
    finest band is deliberately above pixel scale so JPEG noise does not become relief."""
    p = CLASS_PARAMS[cls]
    L = np.sqrt(np.clip(luma(srgb_to_lin(tile_srgb)), 0, 1)).astype(np.float32)
    k = size / 1024.0
    b0, b1, b2, b3 = blur_wrap(L, 1.5 * k), blur_wrap(L, 6.0 * k), blur_wrap(L, 24.0 * k), blur_wrap(L, 96.0 * k)
    bands = [b0 - b1, b1 - b2, b2 - b3]
    h = sum(w * (b / (np.std(b) + 1e-6)) for w, b in zip(p['bands'], bands))
    lo, hi = np.percentile(h, [0.5, 99.5])
    h = np.clip((h - lo) / (hi - lo + 1e-6), 0, 1).astype(np.float32)
    normal = height_to_normal(h, p['normal'] * k)
    fine = (b0 - b2)
    rough = np.clip(p['rough'] - p['rough_mod'] * (fine / (np.std(fine) + 1e-6)) * 0.5, 0.3, 1.0)
    return dict(height=h, normal=normal, rough=rough.astype(np.float32))

def save_maps(tile_srgb, maps, out_dir, stem, size):
    tag = f'{size // 1024}k'
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    def save(arr, name, mode, q):
        pth = out_dir / f'{stem}_{name}_{tag}.jpg'
        img = Image.fromarray(arr) if mode == 'RGB' else Image.fromarray(arr).convert('L')
        img.save(pth, quality=q, subsampling=0)
        files[name] = pth
    save((np.clip(tile_srgb, 0, 1) * 255 + 0.5).astype(np.uint8), 'diff', 'RGB', 85)
    save(maps['normal'], 'nor_gl', 'RGB', 85)
    save((maps['rough'] * 255 + 0.5).astype(np.uint8), 'rough', 'L', 78)
    save((maps['height'] * 255 + 0.5).astype(np.uint8), 'height', 'L', 78)
    return files

# ----------------------------------------------------------------------------- sky: NumPy port of viewer/vendor/addons/objects/Sky.js
TOTAL_RAYLEIGH = np.array([5.804542996261093E-6, 1.3562911419845635E-5, 3.0265902468824876E-5])
MIE_CONST = np.array([1.8399918514433978E14, 2.7798023919660528E14, 4.0790479543861094E14])
CUTOFF_ANGLE, STEEPNESS, EE = 1.6110731556870734, 1.5, 1000.0
SUN_ANGULAR_DIAMETER_COS = 0.999956676946448443553574619906976478926848692873900859324
ACES_IN = np.array([[0.59719, 0.07600, 0.02840], [0.35458, 0.90834, 0.13383], [0.04823, 0.01566, 0.83777]])
ACES_OUT = np.array([[1.60475, -0.10208, -0.00327], [-0.53108, 1.10813, -0.07276], [-0.07367, -0.00605, 1.07602]])

def sky_radiance(dirs, sun, turbidity, rayleigh, mie, g=VIEWER_MIE_G):
    """Sky.js fragment output before tone mapping, for unit directions dirs (N,3) and unit sun (3,)."""
    up_dot_sun = float(sun[1])
    sunE = EE * max(0.0, 1.0 - math.exp(-((CUTOFF_ANGLE - math.acos(max(-1.0, min(1.0, up_dot_sun)))) / STEEPNESS)))
    sunfade = 1.0 - min(1.0, max(0.0, 1.0 - math.exp(up_dot_sun / 450000.0)))
    betaR = TOTAL_RAYLEIGH * (rayleigh - (1.0 - sunfade))
    betaM = 0.434 * (0.2 * turbidity * 10e-18) * MIE_CONST * mie
    zen = np.arccos(np.clip(dirs[:, 1], 0, 1))
    inv = 1.0 / (np.cos(zen) + 0.15 * np.power(93.885 - np.degrees(zen), -1.253))
    Fex = np.exp(-(betaR[None] * (8.4e3 * inv)[:, None] + betaM[None] * (1.25e3 * inv)[:, None]))
    cosT = dirs @ sun
    rPhase = 0.05968310365946075 * (1.0 + (cosT * 0.5 + 0.5) ** 2)
    g2 = g * g
    mPhase = 0.07957747154594767 * ((1.0 - g2) / np.power(1.0 - 2.0 * g * cosT + g2, 1.5))
    ratio = (betaR[None] * rPhase[:, None] + betaM[None] * mPhase[:, None]) / (betaR + betaM)[None]
    Lin = np.power(np.maximum(sunE * ratio * (1.0 - Fex), 0), 1.5)
    w = min(1.0, max(0.0, (1.0 - up_dot_sun) ** 5))
    Lin *= (1.0 - w) + w * np.sqrt(np.maximum(sunE * ratio * Fex, 0))
    L0 = 0.1 * Fex
    t = np.clip((cosT - SUN_ANGULAR_DIAMETER_COS) / 0.00002, 0, 1)
    sundisk = t * t * (3 - 2 * t)
    L0 = L0 + (sunE * 19000.0 * Fex) * sundisk[:, None]
    tex = (Lin + L0) * 0.04 + np.array([0.0, 0.0003, 0.00075])
    return np.power(np.maximum(tex, 0), 1.0 / (1.2 + 1.2 * sunfade))

def aces_filmic(color, exposure):
    c = color * (exposure / 0.6)
    c = c @ ACES_IN
    c = (c * (c + 0.0245786) - 0.000090537) / (c * (0.983729 * c + 0.4329510) + 0.238081)
    c = c @ ACES_OUT
    return np.clip(c, 0, 1)

def sky_display(dirs, sun, turb, ray, mie, exposure):
    return lin_to_srgb(aces_filmic(sky_radiance(dirs, sun, turb, ray, mie), exposure))

def pixel_dirs(xs, ys, W, H, focal_equiv_mm, pitch_deg):
    """Camera-frame unit directions (x right, y up, z forward) for pixel centres, from a 35 mm
    equivalent focal length applied to the frame diagonal and a camera pitch."""
    f = (math.hypot(W, H) / 2) / math.tan(math.atan(21.63 / focal_equiv_mm))
    X = (xs - W / 2) / f
    Y = (H / 2 - ys) / f
    Z = np.ones_like(X)
    p = math.radians(pitch_deg)
    y = Y * math.cos(p) + Z * math.sin(p)
    z = Z * math.cos(p) - Y * math.sin(p)
    d = np.stack([X, y, z], -1)
    return d / np.linalg.norm(d, axis=-1, keepdims=True)

def sun_dir_camera(elev_deg, az_rel_deg):
    e, a = math.radians(elev_deg), math.radians(az_rel_deg)
    return np.array([math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)])

def sun_dir_viewer(elev_deg):
    theta, phi = math.radians(90 - elev_deg), math.radians(VIEWER_SUN_AZIMUTH_DEG)
    return np.array([math.sin(theta) * math.sin(phi), math.cos(theta), math.sin(theta) * math.cos(phi)])

def sky_mask(srgb, roi_quad):
    H, W = srgb.shape[:2]
    r, g, b = srgb[..., 0], srgb[..., 1], srgb[..., 2]
    mx, mn = srgb.max(-1), srgb.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    L = luma(srgb)
    blue = (b > r + 0.03) & (b >= g - 0.01) & (L > 0.25) & (sat < 0.6)
    white = (L > 0.85) & (sat < 0.12)
    # reject mixed pixels at leaf edges: the sky is locally smooth
    mean = ndimage.uniform_filter(L, 7)
    var = ndimage.uniform_filter(L * L, 7) - mean * mean
    smooth = np.sqrt(np.maximum(var, 0)) < 0.025
    m = poly_mask(roi_quad, W, H) & (blue | white) & smooth
    return ndimage.binary_erosion(m, iterations=3)

def fit_sky(dirs, rgb, sun_elev):
    best = None
    starts = [(2.8, 1.4, 0.0035, 1.0), (6.0, 1.2, 0.006, 1.0), (20.0, 0.25, 0.08, 0.9)]
    for az in (0, 30, 60, 90, 120, 150, 180):
        sun = sun_dir_camera(sun_elev, az)
        def loss(p):
            turb, ray, mie, expo = np.exp(p)
            if not (1 <= turb <= 20 and 0.05 <= ray <= 4 and 0.0005 <= mie <= 0.1 and 0.2 <= expo <= 4):
                return 10.0
            return float(((sky_display(dirs, sun, turb, ray, mie, expo) - rgb) ** 2).mean())
        for s in starts:
            res = optimize.minimize(loss, np.log(s), method='Nelder-Mead', options=dict(maxiter=500, xatol=1e-3, fatol=1e-8))
            if best is None or res.fun < best['loss']:
                turb, ray, mie, expo = np.exp(res.x)
                best = dict(loss=float(res.fun), turb=float(turb), ray=float(ray), mie=float(mie), fit_exposure=float(expo), sun_azimuth_rel_deg=az)
    best['rms_srgb'] = math.sqrt(best['loss'])
    return best

def render_equirect(W, H, sun_elev, turb, ray, mie, exposure, ground_srgb, horizon_srgb):
    u = (np.arange(W) + 0.5) / W
    v = 1.0 - (np.arange(H) + 0.5) / H              # v = 1 at the top row (three.js flipY textures)
    phi = (u - 0.5) * 2 * math.pi                     # three.js equirectUv: u = atan(dir.z, dir.x)/2pi + 0.5
    el = (v - 0.5) * math.pi                          #                     v = asin(dir.y)/pi + 0.5
    sun = sun_dir_viewer(sun_elev)
    out = np.zeros((H, W, 3), np.float32)
    ground = np.asarray(ground_srgb, np.float32)
    horizon = np.asarray(horizon_srgb, np.float32)
    for y0 in range(0, H, 64):
        e = el[y0:y0 + 64]
        ce, se = np.cos(e), np.sin(e)
        dirs = np.stack([ce[:, None] * np.cos(phi)[None, :], np.broadcast_to(se[:, None], (len(e), W)),
                         ce[:, None] * np.sin(phi)[None, :]], -1).reshape(-1, 3)
        col = sky_display(dirs, sun, turb, ray, mie, exposure).reshape(len(e), W, 3)
        below = se < 0
        if below.any():
            t = np.clip(-se[below] / math.radians(4.0), 0, 1)[:, None, None]
            depth = np.clip(-se[below] * 1.2, 0, 1)[:, None, None]
            g = ground[None, None, :] * (1.0 - 0.45 * depth)
            col[below] = horizon[None, None, :] * (1 - t) + g * t
        out[y0:y0 + 64] = col
    return out

# ----------------------------------------------------------------------------- lighting analysis
def otsu(x):
    hist, edges = np.histogram(x, bins=128)
    hist = hist.astype(float)
    centers = (edges[:-1] + edges[1:]) / 2
    w0 = np.cumsum(hist)
    w1 = hist.sum() - w0
    m0 = np.cumsum(hist * centers) / np.maximum(w0, 1e-9)
    m1 = (np.cumsum((hist * centers)[::-1])[::-1] / np.maximum(w1, 1e-9))
    m1 = np.concatenate([m1[1:], [m1[-1]]])
    var = w0[:-1] * w1[:-1] * (m0[:-1] - m1[:-1]) ** 2
    return float(centers[int(np.argmax(var))])

def probe_pixels(srgb, quad, exclude=None):
    H, W = srgb.shape[:2]
    m = poly_mask(quad, W, H)
    if exclude is not None:
        m &= ~exclude
    return srgb[m]

def illumination_split(srgb, quad, exclude=None):
    """Split a probe into lit and shaded pixels by ILLUMINATION, not texture: the luminance is
    blurred at about a tenth of the probe size (normalised so the mask border does not bleed in)
    before an Otsu threshold in the log domain. Falls back to the upper/lower 30 % of the blurred
    luminance when Otsu isolates only a sliver."""
    H, W = srgb.shape[:2]
    m = poly_mask(quad, W, H)
    if exclude is not None:
        m &= ~exclude
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sub = srgb_to_lin(srgb[y0:y1, x0:x1])
    msub = m[y0:y1, x0:x1].astype(np.float32)
    L = luma(sub)
    sigma = max(3.0, min(y1 - y0, x1 - x0) / 10.0)
    Lb = ndimage.gaussian_filter(L * msub, sigma) / np.maximum(ndimage.gaussian_filter(msub, sigma), 1e-3)
    inside = msub > 0
    vals = np.log(np.maximum(Lb[inside], 1e-4))
    thr = otsu(vals)
    lit_sel = vals > thr
    frac = float(lit_sel.mean())
    method = f'Otsu on log illumination (blur sigma {sigma:.0f} px)'
    if not (0.08 <= frac <= 0.92):
        lo, hi = np.percentile(vals, [30, 70])
        lit_sel, shade_sel = vals >= hi, vals <= lo
        method += '; Otsu split was one-sided, used the upper/lower 30 % of the blurred luminance'
    else:
        shade_sel = ~lit_sel
    pix = sub[inside]
    return pix[lit_sel], pix[shade_sel], pix, float(lit_sel.mean()), method, float(sigma)

def lighting_analysis(srgb, pack, sky_info, exclude=None):
    probes = pack['probes']
    lit, shade, lin, lit_frac, split_method, split_sigma = illumination_split(srgb, probes['lit_shadow'], exclude)
    px = lin
    lit_m, shade_m = lit.mean(0), shade.mean(0)
    key_fill = float(luma(lit_m) / max(luma(shade_m), 1e-6))
    ratio = max(key_fill - 1.0, 0.0)
    direct = np.maximum(lit_m - shade_m, 1e-6)
    raw_sun = direct / direct.max()
    if sky_info and sky_info.get('mean_srgb'):
        amb_tint = srgb_to_lin(np.array(sky_info['mean_srgb']))
        amb_basis = 'visible sky mean'
    else:
        amb_tint = np.array([0.80, 0.88, 1.0])
        amb_basis = 'assumed blue-sky shade tint (0.80, 0.88, 1.00) because no sky is visible'
    amb_tint = amb_tint / amb_tint.max()
    sun_est = np.maximum(direct / np.maximum(shade_m, 1e-6) * amb_tint, 1e-6)
    sun_est = sun_est / sun_est.max()
    diffuse = ratio < 0.35
    ground_px = srgb_to_lin(probe_pixels(srgb, probes['ground'], exclude)).mean(0)
    fog_px = probe_pixels(srgb, probes['fog'], exclude).mean(0)
    if diffuse:
        sun_i, hemi = 0.55, 1.9
    else:
        hemi = float(np.clip(1.9 - 0.3 * math.log2(1 + ratio), 0.9, 1.9))
        sun_i = float(np.clip(ratio * hemi * 0.9, 0.4, 3.6))
    if sky_info and sky_info.get('fit'):
        f = sky_info['fit']
        turb, ray, mie = f['turb'], f['ray'], f['mie']
        atmos_basis = 'fitted to the visible sky with the viewer Sky shader'
    else:
        t = float(np.clip((ratio - 0.35) / (3.0 - 0.35), 0, 1))
        a, b = VIEWER_PRESETS['overcast'], VIEWER_PRESETS['clear']
        turb = a['turb'] * (1 - t) + b['turb'] * t
        ray = a['ray'] * (1 - t) + b['ray'] * t
        mie = math.exp(math.log(a['mie']) * (1 - t) + math.log(b['mie']) * t)
        atmos_basis = 'interpolated between the overcast and clear presets from the measured key:fill ratio (no sky visible)'
    if sky_info and sky_info.get('mean_srgb'):
        hemi_sky = with_luma(np.array(sky_info['mean_srgb']), 0.78)
        hemi_sky_basis = 'visible sky mean, luma matched to the existing presets'
    else:
        amb = shade_m / direct
        hemi_sky = with_luma(lin_to_srgb(amb / amb.max()), 0.78)
        hemi_sky_basis = 'shade/direct tint of the probe surface (albedo cancels), luma matched to the existing presets'
    hemi_ground = with_luma(lin_to_srgb(ground_px), 0.19)
    fog = with_luma(fog_px, 0.58)
    median_l = float(np.median(luma(srgb.reshape(-1, 3)[::7])))
    exposure = float(np.clip(0.9 + (median_l - 0.35) * 0.6, 0.85, 1.05))
    preset = dict(label=f"{pack['title']} (photo-derived)", sun=r3(sun_i), hemi=r3(hemi), hemiSky=to_hex(hemi_sky),
                  hemiGround=to_hex(hemi_ground), turb=r3(turb), ray=r3(ray), mie=r3(mie), fog=to_hex(fog), exposure=r3(exposure))
    cct = cct_mccamy(sun_est)
    measurements = dict(
        probe_pixels=int(len(px)), lit_fraction=r3(lit_frac), split_method=split_method,
        lit_mean_linear=[r3(v) for v in lit_m], shade_mean_linear=[r3(v) for v in shade_m],
        key_to_fill_luminance_ratio=r3(key_fill), direct_over_ambient=r3(ratio),
        classified_as='diffuse (no usable lit/shade split)' if diffuse else 'directional',
        direct_light_tint_raw=[r3(v) for v in raw_sun],
        direct_light_tint_albedo_cancelled=[r3(v) for v in sun_est],
        direct_light_tint_hex=to_hex(lin_to_srgb(sun_est), '#'),
        direct_light_cct_mccamy_K=None if cct is None else int(round(cct)),
        ambient_tint_basis=amb_basis,
        ground_probe_mean_linear=[r3(v) for v in ground_px], fog_probe_mean_srgb=[r3(v) for v in fog_px],
        image_median_luma=r3(median_l),
        sun_elevation_deg=pack['sun']['elevation_deg'], sun_elevation_basis=pack['sun']['basis'])
    derivation = dict(
        lit_shade_split='lit and shaded pixels are separated by large-scale illumination (blurred luminance), so texture contrast such as bright rootlets over dark crevices does not count as sunlight',
        sun_and_hemi='hemi = clip(1.9 - 0.3*log2(1 + direct/ambient), 0.9, 1.9); sun = clip(ratio*hemi*0.9, 0.4, 3.6). Calibrated so the three existing presets (overcast 0.55/1.9, soft 2.0/1.35, clear 3.3/0.9) are reproduced from their implied ratios.',
        hemiSky=hemi_sky_basis, hemiGround='ground probe mean, luma matched to the existing presets (0.19)',
        fog='far-background probe mean, luma matched to the existing presets (0.58)',
        turb_ray_mie=atmos_basis,
        exposure='clip(0.9 + (median luma - 0.35)*0.6, 0.85, 1.05): brighter photographs get a slightly higher exposure',
        sun_colour='the viewer keeps sun.color fixed (setHSL(.09,.28,.9)); the measured direct-light tint is reported for reference only')
    return preset, measurements, derivation

# ----------------------------------------------------------------------------- mood analysis
def kmeans(X, k, rng, iters=30):
    centres = [X[rng.integers(len(X))]]
    for _ in range(1, k):
        d = np.min(((X[:, None, :] - np.array(centres)[None]) ** 2).sum(-1), 1)
        centres.append(X[rng.choice(len(X), p=d / d.sum())])
    C = np.array(centres)
    for _ in range(iters):
        lab = ((X[:, None, :] - C[None]) ** 2).sum(-1).argmin(1)
        for c in range(k):
            sel = X[lab == c]
            if len(sel):
                C[c] = sel.mean(0)
    lab = ((X[:, None, :] - C[None]) ** 2).sum(-1).argmin(1)
    w = np.bincount(lab, minlength=k) / len(X)
    order = np.argsort(-w)
    return C[order], w[order]

def role_of(srgb):
    r, g, b = srgb
    L = luma(np.asarray(srgb))
    mx, mn = max(srgb), min(srgb)
    sat = (mx - mn) / max(mx, 1e-6)
    if L > 0.85 and sat < 0.15: return 'highlight / sky white'
    if b > r and b > g and L > 0.35: return 'sky'
    if g > r and g > b: return 'foliage / moss'
    if L < 0.12: return 'deep shadow'
    if r > b and sat > 0.2: return 'bark / earth / litter'
    return 'neutral'

def mood_analysis(srgb, mask, rng):
    px = srgb[mask]
    if len(px) > 250000:
        px = px[rng.choice(len(px), 250000, replace=False)]
    C, w = kmeans(px, 8, rng)
    L = luma(px)
    pct = {f'p{q}'.replace('.', '_'): r3(v) for q, v in zip([0.5, 2, 10, 25, 50, 75, 90, 98, 99.5], np.percentile(L, [0.5, 2, 10, 25, 50, 75, 90, 98, 99.5]))}
    mx, mn = px.max(-1), px.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.degrees(np.arctan2(math.sqrt(3) * (px[:, 1] - px[:, 2]), 2 * px[:, 0] - px[:, 1] - px[:, 2])) % 360
    hist, _ = np.histogram(hue, bins=12, range=(0, 360), weights=sat * mx)
    hist = hist / max(hist.sum(), 1e-9)
    dark = px[L <= np.percentile(L, 20)]
    bright = px[L >= np.percentile(L, 80)]
    shadow_tint = (dark - luma(dark)[:, None]).mean(0)
    highlight_tint = (bright - luma(bright)[:, None]).mean(0)
    stats = dict(luma_percentiles=pct, luma_mean=r3(L.mean()), luma_std=r3(L.std()),
                 mean_saturation=r3(sat.mean()), hue_histogram_12=[r3(v) for v in hist],
                 warm_cool_bias=r3((px[:, 0] - px[:, 2]).mean()),
                 shadow_tint=[r3(v) for v in shadow_tint], highlight_tint=[r3(v) for v in highlight_tint])
    palette = [dict(hex=to_hex(c, '#'), srgb=[r3(v) for v in c], linear=[r3(v) for v in srgb_to_lin(c)],
                    weight=r3(wi), role=role_of(c)) for c, wi in zip(C, w)]
    return palette, stats

def make_grade(stats):
    p = stats['luma_percentiles']
    black = min(p['p0_5'], 0.12)
    white = max(p['p99_5'], 0.85)
    median = p['p50']
    gamma = float(np.clip(math.log(max((median - black) / (white - black), 0.05)) / math.log(0.42), 0.6, 1.6))
    s_t = np.array(stats['shadow_tint'])
    h_t = np.array(stats['highlight_tint'])
    sat = float(np.clip(stats['mean_saturation'] / 0.40, 0.8, 1.25))
    def grade(rgb):
        rgb = np.asarray(rgb, np.float64)
        L = luma(rgb)
        Lo = black + (white - black) * np.power(np.clip(L, 0, 1), gamma)
        out = rgb + (Lo - L)[..., None]
        out = out + s_t * ((1 - L) ** 2)[..., None] * 0.8 + h_t * (L ** 2)[..., None] * 0.8
        L2 = luma(out)
        out = L2[..., None] + (out - L2[..., None]) * sat
        return np.clip(out, 0, 1)
    params = dict(black=r3(black), white=r3(white), gamma=r3(gamma), saturation=r3(sat),
                  shadow_tint=[r3(v) for v in s_t], highlight_tint=[r3(v) for v in h_t])
    return grade, params

def write_cube(path, grade, title, n=33):
    g = (np.arange(n) / (n - 1))
    B, G, R = np.meshgrid(g, g, g, indexing='ij')          # r fastest
    rgb = np.stack([R.ravel(), G.ravel(), B.ravel()], -1)
    out = grade(rgb)
    with open(path, 'w') as f:
        f.write(f'TITLE "{title}"\n')
        f.write(f'# Generated by {GENERATOR}. Domain: display-referred sRGB in, sRGB out.\n')
        f.write(f'LUT_3D_SIZE {n}\nDOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n')
        for r, gg, b in out:
            f.write(f'{r:.6f} {gg:.6f} {b:.6f}\n')
    # round-trip check: trilinear lookup of the written table against the function
    table = out.reshape(n, n, n, 3)
    test = np.random.default_rng(1).random((2000, 3))
    idx = test * (n - 1)
    i0 = np.floor(idx).astype(int).clip(0, n - 2)
    t = idx - i0
    acc = np.zeros((2000, 3))
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                wgt = (t[:, 0] if dx else 1 - t[:, 0]) * (t[:, 1] if dy else 1 - t[:, 1]) * (t[:, 2] if dz else 1 - t[:, 2])
                acc += wgt[:, None] * table[i0[:, 2] + dz, i0[:, 1] + dy, i0[:, 0] + dx]
    return float(np.abs(acc - grade(test)).max())

# ----------------------------------------------------------------------------- sheet
def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

def fit_into(img, w, h):
    s = min(w / img.width, h / img.height)
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)

def to_pil(arr):
    return Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8))

def draw_sheet(pack, out_path, thumb, regions_drawn, palette, stats, lighting, sky_img, sky_info, tiles, grade_pair, withheld):
    W, H = 4096, 2900
    sheet = Image.new('RGB', (W, H), (24, 26, 24))
    d = ImageDraw.Draw(sheet)
    f_big, f_mid, f_small = font(58), font(38), font(30)
    d.text((40, 30), f"{pack['id']}  -  {pack['title']}", fill=(240, 240, 235), font=f_big)
    d.text((40, 100), f"generated by {GENERATOR}; measurements and assumptions in {pack['id']}_manifest.json", fill=(170, 175, 170), font=f_small)
    # source thumbnail
    x0, y0 = 40, 160
    if withheld:
        d.rectangle([x0, y0, x0 + 820, y0 + 1100], outline=(120, 60, 60), width=4)
        d.text((x0 + 30, y0 + 40), 'source withheld', fill=(230, 120, 120), font=f_mid)
        d.text((x0 + 30, y0 + 100), 'licensed stock preview:\nno pixels reproduced', fill=(200, 200, 200), font=f_small)
    else:
        th = fit_into(thumb, 820, 1100)
        sheet.paste(th, (x0, y0))
        dd = ImageDraw.Draw(sheet)
        for name, quad, col in regions_drawn:
            pts = [(x0 + p[0] * th.width, y0 + p[1] * th.height) for p in quad]
            dd.polygon(pts, outline=col)
            dd.line(pts + [pts[0]], fill=col, width=3)
            dd.text((pts[0][0] + 4, pts[0][1] + 2), name, fill=col, font=font(22))
    # palette
    px0, py0 = 900, 160
    d.text((px0, py0), 'palette (k-means, weight)', fill=(220, 220, 215), font=f_small)
    for i, p in enumerate(palette):
        y = py0 + 50 + i * 120
        c = tuple(int(v * 255) for v in p['srgb'])
        d.rectangle([px0, y, px0 + 150, y + 100], fill=c)
        d.text((px0 + 165, y + 8), f"{p['hex']}  {p['weight']*100:.0f}%", fill=(230, 230, 225), font=f_small)
        d.text((px0 + 165, y + 50), p['role'], fill=(170, 175, 170), font=font(24))
    # stats + lighting text
    tx0, ty0 = 1340, 160
    lp = lighting['preset']
    m = lighting['measurements']
    lines = ['lighting preset (viewer/app.js PRESETS shape)',
             f"sun {lp['sun']}   hemi {lp['hemi']}   exposure {lp['exposure']}",
             f"hemiSky {lp['hemiSky']}   hemiGround {lp['hemiGround']}   fog {lp['fog']}",
             f"turbidity {lp['turb']}   rayleigh {lp['ray']}   mie {lp['mie']}",
             f"key:fill {m['key_to_fill_luminance_ratio']}   direct/ambient {m['direct_over_ambient']}   {m['classified_as']}",
             f"direct-light tint {m['direct_light_tint_hex']}   CCT ~{m['direct_light_cct_mccamy_K']} K (McCamy)",
             f"sun elevation {m['sun_elevation_deg']} deg (estimate: {m['sun_elevation_basis']})", '',
             'tonal statistics (sRGB luma)',
             f"median {stats['luma_percentiles']['p50']}   p2 {stats['luma_percentiles']['p2']}   p98 {stats['luma_percentiles']['p98']}   std {stats['luma_std']}",
             f"mean saturation {stats['mean_saturation']}   warm-cool bias {stats['warm_cool_bias']}",
             f"shadow tint {stats['shadow_tint']}", f"highlight tint {stats['highlight_tint']}", '']
    if sky_info:
        if sky_info.get('fit'):
            fs = sky_info['fit']
            lines += ['sky fit (Sky.js port)', f"pixels {sky_info['pixel_count']}   rms {fs['rms_srgb']:.3f}   sun az rel {fs['sun_azimuth_rel_deg']} deg   fit exposure {fs['fit_exposure']:.2f}",
                      f"zenith {sky_info.get('zenith_hex')}   horizon {sky_info.get('horizon_hex')}"]
        else:
            lines += ['sky: ' + sky_info.get('status', 'none')]
    y = ty0
    for ln in lines:
        if len(ln) > 78:
            ln = ln[:75] + '...'
        d.text((tx0, y), ln, fill=(225, 225, 220) if ln and not ln[0].islower() else (200, 205, 200), font=f_small)
        y += 44
    # histogram
    hy = ty0 + 46 * len(lines) + 20
    d.text((tx0, hy), 'luma histogram', fill=(220, 220, 215), font=f_small)
    hist = stats.get('_hist')
    if hist is not None:
        hh = 220
        for i, v in enumerate(hist):
            bh = int(v * hh)
            d.rectangle([tx0 + i * 15, hy + 50 + hh - bh, tx0 + i * 15 + 13, hy + 50 + hh], fill=(180, 185, 170))
    # sky image
    sx0, sy0 = 2400, 160
    if sky_img is not None:
        sheet.paste(sky_img.resize((1600, 800), Image.LANCZOS), (sx0, sy0))
        d.text((sx0, sy0 + 810), 'sky/  equirectangular dome, fitted parameters, viewer sun azimuth 155 deg', fill=(200, 205, 200), font=font(24))
    # grade demo
    if grade_pair is not None:
        before, after = grade_pair
        sheet.paste(fit_into(before, 790, 440), (sx0, sy0 + 850))
        sheet.paste(fit_into(after, 790, 440), (sx0 + 810, sy0 + 850))
        d.text((sx0, sy0 + 1295), 'mood/ grade_33.cube applied to renders/after_p4/C1_start_corridor.png (left: before, right: after)', fill=(200, 205, 200), font=font(24))
    # tiles
    ty = 1500
    d.text((40, ty - 50), 'tileable 4K sets (whole tile, then 1:1 crop of the albedo and the normal map)', fill=(220, 220, 215), font=f_small)
    for i, t in enumerate(tiles[:6]):
        cx = 40 + i * 676
        sheet.paste(t['tile'].resize((640, 640), Image.LANCZOS), (cx, ty))
        sheet.paste(t['crop'].resize((315, 315), Image.LANCZOS), (cx, ty + 650))
        sheet.paste(t['normal'].resize((315, 315), Image.LANCZOS), (cx + 325, ty + 650))
        d.text((cx, ty + 975), f"{t['category']}/{t['id']}", fill=(230, 230, 225), font=font(26))
        d.text((cx, ty + 1010), t['scale'], fill=(170, 175, 170), font=font(22))
    sheet.save(out_path, quality=86)

# ----------------------------------------------------------------------------- pack build
def hist_for_sheet(srgb, mask):
    L = luma(srgb[mask])
    h, _ = np.histogram(L, bins=64, range=(0, 1))
    return h / max(h.max(), 1)

def file_record(path, rel_root, pixels=None, extra=None):
    rec = dict(path=str(path.relative_to(rel_root)), bytes=path.stat().st_size, sha256=sha256_file(path))
    if pixels:
        rec['pixels'] = pixels
    if extra:
        rec.update(extra)
    return rec

def build_pack(pack, size, args, cfg_sha):
    t0 = time.time()
    withheld = pack['source']['redistribution'] == 'withheld'
    src_path = None
    for cand in ([Path(args.source_dir) / pack['source']['file']] if args.source_dir else []) + [SRC_DIR / pack['source']['file']]:
        if cand.exists():
            src_path = cand
            break
    if src_path is None:
        print(f"[{pack['id']}] source {pack['source']['file']} not found - skipped")
        return None
    out = OUT_ROOT / pack['id']
    out.mkdir(parents=True, exist_ok=True)
    img, src_rec = load_source(src_path)
    src_rec.update(pack['source'])
    H, W = img.shape[:2]
    rng = np.random.default_rng(20260922)
    print(f"[{pack['id']}] source {W}x{H} {src_rec['colour_handling']}")

    # analysis image: the print interior for the framed photograph, the whole frame otherwise
    if pack.get('analysis_quad'):
        aw, ah, _ = region_size(pack['analysis_quad'], W, H)
        ana = rectify(img, pack['analysis_quad'], aw, ah, order=1)
        ana_note = 'analysis restricted to the rectified print interior (analysis_quad)'
    else:
        ana, ana_note = img, 'analysis over the whole frame minus exclude_rects'
    excl_full = rect_mask(pack.get('exclude_rects'), W, H)
    ana_mask = ~rect_mask(pack.get('exclude_rects'), ana.shape[1], ana.shape[0]) if not pack.get('analysis_quad') else np.ones(ana.shape[:2], bool)
    files = {}

    # ---- sky
    sky_info, sky_img = None, None
    sky_dir = out / 'sky'
    if pack.get('sky_roi'):
        m = sky_mask(img, pack['sky_roi']) & ~excl_full
        n = int(m.sum())
        frac = n / (poly_mask(pack['sky_roi'], W, H).sum() + 1)
        if n >= 400 and frac >= 0.004:
            ys, xs = np.nonzero(m)
            sel = rng.choice(n, min(n, 600), replace=False)
            dirs = pixel_dirs(xs[sel].astype(float), ys[sel].astype(float), W, H, pack['camera']['focal_equiv_mm'], pack['camera']['pitch_deg'])
            rgb = img[ys[sel], xs[sel]].astype(np.float64)
            elev = np.degrees(np.arcsin(np.clip(dirs[:, 1], -1, 1)))
            fit = fit_sky(dirs, rgb, pack['sun']['elevation_deg'])
            bins = {}
            for lo in range(-10, 90, 5):
                s = (elev >= lo) & (elev < lo + 5)
                if s.sum() >= 5:
                    bins[f'{lo}..{lo+5}'] = dict(n=int(s.sum()), srgb=[r3(v) for v in rgb[s].mean(0)], hex=to_hex(rgb[s].mean(0), '#'))
            mean_srgb = rgb.mean(0)
            sky_info = dict(status='fitted', pixel_count=n, roi_fraction=r3(frac), mean_srgb=[r3(v) for v in mean_srgb], mean_hex=to_hex(mean_srgb, '#'),
                            sampled_pixels=int(len(sel)), elevation_bins_deg=bins,
                            elevation_range_deg=[r3(elev.min()), r3(elev.max())], fit=fit,
                            camera_model=dict(pack['camera'], focal_px=r3((math.hypot(W, H) / 2) / math.tan(math.atan(21.63 / pack['camera']['focal_equiv_mm'])))),
                            notes=['The sun azimuth relative to the camera is unknown; it was fitted on a 30 degree grid.',
                                   'fit_exposure absorbs the camera exposure and is not the preset exposure.',
                                   'The dome image is rendered with the viewer sun azimuth (155 deg) and the pack sun elevation.'])
        else:
            sky_info = dict(status=f'no usable sky pixels (found {n}, {frac*100:.2f}% of the sky ROI)', pixel_count=n)
    elif pack.get('sky_proxy'):
        px = probe_pixels(img, pack['sky_proxy'])
        px = px[luma(px) > np.percentile(luma(px), 80)]
        sky_info = dict(status='no sky visible; sky_proxy = brightest 20% of the canopy-gap region, used only for hemiSky tint',
                        mean_srgb=[r3(v) for v in px.mean(0)], mean_hex=to_hex(px.mean(0), '#'), pixel_count=int(len(px)))
    if sky_info and sky_info.get('status') == 'fitted':
        f = sky_info['fit']
        ground = with_luma(lin_to_srgb(srgb_to_lin(probe_pixels(img, pack['probes']['ground'], excl_full)).mean(0)), 0.30)
        horizon_dir = sun_dir_viewer(0.0)
        hz = sky_display(np.array([[math.cos(math.radians(65)), 0.02, math.sin(math.radians(65))]]), sun_dir_viewer(pack['sun']['elevation_deg']), f['turb'], f['ray'], f['mie'], f['fit_exposure'])[0]
        zen = sky_display(np.array([[0.0, 1.0, 0.0]]), sun_dir_viewer(pack['sun']['elevation_deg']), f['turb'], f['ray'], f['mie'], f['fit_exposure'])[0]
        sky_info['horizon_hex'], sky_info['zenith_hex'] = to_hex(hz, '#'), to_hex(zen, '#')
        sky_dir.mkdir(exist_ok=True)
        dome = render_equirect(size, size // 2, pack['sun']['elevation_deg'], f['turb'], f['ray'], f['mie'], f['fit_exposure'], ground, hz)
        sky_img = to_pil(dome)
        p = sky_dir / f"{pack['id']}_sky_equirect_{size // 1024}k.jpg"
        sky_img.save(p, quality=88, subsampling=0)
        files['sky_equirect'] = file_record(p, OUT_ROOT, [size, size // 2], dict(
            mapping='three.js EquirectangularReflectionMapping (u = atan2(z, x)/2pi + 0.5, v = asin(y)/pi + 0.5, top row = zenith)',
            content='upper hemisphere: Sky.js port with fitted parameters through ACES filmic and sRGB; lower hemisphere: ground probe colour, darkened downward',
            colorSpace='sRGB (display-referred, LDR)'))
    if sky_info:
        sky_dir.mkdir(exist_ok=True)
        p = sky_dir / 'sky.json'
        p.write_text(json.dumps(sky_info, indent=2))
        files['sky_json'] = file_record(p, OUT_ROOT)
    print(f"[{pack['id']}] sky: {sky_info['status'] if sky_info else 'none'}  ({time.time()-t0:.0f}s)")

    # ---- lighting
    preset, meas, deriv = lighting_analysis(img, pack, sky_info, excl_full)
    ldir = out / 'lighting'
    ldir.mkdir(exist_ok=True)
    lighting = dict(preset=preset, measurements=meas, derivation=deriv,
                    usage='Add the preset object to PRESETS in viewer/app.js (see preset_snippet.js). Values are calibrated to the existing presets, not absolute radiometry.')
    p = ldir / 'lighting_preset.json'
    p.write_text(json.dumps(lighting, indent=2))
    files['lighting_json'] = file_record(p, OUT_ROOT)
    js = (f"// photo-derived daylight preset from {GENERATOR}; paste into PRESETS in viewer/app.js\n"
          f"{pack['id']}:{{label:{json.dumps(preset['label'])},sun:{preset['sun']},hemi:{preset['hemi']},hemiSky:{preset['hemiSky']},"
          f"hemiGround:{preset['hemiGround']},turb:{preset['turb']},ray:{preset['ray']},mie:{preset['mie']},fog:{preset['fog']},exposure:{preset['exposure']}}},\n")
    p = ldir / 'preset_snippet.js'
    p.write_text(js)
    files['preset_snippet'] = file_record(p, OUT_ROOT)
    print(f"[{pack['id']}] lighting: sun {preset['sun']} hemi {preset['hemi']} key:fill {meas['key_to_fill_luminance_ratio']}")

    # ---- mood
    palette, stats = mood_analysis(ana, ana_mask, rng)
    grade, gparams = make_grade(stats)
    mdir = out / 'mood'
    mdir.mkdir(exist_ok=True)
    cube = mdir / 'grade_33.cube'
    lut_err = write_cube(cube, grade, f"{pack['id']} mood grade")
    mood = dict(palette=palette, tonal=stats, grade=dict(file='grade_33.cube', parameters=gparams, lut_roundtrip_max_error=r3(lut_err),
                derivation='black/white from the 0.5/99.5 luma percentiles (limited to 0.12/0.85), gamma so that input 0.42 maps to the photo median, split-toning with the measured shadow/highlight tints, saturation relative to 0.40 mean HSV saturation',
                usage='three.js LUTCubeLoader + LUTPass on the tone-mapped frame, or any .cube-aware grading tool'),
                analysis_region=ana_note)
    p = mdir / 'mood.json'
    p.write_text(json.dumps(mood, indent=2))
    files['mood_json'] = file_record(p, OUT_ROOT)
    files['grade_cube'] = file_record(cube, OUT_ROOT)
    stats['_hist'] = hist_for_sheet(ana, ana_mask)
    grade_pair = None
    if GRADE_DEMO_RENDER.exists():
        before = Image.open(GRADE_DEMO_RENDER).convert('RGB')
        before = fit_into(before, 1000, 700)
        after = to_pil(grade(np.asarray(before).astype(np.float64) / 255))
        grade_pair = (before, after)
    print(f"[{pack['id']}] mood: {len(palette)} colours, lut err {lut_err:.4f}  ({time.time()-t0:.0f}s)")

    # ---- materials
    tiles, material_records = [], []
    regions_drawn = []
    if withheld and not args.include_withheld:
        print(f"[{pack['id']}] materials withheld (licensed stock preview); pass --include-withheld with a licensed original to build them locally")
    for mat in pack['materials']:
        tm = time.time()
        cyl = bool(mat.get('cylinder'))
        sy = float(mat.get('stretch_y', 1.0))
        cp = CLASS_PARAMS[mat['class']]
        rw0, rh0, native = region_size(mat['quad'], W, H, 1.0, sy, cyl)
        native_ppm = native[0] / mat['physical_width_m']
        # enlarge the source towards the class's intended tile scale, within the cap and the search budget
        up = (size / cp['tile_m']) / native_ppm
        up = float(min(max(up, 1.0), UPSCALE_CAP, math.sqrt(MAX_SOURCE_MEGAPIXELS * 1e6 / (rw0 * rh0))))
        rw, rh, native = region_size(mat['quad'], W, H, up, sy, cyl)
        step, patch, ov, extra = choose_quilt_params(rh, rw, size)
        if extra > 1.0:
            up *= extra
            rw, rh, native = region_size(mat['quad'], W, H, up, sy, cyl)
        region = rectify(img, mat['quad'], rw, rh, cylinder=cyl)
        flat, sigma_px = delight(region, mat.get('delight_sigma', 0.25), mat.get('delight_strength', 1.0))
        mirror = bool(mat.get('mirror', True))
        tile = quilt(flat, size, patch, ov, rng, mirror=mirror)
        grain = GRAIN_AMOUNT if up > 1.5 else 0.0
        if grain:
            tile = add_grain(tile, grain, rng)
        maps = derive_maps(tile, mat['class'], size)
        mdir_ = out / mat['category']
        saved = save_maps(tile, maps, mdir_, mat['id'], size)
        px_per_m = native_ppm * up
        tile_m = size / px_per_m
        rec = dict(id=mat['id'], category=mat['category'], material_class=mat['class'], notes=mat.get('notes', ''),
                   region=dict(quad_normalised=mat['quad'], native_pixels=[r3(native[0]), r3(native[1])], cylinder_unwrap=cyl,
                               upscale=r3(up), stretch_y=sy, rectified_pixels=[rw, rh], delight_sigma_px=r3(sigma_px)),
                   synthesis=dict(method='Efros-Freeman image quilting on a torus (seamless in x and y)' + ('; candidates drawn from the source and its horizontal mirror' if mirror else '; no mirroring (oriented structure)'),
                                  patch=patch, overlap=ov, step=step, patches=(size // step) ** 2, candidate_tolerance=0.15, min_candidates=30, reuse_penalty=0.6, mirror=mirror, seed=20260922),
                   physical_scale=dict(assumed_region_width_m=mat['physical_width_m'], tile_width_m=r3(tile_m),
                                       texels_per_metre=r3(size / tile_m), source_texels_per_metre=r3(native_ppm),
                                       intended_tile_m=cp['tile_m'],
                                       note='region width is an estimate; the tile scale follows from it. Detail above source_texels_per_metre is interpolation, not observation.'),
                   synthetic_micro_grain=dict(amount=grain, reason='the source was enlarged before synthesis; a 3 % periodic grain masks interpolation blur and is not observed detail') if grain else None,
                   maps=dict(diff='sRGB albedo, illumination flattened (large-scale shading and colour drift divided out); the photograph\'s illuminant is NOT neutralised',
                             nor_gl='OpenGL tangent-space normal derived from the luminance height proxy (not a scanned surface)',
                             rough=f"heuristic: {CLASS_PARAMS[mat['class']]['rough']} base for class '{mat['class']}', modulated by fine luminance",
                             height='luminance band mix (fine/mid/coarse), percentile-normalised; dark = low. Ambient occlusion, if wanted, is 1 - k*max(0, blur(height) - height) at two radii'),
                   files={k: file_record(v, OUT_ROOT, [size, size]) for k, v in saved.items()},
                   seconds=int(time.time() - tm))
        material_records.append(rec)
        regions_drawn.append((mat['id'], mat['quad'], (255, 220, 60)))
        crop = tile[size // 2 - 200:size // 2 + 200, size // 2 - 200:size // 2 + 200]
        tiles.append(dict(id=mat['id'], category=mat['category'], tile=to_pil(tile), crop=to_pil(crop),
                          normal=Image.fromarray(maps['normal'][size // 2 - 200:size // 2 + 200, size // 2 - 200:size // 2 + 200]),
                          scale=f"tile ~{tile_m:.2f} m, {size / tile_m:.0f} texel/m"))
        print(f"[{pack['id']}] {mat['category']}/{mat['id']}: region {rw}x{rh} (native {native[0]:.0f}x{native[1]:.0f}, up {up:.2f}) patch {patch}/{ov} -> {size}  ({time.time()-tm:.0f}s)")
        del maps, tile, flat, region
    for name in ('lit_shadow', 'ground', 'fog'):
        regions_drawn.append((f'probe:{name}', pack['probes'][name], (90, 200, 255)))
    if pack.get('sky_roi'):
        regions_drawn.append(('sky roi', pack['sky_roi'], (200, 120, 255)))

    # ---- sheet + manifest
    thumb = to_pil(img) if not withheld else None
    sheet_path = out / f"{pack['id']}_sheet_{size // 1024}k.jpg"
    draw_sheet(pack, sheet_path, thumb, regions_drawn, palette, stats, lighting, sky_img, sky_info, tiles, grade_pair, withheld)
    files['sheet'] = file_record(sheet_path, OUT_ROOT, [4096, 2900])
    manifest = dict(
        pack=pack['id'], title=pack['title'], generator=GENERATOR, generated='2026-09-22', config_sha256=cfg_sha, tile_size=size,
        status=('MEASUREMENTS ONLY. Pixel-derived textures withheld: the source is a watermarked licensed stock preview.' if withheld else
                'PHOTO-DERIVED REPRESENTATIVES. Textures are synthesised from regions of one photograph; the photograph was not taken at Aokigahara unless stated.'),
        source=dict(src_rec, committed_copy=None if withheld else f"asset_packs/_sources/{pack['source']['file']}", exif_gps='none present'),
        camera_estimate=pack['camera'], sun_estimate=pack['sun'], analysis=ana_note,
        sky=sky_info, lighting=lighting, mood=dict(palette=palette, tonal={k: v for k, v in stats.items() if not k.startswith('_')}, grade=mood['grade']),
        materials=material_records, files=files,
        not_claimed=['No map is a scanned or photogrammetric surface: normal, roughness, height and AO are heuristics from image luminance.',
                     'Albedo keeps the photograph\'s illuminant and white balance; only large-scale shading was flattened.',
                     'Sky parameters are a fit to a handful of sky pixels with an unknown sun azimuth; sun elevation is a visual estimate.',
                     'Lighting preset numbers are calibrated to the viewer\'s existing presets, not to measured radiometry.',
                     'Physical scales rest on an estimated region width.',
                     'Species, site and season are not established by any of this.'])
    mp = out / f"{pack['id']}_manifest.json"
    mp.write_text(json.dumps(manifest, indent=2))
    print(f"[{pack['id']}] done in {time.time()-t0:.0f}s -> {out}")
    return manifest

def preview(cfg, args):
    """Region check: rectified + flattened regions and the sky mask, per pack, into the scratch dir."""
    outdir = Path(args.preview_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    for pack in cfg['packs']:
        if args.pack and pack['id'] != args.pack:
            continue
        src = None
        for cand in ([Path(args.source_dir) / pack['source']['file']] if args.source_dir else []) + [SRC_DIR / pack['source']['file']]:
            if cand.exists():
                src = cand
        if src is None:
            print('missing', pack['id']); continue
        img, _ = load_source(src)
        H, W = img.shape[:2]
        panels = []
        for mat in pack['materials']:
            cyl = bool(mat.get('cylinder'))
            rw, rh, native = region_size(mat['quad'], W, H, float(mat.get('upscale', 1.0)), float(mat.get('stretch_y', 1.0)), cyl)
            region = rectify(img, mat['quad'], rw, rh, cylinder=cyl)
            flat, _ = delight(region, mat.get('delight_sigma', 0.25))
            a = fit_into(to_pil(region), 600, 700); b = fit_into(to_pil(flat), 600, 700)
            pnl = Image.new('RGB', (a.width + b.width + 20, max(a.height, b.height) + 40), (30, 30, 30))
            pnl.paste(a, (0, 40)); pnl.paste(b, (a.width + 20, 40))
            ImageDraw.Draw(pnl).text((4, 6), f"{mat['id']} {rw}x{rh} native {native[0]:.0f}x{native[1]:.0f}", fill=(255, 255, 0), font=font(24))
            panels.append(pnl)
        th = fit_into(to_pil(img), 700, 900)
        ov = np.asarray(th).copy()
        if pack.get('sky_roi'):
            m = sky_mask(img, pack['sky_roi'])
            ms = np.asarray(Image.fromarray(m.astype(np.uint8) * 255).resize(th.size, Image.NEAREST)) > 0
            ov[ms] = (ov[ms] * 0.3 + np.array([255, 0, 255]) * 0.7).astype(np.uint8)
            print(pack['id'], 'sky pixels', int(m.sum()))
        ovi = Image.fromarray(ov)
        dd = ImageDraw.Draw(ovi)
        for name in ('lit_shadow', 'ground', 'fog'):
            pts = [(p[0] * th.width, p[1] * th.height) for p in pack['probes'][name]]
            dd.line(pts + [pts[0]], fill=(90, 200, 255), width=2); dd.text(pts[0], name, fill=(90, 200, 255), font=font(20))
        if pack.get('analysis_quad'):
            pts = [(p[0] * th.width, p[1] * th.height) for p in pack['analysis_quad']]
            dd.line(pts + [pts[0]], fill=(255, 80, 80), width=2)
        panels.insert(0, ovi)
        tw = sum(p.width for p in panels) + 20 * len(panels)
        thh = max(p.height for p in panels)
        sheet = Image.new('RGB', (tw, thh), (20, 20, 20))
        x = 0
        for p in panels:
            sheet.paste(p, (x, 0)); x += p.width + 20
        sheet.save(outdir / f"preview_{pack['id']}.jpg", quality=85)
        print('wrote', outdir / f"preview_{pack['id']}.jpg", sheet.size)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--pack', help='build only this pack id')
    ap.add_argument('--size', type=int, default=None, help='tile size (default from config, 4096)')
    ap.add_argument('--source-dir', help='extra directory searched for source photographs (e.g. a withheld original)')
    ap.add_argument('--include-withheld', action='store_true', help='also synthesise textures for packs marked redistribution=withheld')
    ap.add_argument('--preview', action='store_true', help='write region-check sheets only')
    ap.add_argument('--preview-dir', default=str(ROOT / 'work/asset_packs_preview'))
    args = ap.parse_args()
    cfg = json.loads(CONFIG.read_text())
    cfg_sha = sha256_file(CONFIG)
    if args.preview:
        preview(cfg, args)
        return
    size = args.size or cfg['size']
    OUT_ROOT.mkdir(exist_ok=True)
    built = []
    for pack in cfg['packs']:
        if args.pack and pack['id'] != args.pack:
            continue
        m = build_pack(pack, size, args, cfg_sha)
        if m:
            built.append(m)
    # global manifest
    gp = OUT_ROOT / 'PACKS_MANIFEST.json'
    existing = json.loads(gp.read_text()) if gp.exists() else dict(packs={})
    for m in built:
        existing['packs'][m['pack']] = dict(title=m['title'], status=m['status'], manifest=f"asset_packs/{m['pack']}/{m['pack']}_manifest.json",
                                            source=m['source'].get('committed_copy'), source_sha256=m['source']['sha256'],
                                            redistribution=m['source']['redistribution'], tile_size=m['tile_size'],
                                            materials=[f"{r['category']}/{r['id']}" for r in m['materials']],
                                            files=sum(1 for _ in m['files']) + sum(len(r['files']) for r in m['materials']))
    existing.update(dict(generator=GENERATOR, config='construction_code_v2/asset_packs_config.json', config_sha256=cfg_sha,
                         generated='2026-09-22', schemaVersion=1))
    gp.write_text(json.dumps(existing, indent=2))
    print('wrote', gp)

if __name__ == '__main__':
    main()
