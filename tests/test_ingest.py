"""Reader tests on small synthetic HDF5 files laid out like the real products.

Set ``PYGEOPARALLAX_SAMPLE_DATA`` to a folder with real INSAT/GPM files to
also run the tests on real data.
"""

import glob
import os

import h5py
import numpy as np
import pytest

from pygeoparallax.ingest.gpm import CONVECTIVE, NO_RAIN, STRATIFORM, read_gpm_2a
from pygeoparallax.ingest.insat import read_insat_l1c, to_standard_scene

A, B = 6378137.0, 6356752.3142


def _write_insat(path, ny=60, nx=50):
    x = np.linspace(-500000.0, 500000.0, nx)  # around lon_0 = 75
    y = np.linspace(2200000.0, 1200000.0, ny)  # roughly 19N..11N, north to south
    counts = np.tile(np.arange(nx, dtype=np.uint16) * 10, (ny, 1))
    counts[0, 0] = 1023  # fill
    with h5py.File(path, "w") as f:
        f.attrs["Acquisition_Start_Time"] = np.bytes_("30-SEP-2022T03:45:32")
        f.attrs["Acquisition_End_Time"] = np.bytes_("30-SEP-2022T04:12:26")
        f.attrs["Satellite_Name"] = np.bytes_("INSAT-3DR")
        f.attrs["Sensor_Name"] = np.bytes_("IMAGER")
        f.attrs["Unique_Id"] = np.bytes_("3RIMG_TEST")
        f.attrs["Nominal_Central_Point_Coordinates(degrees)_Latitude_Longitude"] = np.array([0.0, 74.0])
        f["X"] = x
        f["Y"] = y
        proj = f.create_dataset("Projection_Information", data=np.zeros(1, np.int32))
        proj.attrs["longitude_of_projection_origin"] = np.array([75.0])
        proj.attrs["standard_parallel"] = np.array([0.0])
        proj.attrs["semi_major_axis"] = np.array([A])
        proj.attrs["semi_minor_axis"] = np.array([B])
        d = f.create_dataset("IMG_TIR1", data=counts[None])
        d.attrs["_FillValue"] = np.array([1023], np.uint16)
        d.attrs["central_wavelength"] = np.array([10.785], np.float32)
        lut = f.create_dataset("IMG_TIR1_TEMP", data=np.linspace(330.0, 160.0, 1024, dtype=np.float32))
        lut.attrs["_FillValue"] = np.array([999.0], np.float32)
    return x, y


def test_insat_reader_synthetic(tmp_path):
    path = tmp_path / "3RIMG_TEST_L1C_SGP.h5"
    x, y = _write_insat(path)
    ds = read_insat_l1c(path, channels=("TIR1",))

    assert ds["TIR1"].shape == (60, 50)
    assert np.isnan(ds["TIR1"].values[0, 0])
    lut = np.linspace(330.0, 160.0, 1024, dtype=np.float32)
    assert ds["TIR1"].values[1, 3] == pytest.approx(lut[30])
    # Mercator: lon = lon_0 + x / a (radians), independent of latitude.
    np.testing.assert_allclose(ds["lon"].values[0], 75.0 + np.degrees(x / A), atol=1e-9)
    assert ds["lat"].values[0, 0] > ds["lat"].values[-1, 0]  # north to south
    assert 10.0 < ds["lat"].values[-1, 0] < ds["lat"].values[0, 0] < 20.0
    assert ds.attrs["sub_satellite_longitude"] == 74.0
    assert ds.attrs["time"] == "2022-09-30T03:58:59"

    sub = read_insat_l1c(path, channels=("TIR1",), bbox=(14.0, 16.0, 74.0, 76.0))
    assert sub["lat"].min() >= 14.0 and sub["lat"].max() <= 16.0
    assert sub["lon"].min() >= 74.0 and sub["lon"].max() <= 76.0
    with pytest.raises(ValueError):
        read_insat_l1c(path, channels=("TIR1",), bbox=(40.0, 45.0, 74.0, 76.0))
    with pytest.raises(KeyError):
        read_insat_l1c(path, channels=("TIR9",))

    scene = to_standard_scene(sub)
    assert {"lat", "lon", "cth", "TIR1"} <= set(scene.data_vars)
    assert np.isnan(scene["cth"]).all()


def _write_gpm(path, nscan=20, nray=5):
    with h5py.File(path, "w") as f:
        fs = f.create_group("FS")
        lat = np.repeat(np.linspace(0.0, 19.0, nscan)[:, None], nray, axis=1).astype(np.float32)
        lon = np.repeat(np.linspace(80.0, 81.0, nray)[None, :], nscan, axis=0).astype(np.float32)
        lat[0, 0] = -9999.9
        for name, arr in (("Latitude", lat), ("Longitude", lon)):
            d = fs.create_dataset(name, data=arr)
            d.attrs["_FillValue"] = np.float32(-9999.9)
        st = fs.create_group("ScanTime")
        secs = np.arange(nscan)
        for name, val in (("Year", 2022), ("Month", 6), ("DayOfMonth", 6), ("Hour", 17)):
            st[name] = np.full(nscan, val, np.int16)
        st["Minute"] = (10 + secs // 60).astype(np.int8)
        st["Second"] = (secs % 60).astype(np.int8)
        st["MilliSecond"] = np.full(nscan, 500, np.int16)

        tp = np.full((nscan, nray), -1111, np.int32)
        tp[5, 2] = 20000000 + 123
        tp[6, 2] = 10000000 + 456
        tp[7, 2] = -9999
        fs["CSF/typePrecip"] = tp
        top = np.full((nscan, nray), -9999.9, np.float32)
        top[5, 2] = 15000.0
        d = fs.create_dataset("PRE/heightStormTop", data=top)
        d.attrs["_FillValue"] = np.float32(-9999.9)
        bb = np.full((nscan, nray), -1111.1, np.float32)
        bb[6, 2] = 4800.0
        fs["CSF/heightBB"] = bb
        fs["SLV/precipRateNearSurface"] = np.where(tp > 0, 10.0, 0.0).astype(np.float32)


def test_gpm_reader_synthetic(tmp_path):
    path = tmp_path / "2A.GPM.Ku.V9-20211125.20220606-S164656-E181924.046997.V07A.HDF5"
    _write_gpm(path)
    ds = read_gpm_2a(path)
    assert ds.sizes == {"scan": 20, "ray": 5}
    assert np.isnan(ds["lat"].values[0, 0])
    assert ds["precip_type"].values[5, 2] == CONVECTIVE
    assert ds["precip_type"].values[6, 2] == STRATIFORM
    assert ds["precip_type"].values[7, 2] == -1
    assert ds["precip_type"].values[0, 0] == NO_RAIN
    assert ds["storm_top_height"].values[5, 2] == 15000.0
    assert np.isnan(ds["storm_top_height"].values[0, 1])
    assert np.isnan(ds["bright_band_height"].values[0, 1])  # -1111.1 = no bright band
    assert ds["bright_band_height"].values[6, 2] == 4800.0
    assert "zero_deg_height" not in ds  # absent variables are skipped
    assert ds["time"].values[0] == np.datetime64("2022-06-06T17:10:00.500")
    assert ds["time"].values[-1] == np.datetime64("2022-06-06T17:10:19.500")
    assert ds.attrs["product"] == "2A.GPM.Ku"

    sub = read_gpm_2a(path, bbox=(4.0, 6.0, 79.0, 82.0))
    assert sub.sizes["scan"] < 20 and (sub["lat"].values >= 3.0).all()
    with pytest.raises(ValueError):
        read_gpm_2a(path, bbox=(30.0, 35.0, 79.0, 82.0))


SAMPLE = os.environ.get("PYGEOPARALLAX_SAMPLE_DATA")


@pytest.mark.skipif(not SAMPLE, reason="set PYGEOPARALLAX_SAMPLE_DATA to run on real files")
def test_real_sample_files():
    insat = sorted(glob.glob(os.path.join(SAMPLE, "**", "3RIMG_*_L1C_SGP_*.h5"), recursive=True))
    gpm = sorted(glob.glob(os.path.join(SAMPLE, "**", "2A.GPM.*.HDF5"), recursive=True))
    assert insat or gpm
    for p in insat[:2]:
        ds = read_insat_l1c(p, bbox=(0.0, 40.0, 60.0, 100.0))
        bt = ds["TIR1"].values
        assert 150.0 < np.nanmin(bt) and np.nanmax(bt) < 340.0
        assert ds.attrs["satellite"].startswith("INSAT")
    for p in gpm[:1]:
        ds = read_gpm_2a(p, bbox=(5.0, 37.0, 66.0, 98.0))
        assert set(np.unique(ds["precip_type"].values)) <= {-1, 0, 1, 2, 3}
        assert np.nanmax(ds["storm_top_height"].values) < 25000.0


def test_insat_position_offset(tmp_path):
    from pygeoparallax.geometry import parallax_shift

    path = tmp_path / "3RIMG_TEST_L1C_SGP.h5"
    _write_insat(path)
    base = read_insat_l1c(path, channels=("TIR1",))
    moved = read_insat_l1c(path, channels=("TIR1",), position_offset_km=(-8.0, 3.0))
    dist, az = parallax_shift(base["lat"].values, base["lon"].values, moved["lat"].values, moved["lon"].values)
    np.testing.assert_allclose(dist, np.hypot(8.0, 3.0) * 1000.0, rtol=1e-6)
    np.testing.assert_allclose(az, np.degrees(np.arctan2(-8.0, 3.0)) % 360.0, atol=1e-3)
    assert moved.attrs["position_offset_km"] == [-8.0, 3.0]
    np.testing.assert_array_equal(moved["TIR1"].values, base["TIR1"].values)  # only positions change
    assert "position_offset_km" not in base.attrs
