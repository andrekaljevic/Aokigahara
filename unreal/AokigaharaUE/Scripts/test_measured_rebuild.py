#!/usr/bin/env python3
from __future__ import annotations

import math
import numpy as np

from jprcs8 import en_to_lonlat, lonlat_to_en
from real_terrain_lib import rasterize_extreme

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

if __name__ == "__main__":
    test_epsg_fixture()
    test_raster_orientation_and_nodata()
    print("ALL MEASURED-REBUILD TESTS PASSED")
