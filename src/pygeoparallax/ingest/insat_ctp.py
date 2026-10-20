"""Reader for the INSAT-3DR Imager cloud-top product (``3RIMG_*_L2B_CTP``).

The product has two grids, both on the full disk in satellite projection:

* **Cloud grid** (~37 km boxes over India): cloud-top pressure ``CTP``
  [hPa, 25 hPa steps], cloud-top temperature ``CTT`` [K] and effective
  emissivity. It contains **no cloud-top height**.
* **Clear-sky grid**: clear-sky brightness temperatures (``CSBT_*``),
  useful as a cloud-mask reference.

The file's ``Nominal_Central_Point`` attribute says 82E. That is wrong for
INSAT-3DR: the latitude/longitude arrays and the ``SAT_ZEN`` minimum are
centred on ~74E, consistent with the L1C files. Use the arrays, not that
attribute.
"""

from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import xarray as xr

from .insat import _attr, _parse_time


def _scaled(dset):
    raw = dset[...]
    if raw.ndim == 3:
        raw = raw[0]
    data = raw.astype(np.float64)
    fill = _attr(dset, "_FillValue")
    bad = raw == fill if fill is not None else np.zeros(raw.shape, bool)
    data = data * float(_attr(dset, "scale_factor", 1.0)) + float(_attr(dset, "add_offset", 0.0))
    data[bad] = np.nan
    return data


def _times(f):
    start = _parse_time(_attr(f, "Acquisition_Start_Time"))
    end = _parse_time(_attr(f, "Acquisition_End_Time"))
    return start, end


def read_insat_ctp(path) -> xr.Dataset:
    """Cloud-top pressure, temperature and emissivity on the product's cloud grid.

    Returns a Dataset with dims ``(row, col)``, 2-D ``lat``/``lon`` (NaN off
    the disk), and ``ctp`` [hPa], ``ctt`` [K], ``emissivity``.
    """
    path = Path(path)
    with h5py.File(path, "r") as f:
        start, end = _times(f)
        ds = xr.Dataset(
            {
                "ctp": (("row", "col"), _scaled(f["CTP"]).astype(np.float32), {"units": "hPa", "long_name": "cloud-top pressure"}),
                "ctt": (("row", "col"), _scaled(f["CTT"]).astype(np.float32), {"units": "K", "long_name": "cloud-top temperature"}),
                "emissivity": (("row", "col"), _scaled(f["EFF_EMISS"]).astype(np.float32), {"long_name": "effective cloud emissivity"}),
            },
            coords={"lat": (("row", "col"), _scaled(f["Latitude"])), "lon": (("row", "col"), _scaled(f["Longitude"]))},
            attrs={"source_file": path.name, "start_time": str(start), "end_time": str(end),
                   "satellite": _attr(f, "Satellite_Name")},
        )
    return ds


def read_insat_csbt(path, channel="TIR1") -> xr.Dataset:
    """Clear-sky brightness temperature for one channel on the product's clear-sky grid.

    Returns ``clear_sky_bt`` [K] with 2-D ``lat``/``lon`` and the
    ``clear_fraction`` of each box.
    """
    path = Path(path)
    with h5py.File(path, "r") as f:
        start, end = _times(f)
        ds = xr.Dataset(
            {
                "clear_sky_bt": (("row", "col"), _scaled(f[f"CSBT_{channel}"]).astype(np.float32), {"units": "K"}),
                "clear_fraction": (("row", "col"), _scaled(f[f"CLRFR_{channel}"]).astype(np.float32)),
            },
            coords={"lat": (("row", "col"), _scaled(f["CSBT_Latitude"])), "lon": (("row", "col"), _scaled(f["CSBT_Longitude"]))},
            attrs={"source_file": path.name, "channel": channel, "start_time": str(start), "end_time": str(end)},
        )
    return ds
