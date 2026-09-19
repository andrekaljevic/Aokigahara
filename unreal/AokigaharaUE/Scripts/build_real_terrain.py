#!/usr/bin/env python3
"""First measured-terrain rebuild pass.

This deliberately stops before Unreal. It inspects the preserved airborne LAS
and can rasterise a user-specified validation window into measured raw-cell
analogues of Yamanashi DEM/DSM1/DSM2.

No synthetic lava, no interpolation, no silent hole filling.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np

from real_terrain_lib import (
    DEFAULT_SURVEY_ROOT,
    class_histogram,
    derive_official_class_products,
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
    histogram = class_histogram(las)
    print("point_count:", len(las.points))
    print("bounds_xyz:", point_bounds(las))
    print("classification:", histogram)
    print("header_crs:", las.header.parse_crs())
    print(
        "Provider semantics: class 1 surface; class 2 ground; "
        "class 9 transmission towers/power lines."
    )
    print(
        "IMPORTANT: preserved notes say these LAS files carry no CRS VLR; "
        "treat coordinates as EPSG:6676 and prove stored X/Y against mmstrj."
    )

    for required_class in (1, 2):
        if histogram.get(required_class, 0) == 0:
            raise SystemExit(
                f"expected provider class {required_class} but found none; "
                "stop rather than inventing a fallback"
            )

    if args.inspect_only:
        return

    if args.bounds is None:
        raise SystemExit(
            "Refusing to guess the validation crop. Pass --bounds XMIN YMIN XMAX YMAX "
            "after checking the MMS trajectory / published relief."
        )

    layers = derive_official_class_products(
        las, tuple(args.bounds), args.resolution
    )
    print("grid:", layers["dem"].shape)
    for key in ("dem", "dsm2_surface", "dsm1_surface_utility", "chm_dsm2", "chm_dsm1"):
        print(f"{key} measured cells:", int(np.isfinite(layers[key]).sum()))

    save_terrain_npz(
        args.out,
        layers,
        tuple(args.bounds),
        args.resolution,
        args.archive,
    )
    print("wrote", args.out, "and", args.out.with_suffix(".json"))
    print(
        "NEXT VALIDATION: compare these raw-cell products against Yamanashi's "
        "published 0.50 m DEM/DSM1/DSM2. Do not treat equality as assumed."
    )

if __name__ == "__main__":
    main()
