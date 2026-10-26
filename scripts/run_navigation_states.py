"""Run every usable case with its year's pooled navigation correction (and the all-India sensitivity value).

For each usable case in ``all_cases.csv``:

- ``<case>_ynav``: navigation from ``nav_corrections/pooled_<year>.json``
  (``yearly_navigation.py``), with and without parallax correction;
- ``<case>_mnav``: the all-India monsoon median (+1.8 km E, +4.8 km N), as a
  sensitivity test;
- ``<case>_gnav`` (with ``--tags gnav``): navigation measured against GPM on all
  the *other* cases (``gpm_navigation.py``).

Existing runs are kept unless ``--rerun`` is given.

Usage:
    python scripts/run_navigation_states.py --base <validation folder>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import run_all_cases  # noqa: E402
import run_validation_case  # noqa: E402

from pygeoparallax.navigation import NavigationCorrection  # noqa: E402

OUT = Path("05_validation/gpm_colocation")
NAV = Path("05_validation/nav_corrections")
ALL_INDIA = (1.8, 4.8)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--tags", nargs="+", default=["ynav", "mnav"], choices=["ynav", "mnav", "gnav"],
                    help="navigation states to run (gnav: GPM-derived, leave-one-case-out)")
    args = ap.parse_args(argv)

    mnav = NAV / "monsoon_median.json"
    if not mnav.exists():
        NavigationCorrection([20.0], [85.0], [ALL_INDIA[0]], [ALL_INDIA[1]],
                             meta={"note": "all-India monsoon median from coastline matching"}).to_json(mnav)
    t = pd.read_csv(OUT / "all_cases.csv")
    cases = t[(t.nav == "no_nav") & t.status.str.startswith("usable")].case.tolist()
    for case in cases:
        region, year = case.split("_")[0], case.split("_")[1][:4]
        folder = Path(args.base) / case
        common = ["--dir", str(folder), "--scan", run_all_cases.case_scan(folder),
                  "--bbox", *map(str, run_all_cases.REGION_BOX[region]), "--nav-only"]
        states = {"ynav": NAV / f"pooled_{year}.json", "mnav": mnav,
                  "gnav": NAV / f"gpm_loo_{case}.json"}  # GPM-derived, leave-one-case-out (gpm_navigation.py)
        for tag, nav in ((t_, states[t_]) for t_ in args.tags):
            if not nav.exists():
                print(f"{case}: no {nav.name}, {tag} skipped", flush=True)
                continue
            if args.rerun or not (OUT / f"{case}_{tag}.json").exists():
                print(f"{case}: {tag}", flush=True)
                run_validation_case.main(common + ["--case", f"{case}_{tag}", "--nav", str(nav)])


if __name__ == "__main__":
    main()
