"""Build the paired uncorrected / parallax-corrected dataset (Model A / Model B inputs).

For every INSAT-3DR L1C file in ``--input`` (searched recursively, each file
once), writes two NetCDF files on the same grid:

- ``<out>/uncorrected/<scene>.nc``: pixels at their navigated positions (Model A);
- ``<out>/corrected/<scene>.nc``: pixels moved to the true cloud-top position (Model B).

Both use the same navigation correction, cloud-top heights and resampling, so
they differ only where clouds were moved; clear cells are identical. Each file
holds the channels, ``cth``, ``fill_flag`` (0 observed, 1 interpolated,
2 empty) and, in the corrected file, ``shift_km``. A manifest CSV lists every
scene with its cloud fraction, shift and fill statistics.

Processing per scene:

1. Read the channels over the grid, adding the navigation correction (default:
   the pooled monsoon value, -0.5 km E / +2.5 km N; or a JSON from
   ``pygeoparallax navigation``; or none).
2. Cloud-top height from TIR1 BT: AFGL tropical profile, or ERA5 profiles
   with ``--era5`` (a file or folder of ``era5_pl_*.nc``; the hour nearest the
   scan is used). Cloud mask from ISRO's clear-sky BT when a matching L2B CTP
   file is next to the L1C, else BT < 270 K.
3. Correct (terrain-aware with ``--dem``) and resample onto the grid.

Scenes whose two output files exist are skipped, so an interrupted run resumes.

Usage:
    python scripts/build_paired_dataset.py --input <L1C folder> --out 04_corrected_output/paired \
        [--channels TIR1 TIR2 WV MIR VIS] [--grid 0 40 60 100 0.04] [--dem 02_standardized_grid/srtm_0p01deg.nc] [-j 4]
"""

from __future__ import annotations

import argparse
import multiprocessing
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from pygeoparallax import __version__, correct_scene
from pygeoparallax.cloudheight import TROPICAL, cloud_top_height, cloud_top_height_profiles
from pygeoparallax.ingest import read_era5_profiles, read_insat_csbt, read_insat_l1c
from pygeoparallax.navigation import NavigationCorrection
from pygeoparallax.resample import EMPTY, INTERPOLATED, OBSERVED, Grid, sample_nearest
from pygeoparallax.terrain import surface_height_from_dataset

POOLED_MONSOON_NAV = (-0.5, 2.5)  # km east, km north (validation_summary.md, "Navigation near the storms")


def scan_time(name):
    return datetime.strptime(name[6:20], "%d%b%Y_%H%M")


def find_era5(era5, when):
    """ERA5 file nearest in time to ``when`` from a file or a folder of era5_pl_YYYYMMDDHH.nc."""
    p = Path(era5)
    if p.is_file():
        return p
    files = sorted(p.rglob("era5_pl_*.nc"))
    if not files:
        raise FileNotFoundError(f"no era5_pl_*.nc under {p}")
    stamps = [datetime.strptime(f.stem[8:18], "%Y%m%d%H") for f in files]
    best = int(np.argmin([abs((s - when).total_seconds()) for s in stamps]))
    if abs((stamps[best] - when).total_seconds()) > 3 * 3600:
        raise FileNotFoundError(f"no ERA5 file within 3 h of {when:%Y-%m-%d %H:%M}")
    return files[best]


def process(path, out, channels, grid, nav, era5, dem):
    t0 = time.perf_counter()
    path = Path(path)
    scene = path.name[6:20]
    bbox = (grid.lat_min, grid.lat_max, grid.lon_min, grid.lon_max)
    if nav == "pooled":
        offset = POOLED_MONSOON_NAV
    elif nav in (None, "none"):
        offset = None
    else:
        offset = NavigationCorrection.from_json(nav)
    ds = read_insat_l1c(path, channels=tuple(dict.fromkeys(("TIR1", *channels))), bbox=bbox, position_offset_km=offset)
    lat, lon, bt = ds["lat"].values, ds["lon"].values, ds["TIR1"].values

    ctp = path.with_name(path.name.replace("_L1C_SGP_", "_L2B_CTP_"))
    clear_bt = None
    if ctp.exists():
        csbt = read_insat_csbt(ctp)
        clear_bt = sample_nearest(csbt["lat"].values, csbt["lon"].values, csbt["clear_sky_bt"].values, lat, lon, 40.0)
    if era5:
        era5_file = find_era5(era5, scan_time(path.name))
        cth = cloud_top_height_profiles(bt, lat, lon, read_era5_profiles(era5_file), clear_bt)
        profile = f"ERA5 ({era5_file.name})"
    else:
        cth = cloud_top_height(bt, clear_bt, TROPICAL)
        profile = "AFGL tropical"
    ground = surface_height_from_dataset(dem) if dem else None

    values = {c: ds[c].values for c in channels}
    attrs = {"scene": scene, "source_file": path.name, "pygeoparallax_version": __version__,
             "navigation_correction": str(nav), "cloud_top_height_profile": profile,
             "cloud_mask": "ISRO clear-sky BT - 8 K" if clear_bt is not None else "BT < 270 K",
             "dem": str(dem) if dem else "none"}
    stats = {"scene": scene, "file": str(path)}
    for kind, correct in (("uncorrected", False), ("corrected", True)):
        grd = correct_scene(lat, lon, values, cth, grid=grid, surface_height=ground if correct else None, correct=correct)
        grd.attrs.update(attrs)
        grd.attrs["model"] = "B (parallax-corrected)" if correct else "A (uncorrected)"
        for c in channels:
            grd[c].attrs.update({k: v for k, v in ds[c].attrs.items() if k in ("units", "long_name", "standard_name")})
        target = Path(out) / kind / f"{scene}.nc"
        target.parent.mkdir(parents=True, exist_ok=True)
        enc = {v: {"zlib": True, "complevel": 4} for v in grd.data_vars}
        grd.to_netcdf(target.with_suffix(".part"), encoding=enc)
        target.with_suffix(".part").replace(target)
        if correct:
            flag = grd["fill_flag"].values
            cloudy = np.isfinite(grd["cth"].values)
            stats.update({
                "cloud_fraction": float(np.isfinite(cth).sum() / max(np.isfinite(bt).sum(), 1)),
                "frac_missing": float(1 - np.isfinite(bt).mean()),
                "shift_median_km": float(np.nanmedian(grd["shift_km"].values[cloudy])) if cloudy.any() else np.nan,
                "frac_observed": float((flag == OBSERVED).mean()),
                "frac_interpolated": float((flag == INTERPOLATED).mean()),
                "frac_empty": float((flag == EMPTY).mean()),
            })
    stats.update({"cloud_mask": attrs["cloud_mask"], "profile": profile, "seconds": time.perf_counter() - t0})
    return stats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--input", required=True, help="folder searched recursively for 3RIMG_*_L1C_SGP_*.h5")
    ap.add_argument("--out", default="04_corrected_output/paired")
    ap.add_argument("--channels", nargs="+", default=["TIR1", "TIR2", "WV", "MIR", "VIS"])
    ap.add_argument("--grid", nargs=5, type=float, default=[0.0, 40.0, 60.0, 100.0, 0.04],
                    metavar=("LAT_MIN", "LAT_MAX", "LON_MIN", "LON_MAX", "RES"))
    ap.add_argument("--nav", default="pooled",
                    help="'pooled' (monsoon -0.5 km E, +2.5 km N), 'none', or a navigation JSON")
    ap.add_argument("--era5", help="ERA5 file or folder of era5_pl_*.nc (default: AFGL standard atmosphere)")
    ap.add_argument("--dem", help="DEM NetCDF for terrain-aware correction (corrected files only)")
    ap.add_argument("--list", help="CSV with an l1c_file column: process only these files")
    ap.add_argument("-j", "--workers", type=int, default=1)
    args = ap.parse_args(argv)

    files = {}
    for p in sorted(Path(args.input).rglob("3RIMG_*_L1C_SGP_V01R00.h5")):
        files.setdefault(p.name, p)
    if args.list:
        wanted = set(pd.read_csv(args.list)["l1c_file"])
        missing = sorted(wanted - set(files))
        if missing:
            print(f"{len(missing)} listed files not found, e.g. {missing[:3]}", file=sys.stderr)
        files = {k: v for k, v in files.items() if k in wanted}
    out = Path(args.out)
    todo = [p for p in files.values()
            if not all((out / k / f"{p.name[6:20]}.nc").exists() for k in ("uncorrected", "corrected"))]
    print(f"{len(files)} scenes, {len(files) - len(todo)} already done, {len(todo)} to process", flush=True)
    grid = Grid(*args.grid[:4], res=args.grid[4])
    job = dict(out=str(out), channels=args.channels, grid=grid, nav=args.nav, era5=args.era5, dem=args.dem)

    manifest = out / "manifest.csv"
    rows = pd.read_csv(manifest).to_dict("records") if manifest.exists() else []

    def record(stats):
        rows[:] = [r for r in rows if r["scene"] != stats["scene"]] + [stats]
        pd.DataFrame(rows).sort_values("scene").to_csv(manifest, index=False)

    failed = []
    if args.workers > 1:
        # "spawn", not fork: forking after Numba's parallel kernels have started can deadlock.
        ctx = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=args.workers, mp_context=ctx) as pool:
            futures = {pool.submit(process, p, **job): p for p in todo}
            for i, fut in enumerate(as_completed(futures), 1):
                p = futures[fut]
                try:
                    record(fut.result())
                    print(f"[{i}/{len(todo)}] {p.name[6:20]} ok", flush=True)
                except Exception as exc:
                    failed.append((p.name, exc))
                    print(f"[{i}/{len(todo)}] {p.name[6:20]} FAILED: {exc}", flush=True)
    else:
        for i, p in enumerate(todo, 1):
            try:
                record(process(p, **job))
                print(f"[{i}/{len(todo)}] {p.name[6:20]} ok", flush=True)
            except Exception as exc:
                failed.append((p.name, exc))
                print(f"[{i}/{len(todo)}] {p.name[6:20]} FAILED: {exc}", flush=True)
    print(f"done: {len(rows)} scenes in {manifest}" + (f"; {len(failed)} failed" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
