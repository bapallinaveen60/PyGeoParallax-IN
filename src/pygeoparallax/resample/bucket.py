"""Occlusion-aware bucket resampling of (parallax-corrected) pixels onto a grid.

After parallax correction, satellite pixels no longer sit on a regular grid:
several can land in one cell and some cells get none. This module puts them
back on a :class:`~pygeoparallax.resample.grid.Grid`:

* **Collisions:** the pixel with the greatest height wins, because a high
  cloud hides whatever is below it from the satellite.
* **Small gaps:** cells left empty by sampling (the pixels spread out) are
  filled by inverse-distance weighting from neighbours within
  ``fill_radius`` cells.
* **Large gaps:** cells behind tall clouds, which the satellite never saw,
  are left as NaN.

``fill_flag`` records which case each cell is, so later analysis can exclude
interpolated or unseen cells.
"""

from __future__ import annotations

import numpy as np
import xarray as xr
from scipy import ndimage

from .grid import Grid

OBSERVED = 0
INTERPOLATED = 1
EMPTY = 2


def bucket_max_height(grid: Grid, lat, lon, height, values: dict):
    """Grid pixels, keeping the highest pixel in each cell.

    Parameters
    ----------
    grid : Grid
    lat, lon : array_like
        Pixel positions [degrees]. NaN positions are dropped.
    height : array_like
        Height used to resolve collisions [m]; NaN counts as lowest.
    values : dict of str -> array_like
        Pixel values to grid, e.g. ``{"TIR1": bt, "cth": cth}``.

    Returns
    -------
    gridded : dict of str -> ndarray
        Gridded values (NaN where empty), plus ``"height"`` (the winning
        height) and ``"count"`` (pixels that landed in each cell).
    """
    lat = np.asarray(lat, float).ravel()
    lon = np.asarray(lon, float).ravel()
    height = np.asarray(height, float).ravel()
    row, col, valid = grid.cell_index(lat, lon)

    cell = (row * grid.shape[1] + col)[valid]
    h = np.where(np.isnan(height), -np.inf, height)[valid]
    src = np.flatnonzero(valid)

    # Sort by cell, then height; the last entry of each cell is the highest pixel.
    order = np.lexsort((h, cell))
    cell_sorted = cell[order]
    last = np.ones(cell_sorted.size, bool)
    last[:-1] = cell_sorted[1:] != cell_sorted[:-1]
    winners = src[order[last]]
    winner_cells = cell_sorted[last]

    n_cells = grid.shape[0] * grid.shape[1]
    out = {}
    for name, arr in {**values, "height": height}.items():
        arr = np.asarray(arr, float).ravel()
        flat = np.full(n_cells, np.nan)
        flat[winner_cells] = arr[winners]
        out[name] = flat.reshape(grid.shape)
    out["count"] = np.bincount(cell, minlength=n_cells).reshape(grid.shape)
    return out


def idw_fill(field, observed, fill_radius=1, power=2.0):
    """Fill unobserved cells from observed neighbours within ``fill_radius`` cells.

    NaN in an *observed* cell is a real value, not a gap: for example, cloud-top
    height over clear sky. Such cells are never overwritten. A filled cell
    becomes NaN as well if most of its neighbour weight comes from NaN cells,
    so clear-sky gaps stay clear.

    Returns the filled field and a boolean mask of the cells that were filled.
    Cells with no observed neighbour in range stay NaN and are not in the mask.
    """
    if fill_radius < 1:
        return field.copy(), np.zeros(field.shape, bool)
    r = int(fill_radius)
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    dist = np.hypot(yy, xx)
    kernel = np.where(dist > 0, 1.0 / np.where(dist > 0, dist, 1.0) ** power, 0.0)

    finite = observed & np.isfinite(field)
    num = ndimage.convolve(np.where(finite, field, 0.0), kernel, mode="constant")
    w_finite = ndimage.convolve(finite.astype(float), kernel, mode="constant")
    w_observed = ndimage.convolve(observed.astype(float), kernel, mode="constant")

    filled_mask = ~observed & (w_observed > 0)
    use = filled_mask & (w_finite >= 0.5 * w_observed)
    out = field.copy()
    out[use] = num[use] / w_finite[use]
    return out, filled_mask


def resample(grid: Grid, lat, lon, height, values: dict, fill_radius=1, power=2.0,
             attrs=None) -> xr.Dataset:
    """Bucket-resample pixels onto ``grid`` and fill small gaps.

    Parameters
    ----------
    grid, lat, lon, height, values
        See :func:`bucket_max_height`.
    fill_radius : int, optional
        Largest gap distance (in cells) to interpolate across. 0 disables filling.
    power : float, optional
        Inverse-distance weighting exponent.
    attrs : dict, optional
        Global attributes for the output dataset.

    Returns
    -------
    xarray.Dataset
        One variable per entry in ``values``, plus ``height``, ``count`` and
        ``fill_flag`` (0 observed, 1 interpolated, 2 empty), on ``lat``/``lon``
        cell-centre coordinates.
    """
    gridded = bucket_max_height(grid, lat, lon, height, values)
    count = gridded.pop("count")
    observed = count > 0

    filled_any = np.zeros(grid.shape, bool)
    for name in gridded:
        gridded[name], filled = idw_fill(gridded[name], observed, fill_radius, power)
        filled_any |= filled

    fill_flag = np.full(grid.shape, EMPTY, np.uint8)
    fill_flag[filled_any] = INTERPOLATED
    fill_flag[observed] = OBSERVED

    dims = ("lat", "lon")
    ds = xr.Dataset(
        {name: (dims, arr) for name, arr in gridded.items()},
        coords={"lat": grid.lats, "lon": grid.lons},
        attrs=dict(attrs or {}),
    )
    ds["count"] = (dims, count.astype(np.int32))
    ds["fill_flag"] = (dims, fill_flag)
    ds["fill_flag"].attrs = {
        "flag_values": [OBSERVED, INTERPOLATED, EMPTY],
        "flag_meanings": "observed interpolated empty",
    }
    ds["height"].attrs = {"units": "m", "long_name": "height used for occlusion (highest pixel in cell)"}
    ds["lat"].attrs = {"units": "degrees_north", "standard_name": "latitude"}
    ds["lon"].attrs = {"units": "degrees_east", "standard_name": "longitude"}
    ds.attrs.setdefault("grid_resolution_deg", grid.res)
    return ds
