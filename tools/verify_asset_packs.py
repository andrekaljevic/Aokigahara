#!/usr/bin/env python3
"""Verify the photo-derived asset packs under asset_packs/ against their manifests.

Checks, for every pack listed in asset_packs/PACKS_MANIFEST.json:
  - every file the pack manifest records exists, with the recorded byte size and SHA-256;
  - every image has the recorded pixel size (tiles are square at the tile size, domes are 2:1);
  - every texture set has the four maps diff / nor_gl / rough / height;
  - every albedo tile wraps seamlessly: the mean absolute difference across the wrap edges
    (last column against first column, last row against first row) is compared with the mean
    absolute difference between adjacent interior columns and rows; a ratio far above 1 means a
    visible seam;
  - no straight edge survives at the end of the quilting overlap bands: the mean difference at the
    column and row boundaries where each patch's overlap ends (step and overlap are read from the
    manifest) is compared with the tile's median boundary difference. A ratio well above 1 there is
    the signature of an inconsistent composite at patch corners, which the generator once had;
  - a pack marked redistribution=withheld carries no texture files and no committed source.

Usage: python3 tools/verify_asset_packs.py [--quick]   (--quick skips the SHA-256 pass)
Exit code 0 when everything matches; 1 on any failure.
"""
import argparse, hashlib, json, os, sys

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKS = os.path.join(REPO, 'asset_packs')
SEAM_RATIO_LIMIT = 1.6
BAND_END_RATIO_LIMIT = 1.4

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def seam_ratio(path, step=None, overlap=None):
    """Returns (wrap ratio, band-end ratio). The band-end ratio is None when the quilting step and
    overlap are unknown."""
    a = np.asarray(Image.open(path).convert('L'), dtype=np.float32)
    col = np.abs(a[:, 1:] - a[:, :-1]).mean(0)
    row = np.abs(a[1:, :] - a[:-1, :]).mean(1)
    wrap = 0.5 * (np.abs(a[:, -1] - a[:, 0]).mean() + np.abs(a[-1, :] - a[0, :]).mean())
    interior = 0.5 * (col.mean() + row.mean())
    band_end = None
    if step and overlap and a.shape[0] % step == 0:
        n = a.shape[0] // step
        idx = [k * step + overlap - 1 for k in range(1, n)]
        band_end = 0.5 * (col[idx].mean() / max(np.median(col), 1e-6) + row[idx].mean() / max(np.median(row), 1e-6))
    return float(wrap / max(interior, 1e-6)), (None if band_end is None else float(band_end))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quick', action='store_true', help='skip the SHA-256 pass')
    a = ap.parse_args()
    index = json.load(open(os.path.join(PACKS, 'PACKS_MANIFEST.json')))
    failures = 0
    files = 0
    seams = []

    def fail(msg):
        nonlocal failures
        failures += 1
        print('FAIL ' + msg)

    for pack_id, entry in index['packs'].items():
        mpath = os.path.join(REPO, entry['manifest'])
        if not os.path.exists(mpath):
            fail(f'{pack_id}: manifest missing at {entry["manifest"]}')
            continue
        m = json.load(open(mpath))
        records = list(m['files'].values())
        for mat in m['materials']:
            missing = [k for k in ('diff', 'nor_gl', 'rough', 'height') if k not in mat['files']]
            if missing:
                fail(f'{pack_id}/{mat["id"]}: maps missing {missing}')
            records += list(mat['files'].values())
        withheld = m['source'].get('redistribution') == 'withheld'
        if withheld:
            if m['materials']:
                fail(f'{pack_id}: withheld pack carries texture sets')
            if m['source'].get('committed_copy'):
                fail(f'{pack_id}: withheld pack claims a committed source copy')
        else:
            src = os.path.join(REPO, m['source']['committed_copy'])
            if not os.path.exists(src):
                fail(f'{pack_id}: committed source missing {m["source"]["committed_copy"]}')
            elif not a.quick and sha256(src) != m['source']['sha256']:
                fail(f'{pack_id}: committed source hash differs from the manifest')
        for rec in records:
            files += 1
            path = os.path.join(PACKS, rec['path'])
            if not os.path.exists(path):
                fail(f'{pack_id}: missing {rec["path"]}')
                continue
            if os.path.getsize(path) != rec['bytes']:
                fail(f'{pack_id}: size differs {rec["path"]}')
            if not a.quick and sha256(path) != rec['sha256']:
                fail(f'{pack_id}: hash differs {rec["path"]}')
            if 'pixels' in rec and path.lower().endswith(('.jpg', '.png')):
                with Image.open(path) as im:
                    if list(im.size) != list(rec['pixels']):
                        fail(f'{pack_id}: pixel size {im.size} != {rec["pixels"]} for {rec["path"]}')
        for mat in m['materials']:
            diff = mat['files'].get('diff')
            if diff:
                syn = mat.get('synthesis', {})
                r, b = seam_ratio(os.path.join(PACKS, diff['path']), syn.get('step'), syn.get('overlap'))
                seams.append((f'{pack_id}/{mat["id"]}', r, b))
                if r > SEAM_RATIO_LIMIT:
                    fail(f'{pack_id}/{mat["id"]}: wrap seam ratio {r:.2f} exceeds {SEAM_RATIO_LIMIT}')
                if b is not None and b > BAND_END_RATIO_LIMIT:
                    fail(f'{pack_id}/{mat["id"]}: overlap band-end ratio {b:.2f} exceeds {BAND_END_RATIO_LIMIT}')
        print(f'{pack_id:26} {len(m["materials"])} texture sets, {len(records)} files, '
              f'{"withheld" if withheld else "textures"}')
    if seams:
        worst = max(seams, key=lambda t: t[1])
        print(f'\nwrap-seam ratio: median {np.median([r for _, r, _ in seams]):.2f}, worst {worst[1]:.2f} ({worst[0]})')
        bands = [(nm, b) for nm, _, b in seams if b is not None]
        if bands:
            wb = max(bands, key=lambda t: t[1])
            print(f'band-end ratio:  median {np.median([b for _, b in bands]):.2f}, worst {wb[1]:.2f} ({wb[0]})')
    print(f'checked {files} files across {len(index["packs"])} packs, failures {failures}')
    if not failures:
        print('OK: every pack matches its manifest and every tile wraps.')
    sys.exit(1 if failures else 0)

if __name__ == '__main__':
    main()
