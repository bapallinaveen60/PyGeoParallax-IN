import numpy as np
import xarray as xr

from pygeoparallax.cli import main

GRID_ARGS = ["--grid", "30.0", "32.0", "76.0", "78.0", "0.04"]


def _write_scene(path, cth_value=12000.0):
    lats = np.arange(30.2, 31.8, 0.02)
    lons = np.arange(76.2, 77.8, 0.02)
    lat, lon = np.meshgrid(lats, lons, indexing="ij")
    cloud = np.hypot(lat - 31.0, lon - 77.0) < 0.2
    xr.Dataset(
        {
            "lat": (("y", "x"), lat),
            "lon": (("y", "x"), lon),
            "cth": (("y", "x"), np.where(cloud, cth_value, np.nan)),
            "TIR1": (("y", "x"), np.where(cloud, 210.0, 290.0)),
            "WV": (("y", "x"), np.where(cloud, 220.0, 240.0)),
        },
        attrs={"sub_satellite_longitude": 74.0, "time": "2023-07-15T06:00:00"},
    ).to_netcdf(path)


def test_correct_command(tmp_path):
    src = tmp_path / "scene.nc"
    _write_scene(src)
    out = tmp_path / "out" / "scene_corrected.nc"
    assert main(["correct", str(src), str(out), *GRID_ARGS]) == 0
    with xr.open_dataset(out) as ds:
        assert {"TIR1", "WV", "cth", "shift_km", "fill_flag"} <= set(ds.data_vars)
        assert ds.attrs["parallax_corrected"] == 1
        assert ds.attrs["time"] == "2023-07-15T06:00:00"
        assert ds.sizes == {"lat": 50, "lon": 50}
        assert float(ds["shift_km"].max()) > 8.0


def test_correct_with_dem_and_no_correction(tmp_path):
    src = tmp_path / "scene.nc"
    _write_scene(src)
    dem = tmp_path / "dem.nc"
    xr.Dataset(
        {"elevation": (("lat", "lon"), np.full((21, 21), 4000.0))},
        coords={"lat": np.linspace(29.0, 33.0, 21), "lon": np.linspace(75.0, 79.0, 21)},
    ).to_netcdf(dem)

    out = tmp_path / "terrain.nc"
    main(["correct", str(src), str(out), "--dem", str(dem), "--channels", "TIR1", *GRID_ARGS])
    with xr.open_dataset(out) as ds:
        assert ds.attrs["terrain_corrected"] == 1
        assert "WV" not in ds
        clear = np.isnan(ds["cth"].values) & (ds["fill_flag"].values == 0)
        assert np.nanmedian(ds["shift_km"].values[clear]) > 2.0  # terrain parallax on a 4 km plateau

    raw = tmp_path / "raw.nc"
    main(["correct", str(src), str(raw), "--no-correction", *GRID_ARGS])
    with xr.open_dataset(raw) as ds:
        assert ds.attrs["parallax_corrected"] == 0
        assert "shift_km" not in ds


def test_batch_command(tmp_path, capsys):
    for i in range(3):
        _write_scene(tmp_path / f"scene_{i}.nc", cth_value=8000.0 + 2000.0 * i)
    out_dir = tmp_path / "batch"
    args = ["batch", str(tmp_path / "scene_*.nc"), "-o", str(out_dir), "-j", "2", *GRID_ARGS]
    assert main(args) == 0
    assert sorted(p.name for p in out_dir.iterdir()) == [f"scene_{i}_corrected.nc" for i in range(3)]

    # A second run skips finished scenes.
    assert main(args) == 0
    assert capsys.readouterr().out.count("skip") == 3


def test_correct_with_navigation_correction(tmp_path):
    from pygeoparallax.navigation import NavigationCorrection

    src = tmp_path / "scene.nc"
    _write_scene(src)
    nav = tmp_path / "nav.json"
    NavigationCorrection([31.0], [77.0], [-20.0], [0.0]).to_json(nav)  # 20 km west everywhere

    plain, shifted = tmp_path / "plain.nc", tmp_path / "shifted.nc"
    main(["correct", str(src), str(plain), "--no-correction", *GRID_ARGS])
    main(["correct", str(src), str(shifted), "--no-correction", "--nav-correction", str(nav), *GRID_ARGS])
    with xr.open_dataset(plain) as a, xr.open_dataset(shifted) as b:
        assert b.attrs["navigation_correction"] == "nav.json"
        cold_a = a["TIR1"].values < 250.0
        cold_b = b["TIR1"].values < 250.0
        cols = np.arange(a.sizes["lon"])
        # The cold cloud moves ~20 km (about 5 cells of 0.04 deg) west.
        shift_cells = (cols * cold_a).sum() / cold_a.sum() - (cols * cold_b).sum() / cold_b.sum()
        assert 4.0 < shift_cells < 6.5
