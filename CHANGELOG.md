# Changelog

## Unreleased

### Added
- **ERA5 profiles:** `read_era5_profiles` (CDS pressure-level NetCDF, geopotential to geometric height), `cloud_top_height_profiles` (per-pixel bilinear profiles, lookup down from each column's cold point), `scripts/download_era5.py`, `--profile era5` in the case driver and `scripts/compare_variants.py`.
- **SRTM:** `read_srtm` (GeoTIFF tiles block-averaged to a coarse grid while reading; damaged parts of a tile are skipped with a warning), `scripts/prepare_srtm.py`, `--dem` in the case driver, `compare_variants.py --variant dem`, and a terrain parallax map (`make_paper_figures.py`, Fig. 6). `rasterio` added to the `dev` extras.
- **Paper figures:** `scripts/make_paper_figures.py` (Figs. 1–6).

### Findings
- ERA5 instead of the AFGL standard atmosphere changes cold-core heights by −0.15 km and the INSAT–GPM offsets by under 0.5 km; the overshoot is not a profile error.
- Terrain-aware correction leaves the storm results unchanged (cloud tops are far above the ground) but moves clear-sky ground in Himalayan scenes by 1.3–2.5 km (median), up to ~5.8 km.

## 0.1.0 (2026-10-25)

First release: the full correction pipeline for INSAT-3DR, a navigation correction, and validation against GPM.

### Added
- **Readers:** INSAT-3DR Imager L1C SGP (BT/albedo via lookup tables, region subsetting, optional position offset), L2B cloud-top pressure and clear-sky BT, GPM 2A Ku/DPR V08 (storm tops placed on the slanted beam).
- **Geometry:** WGS84 ECEF transforms (< 1 mm against pyproj), satellite and solar angles (within 0.01° of pyorbital), ellipsoid ray-tracing parallax solver with Newton refinement (within 25 m of satpy) and a Numba kernel (0.5 s per full disk), terrain-aware correction.
- **Cloud-top height** from TIR1 BT with the AFGL tropical profile (17 km tropopause cap) and a clear-sky BT or 270 K cloud mask.
- **Resampling:** occlusion-aware bucket resampling (highest cloud wins), IDW gap fill, `fill_flag` per cell; `correct_scene()` for the whole pipeline.
- **Navigation:** coastline matching against Natural Earth in 13 windows, `NavigationCorrection` (IDW field with acceptance rules).
- **Validation:** IoU, Pearson r, mutual information, whole-cell and sub-cell displacement, colocation helpers, regional statistics, Monte Carlo and bias sensitivity.
- **CLI:** `pygeoparallax correct`, `batch` (parallel) and `navigation`.
- **Scripts** for GPM overpass search, convection screening, case runs and analysis.
- CI on Ubuntu (Python 3.10, 3.12) and Windows (3.12).

### Findings
- INSAT-3DR L1C navigation error is seasonal: 7–20 km west correction from late September to mid March, small in the monsoon (median +1.8 km E, +4.8 km N).
- Against GPM (14 usable monsoon cases, 4 regions) the median storm-top offset falls from 5.4 to 3.0 km; correct navigation and parallax together. See `00_Documentation/validation_summary.md`.

### Not yet included
- SRTM and ERA5 readers, IMD DWR validation, U-Net comparison.
