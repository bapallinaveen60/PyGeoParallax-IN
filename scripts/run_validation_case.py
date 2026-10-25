"""Run one GPM validation case: INSAT-3DR vs GPM 2A Ku, before and after parallax correction.

Steps:

1. Read the INSAT L1C case scan. Optionally apply a same-day navigation
   correction (JSON from ``pygeoparallax navigation``).
2. Cloud-top height per pixel: TIR1 BT through the AFGL tropical profile.
   ISRO's clear-sky BT (from the matching CTP file) is the cloud-mask
   reference, and ISRO's CTP height is reported as a check. Without a CTP
   file, the cloud mask is BT < 270 K and the check is skipped.
3. Parallax-correct and regrid to ``--res`` degrees, along with an uncorrected
   copy on the same grid.
4. Rasterise the GPM footprints (nearest within 3.5 km) and compare:
   * cold cloud (BT < 235 K) vs echo (Z > 25 dBZ): IoU, correlation,
     mutual information, best-lag offset;
   * deep cores (BT < 220 K) vs GPM convective rain, and vs deep echoes
     (storm top > 8 km): IoU;
   * near the storm, the offset is also measured against GPM storm-top
     height, a second radar field that describes the same storm tops as TIR1.
5. Report the INSAT scan time at the convection's latitude vs the GPM time.

Usage:
    python scripts/run_validation_case.py --dir <case folder> --case northeast_20240818 \
        --scan 18AUG2024_2215 --bbox 21 29 88 97 --nav 05_validation/nav_corrections/18AUG2024.json
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np

from pygeoparallax import correct_scene
from pygeoparallax.cloudheight import TROPICAL, cloud_top_height, height_from_pressure
from pygeoparallax.geometry import parallax_correct, parallax_shift, satellite_view_angles
from pygeoparallax.ingest import read_gpm_2a, read_insat_csbt, read_insat_ctp, read_insat_l1c
from pygeoparallax.navigation import NavigationCorrection
from pygeoparallax.resample import Grid, sample_nearest
from pygeoparallax.validation import compare, iou, range_mask, subcell_displacement

SAT_LON = 74.0
COLD_BT, DEEP_BT, ECHO_DBZ, DEEP_TOP_M = 235.0, 220.0, 25.0, 8000.0
SCAN_MIN, SCAN_LAT = 26.9, (81.0, -81.0)
SLANT_TOPS = True  # place GPM storm tops on the slanted beam (see ingest.gpm.along_beam)


def find(folder, pattern):
    hits = sorted(glob.glob(str(Path(folder) / pattern)))
    if not hits:
        raise FileNotFoundError(f"no {pattern} in {folder}")
    return hits[0]


def insat_time_at(lat, start):
    frac = (SCAN_LAT[0] - lat) / (SCAN_LAT[0] - SCAN_LAT[1])
    return np.datetime64(start) + np.timedelta64(int(SCAN_MIN * 60 * frac), "s")


def gpm_on_grid(path, grid, bbox):
    gpm = read_gpm_2a(path, bbox=bbox)
    glat, glon = np.meshgrid(grid.lats, grid.lons, indexing="ij")
    lat, lon = gpm["lat"].values, gpm["lon"].values
    near = lambda v: sample_nearest(lat, lon, v, glat, glon, max_distance_km=3.5)  # noqa: E731
    # Storm tops sit on the slanted Ku beam, up to ~5 km from the surface footprint (GPM's
    # own parallax). Place them there when the reader provides the beam positions.
    if SLANT_TOPS and "top_lat" in gpm.coords:
        tlat = np.where(np.isfinite(gpm["top_lat"].values), gpm["top_lat"].values, lat)
        tlon = np.where(np.isfinite(gpm["top_lon"].values), gpm["top_lon"].values, lon)
        near_top = lambda v: sample_nearest(tlat, tlon, v, glat, glon, max_distance_km=3.5)  # noqa: E731
    else:
        near_top = near
    covered = np.isfinite(near(np.ones(lat.shape)))
    ptype = gpm["precip_type"].values
    conv = ptype == 2
    rc, cc = np.where(conv & (lat >= bbox[0]) & (lat <= bbox[1]) & (lon >= bbox[2]) & (lon <= bbox[3]))
    centre, n_box = None, int(rc.size)
    if rc.size:
        # Centre on the densest convective cluster (1-degree bins), not the mean of all
        # convection, which can fall between two separate storms.
        clat, clon = lat[rc, cc], lon[rc, cc]
        counts, ey, ex = np.histogram2d(clat, clon, bins=[np.arange(bbox[0], bbox[1] + 1), np.arange(bbox[2], bbox[3] + 1)])
        iy, ix = np.unravel_index(np.argmax(counts), counts.shape)
        y0, x0 = (ey[iy] + ey[iy + 1]) / 2, (ex[ix] + ex[ix + 1]) / 2
        in_cluster = np.hypot(clat - y0, (clon - x0) * np.cos(np.radians(y0))) < 1.35  # ~150 km
        centre = (float(clat[in_cluster].mean()), float(clon[in_cluster].mean()))
        rc, cc = rc[in_cluster], cc[in_cluster]
    t_conv = gpm["time"].values[int(np.median(rc))] if rc.size else gpm["time"].values[len(lat) // 2]
    return {
        "covered": covered,
        "z": np.where(covered, near(np.nan_to_num(gpm["z_near_surface"].values, nan=0.0)), np.nan),
        "convective": near(ptype.astype(float)) == 2,
        "deep": near_top(np.nan_to_num(gpm["storm_top_height"].values, nan=0.0)) > DEEP_TOP_M,
        "top": np.where(covered, near_top(np.nan_to_num(gpm["storm_top_height"].values, nan=0.0)), np.nan),
        "conv_centre": centre,
        "time_conv": str(t_conv)[:19],
        "n_convective": n_box,
        "n_convective_cluster": int(rc.size),
        "storm_top_max_km": float(np.nanmax(gpm["storm_top_height"].values[conv]) / 1000) if conv.any() else None,
    }


def metrics(ds, gpm, max_lag):
    bt = ds["TIR1"].values
    valid = gpm["covered"] & np.isfinite(bt)
    m = compare(bt, gpm["z"], COLD_BT, ECHO_DBZ, valid=valid, max_lag=max_lag)
    m["iou_deep_vs_convective"] = iou(bt < DEEP_BT, gpm["convective"], valid)
    m["iou_deep_vs_deep_echo"] = iou(bt < DEEP_BT, gpm["deep"], valid)
    return {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else int(v)) for k, v in m.items()}


def near_metrics(ds, gpm, grid, centre, radius_km, max_lag):
    """Metrics inside ``radius_km`` of the GPM convection centre, with the offset in km."""
    bt = ds["TIR1"].values
    valid = gpm["covered"] & np.isfinite(bt) & range_mask(grid, centre[0], centre[1], radius_km)
    m = compare(bt, gpm["z"], COLD_BT, ECHO_DBZ, valid=valid, max_lag=max_lag)
    km_s = m["lag_dy_sub"] * grid.res * 111.2
    km_e = m["lag_dx_sub"] * grid.res * 111.2 * np.cos(np.radians(centre[0]))
    return {
        "iou": round(float(m["iou"]), 4), "pearson": round(float(m["pearson"]), 4),
        "lag_cells_s_e": [m["lag_dy_sub"], m["lag_dx_sub"]],
        "offset_km_s_e": [round(float(km_s), 1), round(float(km_e), 1)],
        "offset_km": round(float(np.hypot(km_s, km_e)), 1),
        "iou_deep_vs_deep_echo": round(float(iou(bt < DEEP_BT, gpm["deep"], valid)), 4),
        "top": top_offset(bt, gpm, grid, centre, valid, max_lag),
    }


def top_offset(bt, gpm, grid, centre, valid, max_lag):
    """Offset of INSAT cloud tops against GPM storm-top height (a second, independent radar field)."""
    dy, dx, r = subcell_displacement(-bt, gpm["top"], max_lag, valid)
    km_s = dy * grid.res * 111.2
    km_e = dx * grid.res * 111.2 * np.cos(np.radians(centre[0]))
    return {"lag_cells_s_e": [round(float(dy), 2), round(float(dx), 2)],
            "offset_km_s_e": [round(float(km_s), 1), round(float(km_e), 1)], "r": round(float(r), 4)}


def run(args, nav):
    grid = Grid(*args.bbox, res=args.res)
    pad = (args.bbox[0] - 1, args.bbox[1] + 1, args.bbox[2] - 1, args.bbox[3] + 1)
    l1c = read_insat_l1c(find(args.dir, f"3RIMG_{args.scan}_L1C_SGP*.h5"), channels=("TIR1", "WV"), bbox=pad,
                         position_offset_km=nav)
    lat, lon, bt = l1c["lat"].values, l1c["lon"].values, l1c["TIR1"].values
    try:
        ctp_path = find(args.dir, f"3RIMG_{args.scan}_L2B_CTP*.h5")
    except FileNotFoundError:
        ctp_path = None
    if ctp_path is None:
        # No ISRO CTP file: fixed-threshold cloud mask (BT < 270 K) and no CTP check.
        cth = cloud_top_height(bt, None, TROPICAL)
        ctp_h = np.full(bt.shape, np.nan)
        check = {"ctp_file": "missing; cloud mask = BT < 270 K"}
    else:
        csbt, ctp = read_insat_csbt(ctp_path), read_insat_ctp(ctp_path)
        clear_bt = sample_nearest(csbt["lat"].values, csbt["lon"].values, csbt["clear_sky_bt"].values, lat, lon, 40.0)
        cth = cloud_top_height(bt, clear_bt, TROPICAL)
        ctp_h = sample_nearest(ctp["lat"].values, ctp["lon"].values, height_from_pressure(ctp["ctp"].values), lat, lon, 30.0)
        both = np.isfinite(cth) & np.isfinite(ctp_h)
        deep = both & (bt < DEEP_BT)
        check = {
            "pixels_compared": int(both.sum()),
            "corr_bt_vs_ctp_height": round(float(np.corrcoef(cth[both], ctp_h[both])[0, 1]), 3) if both.sum() > 2 else None,
            "bias_km_bt_minus_ctp": round(float(np.mean(cth[both] - ctp_h[both]) / 1000), 2) if both.any() else None,
            "deep_core_bt_height_km": round(float(np.median(cth[deep]) / 1000), 2) if deep.any() else None,
            "deep_core_ctp_height_km": round(float(np.median(ctp_h[deep]) / 1000), 2) if deep.any() else None,
        }
    channels = {"TIR1": bt, "WV": l1c["WV"].values}
    cor = correct_scene(lat, lon, channels, cth, sat_lon=SAT_LON, grid=grid)
    raw = correct_scene(lat, lon, channels, cth, sat_lon=SAT_LON, grid=grid, correct=False)
    return l1c, cth, ctp_h, cor, raw, check


def figure(cor, raw, gpm, grid, centre, out_png, title):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from scipy import ndimage

    ext = [grid.lon_min, grid.lon_max, grid.lat_min, grid.lat_max]
    conv = np.where(gpm["convective"], 1.0, np.nan)
    # Close the small gaps between footprints so the swath outline is one line (display only).
    swath = ndimage.binary_fill_holes(ndimage.binary_closing(gpm["covered"], iterations=3)).astype(float)
    fig, axes = plt.subplots(1, 3, figsize=(17, 6.2), constrained_layout=True)
    for ax, ds, name in ((axes[0], raw, "Uncorrected"), (axes[1], cor, "Parallax-corrected")):
        im = ax.imshow(ds["TIR1"].values, extent=ext, origin="upper", cmap="gray_r", vmin=190, vmax=300)
        ax.contour(grid.lons, grid.lats, swath, levels=[0.5], colors="tab:blue", linewidths=1.0)
        ax.contourf(grid.lons, grid.lats, conv, levels=[0.5, 1.5], colors="red", alpha=0.4)
        ax.contour(grid.lons, grid.lats, ds["TIR1"].values, levels=[DEEP_BT], colors="gold", linewidths=0.9)
        ax.set_title(f"{name} TIR1\nred: GPM convective, yellow: BT {DEEP_BT:.0f} K, blue: GPM swath", fontsize=10)
        if centre:
            ax.set_xlim(centre[1] - 2.0, centre[1] + 2.0)
            ax.set_ylim(centre[0] - 2.0, centre[0] + 2.0)
        fig.colorbar(im, ax=ax, shrink=0.75, label="K")
    im = axes[2].imshow(cor["shift_km"].values, extent=ext, origin="upper", cmap="viridis", vmin=0, vmax=12)
    axes[2].set_title("Parallax displacement (km)", fontsize=10)
    fig.colorbar(im, ax=axes[2], shrink=0.75, label="km")
    fig.suptitle(title, fontsize=12)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=120)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", required=True, help="folder with the case's INSAT and GPM files")
    ap.add_argument("--case", required=True)
    ap.add_argument("--scan", required=True, help="INSAT scan stamp, e.g. 18AUG2024_2215")
    ap.add_argument("--bbox", nargs=4, type=float, required=True, metavar=("LAT_MIN", "LAT_MAX", "LON_MIN", "LON_MAX"))
    ap.add_argument("--res", type=float, default=0.02)
    ap.add_argument("--nav", help="navigation correction JSON; also runs without it for comparison")
    ap.add_argument("--nav-only", action="store_true", help="with --nav, skip the run without navigation correction")
    ap.add_argument("--max-lag", type=int, default=8, help="lag search in grid cells")
    ap.add_argument("--out", default=".")
    args = ap.parse_args(argv)
    out = Path(args.out)

    grid = Grid(*args.bbox, res=args.res)
    gpm = gpm_on_grid(find(args.dir, "2A.GPM.*"), grid, tuple(args.bbox))
    summary = {"case": args.case, "insat_scan": args.scan, "grid_res_deg": args.res,
               "gpm_time_at_convection": gpm["time_conv"], "gpm_convective_footprints": gpm["n_convective"],
               "gpm_convective_cluster": gpm["n_convective_cluster"],
               "gpm_storm_top_max_km": gpm["storm_top_max_km"], "gpm_convection_centre": gpm["conv_centre"],
               "runs": {}}
    if gpm["conv_centre"]:
        vza, _ = satellite_view_angles(*gpm["conv_centre"], SAT_LON)
        summary["vza_at_convection_deg"] = round(float(vza), 1)
        lat_c, lon_c = parallax_correct(gpm["conv_centre"][0], gpm["conv_centre"][1], 15000.0, SAT_LON)
        d, _ = parallax_shift(*gpm["conv_centre"], lat_c, lon_c)
        summary["shift_km_for_15km_top"] = round(float(d) / 1000, 1)

    variants = [] if (args.nav and args.nav_only) else [("no_nav", None)]
    if args.nav:
        variants.append(("nav", NavigationCorrection.from_json(args.nav)))
    for tag, nav in variants:
        l1c, cth, ctp_h, cor, raw, check = run(args, nav)
        t_ins = insat_time_at(gpm["conv_centre"][0] if gpm["conv_centre"] else np.mean(args.bbox[:2]), l1c.attrs["start_time"])
        cold = cor["TIR1"].values < DEEP_BT
        summary["runs"][tag] = {
            "navigation_offset_km_mean": l1c.attrs.get("position_offset_km"),
            "insat_time_at_convection": str(t_ins),
            "minutes_gpm_minus_insat": round(float((np.datetime64(gpm["time_conv"]) - t_ins) / np.timedelta64(1, "s") / 60), 1),
            "height_check_vs_isro_ctp": check,
            "shift_km_deep_cores_median": round(float(np.nanmedian(cor["shift_km"].values[cold])), 2) if cold.any() else None,
            "uncorrected": metrics(raw, gpm, args.max_lag),
            "corrected": metrics(cor, gpm, args.max_lag),
        }
        if gpm["conv_centre"]:
            for radius in (150, 250):
                summary["runs"][tag][f"near_{radius}km"] = {
                    kind: near_metrics(ds, gpm, grid, gpm["conv_centre"], radius, 10)
                    for kind, ds in (("uncorrected", raw), ("corrected", cor))
                }
        nc = out / "04_corrected_output" / "netcdf"
        nc.mkdir(parents=True, exist_ok=True)
        cor.to_netcdf(nc / f"{args.case}_{tag}_corrected.nc")
        raw.to_netcdf(nc / f"{args.case}_{tag}_uncorrected.nc")
        figure(cor, raw, gpm, grid, gpm["conv_centre"], out / "07_figures" / f"{args.case}_{tag}.png",
               f"{args.case} ({'with' if nav else 'without'} navigation correction)")

    js = out / "05_validation" / "gpm_colocation" / f"{args.case}.json"
    js.parent.mkdir(parents=True, exist_ok=True)
    js.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
