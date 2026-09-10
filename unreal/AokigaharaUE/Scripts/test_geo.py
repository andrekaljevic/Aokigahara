"""Tests for aokigahara_geo, run against real surveyed control points.

    python3 unreal/AokigaharaUE/Scripts/test_geo.py

Dependency-free by default so it can run inside Unreal's embedded Python. If pyproj and numpy
happen to be importable, two extra cross-checks run: the projection against PROJ itself, and the
handedness of the Unreal mapping against a determinant.

Exits non-zero on any failure. Nothing here is a smoke test - every assertion has a number behind
it and a tolerance chosen from the precision of the source data.
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aokigahara_geo as geo  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
CONTEXTS = [os.path.join(REPO, 'viewer/assets/terrain/%s-context.json' % n)
            for n in ('local', 'study')]

_failures = []


def check(name, ok, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('   ' + detail) if detail else ''))
    if not ok:
        _failures.append(name)


def load_landmarks():
    """Every landmark carrying both a scene position and a WGS 84 position, de-duplicated by id."""
    out = {}
    for path in CONTEXTS:
        if not os.path.exists(path):
            continue
        with open(path) as fh:
            for m in json.load(fh).get('landmarks', []):
                if m.get('wgs84') and m.get('coordinates'):
                    out[m['id']] = m
    return list(out.values())


# ---------------------------------------------------------------- tests

def test_projection_against_landmarks(landmarks):
    """The projection must reproduce the stored scene coordinates of real surveyed points."""
    errs = []
    for m in landmarks:
        lon, lat = m['wgs84']
        sx, sz = m['coordinates']
        x, z = geo.wgs84_to_scene(lon, lat)
        errs.append(math.hypot(x - sx, z - sz))
    errs.sort()
    worst = errs[-1]
    median = errs[len(errs) // 2]
    # Stored coordinates carry two decimals, so ~7 mm is the floor for a perfect transform.
    check('projection reproduces %d landmarks' % len(landmarks), worst < 0.02,
          'median %.4f m, max %.4f m' % (median, worst))


def test_falsifier(landmarks):
    """Not negating the northing must be badly wrong - proves the south-axis convention."""
    errs = []
    for m in landmarks:
        lon, lat = m['wgs84']
        sx, sz = m['coordinates']
        x, z = geo.wgs84_to_scene(lon, lat)
        errs.append(math.hypot(x - sx, (-z) - sz))   # deliberately wrong sign
    errs.sort()
    median = errs[len(errs) // 2]
    check('falsifier: unnegated northing is grossly wrong', median > 100.0,
          'median %.1f m' % median)


def test_roundtrip(landmarks):
    """scene -> WGS 84 -> scene must return to the same point."""
    worst = 0.0
    for m in landmarks:
        sx, sz = m['coordinates']
        lon, lat = geo.scene_to_wgs84(sx, sz)
        x, z = geo.wgs84_to_scene(lon, lat)
        worst = max(worst, math.hypot(x - sx, z - sz))
    # Vincenty's iteration converges to a few micrometres, which is the floor here and is six
    # orders of magnitude finer than the 2 cm precision of the source data. 1 mm is a real bound.
    check('scene -> wgs84 -> scene round-trips', worst < 1e-3, 'max %.3e m' % worst)


def test_elevation(landmarks):
    """The 900 m offset must match the elevationM / worldY pairs stored in the data."""
    worst = 0.0
    n = 0
    for m in landmarks:
        if m.get('elevationM') is None or m.get('worldY') is None:
            continue
        n += 1
        worst = max(worst, abs(geo.msl_to_scene_y(m['elevationM']) - m['worldY']))
    check('height offset matches %d stored elevation/worldY pairs' % n, worst < 0.011,
          'max %.4f m' % worst)


def test_ue_roundtrip():
    """scene -> UE -> scene must be exact, and the axes must land where claimed."""
    worst = 0.0
    for x, y, z in ((0, 0, 0), (100, 5, -250), (-1024, 164.4, 1024), (3776.47, 628.25, -2697.03)):
        bx, by, bz = geo.ue_to_scene(*geo.scene_to_ue(x, y, z))
        worst = max(worst, abs(bx - x), abs(by - y), abs(bz - z))
    check('scene -> UE -> scene round-trips', worst < 1e-9, 'max %.3e m' % worst)

    # 100 m due north in the scene is z = -100; it must become UE +X.
    ue = geo.scene_to_ue(0.0, 0.0, -100.0)
    check('100 m north  -> UE +X', abs(ue[0] - 10000.0) < 1e-6 and abs(ue[1]) < 1e-6, str(ue))
    # 100 m due east in the scene is x = +100; it must become UE +Y.
    ue = geo.scene_to_ue(100.0, 0.0, 0.0)
    check('100 m east   -> UE +Y', abs(ue[1] - 10000.0) < 1e-6 and abs(ue[0]) < 1e-6, str(ue))
    # 10 m up must become UE +Z.
    ue = geo.scene_to_ue(0.0, 10.0, 0.0)
    check('10 m up      -> UE +Z', abs(ue[2] - 1000.0) < 1e-6, str(ue))


def test_handedness_by_construction():
    """The mapping must flip handedness. Computed as a 3x3 determinant without numpy."""
    e1 = geo.scene_to_ue(1, 0, 0)
    e2 = geo.scene_to_ue(0, 1, 0)
    e3 = geo.scene_to_ue(0, 0, 1)
    det = (e1[0] * (e2[1] * e3[2] - e2[2] * e3[1])
           - e1[1] * (e2[0] * e3[2] - e2[2] * e3[0])
           + e1[2] * (e2[0] * e3[1] - e2[1] * e3[0]))
    # scale is 100 per axis, so a pure flip gives -100^3
    check('UE mapping flips handedness (det < 0)', det < 0, 'det = %+.0f' % det)


def test_yaw():
    """Scene yaw about +y must map onto Unreal yaw about +Z consistently with the axes."""
    worst = 0.0
    for deg in range(0, 360, 15):
        th = math.radians(deg)
        # three.js rotation about +Y sends (1,0,0) -> (cos th, 0, -sin th) in scene (x, y, z)
        vx, vy, vz = math.cos(th), 0.0, -math.sin(th)
        ux, uy, _ = geo.scene_to_ue(vx, vy, vz)
        expected = math.degrees(math.atan2(uy, ux)) % 360.0
        got = geo.scene_yaw_to_ue_yaw(th)
        diff = abs((got - expected + 180.0) % 360.0 - 180.0)
        worst = max(worst, diff)
    check('scene yaw -> UE yaw matches the axis mapping', worst < 1e-9, 'max %.3e deg' % worst)

    worst = 0.0
    for deg in range(0, 360, 15):
        th = math.radians(deg)
        back = geo.ue_yaw_to_scene_yaw(geo.scene_yaw_to_ue_yaw(th))
        diff = abs((math.degrees(back - th) + 180.0) % 360.0 - 180.0)
        worst = max(worst, diff)
    check('yaw round-trips', worst < 1e-9, 'max %.3e deg' % worst)


def test_against_pyproj(landmarks):
    """Optional: agree with PROJ itself, which is the reference implementation."""
    try:
        from pyproj import CRS, Transformer
    except ImportError:
        print('  SKIP  cross-check against pyproj (not installed)')
        return
    fwd = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_proj4(geo.PROJ4), always_xy=True)
    worst = 0.0
    for m in landmarks:
        lon, lat = m['wgs84']
        E, N = fwd.transform(lon, lat)
        x, z = geo.wgs84_to_scene(lon, lat)
        worst = max(worst, math.hypot(x - E, z - (-N)))
    check('agrees with pyproj over %d landmarks' % len(landmarks), worst < 0.001,
          'max %.6f m' % worst)


def main():
    landmarks = load_landmarks()
    if not landmarks:
        print('FATAL: no landmarks found; expected them in ' + ', '.join(CONTEXTS))
        return 2
    print('aokigahara_geo: %d control points\n' % len(landmarks))
    test_projection_against_landmarks(landmarks)
    test_falsifier(landmarks)
    test_roundtrip(landmarks)
    test_elevation(landmarks)
    test_ue_roundtrip()
    test_handedness_by_construction()
    test_yaw()
    test_against_pyproj(landmarks)
    print('\n' + ('ALL CHECKS PASSED' if not _failures
                  else 'FAILED (%d): %s' % (len(_failures), ', '.join(_failures))))
    return 1 if _failures else 0


if __name__ == '__main__':
    sys.exit(main())
