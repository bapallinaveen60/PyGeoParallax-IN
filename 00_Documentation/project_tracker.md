# PyGeoParallax-IN: Project Progress Tracker

This document tracks the 4-month (16-week) implementation and validation roadmap for the `PyGeoParallax-IN` framework.

---

## 📈 Overall Project Health
*   **Current Phase**: 🏁 Initialization & Data Engineering (Month 1)
*   **Completed Tasks**: 🟢 1 / 16 Weeks
*   **Overall Progress**: `█░░░░░░░░░░░░░░░░░░░ 6%`
*   **Next Milestone**: Week 1 - INSAT-3DR ingest (waiting on MOSDAC data)

---

## 📅 Week-by-Week Implementation Tracker

### Month 1 — Pipeline Setup, Data Engineering & Spatial Transformations
| Status | Week | Task Description | Target Deliverables / Verification | Notes |
| :---: | :---: | :--- | :--- | :--- |
| `[ ]` | **Week 1** | Data Acquisition & Standardized Ingestion | • Ingest script for INSAT-3DR Imager, CTH, GPM 2ADPR, SRTM DEM.<br>• Resample to 0.04° grid. | Package set up; 570 GPM overpasses listed (`00_Documentation/events/`). INSAT ingest waits on MOSDAC data. |
| `[~]` | **Week 2** | Viewing Geometry & Angle Calculation | • VZA, VAA, and SZA angle maps per INSAT scene.<br>• Verify VZA ranges across regions. | `satellite_view_angles` / `solar_angles` done, within 0.01° of pyorbital. Per-scene maps need the INSAT grid. |
| `[x]` | **Week 3** | Geocentric ECEF Transformation Engine | • Bidirectional coordinate converter module (`src/geometry/`).<br>• Unit tests matching `pyproj` (< 1m delta). | Done: `geometry/ecef.py`, matches pyproj to < 1 mm. |
| `[ ]` | **Week 4** | Cloud-Top Height Ingestion & Fallback Module | • CTH grid ingestion parser.<br>• Thermal profile lookup using ERA5 profiles when CTH is NaN. | |

### Month 2 — Ray-Tracing Engine, Terrain Integration & Resampling
| Status | Week | Task Description | Target Deliverables / Verification | Notes |
| :---: | :---: | :--- | :--- | :--- |
| `[ ]` | **Week 5** | Analytical Ellipsoid Ray-Tracing Solver | • Quadratic ellipsoid solver in `src/geometry/`.<br>• Numba/PyCUDA acceleration (< 2s per full disk frame). | |
| `[ ]` | **Week 6** | SRTM Topographic Relief Integration | • Integrate SRTM elevation into projection loop.<br>• Generate local parallax displacement maps (km). | |
| `[ ]` | **Week 7** | BucketResampler & Gridding Strategy | • `BucketResampler` module in `src/resample/`.<br>• Max-CTH occlusion logic and IDW spatial interpolation. | |
| `[ ]` | **Week 8** | Pipeline Automation & Batch Processing | • End-to-end orchestration pipeline runner script.<br>• Batch execution on 100 benchmark monsoon storm scenes. | |

### Month 3 — Multi-Sensor Validation & Quantitative Alignment Analysis
| Status | Week | Task Description | Target Deliverables / Verification | Notes |
| :---: | :---: | :--- | :--- | :--- |
| `[ ]` | **Week 9** | Spaceborne Radar (GPM DPR) Cross-Alignment | • Colocation module between INSAT TIR1 and GPM DPR orbit tracks.<br>• Compute spatial cross-correlation & mutual information. | |
| `[ ]` | **Week 10** | Ground Radar (IMD DWR) Validation | • Volume scan extractor for Mumbai, Goa, Kochi, Agartala.<br>• Compute Intersection-over-Union (IoU) with DWR cores. | |
| `[ ]` | **Week 11** | Regional Statistical Dissection | • Detailed statistics tables partitioned by regime.<br>• Validation of shift direction and distance trends. | |
| `[ ]` | **Week 12** | Sensitivity & Error Budget Analysis | • Monte Carlo simulation script perturbing CTH (+/- 1-2 km).<br>• Error propagation bounds. | |

### Month 4 — Downstream Model Evaluation, Manuscript & Code Release
| Status | Week | Task Description | Target Deliverables / Verification | Notes |
| :---: | :---: | :--- | :--- | :--- |
| `[ ]` | **Week 13** | Impact on Deep Learning Segmentation | • Train two comparative U-Net models (Model A vs. Model B).<br>• Evaluate boundary edge precision over test sets. | |
| `[ ]` | **Week 14** | Manuscript Structuring & Figure Generation | • Outline manuscript sections.<br>• Render 3D ray-tracing diagrams and displacement vector plots. | |
| `[ ]` | **Week 15** | Manuscript Writing & Peer Review | • Compile LaTeX source file.<br>• Mathematical proof verification and self-review. | |
| `[ ]` | **Week 16** | Code Packaging & Submission | • Python library packaging.<br>• Release code on GitHub and submit paper to journal. | |

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

Use this table to log current metrics achieved vs. the project's targets:

| Evaluation Metric | Baseline (Uncorrected) | Project Target (Corrected) | Current Value | Status |
| :--- | :---: | :---: | :---: | :---: |
| **GPM DPR Echo-Top Boundary IoU** | 0.42 – 0.48 | 0.68 – 0.75 | *TBD* | ⚪ Pending |
| **IMD DWR Core Cross-Correlation** | 0.51 | 0.82 | *TBD* | ⚪ Pending |
| **Mean Geolocation Shift Distance** | 0.0 km | 4.2 km (Ghats) / 8.6 km (Himalayas) | *TBD* | ⚪ Pending |
| **Downstream U-Net Edge Precision** | 0.45 | 0.62 | *TBD* | ⚪ Pending |
