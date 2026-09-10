#!/usr/bin/env python3
"""Verify the repository against the Pass 2 handover SHA256 manifest.

The handover archive's manifest (docs/handover/MANIFEST_PASS2_SHA256.json) lists
223 files relative to the original package root. In this repository the package
root maps to the repository root, except the four root documents, which live in
docs/handover/. This tool reports missing files and hash mismatches so the
recovered state can be re-verified at any time (also after an LFS checkout).

Usage: python3 tools/verify_manifest.py [--manifest PATH]
Exit code 0 when every present file matches; 1 on any mismatch.
"""
import argparse, hashlib, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOVED = {
    'Aokigahara_3D_README.md': 'docs/handover/Aokigahara_3D_README.md',
    'Aokigahara_3D_Provenance.json': 'docs/handover/Aokigahara_3D_Provenance.json',
    'Aokigahara_Model_Ground_View.png': 'docs/handover/Aokigahara_Model_Ground_View.png',
    'MANIFEST_SHA256.json': 'docs/handover/MANIFEST_SHA256.json',
    'Aokigahara_3D_Validation.json': 'docs/handover/Aokigahara_3D_Validation.json',
    'HANDOVER.md': 'docs/handover/HANDOVER.md',
}
# Files that were beyond the truncation point of the supplied archive (see docs/PROJECT_STATE.md).
KNOWN_MISSING_AT_HANDOFF = {
    'Aokigahara_3D_Validation.json', 'MANIFEST_SHA256.json', 'HANDOVER.md', 'launch_viewer.py',
    'construction_inputs/procedural_trees/evergreen_spreading/high_leaves.npz',
    'construction_inputs/procedural_trees/evergreen_spreading/high_bark.npz',
    'construction_inputs/procedural_trees/evergreen_spreading/low_bark.npz',
    'viewer_original_backup/app_pass1_original.js', 'viewer_original_backup/index_pass1_original.html',
    'evidence/attachment_audit.md', 'evidence/attachment_cave_constraints.json',
    'evidence/attachment_asset_manifest.json', 'evidence/Research_Source_Catalogue.csv',
}

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def is_lfs_pointer(path):
    try:
        with open(path, 'rb') as f:
            head = f.read(120)
        return head.startswith(b'version https://git-lfs.github.com/spec/v1')
    except OSError:
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', default=os.path.join(REPO, 'docs/handover/MANIFEST_PASS2_SHA256.json'))
    a = ap.parse_args()
    manifest = json.load(open(a.manifest))
    ok = missing = mismatch = pointers = replaced = 0
    # launch_viewer.py was lost in the truncated archive tail and rewritten; see
    # docs/PROJECT_STATE.md section 4.1. Its hash differs by design.
    RECONSTRUCTED = {'launch_viewer.py'}
    for rel, digest in manifest.items():
        target = MOVED.get(rel, rel)
        path = os.path.join(REPO, target)
        if not os.path.exists(path):
            missing += 1
            tag = 'known-missing-at-handoff' if rel in KNOWN_MISSING_AT_HANDOFF else 'MISSING'
            print(f'{tag:26} {rel}')
            continue
        if is_lfs_pointer(path):
            pointers += 1
            print(f'{"lfs-pointer (run git lfs pull)":26} {rel}')
            continue
        if sha256(path) == digest:
            ok += 1
        elif rel in RECONSTRUCTED:
            replaced += 1
            print(f'{"reconstructed replacement":26} {rel}')
        else:
            mismatch += 1
            print(f'{"HASH MISMATCH":26} {rel}')
    print(f'\nverified {ok} / {len(manifest)}   reconstructed {replaced}   '
          f'missing {missing}   lfs-pointers {pointers}   unexpected mismatches {mismatch}')
    if not mismatch and not pointers:
        print('OK: every recovered file matches the Pass-2 manifest byte for byte.')
    sys.exit(1 if mismatch else 0)

if __name__ == '__main__':
    main()
