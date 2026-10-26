"""Reader for SRTM GeoTIFF tiles, block-averaged onto a coarse regular grid.

The imager footprint is 4 km, so the 1 arcsecond (~30 m) SRTM GL1 detail is
not needed: each tile is averaged to ``res`` degrees while it is read (GDAL
``average`` resampling on a decimated read), and the tiles are mosaicked onto
one lat/lon grid. Voids (``nodata``) are ignored in the average; cells with
no valid data are NaN, which :func:`pygeoparallax.terrain.surface_height_from_dataset`
treats as sea level.

SRTM heights are above the EGM96 geoid. Over India the geoid lies 50-105 m
below the ellipsoid; at VZA 35 deg this moves the terrain correction by under
75 m, so heights are used as they are.
"""

from __future__ import annotations

import glob
import warnings
from pathlib import Path

import numpy as np
import xarray as xr


def read_srtm(paths, bbox=None, res=0.01, band_rows=20) -> xr.Dataset:
    """Mosaic SRTM GeoTIFF tiles onto a regular grid, block-averaged to ``res`` degrees.

    Parameters
    ----------
    paths : str, Path or sequence
        GeoTIFF files, a glob pattern, or a folder (all ``*.tif`` in it).
    bbox : (lat_min, lat_max, lon_min, lon_max), optional
        Output extent. Defaults to the union of the tiles, rounded out to ``res``.
    res : float, optional
        Output grid spacing [degrees]. Must be a multiple of the tile pixel size.
    band_rows : int, optional
        Output rows read at a time. A part of a tile that cannot be read is
        left as no data, with a warning, instead of failing the whole mosaic.

    Returns
    -------
    xarray.Dataset
        ``elevation`` [m above the EGM96 geoid] on increasing ``lat``/``lon``
        cell centres; NaN where no tile has valid data.
    """
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.errors import RasterioIOError
    from rasterio.windows import Window

    files = _expand(paths)
    if not files:
        raise FileNotFoundError(f"no GeoTIFF files in {paths!r}")
    with rasterio.open(files[0]) as src:
        pixel = src.res[0]
    factor = int(round(res / pixel))
    if factor < 1 or abs(factor * pixel - res) > 1e-9:
        raise ValueError(f"res={res} is not a multiple of the tile pixel size {pixel}")

    if bbox is None:
        bounds = []
        for f in files:
            with rasterio.open(f) as src:
                bounds.append(src.bounds)
        bbox = (min(b.bottom for b in bounds), max(b.top for b in bounds),
                min(b.left for b in bounds), max(b.right for b in bounds))
    lat0 = np.floor(bbox[0] / res) * res
    lon0 = np.floor(bbox[2] / res) * res
    n_lat = int(round((np.ceil(bbox[1] / res) * res - lat0) / res))
    n_lon = int(round((np.ceil(bbox[3] / res) * res - lon0) / res))
    total = np.zeros((n_lat, n_lon))
    weight = np.zeros((n_lat, n_lon))

    for f in files:
        with rasterio.open(f) as src:
            b = src.bounds
            if b.top <= lat0 or b.bottom >= lat0 + n_lat * res or b.right <= lon0 or b.left >= lon0 + n_lon * res:
                continue
            rows, cols = src.height // factor, src.width // factor
            elev = np.full((rows, cols), np.nan)
            bad = 0
            # Read in bands so a damaged part of a tile (e.g. a truncated download) costs only that band.
            for r in range(0, rows, band_rows):
                n = min(band_rows, rows - r)
                window = Window(0, r * factor, cols * factor, n * factor)
                try:
                    data = src.read(1, window=window, out_shape=(n, cols), resampling=Resampling.average, masked=True)
                except RasterioIOError:
                    bad += n
                    continue
                elev[r:r + n] = np.where(np.ma.getmaskarray(data), np.nan, np.ma.getdata(data).astype(float))
            if bad:
                warnings.warn(f"{Path(f).name}: {bad} of {rows} rows unreadable (damaged file?), left as no data")
            # Output cell of each block, from its centre (tile edges are offset by half a pixel).
            top = b.top - 0.5 * pixel * factor
            r0 = int(round((top - lat0) / res - 0.5))
            c0 = int(round((b.left + 0.5 * pixel * factor - lon0) / res - 0.5))
            r_idx = r0 - np.arange(rows)  # tile rows run north to south
            c_idx = c0 + np.arange(cols)
            rk = (r_idx >= 0) & (r_idx < n_lat)
            ck = (c_idx >= 0) & (c_idx < n_lon)
            block = elev[np.ix_(rk, ck)]
            ok = np.isfinite(block)
            sub = np.ix_(r_idx[rk], c_idx[ck])
            total[sub] += np.where(ok, block, 0.0)
            weight[sub] += ok

    with np.errstate(invalid="ignore"):
        elevation = np.where(weight > 0, total / weight, np.nan).astype(np.float32)
    return xr.Dataset(
        {"elevation": (("lat", "lon"), elevation,
                       {"units": "m", "long_name": "SRTM elevation above the EGM96 geoid"})},
        coords={"lat": lat0 + (np.arange(n_lat) + 0.5) * res, "lon": lon0 + (np.arange(n_lon) + 0.5) * res},
        attrs={"source": "SRTM", "resolution_deg": res, "tiles": len(files)},
    )


def _expand(paths):
    if isinstance(paths, (str, Path)):
        p = Path(paths)
        if p.is_dir():
            return sorted(str(f) for f in p.glob("*.tif"))
        return sorted(glob.glob(str(paths)))
    return [str(p) for p in paths]
