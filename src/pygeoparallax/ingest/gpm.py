"""Reader for GPM Level-2A radar products (2A.GPM.Ku and 2A.GPM.DPR, HDF5).

Only the variables needed for validation are read: positions, scan times,
precipitation type, storm-top and bright-band heights, near-surface
reflectivity and rain rate. Checked against 2A.GPM.Ku V07 files; the DPR
product has the same ``FS`` layout.
"""

from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import xarray as xr

#: Output name -> (path inside the swath group, units, long name)
VARIABLES = {
    "storm_top_height": ("PRE/heightStormTop", "m", "storm-top height (echo top)"),
    "bright_band_height": ("CSF/heightBB", "m", "bright-band height"),
    "zero_deg_height": ("VER/heightZeroDeg", "m", "0 degC isotherm height"),
    "surface_elevation": ("PRE/elevation", "m", "surface elevation"),
    "z_near_surface": ("SLV/zFactorFinalNearSurface", "dBZ", "corrected near-surface reflectivity"),
    "precip_rate": ("SLV/precipRateNearSurface", "mm h-1", "near-surface precipitation rate"),
}

#: Major precipitation types from ``CSF/typePrecip`` (value // 10_000_000).
NO_RAIN, STRATIFORM, CONVECTIVE, OTHER = 0, 1, 2, 3


def _read(group, name, sel):
    dset = group[name]
    data = dset[sel].astype(np.float32)
    fill = dset.attrs.get("_FillValue")
    if fill is not None:
        data[data == np.float32(np.asarray(fill).ravel()[0])] = np.nan
    data[data <= -1111.0] = np.nan  # -1111.1 = "not applicable" (e.g. no bright band), -9999.9 = missing
    return data


def scan_times(group, sel=slice(None)):
    """Scan times as datetime64[ms] from the ``ScanTime`` group."""
    st = group["ScanTime"]
    parts = {k: st[k][sel].astype(np.int64) for k in ("Year", "Month", "DayOfMonth", "Hour", "Minute", "Second")}
    ms = st["MilliSecond"][sel].astype(np.int64) if "MilliSecond" in st else 0
    dates = (
        (parts["Year"] - 1970).astype("datetime64[Y]")
        + (parts["Month"] - 1).astype("timedelta64[M]")
    ).astype("datetime64[D]") + (parts["DayOfMonth"] - 1).astype("timedelta64[D]")
    return (
        dates.astype("datetime64[ms]")
        + parts["Hour"].astype("timedelta64[h]")
        + parts["Minute"].astype("timedelta64[m]")
        + parts["Second"].astype("timedelta64[s]")
        + np.asarray(ms).astype("timedelta64[ms]")
    )


def read_gpm_2a(path, swath="FS", bbox=None) -> xr.Dataset:
    """Read a GPM 2A Ku or DPR file.

    Parameters
    ----------
    path : str or Path
        A ``2A.GPM.Ku.*.HDF5`` or ``2A.GPM.DPR.*.HDF5`` file.
    swath : str, optional
        Swath group (``"FS"``, the full Ku swath in V07).
    bbox : (lat_min, lat_max, lon_min, lon_max), optional
        Keep only the scans with at least one footprint inside the box.
        Footprints outside the box in those scans are kept as well.

    Returns
    -------
    xarray.Dataset
        Dimensions ``(scan, ray)``, with ``lat``/``lon``/``time`` coordinates,
        the variables in :data:`VARIABLES`, and ``precip_type`` (0 none,
        1 stratiform, 2 convective, 3 other, -1 missing).
    """
    path = Path(path)
    with h5py.File(path, "r") as f:
        g = f[swath]
        lat = _read(g, "Latitude", slice(None))
        lon = _read(g, "Longitude", slice(None))
        if bbox is not None:
            lat_min, lat_max, lon_min, lon_max = bbox
            inside = (lat >= lat_min) & (lat <= lat_max) & (lon >= lon_min) & (lon <= lon_max)
            scans = np.flatnonzero(inside.any(axis=1))
            if scans.size == 0:
                raise ValueError(f"{path.name}: no footprints inside {bbox}")
            sel = slice(int(scans[0]), int(scans[-1]) + 1)
        else:
            sel = slice(None)
        lat = lat[sel]
        lon = lon[sel]

        data_vars = {}
        for name, (src, units, long_name) in VARIABLES.items():
            if src in g:
                data_vars[name] = (("scan", "ray"), _read(g, src, sel), {"units": units, "long_name": long_name})

        raw = g["CSF/typePrecip"][sel]
        ptype = np.where(raw > 0, raw // 10_000_000, np.where(raw == -9999, -1, NO_RAIN)).astype(np.int8)
        data_vars["precip_type"] = (("scan", "ray"), ptype, {
            "flag_values": [-1, NO_RAIN, STRATIFORM, CONVECTIVE, OTHER],
            "flag_meanings": "missing no_rain stratiform convective other",
        })
        times = scan_times(g, sel)
        attrs = {
            "source_file": path.name,
            "swath": swath,
            "product": ".".join(path.name.split(".")[:3]),
        }

    ds = xr.Dataset(
        data_vars,
        coords={"lat": (("scan", "ray"), lat), "lon": (("scan", "ray"), lon), "time": ("scan", times)},
        attrs=attrs,
    )
    ds["lat"].attrs = {"units": "degrees_north", "standard_name": "latitude"}
    ds["lon"].attrs = {"units": "degrees_east", "standard_name": "longitude"}
    return ds
