import numpy as np
import pytest

from pygeoparallax.geometry.constants import GEO_RADIUS, SATELLITE_LONGITUDES, WGS84_A
from pygeoparallax.geometry.ecef import ecef_to_geodetic, geodetic_to_ecef
from pygeoparallax.geometry.parallax import (
    parallax_correct,
    parallax_correct_terrain,
    parallax_shift,
)
from pygeoparallax.geometry.viewing import satellite_view_angles

SAT_LON = SATELLITE_LONGITUDES["INSAT-3DR"]
RNG = np.random.default_rng(7)
# Indian region and beyond, out to ~65 deg VZA.
LAT = RNG.uniform(-40.0, 40.0, 400)
LON = RNG.uniform(SAT_LON - 45.0, SAT_LON + 45.0, 400)
H = RNG.uniform(0.0, 18000.0, 400)


def _sat_ecef():
    return np.array([GEO_RADIUS * np.cos(np.radians(SAT_LON)), GEO_RADIUS * np.sin(np.radians(SAT_LON)), 0.0])


def test_corrected_point_lies_on_line_of_sight_at_cloud_height():
    lat_c, lon_c = parallax_correct(LAT, LON, H, SAT_LON)
    p = np.stack(geodetic_to_ecef(LAT, LON, 0.0))
    q = np.stack(geodetic_to_ecef(lat_c, lon_c, H))
    s = _sat_ecef()[:, None]
    # Q must be on the segment from P towards S: cross product ~ 0.
    u = (s - p) / np.linalg.norm(s - p, axis=0)
    off_line = np.linalg.norm(np.cross((q - p).T, u.T), axis=1)
    assert off_line.max() < 1e-3  # metres

    # The point on that line is at the requested geodetic height.
    _, _, qh = ecef_to_geodetic(*q)
    np.testing.assert_allclose(qh, H, atol=1e-3)


def test_no_shift_at_zero_height_or_sub_satellite_point():
    lat_c, lon_c = parallax_correct(LAT, LON, 0.0, SAT_LON)
    np.testing.assert_allclose(lat_c, LAT, atol=1e-9)
    np.testing.assert_allclose(lon_c, LON, atol=1e-9)

    lat_c, lon_c = parallax_correct(0.0, SAT_LON, 15000.0, SAT_LON)
    assert lat_c == pytest.approx(0.0, abs=1e-9)
    assert lon_c == pytest.approx(SAT_LON, abs=1e-9)


def test_shift_points_towards_satellite_with_flat_earth_magnitude():
    lat, lon = 19.13, 72.86  # Mumbai
    vza, vaa = satellite_view_angles(lat, lon, SAT_LON)
    lat_c, lon_c = parallax_correct(lat, lon, 1000.0, SAT_LON)
    dist, az = parallax_shift(lat, lon, lat_c, lon_c)
    # For a low cloud the flat-Earth estimate h * tan(VZA) is very close.
    assert dist == pytest.approx(1000.0 * np.tan(np.radians(vza)), rel=0.01)
    assert az == pytest.approx(vaa, abs=0.5)


def test_nan_height_and_invisible_points_give_nan():
    lat_c, lon_c = parallax_correct([10.0, 0.0], [SAT_LON, SAT_LON + 120.0], [np.nan, 10000.0], SAT_LON)
    assert np.isnan(lat_c).all() and np.isnan(lon_c).all()


def test_navigation_on_terrain_h0():
    # A feature at the navigation surface height does not move.
    lat_c, lon_c = parallax_correct(LAT, LON, 3000.0, SAT_LON, h0=3000.0)
    np.testing.assert_allclose(lat_c, LAT, atol=1e-9)
    np.testing.assert_allclose(lon_c, LON, atol=1e-9)


def test_terrain_correction_clamps_cloud_to_ground_and_moves_clear_sky():
    def plateau(lat, lon):
        return np.full(np.shape(lat), 4000.0)

    lat = np.array([31.1, 31.1, 31.1])
    lon = np.array([77.17, 77.17, 77.17])
    cth = np.array([np.nan, 2000.0, 12000.0])  # clear, cloud "below" ground, high cloud
    lat_c, lon_c, height = parallax_correct_terrain(lat, lon, cth, SAT_LON, plateau)
    np.testing.assert_allclose(height, [4000.0, 4000.0, 12000.0])

    ref_lat, ref_lon = parallax_correct(lat, lon, height, SAT_LON)
    np.testing.assert_allclose(lat_c, ref_lat)
    np.testing.assert_allclose(lon_c, ref_lon)
    # Even clear sky over a 4 km plateau is misplaced by kilometres at ~36 deg VZA.
    dist, _ = parallax_shift(lat[0], lon[0], lat_c[0], lon_c[0])
    assert 2500.0 < dist < 3500.0


def test_terrain_iteration_converges_on_slope():
    # Ground rising northwards at 20 m/km, like the steep side of the Ghats.
    def ramp(lat, lon):
        return np.clip((np.asarray(lat) - 15.0) * 111.0 * 20.0, 0.0, None)

    lat = np.full(5, 15.5)
    lon = np.linspace(73.5, 74.5, 5)
    lat_c, lon_c, height = parallax_correct_terrain(lat, lon, np.full(5, np.nan), SAT_LON, ramp, iterations=6)
    # Fixed point: the corrected location's ground height is the height used.
    np.testing.assert_allclose(ramp(lat_c, lon_c), height, atol=0.5)


def test_matches_satpy_within_spherical_earth_error():
    parallax = pytest.importorskip("satpy.modifiers.parallax")
    lat = np.array([9.96, 15.49, 19.13, 23.89, 31.1])
    lon = np.array([76.29, 73.82, 72.86, 91.24, 77.17])
    h = np.full(5, 12000.0)
    lon_s, lat_s = parallax.get_parallax_corrected_lonlats(
        SAT_LON, 0.0, GEO_RADIUS - WGS84_A, lon, lat, h
    )
    lat_c, lon_c = parallax_correct(lat, lon, h, SAT_LON)
    ours, _ = parallax_shift(lat, lon, lat_c, lon_c)
    theirs, _ = parallax_shift(lat, lon, np.asarray(lat_s), np.asarray(lon_s))
    # Same physics; satpy's spherical Earth differs by ~25 m (0.3%) on an 8 km shift.
    np.testing.assert_allclose(ours, theirs, rtol=0.01)


def test_numba_and_numpy_backends_agree():
    lat = np.append(LAT, [0.0, 10.0])
    lon = np.append(LON, [SAT_LON + 120.0, SAT_LON])  # one invisible point
    h = np.append(H, [10000.0, np.nan])  # one NaN height
    a = parallax_correct(lat, lon, h, SAT_LON, backend="numpy")
    b = parallax_correct(lat, lon, h, SAT_LON, backend="numba")
    for x, y in zip(a, b):
        np.testing.assert_array_equal(np.isnan(x), np.isnan(y))
        np.testing.assert_allclose(x, y, atol=1e-10, equal_nan=True)
    with pytest.raises(ValueError):
        parallax_correct(lat, lon, h, SAT_LON, backend="cuda")
