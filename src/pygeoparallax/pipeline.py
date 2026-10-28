"""End-to-end scene processing: parallax correction followed by regridding.

:func:`correct_scene` puts the corrected scene on a regular lat/lon grid;
:func:`correct_native` puts it back on the input's own pixel grid.
"""

from __future__ import annotations

import numpy as np
import xarray as xr
from scipy import ndimage

from . import __version__
from .geometry.constants import SATELLITE_LONGITUDES
from .geometry.parallax import parallax_correct, parallax_correct_terrain, parallax_shift
from .resample.bucket import EMPTY, resample
from .resample.grid import SOUTH_ASIA_0P04, Grid
from .resample.native import NativeGrid


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
    lat_c, lon_c, height, values, attrs = _prepare(lat, lon, channels, cth, sat_lon, surface_height, correct,
                                                   terrain_iterations)
    ds = resample(grid, lat_c, lon_c, height, values, fill_radius=fill_radius, attrs=attrs)
    _set_attrs(ds, correct)
    return ds


def correct_native(lat, lon, channels: dict, cth, sat_lon=SATELLITE_LONGITUDES["INSAT-3DR"],
                   grid: NativeGrid | None = None, surface_height=None, correct=True, fill_radius=1,
                   fill_empty=False, terrain_iterations=3) -> xr.Dataset:
    """Parallax-correct one scene and put it back on its own pixel grid.

    The output has the input's shape and pixel centres, so corrected and
    uncorrected scenes line up pixel for pixel (for example as inputs to a
    model trained on L1C tiles). The correction and the occlusion-aware
    resampling are the same as in :func:`correct_scene`.

    Parameters
    ----------
    lat, lon, channels, cth, sat_lon, surface_height, correct, fill_radius, terrain_iterations
        As in :func:`correct_scene`. ``lat``/``lon`` are the pixel positions
        to correct, after any navigation correction.
    grid : NativeGrid, optional
        The output grid. Defaults to the grid of ``lat``/``lon`` themselves,
        which must then be separable and regular (true of L1C files read
        without a navigation correction). Pass it explicitly when the
        positions were shifted, e.g. ``NativeGrid.from_2d(*file_lat_lon)``.
    fill_empty : bool, optional
        Fill the channels in cells that no pixel reached (``fill_flag`` 2,
        behind tall clouds or at the edges) with the nearest corrected value.
        Useful for models that need a complete image; the cells stay flagged.

    Returns
    -------
    xarray.Dataset
        Dimensions ``(y, x)`` with 2-D ``lat``/``lon`` coordinates (the pixel
        centres), the channels, ``cth``, ``height``, ``count``, ``fill_flag``
        and, when ``correct`` is True, ``shift_km``.
    """
    if grid is None:
        grid = NativeGrid.from_2d(lat, lon)
    lat_c, lon_c, height, values, attrs = _prepare(lat, lon, channels, cth, sat_lon, surface_height, correct,
                                                   terrain_iterations)
    to_index, index_grid = grid.index_space()
    rows, cols = to_index(lat_c, lon_c)
    gridded = resample(index_grid, rows, cols, height, values, fill_radius=fill_radius, attrs=attrs)

    fill_flag = gridded["fill_flag"].values
    if fill_empty:
        empty = fill_flag == EMPTY
        if empty.any() and not empty.all():
            idx = ndimage.distance_transform_edt(empty, return_distances=False, return_indices=True)
            for name in channels:
                gridded[name].values[...] = gridded[name].values[idx[0], idx[1]]
        attrs["empty_cells_filled"] = "nearest"

    lat2d, lon2d = np.meshgrid(grid.lats, grid.lons, indexing="ij")
    ds = xr.Dataset({name: (("y", "x"), da.values, da.attrs) for name, da in gridded.data_vars.items()},
                    coords={"lat": (("y", "x"), lat2d), "lon": (("y", "x"), lon2d)}, attrs=gridded.attrs)
    ds.attrs.pop("grid_resolution_deg", None)
    ds.attrs["grid"] = f"native ({grid.kind}), {grid.shape[0]} x {grid.shape[1]} pixels"
    ds["lat"].attrs = {"units": "degrees_north", "standard_name": "latitude"}
    ds["lon"].attrs = {"units": "degrees_east", "standard_name": "longitude"}
    _set_attrs(ds, correct)
    return ds


def _prepare(lat, lon, channels, cth, sat_lon, surface_height, correct, terrain_iterations):
    """Corrected positions, occlusion heights, values to grid and global attributes."""
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
    return lat_c, lon_c, height, values, attrs


def _set_attrs(ds, correct):
    ds["cth"].attrs = {"units": "m", "long_name": "cloud-top height"}
    if correct:
        ds["shift_km"].attrs = {"units": "km", "long_name": "parallax displacement of the pixel"}
