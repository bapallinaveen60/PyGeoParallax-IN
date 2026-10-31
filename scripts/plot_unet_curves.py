"""Plot the training loss of the U-Net A/B runs (one panel per task).

Reads ``<runs>/<task>_<model>/history.json`` from ``train_unet_ab.py`` and
writes ``<runs>/training_curves.png``. Only the training loss is shown: the
test set is not used during training.

Usage:
    python scripts/plot_unet_curves.py --runs <runs folder>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

TASKS = ["fourclass", "stratconv", "rain"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--runs", required=True)
    args = ap.parse_args(argv)

    runs = Path(args.runs)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, task in zip(axes, TASKS):
        for model, color in (("A", "#888888"), ("B", "#2a78d6")):
            p = runs / f"{task}_{model}" / "history.json"
            if p.exists():
                h = json.loads(p.read_text())
                ax.plot(h["epoch"], h["loss"], color=color, label=f"Model {model}")
        ax.set_title(task)
        ax.set_xlabel("epoch")
        ax.set_ylabel("training loss")
        if ax.get_legend_handles_labels()[0]:
            ax.legend()
    fig.tight_layout()
    fig.savefig(runs / "training_curves.png", dpi=120)
    print(f"wrote {runs / 'training_curves.png'}")


if __name__ == "__main__":
    main()
