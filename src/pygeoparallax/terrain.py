"""Surface-height lookup from a gridded DEM, for terrain-aware correction."""

from __future__ import annotations

import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator

_LAT_NAMES = ("lat", "latitude", "y")
_LON_NAMES = ("lon", "longitude", "x")


def _coord(ds, names):
    for name in names:
        if name in ds.coords or name in ds.variables:
            return name
    raise KeyError(f"none of {names} found in DEM dataset")


def surface_height_from_dataset(dem, var="elevation"):
    """Build a ``surface_height(lat, lon)`` function from a regular lat/lon DEM.

    Parameters
    ----------
    dem : str, path or xarray.Dataset
        A DEM on a regular lat/lon grid (e.g. SRTM regridded to NetCDF), or a
        path to one.
    var : str, optional
        Name of the elevation variable [m].

    Returns
    -------
    callable
        ``f(lat, lon) -> height [m]``, bilinear. Points outside the DEM and
        NaN voids (open sea) are 0 m.
    """
    ds = xr.open_dataset(dem) if not isinstance(dem, xr.Dataset) else dem
    lat_name = _coord(ds, _LAT_NAMES)
    lon_name = _coord(ds, _LON_NAMES)
    da = ds[var].transpose(lat_name, lon_name).sortby(lat_name).sortby(lon_name)
    values = np.nan_to_num(da.values.astype(float), nan=0.0)
    interp = RegularGridInterpolator(
        (da[lat_name].values, da[lon_name].values), values,
        method="linear", bounds_error=False, fill_value=0.0,
    )

    def surface_height(lat, lon):
        lat = np.asarray(lat, float)
        lon = np.asarray(lon, float)
        pts = np.stack([lat.ravel(), lon.ravel()], axis=-1)
        out = interp(np.nan_to_num(pts, nan=-9999.0))
        return out.reshape(lat.shape)

    return surface_height
