"""Native-grid correction, effective height and the ``l1c`` command."""

import numpy as np
import pytest
import xarray as xr
from test_ingest import _write_insat

from pygeoparallax.cli import main
from pygeoparallax.cloudheight import effective_height
from pygeoparallax.geometry.parallax import parallax_correct
from pygeoparallax.ingest.insat import read_insat_l1c
from pygeoparallax.pipeline import correct_native
from pygeoparallax.resample import EMPTY, NativeGrid, mercator_lat, mercator_y


def _mercator_grid(ny=80, nx=70, lat0=22.0, lon0=76.0, step_km=4.0):
    """Pixel centres regular in Mercator northing, like an L1C file (north to south)."""
    dv = -step_km / 6378.137
    lats = mercator_lat(mercator_y(lat0) + np.arange(ny) * dv)
    lons = lon0 + np.arange(nx) * np.degrees(step_km / 6378.137)
    return np.meshgrid(lats, lons, indexing="ij")


def test_mercator_round_trip():
    lat = np.linspace(-60, 60, 121)
    np.testing.assert_allclose(mercator_lat(mercator_y(lat)), lat, atol=1e-10)


def test_native_grid_fit():
    lat, lon = _mercator_grid()
    grid = NativeGrid.from_2d(lat, lon)
    assert grid.kind == "mercator" and grid.shape == lat.shape
    np.testing.assert_allclose(grid.lats, lat[:, 0], atol=1e-9)
    np.testing.assert_allclose(grid.lons, lon[0], atol=1e-9)
    row, col = grid.fractional_index(lat, lon)
    np.testing.assert_allclose(row, np.arange(lat.shape[0])[:, None] + 0 * col, atol=1e-6)
    np.testing.assert_allclose(col, np.arange(lat.shape[1])[None, :] + 0 * row, atol=1e-6)

    # A plain lat/lon grid is recognised as such.
    g2 = NativeGrid.from_coords(np.linspace(30, 20, 11), np.linspace(70, 80, 11))
    assert g2.kind == "latlon"
    with pytest.raises(ValueError):
        NativeGrid.from_coords(np.array([20.0, 20.5, 22.0, 22.1]), np.linspace(70, 80, 4))
    with pytest.raises(ValueError):  # not separable
        NativeGrid.from_2d(lat + 0.001 * lon, lon)


def test_native_grid_matches_l1c_file(tmp_path):
    path = tmp_path / "3RIMG_TEST_L1C_SGP.h5"
    _write_insat(path)
    ds = read_insat_l1c(path, channels=("TIR1",))
    grid = NativeGrid.from_2d(ds["lat"].values, ds["lon"].values)
    assert grid.kind == "mercator"
    np.testing.assert_allclose(grid.lats, ds["lat"].values[:, 0], atol=1e-8)


def test_correct_native_without_cloud_is_identity():
    lat, lon = _mercator_grid()
    bt = 280.0 + np.random.default_rng(0).normal(0, 1, lat.shape)
    ds = correct_native(lat, lon, {"TIR1": bt}, np.full(lat.shape, np.nan))
    assert ds["TIR1"].dims == ("y", "x") and ds["TIR1"].shape == lat.shape
    np.testing.assert_allclose(ds["TIR1"].values, bt)
    assert (ds["fill_flag"].values == 0).all()
    np.testing.assert_allclose(ds["lat"].values, lat, atol=1e-9)
    assert float(ds["shift_km"].max()) < 1e-9

    raw = correct_native(lat, lon, {"TIR1": bt}, np.full(lat.shape, 12000.0), correct=False)
    np.testing.assert_allclose(raw["TIR1"].values, bt)
    assert raw.attrs["parallax_corrected"] == 0


def test_correct_native_moves_cloud_by_its_parallax():
    lat, lon = _mercator_grid()
    cloud = np.hypot(lat - lat[40, 35], lon - lon[40, 35]) < 0.15
    cth = np.where(cloud, 14000.0, np.nan)
    bt = np.where(cloud, 200.0, 290.0)
    ds = correct_native(lat, lon, {"TIR1": bt}, cth)

    # Expected: the cloud centre moves to its parallax-corrected position.
    lat_c, lon_c = parallax_correct(lat[cloud].mean(), lon[cloud].mean(), 14000.0, 74.0)
    grid = NativeGrid.from_2d(lat, lon)
    row_exp, col_exp = grid.fractional_index(lat_c, lon_c)
    moved = ds["TIR1"].values < 250.0
    rows, cols = np.nonzero(moved)
    assert rows.mean() == pytest.approx(row_exp, abs=0.6)
    assert cols.mean() == pytest.approx(col_exp, abs=0.6)
    assert rows.mean() > 41.0  # northern hemisphere: corrected towards the equator (south, larger row)
    assert ds["shift_km"].values[moved & (ds["fill_flag"].values == 0)].min() > 6.0

    # The strip the cloud leaves (about 1.6 pixels) is never seen. Without gap filling it stays
    # empty; fill_empty fills it with the nearest value and keeps the flag.
    ds = correct_native(lat, lon, {"TIR1": bt}, cth, fill_radius=0)
    empty = ds["fill_flag"].values == EMPTY
    assert empty.any() and np.isnan(ds["TIR1"].values[empty]).all()
    filled = correct_native(lat, lon, {"TIR1": bt}, cth, fill_radius=0, fill_empty=True)
    assert np.isfinite(filled["TIR1"].values).all()
    assert ((filled["fill_flag"].values == EMPTY) == empty).all()


def test_effective_height():
    cth = np.array([np.nan, 1000.0, 10000.0, 17000.0])
    np.testing.assert_array_equal(effective_height(cth), cth)
    np.testing.assert_allclose(effective_height(cth, offset=3000.0), [np.nan, 0.0, 7000.0, 14000.0])
    np.testing.assert_allclose(effective_height(cth, scale=0.5), [np.nan, 500.0, 5000.0, 8500.0])


def test_l1c_command(tmp_path):
    src = tmp_path / "3RIMG_TEST_L1C_SGP.h5"
    _write_insat(src)
    out_dir = tmp_path / "out"

    assert main(["l1c", str(src), "-o", str(out_dir), "--channels", "TIR1", "--native", "-j", "1"]) == 0
    with xr.open_dataset(out_dir / "3RIMG_TEST_L1C_SGP_corrected.nc") as ds:
        assert ds["TIR1"].shape == (60, 50)
        assert {"TIR1", "cth", "shift_km", "fill_flag"} <= set(ds.data_vars)
        assert ds.attrs["source_file"] == src.name and ds.attrs["time"] == "2022-09-30T03:58:59"
        assert "AFGL" in ds.attrs["cloud_top_height"]
        assert ds["TIR1"].attrs["units"] == "K"
        full = float(np.nanmax(ds["shift_km"]))
        assert full > 0

    lower = tmp_path / "lower"
    main(["l1c", str(src), "-o", str(lower), "--channels", "TIR1", "--native", "--height-offset", "3", "-j", "1"])
    with xr.open_dataset(lower / "3RIMG_TEST_L1C_SGP_corrected.nc") as ds:
        assert float(np.nanmax(ds["shift_km"])) < full
        assert ds.attrs["effective_height"] == "1 * cth - 3 km"

    reg = tmp_path / "regular"
    grid = ["--grid", "10.0", "20.0", "70.0", "80.0", "0.04"]
    assert main(["l1c", str(src), "-o", str(reg), "--channels", "TIR1", "--no-correction", *grid, "-j", "1"]) == 0
    with xr.open_dataset(reg / "3RIMG_TEST_L1C_SGP_uncorrected.nc") as ds:
        assert ds.sizes == {"lat": 250, "lon": 250}
        assert ds.attrs["parallax_corrected"] == 0
