import h5py
import numpy as np
import pytest

from pygeoparallax.cloudheight import (
    TROPICAL,
    cloud_mask,
    cloud_top_height,
    height_from_pressure,
    height_from_temperature,
)
from pygeoparallax.ingest import read_insat_csbt, read_insat_ctp
from pygeoparallax.resample import sample_nearest


def test_height_from_temperature_inverts_troposphere():
    z = TROPICAL.height[:17]
    np.testing.assert_allclose(height_from_temperature(TROPICAL.temperature[:17]), z)
    assert height_from_temperature(240.0) == pytest.approx(9000 + 1000 * (243.6 - 240.0) / (243.6 - 237.0))
    # Colder than the cold-point tropopause (overshooting top) -> tropopause; warmer than surface -> 0.
    np.testing.assert_allclose(height_from_temperature([185.0, 305.0]), [TROPICAL.tropopause_height, 0.0])
    assert np.isnan(height_from_temperature(np.nan))


def test_height_from_pressure():
    np.testing.assert_allclose(height_from_pressure(TROPICAL.pressure), TROPICAL.height, atol=1e-6)
    assert 12000.0 < height_from_pressure(200.0) < 13000.0
    assert np.isnan(height_from_pressure(np.nan)) and np.isnan(height_from_pressure(-999.0))


def test_cloud_mask_and_height():
    bt = np.array([295.0, 285.0, 230.0, np.nan])
    csbt = np.array([297.0, 296.0, np.nan, 296.0])
    np.testing.assert_array_equal(cloud_mask(bt, csbt), [False, True, True, False])
    np.testing.assert_array_equal(cloud_mask(bt), [False, False, True, False])
    h = cloud_top_height(bt, csbt)
    assert np.isnan(h[0]) and np.isnan(h[3])
    assert h[2] == pytest.approx(height_from_temperature(230.0))


def test_sample_nearest():
    src_lat = np.array([10.0, 10.0, 11.0, np.nan])
    src_lon = np.array([76.0, 77.0, 76.0, 80.0])
    vals = np.array([1.0, 2.0, 3.0, 9.0])
    out = sample_nearest(src_lat, src_lon, vals, np.array([[10.1, 10.0], [10.9, 20.0]]), np.array([[76.1, 76.9], [76.0, 20.0]]))
    np.testing.assert_allclose(out[0], [1.0, 2.0])
    assert out[1, 0] == 3.0
    assert np.isnan(out[1, 1])  # too far from any source point


def test_ctp_reader_synthetic(tmp_path):
    path = tmp_path / "3RIMG_TEST_L2B_CTP.h5"
    with h5py.File(path, "w") as f:
        f.attrs["Acquisition_Start_Time"] = np.bytes_("06-JUN-2022T17:15:06")
        f.attrs["Acquisition_End_Time"] = np.bytes_("06-JUN-2022T17:41:06")
        f.attrs["Satellite_Name"] = np.bytes_("INSAT-3DR")
        for name in ("Latitude", "Longitude", "CSBT_Latitude", "CSBT_Longitude"):
            arr = np.array([[1000, 1100], [31172, 1200]], np.int16)
            d = f.create_dataset(name, data=arr)
            d.attrs["_FillValue"] = np.array([31172], np.int16)
            d.attrs["scale_factor"] = np.array([0.01], np.float32)
        for name, val in (("CTP", 250.0), ("CTT", 225.0), ("EFF_EMISS", 0.9), ("CSBT_TIR1", 296.0), ("CLRFR_TIR1", 0.8)):
            arr = np.full((1, 2, 2), val, np.float32)
            arr[0, 0, 1] = -999.0
            d = f.create_dataset(name, data=arr)
            d.attrs["_FillValue"] = np.array([-999.0], np.float32)

    ctp = read_insat_ctp(path)
    assert ctp["ctp"].values[0, 0] == 250.0 and np.isnan(ctp["ctp"].values[0, 1])
    assert ctp["lat"].values[0, 1] == pytest.approx(11.0) and np.isnan(ctp["lat"].values[1, 0])
    csbt = read_insat_csbt(path)
    assert csbt["clear_sky_bt"].values[1, 1] == 296.0
    assert csbt.attrs["start_time"] == "2022-06-06T17:15:06"


def _era5_file(path, t_offset=0.0):
    """Synthetic CDS-style ERA5 file: the AFGL tropical profile on 26 levels, uniform in space."""
    import xarray as xr

    from pygeoparallax.ingest.era5 import EARTH_RADIUS, G0

    lat = np.array([30.0, 25.0, 20.0])  # CDS order: north to south
    lon = np.array([85.0, 90.0, 95.0])
    p = TROPICAL.pressure[::-1]  # CDS order: top first
    z = TROPICAL.height[::-1]
    t = TROPICAL.temperature[::-1] + t_offset
    geop = G0 * EARTH_RADIUS * z / (EARTH_RADIUS + z)  # inverse of geometric_height
    shape = (1, p.size, lat.size, lon.size)
    ds = xr.Dataset(
        {"t": (("valid_time", "pressure_level", "latitude", "longitude"), np.broadcast_to(t[None, :, None, None], shape)),
         "z": (("valid_time", "pressure_level", "latitude", "longitude"), np.broadcast_to(geop[None, :, None, None], shape))},
        coords={"valid_time": [np.datetime64("2024-08-18T22:00")], "pressure_level": p, "latitude": lat, "longitude": lon},
    )
    ds.to_netcdf(path)
    return path


def test_read_era5_profiles(tmp_path):
    from pygeoparallax.ingest import read_era5_profiles

    era5 = read_era5_profiles(_era5_file(tmp_path / "era5.nc"))
    assert era5["temperature"].dims == ("level", "lat", "lon")
    assert era5["level"].values[0] == TROPICAL.pressure[0] and np.all(np.diff(era5["lat"].values) > 0)
    np.testing.assert_allclose(era5["height"].values[:, 1, 1], TROPICAL.height, atol=1e-6)
    np.testing.assert_allclose(era5["temperature"].values[:, 0, 2], TROPICAL.temperature)


def test_cloud_top_height_profiles_matches_single_profile(tmp_path):
    from pygeoparallax.cloudheight import cloud_top_height_profiles, height_from_temperature_profiles
    from pygeoparallax.ingest import read_era5_profiles

    bt = np.array([[285.0, 240.0, 210.0], [195.0, 190.0, np.nan]])
    lat = np.full(bt.shape, 24.3)
    lon = np.full(bt.shape, 91.7)
    era5 = read_era5_profiles(_era5_file(tmp_path / "era5.nc"))
    h = cloud_top_height_profiles(bt, lat, lon, era5, min_pressure=50.0)
    np.testing.assert_allclose(h, cloud_top_height(bt), equal_nan=True, atol=1e-6)
    # A warmer atmosphere puts the same BT higher up.
    warm = read_era5_profiles(_era5_file(tmp_path / "warm.nc", t_offset=2.0))
    assert cloud_top_height_profiles(np.array([240.0]), [24.0], [90.0], warm, min_pressure=50.0)[0] > h[0, 1]
    # The search runs down from the cold point, so a low inversion does not capture a high cloud.
    pt = np.array([[290.0, 295.0, 280.0, 250.0, 220.0, 200.0, 210.0]])
    pz = np.array([[0.0, 1000.0, 3000.0, 7000.0, 11000.0, 16000.0, 19000.0]])
    assert height_from_temperature_profiles([292.0], pt, pz)[0] == pytest.approx(1000 + 2000 * 3 / 15)
    assert height_from_temperature_profiles([190.0], pt, pz)[0] == pytest.approx(16000.0)
