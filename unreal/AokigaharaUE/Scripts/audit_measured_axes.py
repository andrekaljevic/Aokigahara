#!/usr/bin/env python3
"""Screen the preserved LAS X/Y order against the MMS trajectory shapefile.

This is a guard against a subtle but expensive ambiguity:
- EPSG:6676's formal axes are northing/easting;
- most GIS software exposes projected coordinates as x=easting, y=northing;
- LAS stores dimensions named X and Y without resolving that semantic question.

This script does NOT declare the answer from convention. It compares the actual
preserved coordinates and reports the evidence. A final world-origin lock still
needs an independent mapped/GSI control.
"""
from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
import zipfile

from real_terrain_lib import DEFAULT_SURVEY_ROOT, point_bounds, read_las_from_zip

def _area(b):
    xmin, ymin, xmax, ymax = b
    return max(0.0, xmax - xmin) * max(0.0, ymax - ymin)

def overlap_fraction_of_target(container, target):
    """Fraction of target bbox area overlapped by container bbox."""
    ax0, ay0, ax1, ay1 = container
    bx0, by0, bx1, by1 = target
    inter = (
        max(0.0, min(ax1, bx1) - max(ax0, bx0))
        * max(0.0, min(ay1, by1) - max(ay0, by0))
    )
    denom = _area(target)
    return 0.0 if denom == 0.0 else inter / denom

def swapped(b):
    xmin, ymin, xmax, ymax = b
    return (ymin, xmin, ymax, xmax)

def trajectory_layers(zip_path: Path):
    try:
        import shapefile
    except ImportError as exc:
        raise RuntimeError(
            "pyshp is required; install Scripts/requirements-measured.txt"
        ) from exc

    out = []
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        shp_names = [n for n in names if n.lower().endswith(".shp")]
        if not shp_names:
            raise ValueError(f"{zip_path}: no .shp members")
        lower = {n.lower(): n for n in names}

        for shp_name in shp_names:
            stem = shp_name[:-4]
            shx = lower.get((stem + ".shx").lower())
            dbf = lower.get((stem + ".dbf").lower())
            kwargs = {"shp": BytesIO(zf.read(shp_name))}
            if shx:
                kwargs["shx"] = BytesIO(zf.read(shx))
            if dbf:
                kwargs["dbf"] = BytesIO(zf.read(dbf))
            reader = shapefile.Reader(**kwargs)
            bbox = tuple(map(float, reader.bbox))
            prj_name = lower.get((stem + ".prj").lower())
            prj = zf.read(prj_name).decode("utf-8", "replace") if prj_name else None
            out.append({
                "name": shp_name,
                "bbox": bbox,
                "records": len(reader),
                "prj": prj,
            })
    return out

def xy_bbox(las):
    xmin, ymin, _zmin, xmax, ymax, _zmax = point_bounds(las)
    return (xmin, ymin, xmax, ymax)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source-root", type=Path, default=DEFAULT_SURVEY_ROOT)
    p.add_argument("--mms", default="mms_08LE9307.zip")
    p.add_argument("--airborne", default="08LE9307.zip")
    p.add_argument("--trajectory", default="mmstrj.zip")
    args = p.parse_args()

    mms = read_las_from_zip(args.source_root / args.mms)
    airborne = read_las_from_zip(args.source_root / args.airborne)
    mms_bbox = xy_bbox(mms)
    airborne_bbox = xy_bbox(airborne)

    print("MMS LAS stored X/Y bbox:     ", mms_bbox)
    print("airborne stored X/Y bbox:    ", airborne_bbox)
    print("MMS header CRS:               ", mms.header.parse_crs())
    print("airborne header CRS:          ", airborne.header.parse_crs())
    print()

    layers = trajectory_layers(args.source_root / args.trajectory)
    best = None
    for layer in layers:
        b = layer["bbox"]
        as_is = overlap_fraction_of_target(b, mms_bbox)
        xy_swapped = overlap_fraction_of_target(swapped(b), mms_bbox)
        print(layer["name"])
        print("  trajectory bbox:            ", b)
        print("  records:                    ", layer["records"])
        print(f"  covers MMS bbox as stored:   {as_is:.6f}")
        print(f"  covers MMS bbox if X/Y swap: {xy_swapped:.6f}")
        if layer["prj"]:
            print("  .prj:", " ".join(layer["prj"].split())[:500])
        candidate = (as_is - xy_swapped, as_is, xy_swapped, layer["name"])
        best = candidate if best is None or candidate > best else best

    print()
    print("airborne↔MMS bbox overlap screen:")
    print(
        "  airborne covers MMS as stored:   ",
        f"{overlap_fraction_of_target(airborne_bbox, mms_bbox):.6f}",
    )
    print(
        "  airborne covers swapped MMS:     ",
        f"{overlap_fraction_of_target(airborne_bbox, swapped(mms_bbox)):.6f}",
    )

    if best is None:
        raise SystemExit("no trajectory layer could be inspected")
    delta, as_is, xy_swapped, name = best
    print()
    if as_is >= 0.01 and delta > 0.001:
        print(
            "SCREEN RESULT: stored X/Y is materially more consistent with the "
            f"trajectory than swapped X/Y (best layer {name})."
        )
    elif xy_swapped >= 0.01 and -delta > 0.001:
        print(
            "SCREEN RESULT: swapped X/Y is materially more consistent. STOP and "
            "resolve before any terrain/world import."
        )
        raise SystemExit(2)
    else:
        print(
            "SCREEN RESULT: bbox test is inconclusive. STOP and use point/trajectory "
            "distance plus an independent GSI control."
        )
        raise SystemExit(3)

    print(
        "This is only an axis-order screen, not absolute georegistration proof. "
        "The next gate is an independent GSI/mapped control."
    )

if __name__ == "__main__":
    main()
