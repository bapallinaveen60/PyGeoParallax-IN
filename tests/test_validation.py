import numpy as np
import pytest
import xarray as xr

from pygeoparallax import correct_scene
from pygeoparallax.geometry import parallax_correct, satellite_view_angles
from pygeoparallax.resample import Grid
from pygeoparallax.validation import (
    best_displacement,
    bias_sweep,
    compare,
    iou,
    monte_carlo_shift,
    mutual_information,
    nearest_time,
    pearson,
    points_to_grid,
    range_mask,
    regional_stats,
)
from pygeoparallax.validation.metrics import _shifted

RNG = np.random.default_rng(3)


def test_iou_and_pearson_basics():
    a = np.zeros((10, 10), bool)
    a[:5] = True
    assert iou(a, a) == 1.0
    assert iou(a, ~a) == 0.0
    b = np.zeros_like(a)
    b[:5, :5] = True
    assert iou(a, b) == pytest.approx(0.5)

    x = RNG.normal(size=(20, 20))
    assert pearson(x, 2 * x + 1) == pytest.approx(1.0)
    assert pearson(x, -x) == pytest.approx(-1.0)
    y = x.copy()
    y[0, 0] = np.nan
    assert np.isfinite(pearson(x, y))


def test_mutual_information_orders_dependence():
    x = RNG.normal(size=(100, 100))
    assert mutual_information(x, x, normalized=True) == pytest.approx(1.0)
    noisy = mutual_information(x, x + RNG.normal(size=x.shape), normalized=True)
    indep = mutual_information(x, RNG.normal(size=x.shape), normalized=True)
    assert 1.0 > noisy > indep >= 0.0
    assert indep < 0.05


def test_best_displacement_recovers_known_shift():
    field = RNG.normal(size=(40, 40))
    target = _shifted(field, 2, -3)
    dy, dx, r = best_displacement(field, target, max_lag=5)
    assert (dy, dx) == (2, -3)
    assert r == pytest.approx(1.0)


def test_correction_improves_alignment_with_radar():
    """Synthetic Agartala storm: correction should raise IoU and remove the offset."""
    lat0, lon0, res = 23.89, 91.24, 0.01
    lats = np.arange(lat0 - 1.0, lat0 + 1.0, res) + res / 2
    lons = np.arange(lon0 - 1.0, lon0 + 1.0, res) + res / 2
    lat, lon = np.meshgrid(lats, lons, indexing="ij")
    storm = np.hypot(lat - lat0, lon - lon0) < 0.25
    bt = np.where(storm, 205.0, 290.0)
    cth = np.where(storm, 14000.0, np.nan)
    grid = Grid(lat0 - 1.0, lat0 + 1.0, lon0 - 1.0, lon0 + 1.0, 0.02)

    # The radar sees the storm where it really is: the satellite's apparent position, corrected.
    t_lat, t_lon = parallax_correct(lat[storm], lon[storm], 14000.0, 74.0)
    radar = points_to_grid(grid, t_lat, t_lon, np.full(t_lat.size, 45.0))
    radar = np.where(np.isnan(radar), 0.0, radar)

    raw = correct_scene(lat, lon, {"TIR1": bt}, cth, grid=grid, correct=False)
    cor = correct_scene(lat, lon, {"TIR1": bt}, cth, grid=grid)
    m_raw = compare(raw["TIR1"].values, radar, 235.0, 20.0, max_lag=6)
    m_cor = compare(cor["TIR1"].values, radar, 235.0, 20.0, max_lag=6)

    assert m_cor["iou"] > 0.9 > m_raw["iou"]
    assert m_cor["pearson"] > m_raw["pearson"]
    assert (m_cor["lag_dy"], m_cor["lag_dx"]) == (0, 0)
    # Uncorrected imagery has to move south-west (towards the satellite) to match.
    assert m_raw["lag_dy"] > 0 and m_raw["lag_dx"] < 0


def test_points_to_grid_and_range_mask():
    grid = Grid(10.0, 11.0, 70.0, 71.0, 0.5)
    g = points_to_grid(grid, [10.9, 10.8, 10.1, 12.0], [70.1, 70.2, 70.9, 70.5], [10.0, 20.0, 5.0, 99.0])
    assert g[0, 0] == pytest.approx(15.0)
    assert g[1, 1] == pytest.approx(5.0)
    assert np.isnan(g[0, 1])
    gmax = points_to_grid(grid, [10.9, 10.8], [70.1, 70.2], [10.0, 20.0], how="max")
    assert gmax[0, 0] == 20.0

    fine = Grid(18.0, 20.0, 72.0, 74.0, 0.02)
    mask = range_mask(fine, 19.0, 73.0, 50.0)
    cell_area = (0.02 * 111.2) * (0.02 * 111.2 * np.cos(np.radians(19.0)))
    assert mask.sum() * cell_area == pytest.approx(np.pi * 50.0**2, rel=0.03)


def test_nearest_time():
    scans = np.array(["2023-07-01T06:00", "2023-07-01T06:30", "2023-07-01T07:00"], dtype="datetime64[m]")
    assert nearest_time(scans, np.datetime64("2023-07-01T06:41")) == 1
    assert nearest_time(scans, np.datetime64("2023-07-01T08:00")) == -1
    assert nearest_time(scans, np.datetime64("2023-07-01T08:00"), max_dt="1h") == 2


def test_regional_stats():
    lat = np.arange(0.0, 40.0, 1.0) + 0.5
    lon = np.arange(60.0, 100.0, 1.0) + 0.5
    glat, _ = np.meshgrid(lat, lon, indexing="ij")
    ds = xr.Dataset({"shift_km": (("lat", "lon"), glat / 4.0)}, coords={"lat": lat, "lon": lon})
    stats = regional_stats(ds, "shift_km")
    assert list(stats.index) == ["western_ghats", "himalayas", "northeast", "central_india"]
    # Shift grows northwards here, so the Himalayas should top the table.
    assert stats["mean"].idxmax() == "himalayas"
    assert (stats["n"] > 0).all()


def test_sensitivity_matches_tan_vza():
    lat, lon = np.array([19.13]), np.array([72.86])  # Mumbai
    vza, _ = satellite_view_angles(lat, lon, 74.0)
    expected_km = np.tan(np.radians(vza[0]))  # per km of CTH error
    mc = monte_carlo_shift(lat, lon, np.array([12000.0]), 74.0, sigma=1000.0, n=400)
    assert mc["position_rmse_km"][0] == pytest.approx(expected_km, rel=0.1)
    assert mc["shift_km"][0] == pytest.approx(12.0 * expected_km, rel=0.02)

    sweep = bias_sweep(lat, lon, np.array([12000.0]), 74.0)
    assert sweep.loc[1000.0, "mean_km"] == pytest.approx(expected_km, rel=0.02)
    assert sweep.loc[-2000.0, "mean_km"] == pytest.approx(2 * expected_km, rel=0.02)
