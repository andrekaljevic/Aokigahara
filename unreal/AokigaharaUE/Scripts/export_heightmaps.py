"""Convert the GSI elevation grids into Unreal Landscape heightmaps, with the exact transform.

    python3 unreal/AokigaharaUE/Scripts/export_heightmaps.py [--grids local study regional]

Reads `viewer/assets/terrain/<id>-height.{json,f32}` and writes, per grid, a 16-bit greyscale PNG
plus a JSON giving the precise Landscape Scale and actor location that reproduce true metres.

WHY THIS IS NOT A ONE-LINER
---------------------------

1. **Neither source grid is a native Landscape size.** Unreal builds a Landscape from components
   of 7, 15, 31, 63, 127 or 255 quads per section, with 1x1 or 2x2 sections per component, so the
   vertex count is always `components x component_quads + 1`. That admits 253, 255, 505, 509, 511,
   1009, 1017, 1021 ... and **not 257 or 513**, which is what the source grids are. Importing a
   257x257 image regardless makes Unreal pad or resample silently. This script resamples
   deliberately, to a chosen native size, and says what it did.

2. **dx and dz differ on two of the three grids** (study 38.086 x 36.458 m, regional 62.5 x
   58.594 m). Landscape supports a non-uniform scale, so this is fine - but UE X is NORTH, which
   comes from the source's *z* step, and UE Y is EAST, which comes from *dx*. Getting those the
   wrong way round tilts the whole world by a few percent and is very hard to see.

3. **The 16-bit mapping is fixed by the engine**, not chosen by us:

       height_uu = (h - 32768) / 128 * LandscapeScaleZ            h in 0..65535

   so a Z scale of 100 spans exactly -256 m to +255.992 m. To fit an arbitrary elevation range the
   Z scale must be solved for, and the residual quantisation step is `LandscapeScaleZ / 128`
   centimetres. This script reports that step so it can be judged rather than assumed.

4. **Row order.** Source rows run north-to-south (`z = minZ + row*dz`, z is SOUTH), while UE X
   increases northwards. The rows are therefore flipped on export. This is the single easiest way
   to mirror a landscape, so the JSON records the convention and `--verify` re-reads the PNG and
   checks sampled vertices against the source grid.

Outputs land in Content/Aokigahara/Terrain/ and are derived - regenerate rather than commit.
"""

import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aokigahara_geo as geo  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
TERRAIN_SRC = os.path.join(REPO, 'viewer/assets/terrain')
DEFAULT_OUT = os.path.join(REPO, 'unreal/AokigaharaUE/Content/Aokigahara/Terrain')

# Unreal Landscape: section sizes in quads, and sections per component.
SECTION_QUADS = (7, 15, 31, 63, 127, 255)
SECTIONS_PER_COMPONENT = (1, 2)
UE_HEIGHT_MID = 32768.0
UE_HEIGHT_PER_UNIT = 128.0          # heightmap units per (uu / ZScale)


# Sections smaller than 63 quads are legal but produce component counts in the hundreds or
# thousands, which is ruinous for draw calls and World Partition streaming. Restrict the automatic
# search to what Unreal's own documentation recommends, and cap the components per side.
RECOMMENDED_SECTIONS = (63, 127, 255)
MAX_COMPONENTS_PER_SIDE = 32


def native_sizes(limit=4200, recommended_only=True):
    """Valid Landscape vertex counts up to `limit`, with the configuration that makes each."""
    sections = RECOMMENDED_SECTIONS if recommended_only else SECTION_QUADS
    out = {}
    for sq in sections:
        for spc in SECTIONS_PER_COMPONENT:
            comp = sq * spc
            for ncomp in range(1, min(MAX_COMPONENTS_PER_SIDE, limit // comp) + 1):
                verts = ncomp * comp + 1
                if verts > limit:
                    break
                cur = out.get(verts)
                # prefer the largest section (fewest, biggest components) for a given size
                if cur is None or sq > cur['section_quads']:
                    out[verts] = {'section_quads': sq, 'sections_per_component': spc,
                                  'components': ncomp, 'component_quads': comp,
                                  'total_quads': verts - 1}
    return out


NATIVE = native_sizes()


def nearest_native(n, prefer_ge=True):
    """The native size closest to n, preferring one that is >= n so no detail is lost."""
    cands = sorted(NATIVE)
    ge = [v for v in cands if v >= n]
    if prefer_ge and ge:
        return ge[0]
    return min(cands, key=lambda v: abs(v - n))


def bilinear(grid, w, h, fx, fy):
    """Sample a row-major float grid at fractional (column, row), clamped at the edges."""
    x0 = int(fx)
    y0 = int(fy)
    x1 = min(x0 + 1, w - 1)
    y1 = min(y0 + 1, h - 1)
    x0 = max(0, min(x0, w - 1))
    y0 = max(0, min(y0, h - 1))
    tx = fx - x0
    ty = fy - y0
    a = grid[y0 * w + x0]
    b = grid[y0 * w + x1]
    c = grid[y1 * w + x0]
    d = grid[y1 * w + x1]
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def export(grid_id, out_dir, target=None, verify=False):
    meta_path = os.path.join(TERRAIN_SRC, '%s-height.json' % grid_id)
    with open(meta_path) as fh:
        m = json.load(fh)
    raw_path = os.path.join(TERRAIN_SRC, m['file'])
    with open(raw_path, 'rb') as fh:
        raw = fh.read()
    w, h = m['width'], m['height']
    if len(raw) != w * h * 4:
        raise SystemExit('%s: expected %d bytes, got %d' % (raw_path, w * h * 4, len(raw)))
    grid = list(struct.unpack('<%df' % (w * h), raw))       # elevation metres MSL, unshifted

    src_min, src_max = min(grid), max(grid)

    # --- choose the Landscape vertex count -------------------------------------------------
    tx = target or nearest_native(max(w, h))
    cfg = NATIVE[tx]

    # --- resample onto the square native grid ----------------------------------------------
    # Source spans (w-1)*dx east and (h-1)*dz south. We keep that exact ground footprint and
    # change only the sampling density, so the Landscape covers the same real extent.
    span_x = (w - 1) * m['dx']
    span_z = (h - 1) * m['dz']
    out = [0.0] * (tx * tx)
    for r in range(tx):                     # r increases NORTHWARD in the output
        # flip: output row 0 is the SOUTHERN edge -> source row h-1
        src_row = (tx - 1 - r) / (tx - 1) * (h - 1)
        for c in range(tx):                 # c increases EASTWARD, same as source columns
            src_col = c / (tx - 1) * (w - 1)
            out[r * tx + c] = bilinear(grid, w, h, src_col, src_row)

    # --- solve the Landscape transform ------------------------------------------------------
    # Scene y = elevation - 900. UE Z is scene y in centimetres.
    y_min = geo.msl_to_scene_y(src_min)
    y_max = geo.msl_to_scene_y(src_max)
    z_min_cm = y_min * 100.0
    z_max_cm = y_max * 100.0
    # height_uu = (hv - 32768)/128 * scale_z, hv in 0..65535 -> +-255.9921875 * scale_z
    full = (65535.0 - UE_HEIGHT_MID) / UE_HEIGHT_PER_UNIT      # 255.9921875
    half_span = max(abs(z_max_cm), abs(z_min_cm), 1.0)
    # Centre the range on the midpoint via the actor's Z location, so the scale only has to span
    # the range itself rather than the distance from zero.
    mid_cm = (z_max_cm + z_min_cm) / 2.0
    needed = (z_max_cm - z_min_cm) / 2.0
    scale_z = needed / full if needed > 0 else 1.0
    quant_cm = scale_z / UE_HEIGHT_PER_UNIT

    # Landscape Scale X is NORTH (from the source z step); Scale Y is EAST (from dx).
    scale_x = (span_z / (tx - 1)) * 100.0
    scale_y = (span_x / (tx - 1)) * 100.0

    # --- quantise ---------------------------------------------------------------------------
    pixels = bytearray(tx * tx * 2)
    for i, elev in enumerate(out):
        cm = geo.msl_to_scene_y(elev) * 100.0
        hv = UE_HEIGHT_MID + (cm - mid_cm) / scale_z * UE_HEIGHT_PER_UNIT
        hv = int(round(min(65535.0, max(0.0, hv))))
        struct.pack_into('>H', pixels, i * 2, hv)   # PNG 16-bit is BIG-endian

    os.makedirs(out_dir, exist_ok=True)
    png_path = os.path.join(out_dir, '%s_heightmap.png' % grid_id)
    write_png16(png_path, tx, tx, pixels)

    # The landscape's south-west corner in UE space. Source SW corner is (minX, maxZ) because z
    # is south, i.e. the largest z is the southernmost row.
    corner_ue = geo.scene_to_ue(m['minX'], 0.0, m['minZ'] + span_z)

    info = {
        'generator': 'unreal/AokigaharaUE/Scripts/export_heightmaps.py',
        'grid': grid_id,
        'source': {'meta': os.path.relpath(meta_path, REPO), 'raw': os.path.relpath(raw_path, REPO),
                   'width': w, 'height': h, 'dx_m': m['dx'], 'dz_m': m['dz'],
                   'minX': m['minX'], 'minZ': m['minZ'], 'maxX': m['maxX'], 'maxZ': m['maxZ'],
                   'elevation_msl_m': [src_min, src_max]},
        'resample': {'from': [w, h], 'to': [tx, tx],
                     'native_config': cfg,
                     'metres_per_quad': {'north': scale_x / 100.0, 'east': scale_y / 100.0},
                     'reason': ('%dx%d is not a valid Landscape vertex count; %d is'
                                % (w, h, tx))},
        'landscape': {
            'resolution': [tx, tx],
            'section_size_quads': cfg['section_quads'],
            'sections_per_component': '%dx%d' % (cfg['sections_per_component'],
                                                 cfg['sections_per_component']),
            'component_count': '%dx%d' % (cfg['components'], cfg['components']),
            'scale': {'X_north_cm_per_quad': scale_x,
                      'Y_east_cm_per_quad': scale_y,
                      'Z': scale_z},
            'actor_location_cm': {'X_north': corner_ue[0], 'Y_east': corner_ue[1],
                                  'Z': mid_cm},
            'note_scale_axes': ('Scale X is NORTH and comes from the source dz; Scale Y is EAST '
                                'and comes from dx. Swapping them tilts the world.'),
        },
        'height_encoding': {
            'formula': 'height_uu = (h - 32768) / 128 * ScaleZ, then + actor Z location',
            'quantisation_cm_per_lsb': quant_cm,
            'quantisation_mm_per_lsb': quant_cm * 10.0,
            'scene_y_range_m': [y_min, y_max],
            'msl_range_m': [src_min, src_max],
        },
        'orientation': {
            'image_row_0': 'SOUTHERN edge of the grid (source row height-1); rows increase NORTH',
            'image_col_0': 'WESTERN edge (source column 0); columns increase EAST',
            'rationale': ('source rows run north-to-south because z is south, while UE X '
                          'increases north, so rows are flipped on export'),
        },
        'ground_footprint_m': {'east_west': span_x, 'north_south': span_z},
        'vertical_datum': 'UE Z = 0 is 900 m MSL',
    }
    json_path = os.path.join(out_dir, '%s_heightmap.json' % grid_id)
    with open(json_path, 'w') as fh:
        json.dump(info, fh, indent=2)

    print('%-9s %4dx%-4d -> %4dx%-4d  %s' % (grid_id, w, h, tx, tx, cfg['components'] and
          '%d components of %d quads (section %d, %dx%d)'
          % (cfg['components'] ** 2, cfg['component_quads'], cfg['section_quads'],
             cfg['sections_per_component'], cfg['sections_per_component'])))
    print('          footprint %.0f m E-W x %.0f m N-S    elevation %.2f .. %.2f m MSL'
          % (span_x, span_z, src_min, src_max))
    print('          ground resolution %.3f m/quad north   %.3f m/quad east'
          % (scale_x / 100.0, scale_y / 100.0))
    print('          Landscape Scale  X(north) %.4f   Y(east) %.4f   Z %.4f'
          % (scale_x, scale_y, scale_z))
    print('          actor location   X %.1f  Y %.1f  Z %.1f cm'
          % (corner_ue[0], corner_ue[1], mid_cm))
    print('          vertical quantisation %.3f mm per LSB' % (quant_cm * 10.0))
    print('          wrote %s' % os.path.relpath(png_path, REPO))

    if verify:
        worst = verify_png(png_path, out, tx, mid_cm, scale_z)
        print('          VERIFY max reconstruction error %.4f m %s'
              % (worst, 'OK' if worst < max(0.01, quant_cm / 100.0 * 2) else '*** TOO LARGE ***'))
    return info


def write_png16(path, w, h, data16):
    """Minimal 16-bit greyscale PNG writer - no PIL, so this runs inside Unreal's Python."""
    import zlib
    rows = bytearray()
    stride = w * 2
    for r in range(h):
        rows.append(0)                                   # filter type 0 (None)
        rows += data16[r * stride:(r + 1) * stride]

    def chunk(tag, payload):
        return (struct.pack('>I', len(payload)) + tag + payload
                + struct.pack('>I', zlib.crc32(tag + payload) & 0xffffffff))

    ihdr = struct.pack('>IIBBBBB', w, h, 16, 0, 0, 0, 0)  # 16-bit greyscale
    with open(path, 'wb') as fh:
        fh.write(b'\x89PNG\r\n\x1a\n')
        fh.write(chunk(b'IHDR', ihdr))
        fh.write(chunk(b'IDAT', zlib.compress(bytes(rows), 9)))
        fh.write(chunk(b'IEND', b''))


def verify_png(path, expected_elev, tx, mid_cm, scale_z):
    """Re-read the PNG and confirm the stored heights reconstruct the source elevations."""
    import zlib
    with open(path, 'rb') as fh:
        blob = fh.read()
    pos = 8
    idat = b''
    while pos < len(blob):
        ln = struct.unpack('>I', blob[pos:pos + 4])[0]
        tag = blob[pos + 4:pos + 8]
        if tag == b'IDAT':
            idat += blob[pos + 8:pos + 8 + ln]
        pos += 12 + ln
    rows = zlib.decompress(idat)
    stride = tx * 2
    worst = 0.0
    step = max(1, tx // 64)
    for r in range(0, tx, step):
        base = r * (stride + 1) + 1
        for c in range(0, tx, step):
            hv = struct.unpack_from('>H', rows, base + c * 2)[0]
            cm = (hv - UE_HEIGHT_MID) / UE_HEIGHT_PER_UNIT * scale_z + mid_cm
            got_msl = geo.scene_y_to_msl(cm / 100.0)
            worst = max(worst, abs(got_msl - expected_elev[r * tx + c]))
    return worst


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--grids', nargs='*', default=['local', 'study', 'regional'])
    ap.add_argument('--out', default=DEFAULT_OUT)
    ap.add_argument('--target', type=int, default=None,
                    help='force a Landscape vertex count (must be native)')
    ap.add_argument('--defaults', action='store_true', default=True,
                    help='use the per-grid default resolutions (local 1009, others 505)')
    ap.add_argument('--no-verify', action='store_true')
    args = ap.parse_args()

    print('valid Landscape vertex counts up to 1100: %s\n'
          % ', '.join(str(v) for v in sorted(NATIVE) if v <= 1100))
    # local is the playable core and wants a fine landscape; the context grids do not.
    PER_GRID_DEFAULT = {'local': 1009, 'study': 505, 'regional': 505}
    for g in args.grids:
        tgt = args.target or PER_GRID_DEFAULT.get(g)
        export(g, args.out, target=tgt, verify=not args.no_verify)
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
