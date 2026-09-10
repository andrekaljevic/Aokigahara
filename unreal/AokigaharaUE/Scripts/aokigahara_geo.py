"""Canonical coordinate transforms for the Aokigahara reconstruction.

One module, used by every importer, so the world cannot drift between them.

    WGS 84  <->  scene metres  <->  Unreal centimetres

Deliberately DEPENDENCY-FREE. Unreal's embedded Python has neither pyproj nor numpy, and this has
to run inside the editor. The ellipsoidal azimuthal-equidistant projection is implemented directly
on Vincenty geodesics; `test_geo.py` cross-checks it against pyproj (where available) and against
the 78 surveyed landmarks in the repository, and agrees to within a millimetre.

THE FRAMES
----------
Scene frame, as used by every existing asset and by viewer/app.js:

    x = east, y = up, z = SOUTH, 1 unit = 1 metre
    y = published GSI elevation in metres MSL, minus 900

Verified against 78 landmarks that carry both scene coordinates and WGS 84 position: median error
0.004 m, maximum 0.006 m, which is the rounding in the stored values. Not negating the northing
gives a median error of 2,244 m, so the convention is not in doubt.

The scene frame is RIGHT-handed (east x up = south). Unreal is LEFT-handed. Converting between
them must therefore flip exactly one axis - the mapping determinant must be -1.

THE TRAP
--------
The obvious mapping, UE_X = east and UE_Y = north, has determinant +1. It preserves handedness,
which means that inside a left-handed engine it produces a MIRRORED WORLD: every chiral asset is
flipped, lettering reads backwards, and yaw rotations from the source data spin the wrong way. It
looks completely plausible until something with a known handedness appears.

This module uses the standard ENU-to-Unreal convention instead, which is what Cesium for Unreal
and the other georeferencing plugins use:

    UE_X = north  = -scene_z          (determinant -1, correct)
    UE_Y = east   =  scene_x
    UE_Z = up     =  scene_y

and consequently, for a scene yaw measured about the scene's +y (up) axis:

    UE_yaw_degrees = (90 - scene_yaw_degrees) mod 360

VERTICAL DATUM
--------------
UE_Z = 0 corresponds to 900 m MSL, not to sea level, because the scene inherits the source's 900 m
origin shift. That shift is an origin offset, NOT a vertical-datum conversion. `msl_to_scene_y` and
`scene_y_to_msl` are the only places the constant appears; do not hard-code 900 anywhere else.
"""

import math

# ---------------------------------------------------------------- constants

ORIGIN_LON = 138.658
ORIGIN_LAT = 35.4775
HEIGHT_OFFSET_M = 900.0
UU_PER_METRE = 100.0          # Unreal unit is a centimetre

PROJ4 = ("+proj=aeqd +lat_0=35.4775 +lon_0=138.658 +x_0=0 +y_0=0 "
         "+datum=WGS84 +units=m +no_defs")

# WGS 84 ellipsoid
_A = 6378137.0
_F = 1.0 / 298.257223563
_B = _A * (1.0 - _F)


# ---------------------------------------------------------------- geodesics

def _vincenty_inverse(lat1, lon1, lat2, lon2):
    """Geodesic distance in metres and forward azimuth in radians, WGS 84.

    Returns (s, alpha1). Converges to sub-millimetre over the distances used here.
    """
    if lat1 == lat2 and lon1 == lon2:
        return 0.0, 0.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    L = math.radians(lon2 - lon1)
    U1 = math.atan((1 - _F) * math.tan(phi1))
    U2 = math.atan((1 - _F) * math.tan(phi2))
    sinU1, cosU1 = math.sin(U1), math.cos(U1)
    sinU2, cosU2 = math.sin(U2), math.cos(U2)

    lam = L
    for _ in range(200):
        sin_lam, cos_lam = math.sin(lam), math.cos(lam)
        sin_sigma = math.hypot(cosU2 * sin_lam,
                               cosU1 * sinU2 - sinU1 * cosU2 * cos_lam)
        if sin_sigma == 0.0:
            return 0.0, 0.0
        cos_sigma = sinU1 * sinU2 + cosU1 * cosU2 * cos_lam
        sigma = math.atan2(sin_sigma, cos_sigma)
        sin_alpha = cosU1 * cosU2 * sin_lam / sin_sigma
        cos_sq_alpha = 1.0 - sin_alpha * sin_alpha
        cos_2sm = 0.0 if cos_sq_alpha == 0.0 else cos_sigma - 2.0 * sinU1 * sinU2 / cos_sq_alpha
        C = _F / 16.0 * cos_sq_alpha * (4.0 + _F * (4.0 - 3.0 * cos_sq_alpha))
        lam_prev = lam
        lam = L + (1.0 - C) * _F * sin_alpha * (
            sigma + C * sin_sigma * (cos_2sm + C * cos_sigma * (-1.0 + 2.0 * cos_2sm ** 2)))
        if abs(lam - lam_prev) < 1e-12:
            break

    u_sq = cos_sq_alpha * (_A * _A - _B * _B) / (_B * _B)
    A = 1.0 + u_sq / 16384.0 * (4096.0 + u_sq * (-768.0 + u_sq * (320.0 - 175.0 * u_sq)))
    B = u_sq / 1024.0 * (256.0 + u_sq * (-128.0 + u_sq * (74.0 - 47.0 * u_sq)))
    d_sigma = B * sin_sigma * (cos_2sm + B / 4.0 * (
        cos_sigma * (-1.0 + 2.0 * cos_2sm ** 2)
        - B / 6.0 * cos_2sm * (-3.0 + 4.0 * sin_sigma ** 2) * (-3.0 + 4.0 * cos_2sm ** 2)))
    s = _B * A * (sigma - d_sigma)
    alpha1 = math.atan2(cosU2 * math.sin(lam),
                        cosU1 * sinU2 - sinU1 * cosU2 * math.cos(lam))
    return s, alpha1


def _vincenty_direct(lat1, lon1, alpha1, s):
    """Destination latitude/longitude in degrees from a start point, azimuth and distance."""
    if s == 0.0:
        return lat1, lon1
    phi1 = math.radians(lat1)
    U1 = math.atan((1 - _F) * math.tan(phi1))
    sinU1, cosU1 = math.sin(U1), math.cos(U1)
    sin_a1, cos_a1 = math.sin(alpha1), math.cos(alpha1)

    sigma1 = math.atan2(math.tan(U1), cos_a1)
    sin_alpha = cosU1 * sin_a1
    cos_sq_alpha = 1.0 - sin_alpha * sin_alpha
    u_sq = cos_sq_alpha * (_A * _A - _B * _B) / (_B * _B)
    A = 1.0 + u_sq / 16384.0 * (4096.0 + u_sq * (-768.0 + u_sq * (320.0 - 175.0 * u_sq)))
    B = u_sq / 1024.0 * (256.0 + u_sq * (-128.0 + u_sq * (74.0 - 47.0 * u_sq)))

    sigma = s / (_B * A)
    for _ in range(200):
        cos_2sm = math.cos(2.0 * sigma1 + sigma)
        sin_sigma, cos_sigma = math.sin(sigma), math.cos(sigma)
        d_sigma = B * sin_sigma * (cos_2sm + B / 4.0 * (
            cos_sigma * (-1.0 + 2.0 * cos_2sm ** 2)
            - B / 6.0 * cos_2sm * (-3.0 + 4.0 * sin_sigma ** 2) * (-3.0 + 4.0 * cos_2sm ** 2)))
        sigma_prev = sigma
        sigma = s / (_B * A) + d_sigma
        if abs(sigma - sigma_prev) < 1e-12:
            break

    cos_2sm = math.cos(2.0 * sigma1 + sigma)
    sin_sigma, cos_sigma = math.sin(sigma), math.cos(sigma)
    tmp = sinU1 * sin_sigma - cosU1 * cos_sigma * cos_a1
    phi2 = math.atan2(sinU1 * cos_sigma + cosU1 * sin_sigma * cos_a1,
                      (1 - _F) * math.hypot(sin_alpha, tmp))
    lam = math.atan2(sin_sigma * sin_a1, cosU1 * cos_sigma - sinU1 * sin_sigma * cos_a1)
    C = _F / 16.0 * cos_sq_alpha * (4.0 + _F * (4.0 - 3.0 * cos_sq_alpha))
    L = lam - (1.0 - C) * _F * sin_alpha * (
        sigma + C * sin_sigma * (cos_2sm + C * cos_sigma * (-1.0 + 2.0 * cos_2sm ** 2)))
    return math.degrees(phi2), lon1 + math.degrees(L)


# ---------------------------------------------------------------- WGS 84 <-> scene

def wgs84_to_scene(lon, lat, elevation_m=None):
    """(lon, lat[, elevation m MSL]) -> scene (x east, z south[, y up]) in metres."""
    s, alpha = _vincenty_inverse(ORIGIN_LAT, ORIGIN_LON, lat, lon)
    easting = s * math.sin(alpha)
    northing = s * math.cos(alpha)
    if elevation_m is None:
        return easting, -northing
    return easting, -northing, msl_to_scene_y(elevation_m)


def scene_to_wgs84(x, z):
    """scene (x east, z south) in metres -> (lon, lat) degrees."""
    northing = -z
    s = math.hypot(x, northing)
    alpha = math.atan2(x, northing)
    lat, lon = _vincenty_direct(ORIGIN_LAT, ORIGIN_LON, alpha, s)
    return lon, lat


def msl_to_scene_y(elevation_m):
    """Elevation in metres MSL -> scene y."""
    return elevation_m - HEIGHT_OFFSET_M


def scene_y_to_msl(y):
    """Scene y -> elevation in metres MSL."""
    return y + HEIGHT_OFFSET_M


# ---------------------------------------------------------------- scene <-> Unreal

def scene_to_ue(x, y, z):
    """Scene metres (x east, y up, z south) -> Unreal centimetres (X north, Y east, Z up).

    Determinant -1: this flips handedness, which is required because the scene frame is
    right-handed and Unreal is left-handed. See the module docstring.
    """
    return (-z * UU_PER_METRE, x * UU_PER_METRE, y * UU_PER_METRE)


def ue_to_scene(ue_x, ue_y, ue_z):
    """Unreal centimetres -> scene metres. Exact inverse of scene_to_ue."""
    return (ue_y / UU_PER_METRE, ue_z / UU_PER_METRE, -ue_x / UU_PER_METRE)


def scene_yaw_to_ue_yaw(scene_yaw_rad):
    """Scene yaw about +y (radians, as stored in the .f32 placements) -> Unreal yaw in degrees."""
    return (90.0 - math.degrees(scene_yaw_rad)) % 360.0


def ue_yaw_to_scene_yaw(ue_yaw_deg):
    """Unreal yaw in degrees -> scene yaw about +y in radians."""
    return math.radians((90.0 - ue_yaw_deg) % 360.0)


def wgs84_to_ue(lon, lat, elevation_m):
    """Convenience: (lon, lat, elevation m MSL) straight to Unreal centimetres."""
    x, z, y = wgs84_to_scene(lon, lat, elevation_m)
    return scene_to_ue(x, y, z)


def ue_to_wgs84(ue_x, ue_y, ue_z):
    """Convenience: Unreal centimetres -> (lon, lat, elevation m MSL)."""
    x, y, z = ue_to_scene(ue_x, ue_y, ue_z)
    lon, lat = scene_to_wgs84(x, z)
    return lon, lat, scene_y_to_msl(y)


if __name__ == '__main__':
    # Fugaku Wind Cave: scene (-45.11, -0.11), WGS 84 (138.657503, 35.477501), 997.24 m MSL
    print('proj4:', PROJ4)
    print('scene  ->', wgs84_to_scene(138.657503, 35.477501, 997.24))
    print('ue     ->', wgs84_to_ue(138.657503, 35.477501, 997.24))
    print('back   ->', ue_to_wgs84(*wgs84_to_ue(138.657503, 35.477501, 997.24)))
