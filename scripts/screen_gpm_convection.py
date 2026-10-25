"""Screen GPM 2A Ku files for convection in the validation regions, before downloading INSAT.

For each GPM file, this reports the convective footprints and storm tops
inside the case region, and the size of the densest convective cluster (the
same measure ``run_all_cases.py`` uses). A case is worth downloading INSAT
for if its cluster has at least 100 convective footprints.

Usage:
    python scripts/screen_gpm_convection.py --dir <folder with GPM files> \
        --cases 00_Documentation/events/validation_gpm_batch2.csv
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np
import pandas as pd

from pygeoparallax.ingest import read_gpm_2a

REGION_BOX = {"northeast": (21, 29, 88, 97), "himalaya": (24, 33, 74, 90)}
MIN_CLUSTER = 100


def screen(path, box):
    g = read_gpm_2a(path, bbox=box)
    lat, lon = g["lat"].values, g["lon"].values
    inside = (lat >= box[0]) & (lat <= box[1]) & (lon >= box[2]) & (lon <= box[3])
    conv = (g["precip_type"].values == 2) & inside
    top = g["storm_top_height"].values
    out = {"convective": int(conv.sum()), "raining_pct": round(100 * float(((g["precip_type"].values > 0) & inside).sum()) / max(1, inside.sum()), 1),
           "storm_top_max_km": round(float(np.nanmax(np.where(conv, top, np.nan))) / 1000, 1) if conv.any() else 0.0,
           "cluster": 0, "cluster_lat": np.nan, "cluster_lon": np.nan}
    if conv.any():
        clat, clon = lat[conv], lon[conv]
        counts, ey, ex = np.histogram2d(clat, clon, bins=[np.arange(box[0], box[1] + 1), np.arange(box[2], box[3] + 1)])
        iy, ix = np.unravel_index(np.argmax(counts), counts.shape)
        y0, x0 = (ey[iy] + ey[iy + 1]) / 2, (ex[ix] + ex[ix + 1]) / 2
        near = np.hypot(clat - y0, (clon - x0) * np.cos(np.radians(y0))) < 1.35
        out.update(cluster=int(near.sum()), cluster_lat=round(float(clat[near].mean()), 2),
                   cluster_lon=round(float(clon[near].mean()), 2))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", required=True)
    ap.add_argument("--cases", default="00_Documentation/events/validation_gpm_batch2.csv")
    ap.add_argument("--out", default="00_Documentation/events/validation_gpm_batch2_screened.csv")
    args = ap.parse_args(argv)
    cases = pd.read_csv(args.cases)
    rows = []
    for _, c in cases.iterrows():
        hits = glob.glob(str(Path(args.dir) / "**" / c["granule"]), recursive=True)
        row = {"region": c["region"], "gpm_time_utc": c["gpm_time_utc"], "insat_scan": c["insat_l1c"][:20], "granule": c["granule"]}
        if not hits:
            row["verdict"] = "GPM file not found"
        else:
            row.update(screen(hits[0], REGION_BOX[c["region"]]))
            row["verdict"] = "download INSAT" if row["cluster"] >= MIN_CLUSTER else "skip (too little convection)"
        rows.append(row)
        print(f"{row['region']:9s} {row['gpm_time_utc'][:16]}  cluster {row.get('cluster', '-'):>4}  "
              f"tops {row.get('storm_top_max_km', '-')} km  -> {row['verdict']}", flush=True)
    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
