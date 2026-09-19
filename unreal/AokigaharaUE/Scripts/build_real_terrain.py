#!/usr/bin/env python3
"""First measured-terrain rebuild pass.

This deliberately stops before Unreal. It inspects the preserved airborne LAS
and can rasterise a user-specified validation window into raw DEM/DSM/CHM NPZ.
No synthetic lava, no interpolation, no silent hole filling.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np

from real_terrain_lib import (
    DEFAULT_SURVEY_ROOT,
    class_histogram,
    derive_dem_dsm,
    point_bounds,
    print_source_report,
    read_las_from_zip,
    save_terrain_npz,
)

def parser():
    p = argparse.ArgumentParser()
    p.add_argument("--source-root", type=Path, default=DEFAULT_SURVEY_ROOT)
    p.add_argument("--archive", default="08LE9307.zip")
    p.add_argument("--inspect-only", action="store_true")
    p.add_argument("--bounds", type=float, nargs=4, metavar=("XMIN", "YMIN", "XMAX", "YMAX"))
    p.add_argument("--resolution", type=float, default=0.5)
    p.add_argument(
        "--out",
        type=Path,
        default=Path("ImportData/measured_validation_0p5m.npz"),
    )
    return p

def main():
    args = parser().parse_args()
    if not print_source_report(args.source_root):
        raise SystemExit("required preserved sources are missing or empty")

    archive = args.source_root / args.archive
    las = read_las_from_zip(archive)
    print("point_count:", len(las.points))
    print("bounds_xyz:", point_bounds(las))
    print("classification:", class_histogram(las))
    print("header_crs:", las.header.parse_crs())
    print(
        "IMPORTANT: preserved notes say these Yamanashi files carry no CRS VLR; "
        "treat coordinates as EPSG:6676."
    )

    if args.inspect_only:
        return

    if args.bounds is None:
        raise SystemExit(
            "Refusing to guess the validation crop. Pass --bounds XMIN YMIN XMAX YMAX "
            "after checking the MMS trajectory / relief source."
        )

    layers = derive_dem_dsm(las, tuple(args.bounds), args.resolution)
    measured = layers["measured_mask"]
    print("grid:", layers["dem"].shape)
    print("DEM measured cells:", int(np.isfinite(layers["dem"]).sum()))
    print("DSM measured cells:", int(np.isfinite(layers["dsm"]).sum()))
    print("CHM measured cells:", int(measured.sum()))
    print("CHM max:", float(np.nanmax(layers["chm"])) if measured.any() else None)

    save_terrain_npz(
        args.out,
        layers,
        tuple(args.bounds),
        args.resolution,
        args.archive,
    )
    print("wrote", args.out, "and", args.out.with_suffix(".json"))

if __name__ == "__main__":
    main()
