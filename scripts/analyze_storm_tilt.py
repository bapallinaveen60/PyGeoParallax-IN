"""Tilt of monsoon convective cells from GPM Ku-band 3-D reflectivity, along the INSAT line of sight.

Section 6.2 of the paper explains why uncorrected INSAT cold cores already sit
on the GPM deep-echo cells: the coldest top of a cell would have to lie, on
average, a parallax-sized distance towards the satellite from the echo below
it. This script measures how far the radar echo itself leans in that direction.

For each usable validation case:

1. Read the GPM 2A Ku profiles (``SLV/zFactorFinal``) near the convective
   cluster, with the height of every range bin (``PRE/height``). Each bin is
   placed on its slanted beam with the spacecraft position, so a tilted beam
   is not mistaken for a tilted storm.
2. Deep convective cells are connected footprints with storm top > 10 km
   (at least ``--min-footprints``), grown by ``--grow`` footprints so that a
   leaning upper part is not cut off.
3. In each cell, the reflectivity-weighted centroid is found in height layers:
   the low-level core (2-4 km, Z >= ``--core-dbz``) and each upper layer
   (Z >= ``--echo-dbz``), plus the echo top (the top 1 km of echo in each
   column).
4. The displacement of each upper centroid from the low-level core is split
   into along-look (positive = towards the satellite at 74 E) and cross-look
   components.

If storms lean towards the satellite by a distance comparable to the parallax,
the parallax displacement (away from the satellite) moves the cold top back
over the rain, which is what the cell measure sees.

Writes ``05_validation/gpm_colocation/storm_tilt_cells.csv`` (per cell and
layer) and ``storm_tilt.csv`` (per case), and prints a summary.

Usage:
    python scripts/analyze_storm_tilt.py --base <validation folder>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
import run_all_cases  # noqa: E402
import run_validation_case as rvc  # noqa: E402

from pygeoparallax.geometry import satellite_view_angles  # noqa: E402
from pygeoparallax.ingest.gpm import along_beam  # noqa: E402

#: Layers [km]: name -> (bottom, top). "top" (the echo top) is handled separately.
LAYERS = {"low": (2.0, 4.0), "mid": (5.0, 7.0), "upper": (8.0, 10.0), "high": (11.0, 13.0)}
SAT_LON = 74.0


def read_profiles(path, bbox, pad=1.0):
    """Footprints, storm tops, precipitation type and 3-D reflectivity for the scans crossing ``bbox``."""
    with h5py.File(path, "r") as f:
        g = f["FS"]
        lat = g["Latitude"][:].astype(float)
        lon = g["Longitude"][:].astype(float)
        lat_min, lat_max, lon_min, lon_max = bbox
        inside = (lat >= lat_min - pad) & (lat <= lat_max + pad) & (lon >= lon_min - pad) & (lon <= lon_max + pad)
        scans = np.flatnonzero(inside.any(axis=1))
        sel = slice(int(scans[0]), int(scans[-1]) + 1)
        z = g["SLV/zFactorFinal"][sel].astype(float)
        h = g["PRE/height"][sel].astype(float)
        top = g["PRE/heightStormTop"][sel].astype(float)
        sc = g["navigation/scPos"][sel].astype(float)
        ptype = g["CSF/typePrecip"][sel]
    z[(z < 0) | (z > 80)] = np.nan            # fill (-9999.9, -28888) and no echo
    h[h < -1000] = np.nan
    top[top < 0] = np.nan
    ptype = np.where(ptype > 0, ptype // 10_000_000, 0)
    return lat[sel], lon[sel], top, ptype, z, h, sc


def weighted_centroid(blat, blon, z):
    """Reflectivity-weighted (linear Z) centroid of bins; NaN if fewer than 3 bins."""
    ok = np.isfinite(z) & np.isfinite(blat)
    if ok.sum() < 3:
        return np.nan, np.nan, 0
    w = 10.0 ** (z[ok] / 10.0)
    return float(np.sum(w * blat[ok]) / w.sum()), float(np.sum(w * blon[ok]) / w.sum()), int(ok.sum())


def along_cross(a, b, vaa):
    """Displacement from a to b [km] as (along-look towards the satellite, cross-look)."""
    dn = (b[0] - a[0]) * 111.2
    de = (b[1] - a[1]) * 111.2 * np.cos(np.radians(a[0]))
    t = np.radians(vaa)
    return de * np.sin(t) + dn * np.cos(t), de * np.cos(t) - dn * np.sin(t)


def analyse_case(path, bbox, centre, radius_km, min_fp, grow, core_dbz, echo_dbz):
    lat, lon, top, ptype, z, h, sc = read_profiles(path, bbox)
    d = np.hypot(lat - centre[0], (lon - centre[1]) * np.cos(np.radians(centre[0]))) * 111.2
    deep = (np.nan_to_num(top) > 10000) & (d <= radius_km)
    labels, n = ndimage.label(deep)
    rows = []
    for lab in range(1, n + 1):
        cell = labels == lab
        if cell.sum() < min_fp:
            continue
        area = ndimage.binary_dilation(cell, iterations=grow) if grow else cell
        si, ri = np.nonzero(area)
        zc, hc = z[si, ri, :], h[si, ri, :]                         # (columns, bins)
        sc_b = np.broadcast_to(sc[si][:, None, :], zc.shape + (3,))
        lat_b = np.broadcast_to(lat[si, ri][:, None], zc.shape)
        lon_b = np.broadcast_to(lon[si, ri][:, None], zc.shape)
        use = np.isfinite(zc) & np.isfinite(hc) & (hc > 1500)
        blat = np.full(zc.shape, np.nan)
        blon = np.full(zc.shape, np.nan)
        blat[use], blon[use] = along_beam(lat_b[use], lon_b[use], hc[use], sc_b[use])
        cen = {}
        for name, (lo, hi) in LAYERS.items():
            thr = core_dbz if name == "low" else echo_dbz
            m = (hc >= lo * 1000) & (hc <= hi * 1000) & (zc >= thr)
            cen[name] = weighted_centroid(np.where(m, blat, np.nan), np.where(m, blon, np.nan), np.where(m, zc, np.nan))
        # Echo top: in each column, the bins within 1 km below the highest bin with Z >= echo_dbz.
        echo = np.where(zc >= echo_dbz, hc, np.nan)
        col_top = np.nanmax(np.where(np.isfinite(echo), echo, -np.inf), axis=1)
        mt = np.isfinite(echo) & (echo >= col_top[:, None] - 1000) & (col_top[:, None] > 10000)
        cen["top"] = weighted_centroid(np.where(mt, blat, np.nan), np.where(mt, blon, np.nan), np.where(mt, zc, np.nan))
        low = cen["low"]
        if not np.isfinite(low[0]):
            continue
        _, vaa = satellite_view_angles(low[0], low[1], SAT_LON)
        row = {"cell_lat": round(low[0], 3), "cell_lon": round(low[1], 3), "footprints": int(cell.sum()),
               "storm_top_max_km": round(float(np.nanmax(top[cell])) / 1000, 2), "vaa_deg": round(float(vaa), 1),
               "convective_fraction": round(float((ptype[cell] == 2).mean()), 2)}
        for name in ("mid", "upper", "high", "top"):
            c = cen[name]
            if np.isfinite(c[0]):
                al, cr = along_cross(low, c[:2], float(vaa))
                row[f"{name}_along_km"], row[f"{name}_cross_km"] = round(al, 2), round(cr, 2)
                dn = (c[0] - low[0]) * 111.2
                de = (c[1] - low[1]) * 111.2 * np.cos(np.radians(low[0]))
                row[f"{name}_east_km"], row[f"{name}_north_km"] = round(de, 2), round(dn, 2)
            row[f"{name}_bins"] = c[2]
        rows.append(row)
    return rows


def cluster_boot(df, col, n=5000, seed=2026):
    """Median of ``col`` over cells with a 95 % interval from resampling whole cases."""
    rng = np.random.default_rng(seed)
    groups = [g[col].dropna().values for _, g in df.groupby("case")]
    groups = [g for g in groups if g.size]
    meds = [np.median(np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))]))
            for _ in range(n)]
    allv = np.concatenate(groups)
    return float(np.median(allv)), float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5)), len(groups), allv.size


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True, help="validation folder with one sub-folder per case")
    ap.add_argument("--radius", type=float, default=250.0, help="km around the GPM convective cluster")
    ap.add_argument("--min-footprints", type=int, default=2, help="smallest deep cell, in GPM footprints")
    ap.add_argument("--grow", type=int, default=2, help="footprints added around each deep cell")
    ap.add_argument("--core-dbz", type=float, default=30.0, help="reflectivity threshold of the low-level core")
    ap.add_argument("--echo-dbz", type=float, default=20.0, help="reflectivity threshold in the upper layers")
    ap.add_argument("--cases", nargs="+", help="only these cases (default: all usable)")
    args = ap.parse_args(argv)

    table = pd.read_csv("05_validation/gpm_colocation/all_cases.csv")
    usable = table[(table.nav == "no_nav") & table.status.str.startswith("usable")]
    cases = args.cases or usable["case"].tolist()
    all_rows = []
    for case in cases:
        region = case.split("_")[0]
        box = run_all_cases.REGION_BOX[region]
        path = rvc.find(Path(args.base) / case, "2A.GPM.*")
        from pygeoparallax.resample import Grid

        centre = rvc.gpm_on_grid(path, Grid(*box, res=0.02), box)["conv_centre"]
        rows = analyse_case(path, box, centre, args.radius, args.min_footprints, args.grow,
                            args.core_dbz, args.echo_dbz)
        for r in rows:
            r.update(case=case, region=region)
        all_rows += rows
        if rows:
            df = pd.DataFrame(rows)
            print(f"{case:22s} cells {len(rows):3d}  along-look tilt (towards satellite), median: "
                  + "  ".join(f"{k} {df[f'{k}_along_km'].median():+5.1f}" for k in ("mid", "upper", "high", "top")
                              if f"{k}_along_km" in df), flush=True)
        else:
            print(f"{case:22s} no deep cells", flush=True)

    cells = pd.DataFrame(all_rows)
    out = Path("05_validation/gpm_colocation")
    cells.to_csv(out / "storm_tilt_cells.csv", index=False)
    per_case = cells.groupby(["case", "region"]).agg(
        cells=("cell_lat", "size"), **{f"{k}_along_median": (f"{k}_along_km", "median") for k in ("mid", "upper", "high", "top")},
        **{f"{k}_east_median": (f"{k}_east_km", "median") for k in ("upper", "top")},
        **{f"{k}_north_median": (f"{k}_north_km", "median") for k in ("upper", "top")}).reset_index()
    per_case.to_csv(out / "storm_tilt.csv", index=False)

    print(f"\n{len(cells)} cells in {cells.case.nunique()} cases. Displacement from the 2-4 km core, "
          "median with 95 % interval (cluster bootstrap over cases):")
    for k, lab in (("mid", "5-7 km"), ("upper", "8-10 km"), ("high", "11-13 km"), ("top", "echo top")):
        for comp in ("along", "cross", "east", "north"):
            col = f"{k}_{comp}_km"
            if col in cells:
                m, lo, hi, nc, nv = cluster_boot(cells, col)
                print(f"  {lab:9s} {comp:5s} {m:+5.1f} km  [{lo:+5.1f}, {hi:+5.1f}]  ({nv} cells, {nc} cases)")
    print("\nEcho-top along-look tilt by region (median of cells):")
    for reg, g in cells.groupby("region"):
        print(f"  {reg:10s} {g['top_along_km'].median():+5.1f} km  ({len(g)} cells, {g.case.nunique()} cases)")
    print(f"wrote {out / 'storm_tilt_cells.csv'} and {out / 'storm_tilt.csv'}")


if __name__ == "__main__":
    main()
