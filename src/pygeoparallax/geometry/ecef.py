"""Conversions between geodetic (WGS84) and Earth-Centred Earth-Fixed coordinates.

All functions are vectorised over numpy arrays. Angles are in degrees and
lengths in metres.
"""

from __future__ import annotations

import numpy as np

from .constants import WGS84_A, WGS84_B, WGS84_E2, WGS84_EP2


def geodetic_to_ecef(lat, lon, h=0.0):
    """Convert geodetic latitude, longitude and ellipsoidal height to ECEF x, y, z."""
    lat = np.radians(lat)
    lon = np.radians(lon)
    sin_lat = np.sin(lat)
    cos_lat = np.cos(lat)
    n = WGS84_A / np.sqrt(1.0 - WGS84_E2 * sin_lat**2)  # prime vertical radius
    x = (n + h) * cos_lat * np.cos(lon)
    y = (n + h) * cos_lat * np.sin(lon)
    z = (n * (1.0 - WGS84_E2) + h) * sin_lat
    return x, y, z


def ecef_to_geodetic(x, y, z, iterations=3):
    """Convert ECEF x, y, z to geodetic latitude, longitude and ellipsoidal height.

    Uses Bowring's method. Three iterations reach sub-millimetre accuracy for
    any point from the Earth's surface out to geostationary orbit.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    lon = np.arctan2(y, x)
    p = np.hypot(x, y)

    beta = np.arctan2(WGS84_A * z, WGS84_B * p)  # initial parametric latitude
    for _ in range(iterations):
        lat = np.arctan2(
            z + WGS84_EP2 * WGS84_B * np.sin(beta) ** 3,
            p - WGS84_E2 * WGS84_A * np.cos(beta) ** 3,
        )
        beta = np.arctan2(WGS84_B * np.sin(lat), WGS84_A * np.cos(lat))

    sin_lat = np.sin(lat)
    n = WGS84_A / np.sqrt(1.0 - WGS84_E2 * sin_lat**2)
    # This height formula stays well-conditioned at both the equator and the poles.
    h = p * np.cos(lat) + z * sin_lat - WGS84_A**2 / n
    return np.degrees(lat), np.degrees(lon), h


def enu_basis(lat, lon):
    """Local east, north and up unit vectors (ECEF components) at geodetic lat/lon.

    Each returned vector has shape ``(3, *lat.shape)``.
    """
    lat = np.radians(lat)
    lon = np.radians(lon)
    sin_lat, cos_lat = np.sin(lat), np.cos(lat)
    sin_lon, cos_lon = np.sin(lon), np.cos(lon)
    zeros = np.zeros_like(sin_lat * sin_lon)
    east = np.stack([-sin_lon + zeros, cos_lon + zeros, zeros])
    north = np.stack([-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat + zeros])
    up = np.stack([cos_lat * cos_lon, cos_lat * sin_lon, sin_lat + zeros])
    return east, north, up
