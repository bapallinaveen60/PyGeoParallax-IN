"""Measure and correct INSAT geolocation errors by matching coastlines.

INSAT-3DR L1C positions can be off by up to ~15 km. The error changes with
time (≈0 on 6 Jun 2022, 8-15 km from Sep 2022) and with region (see
``00_Documentation/navigation_check.md``). It must therefore be measured for
each day or scan, not assumed. This module:

1. **Measures** the offset in coastal windows. Clear-sky VIS (daytime) or
   TIR1 is correlated with a land-fraction map from Natural Earth polygons
   blurred to the pixel footprint, over trial shifts
   (:func:`measure_window`, :func:`measure_scan`).
2. **Fits** a smooth correction field: inverse-distance weighting of the
   window offsets (:class:`NavigationCorrection`).
3. **Applies** the field per pixel:
   ``read_insat_l1c(..., position_offset_km=correction)``.

Offsets are the correction to **add** to INSAT positions to reach the true
ground location [km east, km north].

Land polygons: Natural Earth 10 m land (public domain), e.g.
https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

KM_PER_DEG = 111.2

#: Coastal windows (lat_min, lat_max, lon_min, lon_max) with long, simple coastlines.
WINDOWS = {
    "kutch": (22.0, 23.8, 68.3, 70.8),
    "saurashtra": (20.0, 23.0, 68.5, 71.8),
    "konkan": (17.5, 20.5, 71.5, 74.0),
    "goa_karnataka": (13.5, 16.5, 72.5, 75.5),
    "kerala": (8.0, 11.5, 74.5, 77.5),
    "sri_lanka": (5.8, 10.0, 79.0, 82.2),
    "chennai": (12.0, 14.5, 79.0, 81.0),
    "andhra": (15.0, 17.8, 80.0, 83.0),
    "odisha": (19.0, 22.0, 85.0, 88.0),
    "andaman": (10.5, 13.8, 92.0, 93.6),
    "rakhine": (16.5, 20.5, 92.5, 95.5),
}


def load_land(path):
    """Union of all land polygons in a GeoJSON file (e.g. Natural Earth 10 m land)."""
    import shapely
    from shapely.geometry import shape

    features = json.loads(Path(path).read_text())["features"]
    return shapely.union_all([shape(f["geometry"]) for f in features])


def land_fraction_interpolator(land, bbox, pixel_km=4.0, fine=0.005, pad=0.5):
    """Expected land fraction of a ``pixel_km`` pixel, as a function of (lat, lon).

    The land polygons are rasterised at ``fine`` degrees and box-filtered to
    the pixel size, then wrapped in a bilinear interpolator.
    """
    import shapely
    from scipy.interpolate import RegularGridInterpolator
    from scipy.ndimage import uniform_filter
    from shapely.geometry import box

    lat_min, lat_max, lon_min, lon_max = bbox
    lats = np.arange(lat_min - pad, lat_max + pad, fine)
    lons = np.arange(lon_min - pad, lon_max + pad, fine)
    region = shapely.intersection(land, box(lons[0], lats[0], lons[-1], lats[-1]))
    shapely.prepare(region)
    glon, glat = np.meshgrid(lons, lats)
    mask = shapely.contains_xy(region, glon, glat).astype(float)
    size = max(1, int(round(pixel_km / KM_PER_DEG / fine)))
    frac = uniform_filter(mask, size=size, mode="nearest")
    return RegularGridInterpolator((lats, lons), frac, bounds_error=False, fill_value=np.nan)


def _corr(a, b):
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / den) if den > 0 else np.nan


def measure_window(lat, lon, image, interp, sign=1.0, clear=None, max_km=30.0, coarse_km=2.0,
                   fine_km=0.5, min_pixels=300, min_side=50):
    """Best coastline shift for one window.

    Parameters
    ----------
    lat, lon, image : ndarray
        Pixel positions and the image to match (e.g. VIS albedo).
    interp : callable
        From :func:`land_fraction_interpolator`.
    sign : float
        +1 if land is brighter/warmer than sea in ``image``, -1 if darker/colder.
    clear : ndarray of bool, optional
        Pixels to use (clear sky). Defaults to all finite pixels.
    max_km, coarse_km, fine_km : float
        Search range, coarse step, and refinement step around the coarse best.

    Returns
    -------
    dict or None
        ``east_km``, ``north_km``, ``r_best``, ``r_zero``, ``on_edge`` and pixel
        counts. None if there are too few clear land or sea pixels.
    """
    image = np.asarray(image, float)
    use = np.isfinite(image) if clear is None else (np.asarray(clear, bool) & np.isfinite(image))
    la, lo, v = np.asarray(lat)[use], np.asarray(lon)[use], sign * image[use]
    ref0 = interp(np.stack([la, lo], -1))
    ok = np.isfinite(ref0)
    n_land = int((ref0[ok] > 0.9).sum())
    n_sea = int((ref0[ok] < 0.1).sum())
    if ok.sum() < min_pixels or n_land < min_side or n_sea < min_side:
        return None
    la, lo, v = la[ok], lo[ok], v[ok]
    coslat = np.cos(np.radians(la.mean()))

    def score(de, dn):
        ref = interp(np.stack([la + dn / KM_PER_DEG, lo + de / (KM_PER_DEG * coslat)], -1))
        good = np.isfinite(ref)
        return _corr(v[good], ref[good])

    coarse = np.arange(-max_km, max_km + coarse_km / 2, coarse_km)
    best = max(((score(de, dn), de, dn) for dn in coarse for de in coarse), key=lambda t: t[0])
    _, de0, dn0 = best
    fine = np.arange(-coarse_km, coarse_km + fine_km / 2, fine_km)
    best = max(((score(de0 + a, dn0 + b), de0 + a, dn0 + b) for b in fine for a in fine), key=lambda t: t[0])
    r_best, de, dn = best
    return {
        "east_km": float(de), "north_km": float(dn),
        "r_best": float(r_best), "r_zero": float(score(0.0, 0.0)),
        "on_edge": bool(max(abs(de), abs(dn)) >= max_km),
        "clear_pixels": int(ok.sum()), "land": n_land, "sea": n_sea,
    }


def measure_scan(path, land, windows=None, interps=None, **kwargs):
    """Measure the coastline offset in every usable window of one L1C file.

    Daytime windows (sun zenith < 75 deg) use VIS albedo; night windows use
    TIR1 with land colder than sea. Returns a list of dicts, one per window
    with enough clear land and sea, including ``window``, ``lat``/``lon``
    (window centre) and ``scan``.
    """
    from .geometry import solar_angles
    from .ingest.insat import read_insat_l1c

    windows = WINDOWS if windows is None else windows
    out = []
    for name, bbox in windows.items():
        interp = interps[name] if interps and name in interps else land_fraction_interpolator(land, bbox)
        ds = read_insat_l1c(path, channels=("TIR1", "VIS"), bbox=bbox)
        centre = ((bbox[0] + bbox[1]) / 2, (bbox[2] + bbox[3]) / 2)
        sza, _ = solar_angles(np.datetime64(ds.attrs["time"]), *centre)
        tir, vis = ds["TIR1"].values, ds["VIS"].values
        if sza < 75.0:
            res = measure_window(ds["lat"].values, ds["lon"].values, vis, interp, 1.0,
                                 (vis < 30.0) & (tir > 285.0), **kwargs)
            channel = "VIS"
        else:
            res = measure_window(ds["lat"].values, ds["lon"].values, tir, interp, -1.0, tir > 285.0, **kwargs)
            channel = "TIR1"
        if res is not None:
            res.update({"window": name, "lat": centre[0], "lon": centre[1], "channel": channel,
                        "sza": float(sza), "scan": ds.attrs["product"], "time": ds.attrs["time"]})
            out.append(res)
    return out


@dataclass
class NavigationCorrection:
    """Smooth navigation correction from offsets measured at a few points.

    The correction at any position is the inverse-distance-weighted mean of
    the point offsets (weights ``1 / d**power``, with ``d`` in km). It reduces
    to the nearest measurement close to a window, and to a weighted mean far
    from all of them.
    """

    lat: np.ndarray
    lon: np.ndarray
    east_km: np.ndarray
    north_km: np.ndarray
    power: float = 2.0
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        self.lat, self.lon, self.east_km, self.north_km = (
            np.asarray(a, float).ravel() for a in (self.lat, self.lon, self.east_km, self.north_km)
        )
        if self.lat.size == 0:
            raise ValueError("a navigation correction needs at least one measured point")

    @classmethod
    def from_matches(cls, matches, min_r=0.6, power=2.0):
        """Build from :func:`measure_scan` results (one or several scans).

        Weak (r < ``min_r``) and edge-of-search matches are dropped. Several
        matches for the same window (e.g. from several scans of a day) are
        combined by their median.
        """
        good = [m for m in matches if m["r_best"] >= min_r and not m["on_edge"]]
        by_window = {}
        for m in good:
            by_window.setdefault(m["window"], []).append(m)
        if not by_window:
            raise ValueError("no usable coastline matches (all weak, at the search edge, or cloudy)")
        rows = [
            (np.median([m["lat"] for m in ms]), np.median([m["lon"] for m in ms]),
             np.median([m["east_km"] for m in ms]), np.median([m["north_km"] for m in ms]), name, len(ms))
            for name, ms in sorted(by_window.items())
        ]
        lat, lon, e, n, names, counts = zip(*rows)
        return cls(lat, lon, e, n, power=power,
                   meta={"windows": list(names), "matches_per_window": list(counts), "min_r": min_r,
                         "scans": sorted({m["scan"] for m in good})})

    def __call__(self, lat, lon):
        """Correction (east_km, north_km) at the given positions."""
        lat = np.asarray(lat, float)
        lon = np.asarray(lon, float)
        shape = np.broadcast(lat, lon).shape
        flat_lat = np.broadcast_to(lat, shape).ravel()
        flat_lon = np.broadcast_to(lon, shape).ravel()
        east = np.empty(flat_lat.size)
        north = np.empty(flat_lat.size)
        p2 = np.radians(self.lat)
        chunk = 500_000  # bounds memory to chunk x n_points
        for s in range(0, flat_lat.size, chunk):
            p1 = np.radians(flat_lat[s:s + chunk])[:, None]
            dl = np.radians(flat_lon[s:s + chunk])[:, None] - np.radians(self.lon)
            a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
            d = 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
            w = 1.0 / np.maximum(d, 1.0) ** self.power
            w /= w.sum(axis=1, keepdims=True)
            east[s:s + chunk] = w @ self.east_km
            north[s:s + chunk] = w @ self.north_km
        return east.reshape(shape), north.reshape(shape)

    def to_json(self, path):
        Path(path).write_text(json.dumps({
            "lat": self.lat.tolist(), "lon": self.lon.tolist(),
            "east_km": self.east_km.tolist(), "north_km": self.north_km.tolist(),
            "power": self.power, "meta": self.meta,
        }, indent=2))

    @classmethod
    def from_json(cls, path):
        d = json.loads(Path(path).read_text())
        return cls(d["lat"], d["lon"], d["east_km"], d["north_km"], power=d.get("power", 2.0), meta=d.get("meta", {}))
