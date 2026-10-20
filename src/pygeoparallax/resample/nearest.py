"""Nearest-neighbour sampling between arbitrary lat/lon point sets."""

from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

EARTH_RADIUS_KM = 6371.0


def _unit_xyz(lat, lon):
    lat = np.radians(np.asarray(lat, float))
    lon = np.radians(np.asarray(lon, float))
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=-1)


def sample_nearest(src_lat, src_lon, values, dst_lat, dst_lon, max_distance_km=50.0):
    """Value of the nearest source point for each destination point.

    Use it to bring a coarse product (e.g. ISRO CTP at ~37 km) onto L1C
    pixels. Source points with NaN position or value are ignored, and
    destination points farther than ``max_distance_km`` from any source get NaN.
    """
    src_lat = np.asarray(src_lat, float).ravel()
    src_lon = np.asarray(src_lon, float).ravel()
    values = np.asarray(values, float).ravel()
    ok = np.isfinite(src_lat) & np.isfinite(src_lon) & np.isfinite(values)
    dst_lat = np.asarray(dst_lat, float)
    out = np.full(dst_lat.shape, np.nan)
    if not ok.any():
        return out
    tree = cKDTree(_unit_xyz(src_lat[ok], src_lon[ok]))
    dist, idx = tree.query(_unit_xyz(dst_lat, dst_lon).reshape(-1, 3))
    dist_km = 2 * EARTH_RADIUS_KM * np.arcsin(np.clip(dist / 2, 0, 1))  # chord -> great circle
    vals = values[ok][np.minimum(idx, ok.sum() - 1)]
    vals[~np.isfinite(dist) | (dist_km > max_distance_km)] = np.nan
    return vals.reshape(dst_lat.shape)
