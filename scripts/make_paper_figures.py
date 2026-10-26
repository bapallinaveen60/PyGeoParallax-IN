"""Paper figures from the validation results (PNG at 300 dpi and PDF, in ``07_figures/paper/``).

1. ``fig1_geometry``: INSAT-3DR viewing zenith angle and the parallax shift of a
   12 km cloud top over India, with the four validation regions.
2. ``fig2_navigation``: INSAT-3DR L1C navigation offsets from coastline
   matching, 2022-2024, with the monsoon months shaded.
3. ``fig3_cases``: line-of-sight INSAT-GPM offset per case before and after
   parallax correction (storm-top field, 250 km window).
4. ``fig4_states``: cell-by-cell offsets in the four correction states.
5. ``fig5_heights``: INSAT cold-core height vs GPM maximum echo top per cell.
6. ``fig6_terrain``: clear-sky terrain parallax of the ground from SRTM.

Inputs are the outputs of ``run_all_cases.py``, ``test_navigation_parallax.py``,
``analyze_core_offsets.py`` and ``pygeoparallax navigation`` runs.

Usage:
    python scripts/make_paper_figures.py
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pygeoparallax.geometry import satellite_view_angles  # noqa: E402

VAL = Path("05_validation/gpm_colocation")
NAV = Path("05_validation/nav_corrections")
OUT = Path("07_figures/paper")
LAND = Path("01_raw_data/natural_earth/ne_10m_land.geojson")

INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
#: Regions in fixed categorical order (south to north-east = increasing VZA).
REGIONS = {
    "south": ("South India", "#2a78d6", "o", (8.0, 17.0, 74.0, 80.5)),
    "central": ("Central India", "#eb6834", "s", (19.0, 26.0, 76.0, 85.0)),
    "himalaya": ("Himalaya", "#1baf7a", "^", (27.0, 33.0, 75.0, 89.0)),
    "northeast": ("Northeast", "#eda100", "D", (22.0, 29.0, 89.0, 97.0)),
}
SAT_LON = 74.0

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlesize": 10, "axes.titlecolor": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "legend.frameon": False, "figure.dpi": 100,
})


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / name}.png/.pdf")


def coastlines(ax, box):
    """Natural Earth land outlines clipped to box = (lat0, lat1, lon0, lon1)."""
    from shapely.geometry import box as sbox, shape

    clip = sbox(box[2], box[0], box[3], box[1])
    for feat in json.loads(LAND.read_text())["features"]:
        geom = shape(feat["geometry"])
        if not geom.intersects(clip):
            continue
        geom = geom.intersection(clip)
        for poly in getattr(geom, "geoms", [geom]):
            if poly.geom_type == "Polygon":
                x, y = poly.exterior.xy
                ax.plot(x, y, color=INK2, lw=0.5)


def fig1_geometry():
    box = (5.0, 38.0, 65.0, 100.0)
    lat = np.arange(box[0], box[1] + 0.01, 0.1)
    lon = np.arange(box[2], box[3] + 0.01, 0.1)
    glon, glat = np.meshgrid(lon, lat)
    vza, _ = satellite_view_angles(glat, glon, SAT_LON)
    shift = 12.0 * np.tan(np.radians(vza))  # km, 12 km cloud top
    fig, ax = plt.subplots(figsize=(6.2, 5.6))
    ax.grid(False)
    levels = np.arange(0, 15, 2)
    cf = ax.contourf(glon, glat, shift, levels=levels, colors=BLUE_RAMP[: len(levels) - 1], extend="max")
    cs = ax.contour(glon, glat, vza, levels=[10, 20, 30, 40], colors="white", linewidths=0.8)
    ax.clabel(cs, fmt="VZA %d°", fontsize=7, colors="white", manual=[(78.5, 7.8), (87, 14), (93, 18), (93, 30)])
    coastlines(ax, box)
    for key, (name, color, _, (la0, la1, lo0, lo1)) in REGIONS.items():
        ax.add_patch(plt.Rectangle((lo0, la0), lo1 - lo0, la1 - la0, fill=False, ec=INK, lw=1.3))
        ax.text(lo0 + 0.3, la1 - 0.4, name, va="top", fontsize=8, color=INK, weight="bold",
                bbox={"fc": "white", "ec": "none", "alpha": 0.75, "pad": 1.2})
    ax.plot(SAT_LON, box[0] + 0.3, marker="v", color=INK, ms=7, clip_on=False)
    ax.text(SAT_LON - 0.6, box[0] + 0.4, "74°E", fontsize=7, color=INK, ha="right")
    ax.set_xlim(box[2], box[3])
    ax.set_ylim(box[0], box[1])
    ax.set_aspect(1 / np.cos(np.radians(21)))
    ax.set_xlabel("Longitude [°E]")
    ax.set_ylabel("Latitude [°N]")
    cb = fig.colorbar(cf, ax=ax, shrink=0.8, pad=0.02)
    cb.set_label("Parallax shift of a 12 km cloud top [km]", color=INK2)
    cb.outline.set_edgecolor(AXIS)
    ax.set_title("INSAT-3DR viewing geometry and parallax shift", loc="left")
    save(fig, "fig1_geometry")


def fig2_navigation():
    rows = []
    for p in sorted(NAV.glob("[0-9][0-9][A-Z][A-Z][A-Z][0-9][0-9][0-9][0-9].json")):
        j = json.loads(p.read_text())
        rows.append({"date": datetime.strptime(p.stem, "%d%b%Y"), "east": np.nanmedian(j["east_km"]),
                     "north": np.nanmedian(np.array(j["north_km"], float)), "n": len(j["east_km"])})
    df = pd.DataFrame(rows).sort_values("date")
    fig, axes = plt.subplots(2, 1, figsize=(7.0, 4.6), sharex=True)
    for ax, comp, label in ((axes[0], "east", "East correction [km]"), (axes[1], "north", "North correction [km]")):
        for year in (2022, 2023, 2024):
            ax.axvspan(datetime(year, 6, 1), datetime(year, 9, 30), color="#f0efec", lw=0)
        ax.axhline(0, color=AXIS, lw=0.8)
        many = df.n >= 3
        ax.scatter(df.date[many], df[comp][many], s=24, color=BLUE_RAMP[4], ec="white", lw=0.8, zorder=3)
        ax.scatter(df.date[~many], df[comp][~many], s=20, facecolor="white", edgecolor=BLUE_RAMP[4], lw=1.0, zorder=3)
        ax.set_ylabel(label)
    axes[0].text(datetime(2022, 7, 31), axes[0].get_ylim()[1], "monsoon", ha="center", va="top", fontsize=7, color=MUTED)
    handles = [plt.Line2D([], [], marker="o", ls="", color=BLUE_RAMP[4], mec="white", ms=6, label="3 or more coastal windows"),
               plt.Line2D([], [], marker="o", ls="", mfc="white", mec=BLUE_RAMP[4], ms=5, label="1–2 windows")]
    axes[1].legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=2, fontsize=8)
    axes[1].xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 4, 7, 10)))
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    axes[0].set_title("INSAT-3DR L1C navigation correction from coastline matching (median over windows)", loc="left")
    fig.align_ylabels(axes)
    save(fig, "fig2_navigation")


def fig3_cases():
    t = pd.read_csv(VAL / "all_cases.csv")
    u = t[(t.nav == "no_nav") & t.status.str.startswith("usable") & (t.top_valid250 == True)].copy()  # noqa: E712
    u["region"] = u.case.str.split("_").str[0]
    u = u.sort_values("vza").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(6.4, 0.32 * len(u) + 1.4))
    ax.axvline(0, color=INK2, lw=0.9)
    for i, r in u.iterrows():
        name, color, marker, _ = REGIONS[r.region]
        ax.annotate("", xy=(r.top_along250_after, i), xytext=(r.top_along250_before, i),
                    arrowprops={"arrowstyle": "-|>", "color": MUTED, "lw": 1.0, "shrinkA": 4, "shrinkB": 4})
        ax.scatter(r.top_along250_before, i, s=40, marker=marker, facecolor="white", edgecolor=color, lw=1.5, zorder=3)
        ax.scatter(r.top_along250_after, i, s=40, marker=marker, color=color, ec="white", lw=0.8, zorder=3)
    labels = [f"{REGIONS[r.region][0]}  {datetime.strptime(r.case.split('_')[1], '%Y%m%d'):%d %b %Y}  ({r.vza:.0f}°)"
              for r in u.itertuples()]
    ax.set_yticks(range(len(u)), labels, fontsize=8, color=INK2)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Line-of-sight offset, GPM minus INSAT [km]  (positive: INSAT must move towards the satellite)")
    med_b, med_a = np.median(abs(u.top_along250_before)), np.median(abs(u.top_along250_after))
    ax.set_title(f"Per-case offset before (open) and after (filled) parallax correction\n"
                 f"median |offset| {med_b:.1f} → {med_a:.1f} km, {(abs(u.top_along250_after) < abs(u.top_along250_before)).sum()} of {len(u)} improve",
                 loc="left")
    handles = [plt.Line2D([], [], marker=m, ls="", color=c, mec="white", ms=7, label=n) for n, c, m, _ in REGIONS.values()]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.4, -0.13), fontsize=8, ncol=4)
    save(fig, "fig3_cases")


def fig4_states():
    cells = pd.read_csv(VAL / "core_offsets_cells.csv")
    test = pd.read_csv(VAL / "nav_parallax_test.csv")
    field = test[(test.field == "top") & (test.window_km == 250) & test.valid]
    states = [("uncorrected", "raw", "Raw"), ("nav_only", "navigation", "Navigation only"),
              ("corrected", "parallax", "Parallax only"), ("nav_parallax", "both", "Navigation\n+ parallax")]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.axhline(0, color=INK2, lw=0.9)
    data = [cells[cells.kind == k].along_km.dropna().values for k, _, _ in states]
    bp = ax.boxplot(data, positions=range(4), widths=0.45, whis=(10, 90), showfliers=False, patch_artist=True,
                    medianprops={"color": INK, "lw": 1.6}, whiskerprops={"color": MUTED}, capprops={"color": MUTED})
    for patch in bp["boxes"]:
        patch.set(facecolor=BLUE_RAMP[1], edgecolor=BLUE_RAMP[4], lw=1.0)
    for i, (_, f, _) in enumerate(states):
        m = field[f"along_{f}"].mean()
        ax.scatter(i + 0.33, m, marker="D", s=36, color="#eb6834", ec="white", lw=0.8, zorder=4)
        ax.text(i - 0.3, np.median(data[i]), f"{np.median(data[i]):+.1f}", ha="right", va="center", fontsize=8, color=INK)
    ax.set_xticks(range(4), [s[2] for s in states], color=INK2)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("Line-of-sight offset, GPM minus INSAT [km]")
    handles = [plt.Rectangle((0, 0), 1, 1, fc=BLUE_RAMP[1], ec=BLUE_RAMP[4], label=f"Cell cores (n≈{len(data[0])}; box 25–75 %, whiskers 10–90 %)"),
               plt.Line2D([], [], marker="D", ls="", color="#eb6834", mec="white", ms=6, label=f"Field correlation, mean of {len(field)} cases")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.16), fontsize=8, ncol=2)
    ax.set_xlim(-0.8, 3.6)
    ax.set_title("Offsets in the four correction states (monsoon navigation +1.8 km E, +4.8 km N)", loc="left")
    save(fig, "fig4_states")


def fig5_heights():
    cells = pd.read_csv(VAL / "core_offsets_cells.csv")
    h = cells[cells.kind == "heights"].dropna(subset=["insat_core_height_km", "gpm_top_max_km"]).copy()
    h["region"] = h.case.str.split("_").str[0]
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    ax.plot([5, 19], [5, 19], color=AXIS, lw=1.0)
    ax.text(18.6, 18.2, "1:1", color=MUTED, fontsize=8, ha="right")
    for key, (name, color, marker, _) in REGIONS.items():
        r = h[h.region == key]
        ax.scatter(r.gpm_top_max_km, r.insat_core_height_km, s=26, marker=marker, color=color, ec="white", lw=0.7,
                   label=f"{name} ({len(r)})", zorder=3)
    ax.axhline(17.0, color=MUTED, lw=0.8, ls="--")
    ax.text(5.2, 17.15, "tropopause cap", fontsize=7, color=MUTED)
    ax.set_xlim(5, 19)
    ax.set_ylim(5, 19)
    ax.set_aspect("equal")
    ax.set_xlabel("GPM maximum echo top in the cell [km]")
    ax.set_ylabel("INSAT cold-core height from TIR1 BT [km]")
    gap = np.median(h.insat_core_height_km - h.gpm_top_max_km)
    ax.set_title(f"Cloud-top heights, {len(h)} matched cells\nmedian INSAT minus GPM: {gap:+.1f} km", loc="left")
    ax.legend(loc="lower right", fontsize=8)
    save(fig, "fig5_heights")


def fig6_terrain(dem_path=Path("02_standardized_grid/srtm_0p01deg.nc"), damaged=()):
    import xarray as xr

    from pygeoparallax.geometry import parallax_correct, parallax_shift

    if not dem_path.exists():
        print(f"skip fig6_terrain: no {dem_path} (run scripts/prepare_srtm.py)")
        return
    dem = xr.open_dataset(dem_path)["elevation"].coarsen(lat=5, lon=5, boundary="trim").mean()
    glon, glat = np.meshgrid(dem.lon.values, dem.lat.values)
    h = np.where(dem.values > 0, dem.values, np.nan)
    lat_c, lon_c = parallax_correct(glat, glon, h, SAT_LON)
    shift, _ = parallax_shift(glat, glon, lat_c, lon_c)
    shift = shift / 1000.0
    box = (6.0, 38.0, 68.0, 98.0)
    fig, ax = plt.subplots(figsize=(6.6, 6.2))
    ax.grid(False)
    levels = [0, 0.25, 0.5, 1, 1.5, 2, 3, 4]
    cf = ax.contourf(glon, glat, shift, levels=levels, colors=BLUE_RAMP, extend="max")
    coastlines(ax, box)
    for la0, la1, lo0, lo1 in damaged:
        ax.add_patch(plt.Rectangle((lo0, la0), lo1 - lo0, la1 - la0, fill=False, ec=MUTED, hatch="///", lw=0.6))
    if damaged:
        ax.text(damaged[0][2] + 0.3, damaged[0][0] + 0.3, "DEM tile damaged", fontsize=7, color=INK2,
                bbox={"fc": "white", "ec": "none", "alpha": 0.8, "pad": 1})
    for key, (name, _, _, (la0, la1, lo0, lo1)) in REGIONS.items():
        ax.add_patch(plt.Rectangle((lo0, la0), lo1 - lo0, la1 - la0, fill=False, ec=INK, lw=1.0, ls="--"))
    ax.set_xlim(box[2], box[3])
    ax.set_ylim(box[0], box[1])
    ax.set_aspect(1 / np.cos(np.radians(22)))
    ax.set_xlabel("Longitude [°E]")
    ax.set_ylabel("Latitude [°N]")
    cb = fig.colorbar(cf, ax=ax, shrink=0.8, pad=0.02)
    cb.set_label("Terrain parallax shift of the ground [km]", color=INK2)
    cb.outline.set_edgecolor(AXIS)
    ax.set_title("Clear-sky terrain parallax from SRTM (0.05° mean elevation)", loc="left")
    save(fig, "fig6_terrain")


#: SRTM tiles that could not be read in full (lat0, lat1, lon0, lon1); re-download to fill them.
DAMAGED_SRTM = [(18.0, 24.0, 74.0, 80.0), (18.0, 24.0, 80.0, 86.0), (18.0, 24.0, 92.0, 98.0)]


def main():
    fig1_geometry()
    fig2_navigation()
    fig3_cases()
    fig4_states()
    fig5_heights()
    fig6_terrain(damaged=DAMAGED_SRTM)


if __name__ == "__main__":
    main()
