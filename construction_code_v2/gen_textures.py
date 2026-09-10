"""Procedural PBR texture set for the Aokigahara near-field ground system.
All outputs are PROCEDURAL representatives constrained by descriptive evidence
(moss carpets over blocky/ropy Jogan lava, exposed dark basalt, conifer needle/scale litter).
They are NOT photogrammetric captures from Aokigahara. Deterministic (fixed seeds).
"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parents[1] / 'viewer/assets/materials_v2'
OUT.mkdir(parents=True, exist_ok=True)
N = 1024

def tile_noise(rng, n, freq, octaves=5, persistence=0.55, lacunarity=2.0):
    """Seamless (tileable) fractal value noise in [0,1]."""
    total = np.zeros((n, n)); amp = 1.0; norm = 0.0; f = freq
    for _ in range(octaves):
        cells = max(2, int(round(f)))
        g = rng.random((cells, cells))
        # periodic bicubic-ish upsample via FFT-safe zoom on tiled grid
        big = np.tile(g, (3, 3))
        z = ndimage.zoom(big, n / cells, order=3, mode='wrap')
        s = n  # crop the central tile
        z = z[s:2*s, s:2*s]
        total += amp * z; norm += amp; amp *= persistence; f *= lacunarity
    t = total / norm
    return (t - t.min()) / (t.max() - t.min() + 1e-9)

def worley(rng, n, cells, seed_jitter=1.0):
    """Tileable Worley (cellular) distance field, normalised; also returns nearest-cell id."""
    pts = (np.indices((cells, cells)).transpose(1, 2, 0).reshape(-1, 2) + rng.random((cells*cells, 2)) * seed_jitter) / cells
    yy, xx = np.mgrid[0:n, 0:n] / n
    best = np.full((n, n), 9.0); second = np.full((n, n), 9.0); cid = np.zeros((n, n), dtype=np.int32)
    for k, (py, px) in enumerate(pts):
        dy = np.abs(yy - py); dy = np.minimum(dy, 1 - dy)
        dx = np.abs(xx - px); dx = np.minimum(dx, 1 - dx)
        d = np.sqrt(dx*dx + dy*dy)
        m = d < best; second[m] = best[m]; best[m] = d[m]; cid[m] = k
        m2 = (~m) & (d < second); second[m2] = d[m2]
    worley.f2 = second / best.max()
    best /= best.max()
    return best, cid

def height_to_normal(h, strength=1.0):
    gy, gx = np.gradient(h)
    nx = -gx * strength; ny = -gy * strength; nz = np.ones_like(h)
    l = np.sqrt(nx*nx + ny*ny + nz*nz)
    # OpenGL convention: +Y up in tangent space; image rows go down -> flip y
    n = np.stack([nx/l, -ny/l, nz/l], -1)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)

def save_rgb(arr, name, quality=90):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(OUT / name, quality=quality, subsampling=0)

def save_gray(arr, name):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('L').save(OUT / name, quality=88)

# ---------------- MOSS (feather/cushion moss carpet, ~1.0 m tile) ----------------
def moss():
    rng = np.random.default_rng(101)
    c1, cid = worley(rng, N, 22); c1 = (1 - c1)**1.4      # cushion clumps ~5 cm
    c2, _ = worley(rng, N, 9); c2 = (1 - c2)**1.2          # larger hummocks ~11 cm
    c3, _ = worley(rng, N, 50); c3 = (1 - c3)**2.0         # small shoots ~2 cm
    fine = tile_noise(rng, N, 48, 5, 0.6)          # fibrous shoot structure
    fine2 = tile_noise(rng, N, 140, 3, 0.5)
    macro = tile_noise(rng, N, 3, 4, 0.55)         # thickness variation across the tile
    dead = tile_noise(rng, N, 6, 4, 0.5)           # brown, drying patches
    mixmask = tile_noise(rng, N, 2, 3, 0.5)
    cushion = c1*(1-mixmask) + c2*mixmask
    h = 0.42*cushion + 0.18*c3 + 0.25*fine + 0.15*fine2
    h = h * (0.6 + 0.4*macro)
    h = (h - h.min()) / (h.max() - h.min())
    # colour: valleys darker & bluer green; peaks lighter yellow-green; dead patches brown
    dark = np.array([0.05, 0.085, 0.03]); light = np.array([0.26, 0.36, 0.10]); brown = np.array([0.30, 0.22, 0.09])
    t = np.clip(h**1.3, 0, 1)[..., None]
    col = dark*(1-t) + light*t
    hue_var = tile_noise(rng, N, 5, 3, 0.5)[..., None]
    col = col * (0.85 + 0.3*hue_var)                       # patchy vigour
    dm = np.clip((dead - 0.66) * 4, 0, 1)[..., None] * 0.55
    col = col*(1-dm) + brown*dm
    # tiny needle litter on top of the moss
    lit = tile_noise(rng, N, 160, 2, 0.5)
    lm = np.clip((lit - 0.80) * 6, 0, 1)[..., None] * (0.35 + 0.65*(1-t))
    col = col*(1-lm) + np.array([0.28, 0.19, 0.08])*lm
    alb = (np.clip(col, 0, 1)**(1/2.2)) * 255
    save_rgb(alb, 'moss_diff_1k.jpg')
    # normal: cushions + fibres
    Image.fromarray(height_to_normal(h * 22 + fine * 4, 1.0)).save(OUT / 'moss_nor_gl_1k.jpg', quality=92, subsampling=0)
    rough = 0.92 - 0.10*t[..., 0] + 0.05*(fine-0.5)
    save_gray(rough * 255, 'moss_rough_1k.jpg')
    save_gray(h * 255, 'moss_height_1k.jpg')
    return h

# ---------------- BASALT / JOGAN LAVA (blocky clinker + vesicles + local ropy folds, ~1.5 m tile) ----------------
def basalt():
    rng = np.random.default_rng(202)
    src = Path(__file__).resolve().parents[1] / 'viewer/assets/materials'
    diff = np.asarray(Image.open(src / 'rock_3_diff_1k.jpg').convert('RGB').resize((N, N))).astype(np.float32) / 255
    rough = np.asarray(Image.open(src / 'rock_3_rough_1k.jpg').convert('L').resize((N, N))).astype(np.float32) / 255
    nor = np.asarray(Image.open(src / 'rock_3_nor_gl_1k.jpg').convert('RGB').resize((N, N))).astype(np.float32) / 255 * 2 - 1
    lum = diff.mean(-1)
    lum = (lum - lum.min()) / (lum.max() - lum.min())
    # blocky clinker: cellular blocks with cracks between
    blocks, cid = worley(rng, N, 7); f2 = worley.f2
    seam0 = np.clip(1 - (f2 - blocks) * 9, 0, 1)**2               # seams between clinker blocks
    # domain-warp the seam field so fractures are jagged, not a clean Voronoi paving
    wx = (tile_noise(rng, N, 18, 3, 0.5) - 0.5) * 60; wy = (tile_noise(rng, N, 18, 3, 0.5) - 0.5) * 60
    wx += (tile_noise(rng, N, 90, 2, 0.5) - 0.5) * 10; wy += (tile_noise(rng, N, 90, 2, 0.5) - 0.5) * 10
    yy, xx = np.mgrid[0:N, 0:N]
    seam = ndimage.map_coordinates(seam0, [(yy + wy) % N, (xx + wx) % N], order=1, mode='wrap')
    cid = ndimage.map_coordinates(cid.astype(np.float32), [(yy + wy) % N, (xx + wx) % N], order=0, mode='wrap').astype(np.int32)
    seam *= np.clip((tile_noise(rng, N, 5, 3, 0.5) - 0.25) * 2.2, 0, 1)   # some seams fade out / blocks merge
    fine_cracks = np.clip(1 - np.abs(tile_noise(rng, N, 40, 4, 0.5) - 0.5) * 22, 0, 1)**3 * 0.6
    crackmask = np.clip(seam + fine_cracks, 0, 1)
    blockshade = (np.take(rng.random(64*64), cid % 4096) - 0.5)   # per-block brightness/tilt
    blockshade = ndimage.gaussian_filter(blockshade, 1.5, mode='wrap')
    vesicle = tile_noise(rng, N, 220, 2, 0.5)
    pits = np.clip((vesicle - 0.78) * 7, 0, 1)
    ropy = np.sin((np.mgrid[0:N, 0:N][0] / N * 2*np.pi * 14) + 3.0*tile_noise(rng, N, 4, 3, 0.5)*2*np.pi)  # folds
    ropymask = np.clip((tile_noise(rng, N, 2.5, 3, 0.5) - 0.55) * 4, 0, 1)
    # colour: dark grey basalt, slight rusty/brown iron staining, lichen-grey speckles
    base = np.array([0.055, 0.053, 0.052]); rust = np.array([0.17, 0.11, 0.07]); lichen = np.array([0.30, 0.32, 0.26])
    stain = tile_noise(rng, N, 4, 4, 0.55)
    col = base[None, None] * (0.6 + 0.9*lum[..., None])
    col = col*(1 - 0.5*stain[..., None]) + rust*0.5*stain[..., None]*0.6
    lich = np.clip((tile_noise(rng, N, 90, 3, 0.5) - 0.74) * 5, 0, 1)[..., None]
    col = col*(1-lich*0.35) + lichen*lich*0.35
    col = col*(1 + 0.35*blockshade[..., None])
    col = col * (1 - 0.7*pits[..., None]) * (1 - 0.3*crackmask[..., None])
    col = col * (1 + 0.25*ropy[..., None]*ropymask[..., None])
    alb = (np.clip(col, 0, 1)**(1/2.2)) * 255
    save_rgb(alb, 'basalt_diff_1k.jpg')
    # combine normals: source rock relief + pits + cracks + ropy folds
    h_extra = -pits*6 - crackmask*14 + ropy*ropymask*5 + blockshade*6
    n2 = height_to_normal(h_extra, 1.0).astype(np.float32)/255*2-1
    n = nor + n2; n[..., 2] = nor[..., 2]*n2[..., 2]; n /= np.linalg.norm(n, axis=-1, keepdims=True)
    Image.fromarray(((n*0.5+0.5)*255).astype(np.uint8)).save(OUT / 'basalt_nor_gl_1k.jpg', quality=92, subsampling=0)
    save_gray((np.clip(rough*0.6 + 0.35 + 0.1*pits, 0, 1)) * 255, 'basalt_rough_1k.jpg')

# ---------------- CONIFER LITTER (hemlock needles, hinoki scale sprays, twigs, humus; ~0.8 m tile) ----------------
def litter():
    rng = np.random.default_rng(303)
    humus = tile_noise(rng, N, 24, 5, 0.6)
    base = np.array([0.10, 0.075, 0.045])
    mott = tile_noise(rng, N, 120, 3, 0.5)
    col = base[None, None] * (0.55 + 0.9*humus[..., None]) * (0.8 + 0.4*mott[..., None])
    hgt = humus * 0.25
    # draw needles as short strokes (tileable by wrapping)
    from PIL import ImageDraw
    canvas = Image.fromarray((np.clip(col, 0, 1)**(1/2.2)*255).astype(np.uint8))
    hcanvas = Image.fromarray((hgt*255).astype(np.uint8)).convert('L')
    d = ImageDraw.Draw(canvas); dh = ImageDraw.Draw(hcanvas)
    palette = [(96, 70, 38), (110, 80, 44), (84, 60, 34), (122, 88, 48), (78, 54, 30), (104, 74, 44), (66, 50, 30), (90, 72, 40)]
    scale_px = N / 0.8  # px per metre
    for i in range(42000):
        x, y = rng.random(2) * N
        L = rng.uniform(0.008, 0.018) * scale_px     # 0.8–1.8 cm needles
        a = rng.uniform(0, np.pi)
        dx, dy = np.cos(a)*L/2, np.sin(a)*L/2
        c = palette[rng.integers(len(palette))]
        w = 1 if rng.random()<0.8 else 2
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                d.line([(x-dx+ox, y-dy+oy), (x+dx+ox, y+dy+oy)], fill=c, width=w)
                dh.line([(x-dx+ox, y-dy+oy), (x+dx+ox, y+dy+oy)], fill=int(90 + rng.integers(0, 80)), width=w)
    # hinoki scale sprays: small fan of 4-6 short strokes, greenish-brown when fresh
    for i in range(700):
        x, y = rng.random(2) * N; a0 = rng.uniform(0, 2*np.pi)
        c = (88, 96, 40) if rng.random() < 0.35 else (110, 80, 40)
        for k in range(5):
            a = a0 + (k-2)*0.35; L = rng.uniform(0.02, 0.04)*scale_px
            for ox in (-N, 0, N):
                for oy in (-N, 0, N):
                    d.line([(x+ox, y+oy), (x+np.cos(a)*L+ox, y+np.sin(a)*L+oy)], fill=c, width=2)
                    dh.line([(x+ox, y+oy), (x+np.cos(a)*L+ox, y+np.sin(a)*L+oy)], fill=150, width=2)
    # twigs
    for i in range(160):
        x, y = rng.random(2) * N; a = rng.uniform(0, np.pi); L = rng.uniform(0.05, 0.16)*scale_px
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                d.line([(x+ox, y+oy), (x+np.cos(a)*L+ox, y+np.sin(a)*L+oy)], fill=(70, 52, 34), width=int(rng.integers(2, 5)))
                dh.line([(x+ox, y+oy), (x+np.cos(a)*L+ox, y+np.sin(a)*L+oy)], fill=210, width=int(rng.integers(2, 5)))
    canvas.save(OUT / 'litter_diff_1k.jpg', quality=90, subsampling=0)
    h = np.asarray(hcanvas).astype(np.float32) / 255
    h = ndimage.gaussian_filter(h, 0.7, mode='wrap')
    Image.fromarray(height_to_normal(h * 9, 1.0)).save(OUT / 'litter_nor_gl_1k.jpg', quality=92, subsampling=0)
    save_gray((0.86 + 0.1*(h-0.5)) * 255, 'litter_rough_1k.jpg')

# ---------------- COMPACTED TRAIL SURFACE (~1 m tile): worn cinder/soil with small stones ----------------
def trail():
    rng = np.random.default_rng(404)
    n1 = tile_noise(rng, N, 12, 5, 0.6); n2 = tile_noise(rng, N, 90, 3, 0.5)
    stones = worley(rng, N, 70)[0]
    st = np.clip((0.16 - stones) * 10, 0, 1) * (tile_noise(rng, N, 5, 3, 0.5) > 0.6) * 0.6
    ruts = tile_noise(rng, N, 3, 2, 0.5)
    base = np.array([0.105, 0.085, 0.062])
    col = base[None, None]*(0.55 + 0.9*n1[..., None])*(0.8 + 0.4*n2[..., None])*(0.85 + 0.3*ruts[..., None])
    col = col*(1-st[..., None]) + np.array([0.16, 0.15, 0.13])*st[..., None]*(0.7+0.6*n2[..., None])
    save_rgb((np.clip(col, 0, 1)**(1/2.2))*255, 'trail_diff_1k.jpg')
    Image.fromarray(height_to_normal(n1*4 + n2*2 + st*3, 1.0)).save(OUT / 'trail_nor_gl_1k.jpg', quality=92, subsampling=0)
    save_gray((0.93 - 0.08*st)*255, 'trail_rough_1k.jpg')

# ---------------- ANTI-TILING / BLEND MASK NOISE (world-space, 32 m tile) ----------------
def masknoise():
    rng = np.random.default_rng(505)
    a = tile_noise(rng, 512, 3, 5, 0.55); b = tile_noise(rng, 512, 7, 4, 0.5); c = tile_noise(rng, 512, 16, 3, 0.5)
    Image.fromarray((np.stack([a, b, c], -1)*255).astype(np.uint8)).save(OUT / 'blend_noise_512.png')

if __name__ == '__main__':
    moss(); print('moss'); basalt(); print('basalt'); litter(); print('litter'); trail(); print('trail'); masknoise(); print('mask')
    import json
    (OUT / 'MATERIALS_V2_MANIFEST.json').write_text(json.dumps({
        'generator': 'construction_code_v2/gen_textures.py', 'deterministic_seeds': [101, 202, 303, 404, 505],
        'status': 'PROCEDURAL representatives. Not captured at Aokigahara. Derived inputs: Poly Haven rock_3 (CC0) relief/roughness reused inside basalt maps; everything else synthesised.',
        'physical_scale_m': {'moss': 1.0, 'basalt': 1.5, 'litter': 0.8, 'trail': 1.0, 'blend_noise': 32.0},
        'evidence_basis': ['GEO-002: Jogan products include aa and pahoehoe surfaces (blocky clinker and ropy folds)', 'IMG-007/008/013, ECO-016: moss carpets of varying thickness over irregular lava, roots gripping rock, litter collecting between roots', 'ECO-029: rope-like lava at Fugaku'],
        'not_claimed': 'Moss species, exact colours, litter composition and lava micro-form are interpretive.'
    }, indent=2))
