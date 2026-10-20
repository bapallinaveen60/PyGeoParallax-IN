"""End-to-end scene processing: parallax correction followed by regridding."""

from __future__ import annotations

import numpy as np
import xarray as xr

from . import __version__
from .geometry.constants import SATELLITE_LONGITUDES
from .geometry.parallax import parallax_correct, parallax_correct_terrain, parallax_shift
from .resample.bucket import resample
from .resample.grid import SOUTH_ASIA_0P04, Grid


def correct_scene(lat, lon, channels: dict, cth, sat_lon=SATELLITE_LONGITUDES["INSAT-3DR"],
                  grid: Grid = SOUTH_ASIA_0P04, surface_height=None, correct=True,
                  fill_radius=1, terrain_iterations=3) -> xr.Dataset:
    """Parallax-correct one satellite scene and put it on a regular grid.

    Parameters
    ----------
    lat, lon : array_like
        Navigated (apparent) pixel positions [degrees], same shape as the channels.
    channels : dict of str -> array_like
        Imager channels to carry along, e.g. ``{"TIR1": bt_10p8, "WV": bt_6p7}``.
    cth : array_like
        Cloud-top height above the ellipsoid [m]. NaN means clear sky (or
        unknown; fill these with the ERA5 fallback before calling).
    sat_lon : float, optional
        Sub-satellite longitude [degrees east]. Defaults to INSAT-3DR.
    grid : Grid, optional
        Target grid. Defaults to the project's 0.04 degree South Asia grid.
    surface_height : callable, optional
        ``surface_height(lat, lon) -> m`` (e.g. an SRTM interpolator). If given,
        clouds are clamped to the ground and clear-sky terrain parallax is
        corrected. Otherwise the ground is taken as the ellipsoid.
    correct : bool, optional
        If False, regrid at the apparent positions without correction. Use
        this to produce the uncorrected dataset on exactly the same grid
        (Model A in the U-Net comparison).
    fill_radius : int, optional
        Largest gap (in cells) to interpolate across; see :func:`resample`.
    terrain_iterations : int, optional
        Fixed-point iterations for the terrain height lookup.

    Returns
    -------
    xarray.Dataset
        The gridded channels, ``cth``, ``height``, ``count``, ``fill_flag``
        and, when ``correct`` is True, ``shift_km`` (how far each winning
        pixel moved).
    """
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    cth = np.asarray(cth, float)
    values = {name: np.asarray(arr, float) for name, arr in channels.items()}
    values["cth"] = cth

    if surface_height is not None:
        lat_c, lon_c, height = parallax_correct_terrain(
            lat, lon, cth, sat_lon, surface_height, iterations=terrain_iterations
        )
    else:
        height = np.where(np.isfinite(cth), cth, 0.0)
        lat_c, lon_c = parallax_correct(lat, lon, height, sat_lon)

    if correct:
        dist, _ = parallax_shift(lat, lon, lat_c, lon_c)
        values["shift_km"] = dist / 1000.0
    else:
        lat_c, lon_c = lat, lon

    attrs = {
        "title": "PyGeoParallax-IN gridded scene",
        "software": f"pygeoparallax {__version__}",
        "sub_satellite_longitude": float(sat_lon),
        "parallax_corrected": int(bool(correct)),
        "terrain_corrected": int(bool(correct and surface_height is not None)),
    }
    ds = resample(grid, lat_c, lon_c, height, values, fill_radius=fill_radius, attrs=attrs)
    ds["cth"].attrs = {"units": "m", "long_name": "cloud-top height"}
    if correct:
        ds["shift_km"].attrs = {"units": "km", "long_name": "parallax displacement of the pixel"}
    return ds
