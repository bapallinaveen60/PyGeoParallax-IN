"""A self-contained demonstration and self-test, with no data downloads.

:func:`run_demo` builds a synthetic INSAT-3DR-like scene over Northeast India,
where the parallax is largest. Three storms with flat tops at known heights
(16, 12 and 8 km) sit at known true positions. The satellite view is simulated
exactly: each pixel's line of sight is traced, and the pixel shows the highest
storm top it meets. The scene is then corrected the normal way, with cloud-top
height derived from the brightness temperature, and the corrected storms are
compared with their true positions.

Run it with ``pygeoparallax demo`` or ``python -m pygeoparallax.demo``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr

from .cloudheight import TROPICAL, cloud_top_height
from .geometry.constants import SATELLITE_LONGITUDES
from .geometry.parallax import parallax_correct, parallax_shift
from .pipeline import correct_native
from .resample.native import mercator_lat, mercator_y

SAT_LON = SATELLITE_LONGITUDES["INSAT-3DR"]
PIXEL_KM = 4.0
EARTH_A_KM = 6378.137

#: True storm centres, flat-top heights and radii: (name, lat, lon, height [m], radius [km]).
STORMS = (
    ("deep storm near Agartala", 23.8, 91.3, 16000.0, 22.0),
    ("storm over Bangladesh", 24.5, 90.0, 12000.0, 18.0),
    ("shallow storm over West Bengal", 23.0, 89.0, 8000.0, 15.0),
)


def _grid(lat_top=25.3, lat_bottom=22.3, lon_west=88.2, lon_east=92.2):
    """Pixel centres regular in Mercator northing and longitude, like an L1C file (north to south)."""
    step = PIXEL_KM / EARTH_A_KM  # radians on the unit-radius Mercator plane
    y = np.arange(mercator_y(lat_top), mercator_y(lat_bottom), -step)
    lon = np.arange(lon_west, lon_east, np.degrees(step))
    return np.meshgrid(mercator_lat(y), lon, indexing="ij")


def temperature_at(height):
    """AFGL tropical temperature at ``height`` [m], for heights in the troposphere."""
    k = TROPICAL.tropopause_index
    return np.interp(height, TROPICAL.height[: k + 1], TROPICAL.temperature[: k + 1])


def simulate_scene(seed=0):
    """Apparent (uncorrected) TIR1 brightness temperature as the satellite sees the storms.

    Returns ``lat, lon, bt, truth`` where ``truth`` is an integer map of which
    storm (1, 2, 3) truly lies under each pixel centre, 0 for none.
    """
    rng = np.random.default_rng(seed)
    lat, lon = _grid()
    bt = 296.0 + rng.normal(0.0, 0.5, lat.shape)  # clear-sky surface
    best = np.full(lat.shape, -np.inf)
    truth = np.zeros(lat.shape, np.int8)
    for k, (_, clat, clon, height, radius) in enumerate(STORMS, start=1):
        # Where this pixel's line of sight crosses the storm's top height ...
        tlat, tlon = parallax_correct(lat, lon, np.full(lat.shape, height), SAT_LON)
        # ... is it inside the storm? Higher tops hide lower ones.
        dist_km, _ = parallax_shift(tlat, tlon, np.full(lat.shape, clat), np.full(lat.shape, clon))
        hit = (dist_km / 1000.0 <= radius) & (height > best)
        bt[hit] = temperature_at(height) + rng.normal(0.0, 0.5, hit.sum())
        best[hit] = height
        under, _ = parallax_shift(lat, lon, np.full(lat.shape, clat), np.full(lat.shape, clon))
        truth[under / 1000.0 <= radius] = k
    return lat, lon, bt, truth


def _offsets(lat, lon, bt, height_k, clat, clon, observed=None):
    """Distance [km] from the storm's true centre to the centroid of the pixels showing its top.

    ``observed`` restricts the corrected image to cells a pixel actually landed
    in (``fill_flag`` 0): gap-filled cells next to a moved storm carry
    interpolated cloud values and would pull the centroid back.
    """
    sel = np.abs(bt - temperature_at(height_k)) < 2.5
    if observed is not None:
        sel &= observed
    # Only pixels near this storm (other storms have other temperatures anyway).
    near, _ = parallax_shift(lat, lon, np.full(lat.shape, clat), np.full(lat.shape, clon))
    sel &= near / 1000.0 < 80.0
    if not sel.any():
        return np.nan
    d, _ = parallax_shift(lat[sel].mean(), lon[sel].mean(), clat, clon)
    return float(d) / 1000.0


def run_demo(out_dir="pygeoparallax_demo", plot=True, verbose=True):
    """Simulate, correct and check the synthetic scene; write NetCDF and (optionally) a figure.

    Returns a dict with, for each storm, its height, the offset of the
    uncorrected and corrected storm from its true position [km], and
    ``passed`` (every corrected storm within one pixel, 4 km, of its true position).
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    lat, lon, bt, truth = simulate_scene()

    cth = cloud_top_height(bt)  # the normal workflow: height from brightness temperature
    corrected = correct_native(lat, lon, {"TIR1": bt}, cth, sat_lon=SAT_LON, fill_empty=True)
    bt_c = corrected["TIR1"].values
    observed = corrected["fill_flag"].values == 0

    rows = []
    for name, clat, clon, height, _ in STORMS:
        rows.append({
            "storm": name, "height_km": height / 1000.0,
            "uncorrected_offset_km": _offsets(lat, lon, bt, height, clat, clon),
            "corrected_offset_km": _offsets(lat, lon, bt_c, height, clat, clon, observed),
        })
    passed = all(r["corrected_offset_km"] < PIXEL_KM for r in rows)

    scene = xr.Dataset({"TIR1": (("y", "x"), bt.astype(np.float32), {"units": "K"})},
                       coords={"lat": (("y", "x"), lat), "lon": (("y", "x"), lon)},
                       attrs={"title": "PyGeoParallax-IN synthetic demo scene (uncorrected)",
                              "sub_satellite_longitude": SAT_LON})
    scene.to_netcdf(out / "demo_uncorrected.nc")
    corrected.to_netcdf(out / "demo_corrected.nc")

    figure = None
    if plot:
        figure = _plot(lat, lon, bt, bt_c, corrected["shift_km"].values, out / "demo.png")

    if verbose:
        print("PyGeoParallax-IN demo: synthetic INSAT-3DR scene over Northeast India (satellite at 74 E)")
        print(f"{'storm':34s}{'top':>7s}{'uncorrected':>14s}{'corrected':>12s}")
        for r in rows:
            print(f"{r['storm']:34s}{r['height_km']:5.0f} km{r['uncorrected_offset_km']:11.1f} km"
                  f"{r['corrected_offset_km']:9.1f} km")
        print("offset = distance of the storm in the image from its true position (observed cells)")
        print(f"check: {'PASSED' if passed else 'FAILED'} (every corrected storm within {PIXEL_KM:.0f} km, one pixel)")
        print(f"wrote {out / 'demo_uncorrected.nc'}, {out / 'demo_corrected.nc'}"
              + (f", {figure}" if figure else ""))
    return {"storms": rows, "passed": passed, "out_dir": str(out), "figure": str(figure) if figure else None}


def _plot(lat, lon, bt, bt_c, shift, path):
    try:
        # The object-oriented API draws off-screen without changing the user's pyplot backend.
        from matplotlib.figure import Figure
    except ImportError:
        print("matplotlib not installed: no figure (pip install matplotlib)")
        return None

    fig = Figure(figsize=(15, 4.6), constrained_layout=True)
    ax = fig.subplots(1, 3)
    theta = np.linspace(0, 2 * np.pi, 100)
    for a, img, title in ((ax[0], bt, "As the satellite sees it"), (ax[1], bt_c, "After parallax correction")):
        im = a.pcolormesh(lon, lat, img, cmap="Greys", vmin=190, vmax=300, shading="auto")
        for _, clat, clon, _, radius in STORMS:  # true storm outlines
            a.plot(clon + np.degrees(radius / EARTH_A_KM * np.cos(theta)) / np.cos(np.radians(clat)),
                   clat + np.degrees(radius / EARTH_A_KM * np.sin(theta)), color="tab:red", lw=1.2)
        a.set_title(title)
    fig.colorbar(im, ax=ax[:2], label="10.8 µm brightness temperature [K]", shrink=0.9)
    im = ax[2].pcolormesh(lon, lat, np.where(np.isfinite(shift) & (shift > 0.1), shift, np.nan),
                          cmap="viridis", shading="auto")
    fig.colorbar(im, ax=ax[2], label="shift applied [km]", shrink=0.9)
    ax[2].set_title("How far each pixel was moved")
    for a in ax:
        a.set_xlabel("longitude [° E]")
        a.set_ylabel("latitude [° N]")
        a.set_aspect(1 / np.cos(np.radians(23.8)))
    fig.suptitle("Red circles: true storm positions. Correction moves the storms back onto them.")
    fig.savefig(path, dpi=110)
    return path


if __name__ == "__main__":
    import sys

    sys.exit(0 if run_demo()["passed"] else 1)
