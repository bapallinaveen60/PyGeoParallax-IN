"""Command-line interface: ``pygeoparallax correct`` and ``pygeoparallax batch``.

Both commands read *standard scene* NetCDF files, which the ingest step
writes. A standard scene has:

* 2-D ``lat`` and ``lon`` variables [degrees]: the navigated pixel positions
* a 2-D ``cth`` variable: cloud-top height above the ellipsoid [m], NaN for
  clear sky
* any number of 2-D channel variables with the same shape (e.g. ``TIR1``)
* optionally, a ``sub_satellite_longitude`` global attribute
"""

from __future__ import annotations

import argparse
import glob
import multiprocessing
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import xarray as xr

from . import __version__
from .geometry.constants import SATELLITE_LONGITUDES
from .pipeline import correct_scene
from .resample.grid import SOUTH_ASIA_0P04, Grid


def _grid_from_args(args) -> Grid:
    if args.grid is None:
        return SOUTH_ASIA_0P04
    lat_min, lat_max, lon_min, lon_max, res = args.grid
    return Grid(lat_min, lat_max, lon_min, lon_max, res)


def process_file(in_path, out_path, channels=None, sat_lon=None, dem=None, dem_var="elevation",
                 correct=True, grid=SOUTH_ASIA_0P04, fill_radius=1):
    """Correct one standard-scene file and write the gridded result to ``out_path``."""
    with xr.open_dataset(in_path) as scene:
        lat = scene["lat"].values
        if channels is None:
            channels = [
                name for name, da in scene.data_vars.items()
                if name not in ("lat", "lon", "cth") and da.shape == lat.shape
            ]
        if sat_lon is None:
            sat_lon = float(scene.attrs.get("sub_satellite_longitude", SATELLITE_LONGITUDES["INSAT-3DR"]))
        surface = None
        if dem is not None:
            from .terrain import surface_height_from_dataset

            surface = surface_height_from_dataset(dem, dem_var)

        ds = correct_scene(
            lat, scene["lon"].values, {c: scene[c].values for c in channels}, scene["cth"].values,
            sat_lon=sat_lon, grid=grid, surface_height=surface, correct=correct, fill_radius=fill_radius,
        )
        for key in ("time", "start_time", "satellite"):
            if key in scene.attrs:
                ds.attrs[key] = scene.attrs[key]
        ds.attrs["source_file"] = Path(in_path).name

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    encoding = {name: {"zlib": True, "complevel": 4} for name in ds.data_vars}
    ds.to_netcdf(out_path, encoding=encoding)
    return out_path


def _common_options(p):
    p.add_argument("--channels", nargs="+", help="channel variables to carry (default: all 2-D variables)")
    p.add_argument("--sat-lon", type=float, help="sub-satellite longitude (default: file attribute or INSAT-3DR 74.0)")
    p.add_argument("--dem", help="DEM NetCDF on a regular lat/lon grid, for terrain-aware correction")
    p.add_argument("--dem-var", default="elevation", help="elevation variable in the DEM file")
    p.add_argument("--no-correction", action="store_true",
                   help="regrid without parallax correction (uncorrected baseline)")
    p.add_argument("--grid", nargs=5, type=float, metavar=("LAT_MIN", "LAT_MAX", "LON_MIN", "LON_MAX", "RES"),
                   help="target grid (default: 0-40N, 60-100E at 0.04 deg)")
    p.add_argument("--fill-radius", type=int, default=1, help="largest gap in cells to interpolate (0 = none)")


def _options(args):
    return dict(
        channels=args.channels, sat_lon=args.sat_lon, dem=args.dem, dem_var=args.dem_var,
        correct=not args.no_correction, grid=_grid_from_args(args), fill_radius=args.fill_radius,
    )


def _cmd_correct(args):
    out = process_file(args.input, args.output, **_options(args))
    print(f"wrote {out}")
    return 0


def _cmd_batch(args):
    inputs = sorted({p for pattern in args.inputs for p in glob.glob(pattern)})
    if not inputs:
        print("no input files matched", file=sys.stderr)
        return 1
    suffix = "_uncorrected.nc" if args.no_correction else "_corrected.nc"
    out_dir = Path(args.output_dir)
    jobs = {}
    for path in inputs:
        out = out_dir / (Path(path).stem + suffix)
        if out.exists() and not args.overwrite:
            print(f"skip  {out.name} (exists)")
            continue
        jobs[path] = out

    opts = _options(args)
    failures = 0
    start = time.perf_counter()
    # "spawn", not fork: forking after Numba's parallel kernels have started a
    # thread pool can crash the workers on Linux.
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=ctx) as pool:
        futures = {pool.submit(process_file, path, out, **opts): path for path, out in jobs.items()}
        for fut in as_completed(futures):
            path = futures[fut]
            try:
                print(f"done  {fut.result().name}")
            except Exception as exc:  # report and continue with the other scenes
                failures += 1
                print(f"FAIL  {Path(path).name}: {exc}", file=sys.stderr)
    print(f"{len(jobs) - failures}/{len(jobs)} scenes in {time.perf_counter() - start:.1f} s")
    return 1 if failures else 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pygeoparallax", description="Cloud parallax correction for INSAT-3DR.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("correct", help="correct one standard-scene NetCDF file")
    p.add_argument("input")
    p.add_argument("output")
    _common_options(p)
    p.set_defaults(func=_cmd_correct)

    p = sub.add_parser("batch", help="correct many files in parallel")
    p.add_argument("inputs", nargs="+", help="input files or glob patterns")
    p.add_argument("-o", "--output-dir", required=True)
    p.add_argument("-j", "--workers", type=int, default=None, help="parallel processes (default: CPU count)")
    p.add_argument("--overwrite", action="store_true", help="redo scenes whose output already exists")
    _common_options(p)
    p.set_defaults(func=_cmd_batch)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
