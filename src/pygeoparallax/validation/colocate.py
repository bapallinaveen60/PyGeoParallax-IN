"""Put radar observations on the analysis grid and match them in space and time."""

from __future__ import annotations

import numpy as np

from ..resample.grid import Grid

EARTH_RADIUS_KM = 6371.0


def points_to_grid(grid: Grid, lat, lon, values, how="mean"):
    """Average (or take the maximum of) scattered points per grid cell.

    Use this for GPM-DPR footprints (~5 km) or radar polar bins. Cells without
    points are NaN; NaN values are ignored.
    """
    lat = np.asarray(lat, float).ravel()
    lon = np.asarray(lon, float).ravel()
    values = np.asarray(values, float).ravel()
    row, col, valid = grid.cell_index(lat, lon)
    valid &= np.isfinite(values)
    cell = (row * grid.shape[1] + col)[valid]
    v = values[valid]
    n_cells = grid.shape[0] * grid.shape[1]

    out = np.full(n_cells, np.nan)
    if how == "mean":
        total = np.bincount(cell, weights=v, minlength=n_cells)
        count = np.bincount(cell, minlength=n_cells)
        has = count > 0
        out[has] = total[has] / count[has]
    elif how == "max":
        np.fmax.at(out, cell, v)
    else:
        raise ValueError(f"unknown aggregation {how!r}")
    return out.reshape(grid.shape)


def range_mask(grid: Grid, lat0, lon0, range_km):
    """Cells whose centre is within ``range_km`` of a radar (great-circle distance)."""
    glat, glon = np.meshgrid(np.radians(grid.lats), np.radians(grid.lons), indexing="ij")
    p0, l0 = np.radians(lat0), np.radians(lon0)
    a = np.sin((glat - p0) / 2) ** 2 + np.cos(p0) * np.cos(glat) * np.sin((glon - l0) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a)) <= range_km


def nearest_time(times, target, max_dt="15min"):
    """Index of the time closest to ``target``, or -1 if none is within ``max_dt``.

    Use it to pair a GPM overpass or radar volume with an INSAT-3DR scan.
    """
    times = np.asarray(times, dtype="datetime64[ns]")
    if times.size == 0:
        return -1
    dt = np.abs(times - np.datetime64(target, "ns"))
    i = int(np.argmin(dt))
    limit = _parse_timedelta(max_dt)
    return i if dt[i] <= limit else -1


def _parse_timedelta(value):
    if isinstance(value, np.timedelta64):
        return value.astype("timedelta64[ns]")
    import pandas as pd

    return np.timedelta64(pd.Timedelta(value).value, "ns")
