"""Choose a designed set of INSAT-3DR scenes for the benchmark and the U-Net test set.

The set is stratified so that every part of the monsoon and of the day is
represented equally:

- **Days:** 2 per month, June-September of 2022, 2023 and 2024 (24 days), drawn
  at random (fixed seed) from days 3-28 of each month (3-18 in September, before
  the navigation error changes state around 20 September). Days within 2 days of a
  GPM validation case, and known partial-scan days, are excluded, so the set
  is independent of the validation cases.
- **Times:** 4 scans per day, 6 hours apart: 00:15, 06:15, 12:15 and 18:15 UTC
  (05:45, 11:45, 17:45 and 23:45 IST). 12:15 UTC falls in the afternoon
  convective peak over land.

For each scene the list gives the L1C file and the matching L2B CTP file (its
clear-sky BT improves the cloud mask; about 2 MB each).

Usage:
    python scripts/design_benchmark_set.py --out 00_Documentation/events/benchmark_scenes.csv
"""

from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path

import numpy as np

YEARS = (2022, 2023, 2024)
MONTHS = (6, 7, 8, 9)
DAYS_PER_MONTH = 2
TIMES = ("0015", "0615", "1215", "1815")
#: Days with partial INSAT-3DR scans found in the benchmark (up to 57 % fill values).
PARTIAL_SCANS = {date(2023, 6, d) for d in (11, 12, 13, 14)}
CASE_SCANS = Path(__file__).resolve().parents[1] / "00_Documentation" / "events" / "case_scans.csv"


def excluded_days(margin=2):
    days = set(PARTIAL_SCANS)
    with CASE_SCANS.open(newline="") as fh:
        for row in csv.DictReader(fh):
            d = date.fromisoformat(f"{row['case'].split('_')[1][:4]}-{row['case'].split('_')[1][4:6]}-{row['case'].split('_')[1][6:]}")
            days.update(d + timedelta(days=k) for k in range(-margin, margin + 1))
    return days


def choose(seed=2026):
    rng = np.random.default_rng(seed)
    skip = excluded_days()
    rows = []
    for year in YEARS:
        for month in MONTHS:
            last = 18 if month == 9 else 28  # the navigation error changes state around 20 September
            pool = [date(year, month, d) for d in range(3, last + 1) if date(year, month, d) not in skip]
            for day in sorted(rng.choice(pool, size=DAYS_PER_MONTH, replace=False)):
                for hhmm in TIMES:
                    stamp = f"{day:%d%b%Y}".upper() + f"_{hhmm}"
                    rows.append({"date": day.isoformat(), "utc": f"{hhmm[:2]}:{hhmm[2:]}",
                                 "l1c_file": f"3RIMG_{stamp}_L1C_SGP_V01R00.h5",
                                 "ctp_file": f"3RIMG_{stamp}_L2B_CTP_V01R00.h5"})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="00_Documentation/events/benchmark_scenes.csv")
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args(argv)
    rows = choose(args.seed)
    out = Path(args.out)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}: {len(rows)} scenes on {len({r['date'] for r in rows})} days")


if __name__ == "__main__":
    main()
