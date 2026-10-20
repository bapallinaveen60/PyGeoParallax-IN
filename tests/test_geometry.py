import numpy as np
import pytest
from pyproj import Transformer

from pygeoparallax.geometry.constants import GEO_RADIUS, SATELLITE_LONGITUDES, WGS84_A
from pygeoparallax.geometry.ecef import ecef_to_geodetic, geodetic_to_ecef
from pygeoparallax.geometry.viewing import satellite_view_angles, solar_angles

RNG = np.random.default_rng(42)
LAT = RNG.uniform(-89.0, 89.0, 500)
LON = RNG.uniform(-180.0, 180.0, 500)
H = RNG.uniform(-500.0, 20000.0, 500)  # sea-floor depressions up to deep-convection tops

INSAT_3DR = SATELLITE_LONGITUDES["INSAT-3DR"]


def test_geodetic_to_ecef_matches_pyproj():
    to_ecef = Transformer.from_crs("EPSG:4979", "EPSG:4978", always_xy=True)
    ref = to_ecef.transform(LON, LAT, H)
    ours = geodetic_to_ecef(LAT, LON, H)
    for a, b in zip(ours, ref):
        np.testing.assert_allclose(a, b, atol=1e-3)


def test_ecef_round_trip():
    lat, lon, h = ecef_to_geodetic(*geodetic_to_ecef(LAT, LON, H))
    np.testing.assert_allclose(lat, LAT, atol=1e-9)
    np.testing.assert_allclose(lon, LON, atol=1e-9)
    np.testing.assert_allclose(h, H, atol=1e-3)


def test_ecef_to_geodetic_handles_geostationary_altitude():
    lat, lon, h = ecef_to_geodetic(GEO_RADIUS, 0.0, 0.0)
    assert lat == pytest.approx(0.0, abs=1e-12)
    assert h == pytest.approx(GEO_RADIUS - WGS84_A, abs=1e-3)


def test_sub_satellite_point_is_at_zenith():
    vza, _ = satellite_view_angles(0.0, INSAT_3DR, INSAT_3DR)
    assert vza == pytest.approx(0.0, abs=1e-9)


def test_view_azimuth_directions():
    # North of the sub-satellite point the satellite is due south, and so on.
    _, north = satellite_view_angles(20.0, INSAT_3DR, INSAT_3DR)
    _, east = satellite_view_angles(0.0, INSAT_3DR + 20.0, INSAT_3DR)
    _, west = satellite_view_angles(0.0, INSAT_3DR - 20.0, INSAT_3DR)
    assert north == pytest.approx(180.0)
    assert east == pytest.approx(270.0)
    assert west == pytest.approx(90.0)


def test_satellite_angles_match_pyorbital():
    orbital = pytest.importorskip("pyorbital.orbital")
    lat = RNG.uniform(-60.0, 60.0, 200)
    lon = RNG.uniform(INSAT_3DR - 60.0, INSAT_3DR + 60.0, 200)
    time = np.datetime64("2023-07-15T06:00:00")
    sat_alt_km = (GEO_RADIUS - WGS84_A) / 1000.0
    azi, elev = orbital.get_observer_look(
        np.full_like(lat, INSAT_3DR), np.zeros_like(lat), np.full_like(lat, sat_alt_km),
        time, lon, lat, np.zeros_like(lat),
    )
    vza, vaa = satellite_view_angles(lat, lon, INSAT_3DR)
    np.testing.assert_allclose(vza, 90.0 - elev, atol=0.01)
    dazi = (vaa - azi + 180.0) % 360.0 - 180.0
    np.testing.assert_allclose(dazi, 0.0, atol=0.01)


def test_solar_angles_match_pyorbital():
    astronomy = pytest.importorskip("pyorbital.astronomy")
    times = np.datetime64("2023-06-01T00:00:00") + np.arange(0, 120 * 24, 7).astype("timedelta64[h]")
    lat = RNG.uniform(-60.0, 60.0, times.size)
    lon = RNG.uniform(-180.0, 180.0, times.size)
    sza, saa = solar_angles(times, lat, lon)
    alt, azi = astronomy.get_alt_az(times, lon, lat)
    np.testing.assert_allclose(sza, 90.0 - np.degrees(alt), atol=0.05)
    # Azimuth is ill-defined with the Sun overhead, so only compare it away from zenith.
    ok = sza > 5.0
    dazi = (saa - np.degrees(azi) % 360.0 + 180.0) % 360.0 - 180.0
    np.testing.assert_allclose(dazi[ok], 0.0, atol=0.2)


def test_solar_noon_at_equinox():
    # Around the March 2023 equinox the Sun is nearly overhead at the equator at local noon.
    sza, _ = solar_angles(np.datetime64("2023-03-20T12:07:00"), 0.0, 0.0)
    assert sza < 0.5
