"""Run every GPM validation case folder and tabulate the results.

Each folder under ``--base`` is named ``<region>_<YYYYMMDD>`` and holds:
- one GPM 2A Ku orbit file;
- the INSAT case scan (L1C, and L2B CTP if available);
- that day's 04:15/06:15 L1C scans for navigation.

For each case:

1. Measure a same-day navigation correction from the morning scans (if any
   window passes the acceptance rules).
2. Run ``run_validation_case.py`` with and without it.
3. Split the near-storm INSAT->GPM offset into along-look (towards the
   satellite, the parallax direction) and cross-look parts, before and after
   correction.

Usage:
    python scripts/run_all_cases.py --base D:/Projects/@GeoVision/Insat_data/datasets/validation
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import run_validation_case  # noqa: E402

from pygeoparallax.geometry import satellite_view_angles  # noqa: E402
from pygeoparallax.navigation import (  # noqa: E402
    WINDOWS, NavigationCorrection, land_fraction_interpolator, load_land, measure_scan,
)

REGION_BOX = {"northeast": (21, 29, 88, 97), "himalaya": (24, 33, 74, 90)}
MIN_CLUSTER = 100  # convective footprints in the main cluster for a case to count


def case_scan(folder):
    for p in sorted(glob.glob(str(Path(folder) / "3RIMG_*_L1C_SGP_V01R00.h5"))):
        m = re.match(r"3RIMG_(\d{2}[A-Z]{3}\d{4}_\d{4})_L1C", Path(p).name)
        if m and not m.group(1).endswith(("_0415", "_0615")):
            return m.group(1)
    return None


def navigation(folder, land, interps, out_json):
    matches = []
    for p in sorted(glob.glob(str(Path(folder) / "3RIMG_*_0[46]15_L1C_SGP_V01R00.h5"))):
        try:
            matches += measure_scan(p, land, WINDOWS, interps)
        except OSError:
            continue
    try:
        corr = NavigationCorrection.from_matches(matches)
    except ValueError:
        return None
    corr.meta["matches"] = matches
    corr.to_json(out_json)
    return out_json


def split(offset_s_e, vaa):
    s, e = offset_s_e
    a = np.radians(vaa)
    north = -s
    return e * np.sin(a) + north * np.cos(a), e * np.cos(a) - north * np.sin(a)


def tabulate(cases, skipped, out):
    """Build the all-cases CSV from each case's JSON; mark usable cases."""
    rows = [{"case": c, "status": why} for c, why in skipped]
    for case in cases:
        js = Path("05_validation/gpm_colocation") / f"{case}.json"
        if not js.exists():
            continue
        d = json.loads(js.read_text())
        if not d["gpm_convection_centre"]:
            rows.append({"case": case, "status": "excluded: no GPM convection in region"})
            continue
        _, vaa = satellite_view_angles(*d["gpm_convection_centre"], 74.0)
        cluster = d.get("gpm_convective_cluster") or 0
        for tag, r in d["runs"].items():
            row = {
                "case": case, "nav": tag, "convective_cluster": cluster,
                "storm_top_max_km": round(d["gpm_storm_top_max_km"], 1), "vza": d.get("vza_at_convection_deg"),
                "dt_min": r["minutes_gpm_minus_insat"], "deep_shift_km": r["shift_km_deep_cores_median"],
            }
            at_edge = False
            for rad in (150, 250):
                n = r[f"near_{rad}km"]
                at_edge |= any(max(abs(v) for v in n[k]["lag_cells_s_e"]) >= 9.5 for k in ("uncorrected", "corrected"))
                if "top" in n["uncorrected"]:
                    tb, tcb = split(n["uncorrected"]["top"]["offset_km_s_e"], float(vaa))
                    ta, tca = split(n["corrected"]["top"]["offset_km_s_e"], float(vaa))
                    row.update({f"top_along{rad}_before": round(tb, 1), f"top_along{rad}_after": round(ta, 1),
                                f"top_cross{rad}_before": round(tcb, 1), f"top_cross{rad}_after": round(tca, 1)})
                ab, cb = split(n["uncorrected"]["offset_km_s_e"], float(vaa))
                aa, ca = split(n["corrected"]["offset_km_s_e"], float(vaa))
                row.update({
                    f"along{rad}_before": round(ab, 1), f"along{rad}_after": round(aa, 1),
                    f"cross{rad}_before": round(cb, 1), f"cross{rad}_after": round(ca, 1),
                    f"deepiou{rad}_before": n["uncorrected"]["iou_deep_vs_deep_echo"],
                    f"deepiou{rad}_after": n["corrected"]["iou_deep_vs_deep_echo"],
                    f"r{rad}_before": n["uncorrected"]["pearson"], f"r{rad}_after": n["corrected"]["pearson"],
                })
            if cluster < MIN_CLUSTER:
                row["status"] = f"excluded: {cluster} convective footprints (< {MIN_CLUSTER})"
            elif at_edge:
                row["status"] = "excluded: offset at the search edge (no reliable match)"
            else:
                row["status"] = "usable"
            rows.append(row)
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("case", "nav", "status"), k))
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--land", default="01_raw_data/natural_earth/ne_10m_land.geojson")
    ap.add_argument("--only", nargs="+", help="run only these case folders")
    ap.add_argument("--tabulate-only", action="store_true", help="rebuild the CSV from existing case JSON")
    args = ap.parse_args(argv)

    folders = sorted(p for p in Path(args.base).iterdir() if p.is_dir() and (not args.only or p.name in args.only))
    cases, skipped = [], []
    land = interps = None
    for folder in folders:
        case, region, scan = folder.name, folder.name.split("_")[0], case_scan(folder)
        if region not in REGION_BOX or scan is None:
            skipped.append((case, "skipped: no case scan" if scan is None else "skipped: unknown region"))
            print(f"{case}: {skipped[-1][1]}", flush=True)
            continue
        cases.append(case)
        if args.tabulate_only:
            continue
        if land is None:
            land = load_land(args.land)
            interps = {k: land_fraction_interpolator(land, b) for k, b in WINDOWS.items()}
        nav = navigation(folder, land, interps, Path("05_validation/nav_corrections") / f"{scan[:9]}.json")
        cmd = ["--dir", str(folder), "--case", case, "--scan", scan, "--bbox", *map(str, REGION_BOX[region])]
        if nav:
            cmd += ["--nav", str(nav)]
        print(f"{case}: scan {scan}, navigation {'measured' if nav else 'none'}", flush=True)
        run_validation_case.main(cmd)
    tabulate(cases, skipped, Path("05_validation/gpm_colocation/all_cases.csv"))


if __name__ == "__main__":
    main()
