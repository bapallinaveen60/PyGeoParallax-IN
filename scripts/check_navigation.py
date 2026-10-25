"""Check INSAT-3DR L1C geolocation against the Natural Earth 10 m coastline.

For each coastal window and each scan:

1. Rasterise the land polygons at 0.005 deg and blur them to the ~4 km
   INSAT pixel footprint, giving each pixel an expected land fraction.
2. Keep clear-sky pixels only (daytime: low VIS albedo or warm TIR1;
   night: warm TIR1).
3. Shift the coastline by trial offsets (2 km steps, refined to 0.5 km) and correlate
   the INSAT image with the expected land fraction. Land is brighter in VIS and
   warmer in daytime TIR1, but colder at night, so the sign is set by sun angle.
4. The best-matching offset is the geolocation error. It is reported as the
   correction to *add* to INSAT positions to reach the true ground location.

Usage:
    python scripts/check_navigation.py --data datasets --land 01_raw_data/natural_earth/ne_10m_land.geojson
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np

from pygeoparallax.geometry import solar_angles
from pygeoparallax.ingest import read_insat_l1c
from pygeoparallax.navigation import EAST_ONLY, WINDOWS, land_fraction_interpolator, load_land, measure_window


def match_window(ds, interp, day, east_only=False):
    tir = ds["TIR1"].values
    vis = ds["VIS"].values if "VIS" in ds else None
    if day and vis is not None:
        res = measure_window(ds["lat"].values, ds["lon"].values, vis, interp, 1.0, (vis < 30.0) & (tir > 285.0),
                             east_only=east_only)
        channel = "VIS"
    else:
        res = measure_window(ds["lat"].values, ds["lon"].values, tir, interp, 1.0 if day else -1.0, tir > 285.0,
                             east_only=east_only)
        channel = "TIR1"
    if res is not None:
        res["channel"] = channel
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default="datasets")
    ap.add_argument("--land", default="01_raw_data/natural_earth/ne_10m_land.geojson")
    ap.add_argument("--out", default="05_validation/navigation_check.json")
    ap.add_argument("--min-r", type=float, default=0.5, help="ignore matches weaker than this")
    ap.add_argument("--offset", nargs=2, type=float, metavar=("EAST_KM", "NORTH_KM"),
                    help="apply this position correction first; the result is then the residual error")
    ap.add_argument("--files", default="3RIMG_*_L1C_SGP_*.h5", help="glob for L1C files under --data")
    ap.add_argument("--windows", nargs="+", choices=list(WINDOWS), help="only these windows")
    args = ap.parse_args(argv)

    land = load_land(args.land)
    windows = {k: v for k, v in WINDOWS.items() if not args.windows or k in args.windows}
    interps = {name: land_fraction_interpolator(land, bbox) for name, bbox in windows.items()}

    files = sorted(glob.glob(str(Path(args.data) / "**" / args.files), recursive=True))
    rows = []
    for path in files:
        for name, bbox in windows.items():
            try:
                ds = read_insat_l1c(path, channels=("TIR1", "VIS"), bbox=bbox, position_offset_km=args.offset)
            except OSError as exc:  # e.g. a truncated download
                print(f"skip {Path(path).name}: {exc}")
                break
            centre = ((bbox[0] + bbox[1]) / 2, (bbox[2] + bbox[3]) / 2)
            sza, _ = solar_angles(np.datetime64(ds.attrs["time"]), *centre)
            res = match_window(ds, interps[name], day=bool(sza < 75.0), east_only=name in EAST_ONLY)
            if res is None:
                continue
            res.update({"scan": ds.attrs["product"], "window": name, "sza": float(sza)})
            rows.append(res)
            flag = "" if res["r_best"] >= args.min_r and not res["on_edge"] else "  (weak/edge, ignored)"
            print(f"{res['scan']:28s} {name:14s} {res['channel']:4s} "
                  f"E {res['east_km']:+6.1f} km  N {res['north_km']:+6.1f} km  "
                  f"r {res['r_zero']:.2f} -> {res['r_best']:.2f}  n={res['clear_pixels']}{flag}")

    good = [r for r in rows if r["r_best"] >= args.min_r and not r["on_edge"]]
    summary = {"matches": rows, "used": len(good)}
    if good:
        e = np.array([r["east_km"] for r in good])
        n = np.array([r["north_km"] for r in good])
        summary.update({
            "median_east_km": float(np.median(e)), "median_north_km": float(np.median(n)),
            "iqr_east_km": [float(np.percentile(e, 25)), float(np.percentile(e, 75))],
            "iqr_north_km": [float(np.percentile(n, 25)), float(np.percentile(n, 75))],
            "by_window": {
                w: {"n": int(sum(r["window"] == w for r in good)),
                    "median_east_km": float(np.median([r["east_km"] for r in good if r["window"] == w])),
                    "median_north_km": float(np.median([r["north_km"] for r in good if r["window"] == w]))}
                for w in sorted({r["window"] for r in good})
            },
        })
        print(f"\n{len(good)} good matches: median correction E {summary['median_east_km']:+.1f} km, "
              f"N {summary['median_north_km']:+.1f} km "
              f"(IQR E {summary['iqr_east_km']}, N {summary['iqr_north_km']})")
        for w, s in summary["by_window"].items():
            print(f"  {w:14s} n={s['n']:2d}  E {s['median_east_km']:+.1f}  N {s['median_north_km']:+.1f}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
