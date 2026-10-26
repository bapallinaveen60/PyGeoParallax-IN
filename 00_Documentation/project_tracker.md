# PyGeoParallax-IN: Project Progress Tracker

This document tracks the 4-month (16-week) implementation and validation roadmap for the `PyGeoParallax-IN` framework.

*Last updated: 25 Oct 2026 (commit `d43167c`; 52 tests pass, CI green on Ubuntu 3.10/3.12 and Windows 3.12).*

---

## 📈 Overall Project Health
*   **Current Phase**: 🔬 Validation done with GPM (Month 3) → moving to Month 4 (U-Net comparison, manuscript)
*   **Completed Tasks**: 🟢 11 / 15 Weeks done, 🟡 2 partly done (manuscript drafts, paper submission); Week 10 (IMD ground radar) dropped from scope
*   **Overall Progress**: `████████████████░░░░ 80%` (of the 15 weeks in scope; partly done weeks counted as half)
*   **Next Milestone**: Week 13 - U-Net comparison, uncorrected vs corrected (needs the existing model and its training data)
*   **Key result so far**: the correction moves features by the computed amount along the line of sight. Against GPM (12 cases), the median INSAT–GPM storm-top offset falls from 5.5 km to 3.1 km with parallax correction and to 1.8 km with the monsoon navigation correction as well (−0.5 km E, +2.5 km N, ±2 km). See `validation_summary.md`.

**Legend:** `[x]` done · `[~]` partly done · `[ ]` not started · `[–]` dropped from scope

---

## 📅 Week-by-Week Implementation Tracker

### Month 1 — Pipeline Setup, Data Engineering & Spatial Transformations
| Status | Week | Task Description | Target Deliverables / Verification | Notes |
| :---: | :---: | :--- | :--- | :--- |
| `[x]` | **Week 1** | Data Acquisition & Standardized Ingestion | • Ingest script for INSAT-3DR Imager, CTH, GPM 2ADPR, SRTM DEM.<br>• Resample to 0.04° grid. | **Done:** `read_insat_l1c` (L1C SGP sector, BT/albedo via LUTs, optional position offset), `read_insat_ctp` / `read_insat_csbt` (L2 CTP; it has no height, and its 82°E attribute is wrong), `read_gpm_2a` (2A Ku/DPR V08, storm tops placed on the slanted beam). 0.04° (`SOUTH_ASIA_0P04`) and 0.02° grids. 570 GPM overpasses listed; 34 validation cases downloaded. ERA5 pressure-level reader `read_era5_profiles` plus `scripts/download_era5.py`. SRTM reader `read_srtm` (GeoTIFF tiles block-averaged to 0.01°) plus `scripts/prepare_srtm.py`. See `sample_data_notes.md`. |
| `[x]` | **Week 2** | Viewing Geometry & Angle Calculation | • VZA, VAA, and SZA angle maps per INSAT scene.<br>• Verify VZA ranges across regions. | Done: `satellite_view_angles` / `solar_angles`, within 0.01° of pyorbital, computed per scene from the L1C grid. ISRO's `Sat_Elevation`/`Sat_Azimuth` are ~1° off and are not used. VZA at the cases: South 14–17°, Central 24–26°, Himalaya 33–35°, Northeast 33–38°. |
| `[x]` | **Week 3** | Geocentric ECEF Transformation Engine | • Bidirectional coordinate converter module (`src/geometry/`).<br>• Unit tests matching `pyproj` (< 1m delta). | Done: `geometry/ecef.py`, matches pyproj to < 1 mm. |
| `[x]` | **Week 4** | Cloud-Top Height Ingestion & Fallback Module | • CTH grid ingestion parser.<br>• Thermal profile lookup using ERA5 profiles when CTH is NaN. | Done: `cloudheight.py`: TIR1 BT → height via the AFGL tropical profile or per-pixel ERA5 profiles (`cloud_top_height_profiles`, searched down from each column's cold point); cloud mask from ISRO CSBT, or BT < 270 K without CTP. Kochi: r = 0.86 against ISRO CTP. **ERA5 vs AFGL on the 14 GPM cases:** cold-core height 16.75 vs 16.9 km, offsets change by < 0.5 km; the gap to GPM echo tops (12.45 km) is physical, not a profile error. ERA5 puts mid-level clouds ~0.9 km higher. |

### Month 2 — Ray-Tracing Engine, Terrain Integration & Resampling
| Status | Week | Task Description | Target Deliverables / Verification | Notes |
| :---: | :---: | :--- | :--- | :--- |
| `[x]` | **Week 5** | Analytical Ellipsoid Ray-Tracing Solver | • Quadratic ellipsoid solver in `src/geometry/`.<br>• Numba/PyCUDA acceleration (< 2s per full disk frame). | Done: `geometry/parallax.py` (enlarged ellipsoid plus Newton step, < 1 mm; within 25 m of satpy). Numba kernel: **0.5 s per full disk** (numpy ~9 s). |
| `[x]` | **Week 6** | SRTM Topographic Relief Integration | • Integrate SRTM elevation into projection loop.<br>• Generate local parallax displacement maps (km). | Done: `parallax_correct_terrain` with the SRTM grid (`--dem` in the CLI and case runner). Terrain shift map in `07_figures/paper/fig6_terrain`: ground moves 3–4+ km over the Himalaya and Tibet, 1–2 km over the Northeast hills, < 0.5 km over the Ghats and Deccan. **On the 14 GPM cases terrain changes nothing at the storms** (field and cell offsets identical); in clear sky it moves ground pixels by 1.3–2.5 km (median) up to ~5.8 km in Himalayan scenes, changing 9–19% of cells (Central India: ~0.15 km median, up to 0.65 km). |
| `[x]` | **Week 7** | BucketResampler & Gridding Strategy | • `BucketResampler` module in `src/resample/`.<br>• Max-CTH occlusion logic and IDW spatial interpolation. | Done: `resample/bucket.py` (highest-wins, IDW fill of small gaps only, `fill_flag` 0/1/2) plus `correct_scene()` (~2 s for a 1M-pixel India scene). `correct=False` gives the uncorrected Model A grid. |
| `[x]` | **Week 8** | Pipeline Automation & Batch Processing | • End-to-end orchestration pipeline runner script.<br>• Batch execution on 100 benchmark monsoon storm scenes. | Done: `pygeoparallax correct` / `batch` / `navigation` CLI and case drivers. **Benchmark on 148 monsoon scenes** (`scripts/benchmark_scenes.py`, `benchmark.md`): no failures, 1.8 s per scene (median) for read + cloud height + corrected and uncorrected regridding over India, ~450 MB. 98.7 % of cells observed, 1.3 % interpolated, 0.007 % empty; clear cells identical in corrected and uncorrected grids. 14 scenes (11–14 Jun 2023) are partial INSAT scans. |

### Month 3 — Multi-Sensor Validation & Quantitative Alignment Analysis
| Status | Week | Task Description | Target Deliverables / Verification | Notes |
| :---: | :---: | :--- | :--- | :--- |
| `[x]` | **Week 9** | Spaceborne Radar (GPM DPR) Cross-Alignment | • Colocation module between INSAT TIR1 and GPM DPR orbit tracks.<br>• Compute spatial cross-correlation & mutual information. | Done: `validation/colocate.py`, `metrics.py` (IoU, Pearson, MI, sub-cell shift). **34 cases, 4 regions, 14 usable.** Storm-top field within 250 km: median line-of-sight offset **5.4 → 3.0 km**, 10 of 12 improve; cross-look unchanged. Cell cores: raw −0.1, parallax only −5.7, both −3.3 km. The overshoot comes from navigation (~3–4 km) and BT heights (~1–2 km); the GPM beam slant adds scatter only. See `validation_summary.md`, `validation_cases.md`. |
| `[–]` | **Week 10** | Ground Radar (IMD DWR) Validation | • Volume scan extractor for Mumbai, Goa, Kochi, Agartala.<br>• Compute Intersection-over-Union (IoU) with DWR cores. | **Dropped from scope (26 Oct 2026); future work.** Not required by the thesis or the U-Net, and data access is slow and uncertain. GPM (34 cases, 4 regions) is the validation. The comparison code (`range_mask`, `compare`) is ready if IMD data become available. |
| `[x]` | **Week 11** | Regional Statistical Dissection | • Detailed statistics tables partitioned by regime.<br>• Validation of shift direction and distance trends. | Done for GPM: Northeast, Himalaya, Central and South India boxes (`REGION_BOX`). Applied shift (deep cores, median): South 4.2, Central 7.3, Himalaya 9.8, Northeast 10.5 km, following tan(VZA). Raw INSAT–GPM offset does **not** grow with VZA, because of the navigation error. Gain is clearest at VZA ≥ 30°. |
| `[x]` | **Week 12** | Sensitivity & Error Budget Analysis | • Monte Carlo simulation script perturbing CTH (+/- 1-2 km).<br>• Error propagation bounds. | Done: `monte_carlo_shift`, `bias_sweep`: error ≈ ΔCTH × tan(VZA) (~0.4 km per km at Mumbai, ~0.7 km at Agartala). **Navigation** (`navigation.py`, 13 coastline windows): seasonal; late Sep–mid Mar 7–20 km west, monsoon median +1.8 km E / +4.8 km N; same-day correction 8.8 → 4.3 km. Error budget for the overshoot in `validation_summary.md`. |

### Month 4 — Downstream Model Evaluation, Manuscript & Code Release
| Status | Week | Task Description | Target Deliverables / Verification | Notes |
| :---: | :---: | :--- | :--- | :--- |
| `[ ]` | **Week 13** | Impact on Deep Learning Segmentation | • Train two comparative U-Net models (Model A vs. Model B).<br>• Evaluate boundary edge precision over test sets. | Inputs ready, model not started. `scripts/build_paired_dataset.py` writes Model A (uncorrected) and Model B (corrected) NetCDF per scene on one grid (5 channels, `cth`, `fill_flag`, manifest; parallel, resumable; optional ERA5/DEM). Test set built: 89 of 96 designed scenes (7 slots lost to the eclipse season), paired Model A/B files in `04_corrected_output/paired/` (`events/benchmark_final.csv`). Needs the existing U-Net config, labels and its training dates (to avoid overlap with the test set). |
| `[~]` | **Week 14** | Manuscript Structuring & Figure Generation | • Outline manuscript sections.<br>• Render 3D ray-tracing diagrams and displacement vector plots. | Drafts in `08_manuscript/`: Methods (`methods_draft.md`, with verified references) and Results + Discussion (`results_discussion_draft.md`). Paper figures 1–6 from `scripts/make_paper_figures.py`. Still to do: U-Net section, Introduction, Abstract, Conclusions, ray-tracing diagram. |
| `[ ]` | **Week 15** | Manuscript Writing & Peer Review | • Compile LaTeX source file.<br>• Mathematical proof verification and self-review. | Not started. |
| `[~]` | **Week 16** | Code Packaging & Submission | • Python library packaging.<br>• Release code on GitHub and submit paper to journal. | Package installable (`pyproject.toml`, `pygeoparallax` CLI), public on GitHub with CI; README, API reference and changelog. Releases v0.1.0 (25 Oct 2026) and v0.2.0 (26 Oct 2026). Still to do: paper submission. |

### Work added along the way
| Status | Work stream | Notes |
| :---: | :--- | :--- |
| `[x]` | INSAT navigation check and correction | Coastline matching against Natural Earth; `NavigationCorrection` IDW field with acceptance rules; seasonal (yaw-flip) pattern found. `navigation_check.md`. |
| `[x]` | GPM slant-beam storm tops | `ingest.gpm.along_beam` places storm tops on the Ku beam (median 1 km, up to 5 km from the surface footprint). |
| `[x]` | Cell-by-cell core check | `analyze_core_offsets.py`: 69–73 cells in 11 cases; independent of the field correlation. |
| `[x]` | Same-day navigation near each storm | 57 daytime scans around the case dates. Night matching fails in the monsoon; daytime same-day matches scatter ~9–10 km, so per-case corrections are unreliable. Pooled near-storm correction −0.5 km E, +2.5 km N; with parallax it gives field median 1.8 km (best so far), cells −4.1 km. See `validation_summary.md`. |
| `[ ]` | More South and Central India cases | Only 2–3 usable each. |

---

## 📐 Reference: INSAT-3DR Viewing Geometry at Validation Sites

Computed with `pygeoparallax.geometry.satellite_view_angles` (satellite at 74.0°E). The shift is the approximate cloud displacement, h × tan(VZA). Clouds appear displaced *away* from the satellite, roughly northward over India.

| Site | VZA (3DR) | VAA (3DR) | Shift, 12 km top | Shift, 16 km top | VZA (3DS, 82°E) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Kochi | 12.0° | 193° | 2.6 km | 3.4 km | 13.5° |
| Goa | 18.2° | 179° | 3.9 km | 5.3 km | 20.5° |
| Mumbai | 22.5° | 177° | 5.0 km | 6.6 km | 24.7° |
| Agartala | 34.0° | 217° | 8.1 km | 10.8 km | 29.8° |
| Himalaya (Shimla) | 36.4° | 186° | 8.8 km | 11.8 km | 36.6° |
| Himalaya (Sikkim) | 35.9° | 209° | 8.7 km | 11.6 km | 32.9° |

---

## 🎯 Quantifiable Performance Targets

Measured values are medians over the usable GPM cases (`05_validation/gpm_colocation/all_cases.csv`, 250 km window, parallax correction only).

| Evaluation Metric | Baseline (Uncorrected) | Project Target (Corrected) | Current Value (raw → corrected) | Status |
| :--- | :---: | :---: | :---: | :---: |
| **INSAT–GPM line-of-sight offset (storm top)** | — | < 3 km | 5.4 → **3.0 km** (10 of 12 improve) | 🟢 Met |
| **Cross-look offset unchanged** | — | no change | 7.8 → 7.9 km | 🟢 Met |
| **GPM DPR deep-core IoU** | 0.42 – 0.48 | 0.68 – 0.75 | 0.34 → 0.39 (7 of 13 improve) | 🟠 Below target |
| **GPM storm-top field correlation (r)** | — | — | 0.64 → 0.64 | ⚪ No change |
| **IMD DWR Core Cross-Correlation** | 0.51 | 0.82 | – | ➖ Dropped (future work) |
| **Mean Geolocation Shift Distance** | 0.0 km | 4.2 km (Ghats) / 8.6 km (Himalayas) | South 4.2 / Central 7.3 / Himalaya 9.8 / Northeast 10.5 km | 🟢 Matches geometry |
| **Downstream U-Net Edge Precision** | 0.45 | 0.62 | *TBD* | ⚪ Pending (Week 13) |

IoU and r change little because a 3–10 km shift is small compared with storm size and because GPM samples only part of each storm; the line-of-sight offset is the more direct measure.
