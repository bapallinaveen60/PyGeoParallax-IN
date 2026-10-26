"""Compare a processing variant with the baseline runs, case by case.

Variants:

- ``era5``: cloud-top heights from ERA5 profiles instead of the AFGL standard
  atmosphere (``--profile era5``; needs ``era5_pl_*.nc`` in each case folder).
- ``dem``: terrain-aware correction with an SRTM grid (``--dem``).

For every usable case in ``all_cases.csv``:

1. Re-run the case with the variant, without and with the monsoon navigation
   correction (``<case>_<variant>``, ``<case>_<variant>_mnav``).
2. Take the near-storm line-of-sight offset (storm-top field, 150 and 250 km)
   in the four states (raw, parallax, navigation, both) for the baseline and
   the variant. A case/window counts only if all eight matches lie inside the
   search.

Run ``test_navigation_parallax.py`` first (it writes the monsoon navigation
JSON and the baseline ``_mnav`` runs). Cell-by-cell offsets and core heights:
``analyze_core_offsets.py --suffix _<variant>``.

Usage:
    python scripts/compare_variants.py --base <validation folder> --variant era5
    python scripts/compare_variants.py --base <validation folder> --variant dem --dem 02_standardized_grid/srtm_0p01deg.nc
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


def run_variant(folder, case, variant, extra, rerun=False):
    region = case.split("_")[0]
    common = ["--dir", str(folder), "--scan", run_all_cases.case_scan(folder),
              "--bbox", *map(str, run_all_cases.REGION_BOX[region]), *extra]
    if rerun or not (OUT / f"{case}_{variant}.json").exists():
        run_validation_case.main(common + ["--case", f"{case}_{variant}"])
    if rerun or not (OUT / f"{case}_{variant}_mnav.json").exists():
        run_validation_case.main(common + ["--case", f"{case}_{variant}_mnav", "--nav", str(NAV_JSON), "--nav-only"])


def states(base, nav, rad):
    b = base["runs"]["no_nav"][f"near_{rad}km"]
    n = nav["runs"]["nav"][f"near_{rad}km"]
    return {"raw": b["uncorrected"]["top"], "parallax": b["corrected"]["top"],
            "navigation": n["uncorrected"]["top"], "both": n["corrected"]["top"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--variant", choices=("era5", "dem"), required=True)
    ap.add_argument("--dem", help="DEM NetCDF for --variant dem")
    ap.add_argument("--rerun", action="store_true")
    args = ap.parse_args(argv)
    v = args.variant
    if v == "dem" and not args.dem:
        ap.error("--variant dem needs --dem")
    extra = ["--profile", "era5"] if v == "era5" else ["--dem", args.dem]

    table = pd.read_csv(OUT / "all_cases.csv")
    cases = table[(table.nav == "no_nav") & table.status.str.startswith("usable")]["case"].tolist()
    rows = []
    for case in cases:
        folder = Path(args.base) / case
        if v == "era5" and not list(folder.glob("era5_pl_*.nc")):
            print(f"{case}: no ERA5 file, skipped", flush=True)
            continue
        run_variant(folder, case, v, extra, args.rerun)
        runs = {p: (json.loads((OUT / f"{case}{s}.json").read_text()), json.loads((OUT / f"{case}{s}_mnav.json").read_text()))
                for p, s in (("base", ""), (v, f"_{v}"))}
        _, vaa = satellite_view_angles(*runs["base"][0]["gpm_convection_centre"], 74.0)
        for rad in (150, 250):
            st = {p: states(*runs[p], rad) for p in runs}
            valid = all(max(abs(x) for x in s["lag_cells_s_e"]) < EDGE for p in st for s in st[p].values())
            row = {"case": case, "region": case.split("_")[0], "window_km": rad, "valid": valid,
                   "vza": runs["base"][0].get("vza_at_convection_deg")}
            for p in st:
                row[f"{p}_deep_shift_km"] = runs[p][0]["runs"]["no_nav"]["shift_km_deep_cores_median"]
                for name, s in st[p].items():
                    row[f"{p}_{name}"] = round(run_all_cases.split(s["offset_km_s_e"], float(vaa))[0], 2)
            rows.append(row)
    df = pd.DataFrame(rows)
    out = OUT / f"{v}_comparison.csv"
    df.to_csv(out, index=False)
    print(f"wrote {out}")

    for rad in (250, 150):
        sel = df[(df.window_km == rad) & df.valid]
        print(f"\nStorm-top field, {rad} km window, {len(sel)} cases (positive = INSAT must move towards the satellite):")
        print(f"  {'state':12s} {'base mean':>10s} {v + ' mean':>10s} {'base |med|':>11s} {v + ' |med|':>11s}")
        for name in ("raw", "parallax", "navigation", "both"):
            a, e = sel[f"base_{name}"], sel[f"{v}_{name}"]
            print(f"  {name:12s} {a.mean():+10.1f} {e.mean():+10.1f} {np.median(abs(a)):11.1f} {np.median(abs(e)):11.1f}")
        print(f"  deep-core shift median: base {sel.base_deep_shift_km.median():.1f} km, "
              f"{v} {sel[f'{v}_deep_shift_km'].median():.1f} km")


if __name__ == "__main__":
    main()
