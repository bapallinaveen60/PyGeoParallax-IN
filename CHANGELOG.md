# Changelog

## 0.4.1 (2026-10-31)

### Added
- **`pygeoparallax demo`** (also `pygeoparallax.demo.run_demo`): a self-test that needs no data. Three storms with known heights and positions over Northeast India are seen through an exact simulation of the INSAT-3DR view, corrected, and checked against their true positions (each within one pixel). Writes NetCDF files and a before/after figure.
- **Colab notebook** `colab/try_pygeoparallax.ipynb` with a README button: install, demo, and correction of an uploaded L1C file, in the browser.
- **`CONTRIBUTING.md`** (issues, development setup, tests, support) and a JOSS paper draft (`paper/`).
- **U-Net A/B helpers:** `scripts/run_unet_ab.py` (trains all tasks and models, resumable, then compares) and `scripts/plot_unet_curves.py` (training-loss curves).

## 0.4.0 (2026-10-30)

Easier use of the tool: L1C files can be corrected in one command, on a regular grid or on their own pixel grid, and the correction height can be lowered for precipitation work. The correction itself is unchanged.

### Added
- **`pygeoparallax l1c`:** corrects INSAT-3DR L1C files directly: reads the channels, derives cloud-top height from TIR1 (AFGL tropical atmosphere, or ERA5 with `--era5`) and writes NetCDF. Options for a region (`--bbox`), terrain (`--dem`), navigation correction, an uncorrected baseline and parallel processing.
- **Correction on the native pixel grid:** `correct_native` (also `pygeoparallax l1c --native`) puts the corrected scene back on the input's own pixels, with the same occlusion-aware resampling. `NativeGrid` describes an L1C-style grid (regular in WGS84 Mercator northing). This is the method used for the U-Net patches (`scripts/build_unet_patches.py`), now in the library.
- **Effective height:** `cloudheight.effective_height(cth, scale, offset)` and the CLI options `--height-scale` / `--height-offset` (for `l1c`, `correct` and `batch`). They correct with a lower height than the infrared top, which suits precipitation products better (median infrared top 3.2 km above the GPM storm top).
- **Tutorial:** `notebooks/quickstart.ipynb`, from one L1C file to corrected output, with figures.
- **Tests** for the native grid, the native-grid correction, the effective height and the `l1c` command (64 tests).

## 0.3.0 (2026-10-26)

Full GPM validation (38 usable cases, 2018–2024), the investigation of why most of the parallax is not visible against GPM, and the U-Net A/B retraining package. No changes to the correction itself.

### Added
- **More validation cases:** batch 4 (2018–2021, South and Central India); 63 cases processed, 38 usable. Case scans pinned in `00_Documentation/events/case_scans.csv`.
- **Per-year navigation:** `scripts/yearly_navigation.py` pools each monsoon's daytime coastline matches (all-years value when a year has fewer than 8).
- **GPM-derived navigation test:** `scripts/gpm_navigation.py` (leave-one-case-out) and the `gnav` state in `scripts/run_navigation_states.py`.
- **Diagnostics:** `scripts/check_parallax_visibility.py` (overlays of uncorrected and corrected INSAT on GPM storm tops).
- **U-Net A/B:** `scripts/build_unet_patches.py` (parallax correction of the U-Net training patches on their own L1C pixel grid), `scripts/pack_unet_dataset.py`, `scripts/train_unet_ab.py` (the group's attention U-Net; TensorFlow 2.15 or Keras 3; per-epoch checkpoint and resume), `scripts/compare_unet_ab.py` (paired scene bootstrap), `colab/unet_ab_colab.ipynb`.
- **Paper figures:** Fig. 3 now plots the uncorrected offset against the applied shift; Fig. 4 includes the GPM-navigation state.
- **Manuscript** reframed around the full validation (“the limits of validation against GPM radar”), with four new verified references.

### Findings
- The correction leaves the cross-look offset unchanged (median change 0.0 km, −0.2 … +0.2) and reverses the mean storm-scale offset (+2.2 → −1.9 km), but the per-case gain is not significant (18 of 30 cases, sign p = 0.36).
- Uncorrected INSAT cold cores already sit on the GPM deep-echo cells (−0.1 km); correction moves them 4.7 km past (p < 0.001). Only about 5 % of the computed parallax is visible.
- Navigation fitted to the GPM cells centres them but leaves the storm-scale agreement worse than uncorrected (Wilcoxon p = 0.027); no single translation centres both measures. GPM validation of absolute position is limited to about ±3–5 km.

## 0.2.1 (2026-10-26)

Validation statistics, citation metadata (first release archived on Zenodo), a ray-tracing schematic and the LaTeX manuscript. No changes to the correction itself.

### Added
- **Validation statistics:** `scripts/validation_statistics.py` (bootstrap intervals, cluster bootstrap for cells, Wilcoxon and sign tests, viewing-angle trend).
- **Citation files:** `CITATION.cff` (validated) and `.zenodo.json` for a Zenodo DOI.
- **Ray-tracing schematic** (`make_paper_figures.py`, `fig0_schematic`).
- **LaTeX manuscript** (`08_manuscript/latex_source/`, generated sections via `08_manuscript/md_to_latex.py`).

### Findings
- With 12 cases, parallax correction improves the field offset with moderate evidence (sign test p = 0.039; Wilcoxon p = 0.13) and leaves the cross-look offset unchanged (change 0.0 km, 95 % interval −0.3 … +0.2). Adding the navigation correction is not significantly better in the field measure (p = 0.91) but significantly reduces the cell-measure overshoot (p = 0.002). The viewing-angle trend of the raw offset is not constrained (slope interval −19 … +15 km per unit tan VZA).

## 0.2.0 (2026-10-26)

ERA5 and SRTM inputs, navigation near the storms, a benchmark, and the paired dataset for the U-Net comparison.

### Added
- **ERA5 profiles:** `read_era5_profiles` (CDS pressure-level NetCDF, geopotential to geometric height), `cloud_top_height_profiles` (per-pixel bilinear profiles, lookup down from each column's cold point), `scripts/download_era5.py`, `--profile era5` in the case driver and `scripts/compare_variants.py`.
- **SRTM:** `read_srtm` (GeoTIFF tiles block-averaged to a coarse grid while reading; damaged parts of a tile are skipped with a warning), `scripts/prepare_srtm.py`, `--dem` in the case driver, `compare_variants.py --variant dem`, and a terrain parallax map (`make_paper_figures.py`, Fig. 6). `rasterio` added to the `dev` extras.
- **Case scans pinned** in `00_Documentation/events/case_scans.csv`; the file-name fallback now only accepts L1C files from the case date outside navigation time slots (navigation scans from neighbouring days were being picked).
- **Near-storm navigation:** `scripts/near_storm_navigation.py` measures daytime coastline offsets around each case date and writes per-case and pooled corrections; `analyze_core_offsets.py --nav-tag` selects which navigation runs to analyse.
- **Benchmark:** `scripts/benchmark_scenes.py` (148 scenes: 1.8 s per scene, no failures; `00_Documentation/benchmark.md`). A test checks that clear cells are identical in corrected and uncorrected grids.
- **Methods draft** (`08_manuscript/methods_draft.md`) with verified references.
- **Paired dataset builder:** `scripts/build_paired_dataset.py` writes Model A (uncorrected) and Model B (corrected) NetCDF per scene on the same grid, with a manifest; parallel and resumable, optional ERA5 heights and DEM. `scripts/design_benchmark_set.py` chooses the 96-scene benchmark / test set.
- **Paper figures:** `scripts/make_paper_figures.py` (Figs. 1–6); Fig. 4 shows the near-storm and all-India navigation corrections.

### Findings
- ERA5 instead of the AFGL standard atmosphere changes cold-core heights by −0.15 km and the INSAT–GPM offsets by under 0.5 km; the overshoot is not a profile error.
- Navigation near the storms: night matching fails in the monsoon and same-day daytime matches scatter ~9–10 km, so per-case corrections are unreliable. The pooled near-storm correction (−0.5 km E, +2.5 km N) with parallax gives the closest field agreement so far (median 1.8 km over 12 cases); cells −4.1 km.
- INSAT-3DR L1C scenes of 11–14 June 2023 are partial scans (up to 57 % fill values).
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
