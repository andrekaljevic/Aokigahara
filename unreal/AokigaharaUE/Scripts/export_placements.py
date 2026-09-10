"""Convert the source forest placements into Unreal-space records, with validation.

    python3 unreal/AokigaharaUE/Scripts/export_placements.py [--out DIR] [--csv]

Reads `data/forest-wide.f32` - 467,601 records of six little-endian float32:

    [0] x east m   [1] y scene m   [2] z south m   [3] scale   [4] yaw radians   [5] class 0-3

and writes Unreal-space records plus a JSON sidecar describing them. `viewer/assets/forest-
instances.f32` is NOT read: it is byte-identical to the first 53,999 records of the wide file, and
ingesting both would duplicate 53,999 trees. The script asserts that identity rather than trusting
this comment.

Output (not committed - regenerate it, it is derived):

    placements_ue.bin    N x 6 float32: UE_X_cm, UE_Y_cm, UE_Z_cm, yaw_deg, scale, class
    placements_ue.json   counts, per-class histogram, bounds in both frames, provenance
    placements_ue.csv    optional, --csv, for eyeballing or a UE DataTable

The binary is deliberately the same shape as the source so the conversion is auditable field by
field, and so the UE-side importer is a single `np.fromfile(...).reshape(-1, 6)`.

Everything numeric goes through `aokigahara_geo`, which is tested against 78 surveyed control
points by `test_geo.py`. In particular the handedness flip and the yaw convention live there and
are not reimplemented here.
"""

import argparse
import json
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aokigahara_geo as geo  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
WIDE = os.path.join(REPO, 'data/forest-wide.f32')
CORRIDOR = os.path.join(REPO, 'viewer/assets/forest-instances.f32')
DEFAULT_OUT = os.path.join(REPO, 'unreal/AokigaharaUE/Content/Aokigahara/Data')

REC = 6                       # float32 fields per record
FMT = '<%df' % REC

# From viewer/assets/terrain/local-context.json -> landcoverClasses, and how viewer/app.js uses
# column 5. Recorded here so the UE side does not have to guess what a class means.
CLASS_MEANING = {
    0: 'community class 0 - conifer-dominant stand',
    1: 'community class 1 - conifer-dominant stand, second variant group',
    2: 'community class 2 - deciduous broadleaved association (app.js biases these to broadleaf)',
    3: 'community class 3 - mixed / transitional',
}


def read_records(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    if len(raw) % (REC * 4):
        raise SystemExit('%s: size %d is not a multiple of %d bytes' % (path, len(raw), REC * 4))
    n = len(raw) // (REC * 4)
    return raw, n


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=DEFAULT_OUT)
    ap.add_argument('--csv', action='store_true', help='also write a CSV (about 30 MB)')
    args = ap.parse_args()

    if not os.path.exists(WIDE):
        raise SystemExit('missing %s' % WIDE)
    raw, n = read_records(WIDE)
    print('source: %s  %d records' % (os.path.relpath(WIDE, REPO), n))

    # Assert the duplication rather than trusting it, because ingesting both files would place
    # 53,999 trees twice and the doubling would be invisible in a screenshot.
    if os.path.exists(CORRIDOR):
        craw, cn = read_records(CORRIDOR)
        dup = craw == raw[:len(craw)]
        print('corridor file: %d records, identical to the first %d of the wide set: %s'
              % (cn, cn, dup))
        if not dup:
            raise SystemExit('ABORT: the corridor file is NOT a prefix of the wide file. The '
                             'assumption that the wide file is a superset no longer holds; '
                             'ingesting only the wide file would silently drop placements.')

    os.makedirs(args.out, exist_ok=True)
    out_bin = os.path.join(args.out, 'placements_ue.bin')
    out_json = os.path.join(args.out, 'placements_ue.json')

    hist = {}
    s_min = [float('inf')] * 3
    s_max = [float('-inf')] * 3
    u_min = [float('inf')] * 3
    u_max = [float('-inf')] * 3
    scale_min, scale_max = float('inf'), float('-inf')
    bad_yaw = bad_scale = 0

    with open(out_bin, 'wb') as fh:
        for i in range(n):
            x, y, z, scale, yaw, cls = struct.unpack_from(FMT, raw, i * REC * 4)

            if not (-1e-3 <= yaw <= 2 * math.pi + 1e-3):
                bad_yaw += 1
            if not (0.05 < scale < 20.0):
                bad_scale += 1

            ue_x, ue_y, ue_z = geo.scene_to_ue(x, y, z)
            yaw_deg = geo.scene_yaw_to_ue_yaw(yaw)

            for j, v in enumerate((x, y, z)):
                s_min[j] = min(s_min[j], v)
                s_max[j] = max(s_max[j], v)
            for j, v in enumerate((ue_x, ue_y, ue_z)):
                u_min[j] = min(u_min[j], v)
                u_max[j] = max(u_max[j], v)
            scale_min = min(scale_min, scale)
            scale_max = max(scale_max, scale)
            k = int(cls)
            hist[k] = hist.get(k, 0) + 1

            fh.write(struct.pack(FMT, ue_x, ue_y, ue_z, yaw_deg, scale, float(k)))

    if bad_yaw or bad_scale:
        print('WARNING: %d yaw values outside [0, 2pi], %d scales outside (0.05, 20)'
              % (bad_yaw, bad_scale))

    # Round-trip a sample back through the inverse transform as a self-check.
    worst = 0.0
    step = max(1, n // 5000)
    for i in range(0, n, step):
        x, y, z, _, _, _ = struct.unpack_from(FMT, raw, i * REC * 4)
        bx, by, bz = geo.ue_to_scene(*geo.scene_to_ue(x, y, z))
        worst = max(worst, abs(bx - x), abs(by - y), abs(bz - z))

    meta = {
        'generator': 'unreal/AokigaharaUE/Scripts/export_placements.py',
        'source': os.path.relpath(WIDE, REPO),
        'source_record': '6 x float32 LE: x east m, y scene m, z south m, scale, yaw rad, class',
        'output_record': '6 x float32 LE: UE_X_cm, UE_Y_cm, UE_Z_cm, yaw_deg, scale, class',
        'count': n,
        'corridor_file_is_prefix_of_wide': True,
        'note': ('viewer/assets/forest-instances.f32 is byte-identical to the first 53,999 '
                 'records of the wide file. Ingest the wide file ONLY; the total number of '
                 'unique placements is %d, not %d.' % (n, n + 53999)),
        'class_histogram': {str(k): v for k, v in sorted(hist.items())},
        'class_meaning': {str(k): v for k, v in CLASS_MEANING.items()},
        'scale_range': [scale_min, scale_max],
        'bounds_scene_m': {'min': s_min, 'max': s_max,
                           'axes': 'x east, y up (elevation-900), z south'},
        'bounds_ue_cm': {'min': u_min, 'max': u_max, 'axes': 'X north, Y east, Z up'},
        'extent_m': {'east_west': s_max[0] - s_min[0], 'north_south': s_max[2] - s_min[2],
                     'vertical': s_max[1] - s_min[1]},
        'coordinate_mapping': 'UE_X = -z*100, UE_Y = x*100, UE_Z = y*100 (determinant -1)',
        'yaw_mapping': 'UE_yaw_deg = (90 - degrees(scene_yaw)) mod 360',
        'vertical_datum': 'UE Z = 0 is 900 m MSL, not sea level',
        'roundtrip_max_error_m': worst,
    }
    with open(out_json, 'w') as fh:
        json.dump(meta, fh, indent=2)

    print('\nwrote %s  (%d bytes)' % (os.path.relpath(out_bin, REPO), os.path.getsize(out_bin)))
    print('wrote %s' % os.path.relpath(out_json, REPO))
    print('\n  class histogram      %s' % meta['class_histogram'])
    print('  scale range          %.3f .. %.3f' % (scale_min, scale_max))
    print('  scene bounds  x  %10.2f .. %10.2f m' % (s_min[0], s_max[0]))
    print('                y  %10.2f .. %10.2f m' % (s_min[1], s_max[1]))
    print('                z  %10.2f .. %10.2f m' % (s_min[2], s_max[2]))
    print('  UE bounds     X  %10.0f .. %10.0f cm  (north)' % (u_min[0], u_max[0]))
    print('                Y  %10.0f .. %10.0f cm  (east)' % (u_min[1], u_max[1]))
    print('                Z  %10.0f .. %10.0f cm  (up)' % (u_min[2], u_max[2]))
    print('  extent           %.0f m E-W  x  %.0f m N-S' % (meta['extent_m']['east_west'],
                                                            meta['extent_m']['north_south']))
    print('  round-trip error %.3e m over %d sampled records' % (worst, len(range(0, n, step))))

    if args.csv:
        out_csv = os.path.join(args.out, 'placements_ue.csv')
        with open(out_csv, 'w') as fh:
            fh.write('Name,X,Y,Z,Yaw,Scale,Class\n')
            for i in range(n):
                x, y, z, scale, yaw, cls = struct.unpack_from(FMT, raw, i * REC * 4)
                ux, uy, uz = geo.scene_to_ue(x, y, z)
                fh.write('%d,%.2f,%.2f,%.2f,%.4f,%.5f,%d\n'
                         % (i, ux, uy, uz, geo.scene_yaw_to_ue_yaw(yaw), scale, int(cls)))
        print('wrote %s  (%d bytes)' % (os.path.relpath(out_csv, REPO), os.path.getsize(out_csv)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
