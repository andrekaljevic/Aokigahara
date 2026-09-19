#!/usr/bin/env python3
from __future__ import annotations

import math
from types import SimpleNamespace
import numpy as np

from jprcs8 import en_to_lonlat, lonlat_to_en
from real_terrain_lib import derive_official_class_products, rasterize_extreme

def test_epsg_fixture():
    # EPSG:6676 reference fixture for Fugaku Wind Cave.
    e, n = lonlat_to_en(138.657503, 35.477501)
    assert abs(e - 14292.711575247753) < 0.001
    assert abs(n - (-57956.2426950187)) < 0.001
    lon, lat = en_to_lonlat(e, n)
    assert abs(lon - 138.657503) < 1e-9
    assert abs(lat - 35.477501) < 1e-9

def test_raster_orientation_and_nodata():
    # 2 x 2 m area at 1 m. Row 0 must be north.
    x = np.array([0.25, 0.25, 1.25])
    y = np.array([0.25, 1.25, 1.25])
    z = np.array([10.0, 20.0, 30.0])
    grid, count = rasterize_extreme(
        x, y, z, (0, 0, 2, 2), 1.0, "max"
    )
    assert grid.shape == (2, 2)
    assert grid[0, 0] == 20.0  # north-west
    assert grid[0, 1] == 30.0  # north-east
    assert grid[1, 0] == 10.0  # south-west
    assert math.isnan(float(grid[1, 1]))
    assert count[1, 1] == 0

def test_yamanashi_class_semantics():
    # One cell: ground 10, surface 20, utility 30, unrelated class 5 at 99.
    fake = SimpleNamespace(
        x=np.array([0.2, 0.3, 0.4, 0.45]),
        y=np.array([0.2, 0.3, 0.4, 0.45]),
        z=np.array([10.0, 20.0, 30.0, 99.0]),
        classification=np.array([2, 1, 9, 5], dtype=np.uint8),
    )
    layers = derive_official_class_products(fake, (0, 0, 1, 1), 1.0)
    assert layers["dem"][0, 0] == 10.0
    assert layers["dsm2_surface"][0, 0] == 20.0
    assert layers["dsm1_surface_utility"][0, 0] == 30.0
    assert layers["chm_dsm2"][0, 0] == 10.0
    assert layers["chm_dsm1"][0, 0] == 20.0

if __name__ == "__main__":
    test_epsg_fixture()
    test_raster_orientation_and_nodata()
    test_yamanashi_class_semantics()
    print("ALL MEASURED-REBUILD TESTS PASSED")
