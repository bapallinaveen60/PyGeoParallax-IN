"""Command-line details: region grids, effective-height labels, attributes, error handling, navigation JSON."""

import json

import numpy as np
import xarray as xr
from test_cli import GRID_ARGS, _write_scene
from test_ingest import _write_insat

from pygeoparallax.cli import main
from pygeoparallax.navigation import NavigationCorrection


def test_l1c_bbox_without_grid_uses_the_region(tmp_path):
    src = tmp_path / "3RIMG_TEST_L1C_SGP.h5"
    _write_insat(src)
    assert main(["l1c", str(src), "-o", str(tmp_path / "out"), "--channels", "TIR1",
                 "--bbox", "12", "18", "72", "78", "-j", "1"]) == 0
    with xr.open_dataset(tmp_path / "out" / "3RIMG_TEST_L1C_SGP_corrected.nc") as ds:
        assert ds.sizes == {"lat": 150, "lon": 150}  # 6 deg at 0.04 deg, not the 1000 x 1000 South Asia grid
        assert float(ds["lat"].min()) > 12.0 and float(ds["lon"].max()) < 78.0
        assert ds["count"].attrs["long_name"].startswith("number of pixels")


def test_effective_height_is_labelled(tmp_path):
    src = tmp_path / "scene.nc"
    _write_scene(src)
    out = tmp_path / "eff.nc"
    assert main(["correct", str(src), str(out), "--height-offset", "3", *GRID_ARGS]) == 0
    with xr.open_dataset(out) as ds:
        assert "effective height" in ds["cth"].attrs["long_name"]
        assert ds.attrs["effective_height"] == "1 * cloud-top height - 3 km"


def test_correct_keeps_channel_attributes(tmp_path):
    src = tmp_path / "scene.nc"
    _write_scene(src)
    with xr.open_dataset(src) as ds:
        ds = ds.load()
    ds["TIR1"].attrs = {"units": "K", "long_name": "TIR1 brightness temperature"}
    ds.attrs["sensor"] = "IMAGER"
    ds.to_netcdf(tmp_path / "scene_attrs.nc")
    out = tmp_path / "attrs.nc"
    assert main(["correct", str(tmp_path / "scene_attrs.nc"), str(out), *GRID_ARGS]) == 0
    with xr.open_dataset(out) as res:
        assert res["TIR1"].attrs["units"] == "K"
        assert res.attrs["sensor"] == "IMAGER"


def test_correct_reports_errors_without_traceback(tmp_path, capsys):
    assert main(["correct", str(tmp_path / "missing.nc"), str(tmp_path / "out.nc"), *GRID_ARGS]) == 1
    assert "error: missing.nc" in capsys.readouterr().err


def test_navigation_rejects_unknown_windows(tmp_path, capsys):
    src = tmp_path / "3RIMG_15FEB2023_0415_L1C_SGP_V01R00.h5"
    _write_insat(src)
    land = tmp_path / "land.geojson"
    land.write_text(json.dumps({"type": "FeatureCollection", "features": []}))
    assert main(["navigation", str(src), "-o", str(tmp_path / "nav.json"), "--land", str(land),
                 "--windows", "Atlantis"]) == 1
    assert "unknown window(s): Atlantis" in capsys.readouterr().err


def test_navigation_json_is_standard_and_round_trips_nan(tmp_path):
    corr = NavigationCorrection([20.0, 22.0], [72.0, 88.0], [-3.0, 1.0], [np.nan, 2.0], meta={"r": float("nan")})
    path = tmp_path / "nav.json"
    corr.to_json(path)
    text = path.read_text()
    assert "NaN" not in text
    json.loads(text)  # strict JSON
    back = NavigationCorrection.from_json(path)
    assert np.isnan(back.north_km[0]) and back.north_km[1] == 2.0
    np.testing.assert_allclose(back(21.0, 80.0), corr(21.0, 80.0))
