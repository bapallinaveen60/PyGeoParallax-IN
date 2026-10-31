"""Compare parallax-corrected INSAT-3DR and Meteosat (IODC) cold cores with GPM deep-echo cells.

Both satellites see the same cloud tops from different directions (INSAT at
74 E, Meteosat-8 at 41.5 E until May 2022, Meteosat-9 at 45.5 E after). After
each is corrected for its own parallax, they should put a cloud top in the
same place:

* if both corrected cold cores lie at the same offset from the GPM cell, the
  offset is real: the cold top is displaced from the radar echo;
* if the Meteosat cores sit on the GPM cells and the INSAT cores do not, the
  difference is an INSAT navigation error.

For each case with Meteosat crops from ``download_seviri_iodc.py``:

1. Each Meteosat cycle is corrected with its own cloud-top height (10.8 um BT,
   AFGL tropical atmosphere, BT < 270 K) onto the case's 0.02 degree grid, the
   grid of the INSAT runs in ``04_corrected_output/netcdf``.
2. Storm motion is the displacement between the two Meteosat cycles (field
   correlation of the corrected images near the convective cluster). The
   Meteosat positions are moved to the GPM time with it.
3. For each GPM deep-echo cell (as in ``analyze_core_offsets.py``) the cold
   core is found in the INSAT and Meteosat images, uncorrected and corrected,
   and its offset from the cell is given as east and north components.
4. The whole cloud field of corrected INSAT is matched to corrected Meteosat
   (field correlation within ``--radius`` km): the INSAT minus Meteosat
   displacement, after the motion adjustment.

The whole-field displacement (step 4) is the decisive number. The cell
measure of step 3 is attenuated on real scenes: shifting the INSAT images by
4.4 and 8.9 km moves the cell offsets by a median of 71 % and 64 % of the
shift (mean about 40 %), because large cold anvils clip the 25 km cold-core
search. A test with copies of an INSAT image shifted by 5 and 6.5 km recovers
the field displacement to 0.2 km and the motion to 0.01 km/min.

Writes ``05_validation/seviri/seviri_cells.csv`` and ``seviri_cases.csv`` and
prints a summary.

Usage:
    python scripts/compare_seviri_insat.py --base <validation folder> [--seviri <crops folder>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
import analyze_core_offsets as aco  # noqa: E402
import run_all_cases  # noqa: E402
import run_validation_case as rvc  # noqa: E402
from download_seviri_iodc import DEFAULT_OUT  # noqa: E402

from pygeoparallax.cloudheight import cloud_top_height  # noqa: E402
from pygeoparallax.geometry import satellite_view_angles  # noqa: E402
from pygeoparallax.pipeline import correct_scene  # noqa: E402
from pygeoparallax.resample import Grid  # noqa: E402
from pygeoparallax.validation import range_mask, subcell_displacement  # noqa: E402

KM_PER_DEG = 111.2


def en_km(lat0, a, b):
    """Vector from point a to point b [(lat, lon) degrees] as (east, north) km."""
    return ((b[1] - a[1]) * KM_PER_DEG * np.cos(np.radians(lat0)), (b[0] - a[0]) * KM_PER_DEG)


def shift_en(grid, lat0, dy, dx):
    """subcell_displacement shift (rows south, columns east) as (east, north) km."""
    return dx * grid.res * KM_PER_DEG * np.cos(np.radians(lat0)), -dy * grid.res * KM_PER_DEG


def field_shift(a, b, window, grid, lat0, max_lag):
    """(east, north, r): how far features of ``a`` must move to match ``b``, near the storm."""
    valid = window & np.isfinite(a) & np.isfinite(b)
    if valid.sum() < 200:
        return np.nan, np.nan, np.nan
    a = np.where(window, a, np.nan)
    b = np.where(window, b, np.nan)
    dy, dx, r = subcell_displacement(a, b, max_lag=max_lag, valid=valid)
    e, n = shift_en(grid, lat0, dy, dx)
    return e, n, r


def load_seviri(path, grid, fill_radius):
    """A cropped Meteosat cycle: uncorrected and corrected TIR1 on ``grid``, line time at each row, satellite."""
    ds = xr.open_dataset(path)
    lat, lon, bt = ds["lat"].values, ds["lon"].values, ds["TIR1"].values
    sat_lon = float(ds.attrs["sub_satellite_longitude"])
    cth = cloud_top_height(bt)
    common = dict(sat_lon=sat_lon, grid=grid, fill_radius=fill_radius)
    raw = correct_scene(lat, lon, {"TIR1": bt}, cth, correct=False, **common)["TIR1"].values
    cor = correct_scene(lat, lon, {"TIR1": bt}, cth, **common)["TIR1"].values
    times = ds["acq_time"].values if "acq_time" in ds else None
    line_lat = np.nanmean(lat, axis=1)
    return {"raw": raw, "cor": cor, "sat_lon": sat_lon, "platform": ds.attrs.get("platform_name", ""),
            "times": times, "line_lat": line_lat, "file": Path(path).name}


def time_at(sev, lat0):
    """Acquisition time of the Meteosat line nearest ``lat0`` (falls back to the file-name time)."""
    if sev["times"] is not None and np.isfinite(sev["line_lat"]).any():
        i = int(np.nanargmin(np.abs(sev["line_lat"] - lat0)))
        t = sev["times"][i]
        if not np.isnat(t):
            return np.datetime64(t, "s")
    stamp = sev["file"].rsplit("_", 1)[-1].replace(".nc", "")
    return np.datetime64(f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True, help="validation folder (GPM files)")
    ap.add_argument("--seviri", default=str(DEFAULT_OUT), help="folder with the cropped Meteosat cycles")
    ap.add_argument("--radius", type=float, default=250.0, help="km around the GPM convective cluster")
    ap.add_argument("--search", type=float, default=25.0, help="km around each GPM cell to look for the cold core")
    ap.add_argument("--min-cells", type=int, default=8, help="smallest deep-echo cell, in 0.02 deg grid cells")
    ap.add_argument("--max-lag", type=int, default=10, help="field-correlation search, in grid cells")
    ap.add_argument("--fill-radius", type=int, default=3, help="gap filling for the coarser Meteosat pixels [cells]")
    ap.add_argument("--out", default="05_validation/seviri")
    args = ap.parse_args(argv)

    cases = sorted(p.name for p in Path(args.seviri).iterdir() if p.is_dir() and any(p.glob("*.nc")))
    if not cases:
        raise SystemExit(f"no Meteosat crops in {args.seviri}: run download_seviri_iodc.py first")
    cells_out, case_out = [], []
    for case in cases:
        d = json.loads((Path("05_validation/gpm_colocation") / f"{case}.json").read_text())
        t_gpm = np.datetime64(d["gpm_time_at_convection"], "s")
        box = run_all_cases.REGION_BOX[case.split("_")[0]]
        grid = Grid(*box, res=0.02)
        glat, glon = np.meshgrid(grid.lats, grid.lons, indexing="ij")
        gpm = rvc.gpm_on_grid(rvc.find(Path(args.base) / case, "2A.GPM.*"), grid, box)
        cen = gpm["conv_centre"]
        window = range_mask(grid, cen[0], cen[1], args.radius) & gpm["covered"]
        ins = {k: xr.open_dataset(f"04_corrected_output/netcdf/{case}_no_nav_{f}.nc")["TIR1"].values
               for k, f in (("raw", "uncorrected"), ("cor", "corrected"))}

        sev = [load_seviri(p, grid, args.fill_radius) for p in sorted((Path(args.seviri) / case).glob("*.nc"))]
        for s in sev:
            s["t"] = time_at(s, cen[0])
        sev.sort(key=lambda s: s["t"])
        motion = (np.nan, np.nan, np.nan)            # east km/min, north km/min, r
        if len(sev) >= 2:
            minutes = float((sev[-1]["t"] - sev[0]["t"]) / np.timedelta64(1, "s")) / 60.0
            e, n, r = field_shift(sev[0]["cor"], sev[-1]["cor"], window, grid, cen[0], args.max_lag)
            if minutes > 0 and np.isfinite(e):
                motion = (e / minutes, n / minutes, r)
        near = min(sev, key=lambda s: abs(float((s["t"] - t_gpm) / np.timedelta64(1, "s"))))
        dt_min = float((t_gpm - near["t"]) / np.timedelta64(1, "s")) / 60.0
        adv = (motion[0] * dt_min, motion[1] * dt_min) if np.isfinite(motion[0]) else (0.0, 0.0)
        vza_sev = float(satellite_view_angles(cen[0], cen[1], near["sat_lon"])[0])

        # Whole-field match of corrected INSAT to corrected Meteosat (Meteosat moved to the GPM time).
        fe, fn, fr = field_shift(near["cor"], ins["cor"], window, grid, cen[0], args.max_lag)
        re_, rn, rr = field_shift(near["raw"], ins["raw"], window, grid, cen[0], args.max_lag)
        case_out.append({
            "case": case, "region": case.split("_")[0], "platform": near["platform"], "sat_lon": near["sat_lon"],
            "vza_meteosat": round(vza_sev, 1), "dt_gpm_minus_meteosat_min": round(dt_min, 1),
            "motion_east_kmmin": round(motion[0], 3), "motion_north_kmmin": round(motion[1], 3), "motion_r": round(motion[2], 2),
            # INSAT minus Meteosat position of the cloud field, after moving Meteosat to the GPM time
            "field_cor_east_km": round(fe - adv[0], 2), "field_cor_north_km": round(fn - adv[1], 2), "field_cor_r": round(fr, 2),
            "field_raw_east_km": round(re_ - adv[0], 2), "field_raw_north_km": round(rn - adv[1], 2), "field_raw_r": round(rr, 2),
        })

        labels, n = ndimage.label((np.nan_to_num(gpm["top"]) > 10000) & window)
        for lab in range(1, n + 1):
            m = labels == lab
            if m.sum() < args.min_cells:
                continue
            g = aco.centroid(m, glat, glon)
            row = {"case": case, "cell_lat": round(g[0], 3), "cell_lon": round(g[1], 3)}
            for src, fields, shift in (("insat", ins, (0.0, 0.0)), ("meteosat", near, adv)):
                for state in ("raw", "cor"):
                    c = aco.cold_core(fields[state], glat, glon, g[0], g[1], args.search)
                    if np.isfinite(c[0]):
                        e, n_ = en_km(g[0], g, c)       # cold core minus GPM cell
                        row[f"{src}_{state}_east_km"] = round(e + shift[0], 2)
                        row[f"{src}_{state}_north_km"] = round(n_ + shift[1], 2)
            cells_out.append(row)
        print(f"{case:22s} {near['platform']:12s} VZA {vza_sev:4.1f}  dt {dt_min:+5.1f} min  "
              f"INSAT-Meteosat (corrected field) E {fe - adv[0]:+5.1f} N {fn - adv[1]:+5.1f} km (r {fr:.2f})", flush=True)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cells, cases_df = pd.DataFrame(cells_out), pd.DataFrame(case_out)
    cells.to_csv(out / "seviri_cells.csv", index=False)
    cases_df.to_csv(out / "seviri_cases.csv", index=False)

    def boot(df, col, n=5000, seed=2026):
        rng = np.random.default_rng(seed)
        groups = [g[col].dropna().values for _, g in df.groupby("case") if col in g and g[col].notna().any()]
        if not groups:
            return np.nan, np.nan, np.nan, 0
        meds = [np.median(np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])) for _ in range(n)]
        return float(np.median(np.concatenate(groups))), float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5)), len(groups)

    print(f"\n{len(cases_df)} cases, {len(cells)} GPM cells. Median with 95 % interval (cluster bootstrap over cases):")
    print("Cold core minus GPM cell [km]:")
    for src in ("insat", "meteosat"):
        for state in ("raw", "cor"):
            parts = []
            for comp in ("east", "north"):
                m, lo, hi, nc = boot(cells, f"{src}_{state}_{comp}_km")
                parts.append(f"{comp} {m:+5.1f} [{lo:+5.1f}, {hi:+5.1f}]")
            print(f"  {src:8s} {'corrected' if state == 'cor' else 'uncorrected':11s} " + "   ".join(parts) + f"  ({nc} cases)")
    print("INSAT minus Meteosat, whole cloud field near the storm [km] (median over cases):")
    for state in ("cor", "raw"):
        e, n_ = cases_df[f"field_{state}_east_km"], cases_df[f"field_{state}_north_km"]
        print(f"  {'corrected' if state == 'cor' else 'uncorrected':11s} east {e.median():+5.1f}  north {n_.median():+5.1f}  ({e.notna().sum()} cases)")
    print(f"wrote {out / 'seviri_cells.csv'} and {out / 'seviri_cases.csv'}")


if __name__ == "__main__":
    main()
