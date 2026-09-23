#!/usr/bin/env python3
"""Export a block-out of real Aokigahara ground and tree positions as a GLB for Marble's Chisel.

Chisel (in the Marble web app) accepts an uploaded GLB as the coarse layout of a world and
paints detail over it from a text prompt. This builds that layout from measured data, so it can
be tried on the free Marble plan without the API:

- ground: the 0.5 m bare-earth DEM, cropped to a square around a viewpoint;
- trees: one trunk and one conical crown per canopy-height peak, at its real height (the shapes
  are placeholders, the positions and heights are measured).

The file is glTF Y-up in metres: +X east, +Y up, +Z south. The origin is on the ground directly
below the viewpoint, so the panorama camera goes at (0, 1.6, 0).

Usage:
    python3 tools/marble_test/chisel_glb.py --dem D.tif --dsm2 S.tif --view PANO.json --out block.glb [--half 40]
"""

import argparse
import json

import numpy as np
import trimesh

from depth_pano import detect_stems, tree_mesh
from yamanashi_sheets import load_raster


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dem", required=True)
    ap.add_argument("--dsm2", required=True)
    ap.add_argument("--view", required=True, help="a depth_pano.py viewpoint JSON")
    ap.add_argument("--out", required=True)
    ap.add_argument("--half", type=float, default=40.0, help="half-width of the square crop, metres")
    a = ap.parse_args()

    dem, x0, y_top, res = load_raster(a.dem)
    dsm, *_ = load_raster(a.dsm2)
    chm = dsm - dem
    v = json.load(open(a.view))
    ex, ey, gz = v["easting"], v["northing"], v["ground_elevation_m"]

    c0 = int((ex - a.half - x0) / res); c1 = int((ex + a.half - x0) / res) + 1
    r0 = int((y_top - (ey + a.half)) / res); r1 = int((y_top - (ey - a.half)) / res) + 1
    c0, r0 = max(c0, 0), max(r0, 0)
    sub = dem[r0:r1, c0:c1]
    h, w = sub.shape
    cols, rows = np.meshgrid(np.arange(w), np.arange(h))
    E = x0 + (c0 + cols + 0.5) * res - ex
    N = y_top - (r0 + rows + 0.5) * res - ey
    Z = np.nan_to_num(sub, nan=np.nanmin(sub)) - gz
    verts = np.column_stack([E.ravel(), Z.ravel(), -N.ravel()])        # glTF: X east, Y up, Z south
    idx = np.arange(h * w).reshape(h, w)
    p, q, s, t = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel()
    faces = np.vstack([np.column_stack([p, q, s]), np.column_stack([q, t, s])])
    ground = trimesh.Trimesh(verts, faces, process=False)
    ground.visual.face_colors = [70, 90, 55, 255]

    r, c, th = detect_stems(chm, res)
    se, sn = x0 + (c + 0.5) * res - ex, y_top - (r + 0.5) * res - ey
    keep = (np.abs(se) < a.half) & (np.abs(sn) < a.half)
    trees = tree_mesh(se[keep], sn[keep], dem[r[keep], c[keep]] - gz, th[keep])   # z-up, metres
    tv = trees.vertices.copy()
    trees.vertices = np.column_stack([tv[:, 0], tv[:, 2], -tv[:, 1]])
    trees.visual.face_colors = [95, 80, 60, 255]

    scene = trimesh.Scene({"ground": ground, "trees": trees})
    scene.export(a.out)
    print(json.dumps({
        "out": a.out, "crop_m": 2 * a.half, "ground_triangles": int(len(ground.faces)),
        "trees": int(keep.sum()), "tree_triangles": int(len(trees.faces)),
        "viewpoint_epsg6676": [ex, ey], "ground_elevation_m": gz,
        "camera": "place the panorama camera at (0, 1.6, 0)",
    }, indent=2))


if __name__ == "__main__":
    main()
