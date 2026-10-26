"""Confidence intervals and paired tests for the GPM validation.

Field measure (storm-top field, 250 km window; the cases valid in every state):

- per state: median absolute and mean line-of-sight offset, with 95 % bootstrap
  confidence intervals (cases resampled with replacement);
- per comparison (raw -> parallax, raw -> navigation + parallax,
  parallax -> navigation + parallax): median change in absolute offset with a
  bootstrap interval, the Wilcoxon signed-rank test on the paired absolute
  offsets, and the exact sign test on the number of cases that improve;
- cross-look offsets: the same paired comparison (it should not change);
- viewing-angle dependence of the raw offset: Spearman correlation and the
  slope against tan(VZA), with a bootstrap interval.

Cell measure (GPM deep-echo cells vs INSAT cold cores): cells of one case are not
independent, so intervals come from a cluster bootstrap that resamples cases;
the paired test uses the per-case medians.

Navigation states use the pooled near-storm correction (-0.5 km E, +2.5 km N);
the all-India monsoon median is reported as a sensitivity test.

Usage:
    python scripts/validation_statistics.py [--n-boot 10000]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from run_all_cases import split  # noqa: E402

from pygeoparallax.geometry import satellite_view_angles  # noqa: E402

VAL = Path("05_validation/gpm_colocation")
OUT = Path("05_validation/statistics")
EDGE = 9.5  # cells: a match at the search edge is not reliable
STATES = {"raw": "Raw", "parallax": "Parallax only", "nav": "Navigation only",
          "both": "Navigation + parallax", "both_allindia": "All-India navigation + parallax"}


def field_table(rad=250):
    """Per-case along- and cross-look offsets in every state; only cases valid in all states."""
    t = pd.read_csv(VAL / "all_cases.csv")
    rows = []
    for case in t[(t.nav == "no_nav") & t.status.str.startswith("usable")].case:
        run = {s: json.loads((VAL / f"{case}{s}.json").read_text()) for s in ("", "_pnav", "_mnav")}
        near = {s: r["runs"]["no_nav" if s == "" else "nav"][f"near_{rad}km"] for s, r in run.items()}
        st = {"raw": near[""]["uncorrected"], "parallax": near[""]["corrected"], "nav": near["_pnav"]["uncorrected"],
              "both": near["_pnav"]["corrected"], "both_allindia": near["_mnav"]["corrected"]}
        st = {k: v["top"] for k, v in st.items()}
        if not all(max(abs(x) for x in v["lag_cells_s_e"]) < EDGE for v in st.values()):
            continue
        _, vaa = satellite_view_angles(*run[""]["gpm_convection_centre"], 74.0)
        row = {"case": case, "vza": run[""]["vza_at_convection_deg"]}
        for k, v in st.items():
            row[f"{k}_along"], row[f"{k}_cross"] = split(v["offset_km_s_e"], float(vaa))
        rows.append(row)
    return pd.DataFrame(rows)


def cell_table():
    """Per-cell along-look offsets: raw and parallax from the base runs, navigation states from the near-storm runs."""
    base = pd.read_csv(VAL / "core_offsets_cells.csv")
    near = pd.read_csv(VAL / "core_offsets_pnav_cells.csv")
    parts = {"raw": base[base.kind == "uncorrected"], "parallax": base[base.kind == "corrected"],
             "nav": near[near.kind == "nav_only"], "both": near[near.kind == "nav_parallax"],
             "both_allindia": base[base.kind == "nav_parallax"]}
    out = []
    for state, d in parts.items():
        out.append(d[["case", "cell_lat", "cell_lon", "along_km"]].assign(state=state))
    return pd.concat(out).dropna(subset=["along_km"])


def boot(values, fn, n, rng):
    """Percentile bootstrap 95 % interval of fn over cases."""
    values = np.asarray(values)
    idx = rng.integers(0, len(values), size=(n, len(values)))
    reps = np.array([fn(values[i]) for i in idx])
    return float(np.percentile(reps, 2.5)), float(np.percentile(reps, 97.5))


def cluster_boot(df, fn, n, rng):
    """Bootstrap over cases (clusters): resample cases, keep all their cells."""
    groups = [g for _, g in df.groupby("case")]
    reps = []
    for _ in range(n):
        pick = rng.integers(0, len(groups), size=len(groups))
        reps.append(fn(pd.concat([groups[i] for i in pick])))
    return float(np.percentile(reps, 2.5)), float(np.percentile(reps, 97.5))


def paired(a, b, n, rng):
    """Compare |b| with |a| case by case: median change, bootstrap interval, Wilcoxon and sign tests."""
    da, db = np.abs(np.asarray(a)), np.abs(np.asarray(b))
    diff = db - da
    improved = int((diff < 0).sum())
    return {
        "median_change_km": float(np.median(diff)),
        "median_change_ci": boot(diff, np.median, n, rng),
        "improved": improved, "cases": len(diff),
        "wilcoxon_p": float(stats.wilcoxon(da, db).pvalue),
        "sign_test_p": float(stats.binomtest(improved, len(diff), 0.5).pvalue),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args(argv)
    rng = np.random.default_rng(args.seed)
    n = args.n_boot

    f = field_table()
    res = {"field_cases": len(f), "field": {}, "field_paired": {}, "cells": {}, "cells_paired": {}}
    for s in STATES:
        a = f[f"{s}_along"].values
        res["field"][s] = {
            "median_abs_km": float(np.median(np.abs(a))), "median_abs_ci": boot(np.abs(a), np.median, n, rng),
            "mean_km": float(np.mean(a)), "mean_ci": boot(a, np.mean, n, rng),
        }
    for a, b in (("raw", "parallax"), ("raw", "both"), ("parallax", "both"), ("raw", "both_allindia")):
        res["field_paired"][f"{a}->{b}"] = paired(f[f"{a}_along"], f[f"{b}_along"], n, rng)
    res["field_paired"]["cross_raw->parallax"] = paired(f["raw_cross"], f["parallax_cross"], n, rng)
    tan = np.tan(np.radians(f.vza.values))
    rho, p_rho = stats.spearmanr(tan, f.raw_along)
    slope = float(np.polyfit(tan, f.raw_along, 1)[0])
    idx = rng.integers(0, len(f), size=(n, len(f)))
    slopes = [np.polyfit(tan[i], f.raw_along.values[i], 1)[0] for i in idx if np.ptp(tan[i]) > 0]
    res["vza_dependence"] = {"spearman_rho": float(rho), "spearman_p": float(p_rho), "slope_km_per_tan": slope,
                             "slope_ci": (float(np.percentile(slopes, 2.5)), float(np.percentile(slopes, 97.5))),
                             "expected_slope_for_pure_parallax_km": "about 10-12 (cloud-top height)"}

    cells = cell_table()
    for s in STATES:
        d = cells[cells.state == s]
        res["cells"][s] = {"cells": len(d), "cases": int(d.case.nunique()),
                           "median_km": float(d.along_km.median()),
                           "median_ci": cluster_boot(d, lambda x: x.along_km.median(), n, rng)}
    case_med = cells.groupby(["state", "case"]).along_km.median().unstack(0)
    for a, b in (("raw", "parallax"), ("raw", "both"), ("parallax", "both")):
        m = case_med[[a, b]].dropna()
        res["cells_paired"][f"{a}->{b}"] = {
            "cases": len(m), "median_case_change_km": float((m[b] - m[a]).median()),
            "median_case_change_ci": boot((m[b] - m[a]).values, np.median, n, rng),
            "wilcoxon_p_signed": float(stats.wilcoxon(m[a], m[b]).pvalue),
        }

    OUT.mkdir(parents=True, exist_ok=True)
    f.to_csv(OUT / "field_offsets_by_case.csv", index=False)
    (OUT / "statistics.json").write_text(json.dumps(res, indent=2))

    def ci(x):
        return f"[{x[0]:+.1f}, {x[1]:+.1f}]"

    print(f"Field measure, storm top 250 km, {len(f)} cases (bootstrap n={n}):")
    for s, lab in STATES.items():
        r = res["field"][s]
        print(f"  {lab:34s} median |offset| {r['median_abs_km']:.1f} {ci(r['median_abs_ci'])}  mean {r['mean_km']:+.1f} {ci(r['mean_ci'])}")
    print("Paired, change in |offset| (negative = better):")
    for k, r in res["field_paired"].items():
        print(f"  {k:28s} median {r['median_change_km']:+.1f} {ci(r['median_change_ci'])}  improved {r['improved']}/{r['cases']}"
              f"  Wilcoxon p={r['wilcoxon_p']:.3f}  sign p={r['sign_test_p']:.3f}")
    v = res["vza_dependence"]
    print(f"Raw offset vs tan(VZA): Spearman rho={v['spearman_rho']:+.2f} (p={v['spearman_p']:.2f}), slope {v['slope_km_per_tan']:+.1f} km {ci(v['slope_ci'])}")
    print("Cell measure (cluster bootstrap over cases):")
    for s, lab in STATES.items():
        r = res["cells"][s]
        print(f"  {lab:34s} median {r['median_km']:+.1f} {ci(r['median_ci'])}  ({r['cells']} cells, {r['cases']} cases)")
    for k, r in res["cells_paired"].items():
        print(f"  {k:28s} per-case median change {r['median_case_change_km']:+.1f} {ci(r['median_case_change_ci'])}"
              f"  Wilcoxon p={r['wilcoxon_p_signed']:.3f} ({r['cases']} cases)")
    print(f"wrote {OUT / 'statistics.json'}")


if __name__ == "__main__":
    main()
