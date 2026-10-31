# PyGeoParallax-IN: Project Progress Tracker

This document tracks the 4-month (16-week) implementation and validation roadmap for the `PyGeoParallax-IN` framework.

*Last updated: 30 Oct 2026 (v0.4.0 released; 64 tests pass, CI green on Ubuntu 3.10/3.12 and Windows 3.12).*

---

## 📈 Overall Project Health
*   **Current Phase**: 📝 Month 4: U-Net A/B results in and written up; manuscript complete apart from author, journal and literature checks
*   **Completed Tasks**: 🟢 13 / 15 Weeks done, 🟡 2 partly done (manuscript review and submission, code release); Week 10 (IMD ground radar) dropped from scope
*   **Overall Progress**: `███████████████████░ 93%` (of the 15 weeks in scope; partly done weeks counted as half)
*   **Next Milestone**: Week 15–16 - move the manuscript into the Copernicus (AMT) template, final read-through, and submit
*   **Key result so far**: the correction moves features by the computed amount along the line of sight only. Against GPM (38 usable cases, 2018–2024) it reverses the mean storm-scale offset (+2.2 → −1.9 km), but the per-case gain is not significant (18 of 30). At convective cores, uncorrected cold cores already sit on the GPM cells and only ~5 % of the computed parallax is visible. No single navigation shift centres both measures, so GPM can verify absolute position only to about ±3–5 km. See `validation_summary.md`. **U-Net:** retraining on corrected input gives no gain (accuracy and macro F1 within 0.0012 in all three tasks) and slightly lower convective scores (deep-convective CSI 0.041 → 0.038, p = 0.008), consistent with the cell result.

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
| `[x]` | **Week 9** | Spaceborne Radar (GPM DPR) Cross-Alignment | • Colocation module between INSAT TIR1 and GPM DPR orbit tracks.<br>• Compute spatial cross-correlation & mutual information. | Done: `validation/colocate.py`, `metrics.py` (IoU, Pearson, MI, sub-cell shift). **63 cases processed (2018–2024), 38 usable.** Storm-top field within 250 km: mean line-of-sight offset +2.2 → −1.9 km, median absolute 5.1 → 3.8 km, 18 of 30 improve (not significant); cross-look unchanged. Cell cores: raw −0.1, parallax only −4.7 km (p < 0.001). Synthetic test and overlays confirm the method; GPM-fitted navigation centres the cells but worsens the field (p = 0.027). See `validation_summary.md`, `validation_cases.md`. |
| `[–]` | **Week 10** | Ground Radar (IMD DWR) Validation | • Volume scan extractor for Mumbai, Goa, Kochi, Agartala.<br>• Compute Intersection-over-Union (IoU) with DWR cores. | **Dropped from scope (26 Oct 2026); future work.** Not required by the thesis or the U-Net, and data access is slow and uncertain. GPM (34 cases, 4 regions) is the validation. The comparison code (`range_mask`, `compare`) is ready if IMD data become available. |
| `[x]` | **Week 11** | Regional Statistical Dissection | • Detailed statistics tables partitioned by regime.<br>• Validation of shift direction and distance trends. | Done for GPM: Northeast, Himalaya, Central and South India boxes (`REGION_BOX`). Applied shift (deep cores, median): South 3.9, Central 7.3, Himalaya 9.8, Northeast 10.5 km, following tan(VZA). Raw INSAT–GPM offset does **not** grow with VZA (slope −0.8 km per unit tan VZA, interval −12.9 … +9.4); cell offsets stay within ±3 km of zero in every region. |
| `[x]` | **Week 12** | Sensitivity & Error Budget Analysis | • Monte Carlo simulation script perturbing CTH (+/- 1-2 km).<br>• Error propagation bounds. | Done: `monte_carlo_shift`, `bias_sweep`: error ≈ ΔCTH × tan(VZA) (~0.4 km per km at Mumbai, ~0.7 km at Agartala). **Navigation** (`navigation.py`, 13 coastline windows): seasonal; late Sep–mid Mar 7–20 km west (yaw flip in March and September, Prakash et al. 2014). Monsoon per-year values −2.0 … +3.0 km E, −0.8 … +2.5 km N (`yearly_navigation.py`); the north component is uncertain by several km. GPM-derived navigation (`gpm_navigation.py`) tested leave-one-case-out. |

### Month 4 — Downstream Model Evaluation, Manuscript & Code Release
| Status | Week | Task Description | Target Deliverables / Verification | Notes |
| :---: | :---: | :--- | :--- | :--- |
| `[x]` | **Week 13** | Impact on Deep Learning Segmentation | • Train two comparative U-Net models (Model A vs. Model B).<br>• Evaluate boundary edge precision over test sets. | **Done (30 Oct 2026).** The group's attention U-Net (4 BT channels TIR1/TIR2/WV/MIR, 128×128 patches, GPM DPR precipitation type) retrained twice with identical architecture, labels, mask, seed and schedule: Model A on the original patches, Model B on the same patches parallax-corrected on their own pixel grid (`build_unet_patches.py`; median shift 4.4 km). Train 5,082 patches (2018, 2021–2023), test 2,197 (Sep 2023, 2024); no validation split (it overlapped test). Trained on a GPU machine (`Insat_data/unet_gpu`). **Result** (`compare_unet_ab.py`, scene bootstrap): no gain. Accuracy and macro F1 change by at most 0.0012 in all three tasks (four-class macro F1 0.421 → 0.420, p = 0.05). Convective scores fall slightly: deep-convective CSI 0.041 → 0.038 (p = 0.008), convective CSI 0.429 → 0.428 (p = 0.039). Stratiform and rain unchanged. Caveats: small effects, 22 scores tested (none passes Bonferroni), one run per model. Manuscript Section 6.8 and Table 4. |
| `[x]` | **Week 14** | Manuscript Structuring & Figure Generation | • Outline manuscript sections.<br>• Render 3D ray-tracing diagrams and displacement vector plots. | Done. Drafts in `08_manuscript/`: Methods (`methods_draft.md`, including Section 4.8 on the U-Net experiment) and Results + Discussion (`results_discussion_draft.md`, including Section 6.8 with the U-Net results). Paper figures 0–6 from `scripts/make_paper_figures.py`. Introduction, Abstract and Conclusions in LaTeX, updated with the U-Net result. Title: the limits of validation against GPM radar. |
| `[~]` | **Week 15** | Manuscript Writing & Peer Review | • Compile LaTeX source file.<br>• Mathematical proof verification and self-review. | Full draft compiles (`08_manuscript/latex_source/main.tex`, 27 pages): 7 figures, 6 tables, 24 verified references. Sections 2–6 are generated from the Markdown drafts (`08_manuscript/md_to_latex.py`). Overleaf upload zip: `submission_versions/PyGeoParallax-IN_overleaf.zip`. Independent self-review done (26 Oct 2026) and its fixes applied. U-Net section written (30 Oct 2026). Novelty search done (30 Oct 2026, `reports/INSAT parallax correction novelty.md`); claims reworded, 18 references added (42 in total), Hydro-Estimator ATBD checked. **Journal: Atmospheric Measurement Techniques (AMT).** Sole author (Naveen Bapalli, independent researcher); AMT back matter (code and data availability, author contributions, competing interests, acknowledgements, financial support) added. Still to do: corresponding e-mail, move into the Copernicus template, final read-through, submission. |
| `[~]` | **Week 16** | Code Packaging & Submission | • Python library packaging.<br>• Release code on GitHub and submit paper to journal. | Package installable (`pyproject.toml`, `pygeoparallax` CLI), public on GitHub with CI; README, API reference and changelog. Releases v0.1.0 (25 Oct 2026), v0.2.0, v0.2.1 and v0.3.0 (26 Oct 2026), archived on Zenodo (concept DOI 10.5281/zenodo.23666957). **v0.4.0 released (30 Oct 2026, Zenodo DOI 10.5281/zenodo.23812270):** `pygeoparallax l1c` (one command from L1C files), correction on the native L1C pixel grid (`correct_native`), effective correction height (`--height-offset`), tutorial notebook `notebooks/quickstart.ipynb`; 64 tests. Still to do: paper submission. |

### Work added along the way
| Status | Work stream | Notes |
| :---: | :--- | :--- |
| `[x]` | INSAT navigation check and correction | Coastline matching against Natural Earth; `NavigationCorrection` IDW field with acceptance rules; seasonal (yaw-flip) pattern found. `navigation_check.md`. |
| `[x]` | GPM slant-beam storm tops | `ingest.gpm.along_beam` places storm tops on the Ku beam (median 1 km, up to 5 km from the surface footprint). |
| `[x]` | Cell-by-cell core check | `analyze_core_offsets.py`: 157–167 cells in 27–28 cases; independent of the field correlation. |
| `[x]` | Same-day navigation near each storm | 57 daytime scans around the case dates. Night matching fails in the monsoon; daytime same-day matches scatter ~9–10 km, so per-case corrections are unreliable. Pooled near-storm correction −0.5 km E, +2.5 km N; with parallax it gives field median 1.8 km (best so far), cells −4.1 km. See `validation_summary.md`. |
| `[x]` | More South and Central India cases | Batch 4 (2018–2021): 24 more usable cases; now South 14, Central 15. |
| `[x]` | Investigation of the invisible parallax | Synthetic test, overlays (`check_parallax_visibility.py`), ISRO DQE reports, GPM-derived navigation (`gpm_navigation.py`). Storm tilt from GPM 3-D reflectivity (`analyze_storm_tilt.py`, 31 Oct 2026): cells lean 1.5 km westward but only +0.8 km towards the satellite, so the column tilt does not hide the parallax. Navigation alone cannot explain it either; an offset of the cold top above the radar's view or a northward navigation error remain. |
| `[ ]` | More Himalaya and Northeast cases | Only 4–5 usable each. |

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

Measured values are over the usable GPM cases (`05_validation/statistics/statistics_ynav.json`, 250 km window, parallax correction only; 30 cases valid in every state).

| Evaluation Metric | Baseline (Uncorrected) | Project Target (Corrected) | Current Value (raw → corrected) | Status |
| :--- | :---: | :---: | :---: | :---: |
| **INSAT–GPM line-of-sight offset (storm top)** | — | < 3 km | median absolute 5.1 → 3.8 km (18 of 30 improve, n.s.) | 🟠 Not shown |
| **Cross-look offset unchanged** | — | no change | median change 0.0 km (−0.2 … +0.2) | 🟢 Met |
| **GPM DPR deep-core IoU** | 0.42 – 0.48 | 0.68 – 0.75 | 0.34 → 0.39 (7 of 13 improve; 2022–2024 cases) | 🟠 Below target |
| **GPM storm-top field correlation (r)** | — | — | 0.64 → 0.64 | ⚪ No change |
| **IMD DWR Core Cross-Correlation** | 0.51 | 0.82 | – | ➖ Dropped (future work) |
| **Mean Geolocation Shift Distance** | 0.0 km | 4.2 km (Ghats) / 8.6 km (Himalayas) | South 3.9 / Central 7.3 / Himalaya 9.8 / Northeast 10.5 km | 🟢 Matches geometry |
| **Downstream U-Net (test set, A → B)** | Model A | B better than A | four-class macro F1 0.421 → 0.420; deep-conv CSI 0.041 → 0.038; rain CSI 0.347 → 0.346 | 🟠 No gain |

IoU and r change little because a 3–10 km shift is small compared with storm size and because GPM samples only part of each storm; the line-of-sight offset is the more direct measure, but the field and cell measures disagree by 2–5 km, so GPM cannot verify absolute position to better than about ±3–5 km.
