"""Navigation correction of INSAT-3DR measured against GPM, with leave-one-case-out validation.

After parallax correction, the offset between an INSAT cold core and the GPM
deep-echo cell it is paired with is, to first order, the INSAT navigation error
(plus storm structure and cloud-height error). For each case this takes the
median offset of its cells in the parallax-corrected state, converts it from
along/cross-look to east/north, and then gives every case the median of the
*other* cases (leave-one-case-out), so no case is corrected with its own data.

Writes ``05_validation/nav_corrections/gpm_loo_<case>.json`` per case,
``gpm_navigation_by_case.csv`` and prints the pooled value, per-year medians
and their spread.

Usage:
    python scripts/gpm_navigation.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from pygeoparallax.geometry import satellite_view_angles
from pygeoparallax.navigation import NavigationCorrection

VAL = Path("05_validation/gpm_colocation")
NAV = Path("05_validation/nav_corrections")


def main():
    cells = pd.read_csv(VAL / "core_offsets_cells.csv")
    c = cells[cells.kind == "corrected"].dropna(subset=["along_km", "cross_km"]).copy()
    t = pd.read_csv(VAL / "all_cases.csv")
    usable = t[(t.nav == "no_nav") & t.status.str.startswith("usable")].case.tolist()
    rows = []
    for case, g in c.groupby("case"):
        centre = json.loads((VAL / f"{case}.json").read_text())["gpm_convection_centre"]
        _, vaa = satellite_view_angles(*centre, 74.0)
        th = np.radians(float(vaa))
        # along = e sin(th) + n cos(th); cross = e cos(th) - n sin(th)  ->  invert
        east = g.along_km * np.sin(th) + g.cross_km * np.cos(th)
        north = g.along_km * np.cos(th) - g.cross_km * np.sin(th)
        rows.append({"case": case, "year": int(case.split("_")[1][:4]), "region": case.split("_")[0],
                     "cells": len(g), "east_km": float(np.median(east)), "north_km": float(np.median(north)),
                     "along_km": float(np.median(g.along_km)), "cross_km": float(np.median(g.cross_km))})
    d = pd.DataFrame(rows)
    # Leave-one-case-out: each usable case gets the median of the other cases.
    loo = []
    for case in usable:
        others = d[d.case != case]
        e, n = float(others.east_km.median()), float(others.north_km.median())
        loo.append({"case": case, "loo_east_km": round(e, 2), "loo_north_km": round(n, 2)})
        NavigationCorrection([20.0], [85.0], [e], [n], meta={
            "note": "navigation from GPM: median cell offset after parallax correction of the other cases",
            "cases_used": int(len(others))}).to_json(NAV / f"gpm_loo_{case}.json")
    out = d.merge(pd.DataFrame(loo), on="case", how="right")
    out.to_csv(NAV / "gpm_navigation_by_case.csv", index=False)

    mad = lambda x: 1.4826 * np.median(np.abs(x - np.median(x)))  # noqa: E731
    rng = np.random.default_rng(2026)
    boot = np.array([[np.median(d.east_km.values[i]), np.median(d.north_km.values[i])]
                     for i in rng.integers(0, len(d), size=(10000, len(d)))])
    print(f"{len(d)} cases with cells. Pooled navigation from GPM (correction to add to INSAT positions):")
    print(f"  east  {d.east_km.median():+.1f} km (95 % interval {np.percentile(boot[:, 0], 2.5):+.1f} .. {np.percentile(boot[:, 0], 97.5):+.1f}), case spread {mad(d.east_km):.1f} km")
    print(f"  north {d.north_km.median():+.1f} km (95 % interval {np.percentile(boot[:, 1], 2.5):+.1f} .. {np.percentile(boot[:, 1], 97.5):+.1f}), case spread {mad(d.north_km):.1f} km")
    print("By year:")
    print(d.groupby("year").agg(cases=("case", "size"), east_km=("east_km", "median"), north_km=("north_km", "median")).round(1).to_string())
    print("By region:")
    print(d.groupby("region").agg(cases=("case", "size"), east_km=("east_km", "median"), north_km=("north_km", "median")).round(1).to_string())
    print(f"wrote {len(loo)} leave-one-out corrections to {NAV}/gpm_loo_<case>.json")


if __name__ == "__main__":
    main()
