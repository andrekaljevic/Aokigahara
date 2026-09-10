"""Copy a reference GLB's embedded images into a freshly generated GLB, matching by image name.

Why this is needed
------------------
`construction_code_v2/generate_trees_v2.py` embeds each texture by reading the file in
`work/tex/` verbatim. `work/tex/` is scratch: it is not in the repository, and the exact
preparation the original session applied to those files was not recorded. Its geometry is
faithful — regenerating reproduces all 330 of the shipped library's accessor buffer views
byte-for-byte — but its textures are not: rebuilding from textures re-extracted at source
resolution inflates `tree-library-v2.glb` from 12.5 MB to 16.0 MB for no visual gain, because the
shipped library carries more strongly compressed versions of the same 1024x1024 images.

So a geometry change should not have to pay for that. This grafts the shipped image payload onto
new geometry: images are matched by name, their bytes replaced, and every buffer view re-packed.
Anything the reference does not have is kept as generated, and reported.

  python3 tools/graft_textures.py <generated.glb> <reference.glb> <output.glb> [--manifest FILE]

Prints a per-image report and the size change. Verify the result with tools/compare_glb.py.
`--manifest` rewrites the `sha256` and `bytes` fields of a generator-written manifest so they
describe the grafted file rather than the intermediate one.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path


def read_glb(path):
    d = Path(path).read_bytes()
    if d[:4] != b'glTF':
        raise SystemExit(f'{path}: not a GLB')
    jlen = struct.unpack('<I', d[12:16])[0]
    gltf = json.loads(d[20:20 + jlen])
    off = 20 + jlen
    blen = struct.unpack('<I', d[off:off + 4])[0]
    return gltf, bytearray(d[off + 8:off + 8 + blen])


def write_glb(path, gltf, blob):
    blob = bytes(blob) + b'\0' * ((-len(blob)) % 4)
    js = json.dumps(gltf, separators=(',', ':')).encode()
    js += b' ' * ((-len(js)) % 4)
    total = 12 + 8 + len(js) + 8 + len(blob)
    out = bytearray()
    out += b'glTF' + struct.pack('<II', 2, total)
    out += struct.pack('<II', len(js), 0x4E4F534A) + js
    out += struct.pack('<II', len(blob), 0x004E4942) + blob
    Path(path).write_bytes(out)
    return total


def view_bytes(gltf, blob, index):
    bv = gltf['bufferViews'][index]
    o = bv.get('byteOffset', 0)
    return bytes(blob[o:o + bv['byteLength']])


def main():
    argv = sys.argv[1:]
    manifest = None
    if '--manifest' in argv:
        i = argv.index('--manifest')
        manifest = argv[i + 1]
        del argv[i:i + 2]
    if len(argv) != 3:
        raise SystemExit(__doc__)
    gen_p, ref_p, out_p = argv
    gen, gblob = read_glb(gen_p)
    ref, rblob = read_glb(ref_p)

    ref_images = {im.get('name'): view_bytes(ref, rblob, im['bufferView'])
                  for im in ref.get('images', []) if 'bufferView' in im}

    # New payload for every buffer view: image views take the reference bytes where a name matches.
    replacement = {}
    grafted = kept = 0
    for im in gen.get('images', []):
        name = im.get('name')
        if name in ref_images:
            replacement[im['bufferView']] = ref_images[name]
            was = gen['bufferViews'][im['bufferView']]['byteLength']
            now = len(ref_images[name])
            print(f'  graft  {name:52} {was:>9,} -> {now:>9,}')
            grafted += 1
        else:
            print(f'  keep   {name!s:52} (no image of that name in the reference)')
            kept += 1

    # repack: every view in order, 4-byte aligned, offsets rewritten
    blob = bytearray()
    for i, bv in enumerate(gen['bufferViews']):
        data = replacement.get(i)
        if data is None:
            data = view_bytes(gen, gblob, i)
        blob.extend(b'\0' * ((-len(blob)) % 4))
        bv['byteOffset'] = len(blob)
        bv['byteLength'] = len(data)
        blob.extend(data)
    gen['buffers'][0]['byteLength'] = len(blob) + ((-len(blob)) % 4)

    before = Path(gen_p).stat().st_size
    total = write_glb(out_p, gen, blob)
    print(f'\n  grafted {grafted}, kept {kept}')
    print(f'  {gen_p}  {before:,} bytes')
    print(f'  {out_p}  {total:,} bytes  ({total - before:+,})')
    if manifest:
        mp = Path(manifest)
        m = json.loads(mp.read_text())
        m['sha256'] = hashlib.sha256(Path(out_p).read_bytes()).hexdigest()
        m['bytes'] = total
        m['textures'] = (f'embedded image payload grafted from {Path(ref_p).name} by '
                         f'tools/graft_textures.py; geometry from {Path(gen_p).name}')
        mp.write_text(json.dumps(m, indent=2))
        print(f'  manifest {manifest} updated to sha {m["sha256"][:16]}...')


if __name__ == '__main__':
    main()
