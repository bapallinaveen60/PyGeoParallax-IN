"""Compare cloud-top heights from ERA5 profiles with the AFGL standard atmosphere, case by case.

For every usable case in ``all_cases.csv``:

1. Re-run the case with ERA5 heights (``--profile era5``), without and with
   the monsoon navigation correction (``<case>_era5``, ``<case>_era5_mnav``).
2. Take the near-storm line-of-sight offset (storm-top field, 150 and 250 km)
   in the four states (raw, parallax, navigation, both) for each profile.
   A case/window counts only if all eight matches lie inside the search.

Run ``test_navigation_parallax.py`` first (it writes the monsoon navigation
JSON and the AFGL ``_mnav`` runs). Cell-by-cell offsets and core heights:
``analyze_core_offsets.py --suffix _era5``.

Usage:
    python scripts/compare_era5_heights.py --base <validation folder>
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

OUT = Path("05_validation/gpm_colocation")
NAV_JSON = Path("05_validation/nav_corrections/monsoon_median.json")
EDGE = 9.5  # cells


def run_era5(folder, case, rerun=False):
    region = case.split("_")[0]
    common = ["--dir", str(folder), "--scan", run_all_cases.case_scan(folder),
              "--bbox", *map(str, run_all_cases.REGION_BOX[region]), "--profile", "era5"]
    if rerun or not (OUT / f"{case}_era5.json").exists():
        run_validation_case.main(common + ["--case", f"{case}_era5"])
    if rerun or not (OUT / f"{case}_era5_mnav.json").exists():
        run_validation_case.main(common + ["--case", f"{case}_era5_mnav", "--nav", str(NAV_JSON), "--nav-only"])


def states(base, nav, rad):
    b = base["runs"]["no_nav"][f"near_{rad}km"]
    n = nav["runs"]["nav"][f"near_{rad}km"]
    return {"raw": b["uncorrected"]["top"], "parallax": b["corrected"]["top"],
            "navigation": n["uncorrected"]["top"], "both": n["corrected"]["top"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--rerun", action="store_true")
    args = ap.parse_args(argv)

    table = pd.read_csv(OUT / "all_cases.csv")
    cases = table[(table.nav == "no_nav") & table.status.str.startswith("usable")]["case"].tolist()
    rows = []
    for case in cases:
        folder = Path(args.base) / case
        if not list(folder.glob("era5_pl_*.nc")):
            print(f"{case}: no ERA5 file, skipped", flush=True)
            continue
        run_era5(folder, case, args.rerun)
        runs = {p: (json.loads((OUT / f"{case}{s}.json").read_text()), json.loads((OUT / f"{case}{s}_mnav.json").read_text()))
                for p, s in (("afgl", ""), ("era5", "_era5"))}
        _, vaa = satellite_view_angles(*runs["afgl"][0]["gpm_convection_centre"], 74.0)
        for rad in (150, 250):
            st = {p: states(*runs[p], rad) for p in runs}
            valid = all(max(abs(v) for v in s["lag_cells_s_e"]) < EDGE for p in st for s in st[p].values())
            row = {"case": case, "region": case.split("_")[0], "window_km": rad, "valid": valid,
                   "vza": runs["afgl"][0].get("vza_at_convection_deg")}
            for p in st:
                row[f"{p}_deep_shift_km"] = runs[p][0]["runs"]["no_nav"]["shift_km_deep_cores_median"]
                for name, s in st[p].items():
                    row[f"{p}_{name}"] = round(run_all_cases.split(s["offset_km_s_e"], float(vaa))[0], 2)
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "era5_comparison.csv", index=False)
    print(f"wrote {OUT / 'era5_comparison.csv'}")

    for rad in (250, 150):
        v = df[(df.window_km == rad) & df.valid]
        print(f"\nStorm-top field, {rad} km window, {len(v)} cases (positive = INSAT must move towards the satellite):")
        print(f"  {'state':12s} {'AFGL mean':>10s} {'ERA5 mean':>10s} {'AFGL |med|':>11s} {'ERA5 |med|':>11s}")
        for name in ("raw", "parallax", "navigation", "both"):
            a, e = v[f"afgl_{name}"], v[f"era5_{name}"]
            print(f"  {name:12s} {a.mean():+10.1f} {e.mean():+10.1f} {np.median(abs(a)):11.1f} {np.median(abs(e)):11.1f}")
        print(f"  deep-core shift median: AFGL {v.afgl_deep_shift_km.median():.1f} km, ERA5 {v.era5_deep_shift_km.median():.1f} km")


if __name__ == "__main__":
    main()
