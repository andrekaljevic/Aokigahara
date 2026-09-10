"""Aokigahara tree library v2 — deterministic procedural conifers with exposed surface-root systems.

Species-suggestive variants (NOT botanically exact, NOT surveyed individuals):
  tsuga   : Tsuga-like hemlock; grey plated bark (Poly Haven fir_tree_01 bark, CC0), spreading/drooping laterals, dark blue-green sprays
  hinoki  : Chamaecyparis-like cypress; reddish stringy bark (Poly Haven japanese_cedar_bark, CC0), ascending laterals, yellow-green sprays
  snag    : dead standing hemlock-type stem, broken top, bare branches (dead_tree_trunk textures, CC0)
  sapling : small hinoki/tsuga regeneration stems 1.5–6 m
Foliage cards use the Poly Haven fir_tree_01 twig atlas (CC0). Fir sprays are a REPRESENTATIVE stand-in for Tsuga/Chamaecyparis sprays.
Evidence basis for form: ECO-001/ECO-002 (Tsuga/hinoki stand, heterogeneous size classes, closed canopy, small gaps),
IMG-007/008/013 & ECO-016 (surface roots spreading over lava, moss on roots and trunk bases, leaning trunks).
Output: viewer/assets/tree-library-v2.glb  with meshes  <variant>_<lod>  lod in {high, low, far}.
Y up, metres, trunk base at y=0. Deterministic seeds.

--- modified on dev/generational-visual-upgrade -------------------------------------------------
The mid-detail (`low`) crown-mass cards were rebuilt. As shipped they were four cards sized
`cw*1.1` and then passed through `sz*h*1.15`, where h is the atlas box height as a fraction of the
atlas: about 2 m of card inside a crown 12 m across, so between roughly 46 m and 230 m — most of
the visible forest — a stand thinned to poles. They are now sized in metres and seeded on the
foliage the branch pass already built, so the added mass follows each tree's real habit. `high`,
`far`, snag, log and rock meshes are untouched and remain byte-identical to the shipped library.

Rebuilding needs two steps, because textures here are embedded by reading the files in `work/tex/`
verbatim and that directory is scratch the repository does not carry. Use
`tools/rebuild_tree_library.sh`, which regenerates and then grafts the shipped image payload back
on; run unmodified it reproduces the original library byte-for-byte. Rebuilding without the graft
inflates the file from 12.5 MB to 16.0 MB for no visual gain.
"""
from pathlib import Path
import json, math, struct, hashlib
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / 'work/tex'
MAT = ROOT / 'viewer/assets/materials'
OUT = ROOT / 'viewer/assets/tree-library-v2.glb'

# ---------------------------------------------------------------- twig atlas cards (pixel boxes measured from alpha)
ATLAS = 1024
CARDS = [(187, 41, 445, 325), (662, 35, 966, 384), (499, 260, 652, 416), (307, 403, 666, 800), (643, 457, 987, 856)]
CARD_TIP = [(545, 95, 609, 240), (390, 290, 477, 398)]
DEAD_TWIG = (319, 723, 1024, 1024)

def unit(v):
    v = np.asarray(v, dtype=float); return v / (np.linalg.norm(v) + 1e-12)

def frame(axis):
    axis = unit(axis); ref = np.array([0., 1., 0.]) if abs(axis[1]) < .85 else np.array([1., 0., 0.])
    side = unit(np.cross(axis, ref)); return side, unit(np.cross(side, axis))

def rot_y(v, a):
    c, s = math.cos(a), math.sin(a); return np.array([c*v[0] + s*v[2], v[1], -s*v[0] + c*v[2]])

class Mesh:
    def __init__(self): self.p = []; self.n = []; self.uv = []; self.c = []; self.i = []
    def vertex(self, p, n, uv, c):
        self.p.append(np.asarray(p, float)); self.n.append(np.asarray(n, float)); self.uv.append(uv); self.c.append(c); return len(self.p) - 1
    def tube(self, points, radii, sides=8, uvscale=(0.7, 1.8), color=None, moss=None, flute=0.06, phase=0.0, ground_clip=True, cap=True):
        """Tapered tube; color(j) callable or constant; moss(j,angle) -> tint amount."""
        points = np.asarray(points, float); radii = np.asarray(radii, float); rings = []; dist = 0.0
        for j, (pt, r) in enumerate(zip(points, radii)):
            if j: dist += np.linalg.norm(pt - points[j-1])
            tangent = unit(points[min(j+1, len(points)-1)] - points[max(j-1, 0)])
            side, up = frame(tangent); ring = []
            for k in range(sides + 1):
                a = 2*math.pi*k/sides + phase
                nrm = math.cos(a)*side + math.sin(a)*up
                uneven = 1 + flute*math.sin(3*a + .3*j) + flute*.5*math.cos(5*a - .2*j)
                p = pt + nrm*r*uneven
                if ground_clip: p[1] = max(-0.02, p[1])
                col = color(j, a) if callable(color) else (color or (1, 1, 1))
                ring.append(self.vertex(p, nrm, [k/sides*2*math.pi*r/uvscale[0], dist/uvscale[1]], col))
            rings.append(ring)
        for j in range(len(rings) - 1):
            for k in range(sides):
                a, b, c, d = rings[j][k], rings[j][k+1], rings[j+1][k], rings[j+1][k+1]
                self.i.extend([[a, c, b], [b, c, d]])
        if cap:
            j = len(rings) - 1; t = unit(points[-1] - points[-2]); centre = self.vertex(points[-1], t, [.5, .5], (1, 1, 1))
            for k in range(sides): self.i.append([centre, rings[j][k+1], rings[j][k]])
    def card(self, centre, direction, normal, length, width, box, color, fold=0.25, tipdrop=0.0):
        """Folded foliage card: 3 rows x 2 cols of vertices (6 verts, 4 tris). direction = along spray, normal = card facing."""
        direction = unit(direction); normal = unit(normal - direction*np.dot(direction, normal)); side = unit(np.cross(direction, normal))
        u0, v0, u1, v1 = [b/ATLAS for b in box]
        # sprays in the atlas are oriented with the stem at the bottom (larger v) and the tip upward
        pts = []; uvs = []
        for row, t in enumerate([0.0, 0.5, 1.0]):
            drop = -tipdrop*t*t
            for colm, s in enumerate([-0.5, 0.5]):
                p = centre + direction*length*(t-0.15) + side*width*s + normal*(fold*width*(1 - 4*(s*s)) if row == 1 else 0) + np.array([0, drop, 0])*length
                pts.append(p); uvs.append([u0 + (u1-u0)*(s+0.5), v1 - (v1-v0)*t])
        ids = [self.vertex(p, normal, uv, color) for p, uv in zip(pts, uvs)]
        for r in range(2):
            a, b, c, d = ids[r*2], ids[r*2+1], ids[r*2+2], ids[r*2+3]
            self.i.extend([[a, b, c], [b, d, c]])
    def arrays(self):
        P = np.asarray(self.p, np.float32); Nn = np.asarray(self.n, np.float32); I = np.asarray(self.i, np.uint32)
        Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-9)
        return P, Nn, np.asarray(self.uv, np.float32), np.asarray(self.c, np.float32), I

def interp(points, t):
    j = t*(len(points)-1); i = min(int(j), len(points)-2); f = j - i; return points[i]*(1-f) + points[i+1]*f

def curved(start, end, bow, segments):
    t = np.linspace(0, 1, segments+1); return np.array([start + (end-start)*q + bow*math.sin(math.pi*q) for q in t]), t

# ---------------------------------------------------------------- tree builder
def build_conifer(kind, seed, height, lod, dead=False, lean=None, multistem=False):
    rng = np.random.default_rng(seed)
    bark, foliage, deadwood = Mesh(), Mesh(), Mesh()
    hemlock = kind == 'tsuga'
    hi = lod == 'high'
    # --- trunk: lean + gentle sinuosity; DBH from height (allometric-ish, interpretive)
    if lean is None: lean = rng.uniform(0.02, 0.10)
    lean_dir = rng.uniform(0, 2*math.pi)
    dbh = (0.022 if hemlock else 0.019) * height * rng.uniform(0.85, 1.2)   # e.g. 18 m -> 0.40 m
    r0 = dbh/2
    n_ring = 22 if hi else 10
    trunk = []
    for t in np.linspace(0, 1, n_ring):
        sway = 0.10*math.sin(t*5.1 + seed % 7) + 0.05*math.sin(t*11.3)
        x = math.cos(lean_dir)*lean*height*t*t*1.1 + sway*math.cos(lean_dir + 1.3)
        z = math.sin(lean_dir)*lean*height*t*t*1.1 + sway*math.sin(lean_dir + 1.3)
        trunk.append([x, height*t, z])
    trunk = np.array(trunk)
    if dead:  # broken top
        cut = rng.uniform(0.45, 0.8); trunk = trunk[:max(4, int(n_ring*cut))]
    ts = np.linspace(0, 1, len(trunk))
    rr = r0*(1-ts*0.92)**0.75 + 0.02
    # buttress flare in the lowest ~0.7 m
    flare = 1 + 1.05*np.clip(1 - trunk[:, 1]/0.9, 0, 1)**2.0
    rr = rr*flare
    def bark_col(j, a):
        y = trunk[j][1]
        moss = max(0.0, 1 - y/1.6)**1.5 * (0.55 + 0.45*max(0.0, math.cos(a - 2.1)))
        moss *= 0.0 if dead else 1.0
        return (1 - 0.55*moss, 1 - 0.28*moss, 1 - 0.7*moss)
    (deadwood if dead else bark).tube(trunk, rr, 12 if hi else 7, color=bark_col, flute=0.07)
    # --- surface roots (Aokigahara: shallow soil, roots spread over lava); high LOD only
    if hi:
        nroots = int(rng.integers(7, 11)) if height > 8 else int(rng.integers(3, 5))
        for j in range(nroots):
            ang = j*2*math.pi/nroots + rng.uniform(-0.3, 0.3)
            span = rng.uniform(1.6, 4.2) * (1.0 if not dead else 0.8) * min(1.0, (height/14)**0.8)
            rr0 = r0*rng.uniform(0.42, 0.7)
            pts = []; rad = []
            wobble = rng.uniform(0.15, 0.45); w2 = rng.uniform(0.5, 1.5)
            for t in np.linspace(0, 1, 9):
                a = ang + wobble*math.sin(t*w2*3.1 + j)
                d = span*t
                # starts at the buttress, rides over the surface: slight undulation, ends slightly buried
                y = 0.16*(1-t)**0.6 + 0.09*math.sin(t*6.0 + j*1.7)*t - 0.05*t*t
                radius = rr0*(1-t)**0.9 + 0.015
                pts.append([math.cos(a)*d*(1 + 0.4*(1-t)) , y, math.sin(a)*d*(1 + 0.4*(1-t))])
                rad.append(radius)
            pts = np.array(pts); pts[0] = [math.cos(ang)*r0*0.9, 0.30, math.sin(ang)*r0*0.9]
            def root_col(jj, a, pts=pts):
                moss = 0.5 + 0.5*max(0.0, math.sin(a))   # upper side mossier
                moss *= 0.75 + 0.25*math.sin(jj*1.9)
                return (1 - 0.55*moss, 1 - 0.28*moss, 1 - 0.7*moss)
            bark.tube(pts, rad, 6, color=root_col, flute=0.12, uvscale=(0.5, 1.2), ground_clip=False)
            # occasional forking root
            if rng.random() < 0.5:
                k = int(rng.integers(2, 5)); base = pts[k]; ang2 = ang + rng.uniform(0.5, 1.1)*rng.choice([-1, 1]); span2 = rng.uniform(0.8, 2.0)
                p2 = [base + np.array([math.cos(ang2)*span2*t, -0.03*t + 0.04*math.sin(t*5), math.sin(ang2)*span2*t]) for t in np.linspace(0, 1, 5)]
                bark.tube(p2, [rad[k]*0.8*(1-t)**0.9 + 0.012 for t in np.linspace(0, 1, 5)], 5, color=root_col, flute=0.12, ground_clip=False)
    # --- branches
    if dead:
        nprim = int(rng.integers(5, 10))
        for j in range(nprim):
            level = rng.uniform(0.35, 0.95); a = j*2.399963 + rng.uniform(-0.4, 0.4)
            radial = np.array([math.cos(a), 0, math.sin(a)]); start = interp(trunk, level)
            L = rng.uniform(0.8, 2.6)*(1 - 0.4*level); end = start + radial*L + np.array([0, rng.uniform(-0.6, 0.3), 0])
            p, t = curved(start, end, np.array([0, -0.2, 0]), 4)
            deadwood.tube(p, 0.05*(1-t)**1.1 + 0.008, 5, color=(1, 1, 1), cap=True)
        return bark, foliage, deadwood
    hs = min(1.0, height/18)
    nprim = int(round(((rng.integers(20, 27) if hemlock else rng.integers(22, 30)) if hi else rng.integers(12, 16)) * max(0.35, hs**0.7)))
    crown_base = rng.uniform(0.28, 0.42) if hemlock else rng.uniform(0.30, 0.45)
    if kind == 'sapling': crown_base = rng.uniform(0.08, 0.2)
    tint = np.array([0.55, 0.62, 0.50]) if hemlock else np.array([0.80, 0.86, 0.55])   # multiplies the fir spray texture
    tint *= rng.uniform(0.85, 1.12)
    for j in range(nprim):
        level = crown_base + (1 - crown_base - 0.05)*j/(nprim-1) + rng.uniform(-0.02, 0.02)
        a = j*2.399963 + rng.uniform(-0.35, 0.35)
        radial = np.array([math.cos(a), 0, math.sin(a)])
        rel = (level - crown_base)/(1 - crown_base)
        spread = (4.6 if hemlock else 3.6)*(1 - rel)**0.55*rng.uniform(0.7, 1.25)*(height/18)
        rise = rng.uniform(-0.5, 0.6) if hemlock else rng.uniform(0.6, 1.6)
        start = interp(trunk, level); end = start + radial*spread + np.array([0, rise, 0])
        bow = radial*0.1 + np.array([0, (-0.6 if hemlock else 0.25)*spread/4, 0])
        p, t = curved(start, end, bow, 6 if hi else 3)
        prad = (0.11 if hemlock else 0.085)*(height/18)
        bark.tube(p, prad*(1-t)**1.1 + 0.006, 6 if hi else 3, color=(1, 1, 1))
        # --- foliage: overlapping spray cards along the outer part of the primary (frond), plus secondaries
        branch_dir = unit(end - start)
        sideways0 = np.array([-radial[2], 0, radial[0]])
        def put_card(c, sd, side_vec, size_mult, drop, crossed=False):
            box = CARDS[int(rng.integers(3, 5)) if rng.random() < 0.7 else int(rng.integers(0, 3))]
            w = (box[2]-box[0])/ATLAS; h = (box[3]-box[1])/ATLAS
            size = size_mult*rng.uniform(0.85, 1.25)*max(height/18, 0.36)
            length = size*h*1.3; width = size*w*1.3
            normal = unit(np.array([0, 1, 0])*0.9 + side_vec*rng.uniform(-0.5, 0.5) + radial*rng.uniform(-0.25, 0.25))
            col = tint*rng.uniform(0.8, 1.15)*(0.85 + 0.15*rel)
            foliage.card(c, sd, normal, length, width, box, col, fold=0.3, tipdrop=drop)
            if crossed:
                foliage.card(c, sd, unit(np.cross(sd, normal) + normal*0.25), length*0.9, width*0.9, box, col*0.95, fold=0.3, tipdrop=drop)
        drop = 0.28 if hemlock else 0.06
        ncards_along = max(8, int(spread/0.15)) if hi else max(3, int(spread/0.9))
        for m in range(ncards_along):
            q = 0.30 + 0.70*(m + 0.5)/ncards_along
            c = interp(p, q)
            sign = 1 if m % 2 else -1
            sd = unit(branch_dir*0.85 + sideways0*sign*0.45 + np.array([0, (-0.3 if hemlock else 0.1), 0]))
            put_card(c + sideways0*sign*rng.uniform(0.1, 0.4)*(height/18), sd, sideways0*sign, (1.35 if hi else 2.6), drop, crossed=(not hi) or (m % 2 == 0))
            if hi and m % 2 == 0:  # second, inner layer of shaded foliage under the frond
                put_card(c - sideways0*sign*0.1 + np.array([0, -0.18, 0]), unit(sd + np.array([0, -0.2, 0])), sideways0*sign, 1.1, drop)
        # terminal spray (crossed for volume)
        sd = unit(branch_dir + np.array([0, -0.3 if hemlock else 0.15, 0]))
        put_card(interp(p, 1.0) + sd*0.15*(height/18), sd, sideways0, 1.35 if hi else 3.0, drop, crossed=True)
        if hi:
            nsec = int(rng.integers(3, 6))
            for k in range(nsec):
                tt = 0.35 + 0.6*k/max(1, nsec-1)
                origin = interp(p, tt)
                sign = 1 if (k + j) % 2 else -1
                sideways = sideways0*sign
                sd = unit(radial*0.4 + sideways*0.85 + np.array([0, rng.uniform(-0.4, 0.0) if hemlock else rng.uniform(0.0, 0.45), 0]))
                L = rng.uniform(0.7, 1.4)*(1 - 0.35*tt)*(height/18)
                sp, st = curved(origin, origin + sd*L, np.array([0, -0.12 if hemlock else 0.05, 0]), 3)
                bark.tube(sp, 0.02*(1-st) + 0.005, 4, color=(1, 1, 1), cap=False)
                for m2 in range(4):
                    q = 0.3 + 0.7*m2/3
                    put_card(interp(sp, q) + sideways*rng.uniform(-0.15, 0.15), sd, sideways, 1.1, drop, crossed=(m2 == 3))
    if not hi and not dead:
        # Crown-mass cards for the mid-distance LOD. These carry the silhouette between roughly
        # 46 m and 230 m, which is most of the visible forest, so they have to fill the crown the
        # branches actually reach.
        #
        # They previously did not. Four cards were sized as cw*1.1 and then passed through
        # `sz*h*1.15`, where h is the atlas box's height as a fraction of the atlas — about 0.39.
        # That put each card at roughly 2 m inside a crown 12 m across: about a sixth of the width,
        # four times over. The stand thinned to poles across the whole middle distance.
        #
        # Sizing here is in metres, against the bounding box the branch cards just built, so it
        # cannot drift out of step with the branch geometry again. The vertical taper follows the
        # conical habit of both species.
        P = np.asarray(foliage.p, np.float32)
        if len(P):
            lo, hb = P.min(0), P.max(0)
            crown_r = max(hb[0] - lo[0], hb[2] - lo[2])*0.5
            crown_v = max(hb[1] - lo[1], 0.5)
            # Each card is seeded on a vertex of the foliage already built, jittered slightly.
            # Sampling the real distribution rather than a guessed cone means the added mass lands
            # exactly where this tree's branches are: it densifies the crown instead of reshaping
            # it, and both species keep their own habit — the spreading, drooping laterals of the
            # hemlock and the ascending ones of the cypress — with no per-species tuning here.
            ncards = int(np.clip(round(34*crown_r*crown_v/60.0), 26, 54))
            jit = crown_v*0.035
            for k, i in enumerate(rng.integers(0, len(P), ncards)):
                c = P[i] + np.array([rng.uniform(-1, 1), rng.uniform(-0.6, 0.6), rng.uniform(-1, 1)])*jit
                box = CARDS[3 if k % 2 == 0 else 4]
                aspect = (box[2]-box[0])/(box[3]-box[1])
                length = crown_v*rng.uniform(0.13, 0.21)      # metres, along `sd`
                width = length*aspect
                sd = unit(np.array([rng.uniform(-1, 1), rng.uniform(0.15, 1.25), rng.uniform(-1, 1)]))
                a = k*2.399963
                nm = unit(np.array([math.cos(a), rng.uniform(-0.3, 0.5), math.sin(a)]))
                foliage.card(c, sd, nm, length, width, box, tint*rng.uniform(0.72, 0.96), fold=0.12)
    # leader
    for j in range(8 if hi else 3):
        t = 0.9 + 0.1*j/8; start = interp(trunk, t); a = j*2.399963
        sd = unit([math.cos(a)*0.7, 0.55, math.sin(a)*0.7]); L = (0.9 - 0.7*(t-0.9)/0.1)*(height/18)
        box = CARDS[int(rng.integers(len(CARDS)))]; w = (box[2]-box[0])/ATLAS; h = (box[3]-box[1])/ATLAS
        foliage.card(start + sd*L*0.6, sd, unit(np.array([0, 1, 0]) + np.array([math.sin(a), 0, -math.cos(a)])*0.3), 1.6*h*(height/18), 1.6*w*(height/18), box, tint*1.05, fold=0.3, tipdrop=0.1)
    return bark, foliage, deadwood

def build_far(kind, seed, height):
    """Far impostor: trunk billboard pair + 3 crossed foliage cards (very cheap)."""
    rng = np.random.default_rng(seed); bark, foliage, deadwood = Mesh(), Mesh(), Mesh()
    hemlock = kind == 'tsuga'
    r0 = (0.022 if hemlock else 0.019)*height/2
    bark.tube(np.array([[0, 0, 0], [0, height*0.55, 0], [0, height*0.98, 0]]), [r0*1.2, r0*0.6, 0.03], 4, color=(1, 1, 1))
    tint = (np.array([0.55, 0.62, 0.50]) if hemlock else np.array([0.80, 0.86, 0.55]))*0.9
    for j in range(3):
        a = j*math.pi/3; sd = np.array([0, 1, 0]); normal = np.array([math.cos(a), 0, math.sin(a)])
        box = CARDS[3 if j != 1 else 4]; w = (box[2]-box[0])/ATLAS; h = (box[3]-box[1])/ATLAS
        size = height*0.72
        foliage.card(np.array([0, height*0.62, 0]), sd, normal, size*h*1.4, size*w*1.4, box, tint, fold=0.0)
    return bark, foliage, deadwood


def build_log(seed):
    """Fallen trunk lying on the ground (deadwood texture), mossed upper side, stub branches, broken end."""
    rng = np.random.default_rng(seed); bark, foliage, deadwood = Mesh(), Mesh(), Mesh()
    L = rng.uniform(4.5, 8.0); r0 = rng.uniform(0.2, 0.36); bend = rng.uniform(-0.25, 0.25)
    pts = []; rad = []
    for t in np.linspace(0, 1, 11):
        pts.append([L*(t-0.5), r0*0.72 + 0.05*math.sin(t*7.0+seed), bend*math.sin(math.pi*t)]); rad.append(r0*(1-0.55*t) + 0.02)
    def col(j, a):
        moss = max(0.0, math.sin(a))**0.7*(0.55 + 0.45*rng.random()*0)  # upper side
        moss *= 0.65 + 0.35*math.sin(j*1.3 + seed)
        return (1 - 0.5*moss, 1 - 0.2*moss, 1 - 0.65*moss)
    deadwood.tube(np.array(pts), rad, 9, color=col, flute=0.09, uvscale=(0.9, 1.6), ground_clip=False, cap=True)
    for k in range(int(rng.integers(2, 5))):
        t = rng.uniform(0.15, 0.85); base = interp(np.array(pts), t); a = rng.uniform(0, 2*math.pi)
        d = np.array([math.sin(a)*0.5, abs(math.cos(a))*0.9 + 0.1, math.cos(a)*0.5]); Lb = rng.uniform(0.3, 1.1)
        p2, tt = curved(base, base + unit(d)*Lb, np.array([0, 0.05, 0]), 3)
        deadwood.tube(p2, 0.06*(1-tt) + 0.012, 5, color=(1, 1, 1), ground_clip=False)
    return bark, foliage, deadwood

def build_rock(seed):
    """Lava block: angular displaced icosphere, flattened base, moss vertex tint on upward faces (PROCEDURAL Jogan clinker form)."""
    import trimesh
    rng = np.random.default_rng(seed); bark, foliage, deadwood = Mesh(), Mesh(), Mesh()
    m = trimesh.creation.icosphere(subdivisions=3, radius=1.0); v = np.asarray(m.vertices).copy(); f = np.asarray(m.faces)
    # angular facets: cellular displacement + noise, anisotropic scale
    sc = np.array([rng.uniform(0.8, 1.4), rng.uniform(0.45, 0.8), rng.uniform(0.7, 1.2)])
    cells = rng.normal(size=(7, 3)); cells /= np.linalg.norm(cells, axis=1, keepdims=True)
    disp = np.zeros(len(v))
    for c in cells: disp += np.clip(v @ c - 0.55, 0, None)*rng.uniform(0.6, 1.4)
    n1 = np.sin(v[:, 0]*5.1 + seed) * np.cos(v[:, 2]*4.3) * 0.08 + np.sin(v[:, 1]*9.0 + v[:, 0]*3.0) * 0.05
    v = v*(1 - 0.35*disp[:, None] + n1[:, None])*sc
    v[:, 1] = np.maximum(v[:, 1], -0.25*sc[1])   # buried base
    v[:, 1] += 0.1
    rock = Mesh()
    # normals from faces
    nrm = np.zeros_like(v); fn = np.cross(v[f[:, 1]]-v[f[:, 0]], v[f[:, 2]]-v[f[:, 0]])
    for i in range(3): np.add.at(nrm, f[:, i], fn)
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    up = np.clip(nrm[:, 1], 0, 1)
    mossn = np.sin(v[:, 0]*4.0 + seed*0.3)*0.5 + 0.5
    for i in range(len(v)):
        ax = np.argmax(np.abs(nrm[i]));
        uv = [v[i][(ax+1) % 3]*0.7, v[i][(ax+2) % 3]*0.7]
        moss = (up[i]**1.6)*(0.45 + 0.55*mossn[i])
        rock.vertex(v[i], nrm[i], uv, (1 - 0.55*moss + 0.05, 1 - 0.15*moss + 0.05, 1 - 0.7*moss + 0.02))
    rock.i = f.tolist()
    return rock, foliage, deadwood

# ---------------------------------------------------------------- GLB writer
class GLB:
    def __init__(self):
        self.g = {'asset': {'version': '2.0', 'generator': 'Aokigahara tree library v2 (procedural)'}, 'scene': 0, 'scenes': [{'nodes': []}], 'nodes': [], 'meshes': [], 'accessors': [], 'bufferViews': [], 'buffers': [{'byteLength': 0}], 'materials': [], 'textures': [], 'images': [], 'samplers': [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}]}
        self.b = bytearray()
    def buffer(self, b, target=None):
        self.b.extend(b'\0'*((-len(self.b)) % 4)); v = {'buffer': 0, 'byteOffset': len(self.b), 'byteLength': len(b)}
        if target: v['target'] = target
        self.b.extend(b); self.g['bufferViews'].append(v); return len(self.g['bufferViews'])-1
    def accessor(self, a, typ):
        a = np.ascontiguousarray(a); a = a.astype('<f4') if a.dtype.kind == 'f' else a.astype('<u4')
        v = self.buffer(a.tobytes(), 34963 if typ == 'SCALAR' else 34962)
        d = {'bufferView': v, 'componentType': 5126 if a.dtype.kind == 'f' else 5125, 'count': int(len(a)), 'type': typ}
        if typ == 'VEC3' and a.dtype.kind == 'f': d.update(min=a.min(0).tolist(), max=a.max(0).tolist())
        self.g['accessors'].append(d); return len(self.g['accessors'])-1
    def tex(self, p):
        p = Path(p); self.g['images'].append({'name': p.stem, 'bufferView': self.buffer(p.read_bytes()), 'mimeType': 'image/png' if p.suffix.lower() == '.png' else 'image/jpeg'})
        self.g['textures'].append({'source': len(self.g['images'])-1, 'sampler': 0}); return len(self.g['textures'])-1
    def material(self, name, base=None, normal=None, rough=None, double=False, alpha=None, normal_scale=0.8, extras=None):
        p = {'baseColorFactor': [1, 1, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 0.9}
        if base: p['baseColorTexture'] = {'index': self.tex(base)}
        if rough:
            im = Image.open(rough).convert('L'); packed = Image.merge('RGB', (Image.new('L', im.size, 255), im, Image.new('L', im.size, 0)))
            tmp = TEX/(Path(rough).stem+'_MR.jpg'); packed.save(tmp, quality=85); p['metallicRoughnessTexture'] = {'index': self.tex(tmp)}
        d = {'name': name, 'pbrMetallicRoughness': p, 'doubleSided': double}
        if normal: d['normalTexture'] = {'index': self.tex(normal), 'scale': normal_scale}
        if alpha: d['alphaMode'] = 'MASK'; d['alphaCutoff'] = alpha
        if extras: d['extras'] = extras
        self.g['materials'].append(d); return len(self.g['materials'])-1
    def primitive(self, mesh, material):
        P, Nn, UV, C, I = mesh.arrays()
        at = {'POSITION': self.accessor(P, 'VEC3'), 'NORMAL': self.accessor(Nn, 'VEC3'), 'TEXCOORD_0': self.accessor(UV, 'VEC2'), 'COLOR_0': self.accessor(C[:, :3], 'VEC3')}
        return {'attributes': at, 'indices': self.accessor(I.reshape(-1), 'SCALAR'), 'material': material}, len(I)
    def mesh(self, name, prims, extras=None):
        d = {'name': name, 'primitives': prims}
        if extras: d['extras'] = extras
        self.g['meshes'].append(d); return len(self.g['meshes'])-1
    def node(self, name, mesh, extras=None):
        d = {'name': name, 'mesh': mesh}
        if extras: d['extras'] = extras
        self.g['nodes'].append(d); self.g['scenes'][0]['nodes'].append(len(self.g['nodes'])-1)
    def save(self, p, extras=None):
        if extras: self.g['extras'] = extras
        self.g['buffers'][0]['byteLength'] = len(self.b); j = json.dumps(self.g, separators=(',', ':')).encode(); j += b' '*((-len(j)) % 4)
        b = bytes(self.b); b += b'\0'*((-len(b)) % 4)
        Path(p).write_bytes(struct.pack('<III', 0x46546c67, 2, 28+len(j)+len(b)) + struct.pack('<II', len(j), 0x4e4f534a) + j + struct.pack('<II', len(b), 0x004e4942) + b)
        return Path(p).stat().st_size

if __name__ == '__main__':
    g = GLB()
    m_fir = g.material('Bark tsuga-like: Poly Haven fir_tree_01 bark (CC0), representative', TEX/'fir_tree_c__fir_tree_01_bark_diff.jpg', TEX/'fir_tree_c__fir_tree_01_bark_nor_gl.jpg', TEX/'fir_tree_c__fir_tree_01_bark_rough.jpg', normal_scale=0.9)
    m_cedar = g.material('Bark hinoki-like: Poly Haven japanese_cedar_bark (CC0), representative', MAT/'japanese_cedar_bark_diff_1k.jpg', MAT/'japanese_cedar_bark_nor_gl_1k.jpg', MAT/'japanese_cedar_bark_rough_1k.jpg', normal_scale=0.9)
    m_dead = g.material('Dead wood: Poly Haven dead_tree_trunk (CC0), representative', TEX/'dead_tree_trunk__dead_tree_trunk_diff.jpg', TEX/'dead_tree_trunk__dead_tree_trunk_nor_gl.jpg', TEX/'dead_tree_trunk__dead_tree_trunk_rough.jpg', normal_scale=0.8)
    m_twig = g.material('Foliage cards: Poly Haven fir_tree_01 twig atlas (CC0); fir sprays as representative conifer foliage', TEX/'twig_atlas_boost.png', TEX/'fir_tree_c__fir_tree_01_twig_nor_gl.jpg', TEX/'fir_tree_c__fir_tree_01_twig_rough.jpg', double=True, alpha=0.3, normal_scale=0.5)
    variants = []
    # (name, kind, seed, height, dead, lean, note)
    specs = [
        ('tsuga_a', 'tsuga', 1101, 19.0, False, 0.05), ('tsuga_b', 'tsuga', 1102, 21.5, False, 0.09), ('tsuga_c', 'tsuga', 1103, 16.0, False, 0.14),
        ('hinoki_a', 'hinoki', 2201, 18.0, False, 0.03), ('hinoki_b', 'hinoki', 2202, 20.0, False, 0.07), ('hinoki_c', 'hinoki', 2203, 15.0, False, 0.11),
        ('snag_a', 'tsuga', 3301, 17.0, True, 0.04), ('snag_b', 'tsuga', 3302, 13.0, True, 0.12),
        ('sap_tsuga', 'tsuga', 4401, 4.2, False, 0.06), ('sap_hinoki', 'hinoki', 4402, 3.4, False, 0.04), ('sap_small', 'hinoki', 4403, 1.8, False, 0.03),
    ]
    stats = {}
    for name, kind, seed, height, dead, lean in specs:
        for lod in (['high', 'low', 'far'] if not dead else ['high', 'low']):
            if lod == 'far': bark, fol, dw = build_far(kind, seed, height)
            else: bark, fol, dw = build_conifer(kind if not name.startswith('sap') else kind, seed, height, lod, dead=dead, lean=lean)
            prims = []; tris = 0
            for mesh, mat in [(bark, m_fir if kind == 'tsuga' else m_cedar), (fol, m_twig), (dw, m_dead)]:
                if len(mesh.i) == 0: continue
                pr, n = g.primitive(mesh, mat); prims.append(pr); tris += n
            mi = g.mesh(f'{name}_{lod}', prims, extras={'variant': name, 'kind': kind, 'lod': lod, 'height_m': height, 'dead': dead, 'lean': lean, 'status': 'PROCEDURAL; not a surveyed individual; species-suggestive only'})
            g.node(f'{name}_{lod}', mi); stats[f'{name}_{lod}'] = tris
    m_rock = g.material('Lava block: procedural basalt maps (materials_v2), moss vertex tint', ROOT/'viewer/assets/materials_v2/basalt_diff_1k.jpg', ROOT/'viewer/assets/materials_v2/basalt_nor_gl_1k.jpg', ROOT/'viewer/assets/materials_v2/basalt_rough_1k.jpg', normal_scale=0.9)
    for name, seed in [('log_a', 5501), ('log_b', 5502)]:
        bark, fol, dw = build_log(seed); pr, n = g.primitive(dw, m_dead)
        g.node(f'{name}_high', g.mesh(f'{name}_high', [pr], extras={'variant': name, 'kind': 'fallen log', 'status': 'PROCEDURAL deadwood; not a surveyed object'})); stats[f'{name}_high'] = n
    for k, name in enumerate(['rock_a', 'rock_b', 'rock_c', 'rock_d']):
        rk, fol, dw = build_rock(6601 + k); pr, n = g.primitive(rk, m_rock)
        g.node(f'{name}_high', g.mesh(f'{name}_high', [pr], extras={'variant': name, 'kind': 'lava block', 'status': 'PROCEDURAL Jogan clinker block form; not a scanned rock'})); stats[f'{name}_high'] = n
    size = g.save(OUT, extras={'library': 'Aokigahara tree library v2', 'provenance': __doc__.strip(), 'triangles': stats})
    print('saved', OUT, size, 'bytes'); print(json.dumps(stats, indent=1))
    (ROOT/'viewer/assets/tree-library-v2.json').write_text(json.dumps({'file': 'tree-library-v2.glb', 'sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(), 'bytes': size, 'meshes': stats, 'lods': ['high', 'low', 'far'], 'variants': [s[0] for s in specs], 'generator': 'construction_code_v2/generate_trees_v2.py', 'provenance': __doc__.strip()}, indent=2))
