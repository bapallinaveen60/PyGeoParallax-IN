"""Test whether parallax and navigation corrections together centre the INSAT-GPM offset on zero.

For every usable case in ``all_cases.csv`` the line-of-sight offset (INSAT
cloud tops vs GPM, near the storm) is compared in four states:

- **raw:** no correction
- **parallax:** parallax correction only (from the existing runs)
- **navigation:** the monsoon navigation correction only
- **both:** navigation, then parallax

The navigation correction is the monsoon median measured by coastline
matching (+1.8 km E, +4.8 km N; ``navigation_check.md``), applied the same
way to every case, since same-day measurements were unreliable in monsoon
cloud. A field/window result counts only if all four matches lie inside the
search.

Usage:
    python scripts/test_navigation_parallax.py --base <validation folder>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import run_all_cases  # noqa: E402
import run_validation_case  # noqa: E402

from pygeoparallax.geometry import satellite_view_angles  # noqa: E402
from pygeoparallax.navigation import NavigationCorrection  # noqa: E402

MONSOON_NAV = (1.8, 4.8)  # km east, km north
EDGE = 9.5  # cells


def along(offset_s_e, vaa):
    return run_all_cases.split(offset_s_e, vaa)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--rerun", action="store_true", help="re-run cases whose navigation result already exists")
    args = ap.parse_args(argv)

    table = pd.read_csv("05_validation/gpm_colocation/all_cases.csv")
    cases = table[(table.nav == "no_nav") & table.status.str.startswith("usable")]["case"].tolist()
    nav_json = Path("05_validation/nav_corrections/monsoon_median.json")
    NavigationCorrection([20.0], [85.0], [MONSOON_NAV[0]], [MONSOON_NAV[1]],
                         meta={"note": "monsoon median from coastline matching, Jun-Sep 2023/2024"}).to_json(nav_json)

    rows = []
    for case in cases:
        region = case.split("_")[0]
        folder = Path(args.base) / case
        out = Path("05_validation/gpm_colocation") / f"{case}_mnav.json"
        if args.rerun or not out.exists():
            print(f"{case}: running with monsoon navigation", flush=True)
            run_validation_case.main(["--dir", str(folder), "--case", f"{case}_mnav", "--scan", run_all_cases.case_scan(folder),
                                      "--bbox", *map(str, run_all_cases.REGION_BOX[region]),
                                      "--nav", str(nav_json), "--nav-only"])
        base = json.loads((Path("05_validation/gpm_colocation") / f"{case}.json").read_text())
        nav = json.loads(out.read_text())
        _, vaa = satellite_view_angles(*base["gpm_convection_centre"], 74.0)
        for rad in (150, 250):
            b = base["runs"]["no_nav"][f"near_{rad}km"]
            n = nav["runs"]["nav"][f"near_{rad}km"]
            for field in ("top", "z"):
                def pick(d, kind):
                    return d[kind]["top"] if field == "top" else d[kind]
                states = {"raw": pick(b, "uncorrected"), "parallax": pick(b, "corrected"),
                          "navigation": pick(n, "uncorrected"), "both": pick(n, "corrected")}
                valid = all(max(abs(v) for v in st["lag_cells_s_e"]) < EDGE for st in states.values())
                row = {"case": case, "field": field, "window_km": rad, "valid": valid}
                for name, st in states.items():
                    a, c = along(st["offset_km_s_e"], float(vaa))
                    row[f"along_{name}"] = round(a, 1)
                    row[f"cross_{name}"] = round(c, 1)
                rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv("05_validation/gpm_colocation/nav_parallax_test.csv", index=False)
    print("\nLine-of-sight offset [km] (positive = INSAT must move towards the satellite to match GPM)")
    for (field, rad), g in df[df.valid].groupby(["field", "window_km"]):
        parts = [f"{field:3s} {rad} km, n={len(g)}:"]
        for st in ("raw", "parallax", "navigation", "both"):
            v = g[f"along_{st}"]
            parts.append(f"{st} mean {v.mean():+.1f} / median|.| {v.abs().median():.1f}")
        print("  ".join(parts))
    print("wrote 05_validation/gpm_colocation/nav_parallax_test.csv")


if __name__ == "__main__":
    main()
