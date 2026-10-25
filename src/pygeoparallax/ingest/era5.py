"""Reader for ERA5 pressure-level temperature and geopotential (CDS NetCDF).

Files come from ``scripts/download_era5.py`` (``reanalysis-era5-pressure-levels``,
variables ``temperature`` and ``geopotential``). The reader returns profiles
ordered from the surface upwards, with geopotential converted to geometric
height above mean sea level, ready for
:func:`pygeoparallax.cloudheight.cloud_top_height_profiles`.
"""

from __future__ import annotations

import numpy as np
import xarray as xr

G0 = 9.80665  # standard gravity [m s-2], the WMO geopotential reference
EARTH_RADIUS = 6371008.8  # mean Earth radius [m]


def geometric_height(geopotential):
    """Geometric height [m] from geopotential [m2 s-2] (spherical Earth, constant g0).

    The difference from geopotential height is about 45 m at 17 km.
    """
    zg = np.asarray(geopotential, float) / G0
    return EARTH_RADIUS * zg / (EARTH_RADIUS - zg)


def read_era5_profiles(path, time=None) -> xr.Dataset:
    """Read an ERA5 pressure-level file as profiles on a lat/lon grid.

    Parameters
    ----------
    path : str or Path
        NetCDF from the CDS with ``t`` and ``z`` on ``pressure_level``.
    time : datetime-like, optional
        Time to select (nearest). Defaults to the first time in the file.

    Returns
    -------
    xarray.Dataset
        ``temperature`` [K] and ``height`` [m above mean sea level] on
        ``(level, lat, lon)``, with ``level`` the pressure [hPa] in decreasing
        order (surface first) and ``lat`` increasing.
    """
    with xr.open_dataset(path) as raw:
        ds = raw.load()
    tname = "valid_time" if "valid_time" in ds.dims else "time" if "time" in ds.dims else None
    if tname:
        ds = ds.sel({tname: np.datetime64(time, "ns")}, method="nearest") if time is not None else ds.isel({tname: 0})
    ds = ds.rename({"pressure_level": "level", "latitude": "lat", "longitude": "lon"})
    ds = ds.sortby("level", ascending=False).sortby("lat")
    out = xr.Dataset(
        {
            "temperature": (("level", "lat", "lon"), ds["t"].values.astype(float), {"units": "K"}),
            "height": (("level", "lat", "lon"), geometric_height(ds["z"].values),
                       {"units": "m", "long_name": "geometric height above mean sea level"}),
        },
        coords={"level": ("level", ds["level"].values, {"units": "hPa"}),
                "lat": ds["lat"].values, "lon": ds["lon"].values},
    )
    if tname:
        out.attrs["time"] = str(ds[tname].values)
    return out
