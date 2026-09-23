#!/usr/bin/env python3
"""Render equirectangular depth panoramas of the real ground and tree positions of one sheet.

The panoramas are the geometry input for Marble's depth-to-RGB endpoint, which paints a
photographic panorama that follows the supplied depth. The scene is built from measured data
only, apart from the tree shapes:

- ground: the 0.5 m bare-earth DEM as a triangle mesh, so lava relief is real;
- trees: one stem per local maximum of the canopy height model (DSM2 minus DEM), with its real
  height. Trunk and crown sizes are allometric guesses, and crowns are cones, so treat them as
  placeholders that only fix where trees stand and how tall they are.

Outputs per viewpoint, in --out:
    <name>_depth.exr     radial distance in metres, float32 (RGB channels identical)
    <name>_depth.png     16-bit log depth, inverted (near = white), as in World Labs' example;
                         decode with z_min and z_max from the JSON
    <name>_preview.jpg   false-colour preview
    <name>.json          viewpoint in EPSG:6676, eye height, panorama convention, z range

Panorama convention: 2:1 equirectangular, centre column faces grid north, azimuth increases
to the right (clockwise from above), top row is straight up.

Usage:
    python3 tools/marble_test/depth_pano.py --dem D.tif --dsm2 S.tif --out DIR [--views 3]
"""

import argparse
import json
import os

import numpy as np
from scipy import ndimage

from yamanashi_sheets import load_raster

SKY = 1000.0      # metres assigned to rays that reach open sky
Z_MIN, Z_MAX = 0.1, 1000.0
EYE = 1.6


def detect_stems(chm, res, min_h=8.0):
    """Local maxima of a lightly smoothed CHM; returns (rows, cols, heights)."""
    sm = ndimage.gaussian_filter(np.nan_to_num(chm), sigma=1.0 / res)
    peak = ndimage.maximum_filter(sm, size=int(round(3.0 / res)) | 1)
    r, c = np.nonzero((sm == peak) & (sm >= min_h))
    return r, c, chm[r, c]


def terrain_mesh(dem, x0, y_top, res, ox, oy, oz):
    """Grid DEM as a triangle mesh in local metres (x east, y north, z up) around origin."""
    import trimesh

    h, w = dem.shape
    cols, rows = np.meshgrid(np.arange(w), np.arange(h))
    X = x0 + (cols + 0.5) * res - ox
    Y = y_top - (rows + 0.5) * res - oy
    Z = np.nan_to_num(dem, nan=np.nanmin(dem)) - oz
    v = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    idx = np.arange(h * w).reshape(h, w)
    a, b, c, d = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel()
    f = np.vstack([np.column_stack([a, c, b]), np.column_stack([b, c, d])])
    return trimesh.Trimesh(vertices=v, faces=f, process=False)


def tree_mesh(px, py, ground, height, seg=10):
    """Trunk cylinder plus conical crown for each stem, merged into one mesh."""
    import trimesh

    parts = []
    for x, y, g, h in zip(px, py, ground, height):
        trunk_r = 0.08 + 0.012 * h
        crown_r = min(0.6 + 0.16 * h, 5.0)
        base = 0.40 * h
        trunk = trimesh.creation.cylinder(radius=trunk_r, height=0.9 * h, sections=seg)
        trunk.apply_translation([x, y, g + 0.45 * h])
        crown = trimesh.creation.cone(radius=crown_r, height=h - base, sections=seg)
        crown.apply_translation([x, y, g + base])
        parts += [trunk, crown]
    return trimesh.util.concatenate(parts)


def pano_dirs(w, h):
    u = (np.arange(w) + 0.5) / w
    v = (np.arange(h) + 0.5) / h
    lon = (u - 0.5) * 2 * np.pi
    lat = (0.5 - v) * np.pi
    LON, LAT = np.meshgrid(lon, lat)
    d = np.stack([np.cos(LAT) * np.sin(LON), np.cos(LAT) * np.cos(LON), np.sin(LAT)], -1)
    return d.reshape(-1, 3), LAT.ravel()


def cast(scene, origin, dirs, lat, half_extent):
    """Radial distance of the first hit per ray. Missed rays above 15 degrees are sky; lower
    misses left the sheet and are given the distance to the sheet edge (more forest beyond)."""
    loc, ray_idx, _ = scene.ray.intersects_location(np.repeat(origin[None], len(dirs), 0), dirs,
                                                    multiple_hits=False)
    depth = np.full(len(dirs), np.nan)
    depth[ray_idx] = np.linalg.norm(loc - origin, axis=1)
    miss = np.isnan(depth)
    hx, hy = half_extent
    with np.errstate(divide="ignore"):
        tx = np.where(np.abs(dirs[:, 0]) > 1e-6, (np.sign(dirs[:, 0]) * hx - origin[0]) / dirs[:, 0], np.inf)
        ty = np.where(np.abs(dirs[:, 1]) > 1e-6, (np.sign(dirs[:, 1]) * hy - origin[1]) / dirs[:, 1], np.inf)
    edge = np.minimum(tx, ty)
    depth[miss & (lat > np.radians(15))] = SKY
    low = miss & (lat <= np.radians(15))
    depth[low] = np.clip(edge[low], 1.0, SKY)
    return depth


def choose_views(dem, chm, res, n, margin_m=90.0):
    """Viewpoints under closed canopy, on gentle ground, away from sheet edges, spread apart."""
    h, w = dem.shape
    m = int(margin_m / res)
    cover = ndimage.uniform_filter((np.nan_to_num(chm) > 10).astype(float), size=int(20 / res))
    gy, gx = np.gradient(np.nan_to_num(dem), res)
    slope = np.hypot(gx, gy)
    score = cover - 0.5 * np.clip(slope, 0, 1)
    score[:m, :] = score[-m:, :] = -9
    score[:, :m] = score[:, -m:] = -9
    score[np.nan_to_num(chm) > 3] -= 0.5          # stand beside trunks, not inside a crown
    picks = []
    for _ in range(n):
        r, c = np.unravel_index(np.argmax(score), score.shape)
        picks.append((r, c))
        rr, cc = np.ogrid[:h, :w]
        score[(rr - r) ** 2 + (cc - c) ** 2 < (40 / res) ** 2] = -9
    return picks


def write_outputs(depth, w, h, base, meta):
    import OpenEXR
    from PIL import Image

    img = depth.reshape(h, w).astype(np.float32)
    OpenEXR.File({"type": OpenEXR.scanlineimage}, {"RGB": np.repeat(img[..., None], 3, -1)}).write(base + "_depth.exr")
    norm = (np.log(np.clip(img, Z_MIN, Z_MAX)) - np.log(Z_MIN)) / (np.log(Z_MAX) - np.log(Z_MIN))
    Image.fromarray(((1 - norm) * 65535).astype(np.uint16)).save(base + "_depth.png")
    viz = np.clip(1 - norm, 0, 1) ** 1.5
    Image.fromarray(np.stack([viz * 255, viz * 200, 80 + viz * 120], -1).astype(np.uint8)).save(base + "_preview.jpg", quality=88)
    with open(base + ".json", "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dem", required=True)
    ap.add_argument("--dsm2", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--views", type=int, default=3)
    ap.add_argument("--width", type=int, default=2048)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    dem, x0, y_top, res = load_raster(args.dem)
    dsm, *_ = load_raster(args.dsm2)
    chm = dsm - dem
    sheet = os.path.splitext(os.path.basename(args.dem))[0]
    h_px, w_px = dem.shape
    cx, cy = x0 + w_px * res / 2, y_top - h_px * res / 2
    oz = float(np.nanmin(dem))

    r, c, th = detect_stems(chm, res)
    sx, sy = x0 + (c + 0.5) * res - cx, y_top - (r + 0.5) * res - cy
    import trimesh
    ground = terrain_mesh(dem, x0, y_top, res, cx, cy, oz)
    trees = tree_mesh(sx, sy, dem[r, c] - oz, th)
    scene = trimesh.util.concatenate([ground, trees])
    print(f"{sheet}: {len(th)} stems, median height {np.median(th):.1f} m, {len(scene.faces):,} triangles")

    w, h = args.width, args.width // 2
    dirs, lat = pano_dirs(w, h)
    views = choose_views(dem, chm, res, args.views)
    for i, (vr, vc) in enumerate(views):
        ex, ey = x0 + (vc + 0.5) * res, y_top - (vr + 0.5) * res
        origin = np.array([ex - cx, ey - cy, dem[vr, vc] - oz + EYE])
        depth = cast(scene, origin, dirs, lat, (w_px * res / 2, h_px * res / 2))
        name = f"{sheet}_v{i + 1}"
        meta = {
            "sheet": sheet, "crs": "EPSG:6676", "easting": ex, "northing": ey,
            "ground_elevation_m": float(dem[vr, vc]), "eye_height_m": EYE,
            "canopy_height_here_m": float(np.nan_to_num(chm[vr, vc])),
            "panorama": "equirectangular 2:1; centre column faces grid north; azimuth increases to the right; top row is zenith",
            "depth": "radial metres; sky = %g; EXR float32; PNG 16-bit log, inverted" % SKY,
            "z_min": Z_MIN, "z_max": Z_MAX, "width": w, "height": h,
            "stems_in_sheet": int(len(th)),
            "median_depth_below_horizon_m": float(np.median(depth[lat < 0])),
            "sky_fraction": float(np.mean(depth >= SKY)),
        }
        write_outputs(depth, w, h, os.path.join(args.out, name), meta)
        print(f"  {name}: E {ex:.1f} N {ey:.1f}, median ground-ray depth {meta['median_depth_below_horizon_m']:.1f} m, sky {meta['sky_fraction']:.3f}")


if __name__ == "__main__":
    main()
