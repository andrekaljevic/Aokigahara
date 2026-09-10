"""Compare two GLB files structurally: which meshes, accessors and images actually differ.

  python3 tools/compare_glb.py <a.glb> <b.glb> [--quiet]

Hashes each accessor's buffer view so geometry is compared independently of the embedded image
payload. Use it to check that a regeneration changed only what it was meant to change: an edit
aimed at the mid-detail meshes should leave every `_high` and `_far` accessor identical.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path


def read(path):
    d = Path(path).read_bytes()
    jlen = struct.unpack('<I', d[12:16])[0]
    gltf = json.loads(d[20:20 + jlen])
    off = 20 + jlen
    blen = struct.unpack('<I', d[off:off + 4])[0]
    return gltf, d[off + 8:off + 8 + blen]


def accessor_hashes(gltf, blob):
    out = {}
    for i, ac in enumerate(gltf['accessors']):
        bv = gltf['bufferViews'][ac['bufferView']]
        o = bv.get('byteOffset', 0)
        out[i] = hashlib.sha256(blob[o:o + bv['byteLength']]).hexdigest()
    return out


def mesh_accessors(gltf):
    """mesh name -> the accessor indices it uses"""
    out = {}
    for m in gltf['meshes']:
        idx = set()
        for p in m['primitives']:
            idx.update(p['attributes'].values())
            if 'indices' in p:
                idx.add(p['indices'])
        out[m['name']] = idx
    return out


def main():
    a_p, b_p = sys.argv[1], sys.argv[2]
    quiet = '--quiet' in sys.argv
    A, ab = read(a_p)
    B, bb = read(b_p)
    ha, hb = accessor_hashes(A, ab), accessor_hashes(B, bb)
    ma, mb = mesh_accessors(A), mesh_accessors(B)

    only_a = sorted(set(ma) - set(mb))
    only_b = sorted(set(mb) - set(ma))
    if only_a:
        print('meshes only in', a_p, ':', ', '.join(only_a))
    if only_b:
        print('meshes only in', b_p, ':', ', '.join(only_b))

    changed, same = [], []
    for name in sorted(set(ma) & set(mb)):
        sa = sorted(ha[i] for i in ma[name])
        sb = sorted(hb[i] for i in mb[name])
        (changed if sa != sb else same).append(name)
    print(f'meshes identical: {len(same)}   changed: {len(changed)}')
    if changed:
        print('  changed:', ', '.join(changed))
    if same and not quiet:
        print('  identical:', ', '.join(same))

    ia = {im.get('name'): A['bufferViews'][im['bufferView']]['byteLength'] for im in A.get('images', [])}
    ib = {im.get('name'): B['bufferViews'][im['bufferView']]['byteLength'] for im in B.get('images', [])}
    diff = [k for k in ia if k in ib and ia[k] != ib[k]]
    print(f'images: {len(ia)} vs {len(ib)}, differing byte length: {len(diff)}')
    for k in diff:
        print(f'  {k:52} {ia[k]:>9,} vs {ib[k]:>9,}')
    print(f'file sizes: {Path(a_p).stat().st_size:,} vs {Path(b_p).stat().st_size:,}')
    return 1 if (changed or only_a or only_b) else 0


if __name__ == '__main__':
    raise SystemExit(main())
