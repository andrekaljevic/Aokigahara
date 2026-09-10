"""Procedural broadleaf foliage atlas for the Aokigahara deciduous component.

The reconstruction inherited only conifer foliage: a Poly Haven fir twig atlas standing in for
Tsuga and Chamaecyparis sprays. The deciduous broadleaved community the underlying vegetation
survey distinguishes had no foliage source at all, so Pass-1 broadleaf trees used untextured
flat-coloured geometry. This builds the missing source.

Output: viewer/assets/materials_v2/broadleaf_atlas.png  (1024x1024 RGBA)
        viewer/assets/materials_v2/broadleaf_atlas_nor_gl.png
        viewer/assets/materials_v2/broadleaf_atlas_rough.jpg
        construction_code_v2/broadleaf_atlas_boxes.json  (pixel boxes for the card sampler)

Each box holds one leafy BRANCHLET: a main axis carrying lateral shoots, each with its own small
leaves, drawn stem-at-bottom so it matches the card UV convention in generate_trees_v2.py (v runs
from v1 at the stem to v0 at the tip). A branchlet rather than a single shoot because the runtime
card is about a metre across, so a box holding a handful of large leaves puts each lamina at a
third of a metre — several times life size, and obvious at eye level.

STATUS: PROCEDURAL. These are representative deciduous leaves. They are not a scan, not a species
determination, and not captured at Aokigahara. Leaf outline, venation, colour spread and shoot
arrangement are interpretive, informed by the survey's deciduous broadleaved community occupying
deeper-soil sites that escaped the Jogan lava rather than by any individual tree.

Deterministic: fixed seeds, so a rebuild reproduces the same atlas.
"""
from pathlib import Path
import json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'viewer/assets/materials_v2'
OUT.mkdir(parents=True, exist_ok=True)
N = 1024

# Boxes are laid out by hand so shoots never overlap and each has clean alpha margins.
# (x0, y0, x1, y1, lateral_shoot_count, style) with style in {'alternate', 'opposite'}
BOXES = [
    (16, 16, 330, 300, 9, 'alternate'),
    (346, 16, 660, 300, 6, 'opposite'),
    (676, 16, 1008, 300, 10, 'alternate'),
    (16, 316, 330, 600, 6, 'opposite'),
    (346, 316, 660, 600, 9, 'alternate'),
    (676, 316, 1008, 600, 7, 'opposite'),
    # two small tip branchlets for fine detail near the camera
    (16, 616, 240, 820, 4, 'alternate'),
    (256, 616, 480, 820, 3, 'opposite'),
]

# Deciduous greens plus a minority of senescing tones. Values are sRGB base-colour, i.e. the
# albedo a leaf shows under neutral light, not the darker value it takes under closed canopy.
# The runtime multiplies these by a per-tree tint and by the canopy-darkening term, so an atlas
# authored at shade values compounds twice and reads black.
GREENS = [(96, 124, 52), (112, 142, 62), (84, 112, 46), (126, 154, 72),
          (104, 132, 56), (76, 102, 42), (136, 162, 80), (92, 120, 50)]
SENESCE = [(168, 150, 66), (182, 138, 58), (150, 132, 56)]


def leaf_polygon(length, width, lobes, rng):
    """Ovate leaf outline, sampled as a closed polygon in local coordinates.

    x runs along the midrib from base (0) to tip (length); y is the half-width, mirrored.
    A low-frequency ripple stands in for marginal teeth without drawing every serration.
    """
    pts = []
    steps = 26
    for i in range(steps + 1):
        t = i / steps
        # ovate profile: widest around a third from the base
        w = math.sin(math.pi * (t ** 0.72)) ** 0.82
        tooth = 1.0 + 0.06 * math.sin(t * math.pi * lobes) * (1 - abs(2 * t - 1))
        pts.append((t * length, w * width * 0.5 * tooth))
    for i in range(steps, -1, -1):
        x, y = pts[i]
        pts.append((x, -y)) if i != steps else None
    # rebuild cleanly: forward edge then mirrored return
    fwd = [(t / steps * length,
            (math.sin(math.pi * ((t / steps) ** 0.72)) ** 0.82) * width * 0.5 *
            (1.0 + 0.06 * math.sin((t / steps) * math.pi * lobes) * (1 - abs(2 * (t / steps) - 1))))
           for t in range(steps + 1)]
    return [(x, y) for x, y in fwd] + [(x, -y) for x, y in reversed(fwd)]


def draw_leaf(d, dv, origin, ang, L, W, side, rng, senescing):
    """One lamina with its petiole, midrib and laterals. ang is measured from the shoot axis."""
    ax, ay = origin
    ca, sa = math.sin(ang) * side, -math.cos(ang)
    poly = leaf_polygon(L, W, rng.integers(5, 10), rng)
    pts = [(ax + px * ca - py * sa, ay + px * sa + py * ca) for px, py in poly]
    col = SENESCE[int(rng.integers(len(SENESCE)))] if (senescing and rng.random() < 0.34) \
        else GREENS[int(rng.integers(len(GREENS)))]
    jitter = rng.uniform(0.88, 1.12)
    d.polygon(pts, fill=tuple(min(255, int(c * jitter)) for c in col) + (255,))
    d.line([(ax, ay), pts[0]], fill=(110, 96, 62, 255), width=1)
    tipx, tipy = ax + L * ca, ay + L * sa
    dv.line([(ax, ay), (tipx, tipy)], fill=200, width=max(1, int(L / 26)))
    for m in range(3):
        q = 0.28 + 0.24 * m
        mx, my = ax + L * q * ca, ay + L * q * sa
        for ss in (-1, 1):
            lang = ang + ss * math.radians(52)
            dv.line([(mx, my), (mx + math.sin(lang) * side * W * 0.42,
                                my - math.cos(lang) * W * 0.42)], fill=120, width=1)


def draw_shoot(rgba, box, laterals, style, rng):
    """Draw one leafy BRANCHLET into a box: a main axis carrying several lateral shoots, each
    bearing its own small leaves.

    This is deliberately not a single shoot with a few large leaves. A crown card is roughly a
    metre across in the runtime, so whatever fraction of the box one lamina occupies is the
    fraction of a metre that leaf appears to be. A box holding sixteen leaves makes each of them
    about 0.35 m long — five times a Fagus crenata leaf, and unmistakable at eye level. Filling
    the same box with a branchlet of sixty-odd small leaves puts the lamina back at roughly 0.1 m
    on the same card, at no cost in triangles.
    """
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    veins = Image.new('L', (w, h), 0)
    dv = ImageDraw.Draw(veins)

    # main axis: stem at bottom centre, curving gently to the tip at top
    bow = rng.uniform(-0.16, 0.16)
    axis = [(w * (0.5 + bow * math.sin(math.pi * t)), h * (1.0 - t * 0.97))
            for t in np.linspace(0, 1, 32)]
    for i in range(len(axis) - 1):
        d.line([axis[i], axis[i + 1]], fill=(104, 88, 58, 255),
               width=max(1, int(round(4.0 * (1 - i / len(axis)) + 1))))

    senescing = rng.random() < 0.14
    leaf_len = h * rng.uniform(0.100, 0.135)      # one lamina as a fraction of the box
    total = 0
    for k in range(laterals):
        t = 0.05 + 0.90 * (k + rng.uniform(0.0, 0.4)) / laterals
        ai = min(len(axis) - 1, int(t * (len(axis) - 1)))
        bx, by = axis[ai]
        sides = [-1, 1] if style == 'opposite' else [1 if (k % 2 == 0) else -1]
        for s in sides:
            # a lateral shoot leaving the main axis, shortening toward the tip
            lat_len = h * rng.uniform(0.30, 0.46) * (1.0 - 0.34 * t)
            lat_ang = math.radians(rng.uniform(46, 82))
            lca, lsa = math.sin(lat_ang) * s, -math.cos(lat_ang)
            lat = [(bx + lat_len * q * lca + rng.uniform(-1, 1) * 1.2,
                    by + lat_len * q * lsa) for q in np.linspace(0, 1, 10)]
            for i in range(len(lat) - 1):
                d.line([lat[i], lat[i + 1]], fill=(112, 96, 62, 255),
                       width=2 if i < 4 else 1)
            n_leaf = int(rng.integers(9, 15))
            for j in range(n_leaf):
                q = 0.10 + 0.88 * (j + rng.uniform(0, 0.4)) / n_leaf
                li = min(len(lat) - 1, int(q * (len(lat) - 1)))
                L = leaf_len * (1.0 - 0.30 * q) * rng.uniform(0.82, 1.18)
                W = L * rng.uniform(0.60, 0.82)
                # leaves alternate about the lateral, angled away from it
                ls = 1 if (j % 2 == 0) else -1
                ang = lat_ang * s + ls * math.radians(rng.uniform(42, 88))
                draw_leaf(d, dv, lat[li], ang, L, W, 1, rng, senescing)
                total += 1
            # a terminal pair closing the lateral
            for ls in (-1, 1):
                ang = lat_ang * s + ls * math.radians(rng.uniform(18, 40))
                draw_leaf(d, dv, lat[-1], ang, leaf_len * rng.uniform(0.7, 0.95),
                          leaf_len * 0.55, 1, rng, senescing)
                total += 1

    rgba.alpha_composite(layer, (x0, y0))
    return veins, (x0, y0), total


def main():
    rng = np.random.default_rng(7701)
    atlas = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    height = Image.new('L', (N, N), 0)
    boxes = []
    for (x0, y0, x1, y1, n, style) in BOXES:
        veins, org, leaves = draw_shoot(atlas, (x0, y0, x1, y1), n, style, rng)
        height.paste(veins, org, veins)
        boxes.append(dict(box=[x0, y0, x1, y1], laterals=n, leaves=leaves, arrangement=style))

    # A little alpha erosion keeps the 0.3 mask cutoff from leaving haloes.
    a = np.asarray(atlas).astype(np.float32)
    al = a[..., 3] / 255.0
    al = np.clip((al - 0.06) / 0.94, 0, 1) ** 0.85
    a[..., 3] = al * 255
    atlas = Image.fromarray(a.astype(np.uint8))
    atlas.save(OUT / 'broadleaf_atlas.png')

    # normal map from the vein height field, slightly blurred so it reads as leaf relief
    hf = np.asarray(height.filter(ImageFilter.GaussianBlur(1.1))).astype(np.float32) / 255.0
    hf = hf * (al > 0.3)
    gy, gx = np.gradient(hf * 5.0)
    nx, ny, nz = -gx, gy, np.ones_like(hf)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nor = np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5
    Image.fromarray((nor * 255).astype(np.uint8)).save(OUT / 'broadleaf_atlas_nor_gl.png')

    rough = np.clip(0.86 - 0.10 * hf, 0, 1) * 255
    Image.fromarray(rough.astype(np.uint8)).convert('L').save(
        OUT / 'broadleaf_atlas_rough.jpg', quality=90)

    meta = dict(
        generator='construction_code_v2/gen_broadleaf_atlas.py',
        seed=7701,
        atlas=N,
        boxes=boxes,
        status='PROCEDURAL representative deciduous foliage. Not a scan, not a species '
               'determination, not captured at Aokigahara.',
        evidence_basis='The vegetation survey behind the project blueprint distinguishes a '
                       'deciduous broadleaved community associated with deeper-soil sites that '
                       'escaped the Jogan lava. Leaf outline, venation, colour spread and shoot '
                       'arrangement are interpretive.',
        coverage_above_cutoff=round(float((al > 0.3).mean()), 4),
    )
    (Path(__file__).resolve().parent / 'broadleaf_atlas_boxes.json').write_text(
        json.dumps(meta, indent=2))
    print('wrote', OUT / 'broadleaf_atlas.png', atlas.size)
    print('alpha coverage above 0.3 cutoff:', meta['coverage_above_cutoff'])
    print('boxes:', len(boxes))


if __name__ == '__main__':
    main()
