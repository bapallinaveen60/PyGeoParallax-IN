"""Benchmark the full pipeline on many INSAT-3DR L1C scenes.

For every L1C file found (each file once, however many folders hold it):

1. Read TIR1 and WV over the South Asia grid, with the monsoon navigation
   correction (pooled near-storm value, -0.5 km E / +2.5 km N).
2. Cloud-top height from TIR1 BT (AFGL tropical profile); the cloud mask uses
   ISRO's clear-sky BT when a matching L2B CTP file is present, else BT < 270 K.
3. Parallax-correct and regrid to the 0.04 deg South Asia grid, and regrid
   the same pixels uncorrected.

It records the time of each stage, peak memory, missing data (partial scans),
cloud fraction, the parallax
shift of cloudy pixels, the share of observed / interpolated / empty cells,
and how many clear cells differ between the corrected and uncorrected grids
(clear ground overwritten by a cloud moved onto it). Failures are recorded,
not raised.

Usage:
    python scripts/benchmark_scenes.py --base <folder with L1C files> [--limit N]
"""

from __future__ import annotations

import argparse
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import psutil

from pygeoparallax import correct_scene
from pygeoparallax.cloudheight import TROPICAL, cloud_top_height
from pygeoparallax.ingest import read_insat_csbt, read_insat_l1c
from pygeoparallax.resample import EMPTY, INTERPOLATED, OBSERVED, SOUTH_ASIA_0P04, sample_nearest

NAV = (-0.5, 2.5)  # km east, km north: pooled near-storm monsoon correction
GRID = SOUTH_ASIA_0P04
BBOX = (GRID.lat_min, GRID.lat_max, GRID.lon_min, GRID.lon_max)
OUT = Path("05_validation/benchmark")


def scene(path):
    proc = psutil.Process()
    rss0 = proc.memory_info().rss
    peak = rss0
    row = {"scene": path.name[6:20]}
    t = time.perf_counter()
    ds = read_insat_l1c(path, channels=("TIR1", "WV"), bbox=BBOX, position_offset_km=NAV)
    lat, lon, bt = ds["lat"].values, ds["lon"].values, ds["TIR1"].values
    row["t_read_s"] = time.perf_counter() - t
    peak = max(peak, proc.memory_info().rss)

    t = time.perf_counter()
    ctp = path.with_name(path.name.replace("_L1C_SGP_", "_L2B_CTP_"))
    clear_bt = None
    if ctp.exists():
        csbt = read_insat_csbt(ctp)
        clear_bt = sample_nearest(csbt["lat"].values, csbt["lon"].values, csbt["clear_sky_bt"].values, lat, lon, 40.0)
    cth = cloud_top_height(bt, clear_bt, TROPICAL)
    row["t_height_s"] = time.perf_counter() - t
    row["cloud_mask"] = "csbt" if clear_bt is not None else "270K"

    channels = {"TIR1": bt, "WV": ds["WV"].values}
    t = time.perf_counter()
    cor = correct_scene(lat, lon, channels, cth, grid=GRID)
    row["t_correct_s"] = time.perf_counter() - t
    peak = max(peak, proc.memory_info().rss)
    t = time.perf_counter()
    raw = correct_scene(lat, lon, channels, cth, grid=GRID, correct=False)
    row["t_uncorrected_s"] = time.perf_counter() - t
    peak = max(peak, proc.memory_info().rss)

    valid = np.isfinite(bt)
    cloudy = np.isfinite(cth)
    shift = cor["shift_km"].values
    cloudy_cells = np.isfinite(cor["cth"].values)
    row.update({
        "pixels": int(valid.sum()),
        "frac_missing": float(1 - valid.mean()),  # fill values, e.g. a partial scan
        "cloud_fraction": float(cloudy.sum() / max(valid.sum(), 1)),
        "cth_median_km": float(np.nanmedian(cth) / 1000) if cloudy.any() else np.nan,
        "shift_median_km": float(np.nanmedian(shift[cloudy_cells])) if cloudy_cells.any() else np.nan,
        "shift_p95_km": float(np.nanpercentile(shift[cloudy_cells], 95)) if cloudy_cells.any() else np.nan,
        "shift_max_km": float(np.nanmax(shift[cloudy_cells])) if cloudy_cells.any() else np.nan,
    })
    # Fill statistics over cells the satellite covers (observed or not in the uncorrected grid).
    covered = raw["fill_flag"].values != EMPTY
    flag = cor["fill_flag"].values[covered]
    row.update({
        "cells_covered": int(covered.sum()),
        "frac_observed": float((flag == OBSERVED).mean()),
        "frac_interpolated": float((flag == INTERPOLATED).mean()),
        "frac_empty": float((flag == EMPTY).mean()),
    })
    # Clear cells (observed, no cloud in both grids): unchanged unless a moved cloud now covers them.
    rc, cc = raw["cth"].values, cor["cth"].values
    clear_raw = (raw["fill_flag"].values == OBSERVED) & np.isnan(rc)
    same = clear_raw & (cor["fill_flag"].values == OBSERVED) & np.isnan(cc)
    a, b = cor["TIR1"].values[same], raw["TIR1"].values[same]
    row["frac_clear_identical"] = float(np.mean((a == b) | (np.isnan(a) & np.isnan(b)))) if same.any() else np.nan
    row["frac_clear_covered_by_cloud"] = float(np.mean(np.isfinite(cc[clear_raw]))) if clear_raw.any() else np.nan
    row["peak_rss_mb"] = peak / 2**20
    row["t_total_s"] = row["t_read_s"] + row["t_height_s"] + row["t_correct_s"] + row["t_uncorrected_s"]
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True, help="folder searched recursively for 3RIMG_*_L1C_SGP_*.h5")
    ap.add_argument("--limit", type=int, help="process only the first N scenes")
    args = ap.parse_args(argv)

    files = {}
    for p in sorted(Path(args.base).rglob("3RIMG_*_L1C_SGP_V01R00.h5")):
        files.setdefault(p.name, p)
    paths = list(files.values())[: args.limit]
    print(f"{len(paths)} scenes", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, path in enumerate(paths, 1):
        try:
            row = scene(path)
            row["status"] = "ok"
            print(f"[{i}/{len(paths)}] {row['scene']}: {row['t_total_s']:.1f} s, cloud {row['cloud_fraction']:.0%}, "
                  f"shift median {row['shift_median_km']:.1f} km, empty {row['frac_empty']:.2%}", flush=True)
        except Exception as exc:  # recorded, not raised: failures are part of the benchmark
            row = {"scene": path.name[6:20], "status": f"failed: {type(exc).__name__}: {exc}"}
            print(f"[{i}/{len(paths)}] {row['scene']}: {row['status']}", flush=True)
            traceback.print_exc()
        row["file"] = str(path)
        rows.append(row)
        pd.DataFrame(rows).to_csv(OUT / "benchmark_scenes.csv", index=False)
    df = pd.DataFrame(rows)
    ok = df[df.status == "ok"]
    print(f"\n{len(ok)} of {len(df)} scenes processed")
    if len(ok):
        for col in ("t_read_s", "t_height_s", "t_correct_s", "t_uncorrected_s", "t_total_s", "peak_rss_mb"):
            print(f"  {col:18s} median {ok[col].median():8.2f}  p95 {ok[col].quantile(0.95):8.2f}  max {ok[col].max():8.2f}")
        for col in ("frac_missing", "cloud_fraction", "shift_median_km", "shift_p95_km", "frac_observed", "frac_interpolated",
                    "frac_empty", "frac_clear_identical", "frac_clear_covered_by_cloud"):
            print(f"  {col:28s} median {ok[col].median():.3f}  range {ok[col].min():.3f}-{ok[col].max():.3f}")
    print(f"wrote {OUT / 'benchmark_scenes.csv'}")


if __name__ == "__main__":
    main()
