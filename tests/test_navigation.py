import numpy as np
import pytest
from shapely.geometry import Polygon

from pygeoparallax.ingest.insat import shift_positions
from pygeoparallax.navigation import NavigationCorrection, land_fraction_interpolator, measure_window

BBOX = (9.5, 12.5, 73.5, 77.0)


def _wavy_land():
    """Land east of a wavy coastline, so the coast constrains both east and north shifts."""
    lats = np.linspace(8.0, 14.0, 400)
    coast = 75.0 + 0.25 * np.sin(lats * 3.0)
    return Polygon(list(zip(coast, lats)) + [(80.0, 14.0), (80.0, 8.0)])


def test_measure_window_recovers_known_offset():
    interp = land_fraction_interpolator(_wavy_land(), BBOX)
    lat, lon = np.meshgrid(np.arange(9.6, 12.4, 0.036), np.arange(73.6, 76.9, 0.036), indexing="ij")
    true_east, true_north = -7.5, 3.0
    # The satellite reports positions that are off by -offset; the scene is what is really at lat/lon + offset.
    t_lat, t_lon = shift_positions(lat, lon, true_east, true_north)
    rng = np.random.default_rng(0)
    vis = 8.0 + 20.0 * interp(np.stack([t_lat, t_lon], -1)) + rng.normal(0, 0.5, lat.shape)

    res = measure_window(lat, lon, vis, interp)
    assert res["east_km"] == pytest.approx(true_east, abs=0.6)
    assert res["north_km"] == pytest.approx(true_north, abs=0.6)
    assert res["r_best"] > res["r_zero"]
    assert not res["on_edge"]

    # Too few clear pixels -> no estimate.
    assert measure_window(lat, lon, vis, interp, clear=np.zeros(lat.shape, bool)) is None


def _match(window, lat, lon, east, north, r=0.8, scan="S1", edge=False):
    return {"window": window, "lat": lat, "lon": lon, "east_km": east, "north_km": north,
            "r_best": r, "on_edge": edge, "scan": scan}


def test_navigation_correction_field(tmp_path):
    matches = [
        _match("konkan", 19.0, 73.0, 0.0, 0.0),
        _match("odisha", 20.5, 86.5, -15.0, 1.0),
        _match("odisha", 20.5, 86.5, -13.0, 1.0, scan="S2"),  # combined by median -> -14
        _match("kerala", 10.0, 76.0, 50.0, 50.0, r=0.2),  # weak: dropped
        _match("goa", 15.0, 74.0, 50.0, 50.0, edge=True),  # at search edge: dropped
    ]
    corr = NavigationCorrection.from_matches(matches)
    assert corr.meta["windows"] == ["konkan", "odisha"]
    e, n = corr(np.array([19.0, 20.5]), np.array([73.0, 86.5]))
    np.testing.assert_allclose(e, [0.0, -14.0], atol=0.05)
    np.testing.assert_allclose(n, [0.0, 1.0], atol=0.01)
    # Between the two windows the correction lies between their values.
    mid_e, _ = corr(19.75, 79.75)
    assert -14.0 < float(mid_e) < 0.0

    path = tmp_path / "nav.json"
    corr.to_json(path)
    again = NavigationCorrection.from_json(path)
    np.testing.assert_allclose(again(19.0, 73.0), corr(19.0, 73.0))

    with pytest.raises(ValueError):
        NavigationCorrection.from_matches([_match("x", 0, 0, 1, 1, r=0.1)])


def test_from_matches_quality_rules():
    matches = [
        _match("kutch", 23.0, 69.5, 4.0, 2.0, scan="0415"),
        _match("kutch", 23.0, 69.5, 6.0, 3.0, scan="0615"),  # agrees within 5 km: kept (median 5, 2.5)
        _match("andhra", 16.4, 81.5, 0.0, 2.0, scan="0415"),
        _match("andhra", 16.4, 81.5, -9.0, 12.0, scan="0615"),  # disagrees: window dropped
        _match("chennai", 13.2, 80.0, 3.0, 1.0, r=0.70),  # single scan, r < 0.75: dropped
        _match("sri_lanka", 7.9, 80.6, 2.0, 1.0, r=0.80),  # single scan, strong: kept
        _match("rakhine", 18.5, 94.0, 26.5, 28.0, r=0.71, scan="0415"),  # implausible: dropped
    ]
    corr = NavigationCorrection.from_matches(matches)
    assert corr.meta["windows"] == ["kutch", "sri_lanka"]
    np.testing.assert_allclose(corr.east_km, [5.0, 2.0])
    np.testing.assert_allclose(corr.north_km, [2.5, 1.0])
