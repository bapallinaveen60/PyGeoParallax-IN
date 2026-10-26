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
    """Uncorrected offset against the parallax the correction applies: how much of it does GPM see?"""
    t = pd.read_csv(VAL / "all_cases.csv")
    u = t[(t.nav == "no_nav") & t.status.str.startswith("usable")].set_index("case")
    cells = pd.read_csv(VAL / "core_offsets_cells.csv")
    raw_cells = cells[cells.kind == "uncorrected"].groupby("case").along_km.median()
    field = u[u.top_valid250 == True].top_along250_before  # noqa: E712
    panels = [(field, "(a) Storm-top field (250 km)"), (raw_cells, "(b) Deep-echo cells (case median)")]
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.0), sharey=True)
    for ax, (off, title) in zip(axes, panels):
        d = pd.DataFrame({"shift": u.deep_shift_km, "off": off}).dropna()
        d["region"] = d.index.str.split("_").str[0]
        ax.plot([0, 13], [0, 13], color=INK2, lw=1.0, ls="--")
        ax.text(12.6, 11.4, "parallax fully\nvisible", ha="right", fontsize=7, color=INK2)
        ax.axhline(0, color=MUTED, lw=0.8)
        for key, (name, color, marker, _) in REGIONS.items():
            r = d[d.region == key]
            ax.scatter(r["shift"], r.off, s=30, marker=marker, color=color, ec="white", lw=0.7,
                       label=f"{name} ({len(r)})", zorder=3)
        k = np.polyfit(d["shift"], d.off, 1)
        x = np.array([d["shift"].min(), d["shift"].max()])
        ax.plot(x, np.polyval(k, x), color="#eb6834", lw=1.4)
        ax.set_title(f"{title}\n{len(d)} cases, median {d.off.median():+.1f} km, fitted slope {k[0]:+.2f}",
                     loc="left", fontsize=9)
        ax.set_xlim(0, 13)
        ax.set_xlabel("Shift applied to deep cores (BT < 220 K) [km]")
    axes[0].set_ylabel("Uncorrected offset along the line of sight [km]\n(positive: INSAT must move towards the satellite)")
    axes[0].set_ylim(-16, 18)
    axes[1].legend(loc="lower right", fontsize=7)
    save(fig, "fig3_cases")


def field_offsets(rad=250):
    """Per-case line-of-sight offset (storm-top field) in each state; only cases valid in all of them."""
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from run_all_cases import split

    t = pd.read_csv(VAL / "all_cases.csv")
    rows = []
    for case in t[(t.nav == "no_nav") & t.status.str.startswith("usable")].case:
        files = {s: VAL / f"{case}{s}.json" for s in ("", "_mnav", "_ynav", "_gnav")}
        if not all(f.exists() for f in files.values()):
            continue
        runs = {s: json.loads(f.read_text()) for s, f in files.items()}
        near = {s: r["runs"]["no_nav" if s == "" else "nav"][f"near_{rad}km"] for s, r in runs.items()}
        st = {"raw": near[""]["uncorrected"], "parallax": near[""]["corrected"],
              "nav_near": near["_ynav"]["uncorrected"], "both_near": near["_ynav"]["corrected"],
              "both_monsoon": near["_mnav"]["corrected"], "both_gpm": near["_gnav"]["corrected"]}
        st = {k: v["top"] for k, v in st.items()}
        if all(max(abs(x) for x in v["lag_cells_s_e"]) < 9.5 for v in st.values()):
            _, vaa = satellite_view_angles(*runs[""]["gpm_convection_centre"], SAT_LON)
            rows.append({k: split(v["offset_km_s_e"], float(vaa))[0] for k, v in st.items()})
    return pd.DataFrame(rows)


def fig4_states():
    base = pd.read_csv(VAL / "core_offsets_cells.csv")
    near = pd.read_csv(VAL / "core_offsets_ynav_cells.csv")
    gpm = pd.read_csv(VAL / "core_offsets_gnav_cells.csv")
    field = field_offsets()
    # (cell table, cell kind, field column, label)
    states = [(base, "uncorrected", "raw", "Raw"),
              (base, "corrected", "parallax", "Parallax\nonly"),
              (near, "nav_parallax", "both_near", "Coastline nav.\n+ parallax"),
              (gpm, "nav_parallax", "both_gpm", "GPM nav.\n+ parallax")]
    n = len(states)
    fig, ax = plt.subplots(figsize=(7.0, 3.9))
    ax.axhline(0, color=INK2, lw=0.9)
    ax.axvspan(n - 1.5, n - 0.5, color="#f0efec", lw=0, zorder=0)
    data = [tab[tab.kind == k].along_km.dropna().values for tab, k, _, _ in states]
    bp = ax.boxplot(data, positions=range(n), widths=0.45, whis=(10, 90), showfliers=False, patch_artist=True,
                    medianprops={"color": INK, "lw": 1.6}, whiskerprops={"color": MUTED}, capprops={"color": MUTED})
    for patch in bp["boxes"]:
        patch.set(facecolor=BLUE_RAMP[1], edgecolor=BLUE_RAMP[4], lw=1.0)
    for i, (_, _, f, _) in enumerate(states):
        ax.scatter(i + 0.33, field[f].mean(), marker="D", s=36, color="#eb6834", ec="white", lw=0.8, zorder=4)
        ax.text(i - 0.3, np.median(data[i]), f"{np.median(data[i]):+.1f}", ha="right", va="center", fontsize=8, color=INK)
    ax.set_xticks(range(n), [s[3] for s in states], color=INK2)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("Line-of-sight offset, GPM minus INSAT [km]")
    handles = [plt.Rectangle((0, 0), 1, 1, fc=BLUE_RAMP[1], ec=BLUE_RAMP[4], label=f"Cell cores (n≈{len(data[0])}; box 25–75 %, whiskers 10–90 %)"),
               plt.Line2D([], [], marker="D", ls="", color="#eb6834", mec="white", ms=6, label=f"Field correlation, mean of {len(field)} cases")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=8, ncol=2)
    ax.set_xlim(-0.8, n - 0.4)
    ax.set_title("Offsets by correction state. Coastline navigation: pooled monsoon value of each year;\n"
                 "shaded: navigation fitted to the GPM cells of the other cases (leave one out)", loc="left", fontsize=9)
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


def fig0_schematic(vza_deg=35.0):
    """Cross-section (not to scale) of cloud and terrain parallax for a geostationary view."""
    from matplotlib.patches import Arc, FancyArrowPatch, Polygon

    t = np.tan(np.radians(vza_deg))
    los = np.array([np.sin(np.radians(vza_deg)), -np.cos(np.radians(vza_deg))])  # downwards, away from the satellite
    blue, orange = "#2a78d6", "#eb6834"
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.set_axis_off()
    ax.plot([-6, 66], [0, 0], color=INK2, lw=1.2)
    ax.text(-6, -0.9, "ellipsoid\n(navigation\nsurface)", ha="left", va="top", fontsize=8, color=INK2)

    # Cloud: anvil with its top at height h above the true position T.
    h, xt = 12.0, 16.0
    anvil = np.array([[xt - 9, h - 1.6], [xt - 7, h - 0.2], [xt - 3, h + 0.4], [xt, h], [xt + 3, h + 0.4],
                      [xt + 7, h - 0.2], [xt + 9, h - 1.6], [xt + 2.5, h - 2.4], [xt + 2, 1.0], [xt - 2, 1.0], [xt - 2.5, h - 2.4]])
    ax.add_patch(Polygon(anvil, closed=True, fc="#e7f1fb", ec=blue, lw=1.0))
    xa = xt + h * t  # apparent position
    top = (xt - (23 - h) * t, 23.0)  # where the line of sight leaves the frame, towards the satellite
    ax.plot(*zip(top, (xt, h)), color=blue, lw=1.4)
    ax.plot([xt, xa], [h, 0], color=blue, lw=1.4, ls=(0, (4, 3)))
    ax.plot(xt, h, "o", color=INK, ms=4, zorder=5)
    ax.annotate("cloud top", (xt, h), xytext=(xt + 1.2, h + 1.6), fontsize=8, color=INK)
    ax.plot([xt, xt], [0, h], color=MUTED, lw=0.8, ls=":")
    ax.annotate("", xy=(xt - 3.5, h), xytext=(xt - 3.5, 0), arrowprops={"arrowstyle": "<->", "color": INK2, "lw": 0.8})
    ax.text(xt - 4.3, h / 2, "$h$", ha="right", va="center", fontsize=10, color=INK)
    ax.plot(xt, 0, "^", color=INK, ms=7, zorder=5)
    ax.text(xt - 0.6, -1.0, "true position\n(corrected)", ha="right", va="top", fontsize=8, color=INK)
    ax.plot(xa, 0, "v", color=blue, ms=7, zorder=5)
    ax.text(xa + 0.6, -1.0, "apparent position\n(as navigated)", ha="left", va="top", fontsize=8, color=blue)
    ax.add_patch(FancyArrowPatch((xa, 2.2), (xt, 2.2), arrowstyle="-|>", mutation_scale=10, color=orange, lw=1.4))
    ax.text(xa + 1.0, 2.2, "parallax shift\n" + r"$\approx h\,\tan(\mathrm{VZA})$", ha="left", va="center", fontsize=8, color=orange)
    ax.add_patch(Arc((xa, 0), 9, 9, theta1=90, theta2=90 + vza_deg, color=INK2, lw=0.8))
    ax.plot([xa, xa], [0, 5.2], color=MUTED, lw=0.8, ls=":")
    ax.text(xa - 1.1, 5.4, "VZA", fontsize=8, color=INK2, ha="right")

    # Terrain: a ridge whose summit is also seen displaced away from the satellite.
    xr = np.linspace(40, 58, 60)
    zr = 4.0 * np.exp(-((xr - 48) / 4.0) ** 2)
    ax.fill_between(xr, 0, zr, color="#e1e0d9", lw=0)
    ax.plot(xr, zr, color=INK2, lw=1.0)
    zg, xg = 4.0, 48.0
    xga = xg + zg * t
    ax.plot([xg - 7 * los[0] * 1.6, xg], [zg - 7 * los[1] * 1.6, zg], color=blue, lw=1.4)
    ax.plot([xg, xga], [zg, 0], color=blue, lw=1.4, ls=(0, (4, 3)))
    ax.plot(xg, zg, "o", color=INK, ms=4, zorder=5)
    ax.plot(xga, 0, "v", color=blue, ms=7, zorder=5)
    ax.add_patch(FancyArrowPatch((xga, -0.5), (xg, -0.5), arrowstyle="-|>", mutation_scale=9, color=orange, lw=1.2))
    ax.text(xg + 1.5, -1.3, "terrain parallax\n(clear sky)", ha="center", va="top", fontsize=8, color=orange)
    ax.text(xg, zg + 0.7, "summit", ha="center", fontsize=8, color=INK)

    ax.text(top[0] + 3.0, top[1] - 0.6, "line of sight to INSAT-3DR\n(36 000 km above 74°E)", fontsize=8, color=blue,
            ha="left", va="top")
    ax.text(64, 21, "away from the satellite\n(northwards over India)", ha="right", va="center", fontsize=8, color=INK2)
    ax.annotate("", xy=(64, 18.6), xytext=(52, 18.6), arrowprops={"arrowstyle": "-|>", "color": INK2, "lw": 0.8})
    ax.set_xlim(-7, 66)
    ax.set_ylim(-5, 25)
    ax.set_title("Cloud and terrain parallax in geostationary imagery (not to scale)", loc="left")
    save(fig, "fig0_schematic")


#: SRTM tiles that could not be read in full (lat0, lat1, lon0, lon1); hatched on the map. None at present.
DAMAGED_SRTM = []


def main():
    fig1_geometry()
    fig2_navigation()
    fig3_cases()
    fig4_states()
    fig5_heights()
    fig6_terrain(damaged=DAMAGED_SRTM)


if __name__ == "__main__":
    main()
