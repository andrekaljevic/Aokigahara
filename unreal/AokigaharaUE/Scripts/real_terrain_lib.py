"""Measured-terrain utilities for the Aokigahara rebuild.

No procedural terrain synthesis belongs here. Missing measurements remain NaN
and are accompanied by counts/masks so downstream steps cannot mistake filled
or fabricated values for observations.

Yamanashi's current catalogue documents the airborne LAS classes used here:
    class 1 = surface (buildings/trees/other surface features)
    class 2 = ground
    class 9 = transmission towers / power lines

Its published 0.50 m products are:
    DSM1: classes 1 + 9
    DSM2: class 1
    DEM:  ground/class 2

The raw-point rasteriser below follows those class sets, but it is NOT claimed
to reproduce the provider's gridding algorithm byte-for-byte. Published grids
remain the validation reference.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import io
import json
import os
import zipfile

import numpy as np

CRS_EPSG = 6676
OFFICIAL_SURFACE_CLASSES = (1,)
OFFICIAL_GROUND_CLASSES = (2,)
OFFICIAL_UTILITY_CLASSES = (9,)

DEFAULT_SURVEY_ROOT = Path(
    os.environ.get("AOKIGAHARA_SURVEY_ROOT", "/Users/Shared/Aokigahara-survey-2026-09-17")
)

@dataclass(frozen=True)
class SourceSpec:
    filename: str
    purpose: str
    required: bool = True

SOURCES = (
    SourceSpec("08LE9307.zip", "Yamanashi 2024 airborne classified LAS"),
    SourceSpec("mms_08LE9307.zip", "Yamanashi 2024 MMS vehicle LiDAR + genuine per-point RGB"),
    SourceSpec("mmstrj.zip", "MMS trajectory shapefile"),
    SourceSpec("fr_mesh20m_08le3_2025.7z", "20 m forest register: species and stand age"),
    SourceSpec("survey_report.md", "source catalogue, licence audit and re-download instructions"),
)

def validate_source_root(root: Path = DEFAULT_SURVEY_ROOT) -> dict:
    root = Path(root)
    rows = []
    ok = True
    for spec in SOURCES:
        p = root / spec.filename
        exists = p.is_file()
        size = p.stat().st_size if exists else 0
        good = exists and size > 0
        ok = ok and (good or not spec.required)
        rows.append({
            "filename": spec.filename,
            "purpose": spec.purpose,
            "required": spec.required,
            "exists": exists,
            "bytes": size,
            "nonempty": good,
        })
    return {"root": str(root), "ok": ok, "sources": rows}

def print_source_report(root: Path = DEFAULT_SURVEY_ROOT) -> bool:
    report = validate_source_root(root)
    print(f"survey root: {report['root']}")
    for row in report["sources"]:
        mark = "OK" if row["nonempty"] else "MISSING"
        print(f"{mark:7s} {row['filename']:28s} {row['bytes']:>12,d}  {row['purpose']}")
    return bool(report["ok"])

def read_las_from_zip(zip_path: Path, member: str | None = None):
    """Read the single LAS/LAZ member of a zip with laspy, without permanent extraction."""
    try:
        import laspy
    except ImportError as exc:
        raise RuntimeError("laspy is required; install requirements-measured.txt") from exc

    zip_path = Path(zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        candidates = [n for n in zf.namelist() if n.lower().endswith((".las", ".laz"))]
        if member is None:
            if len(candidates) != 1:
                raise ValueError(
                    f"{zip_path.name}: expected exactly one LAS/LAZ member; found {candidates}"
                )
            member = candidates[0]
        if member not in zf.namelist():
            raise FileNotFoundError(f"{member!r} not present in {zip_path}")
        data = zf.read(member)
    return laspy.read(io.BytesIO(data))

def class_histogram(las) -> dict[int, int]:
    c = np.asarray(las.classification, dtype=np.uint8)
    keys, counts = np.unique(c, return_counts=True)
    return {int(k): int(v) for k, v in zip(keys, counts)}

def point_bounds(las) -> tuple[float, float, float, float, float, float]:
    x = np.asarray(las.x)
    y = np.asarray(las.y)
    z = np.asarray(las.z)
    return tuple(map(float, (x.min(), y.min(), z.min(), x.max(), y.max(), z.max())))

def _grid_shape(bounds, resolution):
    xmin, ymin, xmax, ymax = map(float, bounds)
    if not (xmax > xmin and ymax > ymin and resolution > 0):
        raise ValueError("invalid bounds or resolution")
    cols = int(np.ceil((xmax - xmin) / resolution))
    rows = int(np.ceil((ymax - ymin) / resolution))
    return rows, cols

def rasterize_extreme(x, y, z, bounds, resolution, mode="min"):
    """Rasterise measured points; row 0 is the NORTH/top edge.

    Returns (grid, count). Cells without observations remain NaN.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    if not (x.shape == y.shape == z.shape):
        raise ValueError("x/y/z shapes differ")

    xmin, ymin, xmax, ymax = map(float, bounds)
    rows, cols = _grid_shape(bounds, resolution)
    col = np.floor((x - xmin) / resolution).astype(np.int64)
    row_from_south = np.floor((y - ymin) / resolution).astype(np.int64)
    row = rows - 1 - row_from_south
    valid = (
        np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
        & (col >= 0) & (col < cols) & (row >= 0) & (row < rows)
    )
    row = row[valid]
    col = col[valid]
    zv = z[valid]
    flat = row * cols + col

    count = np.zeros(rows * cols, dtype=np.uint32)
    np.add.at(count, flat, 1)

    if mode == "min":
        work = np.full(rows * cols, np.inf, dtype=np.float64)
        np.minimum.at(work, flat, zv)
    elif mode == "max":
        work = np.full(rows * cols, -np.inf, dtype=np.float64)
        np.maximum.at(work, flat, zv)
    else:
        raise ValueError("mode must be 'min' or 'max'")

    work[count == 0] = np.nan
    return work.reshape(rows, cols).astype(np.float32), count.reshape(rows, cols)

def _class_mask(cls, classes):
    return np.isin(cls, np.asarray(tuple(classes), dtype=np.uint8))

def derive_official_class_products(
    las,
    bounds,
    resolution=0.5,
    ground_classes=OFFICIAL_GROUND_CLASSES,
    surface_classes=OFFICIAL_SURFACE_CLASSES,
    utility_classes=OFFICIAL_UTILITY_CLASSES,
):
    """Create measured raw-cell analogues of Yamanashi DEM/DSM1/DSM2.

    DEM raw-cell analogue  = minimum class-2 ground return.
    DSM2 raw-cell analogue = maximum class-1 surface return.
    DSM1 raw-cell analogue = maximum class-1 or class-9 return.

    This deliberately does NOT interpolate and does not claim to duplicate the
    provider's published gridding algorithm. Use the published 0.50 m grids as
    the external validation target.
    """
    x = np.asarray(las.x)
    y = np.asarray(las.y)
    z = np.asarray(las.z)
    cls = np.asarray(las.classification, dtype=np.uint8)

    ground = _class_mask(cls, ground_classes)
    surface = _class_mask(cls, surface_classes)
    surface_utility = _class_mask(cls, tuple(surface_classes) + tuple(utility_classes))

    dem, ground_count = rasterize_extreme(
        x[ground], y[ground], z[ground], bounds, resolution, "min"
    )
    dsm2, surface_count = rasterize_extreme(
        x[surface], y[surface], z[surface], bounds, resolution, "max"
    )
    dsm1, surface_utility_count = rasterize_extreme(
        x[surface_utility], y[surface_utility], z[surface_utility],
        bounds, resolution, "max"
    )

    def chm(dsm):
        out = np.full_like(dem, np.nan, dtype=np.float32)
        measured = np.isfinite(dem) & np.isfinite(dsm)
        out[measured] = np.maximum(dsm[measured] - dem[measured], 0.0)
        return out, measured

    chm2, measured2 = chm(dsm2)
    chm1, measured1 = chm(dsm1)
    return {
        "dem": dem,
        "dsm2_surface": dsm2,
        "dsm1_surface_utility": dsm1,
        "chm_dsm2": chm2,
        "chm_dsm1": chm1,
        "ground_count": ground_count,
        "surface_count": surface_count,
        "surface_utility_count": surface_utility_count,
        "measured_mask_dsm2": measured2,
        "measured_mask_dsm1": measured1,
    }

# Backward-compatible name for the first rebuild commit. New code should call
# derive_official_class_products so the provider semantics are visible.
derive_dem_dsm = derive_official_class_products

def save_terrain_npz(path: Path, layers: dict, bounds, resolution: float, source_archive: str):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        **layers,
        bounds=np.asarray(bounds, dtype=np.float64),
        resolution=np.asarray([resolution], dtype=np.float64),
        crs_epsg=np.asarray([CRS_EPSG], dtype=np.int32),
    )
    meta = {
        "crs_epsg": CRS_EPSG,
        "axis_note": (
            "grid coordinates are LAS x/y as stored; validate against trajectory "
            "before naming them easting/northing"
        ),
        "row_order": "north_to_south",
        "resolution_m": float(resolution),
        "bounds": list(map(float, bounds)),
        "source_archive": source_archive,
        "classification": {
            "surface_class": 1,
            "ground_class": 2,
            "utility_class": 9,
            "dsm1_classes": [1, 9],
            "dsm2_classes": [1],
        },
        "gridding": "raw cell extrema; not asserted identical to provider published grids",
        "interpolation": "none",
        "nodata": "NaN",
    }
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2) + "\n")
