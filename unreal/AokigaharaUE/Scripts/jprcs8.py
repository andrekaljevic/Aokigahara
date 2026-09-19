"""JGD2011 / Japan Plane Rectangular CS VIII helpers.

EPSG:6676 is the CRS used by the preserved Yamanashi point-cloud sources.
This module is for OFFLINE preprocessing, not Unreal's embedded Python.

Important axis convention:
    pyproj with always_xy=True returns (easting, northing).
EPSG's formal axis names are northing (X), easting (Y), so do not mix the
two conventions silently. Functions here are named *_en to make the order
explicit.
"""
from __future__ import annotations

EPSG = 6676
PROJ4 = (
    "+proj=tmerc +lat_0=36 +lon_0=138.5 +k=0.9999 "
    "+x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs +type=crs"
)

def _transformers():
    try:
        from pyproj import Transformer
    except ImportError as exc:
        raise RuntimeError(
            "pyproj is required for the measured-data preprocessing pipeline. "
            "Install Scripts/requirements-measured.txt."
        ) from exc
    fwd = Transformer.from_crs(4326, EPSG, always_xy=True)
    inv = Transformer.from_crs(EPSG, 4326, always_xy=True)
    return fwd, inv

def lonlat_to_en(lon: float, lat: float) -> tuple[float, float]:
    """WGS84 longitude/latitude -> (easting, northing) metres in EPSG:6676."""
    fwd, _ = _transformers()
    e, n = fwd.transform(lon, lat)
    return float(e), float(n)

def en_to_lonlat(easting: float, northing: float) -> tuple[float, float]:
    """(easting, northing) metres in EPSG:6676 -> WGS84 (lon, lat)."""
    _, inv = _transformers()
    lon, lat = inv.transform(easting, northing)
    return float(lon), float(lat)

def epsg_axis_xy(lon: float, lat: float) -> tuple[float, float]:
    """Return formal EPSG axis order: (northing X, easting Y)."""
    e, n = lonlat_to_en(lon, lat)
    return n, e

if __name__ == "__main__":
    # Independent fixture: Fugaku Wind Cave WGS84 coordinates used elsewhere
    # in the project. Expected values were generated from EPSG:6676.
    lon, lat = 138.657503, 35.477501
    e, n = lonlat_to_en(lon, lat)
    print(f"EPSG:{EPSG} easting={e:.6f} northing={n:.6f}")
    print("roundtrip", en_to_lonlat(e, n))
