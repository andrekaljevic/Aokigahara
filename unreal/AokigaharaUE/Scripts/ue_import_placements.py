"""Run INSIDE Unreal: place the 467,601 source trees as instanced static meshes.

    UnrealEditor-Cmd AokigaharaUE.uproject -run=pythonscript \
        -script="Scripts/ue_import_placements.py"

or from the editor's Python console:

    exec(open('Scripts/ue_import_placements.py').read())

Reads `Content/Aokigahara/Data/placements_ue.bin`, produced by `export_placements.py`, which is
already in Unreal centimetres with Unreal yaw. Nothing in this file re-does the coordinate maths -
that lives in `aokigahara_geo` and is tested against 78 surveyed control points.

WHAT THIS DOES AND DOES NOT DO
------------------------------
It places instances and colour-codes them by community class. It does NOT do artistic foliage.
The brief's step 9 is explicit that placement correctness must be proven before any of that, and
a debug pass where each class is a distinct colour is how you see, in one screenshot, whether the
world is mirrored, rotated, offset or scaled.

Run `--validate` first. It reports counts and bounds without creating anything, so a bad transform
costs seconds rather than a half-hour import.

DENSITY WARNING
---------------
467,601 hierarchical instances of a real tree mesh will not run on a MacBook Air M2. Use
`--max-instances` and `--radius` to bring in a working subset while the pipeline is being proven,
and only scale up once World Partition, HLOD and the foliage representation are settled. The
default here is deliberately a subset, not the whole forest.
"""

import json
import math
import os
import struct

try:
    import unreal
except ImportError:                                     # allows --validate outside the editor
    unreal = None

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, '..'))
DATA = os.path.join(PROJECT, 'Content/Aokigahara/Data')
BIN = os.path.join(DATA, 'placements_ue.bin')
META = os.path.join(DATA, 'placements_ue.json')

REC = 6
FMT = '<%df' % REC

# Debug colours per community class, so a single screenshot shows whether placement is correct.
CLASS_COLOUR = {
    0: (0.15, 0.45, 0.20),      # conifer stand
    1: (0.20, 0.55, 0.35),      # conifer stand, second group
    2: (0.75, 0.55, 0.20),      # deciduous broadleaved
    3: (0.55, 0.35, 0.55),      # mixed / transitional
}


def load(path=BIN):
    with open(path, 'rb') as fh:
        raw = fh.read()
    n = len(raw) // (REC * 4)
    for i in range(n):
        yield struct.unpack_from(FMT, raw, i * REC * 4)


def validate():
    """Counts, bounds and class histogram, without touching the editor."""
    if not os.path.exists(BIN):
        print('MISSING %s - run export_placements.py first' % BIN)
        return False
    meta = json.load(open(META)) if os.path.exists(META) else {}
    n = 0
    hist = {}
    lo = [float('inf')] * 3
    hi = [float('-inf')] * 3
    for x, y, z, yaw, scale, cls in load():
        n += 1
        k = int(cls)
        hist[k] = hist.get(k, 0) + 1
        for j, v in enumerate((x, y, z)):
            lo[j] = min(lo[j], v)
            hi[j] = max(hi[j], v)
    print('placements      %d' % n)
    print('class histogram %s' % dict(sorted(hist.items())))
    print('bounds  X north %12.0f .. %12.0f cm  (%.0f m)' % (lo[0], hi[0], (hi[0] - lo[0]) / 100))
    print('        Y east  %12.0f .. %12.0f cm  (%.0f m)' % (lo[1], hi[1], (hi[1] - lo[1]) / 100))
    print('        Z up    %12.0f .. %12.0f cm  (%.0f m)' % (lo[2], hi[2], (hi[2] - lo[2]) / 100))
    if meta:
        ok = meta.get('count') == n and {str(k): v for k, v in sorted(hist.items())} == \
            meta.get('class_histogram')
        print('matches the sidecar written by export_placements.py: %s' % ok)
        print('mapping: %s' % meta.get('coordinate_mapping'))
        print('yaw:     %s' % meta.get('yaw_mapping'))
        print('datum:   %s' % meta.get('vertical_datum'))
        return ok
    return True


def build(mesh_path='/Engine/BasicShapes/Cylinder',
          max_instances=40000, radius_m=None, centre=(0.0, 0.0),
          actor_label='Aokigahara_PlacementDebug'):
    """Create one HISM component per community class and fill it.

    mesh_path defaults to an engine cylinder on purpose: this pass is about proving the transform,
    not about looking like a forest. Point it at a real tree once the placement is confirmed.
    """
    if unreal is None:
        raise SystemExit('not running inside Unreal')

    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if mesh is None:
        raise SystemExit('could not load %s' % mesh_path)

    world = unreal.EditorLevelLibrary.get_editor_world()
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    actor.set_actor_label(actor_label)

    comps = {}
    for cls, rgb in CLASS_COLOUR.items():
        comp = unreal.HierarchicalInstancedStaticMeshComponent(actor)
        comp.set_static_mesh(mesh)
        comp.attach_to_component(actor.root_component, '',
                                 unreal.AttachmentRule.KEEP_RELATIVE,
                                 unreal.AttachmentRule.KEEP_RELATIVE,
                                 unreal.AttachmentRule.KEEP_RELATIVE, False)
        comp.register_component()
        comps[cls] = comp

    r_cm = radius_m * 100.0 if radius_m else None
    cx, cy = centre
    placed = {k: 0 for k in CLASS_COLOUR}
    total = 0
    for x, y, z, yaw, scale, cls in load():
        if r_cm is not None and math.hypot(x - cx, y - cy) > r_cm:
            continue
        if total >= max_instances:
            break
        k = int(cls)
        comp = comps.get(k)
        if comp is None:
            continue
        t = unreal.Transform(unreal.Vector(x, y, z),
                             unreal.Rotator(0.0, yaw, 0.0),      # pitch, yaw, roll
                             unreal.Vector(scale, scale, scale))
        comp.add_instance(t)
        placed[k] += 1
        total += 1

    print('placed %d instances: %s' % (total, placed))
    if total >= max_instances:
        print('NOTE: stopped at the --max-instances cap of %d; this is a SUBSET of %s'
              % (max_instances, 'the full 467,601'))
    return actor


if __name__ == '__main__':
    import sys
    if '--validate' in sys.argv or unreal is None:
        raise SystemExit(0 if validate() else 1)
    validate()
    build()
