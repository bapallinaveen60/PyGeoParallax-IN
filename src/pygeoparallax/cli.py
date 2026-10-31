"""Command-line interface: ``pygeoparallax demo``, ``l1c``, ``correct``, ``batch`` and ``navigation``.

``demo`` runs a self-test on a synthetic scene with storms at known positions
(no data needed) and saves a before/after figure.

``l1c`` corrects INSAT-3DR L1C files directly: it reads the channels, derives
cloud-top height from TIR1 and writes corrected NetCDF, on a regular lat/lon
grid or on the file's own pixel grid (``--native``).

``correct`` and ``batch`` read *standard scene* NetCDF files, which the
ingest step writes. ``navigation`` measures an INSAT geolocation correction
from L1C files by coastline matching and saves it as JSON, for use with
``--nav-correction``. A standard scene has:

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
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import xarray as xr

from . import __version__
from .cloudheight import effective_height
from .geometry.constants import SATELLITE_LONGITUDES
from .pipeline import correct_native, correct_scene
from .resample.grid import SOUTH_ASIA_0P04, Grid


def _grid_from_args(args) -> Grid:
    if args.grid is None:
        return SOUTH_ASIA_0P04
    lat_min, lat_max, lon_min, lon_max, res = args.grid
    return Grid(lat_min, lat_max, lon_min, lon_max, res)


def _surface(dem, dem_var):
    if dem is None:
        return None
    from .terrain import surface_height_from_dataset

    return surface_height_from_dataset(dem, dem_var)


#: Default number of parallel processes: a full L1C sector needs about 1.5 GB per process.
DEFAULT_WORKERS = min(4, os.cpu_count() or 1)


def _height_attrs(ds, height_scale, height_offset_km):
    if height_scale != 1.0 or height_offset_km != 0.0:
        rule = f"{height_scale:g} * cloud-top height - {height_offset_km:g} km"
        ds.attrs["effective_height"] = rule
        ds["cth"].attrs["long_name"] = f"effective height used for the correction ({rule})"


def _write(ds, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    encoding = {name: {"zlib": True, "complevel": 4} for name in ds.data_vars}
    ds.to_netcdf(out_path, encoding=encoding)
    return out_path


def process_file(in_path, out_path, channels=None, sat_lon=None, dem=None, dem_var="elevation",
                 correct=True, grid=SOUTH_ASIA_0P04, fill_radius=1, nav_correction=None,
                 height_scale=1.0, height_offset_km=0.0):
    """Correct one standard-scene file and write the gridded result to ``out_path``.

    ``nav_correction`` is a JSON file from ``pygeoparallax navigation``. It is
    applied to the pixel positions before parallax correction.
    ``height_scale`` and ``height_offset_km`` turn the scene's cloud-top height
    into an effective height (:func:`pygeoparallax.cloudheight.effective_height`).
    """
    with xr.open_dataset(in_path) as scene:
        lat = scene["lat"].values
        lon = scene["lon"].values
        if nav_correction is not None:
            from .ingest.insat import shift_positions
            from .navigation import NavigationCorrection

            east, north = NavigationCorrection.from_json(nav_correction)(lat, lon)
            lat, lon = shift_positions(lat, lon, east, north)
        if channels is None:
            channels = [
                name for name, da in scene.data_vars.items()
                if name not in ("lat", "lon", "cth") and da.shape == lat.shape
            ]
        if sat_lon is None:
            sat_lon = float(scene.attrs.get("sub_satellite_longitude", SATELLITE_LONGITUDES["INSAT-3DR"]))
        cth = effective_height(scene["cth"].values, height_scale, height_offset_km * 1000.0)
        ds = correct_scene(
            lat, lon, {c: scene[c].values for c in channels}, cth,
            sat_lon=sat_lon, grid=grid, surface_height=_surface(dem, dem_var), correct=correct,
            fill_radius=fill_radius,
        )
        _height_attrs(ds, height_scale, height_offset_km)
        for c in channels:
            ds[c].attrs = dict(scene[c].attrs)
        for key in ("satellite", "sensor", "product", "start_time", "end_time", "time"):
            if key in scene.attrs:
                ds.attrs[key] = scene.attrs[key]
        ds.attrs["source_file"] = Path(in_path).name
        if nav_correction is not None:
            ds.attrs["navigation_correction"] = Path(nav_correction).name
    return _write(ds, out_path)


def process_l1c(in_path, out_path, channels=("TIR1", "TIR2", "WV", "MIR"), bbox=None, native=False,
                grid=SOUTH_ASIA_0P04, era5=None, cloud_threshold=270.0, dem=None, dem_var="elevation",
                correct=True, fill_radius=1, fill_empty=False, nav_correction=None,
                height_scale=1.0, height_offset_km=0.0):
    """Correct one INSAT-3DR L1C file and write the result to ``out_path``.

    Cloud-top height comes from TIR1: BT below ``cloud_threshold`` [K] is
    cloud, and its height is looked up in the AFGL tropical atmosphere or, with
    ``era5`` (a pressure-level NetCDF), in the ERA5 profile nearest in time.
    With ``native`` the output stays on the file's own pixel grid; otherwise it
    goes on ``grid``.
    """
    from .cloudheight import cloud_top_height, cloud_top_height_profiles
    from .ingest.insat import read_insat_l1c, shift_positions
    from .resample.native import NativeGrid

    channels = list(dict.fromkeys(channels))
    scene = read_insat_l1c(in_path, channels=list(dict.fromkeys(["TIR1", *channels])), bbox=bbox)
    lat = scene["lat"].values
    lon = scene["lon"].values
    native_grid = NativeGrid.from_2d(lat, lon) if native else None
    if nav_correction is not None:
        from .navigation import NavigationCorrection

        east, north = NavigationCorrection.from_json(nav_correction)(lat, lon)
        lat, lon = shift_positions(lat, lon, east, north)

    bt = scene["TIR1"].values
    if era5 is not None:
        from .ingest.era5 import read_era5_profiles

        profiles = read_era5_profiles(era5, time=np.datetime64(scene.attrs["time"]))
        cth = cloud_top_height_profiles(bt, lat, lon, profiles, threshold=cloud_threshold)
    else:
        cth = cloud_top_height(bt, threshold=cloud_threshold)
    cth = effective_height(cth, height_scale, height_offset_km * 1000.0)

    values = {c: scene[c].values for c in channels}
    common = dict(sat_lon=scene.attrs["sub_satellite_longitude"], surface_height=_surface(dem, dem_var),
                  correct=correct, fill_radius=fill_radius)
    if native:
        ds = correct_native(lat, lon, values, cth, grid=native_grid, fill_empty=fill_empty, **common)
    else:
        ds = correct_scene(lat, lon, values, cth, grid=grid, **common)
    for c in channels:
        ds[c].attrs = scene[c].attrs
    for key in ("satellite", "sensor", "product", "start_time", "end_time", "time"):
        ds.attrs[key] = scene.attrs[key]
    ds.attrs["source_file"] = Path(in_path).name
    ds.attrs["cloud_top_height"] = (f"TIR1 BT < {cloud_threshold:g} K, "
                                    + ("ERA5 profile" if era5 is not None else "AFGL tropical atmosphere"))
    _height_attrs(ds, height_scale, height_offset_km)
    if nav_correction is not None:
        ds.attrs["navigation_correction"] = Path(nav_correction).name
    return _write(ds, out_path)


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
    p.add_argument("--nav-correction", help="navigation correction JSON from `pygeoparallax navigation`")
    p.add_argument("--height-scale", type=float, default=1.0,
                   help="correct with height-scale * cloud-top height - height-offset (default 1)")
    p.add_argument("--height-offset", type=float, default=0.0, metavar="KM",
                   help="subtract this from the cloud-top height [km], e.g. 3 for precipitation (default 0)")


def _options(args):
    return dict(
        channels=args.channels, sat_lon=args.sat_lon, dem=args.dem, dem_var=args.dem_var,
        correct=not args.no_correction, grid=_grid_from_args(args), fill_radius=args.fill_radius,
        nav_correction=args.nav_correction, height_scale=args.height_scale, height_offset_km=args.height_offset,
    )


def _cmd_correct(args):
    try:
        out = process_file(args.input, args.output, **_options(args))
    except Exception as exc:  # a clear one-line message instead of a traceback
        print(f"error: {Path(args.input).name}: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {out}")
    return 0


def _cmd_batch(args):
    return _run_batch(args, process_file, _options(args))


def _cmd_l1c(args):
    grid = _grid_from_args(args)
    if args.bbox and args.grid is None and not args.native:
        # Without --grid, a region read with --bbox goes on a 0.04 deg grid over that region only.
        lat_min, lat_max, lon_min, lon_max = args.bbox
        grid = Grid(lat_min, lat_max, lon_min, lon_max, SOUTH_ASIA_0P04.res)
    opts = dict(
        channels=args.channels, bbox=args.bbox, native=args.native, grid=grid, era5=args.era5,
        cloud_threshold=args.cloud_threshold, dem=args.dem, dem_var=args.dem_var, correct=not args.no_correction,
        fill_radius=args.fill_radius, fill_empty=args.fill_empty, nav_correction=args.nav_correction,
        height_scale=args.height_scale, height_offset_km=args.height_offset,
    )
    return _run_batch(args, process_l1c, opts)


def _run_batch(args, func, opts):
    """Run ``func(input, output, **opts)`` for every input file, in parallel processes."""
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

    failures = 0
    start = time.perf_counter()
    # "spawn", not fork: forking after Numba's parallel kernels have started a
    # thread pool can crash the workers on Linux.
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=args.workers or DEFAULT_WORKERS, mp_context=ctx) as pool:
        futures = {pool.submit(func, path, out, **opts): path for path, out in jobs.items()}
        for fut in as_completed(futures):
            path = futures[fut]
            try:
                print(f"done  {fut.result().name}")
            except Exception as exc:  # report and continue with the other scenes
                failures += 1
                print(f"FAIL  {Path(path).name}: {exc}", file=sys.stderr)
    print(f"{len(jobs) - failures}/{len(jobs)} scenes in {time.perf_counter() - start:.1f} s")
    return 1 if failures else 0


def _cmd_navigation(args):
    from .navigation import WINDOWS, NavigationCorrection, land_fraction_interpolator, load_land, measure_scan

    inputs = sorted({p for pattern in args.inputs for p in glob.glob(pattern)})
    if not inputs:
        print("no input files matched", file=sys.stderr)
        return 1
    unknown = sorted(set(args.windows or ()) - set(WINDOWS))
    if unknown:
        print(f"unknown window(s): {', '.join(unknown)}; choose from: {', '.join(WINDOWS)}", file=sys.stderr)
        return 1
    windows = {k: v for k, v in WINDOWS.items() if not args.windows or k in args.windows}
    days = {m.group(1) for p in inputs if (m := re.search(r"_(\d{2}[A-Z]{3}\d{4})_", Path(p).name))}
    if len(days) > 1:
        print(f"warning: the scans span {len(days)} days ({', '.join(sorted(days))}); the navigation error "
              "changes from day to day, so one correction for all of them is only an average", file=sys.stderr)
    land = load_land(args.land)
    interps = {k: land_fraction_interpolator(land, b) for k, b in windows.items()}
    matches = []
    for path in inputs:
        try:
            found = measure_scan(path, land, windows, interps)
        except OSError as exc:  # e.g. a truncated download
            print(f"skip  {Path(path).name}: {exc}", file=sys.stderr)
            continue
        for m in found:
            ok = m["r_best"] >= args.min_r and not m["on_edge"]
            print(f"{m['scan']:26s} {m['window']:14s} {m['channel']:4s} E {m['east_km']:+6.1f}  N {m['north_km']:+6.1f}"
                  f"  r {m['r_zero']:.2f}->{m['r_best']:.2f}{'' if ok else '  (rejected)'}")
        matches.extend(found)
    try:
        corr = NavigationCorrection.from_matches(matches, min_r=args.min_r)
    except ValueError as exc:
        print(f"no correction: {exc}", file=sys.stderr)
        return 1
    corr.meta["matches"] = matches
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    corr.to_json(out)
    used = zip(corr.meta["windows"], corr.east_km, corr.north_km)
    print("\nwindows used: " + ", ".join(f"{w} ({e:+.1f} E, {n:+.1f} N)" for w, e, n in used))
    print(f"wrote {out}")
    return 0


def _cmd_demo(args):
    from .demo import run_demo

    return 0 if run_demo(args.output_dir, plot=not args.no_plot)["passed"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pygeoparallax", description="Cloud parallax correction for INSAT-3DR.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("demo", help="self-test on a synthetic scene (no data needed); saves a before/after figure")
    p.add_argument("-o", "--output-dir", default="pygeoparallax_demo", help="where to write the demo files")
    p.add_argument("--no-plot", action="store_true", help="skip the figure (no matplotlib needed)")
    p.set_defaults(func=_cmd_demo)

    p = sub.add_parser("l1c", help="correct INSAT-3DR L1C files (HDF5) directly")
    p.add_argument("inputs", nargs="+", help="3RIMG_*_L1C_SGP*.h5 files or glob patterns")
    p.add_argument("-o", "--output-dir", required=True)
    p.add_argument("-j", "--workers", type=int, default=None, help="parallel processes (default: 4 or the CPU count if lower; about 1.5 GB each for a full sector)")
    p.add_argument("--overwrite", action="store_true", help="redo files whose output already exists")
    p.add_argument("--channels", nargs="+", default=["TIR1", "TIR2", "WV", "MIR"],
                   help="channels to correct (default: TIR1 TIR2 WV MIR; also VIS, SWIR)")
    p.add_argument("--bbox", nargs=4, type=float, metavar=("LAT_MIN", "LAT_MAX", "LON_MIN", "LON_MAX"),
                   help="read only this region of the file")
    p.add_argument("--native", action="store_true",
                   help="keep the file's own pixel grid instead of regridding to a regular lat/lon grid")
    p.add_argument("--fill-empty", action="store_true",
                   help="with --native: fill cells no pixel reached with the nearest corrected value")
    p.add_argument("--era5", help="ERA5 pressure-level NetCDF for cloud-top height (default: AFGL tropical)")
    p.add_argument("--cloud-threshold", type=float, default=270.0, help="TIR1 BT below this is cloud [K]")
    p.add_argument("--dem", help="DEM NetCDF on a regular lat/lon grid, for terrain-aware correction")
    p.add_argument("--dem-var", default="elevation", help="elevation variable in the DEM file")
    p.add_argument("--no-correction", action="store_true",
                   help="regrid without parallax correction (uncorrected baseline)")
    p.add_argument("--grid", nargs=5, type=float, metavar=("LAT_MIN", "LAT_MAX", "LON_MIN", "LON_MAX", "RES"),
                   help="target grid without --native (default: the --bbox region at 0.04 deg, else 0-40N, 60-100E)")
    p.add_argument("--fill-radius", type=int, default=1, help="largest gap in cells to interpolate (0 = none)")
    p.add_argument("--nav-correction", help="navigation correction JSON from `pygeoparallax navigation`")
    p.add_argument("--height-scale", type=float, default=1.0,
                   help="correct with height-scale * cloud-top height - height-offset (default 1)")
    p.add_argument("--height-offset", type=float, default=0.0, metavar="KM",
                   help="subtract this from the cloud-top height [km], e.g. 3 for precipitation (default 0)")
    p.set_defaults(func=_cmd_l1c)

    p = sub.add_parser("correct", help="correct one standard-scene NetCDF file")
    p.add_argument("input")
    p.add_argument("output")
    _common_options(p)
    p.set_defaults(func=_cmd_correct)

    p = sub.add_parser("batch", help="correct many files in parallel")
    p.add_argument("inputs", nargs="+", help="input files or glob patterns")
    p.add_argument("-o", "--output-dir", required=True)
    p.add_argument("-j", "--workers", type=int, default=None, help="parallel processes (default: 4 or the CPU count if lower; about 1.5 GB each for a full sector)")
    p.add_argument("--overwrite", action="store_true", help="redo scenes whose output already exists")
    _common_options(p)
    p.set_defaults(func=_cmd_batch)

    p = sub.add_parser("navigation", help="measure an INSAT L1C geolocation correction by coastline matching")
    p.add_argument("inputs", nargs="+", help="L1C files or glob patterns (e.g. all scans of one day)")
    p.add_argument("-o", "--output", required=True, help="correction JSON to write")
    p.add_argument("--land", default="01_raw_data/natural_earth/ne_10m_land.geojson",
                   help="land polygons GeoJSON (Natural Earth 10 m land)")
    p.add_argument("--windows", nargs="+", help="coastal windows to use (default: all)")
    p.add_argument("--min-r", type=float, default=0.6, help="reject matches weaker than this")
    p.set_defaults(func=_cmd_navigation)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
