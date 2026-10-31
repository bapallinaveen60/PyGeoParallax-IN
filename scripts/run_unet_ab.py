"""Train and compare all U-Net A/B models on a GPU machine, one after another.

Runs ``train_unet_ab.py`` for each task and model (four-class, stratiform /
convective, rain / no-rain; A and B), each with its own log file, then
``compare_unet_ab.py`` for every task whose A and B runs are both finished,
and ``plot_unet_curves.py``. Finished runs are skipped and interrupted ones
resume from their last epoch, so the script can simply be started again.

Usage (from the folder that holds ``scripts/`` and ``data/``):
    python scripts/run_unet_ab.py [--tasks fourclass stratconv rain] [--models A B] [--epochs 100]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS = ["fourclass", "stratconv", "rain"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default=str(HERE.parent / "data"), help="folder with train.npz and test.npz")
    ap.add_argument("--out", default=str(HERE.parent / "runs"), help="runs folder")
    ap.add_argument("--tasks", nargs="+", default=TASKS, choices=TASKS)
    ap.add_argument("--models", nargs="+", default=["A", "B"], choices=["A", "B"])
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--max-train", type=int, help="first N training patches only (quick test)")
    args = ap.parse_args(argv)

    out = Path(args.out)
    logs = out / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    for task in args.tasks:
        for model in args.models:
            if (out / f"{task}_{model}" / "test_metrics.json").exists():
                print(f"{task} {model}: finished, skipped", flush=True)
                continue
            log = logs / f"{task}_{model}.log"
            print(f"{task} {model}: training (log: {log})", flush=True)
            t0 = time.time()
            cmd = [sys.executable, str(HERE / "train_unet_ab.py"), "--model", model, "--task", task,
                   "--data", args.data, "--out", str(out), "--epochs", str(args.epochs)]
            if args.max_train:
                cmd += ["--max-train", str(args.max_train)]
            with open(log, "a", encoding="utf-8") as f:
                rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT)
            print(f"{task} {model}: exit {rc} after {(time.time() - t0) / 3600:.1f} h", flush=True)
            if rc != 0:
                print(f"  see {log}; run this script again to resume", flush=True)
                return rc

    for task in args.tasks:
        if all((out / f"{task}_{m}" / "test_metrics.json").exists() for m in "AB"):
            subprocess.call([sys.executable, str(HERE / "compare_unet_ab.py"), "--runs", str(out), "--task", task])
    subprocess.call([sys.executable, str(HERE / "plot_unet_curves.py"), "--runs", str(out)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
