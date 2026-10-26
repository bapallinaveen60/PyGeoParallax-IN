"""Compare Model A (uncorrected input) and Model B (parallax-corrected input) on the test patches.

Reads ``<runs>/<task>_A`` and ``<runs>/<task>_B`` (``train_unet_ab.py``). Both
are scored on the same pixels, and the B - A differences are tested with a
paired bootstrap that resamples whole scenes (patches of one INSAT/GPM pair
stay together).

Reported metrics: accuracy, macro F1, and per-class F1 and CSI. They are given
for the full test split, for its validation subset, and for the test-only
remainder.

Writes ``<runs>/comparison_<task>.json`` and prints a table.

Usage:
    python scripts/compare_unet_ab.py --runs <runs folder> --task fourclass
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

N_BOOT = 2000


def metrics(cm, classes):
    tp = np.diag(cm).astype(float)
    fp, fn = cm.sum(0) - tp, cm.sum(1) - tp
    with np.errstate(invalid="ignore", divide="ignore"):
        prec, rec = tp / (tp + fp), tp / (tp + fn)
        f1 = 2 * prec * rec / (prec + rec)
        csi = tp / (tp + fp + fn)
    out = {"accuracy": tp.sum() / cm.sum(), "macro_f1": np.nanmean(f1)}
    for k, c in enumerate(classes):
        out[f"F1 {c}"], out[f"CSI {c}"] = f1[k], csi[k]
    return out


def compare(cm_a, cm_b, scenes, classes, seed=2026):
    a, b = metrics(cm_a.sum(0), classes), metrics(cm_b.sum(0), classes)
    uniq, inv = np.unique(scenes, return_inverse=True)
    sa = np.stack([cm_a[inv == s].sum(0) for s in range(len(uniq))])
    sb = np.stack([cm_b[inv == s].sum(0) for s in range(len(uniq))])
    rng = np.random.default_rng(seed)
    boot = {k: [] for k in a}
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(uniq), len(uniq))
        ma, mb = metrics(sa[idx].sum(0), classes), metrics(sb[idx].sum(0), classes)
        for k in a:
            boot[k].append(mb[k] - ma[k])
    rows = {}
    for k in a:
        d = np.array(boot[k])
        d = d[np.isfinite(d)]
        p = 2 * min((d <= 0).mean(), (d >= 0).mean()) if len(d) else np.nan
        rows[k] = {"A": float(a[k]), "B": float(b[k]), "B_minus_A": float(b[k] - a[k]),
                   "ci95": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))] if len(d) else None,
                   "p_two_sided": float(min(p, 1.0))}
    return {"scenes": int(len(uniq)), "patches": int(len(scenes)), "metrics": rows}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--runs", required=True)
    ap.add_argument("--task", required=True)
    args = ap.parse_args(argv)

    runs = Path(args.runs)
    ra, rb = (np.load(runs / f"{args.task}_{m}" / "test_confusion_by_patch.npz") for m in "AB")
    assert np.array_equal(ra["patches"], rb["patches"]), "A and B were scored on different patches"
    classes = list(json.loads((runs / f"{args.task}_A" / "test_metrics.json").read_text())["per_class"])
    names, scenes, in_val = ra["patches"], ra["scene"], ra["in_val"]

    result = {"task": args.task}
    for label, sel in (("test", np.ones(len(names), bool)), ("val_subset", in_val), ("test_only", ~in_val)):
        result[label] = compare(ra["confusion"][sel], rb["confusion"][sel], scenes[sel], classes)
        r = result[label]
        print(f"\n{args.task}, {label}: {r['patches']} patches, {r['scenes']} scenes (scene bootstrap, n={N_BOOT})")
        print(f"  {'metric':<24}{'A':>8}{'B':>8}{'B-A':>9}   95% interval       p")
        for k, m in r["metrics"].items():
            ci = m["ci95"] or [np.nan, np.nan]
            print(f"  {k:<24}{m['A']:8.4f}{m['B']:8.4f}{m['B_minus_A']:+9.4f}   [{ci[0]:+.4f}, {ci[1]:+.4f}]  {m['p_two_sided']:.3f}")
    out = runs / f"comparison_{args.task}.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
