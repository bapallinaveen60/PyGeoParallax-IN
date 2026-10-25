"""Find GPM Ku passes over high-VZA regions with an INSAT-3DR scan close in time.

For each GPM orbit whose swath centre line crosses a region box during the
monsoon "summer navigation state" (1 Jun – 20 Sep):

1. Take the part of the swath centre line inside the box, and the time GPM
   spent there (interpolated along the orbit).
2. Estimate when an INSAT-3DR full-disk scan reaches that latitude. Scans start
   at HH:15 and HH:45 and sweep north to south from 81N to 81S in ~26.9 min
   (from the L1C start/end attributes).
3. Keep crossings within ``--max-dt`` minutes of an INSAT scan.

The output CSV is the candidate list. Whether a case has convection is only
known after downloading the GPM file (`precip_type`, `storm_top_height`).

Usage:
    python scripts/find_validation_cases.py --years 2022 2023 2024 --out 00_Documentation/events/validation_candidates.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import find_gpm_overpasses as gpm  # noqa: E402

from pygeoparallax.geometry import satellite_view_angles  # noqa: E402

#: High-VZA validation regions (lat_min, lat_max, lon_min, lon_max).
REGIONS = {
    "northeast": (22.0, 29.0, 89.0, 97.0),  # Assam, Meghalaya, Tripura, Bangladesh east; VZA ~33-37
    "himalaya": (27.0, 33.0, 75.0, 89.0),  # Uttarakhand, Himachal, Nepal; VZA ~31-38
    "central": (19.0, 26.0, 76.0, 85.0),  # Madhya Pradesh, Chhattisgarh, Vidarbha; VZA ~21-30
    "south": (8.0, 17.0, 74.0, 80.5),  # Kerala, Karnataka, Tamil Nadu, Western Ghats; VZA ~9-20
}
SEASON = ("06-01T00:00:00Z", "09-20T23:59:59Z")  # summer yaw-flip state only
SCAN_MIN = 26.9  # full-disk scan duration [min]
SCAN_LAT = (81.0, -81.0)
SAT_LON = 74.0


def insat_time_at(lat, scan_start):
    frac = (SCAN_LAT[0] - lat) / (SCAN_LAT[0] - SCAN_LAT[1])
    return scan_start + timedelta(minutes=SCAN_MIN * frac)


def nearest_insat_scan(t, lat):
    """Scan start (HH:15 or HH:45) whose pass over ``lat`` is closest to ``t``; returns (start, dt_min)."""
    base = t.replace(minute=0, second=0, microsecond=0)
    starts = [base + timedelta(minutes=m) for m in (-45, -15, 15, 45, 75)]
    best = min(starts, key=lambda s: abs((t - insat_time_at(lat, s)).total_seconds()))
    return best, (t - insat_time_at(lat, best)).total_seconds() / 60.0


def crossing(entry, box):
    """Centre-line points inside ``box`` with times; None if the centre line misses the box."""
    line = gpm.swath_centreline(entry.get("polygons", []))
    if len(line) < 2:
        return None
    dense = []
    for (la1, lo1), (la2, lo2) in zip(line, line[1:]):
        dlon = ((lo2 - lo1 + 180) % 360) - 180
        n = max(1, int(gpm._haversine_km(la1, lo1, la2, lo2) / 2))
        dense.extend((la1 + (la2 - la1) * i / n, lo1 + dlon * i / n) for i in range(n))
    dense.append(line[-1])
    cum = np.concatenate([[0.0], np.cumsum([gpm._haversine_km(*a, *b) for a, b in zip(dense, dense[1:])])])
    lat = np.array([p[0] for p in dense])
    lon = np.array([p[1] for p in dense])
    inside = (lat >= box[0]) & (lat <= box[1]) & (lon >= box[2]) & (lon <= box[3])
    if not inside.any():
        return None
    t0 = datetime.fromisoformat(entry["time_start"].replace("Z", "+00:00"))
    t1 = datetime.fromisoformat(entry["time_end"].replace("Z", "+00:00"))
    times = [t0 + (t1 - t0) * (c / cum[-1]) for c in cum]
    idx = np.flatnonzero(inside)
    mid = idx[len(idx) // 2]
    return {
        "t_in": times[idx[0]], "t_out": times[idx[-1]], "t_mid": times[mid],
        "lat": float(lat[mid]), "lon": float(lon[mid]), "track_km": float(cum[idx[-1]] - cum[idx[0]]),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=[2022, 2023, 2024])
    ap.add_argument("--regions", nargs="+", default=list(REGIONS), choices=list(REGIONS))
    ap.add_argument("--max-dt", type=float, default=5.0, help="max |GPM - INSAT| time at the crossing [min]")
    ap.add_argument("--product", default="GPM_2AKu")
    ap.add_argument("--version", default="08")
    ap.add_argument("--out", default="00_Documentation/events/validation_candidates.csv")
    args = ap.parse_args(argv)

    concept = gpm.collection_id(args.product, args.version)
    rows = []
    for region in args.regions:
        box = REGIONS[region]
        for year in args.years:
            temporal = f"{year}-{SEASON[0]},{year}-{SEASON[1]}"
            centre_lat, centre_lon = (box[0] + box[1]) / 2, (box[2] + box[3]) / 2
            radius = gpm._haversine_km(box[0], box[2], box[1], box[3]) / 2
            n_pass = 0
            for e in gpm.search_granules(concept, temporal, centre_lat, centre_lon, radius):
                c = crossing(e, box)
                if c is None:
                    continue
                n_pass += 1
                start, dt = nearest_insat_scan(c["t_mid"], c["lat"])
                if abs(dt) > args.max_dt:
                    continue
                vza, _ = satellite_view_angles(c["lat"], c["lon"], SAT_LON)
                stamp = start.strftime("%d%b%Y_%H%M").upper()
                rows.append({
                    "region": region,
                    "gpm_time_utc": c["t_mid"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "dt_min_gpm_minus_insat": round(dt, 1),
                    "insat_l1c": f"3RIMG_{stamp}_L1C_SGP_V01R00.h5",
                    "insat_ctp": f"3RIMG_{stamp}_L2B_CTP_V01R00.h5",
                    "crossing_lat": round(c["lat"], 2),
                    "crossing_lon": round(c["lon"], 2),
                    "vza_deg": round(float(vza), 1),
                    "track_km_in_region": round(c["track_km"]),
                    "orbit": e["producer_granule_id"].split(".")[-3],
                    "granule": e["producer_granule_id"],
                    "url": next((l["href"] for l in e.get("links", []) if l["href"].startswith("https://data.")), ""),
                })
            print(f"{region:9s} {year}: {n_pass} crossings, "
                  f"{sum(r['region'] == region and r['gpm_time_utc'].startswith(str(year)) for r in rows)} within "
                  f"{args.max_dt:g} min of INSAT", file=sys.stderr)

    rows.sort(key=lambda r: (abs(r["dt_min_gpm_minus_insat"]), r["gpm_time_utc"]))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["region"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} candidates to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
