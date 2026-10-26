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
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import run_validation_case  # noqa: E402

from pygeoparallax.geometry import satellite_view_angles  # noqa: E402
from pygeoparallax.navigation import (  # noqa: E402
    WINDOWS, NavigationCorrection, land_fraction_interpolator, load_land, measure_scan,
)

REGION_BOX = {"northeast": (21, 29, 88, 97), "himalaya": (24, 33, 74, 90), "central": (18, 27, 75, 86), "south": (7, 18, 73, 82)}
MIN_CLUSTER = 100  # convective footprints in the main cluster for a case to count
# A field/window counts only if its best match lies inside the +/-10-cell search (no edge hit).
# GPM storm-top height is the primary field (same storm tops as TIR1); rain intensity (Z) is secondary.


#: Case scans fixed when each case was first run. Case folders also hold navigation scans
#: (other times, and the days before and after), so a rule on file names alone is ambiguous.
CASE_SCANS = Path(__file__).resolve().parents[1] / "00_Documentation" / "events" / "case_scans.csv"
NAV_SLOTS = ("_0315", "_0415", "_0515", "_0615", "_0815")


def case_scan(folder):
    """The INSAT case scan of a case folder.

    1. The scan pinned in ``case_scans.csv``, if the case is listed.
    2. Else the stamp of a CTP file on the case date (a case scan can be at 04:15 or 06:15).
    3. Else an L1C on the case date that is not in a navigation time slot.
    """
    folder = Path(folder)
    if CASE_SCANS.exists():
        with CASE_SCANS.open(newline="") as fh:
            pinned = {r["case"]: r["insat_scan"] for r in csv.DictReader(fh)}
        if folder.name in pinned:
            return pinned[folder.name]
    try:
        day = datetime.strptime(folder.name.split("_")[1], "%Y%m%d").strftime("%d%b%Y").upper()
    except (IndexError, ValueError):
        return None
    for p in sorted(folder.glob(f"3RIMG_{day}_*_L2B_CTP_V01R00.h5")):
        stamp = p.name[6:20]
        if (folder / f"3RIMG_{stamp}_L1C_SGP_V01R00.h5").exists():
            return stamp
    for p in sorted(folder.glob(f"3RIMG_{day}_*_L1C_SGP_V01R00.h5")):
        stamp = p.name[6:20]
        if not stamp.endswith(NAV_SLOTS):
            return stamp
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
            valid = {}
            for rad in (150, 250):
                n = r[f"near_{rad}km"]
                edge = lambda key: any(  # noqa: E731
                    max(abs(v) for v in (n[k][key]["lag_cells_s_e"] if key else n[k]["lag_cells_s_e"])) >= 9.5
                    for k in ("uncorrected", "corrected"))
                valid[f"z{rad}"] = not edge(None)
                ab, cb = split(n["uncorrected"]["offset_km_s_e"], float(vaa))
                aa, ca = split(n["corrected"]["offset_km_s_e"], float(vaa))
                row.update({
                    f"z_valid{rad}": valid[f"z{rad}"],
                    f"along{rad}_before": round(ab, 1), f"along{rad}_after": round(aa, 1),
                    f"cross{rad}_before": round(cb, 1), f"cross{rad}_after": round(ca, 1),
                    f"deepiou{rad}_before": n["uncorrected"]["iou_deep_vs_deep_echo"],
                    f"deepiou{rad}_after": n["corrected"]["iou_deep_vs_deep_echo"],
                    f"r{rad}_before": n["uncorrected"]["pearson"], f"r{rad}_after": n["corrected"]["pearson"],
                })
                if "top" in n["uncorrected"]:
                    valid[f"top{rad}"] = not edge("top")
                    tb, tcb = split(n["uncorrected"]["top"]["offset_km_s_e"], float(vaa))
                    ta, tca = split(n["corrected"]["top"]["offset_km_s_e"], float(vaa))
                    row.update({f"top_valid{rad}": valid[f"top{rad}"],
                                f"top_along{rad}_before": round(tb, 1), f"top_along{rad}_after": round(ta, 1),
                                f"top_cross{rad}_before": round(tcb, 1), f"top_cross{rad}_after": round(tca, 1),
                                f"top_r{rad}_before": n["uncorrected"]["top"]["r"], f"top_r{rad}_after": n["corrected"]["top"]["r"]})
            if cluster < MIN_CLUSTER:
                row["status"] = f"excluded: {cluster} convective footprints (< {MIN_CLUSTER})"
            elif not any(valid.values()):
                row["status"] = "excluded: no reliable match in any field or window"
            else:
                row["status"] = "usable: " + ", ".join(k for k, ok in valid.items() if ok)
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
        case, region = folder.name, folder.name.split("_")[0]
        if region not in REGION_BOX:
            continue  # not a case folder (e.g. gpm_screen)
        scan = case_scan(folder)
        if scan is None:
            skipped.append((case, "skipped: no case scan"))
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
