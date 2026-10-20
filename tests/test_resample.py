import numpy as np
import pytest

from pygeoparallax import correct_scene
from pygeoparallax.geometry import parallax_correct, parallax_shift, satellite_view_angles
from pygeoparallax.resample import EMPTY, INTERPOLATED, OBSERVED, Grid, bucket_max_height, idw_fill, resample

GRID = Grid(lat_min=10.0, lat_max=11.0, lon_min=70.0, lon_max=71.0, res=0.1)


def test_grid_geometry():
    assert GRID.shape == (10, 10)
    np.testing.assert_allclose(GRID.lats[[0, -1]], [10.95, 10.05])
    np.testing.assert_allclose(GRID.lons[[0, -1]], [70.05, 70.95])
    row, col, valid = GRID.cell_index([10.99, 10.01, 12.0, np.nan], [70.01, 70.99, 70.5, 70.5])
    np.testing.assert_array_equal(valid, [True, True, False, False])
    assert (row[0], col[0]) == (0, 0)
    assert (row[1], col[1]) == (9, 9)


def test_highest_pixel_wins_collision():
    lat = [10.55, 10.55, 10.55]
    lon = [70.55, 70.56, 70.57]
    out = bucket_max_height(GRID, lat, lon, [500.0, 12000.0, np.nan], {"bt": [290.0, 210.0, 280.0]})
    r, c = 4, 5
    assert out["bt"][r, c] == 210.0
    assert out["height"][r, c] == 12000.0
    assert out["count"][r, c] == 3
    assert out["count"].sum() == 3
    assert np.isnan(out["bt"]).sum() == 99


def test_idw_fill_rules():
    field = np.full((5, 5), 280.0)
    observed = np.ones((5, 5), bool)
    observed[2, 2] = False  # a one-cell sampling gap
    field[2, 2] = np.nan
    filled, mask = idw_fill(field, observed)
    assert filled[2, 2] == pytest.approx(280.0)
    assert mask.sum() == 1

    # An observed NaN (clear-sky CTH) is a value, not a gap.
    field[0, 0] = np.nan
    filled, mask = idw_fill(field, observed)
    assert np.isnan(filled[0, 0]) and not mask[0, 0]

    # A gap surrounded mostly by clear sky stays clear.
    cth = np.full((5, 5), np.nan)
    cth[1, 1] = 10000.0
    filled, mask = idw_fill(cth, observed)
    assert mask[2, 2] and np.isnan(filled[2, 2])


def test_large_gap_stays_empty():
    lat, lon = np.meshgrid(GRID.lats, GRID.lons, indexing="ij")
    keep = ~((lat > 10.2) & (lat < 10.8) & (lon > 70.2) & (lon < 70.8))  # 6x6 hole
    ds = resample(GRID, lat[keep], lon[keep], np.zeros(keep.sum()), {"bt": np.full(keep.sum(), 290.0)})
    flag = ds["fill_flag"].values
    assert (flag == OBSERVED).sum() == keep.sum()
    assert (flag == INTERPOLATED).sum() == 20  # the hole's outer ring
    assert (flag == EMPTY).sum() == 16  # its 4x4 core
    assert np.isnan(ds["bt"].values[flag == EMPTY]).all()


def _synthetic_scene(lat0=23.89, lon0=91.24, res=0.01, cloud_cth=12000.0):
    """Clear 290 K scene with a 0.4 x 0.4 degree, 210 K cloud block at its apparent position."""
    lats = np.arange(lat0 - 1.0, lat0 + 1.0, res) + res / 2
    lons = np.arange(lon0 - 1.0, lon0 + 1.0, res) + res / 2
    lat, lon = np.meshgrid(lats, lons, indexing="ij")
    cloud = (np.abs(lat - lat0) < 0.2) & (np.abs(lon - lon0) < 0.2)
    bt = np.where(cloud, 210.0, 290.0)
    cth = np.where(cloud, cloud_cth, np.nan)
    grid = Grid(lat0 - 1.0, lat0 + 1.0, lon0 - 1.0, lon0 + 1.0, 0.02)
    return lat, lon, bt, cth, cloud, grid


def test_synthetic_cloud_moves_towards_satellite():
    lat, lon, bt, cth, cloud, grid = _synthetic_scene()
    raw = correct_scene(lat, lon, {"TIR1": bt}, cth, grid=grid, correct=False, fill_radius=0)
    cor = correct_scene(lat, lon, {"TIR1": bt}, cth, grid=grid, fill_radius=0)

    def centroid(ds):
        cold = ds["TIR1"].values < 250.0
        glat, glon = np.meshgrid(ds.lat.values, ds.lon.values, indexing="ij")
        return glat[cold].mean(), glon[cold].mean()

    # The uncorrected grid keeps the block in place.
    rlat, rlon = centroid(raw)
    assert rlat == pytest.approx(23.89, abs=0.01) and rlon == pytest.approx(91.24, abs=0.01)

    # The corrected block moves by the expected shift, towards the satellite (SW at Agartala).
    clat, clon = centroid(cor)
    exp_lat, exp_lon = parallax_correct(23.89, 91.24, 12000.0, 74.0)
    dist, az = parallax_shift(rlat, rlon, clat, clon)
    exp_dist, _ = parallax_shift(23.89, 91.24, exp_lat, exp_lon)
    _, vaa = satellite_view_angles(23.89, 91.24, 74.0)
    assert dist == pytest.approx(exp_dist, rel=0.1)  # ~8 km
    assert az == pytest.approx(vaa, abs=5.0)

    # The ground the cloud hid, on its far side from the satellite, is now an empty strip.
    flag = cor["fill_flag"].values
    assert (flag == EMPTY).sum() > 0
    assert (raw["fill_flag"].values == EMPTY).sum() == 0
    assert cor["shift_km"].max() == pytest.approx(exp_dist / 1000.0, rel=0.05)
    assert cor.attrs["parallax_corrected"] == 1


def test_terrain_scene_flags_and_clear_sky_shift():
    lat, lon, bt, cth, cloud, grid = _synthetic_scene(lat0=31.1, lon0=77.17)
    cor = correct_scene(lat, lon, {"TIR1": bt}, cth, grid=grid,
                        surface_height=lambda la, lo: np.full(np.shape(la), 4000.0))
    assert cor.attrs["terrain_corrected"] == 1
    clear = np.isnan(cor["cth"].values) & (cor["fill_flag"].values == OBSERVED)
    # Clear sky over a 4 km plateau at Shimla moves ~3 km.
    assert np.nanmedian(cor["shift_km"].values[clear]) == pytest.approx(2.9, abs=0.3)
