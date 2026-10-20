"""Command-line interface: ``pygeoparallax correct`` and ``pygeoparallax batch``.

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
                 correct=True, grid=SOUTH_ASIA_0P04, fill_radius=1, nav_correction=None):
    """Correct one standard-scene file and write the gridded result to ``out_path``.

    ``nav_correction`` is a JSON file from ``pygeoparallax navigation``. It is
    applied to the pixel positions before parallax correction.
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
        surface = None
        if dem is not None:
            from .terrain import surface_height_from_dataset

            surface = surface_height_from_dataset(dem, dem_var)

        ds = correct_scene(
            lat, lon, {c: scene[c].values for c in channels}, scene["cth"].values,
            sat_lon=sat_lon, grid=grid, surface_height=surface, correct=correct, fill_radius=fill_radius,
        )
        for key in ("time", "start_time", "satellite"):
            if key in scene.attrs:
                ds.attrs[key] = scene.attrs[key]
        ds.attrs["source_file"] = Path(in_path).name
        if nav_correction is not None:
            ds.attrs["navigation_correction"] = Path(nav_correction).name

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
    p.add_argument("--nav-correction", help="navigation correction JSON from `pygeoparallax navigation`")


def _options(args):
    return dict(
        channels=args.channels, sat_lon=args.sat_lon, dem=args.dem, dem_var=args.dem_var,
        correct=not args.no_correction, grid=_grid_from_args(args), fill_radius=args.fill_radius,
        nav_correction=args.nav_correction,
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


def _cmd_navigation(args):
    from .navigation import WINDOWS, NavigationCorrection, land_fraction_interpolator, load_land, measure_scan

    inputs = sorted({p for pattern in args.inputs for p in glob.glob(pattern)})
    if not inputs:
        print("no input files matched", file=sys.stderr)
        return 1
    windows = {k: v for k, v in WINDOWS.items() if not args.windows or k in args.windows}
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
