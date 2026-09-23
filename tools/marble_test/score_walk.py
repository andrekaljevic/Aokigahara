#!/usr/bin/env python3
"""Score a walk-out render set from view_splats.mjs: where does the world break down?

For every view it measures:
    holes        share of pixels still showing the magenta background, i.e. no splats there
    edge_density share of pixels on a Sobel edge above a fixed threshold (fine structure)
    detail       mean absolute Laplacian of luminance (the same measure used against the owner's
                 Aokigahara photos: real photos score about 23-39 at 1280 px wide)
plus the lighting metrics from tools/lighting_stats.py, computed with hole pixels excluded where
it matters. Views are grouped by distance from the world origin, and a contact sheet is written
with one row per distance.

Usage:
    python3 tools/marble_test/score_walk.py WALK_DIR [--ref PHOTO ...]
"""

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lighting_stats import measure  # noqa: E402


def luminance(rgb):
    return rgb @ np.array([0.2126, 0.7152, 0.0722])


def texture(path, mask_holes=True):
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(float)
    holes = (rgb[..., 0] > 245) & (rgb[..., 1] < 10) & (rgb[..., 2] > 245)
    lum = luminance(rgb)
    if mask_holes and holes.any():
        lum = np.where(holes, ndimage.median_filter(lum, 5), lum)
    sx, sy = ndimage.sobel(lum, 1), ndimage.sobel(lum, 0)
    edges = np.hypot(sx, sy) > 60
    lap = np.abs(ndimage.laplace(lum))
    keep = ~holes if holes.mean() < 0.99 else np.ones_like(holes)
    return {"holes": float(holes.mean()), "edge_density": float(edges[keep].mean()),
            "detail": float(lap[keep].mean())}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("walk")
    ap.add_argument("--ref", nargs="*", default=[], help="reference photos to score the same way")
    a = ap.parse_args()
    meta = json.load(open(os.path.join(a.walk, "views.json")))
    rows = []
    for v in meta["views"]:
        p = os.path.join(a.walk, v["file"])
        r = {"file": v["file"], "d": v["d"], "yaw": v["yaw"], **texture(p)}
        light = measure(p)
        r.update({k: light[k] for k in ("log_avg_luminance", "sunfleck_fraction", "black_fraction", "highlight_blue_ratio")})
        rows.append(r)
    by_d = {}
    for r in rows:
        by_d.setdefault(r["d"], []).append(r)
    summary = []
    print(f"{'dist':>6} {'holes':>7} {'edges':>7} {'detail':>7}")
    for d in sorted(by_d):
        g = by_d[d]
        s = {"d": d, **{k: float(np.mean([x[k] for x in g])) for k in ("holes", "edge_density", "detail")}}
        summary.append(s)
        print(f"{d:>6} {s['holes']:>7.3f} {s['edge_density']:>7.3f} {s['detail']:>7.1f}")
    refs = []
    for p in a.ref:
        im = Image.open(p).convert("RGB")
        if im.width != 1280:
            im = im.resize((1280, round(im.height * 1280 / im.width)))
            tmp = os.path.join(a.walk, "_ref_" + os.path.basename(p) + ".png")
            im.save(tmp)
            p = tmp
        refs.append({"file": os.path.basename(p), **texture(p, mask_holes=False)})
    if refs:
        print("reference photos: edges %.3f-%.3f, detail %.1f-%.1f" % (
            min(r["edge_density"] for r in refs), max(r["edge_density"] for r in refs),
            min(r["detail"] for r in refs), max(r["detail"] for r in refs)))
    with open(os.path.join(a.walk, "scores.json"), "w") as f:
        json.dump({"per_view": rows, "by_distance": summary, "references": refs}, f, indent=2)
        f.write("\n")

    # Contact sheet: one row per distance, four headings per row.
    thumbs = {}
    for r in rows:
        im = Image.open(os.path.join(a.walk, r["file"])).convert("RGB")
        im.thumbnail((320, 200))
        thumbs[(r["d"], r["yaw"])] = im
    ds = sorted(by_d)
    yaws = sorted({r["yaw"] for r in rows})
    tw, th = 320, 200
    sheet = Image.new("RGB", (60 + tw * len(yaws), th * len(ds)), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    for i, d in enumerate(ds):
        draw.text((6, i * th + th // 2), f"{d} m", fill=(230, 230, 230))
        for j, y in enumerate(yaws):
            if (d, y) in thumbs:
                sheet.paste(thumbs[(d, y)], (60 + j * tw, i * th))
    sheet.save(os.path.join(a.walk, "contact_sheet.jpg"), quality=88)


if __name__ == "__main__":
    main()
