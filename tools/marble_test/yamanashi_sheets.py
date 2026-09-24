#!/usr/bin/env python3
"""Find and download Yamanashi 2024 point-cloud grid products for one 1:500 sheet.

The prefecture publishes its airborne LiDAR products (CC BY 4.0 / ODbL, see the geospatial.jp
dataset `yamanashi-pointcloud-2024`) as one ZIP per 400 m x 300 m sheet. The download URL of each
sheet is carried as a feature property in a vector-tile index, one index per product. This module
reads that index, so a sheet can be fetched from its ID or from any point inside it.

Usage:
    python3 tools/marble_test/yamanashi_sheets.py --lat 35.4775 --lon 138.658 --out DIR
    python3 tools/marble_test/yamanashi_sheets.py --sheet 08LE9335 --lat 35.4775 --lon 138.658 --out DIR

Needs: mapbox-vector-tile, tifffile, numpy. Rasters are in EPSG:6676 (JGD2011 / Japan Plane
Rectangular CS VIII), 0.5 m for DEM and DSM2, 0.25 m for the orthophoto.
"""

import argparse
import io
import json
import math
import os
import sys
import urllib.request
import zipfile

import numpy as np

INDEX = "https://gic-yamanashi.s3.ap-northeast-1.amazonaws.com/2024/Vectortile2026/{layer}/{z}/{x}/{y}.pbf"
PRODUCTS = {
    "dem": "gridtif",       # bare-earth DEM, 0.5 m
    "dsm2": "dsm2gridtif",  # surface (class 1: trees and other features), 0.5 m
    "ortho": "ortho",       # orthophoto, 0.25 m
}
NODATA_ABOVE = 1e30


def _get(url):
    with urllib.request.urlopen(url, timeout=300) as r:
        return r.read()


def _tile(lat, lon, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def _inside(ring, px, py):
    c = False
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[i - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            c = not c
    return c


def sheet_urls(lat, lon, sheet=None, z=14):
    """Return {product: (sheet_id, url)} for the sheet containing (lat, lon), or the named sheet
    within the same index tile."""
    import mapbox_vector_tile as mvt

    fx, fy = _tile(lat, lon, z)
    tx, ty = int(fx), int(fy)
    found = {}
    for product, layer in PRODUCTS.items():
        tile = mvt.decode(_get(INDEX.format(layer=layer, z=z, x=tx, y=ty)),
                          default_options={"y_coord_down": True})
        for lyr in tile.values():
            ext = lyr.get("extent", 4096)
            px, py = (fx - tx) * ext, (fy - ty) * ext
            for f in lyr["features"]:
                props = f["properties"]
                if sheet:
                    hit = props.get("MESH_NO") == sheet
                else:
                    g = f["geometry"]
                    ring = g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0]
                    hit = _inside(ring, px, py)
                if hit:
                    found[product] = (props["MESH_NO"], props["URL"])
                    break
    return found


def download(urls, out):
    """Download and unzip each product's GeoTIFF into out/<product>/<sheet>.tif."""
    paths = {}
    for product, (sheet, url) in urls.items():
        d = os.path.join(out, product)
        os.makedirs(d, exist_ok=True)
        tif = os.path.join(d, f"{sheet}.tif")
        if not os.path.exists(tif):
            with zipfile.ZipFile(io.BytesIO(_get(url))) as z:
                name = next(n for n in z.namelist() if n.lower().endswith(".tif"))
                with open(tif, "wb") as f:
                    f.write(z.read(name))
        paths[product] = tif
    return paths


def load_raster(path):
    """Return (array, x0, y_top, res) with NaN for no-data. x0/y_top are EPSG:6676 easting and
    northing of the top-left pixel corner."""
    import tifffile

    with tifffile.TiffFile(path) as t:
        page = t.pages[0]
        a = page.asarray()
        res = float(page.tags[33550].value[0])
        tie = page.tags[33922].value
    if a.dtype.kind == "f":
        a = a.astype(np.float64)
        a[~np.isfinite(a) | (np.abs(a) > NODATA_ABOVE)] = np.nan
    return a, float(tie[3]), float(tie[4]), res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--sheet", help="sheet ID, e.g. 08LE9335; must lie in the same z14 index tile")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    urls = sheet_urls(args.lat, args.lon, args.sheet)
    if set(urls) != set(PRODUCTS):
        sys.exit(f"sheet not found for every product: {urls}")
    paths = download(urls, args.out)
    print(json.dumps({"sheet": urls["dem"][0], "paths": paths}, indent=2))


if __name__ == "__main__":
    main()
