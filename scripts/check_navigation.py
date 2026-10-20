"""Check INSAT-3DR L1C geolocation against the Natural Earth 10 m coastline.

For each coastal window and each scan:

1. Rasterise the land polygons at 0.005 deg and blur them to the ~4 km
   INSAT pixel footprint, giving each pixel an expected land fraction.
2. Keep clear-sky pixels only (daytime: low VIS albedo or warm TIR1;
   night: warm TIR1).
3. Shift the coastline by trial offsets (east/north, 1 km steps) and correlate
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
import shapely
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import uniform_filter
from shapely.geometry import box, shape

from pygeoparallax.geometry import solar_angles
from pygeoparallax.ingest import read_insat_l1c

#: Coastal windows (lat_min, lat_max, lon_min, lon_max) with long, simple coastlines.
WINDOWS = {
    "saurashtra": (20.0, 23.0, 68.5, 71.8),
    "konkan": (17.5, 20.5, 71.5, 74.0),
    "goa_karnataka": (13.5, 16.5, 72.5, 75.5),
    "kerala": (8.0, 11.5, 74.5, 77.5),
    "sri_lanka": (5.8, 10.0, 79.0, 82.2),
    "andhra": (15.0, 17.8, 80.0, 83.0),
    "odisha": (19.0, 22.0, 85.0, 88.0),
}
FINE = 0.005  # deg, coastline raster
PIXEL_KM = 4.0
MAX_KM = 20
KM_PER_DEG = 111.2


def land_fraction_interpolator(land, bbox, pad=0.5):
    lat_min, lat_max, lon_min, lon_max = bbox
    lats = np.arange(lat_min - pad, lat_max + pad, FINE)
    lons = np.arange(lon_min - pad, lon_max + pad, FINE)
    region = shapely.intersection(land, box(lons[0], lats[0], lons[-1], lats[-1]))
    shapely.prepare(region)
    glon, glat = np.meshgrid(lons, lats)
    mask = shapely.contains_xy(region, glon, glat).astype(float)
    size = max(1, int(round(PIXEL_KM / KM_PER_DEG / FINE)))
    frac = uniform_filter(mask, size=size, mode="nearest")
    return RegularGridInterpolator((lats, lons), frac, bounds_error=False, fill_value=np.nan)


def corr(a, b):
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / den) if den > 0 else np.nan


def match_window(ds, interp, day):
    lat = ds["lat"].values
    lon = ds["lon"].values
    tir = ds["TIR1"].values
    vis = ds["VIS"].values if "VIS" in ds else None
    if day and vis is not None:
        clear = (vis < 30.0) & (tir > 285.0)
        img, sign = vis, 1.0
    else:
        clear = tir > 285.0
        img, sign = tir, (1.0 if day else -1.0)
    clear &= np.isfinite(img)
    ref0 = interp(np.stack([lat[clear], lon[clear]], -1))
    ok = np.isfinite(ref0)
    n_land = int((ref0[ok] > 0.9).sum())
    n_sea = int((ref0[ok] < 0.1).sum())
    if ok.sum() < 300 or n_land < 50 or n_sea < 50:
        return None
    la, lo, v = lat[clear][ok], lon[clear][ok], sign * img[clear][ok]
    coslat = np.cos(np.radians(la.mean()))
    offsets = np.arange(-MAX_KM, MAX_KM + 1, 1.0)
    surface = np.full((offsets.size, offsets.size), np.nan)
    for i, dn in enumerate(offsets):
        for j, de in enumerate(offsets):
            # True position = INSAT position + (de, dn): sample the coastline there.
            ref = interp(np.stack([la + dn / KM_PER_DEG, lo + de / (KM_PER_DEG * coslat)], -1))
            good = np.isfinite(ref)
            surface[i, j] = corr(v[good], ref[good])
    i, j = np.unravel_index(np.nanargmax(surface), surface.shape)
    zero = surface[MAX_KM, MAX_KM]
    return {
        "east_km": float(offsets[j]), "north_km": float(offsets[i]),
        "r_best": float(surface[i, j]), "r_zero": float(zero),
        "on_edge": bool(i in (0, offsets.size - 1) or j in (0, offsets.size - 1)),
        "clear_pixels": int(ok.sum()), "land": n_land, "sea": n_sea,
        "channel": "VIS" if (day and vis is not None) else "TIR1",
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default="datasets")
    ap.add_argument("--land", default="01_raw_data/natural_earth/ne_10m_land.geojson")
    ap.add_argument("--out", default="05_validation/navigation_check.json")
    ap.add_argument("--min-r", type=float, default=0.5, help="ignore matches weaker than this")
    args = ap.parse_args(argv)

    features = json.loads(Path(args.land).read_text())["features"]
    land = shapely.union_all([shape(f["geometry"]) for f in features])
    interps = {name: land_fraction_interpolator(land, bbox) for name, bbox in WINDOWS.items()}

    files = sorted(glob.glob(str(Path(args.data) / "**" / "3RIMG_*_L1C_SGP_*.h5"), recursive=True))
    rows = []
    for path in files:
        for name, bbox in WINDOWS.items():
            try:
                ds = read_insat_l1c(path, channels=("TIR1", "VIS"), bbox=bbox)
            except OSError as exc:  # e.g. a truncated download
                print(f"skip {Path(path).name}: {exc}")
                break
            centre = ((bbox[0] + bbox[1]) / 2, (bbox[2] + bbox[3]) / 2)
            sza, _ = solar_angles(np.datetime64(ds.attrs["time"]), *centre)
            res = match_window(ds, interps[name], day=bool(sza < 75.0))
            if res is None:
                continue
            res.update({"scan": ds.attrs["product"], "window": name, "sza": float(sza)})
            rows.append(res)
            flag = "" if res["r_best"] >= args.min_r and not res["on_edge"] else "  (weak/edge, ignored)"
            print(f"{res['scan']:28s} {name:14s} {res['channel']:4s} "
                  f"E {res['east_km']:+5.0f} km  N {res['north_km']:+5.0f} km  "
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
