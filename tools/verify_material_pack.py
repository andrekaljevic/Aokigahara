#!/usr/bin/env python3
"""Independent quality checks for a tileable PBR material pack.

Written separately from the extraction pipeline so that the checks do not share
its assumptions. It measures, per material:

  seams        wrap-around discontinuity of every map relative to interior gradients
  normal       decoded-vector sanity and agreement with the repository's
               height_to_normal() convention (construction_code_v2/gen_textures.py)
  roughness    value range (the ground shader clamps below 0.35)
  exposure     mean linear luminance of the albedo against a counterpart texture
  residue      clipped-highlight residue and bright blobs (baked sun dapples)
  lowfreq      residual low-frequency lighting gradient
  focus        fraction of soft (out-of-focus / smeared) windows
  files        dimensions, byte sizes and SHA-256 against the pack manifest

Usage:
  python3 tools/verify_material_pack.py viewer/assets/materials_uhd            # all materials
  python3 tools/verify_material_pack.py viewer/assets/materials_uhd --material moss_uhd --json
  python3 tools/verify_material_pack.py viewer/assets/materials_v2 --material moss --counterpart viewer/assets/materials_v2/moss_diff_1k.jpg

Exit status is 1 if any BLOCKING threshold is crossed, else 0.
Only numpy, pillow and scipy are required.
"""
import argparse, hashlib, json, os, sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'construction_code_v2'))
try:
    from gen_textures import height_to_normal  # noqa: E402  (module main is guarded)
except Exception:  # pragma: no cover
    height_to_normal = None

MAPS = ('diff', 'nor_gl', 'rough', 'height', 'ao')
SLOT_COUNTERPART = {
    'moss': 'viewer/assets/materials_v2/moss_diff_1k.jpg',
    'root': 'viewer/assets/materials_v2/moss_diff_1k.jpg',
    'understorey': 'viewer/assets/materials_v2/moss_diff_1k.jpg',
    'rock': 'viewer/assets/materials_v2/basalt_diff_1k.jpg',
    'litter': 'viewer/assets/materials_v2/litter_diff_1k.jpg',
    'deadwood': 'viewer/assets/materials_v2/litter_diff_1k.jpg',
    'trail': 'viewer/assets/materials_v2/trail_diff_1k.jpg',
    'bark': 'viewer/assets/materials/japanese_cedar_bark_diff_1k.jpg',
}
SLOT_STRENGTH = {'moss': 18, 'root': 18, 'rock': 26, 'litter': 10, 'trail': 8, 'understorey': 12, 'bark': 14, 'deadwood': 12}

# thresholds: (minor, blocking)
T = {
    'seam_diff': (1.3, 1.6), 'seam_height': (1.3, 1.6), 'seam_other': (1.5, 2.2),
    'normal_mean_dev': (0.03, 0.06), 'normal_len_bad': (0.05, 0.15), 'normal_corr': (0.7, 0.5),
    'rough_out': (0.05, 0.15), 'expo_ratio_lo': (0.6, 0.5), 'expo_ratio_hi': (1.6, 2.0),
    'bright_frac': (0.002, 0.01), 'clip_frac': (0.003, 0.01), 'blobs': (3, 6),
    'lowfreq': (0.14, 0.20), 'soft_frac': (0.20, 0.40), 'max_bytes': (2_000_000, 2_500_000),
}


def srgb_to_lin(x):
    x = x.astype(np.float32) / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def luma_lin(rgb_lin):
    return 0.2126 * rgb_lin[..., 0] + 0.7152 * rgb_lin[..., 1] + 0.0722 * rgb_lin[..., 2]


def seam_score(a):
    """(edge mismatch) / (mean interior 1-px gradient). ~1.0 means the wrap is as smooth as the interior."""
    a = a.astype(np.float32)
    if a.ndim == 2:
        a = a[..., None]
    edge = np.abs(a[0] - a[-1]).mean() + np.abs(a[:, 0] - a[:, -1]).mean()
    interior = np.abs(np.diff(a, axis=0)).mean() + np.abs(np.diff(a, axis=1)).mean()
    return float(edge / max(interior, 1e-6))


def load(path, mode):
    im = Image.open(path)
    return np.asarray(im.convert(mode)), im


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def find_manifest(pack_dir):
    for name in os.listdir(pack_dir):
        if name.upper().endswith('MANIFEST.JSON'):
            try:
                return json.load(open(pack_dir / name))
            except Exception:
                pass
    return None


def manifest_entry(manifest, mid):
    if not manifest:
        return None
    mats = manifest.get('materials')
    if isinstance(mats, dict):
        return mats.get(mid)
    if isinstance(mats, list):
        for m in mats:
            if isinstance(m, dict) and m.get('id') == mid:
                return m
    return None


def grade(value, key, higher_is_worse=True):
    lo, hi = T[key]
    if higher_is_worse:
        if value > hi:
            return 'BLOCKING'
        if value > lo:
            return 'minor'
        return 'ok'
    if value < hi:
        return 'BLOCKING'
    if value < lo:
        return 'minor'
    return 'ok'


def verify_material(pack_dir, mid, manifest, counterpart=None):
    out = {'material': mid, 'checks': {}, 'measurements': {}}
    C = out['checks']; M = out['measurements']
    entry = manifest_entry(manifest, mid) or {}
    slot = entry.get('slot', '')
    files = {}
    for m in MAPS:
        cands = sorted(pack_dir.glob(f'{mid}_{m}_*.jpg')) + sorted(pack_dir.glob(f'{mid}_{m}_*.png'))
        if cands:
            files[m] = cands[0]
    M['files'] = {k: str(v.name) for k, v in files.items()}
    if 'diff' not in files:
        C['files'] = 'BLOCKING'; M['error'] = 'no albedo (diff) map found'
        return out

    # ---- files: dims, bytes, sha256 vs manifest
    dims = {}
    fc = 'ok'
    for m, p in files.items():
        with Image.open(p) as im:
            dims[m] = im.size
            fmt = im.format
        b = p.stat().st_size
        if b > T['max_bytes'][1]:
            fc = 'BLOCKING'
        elif b > T['max_bytes'][0] and fc == 'ok':
            fc = 'minor'
        if fmt not in ('JPEG', 'PNG'):
            fc = 'BLOCKING'
        mm = (entry.get('maps') or {}).get(m) if isinstance(entry.get('maps'), dict) else None
        if isinstance(mm, dict):
            if 'bytes' in mm and int(mm['bytes']) != b:
                fc = 'BLOCKING'; M.setdefault('manifest_mismatch', []).append(f'{m}: bytes {mm["bytes"]} != {b}')
            if 'sha256' in mm and mm['sha256'] != sha256(p):
                fc = 'BLOCKING'; M.setdefault('manifest_mismatch', []).append(f'{m}: sha256 differs')
    if len(set(dims.values())) != 1:
        fc = 'BLOCKING'; M['dims_mismatch'] = {k: list(v) for k, v in dims.items()}
    tile_px = entry.get('tile_px')
    if tile_px and tuple(tile_px) != dims['diff']:
        fc = 'BLOCKING'; M['tile_px_mismatch'] = [list(tile_px), list(dims['diff'])]
    M['dims'] = list(dims['diff']); M['bytes'] = {m: files[m].stat().st_size for m in files}
    C['files'] = fc

    # ---- albedo
    rgb8, _ = load(files['diff'], 'RGB')
    lin = srgb_to_lin(rgb8)
    Y = luma_lin(lin)
    M['seam_diff'] = round(seam_score(rgb8), 3)
    C['seam_diff'] = grade(M['seam_diff'], 'seam_diff')
    M['mean_linear_luma'] = round(float(Y.mean()), 4)
    M['mean_srgb'] = round(float(rgb8.mean()), 1)
    cp = counterpart or entry.get('counterpart_file') or entry.get('v2_counterpart_file')
    if not cp:
        v2 = entry.get('v2_counterpart')
        if v2:
            cp = f'viewer/assets/materials_v2/{v2}_diff_1k.jpg'
        elif slot in SLOT_COUNTERPART:
            cp = SLOT_COUNTERPART[slot]
    if cp:
        cpp = Path(cp) if os.path.isabs(cp) else ROOT / cp
        if cpp.exists():
            cy = luma_lin(srgb_to_lin(load(cpp, 'RGB')[0])).mean()
            ratio = float(Y.mean() / max(cy, 1e-6))
            M['counterpart'] = str(cp); M['counterpart_mean_linear_luma'] = round(float(cy), 4); M['exposure_ratio'] = round(ratio, 3)
            g = 'ok'
            if ratio < T['expo_ratio_lo'][1] or ratio > T['expo_ratio_hi'][1]:
                g = 'BLOCKING'
            elif ratio < T['expo_ratio_lo'][0] or ratio > T['expo_ratio_hi'][0]:
                g = 'minor'
            C['exposure'] = g
        else:
            C['exposure'] = 'skipped'; M['counterpart'] = f'missing: {cp}'
    else:
        C['exposure'] = 'skipped'
    M['bright_frac_gt085'] = round(float((Y > 0.85).mean()), 5)
    M['clip_frac_gt09'] = round(float((Y > 0.9).mean()), 5)
    lab, n = ndimage.label(Y > 0.7)
    sizes = ndimage.sum(np.ones_like(Y), lab, range(1, n + 1)) if n else np.array([])
    M['bright_blobs_gt80px'] = int((sizes > 80).sum()) if n else 0
    C['residue'] = max([grade(M['bright_frac_gt085'], 'bright_frac'), grade(M['clip_frac_gt09'], 'clip_frac'), grade(M['bright_blobs_gt80px'], 'blobs')],
                       key=lambda s: ['ok', 'minor', 'BLOCKING'].index(s))
    box = ndimage.uniform_filter(Y, 64, mode='wrap')
    M['lowfreq_std_over_mean'] = round(float(box.std() / max(box.mean(), 1e-6)), 4)
    C['lowfreq'] = grade(M['lowfreq_std_over_mean'], 'lowfreq')
    lap = ndimage.laplace(Y.astype(np.float32))
    h, w = Y.shape
    win = 32
    lv = lap[:h // win * win, :w // win * win].reshape(h // win, win, w // win, win).var(axis=(1, 3))
    med = np.median(lv)
    M['soft_window_frac'] = round(float((lv < 0.25 * med).mean()), 4)
    C['focus'] = grade(M['soft_window_frac'], 'soft_frac')

    # ---- other maps: seams
    for m in ('nor_gl', 'rough', 'height', 'ao'):
        if m in files:
            arr, _ = load(files[m], 'RGB' if m == 'nor_gl' else 'L')
            s = round(seam_score(arr), 3)
            M[f'seam_{m}'] = s
            C[f'seam_{m}'] = grade(s, 'seam_height' if m == 'height' else 'seam_other')

    # ---- normal map
    if 'nor_gl' in files:
        n8, _ = load(files['nor_gl'], 'RGB')
        nv = n8.astype(np.float32) / 255.0 * 2.0 - 1.0
        ln = np.linalg.norm(nv, axis=-1)
        mean = nv.reshape(-1, 3).mean(0)
        M['normal_mean'] = [round(float(x), 4) for x in mean]
        M['normal_len_bad_frac'] = round(float(((ln < 0.9) | (ln > 1.1)).mean()), 5)
        M['normal_z_neg_frac'] = round(float((nv[..., 2] < 0).mean()), 5)
        # only the tangent components must average to zero; mean z is < 1 for any non-flat surface
        dev = float(np.abs(mean[:2]).max())
        g = [grade(dev, 'normal_mean_dev'), grade(M['normal_len_bad_frac'], 'normal_len_bad')]
        if 'height' in files and height_to_normal is not None:
            hgt = load(files['height'], 'L')[0].astype(np.float32) / 255.0
            strength = float(entry.get('normal_strength') or SLOT_STRENGTH.get(slot, 12))
            ref = height_to_normal(hgt * strength, 1.0).astype(np.float32)
            cg = float(np.corrcoef(ref[..., 1].ravel(), n8[..., 1].ravel().astype(np.float32))[0, 1])
            cr = float(np.corrcoef(ref[..., 0].ravel(), n8[..., 0].ravel().astype(np.float32))[0, 1])
            M['normal_corr_G'] = round(cg, 3); M['normal_corr_R'] = round(cr, 3); M['normal_strength_assumed'] = strength
            g.append(grade(min(cg, cr), 'normal_corr', higher_is_worse=False))
        C['normal'] = max(g, key=lambda s: ['ok', 'minor', 'BLOCKING'].index(s))

    # ---- roughness
    if 'rough' in files:
        r = load(files['rough'], 'L')[0].astype(np.float32) / 255.0
        M['rough_mean'] = round(float(r.mean()), 3); M['rough_min'] = round(float(r.min()), 3); M['rough_max'] = round(float(r.max()), 3)
        M['rough_out_of_range_frac'] = round(float(((r < 0.45) | (r > 1.0)).mean()), 5)
        C['roughness'] = grade(M['rough_out_of_range_frac'], 'rough_out')

    # ---- honesty text
    status = json.dumps(entry).lower() if entry else ''
    bad_words = [w for w in ('photogrammetry', 'scanned', 'surveyed', 'measured scale', 'cc0', 'cc-by', 'licensed under') if w in status]
    if entry:
        M['status_bad_words'] = bad_words
        M['status_says_estimated'] = ('estimat' in status) or ('heuristic' in status)
        C['honesty'] = 'BLOCKING' if bad_words or not M['status_says_estimated'] else 'ok'

    out['verdict'] = 'BLOCKING' if any(v == 'BLOCKING' for v in C.values()) else ('minor' if any(v == 'minor' for v in C.values()) else 'ok')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pack_dir')
    ap.add_argument('--material', action='append', help='material id (repeatable); default: every *_diff_* in the directory')
    ap.add_argument('--counterpart', help='albedo file to exposure-match against (overrides slot default)')
    ap.add_argument('--json', action='store_true', help='print JSON only')
    a = ap.parse_args()
    pack_dir = Path(a.pack_dir)
    if not pack_dir.is_absolute():
        pack_dir = (Path.cwd() / pack_dir).resolve()
    manifest = find_manifest(pack_dir)
    mats = a.material or sorted({p.name.split('_diff_')[0] for p in pack_dir.glob('*_diff_*.jpg')})
    results = [verify_material(pack_dir, m, manifest, a.counterpart) for m in mats]
    if a.json:
        print(json.dumps(results, indent=1))
    else:
        for r in results:
            print(f"== {r['material']}: {r.get('verdict', '?')}")
            for k, v in r['checks'].items():
                print(f"   {k:12s} {v}")
            print('   ' + json.dumps(r['measurements']))
    sys.exit(1 if any(r.get('verdict') == 'BLOCKING' for r in results) else 0)


if __name__ == '__main__':
    main()
