"""Monsoon navigation correction per year, pooled from daytime coastline matches in the case folders.

Night-time coastline matching fails in the monsoon and single-day daytime
matches scatter by ~10 km, so the correction is pooled over a season. For every
case folder this measures the coastline offset in each daytime L1C scan
(03:15-08:15 UTC) in the coastal windows nearest the case region, then pools the
reliable matches (r >= 0.7, not at the search edge, both components within
25 km) by year. Per-year corrections are written as
``05_validation/nav_corrections/pooled_<year>.json``; all matches go to
``yearly_matches.csv`` and the summary to ``yearly_summary.csv``.

Usage:
    python scripts/yearly_navigation.py --base <validation folder>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from near_storm_navigation import NEAR  # noqa: E402

from pygeoparallax.navigation import (  # noqa: E402
    WINDOWS, NavigationCorrection, land_fraction_interpolator, load_land, measure_scan,
)

NAV = Path("05_validation/nav_corrections")
DAYTIME = ("_0315", "_0345", "_0415", "_0445", "_0515", "_0545", "_0615", "_0645", "_0715", "_0745", "_0815")
MIN_R, MAX_KM = 0.7, 25.0
MIN_MATCHES = 8  # fewer reliable matches in a year: use the value pooled over all years


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--land", default="01_raw_data/natural_earth/ne_10m_land.geojson")
    ap.add_argument("--rerun", action="store_true", help="re-measure folders already in yearly_matches.csv")
    args = ap.parse_args(argv)

    out_csv = NAV / "yearly_matches.csv"
    old = pd.read_csv(out_csv) if out_csv.exists() and not args.rerun else pd.DataFrame(columns=["case"])
    done = set(old.case)
    land = load_land(args.land)
    interps, rows = {}, []
    folders = sorted(p for p in Path(args.base).iterdir() if p.is_dir() and p.name.split("_")[0] in NEAR)
    for folder in folders:
        if folder.name in done:
            continue
        region = folder.name.split("_")[0]
        windows = {k: WINDOWS[k] for k in NEAR[region]}
        for k in windows:
            if k not in interps:
                interps[k] = land_fraction_interpolator(land, WINDOWS[k])
        n = 0
        for p in sorted(folder.glob("3RIMG_*_L1C_SGP_V01R00.h5")):
            if not p.name[6:20].endswith(DAYTIME):
                continue
            try:
                found = measure_scan(p, land, windows, interps)
            except OSError as exc:
                print(f"  skip {p.name}: {exc}", flush=True)
                continue
            for m in found:
                rows.append({"case": folder.name, "year": int(p.name[11:15]), **{k: m[k] for k in (
                    "scan", "window", "channel", "east_km", "north_km", "r_best", "r_zero", "on_edge", "lat", "lon")}})
                n += 1
        print(f"{folder.name}: {n} matches", flush=True)
    allm = pd.concat([old, pd.DataFrame(rows)], ignore_index=True) if rows else old
    allm.to_csv(out_csv, index=False)

    allm["year"] = allm["year"].astype(int)
    ok = allm[(allm.r_best >= MIN_R) & ~allm.on_edge.astype(bool) & (allm.east_km.abs() <= MAX_KM)
              & (allm.north_km.abs().fillna(0) <= MAX_KM)]
    mad = lambda x: float(1.4826 * np.nanmedian(np.abs(x - np.nanmedian(x))))  # noqa: E731
    all_e, all_n = ok.east_km.median(), ok.north_km.median()
    summary = []
    for year in sorted(allm.year.unique()):
        g = ok[ok.year == year]
        own = len(g) >= MIN_MATCHES
        e, nth = (g.east_km.median(), g.north_km.median()) if own else (all_e, all_n)
        summary.append({"year": int(year), "matches": len(g), "days": g.case.nunique(),
                        "east_km": round(e, 1), "north_km": round(nth, 1),
                        "east_spread_km": round(mad(g.east_km), 1) if len(g) else np.nan,
                        "north_spread_km": round(mad(g.north_km), 1) if len(g) else np.nan,
                        "source": "this year" if own else f"all years (fewer than {MIN_MATCHES} matches)"})
        NavigationCorrection([20.0], [85.0], [e], [nth], meta={
            "note": (f"pooled daytime coastline matches near the {year} monsoon validation cases" if own else
                     f"{year} has only {len(g)} reliable matches; pooled value of all years used"),
            "matches": len(g), "rule": f"r >= {MIN_R}, not at the search edge, |offset| <= {MAX_KM} km"}).to_json(
            NAV / f"pooled_{int(year)}.json")
    summary.append({"year": "all", "matches": len(ok), "days": ok.case.nunique(), "east_km": round(all_e, 1),
                    "north_km": round(all_n, 1), "east_spread_km": round(mad(ok.east_km), 1),
                    "north_spread_km": round(mad(ok.north_km), 1), "source": "all years"})
    s = pd.DataFrame(summary)
    s.to_csv(NAV / "yearly_summary.csv", index=False)
    print(s.to_string(index=False))


if __name__ == "__main__":
    main()
