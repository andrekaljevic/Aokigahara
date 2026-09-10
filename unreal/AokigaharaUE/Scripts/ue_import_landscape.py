"""Run INSIDE Unreal: import a GSI heightmap as a Landscape with the correct transform.

    exec(open('Scripts/ue_import_landscape.py').read())          # editor Python console
    python3 Scripts/ue_import_landscape.py --print local          # outside the editor

Consumes the PNG + JSON pair written by `export_heightmaps.py`. All the arithmetic - native
Landscape sizing, the 16-bit height encoding, the non-uniform X/Y scale and the row flip - is
already solved and verified there; this script only applies it.

ON THE PROGRAMMATIC IMPORT
--------------------------
Creating a Landscape from Python is version-sensitive: the editor subsystem that does it has moved
between releases, and this file was written without an Unreal install to test against. So it works
in two modes, and says which one it is using:

  * `--print` (and the fallback) prints the exact figures to type into the Landscape tool's Import
    panel. That path cannot break, and is the one to trust if the API call errors.
  * The programmatic path is attempted only if the expected subsystem is present, and any failure
    falls back to printing rather than leaving a half-made Landscape in the level.

Whichever path runs, VERIFY afterwards with `--verify`, which line-traces onto the created
Landscape at the surveyed control points and compares against the source elevation. Import
succeeding is not evidence that the terrain is in the right place.
"""

import json
import os
import sys

try:
    import unreal
except ImportError:
    unreal = None

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, '..'))
TERRAIN = os.path.join(PROJECT, 'Content/Aokigahara/Terrain')
sys.path.insert(0, HERE)
import aokigahara_geo as geo  # noqa: E402


def load_info(grid_id):
    path = os.path.join(TERRAIN, '%s_heightmap.json' % grid_id)
    if not os.path.exists(path):
        raise SystemExit('missing %s - run export_heightmaps.py first' % path)
    with open(path) as fh:
        return json.load(fh)


def print_settings(grid_id):
    """Everything needed to do the import by hand, which is the reliable path."""
    info = load_info(grid_id)
    ls = info['landscape']
    png = os.path.join(TERRAIN, '%s_heightmap.png' % grid_id)
    print('=' * 74)
    print('Landscape import settings for the "%s" grid' % grid_id)
    print('=' * 74)
    print('  Heightmap file        %s' % png)
    print('  Resolution            %d x %d' % tuple(ls['resolution']))
    print('  Section size          %d x %d quads' % (ls['section_size_quads'],
                                                     ls['section_size_quads']))
    print('  Sections per component %s' % ls['sections_per_component'])
    print('  Number of components   %s' % ls['component_count'])
    print()
    print('  Location   X %14.2f   Y %14.2f   Z %14.2f      (centimetres)'
          % (ls['actor_location_cm']['X_north'], ls['actor_location_cm']['Y_east'],
             ls['actor_location_cm']['Z']))
    print('  Scale      X %14.6f   Y %14.6f   Z %14.6f'
          % (ls['scale']['X_north_cm_per_quad'], ls['scale']['Y_east_cm_per_quad'],
             ls['scale']['Z']))
    print()
    print('  X is NORTH and Y is EAST. %s' % ls['note_scale_axes'])
    print('  Ground resolution     %.3f m/quad north, %.3f m/quad east'
          % (info['resample']['metres_per_quad']['north'],
             info['resample']['metres_per_quad']['east']))
    print('  Vertical quantisation %.3f mm per heightmap LSB'
          % info['height_encoding']['quantisation_mm_per_lsb'])
    print('  Elevation covered     %.2f .. %.2f m MSL'
          % tuple(info['height_encoding']['msl_range_m']))
    print('  Z datum               %s' % info['vertical_datum'])
    print('  Resampled             %s -> %s (%s)'
          % (info['resample']['from'], info['resample']['to'], info['resample']['reason']))
    print('=' * 74)
    return info


def do_import(grid_id):
    """Attempt the programmatic import, falling back to printing on any problem."""
    info = print_settings(grid_id)
    if unreal is None:
        return None
    subsystem = getattr(unreal, 'LandscapeEditorSubsystem', None)
    if subsystem is None:
        print('\nNOTE: unreal.LandscapeEditorSubsystem is not present in this build. Use the '
              'Landscape tool with the settings above; they are exact.')
        return None
    try:
        sub = unreal.get_editor_subsystem(unreal.LandscapeEditorSubsystem)
    except Exception as exc:                                     # noqa: BLE001
        print('\nNOTE: could not acquire the landscape subsystem (%s). Import by hand with the '
              'settings above.' % exc)
        return None
    print('\nLandscape subsystem available. Import via the Landscape tool using the settings '
          'above; a scripted call is intentionally not made here because it was never run '
          'against a real editor and a half-created Landscape is worse than none.')
    return sub


def verify(grid_id, samples=12):
    """Line-trace onto the Landscape at surveyed control points and compare elevations."""
    if unreal is None:
        raise SystemExit('--verify must run inside Unreal')
    ctx = os.path.join(PROJECT, '..', '..', 'viewer/assets/terrain/local-context.json')
    ctx = os.path.abspath(ctx)
    with open(ctx) as fh:
        landmarks = [m for m in json.load(fh).get('landmarks', [])
                     if m.get('coordinates') and m.get('elevationM') is not None]
    world = unreal.EditorLevelLibrary.get_editor_world()
    worst = 0.0
    checked = 0
    for m in landmarks[:samples]:
        sx, sz = m['coordinates']
        ue_x, ue_y, _ = geo.scene_to_ue(sx, 0.0, sz)
        start = unreal.Vector(ue_x, ue_y, 500000.0)
        end = unreal.Vector(ue_x, ue_y, -500000.0)
        hit = unreal.SystemLibrary.line_trace_single(
            world, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
            unreal.DrawDebugTrace.NONE, True)
        if not hit:
            print('  no hit at %-34s (%.0f, %.0f)' % (m['name'][:34], ue_x, ue_y))
            continue
        got_msl = geo.scene_y_to_msl(hit.impact_point.z / 100.0)
        err = abs(got_msl - m['elevationM'])
        worst = max(worst, err)
        checked += 1
        print('  %-34s expected %8.2f m  got %8.2f m  err %6.2f m'
              % (m['name'][:34], m['elevationM'], got_msl, err))
    print('\n%d checked, worst error %.2f m' % (checked, worst))
    # The local grid is an 8 m resample, so metres of disagreement at a point are plausible;
    # tens of metres, or a systematic sign, mean the transform is wrong.
    print('VERDICT: %s' % ('plausible' if worst < 15.0 else
                           '*** TRANSFORM LIKELY WRONG - check the row flip and X/Y axes ***'))
    return worst


if __name__ == '__main__':
    grid = 'local'
    for a in sys.argv[1:]:
        if not a.startswith('--'):
            grid = a
    if '--verify' in sys.argv:
        verify(grid)
    elif '--print' in sys.argv or unreal is None:
        print_settings(grid)
    else:
        do_import(grid)
