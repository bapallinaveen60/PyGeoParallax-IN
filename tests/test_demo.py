"""The synthetic demo: the simulated satellite view and the self-test."""

import numpy as np
import pytest
import xarray as xr

from pygeoparallax.cli import main
from pygeoparallax.demo import STORMS, run_demo, simulate_scene, temperature_at


def test_simulated_scene_is_displaced_away_from_the_satellite():
    lat, lon, bt, truth = simulate_scene()
    assert lat.shape == bt.shape and lat[0, 0] > lat[-1, 0]  # north to south, like L1C
    for k, (_, clat, clon, height, _) in enumerate(STORMS, start=1):
        seen = np.abs(bt - temperature_at(height)) < 2.5
        assert seen.any()
        # The satellite at 74 E is south-west of Northeast India: tops appear north-east of the truth.
        assert lat[seen].mean() > lat[truth == k].mean()
        assert lon[seen].mean() > lon[truth == k].mean()


def test_run_demo_passes_and_writes_files(tmp_path, capsys):
    result = run_demo(tmp_path / "demo", plot=False)
    assert result["passed"]
    for row, (_, _, _, height, _) in zip(result["storms"], STORMS):
        assert row["corrected_offset_km"] < 4.0
        # Uncorrected offset grows with height: about h * tan(VZA), VZA ~ 34 deg here.
        assert row["uncorrected_offset_km"] == pytest.approx(height / 1000 * np.tan(np.radians(34)), rel=0.25)
    with xr.open_dataset(tmp_path / "demo" / "demo_corrected.nc") as ds:
        assert {"TIR1", "cth", "shift_km", "fill_flag"} <= set(ds.data_vars)
    assert "PASSED" in capsys.readouterr().out


def test_demo_command(tmp_path):
    assert main(["demo", "-o", str(tmp_path / "cli_demo"), "--no-plot"]) == 0
    assert (tmp_path / "cli_demo" / "demo_uncorrected.nc").exists()
