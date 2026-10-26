"""Pack the U-Net A/B patches into one file per split for training on Colab.

Reads the original patches (``U_net_info/data_trs/BT_patches``, Model A input
and labels) and the parallax-corrected copies (``build_unet_patches.py``,
Model B input). Writes ``<out>/train.npz`` and ``<out>/test.npz`` with:

- ``x_A``, ``x_B``: (N, 128, 128, 4) float16, ``(bt - 180) / 150`` clipped to [0, 1] as in
  the patches' ``bt_norm``, channels TIR1, TIR2, WV, MIR;
- ``precip_type``: (N, 128, 128) int8, the patches' GPM label, set to -99
  where the corrected field had no data, so that A and B are scored on the
  same pixels;
- ``scene``, ``patch``: names; ``in_val`` (test only): patch is also in the
  notebooks' validation folder.

float16 keeps the normalised BT to about 0.1 K.

Usage:
    python scripts/pack_unet_dataset.py --patches U_net_info/data_trs/BT_patches \
        --corrected D:/Projects/@GeoVision/Insat_data/unet_patches/corrected --out D:/Projects/@GeoVision/Insat_data/unet_colab/data
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def norm(bt):
    """The patches' bt_norm: (bt - 180) / 150 clipped to [0, 1]."""
    return np.clip((bt - 180.0) / 150.0, 0.0, 1.0)


def pack(patches, corrected, split, out):
    src = Path(patches) / f"final_patches_{split}"
    names = sorted(p.name for p in src.glob("*.npz"))
    n = len(names)
    x_a = np.empty((n, 128, 128, 4), np.float16)
    x_b = np.empty((n, 128, 128, 4), np.float16)
    y = np.empty((n, 128, 128), np.int8)
    for k, name in enumerate(names):
        d = np.load(src / name)
        c = np.load(Path(corrected) / split / name)
        x_a[k] = np.transpose(norm(d["bt"]), (1, 2, 0))
        x_b[k] = np.transpose(norm(c["bt"]), (1, 2, 0))
        lab = d["precip_type"].copy()
        lab[c["ignore"]] = -99
        y[k] = lab
    extra = {}
    if split == "test":
        val = {p.name for p in (Path(patches) / "final_patches_val").glob("*.npz")}
        extra["in_val"] = np.array([nm in val for nm in names])
    scene = np.array([nm.rsplit("_patch_", 1)[0] for nm in names])
    path = Path(out) / f"{split}.npz"
    np.savez(path, x_A=x_a, x_B=x_b, precip_type=y, patch=np.array(names), scene=scene, **extra)
    print(f"{path}: {n} patches, {len(set(scene))} scenes, {path.stat().st_size / 1e9:.2f} GB", flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--patches", required=True)
    ap.add_argument("--corrected", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    Path(args.out).mkdir(parents=True, exist_ok=True)
    for split in ("train", "test"):
        pack(args.patches, args.corrected, split, args.out)


if __name__ == "__main__":
    main()
