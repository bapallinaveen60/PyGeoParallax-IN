"""Regional breakdown of gridded results (Western Ghats, Himalayas, and so on)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

#: Approximate study regions as (lat_min, lat_max, lon_min, lon_max). These
#: are deliberately simple boxes. Refine them (e.g. intersect with an
#: elevation threshold or a shapefile) before reporting final numbers.
REGIONS = {
    "western_ghats": (8.0, 21.0, 73.0, 77.5),
    "himalayas": (28.0, 36.0, 73.0, 89.0),
    "northeast": (22.0, 29.0, 89.0, 97.5),
    "central_india": (18.0, 26.0, 77.5, 85.0),
}


def region_mask(lat, lon, box):
    """Boolean mask of the cells of a ``lat``/``lon`` grid inside ``box``."""
    lat_min, lat_max, lon_min, lon_max = box
    glat, glon = np.meshgrid(np.asarray(lat), np.asarray(lon), indexing="ij")
    return (glat >= lat_min) & (glat < lat_max) & (glon >= lon_min) & (glon < lon_max)


def regional_stats(ds: xr.Dataset, variable: str, regions=None, mask=None) -> pd.DataFrame:
    """Summary statistics of ``ds[variable]`` for each region.

    Parameters
    ----------
    ds : xarray.Dataset
        A gridded output with ``lat``/``lon`` coordinates (e.g. from ``correct_scene``).
    variable : str
        The variable to summarise, e.g. ``"shift_km"``.
    regions : dict, optional
        Name -> box. Defaults to :data:`REGIONS`.
    mask : ndarray of bool, optional
        Extra cell filter, e.g. ``ds.fill_flag == 0`` to use observed cells only.

    Returns
    -------
    pandas.DataFrame
        One row per region: ``n``, ``mean``, ``std``, ``median``, ``p90``, ``max``.
    """
    regions = REGIONS if regions is None else regions
    data = ds[variable].values
    rows = []
    for name, box in regions.items():
        sel = region_mask(ds["lat"].values, ds["lon"].values, box) & np.isfinite(data)
        if mask is not None:
            sel &= np.asarray(mask, bool)
        v = data[sel]
        rows.append({
            "region": name,
            "n": int(v.size),
            "mean": float(v.mean()) if v.size else np.nan,
            "std": float(v.std()) if v.size else np.nan,
            "median": float(np.median(v)) if v.size else np.nan,
            "p90": float(np.percentile(v, 90)) if v.size else np.nan,
            "max": float(v.max()) if v.size else np.nan,
        })
    return pd.DataFrame(rows).set_index("region")
