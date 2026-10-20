"""Reader for INSAT-3DR / INSAT-3D Imager Level-1C sector products (``3RIMG_*_L1C_SGP``).

The L1C SGP product is already navigated and resampled by ISRO onto an
ellipsoidal Mercator grid (WGS84, ``lon_0`` from the file, true scale at the
equator, ~4 km pixels). Each channel is stored as 10-bit counts with a
1024-entry lookup table to brightness temperature (IR), albedo (VIS) or
radiance (SWIR).

Two caveats, found while checking the sample files:

* The ``Sat_Elevation``/``Sat_Azimuth`` fields disagree with an independent
  geometry calculation by about 1 degree. At the sub-satellite point they give
  an elevation above 90 degrees, which is impossible. The reader therefore does
  not load them; use :func:`pygeoparallax.geometry.satellite_view_angles`.
* The ``X``/``Y`` coordinates are taken as pixel centres. The first and last
  values coincide with the product's corner coordinates, so if ISRO intended
  them as edges, positions are off by at most half a pixel (2 km).
"""

from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import xarray as xr
from pyproj import CRS, Transformer

#: Channel name -> (count dataset, lookup-table dataset, physical quantity, units)
CHANNELS = {
    "TIR1": ("IMG_TIR1", "IMG_TIR1_TEMP", "brightness_temperature", "K"),
    "TIR2": ("IMG_TIR2", "IMG_TIR2_TEMP", "brightness_temperature", "K"),
    "WV": ("IMG_WV", "IMG_WV_TEMP", "brightness_temperature", "K"),
    "MIR": ("IMG_MIR", "IMG_MIR_TEMP", "brightness_temperature", "K"),
    "VIS": ("IMG_VIS", "IMG_VIS_ALBEDO", "albedo", "%"),
    "SWIR": ("IMG_SWIR", "IMG_SWIR_RADIANCE", "radiance", "mW.cm-2.sr-1.micron-1"),
}


def _attr(obj, name, default=None):
    if name not in obj.attrs:
        return default
    v = obj.attrs[name]
    if isinstance(v, bytes):
        return v.decode()
    if isinstance(v, np.ndarray) and v.size == 1:
        v = v.item()
        return v.decode() if isinstance(v, bytes) else v
    return v


def _parse_time(value):
    """'30-SEP-2022T03:45:32' -> numpy datetime64."""
    from datetime import datetime

    return np.datetime64(datetime.strptime(value.title(), "%d-%b-%YT%H:%M:%S"), "s")


def _mercator_transformer(proj_info) -> Transformer:
    lon_0 = float(_attr(proj_info, "longitude_of_projection_origin"))
    lat_ts = float(_attr(proj_info, "standard_parallel", 0.0))
    a = float(_attr(proj_info, "semi_major_axis", 6378137.0))
    b = float(_attr(proj_info, "semi_minor_axis", 6356752.3142))
    crs = CRS.from_proj4(f"+proj=merc +lon_0={lon_0} +lat_ts={lat_ts} +a={a} +b={b} +x_0=0 +y_0=0 +units=m")
    return Transformer.from_crs(crs, "EPSG:4326", always_xy=True)


def _index_range(coord, lo, hi):
    """Slice of the (monotonic) 1-D ``coord`` covering [lo, hi]."""
    idx = np.flatnonzero((coord >= lo) & (coord <= hi))
    if idx.size == 0:
        raise ValueError(f"bounding box [{lo}, {hi}] does not overlap the product ({coord.min()}..{coord.max()})")
    return slice(int(idx[0]), int(idx[-1]) + 1)


def read_insat_l1c(path, channels=("TIR1", "TIR2", "WV", "MIR", "VIS"), bbox=None) -> xr.Dataset:
    """Read an INSAT-3DR Imager L1C sector file.

    Parameters
    ----------
    path : str or Path
        A ``3RIMG_*_L1C_SGP_*.h5`` file.
    channels : sequence of str, optional
        Any of :data:`CHANNELS`. IR channels come out as brightness temperature
        [K], VIS as albedo [%], SWIR as radiance.
    bbox : (lat_min, lat_max, lon_min, lon_max), optional
        Read only this region. Only that part of the file is decoded, which is
        much faster than reading the whole sector.

    Returns
    -------
    xarray.Dataset
        Dimensions ``(y, x)``, with 2-D ``lat``/``lon`` coordinates, one
        variable per channel (NaN where fill), and attributes ``satellite``,
        ``sub_satellite_longitude``, ``start_time``, ``end_time`` and ``time``
        (scan midpoint).
    """
    path = Path(path)
    with h5py.File(path, "r") as f:
        x = f["X"][:]
        y = f["Y"][:]
        to_ll = _mercator_transformer(f["Projection_Information"])
        # Mercator is separable: longitude depends only on x, latitude only on y.
        lon_1d, _ = to_ll.transform(x, np.zeros_like(x))
        _, lat_1d = to_ll.transform(np.zeros_like(y), y)

        if bbox is not None:
            lat_min, lat_max, lon_min, lon_max = bbox
            rows = _index_range(lat_1d, lat_min, lat_max)
            cols = _index_range(lon_1d, lon_min, lon_max)
        else:
            rows = slice(None)
            cols = slice(None)
        lat_1d = lat_1d[rows]
        lon_1d = lon_1d[cols]

        data_vars = {}
        for name in channels:
            if name not in CHANNELS:
                raise KeyError(f"unknown channel {name!r}; choose from {sorted(CHANNELS)}")
            count_name, lut_name, quantity, units = CHANNELS[name]
            dset = f[count_name]
            counts = dset[0, rows, cols]
            lut = f[lut_name][:].astype(np.float32)
            lut_fill = _attr(f[lut_name], "_FillValue")
            if lut_fill is not None:
                lut[lut == lut_fill] = np.nan
            values = lut[np.minimum(counts, lut.size - 1)]
            fill = _attr(dset, "_FillValue")
            if fill is not None:
                values[counts == fill] = np.nan
            data_vars[name] = (("y", "x"), values, {
                "long_name": f"{name} {quantity.replace('_', ' ')}",
                "units": units,
                "central_wavelength_um": float(_attr(dset, "central_wavelength")),
            })

        start = _parse_time(_attr(f, "Acquisition_Start_Time"))
        end = _parse_time(_attr(f, "Acquisition_End_Time"))
        centre = np.atleast_1d(f.attrs["Nominal_Central_Point_Coordinates(degrees)_Latitude_Longitude"])
        attrs = {
            "satellite": _attr(f, "Satellite_Name"),
            "sensor": _attr(f, "Sensor_Name"),
            "product": _attr(f, "Unique_Id"),
            "sub_satellite_longitude": float(centre[-1]),
            "start_time": str(start),
            "end_time": str(end),
            "time": str(start + (end - start) // 2),
            "source_file": path.name,
        }

    lat2d, lon2d = np.meshgrid(lat_1d, lon_1d, indexing="ij")
    ds = xr.Dataset(data_vars, coords={"lat": (("y", "x"), lat2d), "lon": (("y", "x"), lon2d)}, attrs=attrs)
    ds["lat"].attrs = {"units": "degrees_north", "standard_name": "latitude"}
    ds["lon"].attrs = {"units": "degrees_east", "standard_name": "longitude"}
    return ds


def to_standard_scene(ds: xr.Dataset, cth=None) -> xr.Dataset:
    """Convert a :func:`read_insat_l1c` result into a *standard scene* for the CLI.

    ``cth`` is the cloud-top height [m] on the same ``(y, x)`` grid. L1C files
    contain none: pass the L2 CTH product or the ERA5 fallback. Without it,
    ``cth`` is all NaN and the correction leaves the scene unchanged.
    """
    out = ds.reset_coords(["lat", "lon"])
    out["cth"] = (("y", "x"), np.full(ds["lat"].shape, np.nan, np.float32) if cth is None
                  else np.asarray(cth, np.float32))
    out["cth"].attrs = {"units": "m", "long_name": "cloud-top height above the ellipsoid"}
    return out
