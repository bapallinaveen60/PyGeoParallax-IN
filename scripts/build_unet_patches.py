"""Parallax-corrected copies of the U-Net training patches (Model B), on the patches' own pixel grid.

The U-Net patches (``U_net_info/data_trs/BT_patches``) are 128 x 128 tiles of
the INSAT-3DR L1C Mercator grid. Each holds four BT channels (TIR1, TIR2, WV,
MIR), ``bt_norm = (bt - 180) / 150`` and the GPM DPR precipitation type matched
to each pixel's *navigated* position. GPM positions are on the ground, so the
labels are already at ground positions. Only the INSAT input is displaced by
parallax, and only the input changes between Model A and Model B.

Processing per scene (all tiles of one INSAT/GPM pair):

1. Mosaic the tiles at their (i, j) offsets. The grid is regular in Mercator y
   and longitude, fitted from the tiles' lat/lon.
2. Cloud-top height from TIR1 with the AFGL tropical profile. The patches carry
   no clear-sky BT, so cloudy means BT < 270 K.
3. Parallax-correct every pixel (ellipsoid ray tracing, INSAT-3DR at 74 E).
   Then bucket-resample onto the same pixel grid, as in the main pipeline:
   the highest pixel wins, and one-cell IDW fill.
4. Cut the tiles back out.

Cells the satellite never saw, or whose source pixels fall in tiles that were
not kept, stay empty (fill_flag 2). Their input is filled with the nearest
corrected value so the U-Net gets a complete image. ``ignore`` marks them, and
the training script drops their labels in *both* A and B, so the two models are
scored on the same pixels.

Writes ``<out>/<split>/<patch>.npz`` (``bt`` corrected, ``fill_flag``,
``shift_km``, ``ignore``) for the train and test folders. Validation patches are
a subset of test. Also writes ``<out>/manifest.csv`` with per-patch shift and
ignore statistics. Existing outputs are kept, so an interrupted run resumes.

Usage:
    python scripts/build_unet_patches.py --patches U_net_info/data_trs/BT_patches \
        --out D:/Projects/@GeoVision/Insat_data/unet_patches/corrected [-j 6]
"""

from __future__ import annotations

import argparse
import multiprocessing
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage

from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.geometry.constants import SATELLITE_LONGITUDES
from pygeoparallax.geometry.parallax import parallax_correct, parallax_shift
from pygeoparallax.resample import EMPTY, Grid
from pygeoparallax.resample.bucket import resample

SPLITS = ("final_patches_train", "final_patches_test")
CHANNELS = ("TIR1", "TIR2", "WV", "MIR")  # order in the patches, checked against the matched L1C file
TILE = 128


E = 0.0818191908426  # WGS84 eccentricity


def merc_y(lat):
    """Ellipsoidal (WGS84) Mercator northing on the unit sphere scale."""
    phi = np.radians(lat)
    es = E * np.sin(phi)
    return np.log(np.tan(np.pi / 4 + phi / 2) * ((1 - es) / (1 + es)) ** (E / 2))


def merc_lat(y, iterations=6):
    """Inverse of :func:`merc_y`."""
    t = np.exp(-y)
    phi = np.pi / 2 - 2 * np.arctan(t)
    for _ in range(iterations):
        es = E * np.sin(phi)
        phi = np.pi / 2 - 2 * np.arctan(t * ((1 - es) / (1 + es)) ** (E / 2))
    return np.degrees(phi)


def process_scene(scene, tiles, out):
    """Correct one scene. ``tiles`` is a list of (split, path); returns manifest rows."""
    t0 = time.perf_counter()
    data = [(split, path, np.load(path)) for split, path in tiles]
    nrow = max(int(d["i"]) for _, _, d in data) + TILE
    ncol = max(int(d["j"]) for _, _, d in data) + TILE

    # Grid: Mercator y linear in row, longitude linear in column (pixel centres).
    rows, ys, cols, lons = [], [], [], []
    for _, _, d in data:
        i, j = int(d["i"]), int(d["j"])
        rows.append(i + np.arange(TILE))
        ys.append(merc_y(d["lat"][:, 0].astype(float)))
        cols.append(j + np.arange(TILE))
        lons.append(d["lon"][0, :].astype(float))
    ay = np.polyfit(np.concatenate(rows), np.concatenate(ys), 1)
    al = np.polyfit(np.concatenate(cols), np.concatenate(lons), 1)

    bt = np.full((4, nrow, ncol), np.nan)
    for _, _, d in data:
        i, j = int(d["i"]), int(d["j"])
        bt[:, i:i + TILE, j:j + TILE] = d["bt"]
    rr, cc = np.mgrid[0:nrow, 0:ncol]
    lat = merc_lat(np.polyval(ay, rr))
    lon = np.polyval(al, cc)

    have = np.isfinite(bt[0])
    cth = cloud_top_height(bt[0])
    height = np.where(np.isfinite(cth), cth, 0.0)
    lat_c, lon_c = parallax_correct(lat[have], lon[have], height[have], SATELLITE_LONGITUDES["INSAT-3DR"])
    shift, _ = parallax_shift(lat[have], lon[have], lat_c, lon_c)

    # Corrected positions as fractional pixel coordinates; a 1-pixel "grid" in index space.
    row_f = (merc_y(lat_c) - ay[1]) / ay[0] + 0.5
    col_f = (lon_c - al[1]) / al[0] + 0.5
    grid = Grid(lat_min=-nrow, lat_max=0.0, lon_min=0.0, lon_max=ncol, res=1.0)
    values = {c: bt[k][have] for k, c in enumerate(CHANNELS)}
    values["shift_km"] = shift / 1000.0
    ds = resample(grid, -row_f, col_f, height[have], values, fill_radius=1)

    fill = ds["fill_flag"].values
    cor = np.stack([ds[c].values for c in CHANNELS])
    empty = (fill == EMPTY) | ~np.isfinite(cor[0])
    if empty.any():  # nearest corrected value, input only
        idx = ndimage.distance_transform_edt(empty, return_distances=False, return_indices=True)
        cor = cor[:, idx[0], idx[1]]
    shift_g = ds["shift_km"].values

    rows_out = []
    for split, path, d in data:
        i, j = int(d["i"]), int(d["j"])
        sl = (slice(i, i + TILE), slice(j, j + TILE))
        ign = empty[sl]
        dst = out / split.replace("final_patches_", "") / path.name
        np.savez_compressed(dst, bt=cor[(slice(None),) + sl].astype(np.float32), fill_flag=fill[sl].astype(np.uint8),
                            shift_km=np.nan_to_num(shift_g[sl]).astype(np.float16), ignore=ign)
        lab = d["precip_type"]
        cloudy = np.isfinite(cth[sl])
        s = shift_g[sl]
        rows_out.append({
            "patch": path.name, "split": split.replace("final_patches_", ""), "scene": scene,
            "frac_cloudy": float(cloudy.mean()),
            "shift_median_km": float(np.nanmedian(s[cloudy])) if cloudy.any() else 0.0,
            "shift_p95_km": float(np.nanpercentile(s[cloudy], 95)) if cloudy.any() else 0.0,
            "frac_ignore": float(ign.mean()),
            "labels_valid": int((lab != -99).sum()),
            "labels_ignored": int(((lab != -99) & ign).sum()),
            "frac_tir1_changed_1K": float((np.abs(cor[0][sl] - d["bt"][0]) > 1.0).mean()),
            "seconds": time.perf_counter() - t0,
        })
    return rows_out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--patches", required=True, help="BT_patches folder")
    ap.add_argument("--out", required=True)
    ap.add_argument("-j", "--jobs", type=int, default=max(1, multiprocessing.cpu_count() // 2))
    ap.add_argument("--limit", type=int, help="process only the first N scenes (testing)")
    args = ap.parse_args(argv)

    out = Path(args.out)
    scenes = defaultdict(list)
    for split in SPLITS:
        (out / split.replace("final_patches_", "")).mkdir(parents=True, exist_ok=True)
        for p in sorted((Path(args.patches) / split).glob("*.npz")):
            scenes[p.name.rsplit("_patch_", 1)[0]].append((split, p))
    todo = {s: t for s, t in sorted(scenes.items())
            if not all((out / sp.replace("final_patches_", "") / p.name).exists() for sp, p in t)}
    if args.limit:
        todo = dict(list(todo.items())[:args.limit])
    print(f"{len(scenes)} scenes, {sum(map(len, scenes.values()))} patches; {len(todo)} scenes to do", flush=True)

    manifest = out / "manifest.csv"
    old = pd.read_csv(manifest) if manifest.exists() else pd.DataFrame()
    rows, t0 = [], time.perf_counter()
    with ProcessPoolExecutor(args.jobs) as ex:
        futs = {ex.submit(process_scene, s, t, out): s for s, t in todo.items()}
        for n, f in enumerate(as_completed(futs), 1):
            try:
                rows += f.result()
            except Exception as e:  # keep going; the scene is retried on the next run
                print(f"{futs[f]}: FAILED {e}", flush=True)
            if n % 50 == 0 or n == len(futs):
                print(f"{n}/{len(futs)} scenes, {time.perf_counter() - t0:.0f} s", flush=True)
    new = pd.concat([old, pd.DataFrame(rows)]).drop_duplicates(["patch", "split"], keep="last")
    new.to_csv(manifest, index=False)
    print(f"wrote {manifest} ({len(new)} patches)")
    if len(new):
        print(new[["shift_median_km", "shift_p95_km", "frac_ignore", "frac_tir1_changed_1K"]].describe().round(3).to_string())
        print(f"labels ignored: {new.labels_ignored.sum()} of {new.labels_valid.sum()} "
              f"({new.labels_ignored.sum() / max(new.labels_valid.sum(), 1):.2%})")


if __name__ == "__main__":
    main()
