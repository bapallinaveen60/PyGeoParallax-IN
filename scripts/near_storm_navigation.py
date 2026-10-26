"""Navigation correction near each storm, from daytime coastline matching around the case date.

Coastline matching only works in daytime (VIS) during the monsoon: at night land
and sea have almost the same temperature. For every usable case this script:

1. Measures the coastline offset in every daytime L1C scan in the case folder
   (case day 03:15-08:15 UTC and the days before and after), in the coastal
   windows nearest the case region.
2. Builds a correction from the matches that pass the usual acceptance rules
   (``NavigationCorrection.from_matches``), and writes it as
   ``05_validation/nav_corrections/near_<case>.json``.
3. With ``--run``, re-runs the case with that correction
   (``<case>_snav``) for comparison with the monsoon-median correction.

All matches go to ``05_validation/nav_corrections/near_storm_matches.csv``.

Usage:
    python scripts/near_storm_navigation.py --base <validation folder> [--run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import run_all_cases  # noqa: E402
import run_validation_case  # noqa: E402

from pygeoparallax.navigation import (  # noqa: E402
    WINDOWS, NavigationCorrection, land_fraction_interpolator, load_land, measure_scan,
)

#: Coastal windows nearest each case region. The Himalaya has no coast near its storms.
NEAR = {"northeast": ["chittagong", "sundarbans", "rakhine", "odisha"],
        "himalaya": ["kutch", "saurashtra", "sundarbans", "odisha"],
        "central": ["odisha", "andhra", "konkan", "saurashtra"],
        "south": ["kerala", "goa_karnataka", "chennai", "sri_lanka"]}
NAV = Path("05_validation/nav_corrections")
DAYTIME = ("_0315", "_0415", "_0515", "_0615", "_0815")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--land", default="01_raw_data/natural_earth/ne_10m_land.geojson")
    ap.add_argument("--run", action="store_true", help="re-run each case with its near-storm correction")
    args = ap.parse_args(argv)

    table = pd.read_csv("05_validation/gpm_colocation/all_cases.csv")
    cases = table[(table.nav == "no_nav") & table.status.str.startswith("usable")]["case"].tolist()
    land = load_land(args.land)
    interps = {}
    rows, summary = [], []
    for case in cases:
        region = case.split("_")[0]
        folder = Path(args.base) / case
        windows = {k: WINDOWS[k] for k in NEAR[region]}
        for k in windows:
            if k not in interps:
                interps[k] = land_fraction_interpolator(land, WINDOWS[k])
        matches = []
        for p in sorted(folder.glob("3RIMG_*_L1C_SGP_V01R00.h5")):
            if not p.name[6:20].endswith(DAYTIME):
                continue
            try:
                found = measure_scan(p, land, windows, interps)
            except OSError as exc:
                print(f"  skip {p.name}: {exc}", flush=True)
                continue
            for m in found:
                rows.append({"case": case, **{k: m[k] for k in ("scan", "window", "channel", "east_km", "north_km",
                                                               "r_best", "r_zero", "on_edge")}})
            matches += found
        out = NAV / f"near_{case}.json"
        try:
            corr = NavigationCorrection.from_matches(matches)
        except ValueError:
            print(f"{case}: no accepted near-storm match", flush=True)
            summary.append({"case": case, "windows": "", "east_km": np.nan, "north_km": np.nan})
            continue
        corr.meta["matches"] = matches
        corr.to_json(out)
        used = ", ".join(f"{w} ({e:+.1f} E, {n:+.1f} N)" for w, e, n in zip(corr.meta["windows"], corr.east_km, corr.north_km))
        print(f"{case}: {used}", flush=True)
        # The correction at the storm (IDW of the windows).
        js = pd.read_json(Path("05_validation/gpm_colocation") / f"{case}.json", typ="series")
        lat, lon = js["gpm_convection_centre"]
        e, n = corr(lat, lon)
        summary.append({"case": case, "windows": "; ".join(corr.meta["windows"]),
                        "east_km": round(float(e), 1), "north_km": round(float(n), 1)})
        if args.run:
            run_validation_case.main(["--dir", str(folder), "--case", f"{case}_snav", "--scan", run_all_cases.case_scan(folder),
                                      "--bbox", *map(str, run_all_cases.REGION_BOX[region]),
                                      "--nav", str(out), "--nav-only"])
    pd.DataFrame(rows).to_csv(NAV / "near_storm_matches.csv", index=False)
    pd.DataFrame(summary).to_csv(NAV / "near_storm_summary.csv", index=False)
    print(f"wrote {NAV / 'near_storm_matches.csv'} and near_storm_summary.csv")


if __name__ == "__main__":
    main()
