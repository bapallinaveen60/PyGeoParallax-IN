"""Diagnostic overlays: is the parallax of deep convection visible between INSAT and GPM?

For each case, around the main GPM convective cluster:

- left panel: uncorrected INSAT TIR1 with GPM storm-top contours (10 and 13 km);
- right panel: the same with the parallax-corrected INSAT field.

On every GPM deep-echo cell (storm top > 10 km) the cell centroid (black cross),
the INSAT cold core found within 25 km (blue dot) and the position where
geometry says the uncorrected cold core should appear (orange triangle, the
centroid displaced away from the satellite by the computed parallax of the
local cold-core height) are marked.

Usage:
    python scripts/check_parallax_visibility.py --base <validation folder> --cases northeast_20230613 ...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import xarray as xr  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import run_all_cases  # noqa: E402
import run_validation_case as rvc  # noqa: E402
from analyze_core_offsets import centroid, cold_core  # noqa: E402

from pygeoparallax.geometry import parallax_correct  # noqa: E402
from pygeoparallax.resample import Grid  # noqa: E402

OUT = Path("07_figures/checks")


def apparent(lat, lon, h, sat_lon=74.0):
    """Where a feature at (lat, lon, h) appears in ellipsoid-navigated imagery (inverse of the correction)."""
    a = np.array([lat, lon], float)
    for _ in range(20):
        c = np.array(parallax_correct(a[0], a[1], h, sat_lon))
        a = a + (np.array([lat, lon]) - c)
    return a


def main(argv=None):
    from scipy import ndimage

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--cases", nargs="+", required=True)
    ap.add_argument("--half-width", type=float, default=1.3, help="degrees around the cluster centre")
    args = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    for case in args.cases:
        region = case.split("_")[0]
        box = run_all_cases.REGION_BOX[region]
        grid = Grid(*box, res=0.02)
        gpm = rvc.gpm_on_grid(rvc.find(Path(args.base) / case, "2A.GPM.*"), grid, box)
        c0 = gpm["conv_centre"]
        glat, glon = np.meshgrid(grid.lats, grid.lons, indexing="ij")
        nc = Path("04_corrected_output/netcdf")
        raw = xr.open_dataset(nc / f"{case}_no_nav_uncorrected.nc")
        cor = xr.open_dataset(nc / f"{case}_no_nav_corrected.nc")
        top = np.nan_to_num(gpm["top"])
        near = (np.abs(glat - c0[0]) < args.half_width) & (np.abs(glon - c0[1]) < args.half_width) & gpm["covered"]
        labels, n = ndimage.label((top > 10000) & near)
        cells = []
        for lab in range(1, n + 1):
            m = labels == lab
            if m.sum() < 8:
                continue
            g = centroid(m, glat, glon)
            core_raw = cold_core(raw["TIR1"].values, glat, glon, g[0], g[1], 25.0)
            core_cor = cold_core(cor["TIR1"].values, glat, glon, g[0], g[1], 25.0)
            h = np.nanmedian(np.where(np.hypot(glat - core_raw[0], glon - core_raw[1]) < 0.06, raw["cth"].values, np.nan))
            exp = apparent(g[0], g[1], h if np.isfinite(h) else 15000.0)
            cells.append((g, core_raw, core_cor, exp))

        fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), sharex=True, sharey=True)
        ext = [grid.lons[0], grid.lons[-1], grid.lats[-1], grid.lats[0]]
        for ax, ds, title, k in ((axes[0], raw, "Uncorrected INSAT TIR1", 1), (axes[1], cor, "Parallax-corrected INSAT TIR1", 2)):
            im = ax.imshow(ds["TIR1"].values, extent=ext, cmap="Greys", vmin=190, vmax=300, origin="upper", aspect="auto")
            ax.contour(grid.lons, grid.lats, np.where(gpm["covered"], top, np.nan), levels=[10000, 13000],
                       colors=["#eb6834", "#d03b3b"], linewidths=[0.8, 1.3])
            ax.contour(grid.lons, grid.lats, gpm["covered"].astype(float), levels=[0.5], colors="#2a78d6", linewidths=0.8)
            for g, cr, cc, ex in cells:
                ax.plot(g[1], g[0], "x", color="black", ms=8, mew=2)
                core = cr if k == 1 else cc
                if np.isfinite(core[0]):
                    ax.plot(core[1], core[0], "o", color="#2a78d6", ms=6, mec="white")
                if k == 1:
                    ax.plot(ex[1], ex[0], "^", color="#eda100", ms=7, mec="black", mew=0.5)
                    ax.annotate("", xy=(ex[1], ex[0]), xytext=(g[1], g[0]),
                                arrowprops={"arrowstyle": "-|>", "color": "#eda100", "lw": 1})
            ax.set_xlim(c0[1] - args.half_width, c0[1] + args.half_width)
            ax.set_ylim(c0[0] - args.half_width, c0[0] + args.half_width)
            ax.set_title(title, fontsize=10, loc="left")
            ax.set_xlabel("Longitude [°E]")
        axes[0].set_ylabel("Latitude [°N]")
        fig.colorbar(im, ax=axes, shrink=0.8, label="TIR1 BT [K]")
        fig.suptitle(f"{case}: GPM storm top 10 km (orange) / 13 km (red), swath edge (blue). x GPM cell, "
                     f"o INSAT cold core, ^ expected uncorrected position", fontsize=9)
        fig.savefig(OUT / f"{case}_visibility.png", dpi=110, bbox_inches="tight")
        plt.close(fig)
        dist = [np.hypot((cr[0] - g[0]) * 111.2, (cr[1] - g[1]) * 111.2 * np.cos(np.radians(g[0]))) for g, cr, _, _ in cells if np.isfinite(cr[0])]
        dexp = [np.hypot((cr[0] - ex[0]) * 111.2, (cr[1] - ex[1]) * 111.2 * np.cos(np.radians(g[0]))) for g, cr, _, ex in cells if np.isfinite(cr[0])]
        print(f"{case}: {len(cells)} cells; raw cold core to GPM cell median {np.median(dist):.1f} km, "
              f"to expected apparent position {np.median(dexp):.1f} km -> {OUT / (case + '_visibility.png')}")


if __name__ == "__main__":
    main()
