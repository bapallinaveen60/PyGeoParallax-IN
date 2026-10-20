"""Case study: 6 June 2022, deep convection over Kochi, GPM orbit 046997 overhead at ~17:13 UTC.

Steps:

1. Read the INSAT-3DR L1C scans (16:45 and 17:15) and the matching ISRO CTP files.
2. Cloud-top height per pixel: TIR1 brightness temperature mapped through the
   AFGL tropical profile, with ISRO's clear-sky BT as the cloud-mask reference.
3. Check those heights against ISRO's cloud-top pressure, converted to
   height with the same profile.
4. Parallax-correct both scans and regrid them, along with uncorrected copies,
   onto a 0.02 degree grid.
5. Rasterise GPM 2A Ku onto the same grid and compare satellite vs radar
   before and after correction.
6. Estimate storm motion between the two scans. The scans are ~13-17 min away
   from the GPM time, which moves storms by a few km: the same order as the
   parallax shift at Kochi.

Usage:
    python scripts/run_kochi_case.py --data datasets
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np

from pygeoparallax import correct_scene
from pygeoparallax.cloudheight import TROPICAL, cloud_top_height, height_from_pressure
from pygeoparallax.geometry import satellite_view_angles
from pygeoparallax.ingest import read_gpm_2a, read_insat_csbt, read_insat_ctp, read_insat_l1c
from pygeoparallax.resample import Grid, sample_nearest
from pygeoparallax.validation import best_displacement, compare, iou

KOCHI = (9.96, 76.29)
BBOX = (6.0, 14.0, 72.0, 80.5)
GRID = Grid(*BBOX, res=0.02)
SAT_LON = 74.0
GPM_ORBIT = "046997"
SCANS = ("1645", "1715")
COLD_BT = 235.0  # K, cold cloud
DEEP_BT = 220.0  # K, deep convective core
ECHO_DBZ = 25.0  # near-surface reflectivity defining a radar echo


def scan_time_at(lat, start, end, lat_top=81.0, lat_bottom=-81.0):
    """Approximate time the north-to-south full-disk scan reaches ``lat``."""
    start = np.datetime64(start)
    end = np.datetime64(end)
    frac = (lat_top - lat) / (lat_top - lat_bottom)
    return start + (end - start) * frac


def find(data, pattern):
    hits = sorted(glob.glob(str(Path(data) / "**" / pattern), recursive=True))
    if not hits:
        raise FileNotFoundError(f"no file matching {pattern} under {data}")
    return hits[0]


def gpm_on_grid(path):
    gpm = read_gpm_2a(path, bbox=BBOX)
    glat, glon = np.meshgrid(GRID.lats, GRID.lons, indexing="ij")
    lat, lon = gpm["lat"].values, gpm["lon"].values
    # Ku footprints are ~5 km apart: give each grid cell its nearest footprint within 3.5 km.
    covered = np.isfinite(sample_nearest(lat, lon, np.ones(lat.shape), glat, glon, max_distance_km=3.5))
    z = sample_nearest(lat, lon, np.nan_to_num(gpm["z_near_surface"].values, nan=0.0), glat, glon, 3.5)
    ptype = sample_nearest(lat, lon, gpm["precip_type"].values.astype(float), glat, glon, 3.5)
    top = sample_nearest(lat, lon, gpm["storm_top_height"].values, glat, glon, 3.5)
    t = gpm["time"].values
    near = (np.abs(lat - KOCHI[0]) < 1.0).any(axis=1)
    return {
        "covered": covered, "z": np.where(covered, z, np.nan), "convective": ptype == 2,
        "storm_top": top, "time": str(t[near][len(t[near]) // 2]) if near.any() else str(t[len(t) // 2]),
        "raw": gpm,
    }


def process_scan(data, scan, nav_offset=None):
    l1c = read_insat_l1c(find(data, f"3RIMG_06JUN2022_{scan}_L1C_SGP*.h5"), channels=("TIR1", "WV"), bbox=BBOX,
                         position_offset_km=nav_offset)
    ctp_path = find(data, f"3RIMG_06JUN2022_{scan}_L2B_CTP*.h5")
    csbt = read_insat_csbt(ctp_path)
    ctp = read_insat_ctp(ctp_path)
    lat, lon = l1c["lat"].values, l1c["lon"].values
    bt = l1c["TIR1"].values

    clear_bt = sample_nearest(csbt["lat"].values, csbt["lon"].values, csbt["clear_sky_bt"].values, lat, lon, 40.0)
    cth = cloud_top_height(bt, clear_bt, TROPICAL)

    # Check against ISRO: their CTP converted to height, nearest box within 30 km.
    ctp_h = sample_nearest(ctp["lat"].values, ctp["lon"].values, height_from_pressure(ctp["ctp"].values), lat, lon, 30.0)
    ctt = sample_nearest(ctp["lat"].values, ctp["lon"].values, ctp["ctt"].values, lat, lon, 30.0)
    both = np.isfinite(cth) & np.isfinite(ctp_h)
    deep = both & (bt < DEEP_BT)
    check = {
        "pixels_compared": int(both.sum()),
        "bias_km_bt_minus_ctp": float(np.mean(cth[both] - ctp_h[both]) / 1000) if both.any() else None,
        "corr": float(np.corrcoef(cth[both], ctp_h[both])[0, 1]) if both.sum() > 2 else None,
        "deep_core_bt_height_km": float(np.median(cth[deep]) / 1000) if deep.any() else None,
        "deep_core_ctp_height_km": float(np.median(ctp_h[deep]) / 1000) if deep.any() else None,
        "isro_ctp_min_hpa_near_kochi": float(np.nanmin(np.where(np.hypot(lat - KOCHI[0], lon - KOCHI[1]) < 1.0,
                                                              sample_nearest(ctp["lat"].values, ctp["lon"].values, ctp["ctp"].values, lat, lon, 30.0), np.nan))),
    }

    channels = {"TIR1": bt, "WV": l1c["WV"].values}
    cor = correct_scene(lat, lon, channels, cth, sat_lon=SAT_LON, grid=GRID)
    raw = correct_scene(lat, lon, channels, cth, sat_lon=SAT_LON, grid=GRID, correct=False)
    for ds in (cor, raw):
        ds.attrs.update({k: l1c.attrs[k] for k in ("start_time", "end_time", "satellite")})
        ds.attrs["cth_source"] = "TIR1 BT + AFGL tropical profile; ISRO CSBT_TIR1 cloud mask"
    t_kochi = scan_time_at(KOCHI[0], l1c.attrs["start_time"], l1c.attrs["end_time"])
    return {"l1c": l1c, "cth": cth, "ctp_h": ctp_h, "ctt": ctt, "cor": cor, "raw": raw,
            "check": check, "time_at_kochi": str(t_kochi.astype("datetime64[s]"))}


def metrics(ds, gpm):
    bt = ds["TIR1"].values
    valid = gpm["covered"] & np.isfinite(bt)
    m = compare(bt, gpm["z"], COLD_BT, ECHO_DBZ, valid=valid, max_lag=6)
    m["iou_deep_vs_convective"] = iou(bt < DEEP_BT, gpm["convective"], valid)
    return {k: (float(v) if isinstance(v, (float, np.floating)) else int(v)) for k, v in m.items()}


def figure(results, gpm, out_png):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    scan = results["1715"]
    ext = [GRID.lon_min, GRID.lon_max, GRID.lat_min, GRID.lat_max]
    fig, axes = plt.subplots(2, 2, figsize=(12, 11), constrained_layout=True)
    conv = np.where(gpm["convective"], 1.0, np.nan)
    swath = gpm["covered"].astype(float)
    for ax, key, title in ((axes[0, 0], "raw", "Uncorrected"), (axes[0, 1], "cor", "Parallax-corrected")):
        im = ax.imshow(scan[key]["TIR1"].values, extent=ext, origin="upper", cmap="gray_r", vmin=190, vmax=300)
        ax.contour(GRID.lons, GRID.lats, swath, levels=[0.5], colors="tab:blue", linewidths=0.8)
        ax.contourf(GRID.lons, GRID.lats, conv, levels=[0.5, 1.5], colors="red", alpha=0.35)
        ax.contour(GRID.lons, GRID.lats, scan[key]["TIR1"].values, levels=[DEEP_BT], colors="yellow", linewidths=0.8)
        ax.plot(KOCHI[1], KOCHI[0], "c^", ms=9)
        ax.set_title(f"{title} TIR1, 17:15 scan\nred: GPM convective; yellow: BT {DEEP_BT:.0f} K; blue: GPM swath",
                     fontsize=10)
        ax.set_xlim(74.5, 78.5)
        ax.set_ylim(8.0, 12.0)
        fig.colorbar(im, ax=ax, shrink=0.8, label="K")
    im = axes[1, 0].imshow(scan["cor"]["shift_km"].values, extent=ext, origin="upper", cmap="viridis", vmin=0, vmax=4)
    axes[1, 0].set_title("Parallax displacement (km)")
    axes[1, 0].plot(KOCHI[1], KOCHI[0], "r^", ms=9)
    fig.colorbar(im, ax=axes[1, 0], shrink=0.8, label="km")
    ax = axes[1, 1]
    ok = np.isfinite(scan["cth"]) & np.isfinite(scan["ctp_h"])
    ax.hexbin(scan["ctp_h"][ok] / 1000, scan["cth"][ok] / 1000, gridsize=40, mincnt=1, cmap="magma_r")
    ax.plot([0, 17], [0, 17], "k--", lw=0.8)
    ax.set_xlabel("ISRO CTP converted to height (km)")
    ax.set_ylabel("TIR1 BT height (km)")
    ax.set_title("Per-pixel BT height vs ISRO CTP height (17:15)")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=130)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default="datasets")
    ap.add_argument("--out", default=".")
    ap.add_argument("--nav-offset", nargs=2, type=float, metavar=("EAST_KM", "NORTH_KM"),
                    help="INSAT navigation correction to apply (see scripts/check_navigation.py)")
    args = ap.parse_args(argv)
    out = Path(args.out)
    tag = "" if args.nav_offset is None else f"_nav{args.nav_offset[0]:+g}e{args.nav_offset[1]:+g}n"

    gpm = gpm_on_grid(find(args.data, f"2A.GPM.Ku.*.{GPM_ORBIT}.*.HDF5"))
    results = {s: process_scan(args.data, s, args.nav_offset) for s in SCANS}

    vza, vaa = satellite_view_angles(*KOCHI, SAT_LON)
    summary = {
        "case": "2022-06-06 Kochi",
        "gpm_orbit": GPM_ORBIT,
        "insat_position_offset_km": args.nav_offset,
        "gpm_time_near_kochi": gpm["time"],
        "kochi_vza_deg": float(vza),
        "kochi_vaa_deg": float(vaa),
        "scans": {},
    }
    for s, r in results.items():
        cor, raw = r["cor"], r["raw"]
        cold = cor["TIR1"].values < DEEP_BT
        summary["scans"][s] = {
            "insat_time_at_kochi": r["time_at_kochi"],
            "minutes_from_gpm": float((np.datetime64(r["time_at_kochi"]) - np.datetime64(gpm["time"][:19])) / np.timedelta64(1, "m")),
            "height_check_vs_isro_ctp": r["check"],
            "shift_km_deep_cores_median": float(np.nanmedian(cor["shift_km"].values[cold])) if cold.any() else None,
            "shift_km_max": float(np.nanmax(cor["shift_km"].values)),
            "uncorrected": metrics(raw, gpm),
            "corrected": metrics(cor, gpm),
        }
        nc = out / "04_corrected_output" / "netcdf"
        nc.mkdir(parents=True, exist_ok=True)
        cor.to_netcdf(nc / f"kochi_20220606_{s}{tag}_corrected.nc")
        raw.to_netcdf(nc / f"kochi_20220606_{s}{tag}_uncorrected.nc")

    # Storm motion between the two scans (uncorrected grids), in cells of GRID.res degrees.
    dy, dx, r = best_displacement(results["1645"]["raw"]["TIR1"].values, results["1715"]["raw"]["TIR1"].values, max_lag=15)
    km_per_cell = GRID.res * 111.2
    speed = np.hypot(dy * km_per_cell, dx * km_per_cell * np.cos(np.radians(KOCHI[0]))) / 30.0
    summary["storm_motion_1645_to_1715"] = {
        "dy_cells_south": int(dy), "dx_cells_east": int(dx), "corr": float(r),
        "speed_km_per_min": float(speed),
        "displacement_km_in_13_min": float(speed * 13.0),
    }

    js = out / "05_validation" / "gpm_colocation" / f"kochi_20220606{tag}.json"
    js.parent.mkdir(parents=True, exist_ok=True)
    js.write_text(json.dumps(summary, indent=2))
    figure(results, gpm, out / "07_figures" / f"kochi_20220606{tag}.png")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
