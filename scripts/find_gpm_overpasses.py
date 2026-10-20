"""Find GPM-DPR (2A.DPR) overpasses near the IMD Doppler Weather Radar sites.

Queries NASA's public CMR catalogue (no Earthdata login needed) for 2A.DPR
orbit granules whose swath passes within ``--radius-km`` of each radar, then
estimates the overpass time and nadir distance from the granule's swath
polygons. The output CSV is the candidate list used to pick validation events
and to request matching INSAT-3DR / ERA5 / IMD data.

The overpass time is interpolated along the swath centre line, assuming a
constant ground speed through the orbit, which is accurate to about a minute.
Use it to choose INSAT-3DR scan slots, and read the exact scan time from the
2A.DPR file once it is downloaded.

Example
-------
    python scripts/find_gpm_overpasses.py --years 2022 2023 2024 \
        --out 00_Documentation/events/gpm_overpasses_jjas_2022_2024.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

CMR_GRANULES = "https://cmr.earthdata.nasa.gov/search/granules.json"
CMR_COLLECTIONS = "https://cmr.earthdata.nasa.gov/search/collections.json"
EARTH_RADIUS_KM = 6371.0
# The Ku-band DPR swath is ~245 km wide, so a site within this distance of nadir is inside the swath.
DPR_HALF_SWATH_KM = 122.5

# Approximate IMD S-band DWR locations (lat, lon). Verify against IMD metadata
# before using them for colocation.
RADAR_SITES = {
    "mumbai": (19.13, 72.86),
    "goa": (15.49, 73.82),
    "kochi": (9.96, 76.29),
    "agartala": (23.89, 91.24),
}

JJAS = ("06-01T00:00:00Z", "09-30T23:59:59Z")


def _get_json(url: str, params: dict, headers: dict | None = None):
    req = urllib.request.Request(
        url + "?" + urllib.parse.urlencode(params, doseq=True), headers=headers or {}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp), resp.headers


def collection_id(short_name: str, version: str) -> str:
    data, _ = _get_json(CMR_COLLECTIONS, {"short_name": short_name, "version": version})
    entries = data["feed"]["entry"]
    if not entries:
        sys.exit(f"No CMR collection found for {short_name} v{version}")
    return entries[0]["id"]


def search_granules(concept_id: str, temporal: str, lat: float, lon: float, radius_km: float):
    """Yield every granule intersecting a circle, following CMR search-after paging."""
    params = {
        "collection_concept_id": concept_id,
        "temporal": temporal,
        "circle": f"{lon},{lat},{radius_km * 1000:.0f}",
        "page_size": 2000,
        "sort_key": "start_date",
    }
    headers = {}
    while True:
        data, resp_headers = _get_json(CMR_GRANULES, params, headers)
        entries = data["feed"]["entry"]
        yield from entries
        after = resp_headers.get("CMR-Search-After")
        if not entries or not after:
            return
        headers = {"CMR-Search-After": after}


def _haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def swath_centreline(polygons) -> list[tuple[float, float]]:
    """Centre line of the swath as (lat, lon) points, in along-track order.

    CMR stores each GPM orbit as consecutive quadrilaterals ``lat lon`` x5 (closed);
    vertices 0/3 are the trailing edge and 1/2 the leading edge of each segment.
    """
    line = []
    for poly in polygons:
        nums = [float(v) for v in poly[0].split()]
        pts = list(zip(nums[0::2], nums[1::2]))
        if len(pts) < 4:
            continue
        for a, b in ((pts[0], pts[3]), (pts[1], pts[2])):
            lat = (a[0] + b[0]) / 2
            # Average longitudes across the dateline correctly.
            dlon = ((b[1] - a[1] + 180) % 360) - 180
            lon = ((a[1] + dlon / 2 + 180) % 360) - 180
            line.append((lat, lon))
    return line


def estimate_overpass(entry: dict, lat: float, lon: float):
    """Return (overpass time, distance of the site from nadir in km)."""
    line = swath_centreline(entry.get("polygons", []))
    if len(line) < 2:
        return None, None
    # Densify so the nearest centre-line point is within ~2 km of the true closest approach.
    dense = []
    for (la1, lo1), (la2, lo2) in zip(line, line[1:]):
        dlon = ((lo2 - lo1 + 180) % 360) - 180
        n = max(1, int(_haversine_km(la1, lo1, la2, lo2) / 2))
        dense.extend((la1 + (la2 - la1) * i / n, lo1 + dlon * i / n) for i in range(n))
    dense.append(line[-1])

    cum = [0.0]
    for (la1, lo1), (la2, lo2) in zip(dense, dense[1:]):
        cum.append(cum[-1] + _haversine_km(la1, lo1, la2, lo2))
    dists = [_haversine_km(lat, lon, la, lo) for la, lo in dense]
    i = min(range(len(dists)), key=dists.__getitem__)

    t0 = datetime.fromisoformat(entry["time_start"].replace("Z", "+00:00"))
    t1 = datetime.fromisoformat(entry["time_end"].replace("Z", "+00:00"))
    t = t0 + (t1 - t0) * (cum[i] / cum[-1])
    return t, dists[i]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=[2022, 2023, 2024])
    ap.add_argument("--sites", nargs="+", default=list(RADAR_SITES), choices=list(RADAR_SITES))
    ap.add_argument("--radius-km", type=float, default=150.0,
                    help="search radius around each radar (S-band DWR range is ~250 km)")
    ap.add_argument("--version", default="08", help="2A.DPR product version")
    ap.add_argument("--out", default="gpm_overpasses.csv")
    args = ap.parse_args(argv)

    concept = collection_id("GPM_2ADPR", args.version)
    rows = []
    for site in args.sites:
        lat, lon = RADAR_SITES[site]
        for year in args.years:
            temporal = f"{year}-{JJAS[0]},{year}-{JJAS[1]}"
            n = 0
            for g in search_granules(concept, temporal, lat, lon, args.radius_km):
                t, d = estimate_overpass(g, lat, lon)
                if t is None:
                    continue
                https = next((l["href"] for l in g.get("links", [])
                              if l["href"].startswith("https://data.")), "")
                rows.append({
                    "site": site,
                    "site_lat": lat,
                    "site_lon": lon,
                    "overpass_utc": t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "nadir_dist_km": round(d, 1),
                    "site_in_swath": d <= DPR_HALF_SWATH_KM,
                    "orbit": g["producer_granule_id"].split(".")[-3],
                    "granule": g["producer_granule_id"],
                    "url": https,
                })
                n += 1
            print(f"{site:9s} {year}: {n} overpasses", file=sys.stderr)

    rows.sort(key=lambda r: (r["site"], r["overpass_utc"]))
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["site"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
