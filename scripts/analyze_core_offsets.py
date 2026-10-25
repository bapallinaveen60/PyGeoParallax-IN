"""Offset between INSAT cold cores and GPM deep-echo cells, cell by cell (no field correlation).

For each usable case, inside the GPM swath and within ``--radius`` km of the
GPM convective cluster:

1. Label each GPM deep-echo cell: connected cells with storm top > 10 km,
   at least ``--min-cells`` grid cells.
2. Around each cell's centroid, take the INSAT pixels within ``--search`` km,
   and the centroid of those within 3 K of the local minimum BT (the cold
   core). Do this for the uncorrected and the parallax-corrected grids.
3. The cell offset (GPM minus INSAT) is split into along-look (towards the
   satellite) and cross-look parts. The case value is the median over its cells.

Whole-window centroids do not work: a 150 km window holds several separate
cells, and the coldest pixels and the echo cores sit in different parts of it.

Usage:
    python scripts/analyze_core_offsets.py --base <validation folder>
    python scripts/analyze_core_offsets.py --base <validation folder> --suffix _era5   # ERA5-height runs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).parent))
import run_all_cases  # noqa: E402
import run_validation_case as rvc  # noqa: E402

from pygeoparallax.geometry import satellite_view_angles  # noqa: E402
from pygeoparallax.resample import Grid  # noqa: E402
from pygeoparallax.validation import range_mask  # noqa: E402


def centroid(mask, glat, glon):
    if mask.sum() < 5:
        return np.nan, np.nan
    return float(glat[mask].mean()), float(glon[mask].mean())


def offset_km(a, b, vaa):
    """GPM minus INSAT as (along-look, cross-look) km; along > 0 = INSAT must move towards the satellite."""
    dn = (b[0] - a[0]) * 111.2
    de = (b[1] - a[1]) * 111.2 * np.cos(np.radians(a[0]))
    t = np.radians(vaa)
    return de * np.sin(t) + dn * np.cos(t), de * np.cos(t) - dn * np.sin(t)


def core_height(bt, cth, glat, glon, lat0, lon0, search_km):
    """Cloud-top height [m] of the cold core (median of the gridded height over its pixels)."""
    d = np.hypot(glat - lat0, (glon - lon0) * np.cos(np.radians(lat0))) * 111.2
    near = (d <= search_km) & np.isfinite(bt)
    if near.sum() < 10:
        return np.nan, np.nan
    core = near & (bt <= np.nanmin(bt[near]) + 3.0) & np.isfinite(cth)
    if not core.any():
        return np.nan, float(np.nanmin(bt[near]))
    return float(np.median(cth[core])), float(np.nanmin(bt[near]))


def cold_core(bt, glat, glon, lat0, lon0, search_km):
    d = np.hypot(glat - lat0, (glon - lon0) * np.cos(np.radians(lat0))) * 111.2
    near = (d <= search_km) & np.isfinite(bt)
    if near.sum() < 10:
        return np.nan, np.nan
    core = near & (bt <= np.nanmin(bt[near]) + 3.0)
    return centroid(core, glat, glon) if core.sum() >= 1 else (np.nan, np.nan)


def main(argv=None):
    from scipy import ndimage

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--radius", type=float, default=250.0)
    ap.add_argument("--search", type=float, default=25.0, help="km around each GPM cell to look for the cold core")
    ap.add_argument("--min-cells", type=int, default=8, help="smallest deep-echo cell, in 0.02 deg grid cells")
    ap.add_argument("--suffix", default="", help="case-name suffix of the runs to analyse, e.g. _era5")
    args = ap.parse_args(argv)

    table = pd.read_csv("05_validation/gpm_colocation/all_cases.csv")
    cases = table[(table.nav == "no_nav") & table.status.str.startswith("usable")]["case"].tolist()
    rows, cells_out = [], []
    for case in cases:
        region = case.split("_")[0]
        box = run_all_cases.REGION_BOX[region]
        grid = Grid(*box, res=0.02)
        gpm = rvc.gpm_on_grid(rvc.find(Path(args.base) / case, "2A.GPM.*"), grid, box)
        cen = gpm["conv_centre"]
        _, vaa = satellite_view_angles(*cen, 74.0)
        d = json.loads((Path("05_validation/gpm_colocation") / f"{case}{args.suffix}.json").read_text())
        glat, glon = np.meshgrid(grid.lats, grid.lons, indexing="ij")
        near = range_mask(grid, cen[0], cen[1], args.radius) & gpm["covered"]
        labels, n = ndimage.label((np.nan_to_num(gpm["top"]) > 10000) & near)
        grids = {k: xr.open_dataset(f"04_corrected_output/netcdf/{case}{args.suffix}_no_nav_{k}.nc")
                 for k in ("uncorrected", "corrected")}
        bts = {k: g["TIR1"].values for k, g in grids.items()}
        raw_cth = grids["uncorrected"]["cth"].values
        # With the monsoon navigation correction (from test_navigation_parallax.py), if available.
        for k, src in (("nav_only", "uncorrected"), ("nav_parallax", "corrected")):
            f = Path("04_corrected_output/netcdf") / f"{case}{args.suffix}_mnav_nav_{src}.nc"
            if f.exists():
                bts[k] = xr.open_dataset(f)["TIR1"].values
        per = {k: [] for k in bts}
        d = json.loads((Path("05_validation/gpm_colocation") / f"{case}{args.suffix}.json").read_text())
        for lab in range(1, n + 1):
            m = labels == lab
            if m.sum() < args.min_cells:
                continue
            g = centroid(m, glat, glon)
            h_ins, bt_min = core_height(bts["uncorrected"], raw_cth, glat, glon, g[0], g[1], args.search)
            tops = np.nan_to_num(gpm["top"])[m]
            cells_out.append({"case": case, "kind": "heights", "cell_lat": round(g[0], 3), "cell_lon": round(g[1], 3),
                              "insat_core_height_km": round(h_ins / 1000, 2), "insat_core_bt_min": round(bt_min, 1),
                              "gpm_top_max_km": round(float(tops.max()) / 1000, 2),
                              "gpm_top_p90_km": round(float(np.percentile(tops, 90)) / 1000, 2),
                              "vza": d.get("vza_at_convection_deg")})
            for kind, bt in bts.items():
                c = cold_core(bt, glat, glon, g[0], g[1], args.search)
                if np.isfinite(c[0]):
                    al, cr = offset_km(c, g, float(vaa))
                    per[kind].append((al, cr))
                    cells_out.append({"case": case, "kind": kind, "cell_lat": round(g[0], 3), "cell_lon": round(g[1], 3),
                                      "along_km": round(al, 1), "cross_km": round(cr, 1)})
        row = {"case": case, "region": region, "vza": d.get("vza_at_convection_deg"),
               "deep_shift_km": d["runs"]["no_nav"]["shift_km_deep_cores_median"], "cells": len(per["uncorrected"])}
        for kind, v in per.items():
            v = np.array(v) if v else np.full((1, 2), np.nan)
            if np.all(np.isnan(v)):
                row[f"{kind}_along_median"] = row[f"{kind}_cross_median"] = np.nan
                continue
            row[f"{kind}_along_median"] = round(float(np.nanmedian(v[:, 0])), 1)
            row[f"{kind}_cross_median"] = round(float(np.nanmedian(v[:, 1])), 1)
        rows.append(row)
        print(f"{case:20s} VZA {row['vza']:4.1f}  cells {row['cells']:3d}  along median: "
              + "  ".join(f"{k} {row.get(k + '_along_median', float('nan')):+6.1f}" for k in per), flush=True)

    out = Path("05_validation/gpm_colocation")
    pd.DataFrame(rows).to_csv(out / f"core_offsets{args.suffix}.csv", index=False)
    pd.DataFrame(cells_out).to_csv(out / f"core_offsets{args.suffix}_cells.csv", index=False)
    print(f"wrote {out}/core_offsets{args.suffix}.csv and core_offsets{args.suffix}_cells.csv")


if __name__ == "__main__":
    main()
