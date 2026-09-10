"""Aokigahara broadleaf library — deterministic procedural deciduous trees.

Why this exists
---------------
Tree library v2 gave the conifers real form: modelled surface roots, buttress flare, alpha-cut
spray foliage and three levels of detail. The deciduous broadleaved component never got that pass.
Broadleaf stems kept the Pass-1 representation: clumps of flat, untextured, single-colour geometry
with no alpha cut, and no far impostor at all, so every broadleaf beyond the near field rendered at
1,684 triangles apiece against 32 for a conifer at the same distance. They cost fifty-three times
as much as a distant conifer and read as pale blobs while doing it.

This builds the missing library, in the same style and to the same interfaces as
generate_trees_v2.py, whose mesh and GLB machinery it imports directly so the output format cannot
drift.

Variants (species-suggestive, NOT botanically exact, NOT surveyed individuals):
  beech    : Fagus-like. Smooth pale bole, high fork, dense rounded crown, layered horizontal shoots
  oak      : Quercus-like. Stout short bole, heavy low limbs, broad irregular crown, gnarled
  maple    : Acer-like. Slender multi-stem, opposite branching, open airy crown

Evidence basis for the community, not for any individual: the vegetation survey behind the project
blueprint distinguishes deciduous broadleaved forest associated with deeper-soil sites that escaped
the Jogan lava, and the research dossier records a beech stand at the Mt Omuro sector. Form,
proportion, branching and crown density here are interpretive.

Bark uses the Poly Haven fir_tree_01 bark maps (CC0) as a representative grey plated bark. Foliage
uses the procedural atlas from gen_broadleaf_atlas.py. Neither was captured at Aokigahara.

Output: viewer/assets/tree-library-broadleaf.glb with meshes <variant>_<lod>, lod in {high,low,far}
Y up, metres, trunk base at y=0. Deterministic seeds.
"""
from pathlib import Path
import json, math, hashlib, sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_trees_v2 import Mesh, GLB, curved, interp, unit  # noqa: E402  proven, shared machinery

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / 'work/tex'
MATV2 = ROOT / 'viewer/assets/materials_v2'
OUT = ROOT / 'viewer/assets/tree-library-broadleaf.glb'
ATLAS = 1024

_meta = json.loads((Path(__file__).resolve().parent / 'broadleaf_atlas_boxes.json').read_text())
BOXES = [tuple(b['box']) for b in _meta['boxes']]
BIG = [b for b in BOXES if (b[2] - b[0]) > 280]          # full shoots
SMALL = [b for b in BOXES if (b[2] - b[0]) <= 280]       # tip shoots

SPECIES = {
    #            fork_h  n_prim  spread  rise    crown_ratio  taper  lean_max  tint
    'beech': dict(fork=0.28, prim=(9, 13), spread=4.1, rise=(0.02, 1.20), crown=0.58,
                  taper=0.80, dbh=0.040, tint=(0.88, 0.96, 0.72)),
    'oak':   dict(fork=0.22, prim=(8, 12), spread=5.0, rise=(-0.18, 1.00), crown=0.70,
                  taper=0.70, dbh=0.049, tint=(0.80, 0.88, 0.64)),
    'maple': dict(fork=0.24, prim=(8, 12), spread=3.7, rise=(0.20, 1.40), crown=0.64,
                  taper=0.86, dbh=0.034, tint=(0.94, 1.00, 0.78)),
}


def bark_colour(y, dead=False):
    """Moss climbs the lowest metre or so of a trunk on this substrate."""
    def f(j, a, ys=y):
        yy = ys[j][1] if hasattr(ys[j], '__len__') else ys[j]
        moss = max(0.0, 1 - yy / 1.4) ** 1.5 * (0.5 + 0.5 * max(0.0, math.cos(a - 2.1)))
        return (1 - 0.5 * moss, 1 - 0.24 * moss, 1 - 0.66 * moss)
    return f


def surface_roots(bark, r0, height, rng, count):
    """Roots riding over lava: shallow soil forces them across the surface rather than into it."""
    for j in range(count):
        ang = j * 2 * math.pi / count + rng.uniform(-0.3, 0.3)
        span = rng.uniform(1.5, 3.8) * min(1.0, (height / 14) ** 0.8)
        rr0 = r0 * rng.uniform(0.40, 0.66)
        wobble, w2 = rng.uniform(0.15, 0.45), rng.uniform(0.5, 1.5)
        pts, rad = [], []
        for t in np.linspace(0, 1, 9):
            a = ang + wobble * math.sin(t * w2 * 3.1 + j)
            d = span * t
            y = 0.15 * (1 - t) ** 0.6 + 0.08 * math.sin(t * 6.0 + j * 1.7) * t - 0.05 * t * t
            pts.append([math.cos(a) * d * (1 + 0.4 * (1 - t)), y, math.sin(a) * d * (1 + 0.4 * (1 - t))])
            rad.append(rr0 * (1 - t) ** 0.9 + 0.014)
        pts = np.array(pts)
        pts[0] = [math.cos(ang) * r0 * 0.9, 0.28, math.sin(ang) * r0 * 0.9]

        def root_col(jj, a):
            moss = 0.5 + 0.5 * max(0.0, math.sin(a))
            moss *= 0.75 + 0.25 * math.sin(jj * 1.9)
            return (1 - 0.55 * moss, 1 - 0.28 * moss, 1 - 0.7 * moss)
        bark.tube(pts, rad, 6, color=root_col, flute=0.12, uvscale=(0.5, 1.2), ground_clip=False)


def build_broadleaf(kind, seed, height, lod):
    """One deciduous tree. Returns (bark, foliage) meshes."""
    S = SPECIES[kind]
    rng = np.random.default_rng(seed)
    bark, foliage = Mesh(), Mesh()
    hi = lod == 'high'

    # --- bole: stouter and shorter than the conifers, with a real fork
    lean = rng.uniform(0.02, 0.09)
    lean_dir = rng.uniform(0, 2 * math.pi)
    dbh = S['dbh'] * height * rng.uniform(0.85, 1.2)
    r0 = dbh / 2
    fork_h = height * S['fork'] * rng.uniform(0.9, 1.1)
    n_ring = 16 if hi else 8
    bole = []
    for t in np.linspace(0, 1, n_ring):
        sway = 0.07 * math.sin(t * 4.3 + seed % 7)
        x = math.cos(lean_dir) * lean * fork_h * t * t + sway * math.cos(lean_dir + 1.3)
        z = math.sin(lean_dir) * lean * fork_h * t * t + sway * math.sin(lean_dir + 1.3)
        bole.append([x, fork_h * t, z])
    bole = np.array(bole)
    ts = np.linspace(0, 1, len(bole))
    rr = r0 * (1 - ts * 0.42) ** S['taper'] + 0.02
    rr = rr * (1 + 1.15 * np.clip(1 - bole[:, 1] / 1.0, 0, 1) ** 2.0)      # buttress flare
    bark.tube(bole, rr, 12 if hi else 7, color=bark_colour(bole), flute=0.05)

    if hi:
        surface_roots(bark, r0, height, rng, int(rng.integers(6, 10)))

    tint = np.array(S['tint']) * rng.uniform(0.86, 1.12)
    top_r = float(rr[-1])
    crown_top = height
    cards = []          # (centre, direction, size, level) collected then emitted

    def put_card(c, sd, size_mult, rel, crossed=False, small=False):
        pool = SMALL if (small and SMALL) else BIG
        box = pool[int(rng.integers(len(pool)))]
        bw = (box[2] - box[0]) / ATLAS
        bh = (box[3] - box[1]) / ATLAS
        size = size_mult * rng.uniform(0.85, 1.2) * max(height / 16, 0.4)
        length, width = size * bh * 1.35, size * bw * 1.35
        # leaves present their faces broadly upward toward the canopy gap
        normal = unit(np.array([0, 1, 0]) * 0.85 + np.array([rng.uniform(-.6, .6), 0, rng.uniform(-.6, .6)]))
        col = tint * rng.uniform(0.82, 1.16) * (0.84 + 0.16 * rel)
        foliage.card(c, sd, normal, length, width, box, col, fold=0.32, tipdrop=0.12)
        if crossed:
            side = unit(np.cross(sd, normal) + normal * 0.25)
            foliage.card(c, sd, side, length * 0.92, width * 0.92, box, col * 0.94,
                         fold=0.32, tipdrop=0.12)

    def limb(start, direction, length, radius, depth, rel):
        """Recursive forking limb. Leaves hang off the last two levels."""
        end = start + direction * length
        bow = np.array([0, -0.10 * length if depth == 0 else 0.05 * length, 0])
        seg = (5, 3, 2)[min(depth, 2)] if hi else 2
        sides = (7, 5, 4)[min(depth, 2)] if hi else 3
        p, t = curved(start, end, bow, seg)
        bark.tube(p, radius * (1 - t) ** 1.05 + 0.008, sides, color=(1, 1, 1))
        if depth >= (2 if hi else 1):
            n = (5 if hi else 3)
            for m in range(n):
                q = 0.14 + 0.86 * (m + 0.5) / n
                c = interp(p, q)
                # leafy shoots stand out from the twig in every direction, not just forward
                sd = unit(direction * 0.55 + np.array([rng.uniform(-1, 1), rng.uniform(-.25, .85),
                                                       rng.uniform(-1, 1)]))
                off = np.array([rng.uniform(-.3, .3), rng.uniform(-.2, .2), rng.uniform(-.3, .3)]) * (height / 16)
                put_card(c + off, sd, 2.15 if hi else 2.6, rel, crossed=True,
                         small=hi and m % 4 == 0)
            sd = unit(direction + np.array([0, 0.28, 0]))
            put_card(end, sd, 2.4 if hi else 3.0, rel, crossed=True)
            return
        if depth >= 1 and hi:
            # interior shoots: a deciduous crown carries leaves back along the limbs, not just at
            # the tips, and without them the crown renders as a hollow shell of foliage
            for m in range(2):
                q = 0.35 + 0.55 * (m + 0.5) / 2
                c = interp(p, q)
                sd = unit(direction * 0.4 + np.array([rng.uniform(-1, 1), rng.uniform(-.1, 1.0),
                                                      rng.uniform(-1, 1)]))
                put_card(c, sd, 2.0, rel, crossed=True, small=(m == 1))
        nsub = int(rng.integers(3, 5)) if hi else int(rng.integers(2, 4))
        for k in range(nsub):
            a = k * 2.399963 + rng.uniform(-0.5, 0.5)
            spread = rng.uniform(0.70, 1.35)
            sd = unit(direction * (1.0 + 0.4 * rng.random())
                      + np.array([math.cos(a), rng.uniform(0.05, 0.75), math.sin(a)]) * spread)
            limb(end, sd, length * rng.uniform(0.55, 0.78), radius * 0.58, depth + 1,
                 min(1.0, rel + 0.25))

    # --- the leader carries on above the fork and the primary limbs leave it at staggered
    # heights. Emitting every primary from one fork point produces a flat plate of foliage;
    # a deciduous crown is a deep mass, so the origins have to be spread up the axis.
    lead_len = (crown_top - fork_h) * rng.uniform(0.82, 0.94)
    leader_dir = unit(np.array([rng.uniform(-.16, .16), 1, rng.uniform(-.16, .16)]))
    leader_end = bole[-1] + leader_dir * lead_len
    lp, _ = curved(bole[-1], leader_end,
                   np.array([rng.uniform(-.3, .3), 0, rng.uniform(-.3, .3)]) * lead_len,
                   5 if hi else 2)
    bark.tube(lp, top_r * 0.78 * (1 - np.linspace(0, 1, len(lp))) ** 1.1 + 0.012,
              8 if hi else 4, color=(1, 1, 1))

    nprim = int(rng.integers(*S['prim']))
    if not hi:
        nprim = max(4, nprim - 2)
    for j in range(nprim):
        # height fraction up the leader, lowest limbs longest and flattest
        u = (j + rng.uniform(0.1, 0.9)) / nprim
        origin = interp(lp, min(0.96, u * 0.95))
        a = j * 2.399963 + rng.uniform(-0.35, 0.35)
        radial = np.array([math.cos(a), 0, math.sin(a)])
        # limbs rise more steeply the higher they leave the leader, closing the crown dome
        rise = S['rise'][0] * (1 - u) + S['rise'][1] * u + rng.uniform(-0.16, 0.16)
        sd = unit(radial + np.array([0, rise, 0]))
        L = S['spread'] * (height / 16) * rng.uniform(0.80, 1.20) * (1.0 - 0.42 * u)
        limb(origin, sd, L, top_r * 0.80 * (1 - 0.45 * u), 0, 0.18 + 0.5 * u)

    # the leader's own terminal shoot closes the top of the crown
    limb(leader_end, unit(leader_dir + np.array([rng.uniform(-.2, .2), 0.5, rng.uniform(-.2, .2)])),
         S['spread'] * (height / 16) * 0.42, top_r * 0.34, 1, 0.85)

    if not hi:
        # Crown-mass cards. These carry the mid-distance silhouette, and they have to fill the
        # same volume the high mesh's branch system does or the LOD switch shows as a band of
        # bare stems across the canopy. Sized in metres against the crown the limbs actually
        # reach: one primary of length L plus one sub-limb generation at 0.55-0.78 L.
        crown_r = S['spread'] * (height / 16) * 2.25   # matches the high mesh's measured spread
        crown_v = (crown_top - fork_h) * 0.95
        cbase = fork_h + (crown_top - fork_h) * 0.44
        # a card is four triangles, so the mid LOD can afford a couple of dozen modest ones. Many
        # small cards read as a crown; ten large ones read as banners, because the shoot in the
        # atlas gets magnified past the scale any leaf on it could be.
        # card count follows crown area, or a large crown gets the same budget as a small one
        # and its cards separate into visible vertical banners
        ncards = int(np.clip(round(22 * (crown_r * crown_v) / 60.0), 22, 46))
        for k in range(ncards):
            a = k * 2.399963 + rng.uniform(-0.4, 0.4)
            # sqrt keeps the sample areal rather than centre-heavy; the crown is hollow-ish, so
            # bias outward and flatten the vertical spread toward the rim
            u = math.sqrt(rng.uniform(0.06, 1.0))
            rad = crown_r * 0.78 * u
            c = np.array([math.cos(a) * rad,
                          cbase + rng.uniform(-0.38, 0.42) * crown_v * (1.0 - 0.45 * u),
                          math.sin(a) * rad])
            box = BIG[int(rng.integers(len(BIG)))]
            aspect = (box[2] - box[0]) / (box[3] - box[1])
            length = crown_v * rng.uniform(0.22, 0.34)      # metres, along `sd`
            width = length * aspect
            # a crown of uniformly upright cards stripes vertically; real shoots hang out and
            # over at every angle, so tilt hard and vary it
            sd = unit(np.array([rng.uniform(-1, 1), rng.uniform(0.35, 1.7), rng.uniform(-1, 1)]))
            nm = unit(np.array([math.cos(a + 1.57), rng.uniform(-.4, .6), math.sin(a + 1.57)]))
            foliage.card(c, sd, nm, length, width, box, tint * rng.uniform(0.80, 1.00), fold=0.14)

    return bark, foliage


def build_far(kind, seed, height):
    """Far impostor: trunk stub plus three crossed crown cards. The thing the Pass-1 broadleaves
    never had, and the whole reason distant broadleaf cost fifty-three times a distant conifer."""
    S = SPECIES[kind]
    rng = np.random.default_rng(seed)
    bark, foliage = Mesh(), Mesh()
    r0 = S['dbh'] * height / 2
    fork_h = height * S['fork']
    bark.tube(np.array([[0, 0, 0], [0, fork_h, 0], [0, height * 0.92, 0]]),
              [r0 * 1.2, r0 * 0.7, 0.03], 4, color=(1, 1, 1))
    tint = np.array(S['tint']) * 0.92
    crown_c = np.array([0, fork_h + (height - fork_h) * 0.50, 0])
    crown_v = (height - fork_h) * 1.02
    crown_w = S['spread'] * (height / 16) * 4.4        # full width the limb system reaches
    for j in range(3):
        a = j * math.pi / 3
        box = BIG[j % len(BIG)]
        foliage.card(crown_c, np.array([0, 1, 0]),
                     np.array([math.cos(a), 0, math.sin(a)]),
                     crown_v, crown_w, box, tint, fold=0.0)
    return bark, foliage


def main():
    g = GLB()
    m_bark = g.material(
        'Bark broadleaf-like: Poly Haven fir_tree_01 bark (CC0), representative grey plated bark',
        TEX / 'fir_tree_c__fir_tree_01_bark_diff.jpg',
        TEX / 'fir_tree_c__fir_tree_01_bark_nor_gl.jpg',
        TEX / 'fir_tree_c__fir_tree_01_bark_rough.jpg', normal_scale=0.9)
    m_leaf = g.material(
        'Broadleaf foliage cards: procedural deciduous atlas (gen_broadleaf_atlas.py)',
        MATV2 / 'broadleaf_atlas.png',
        MATV2 / 'broadleaf_atlas_nor_gl.png',
        MATV2 / 'broadleaf_atlas_rough.jpg',
        double=True, alpha=0.3, normal_scale=0.6)

    specs = [
        ('broadleaf_a', 'beech', 8801, 16.0),
        ('broadleaf_b', 'oak',   8802, 13.5),
        ('broadleaf_c', 'maple', 8803, 11.0),
    ]
    stats = {}
    for name, kind, seed, height in specs:
        for lod in ('high', 'low', 'far'):
            if lod == 'far':
                bark, fol = build_far(kind, seed, height)
            else:
                bark, fol = build_broadleaf(kind, seed, height, lod)
            prims, tris = [], 0
            for mesh, mat in ((bark, m_bark), (fol, m_leaf)):
                if len(mesh.i) == 0:
                    continue
                pr, n = g.primitive(mesh, mat)
                prims.append(pr)
                tris += n
            mi = g.mesh(f'{name}_{lod}', prims, extras={
                'variant': name, 'kind': kind, 'lod': lod, 'height_m': height,
                'status': 'PROCEDURAL; not a surveyed individual; species-suggestive only'})
            g.node(f'{name}_{lod}', mi)
            stats[f'{name}_{lod}'] = tris

    size = g.save(OUT, extras={'library': 'Aokigahara broadleaf library',
                               'provenance': __doc__.strip(), 'triangles': stats})
    manifest = dict(
        file=OUT.name, sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(), bytes=size,
        meshes=stats, lods=['high', 'low', 'far'],
        variants=[s[0] for s in specs],
        species={s[0]: s[1] for s in specs},
        generator='construction_code_v2/generate_broadleaf.py',
        atlas='construction_code_v2/gen_broadleaf_atlas.py',
        atlasManifest='construction_code_v2/broadleaf_atlas_boxes.json',
        seeds={s[0]: s[2] for s in specs},
        heights_m={s[0]: s[3] for s in specs},
        sources={
            'bark': 'Poly Haven fir_tree_01 bark maps, CC0, extracted from viewer/assets/models/'
                    'fir_tree_c.glb. Representative grey plated bark; NOT captured at Aokigahara '
                    'and NOT a species determination.',
            'foliage': 'Procedural, generated by gen_broadleaf_atlas.py at seed 7701. Drawn, not '
                       'photographed. Leaf outline, venation, colour spread and shoot arrangement '
                       'are interpretive.',
        },
        status='PROCEDURAL. No variant is a surveyed individual. Species names are suggestive of '
               'form only and establish no botanical identity.',
        provenance=__doc__.strip())
    (ROOT / 'viewer/assets/tree-library-broadleaf.json').write_text(json.dumps(manifest, indent=2))
    print('saved', OUT, size, 'bytes')
    for k, v in stats.items():
        print(f'  {k:22} {v:>7} triangles')


if __name__ == '__main__':
    main()
