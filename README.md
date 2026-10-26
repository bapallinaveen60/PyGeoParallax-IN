# PyGeoParallax-IN

[![tests](https://github.com/bapallinaveen60/PyGeoParallax-IN/actions/workflows/tests.yml/badge.svg)](https://github.com/bapallinaveen60/PyGeoParallax-IN/actions/workflows/tests.yml)

PyGeoParallax-IN is a Python-based processing pipeline designed to correct **cloud parallax errors** in INSAT-3DR geostationary satellite observations over the Indian Subcontinent. It estimates cloud-top heights, traces each pixel's line of sight back to the cloud top on the WGS84 ellipsoid, and regrids the scene at the corrected positions. Optional terrain heights (DEM) and a coastline-based navigation correction are applied in the same pass.

The corrected output is validated against spaceborne radar overpasses from the Global Precipitation Measurement (GPM) mission. Validation against ground-based Doppler Weather Radar from the India Meteorological Department (IMD) is left for future work; the comparison code supports it.

## Status (v0.2.1)

| Part | State |
| :--- | :--- |
| INSAT-3DR L1C SGP reader, L2 CTP / clear-sky BT reader, GPM 2A Ku/DPR reader | done |
| Viewing and solar angles, ECEF transforms, ellipsoid ray-tracing solver (numpy and Numba; 0.5 s per full disk) | done |
| Cloud-top height from TIR1 BT (AFGL tropical profile or per-pixel ERA5 profiles) | done |
| Terrain-aware correction with SRTM | done |
| Occlusion-aware bucket resampling with gap filling | done |
| Coastline-based INSAT navigation correction | done |
| CLI (`correct`, `batch`, `navigation`) | done |
| Validation metrics (IoU, correlation, mutual information, sub-cell displacement) | done |

**Validation against GPM** (34 monsoon cases 2022–2024, 14 usable, 4 regions): the correction moves features by the computed amount along the line of sight and lowers the median INSAT–GPM storm-top offset from 5.4 to 3.0 km (10 of 12 cases improve). In monsoon INSAT-3DR data a navigation error of ~3–4 km partly masks the parallax, so correct navigation and parallax together. Details: [validation_summary.md](00_Documentation/validation_summary.md).

Speed: 1.8 s per India scene ([benchmark.md](00_Documentation/benchmark.md)). API overview: [api_reference.md](00_Documentation/api_reference.md). Changes: [CHANGELOG.md](CHANGELOG.md).

---

## Folder Structure

The project is structured as follows:

```
PyGeoParallax-IN/
│
├── 00_Documentation/
│   ├── PROJECT_INDEX.md             # Guide to directory roles & workflow
│   ├── project_tracker.md           # 16-week project implementation tracker
│   ├── api_reference.md             # Public functions and CLI
│   ├── validation_summary.md        # GPM validation results
│   ├── navigation_check.md          # INSAT-3DR geolocation check
│   ├── project_dashboard.html       # Interactive visual roadmap & metrics dashboard
│   ├── events/                      # GPM overpass candidates for validation
│   ├── related_papers/              # Core literature papers
│   │   ├── vicente_2002.pdf         # Vicente et al. (2002) foundational paper
│   │   ├── bielinski_2020.pdf       # Bieliński (2020) modern implementation
│   │   └── reading_tracker.md       # Literature review status tracker
│   └── data_access_notes.md         # Credentials and download instructions
│
├── 01_raw_data/                     # Raw satellite, reanalysis, and radar inputs
│   ├── insat3dr_l1c/                # INSAT-3DR Imager Level-1C HDF5 data
│   ├── insat3dr_cth/                # INSAT-3DR Cloud-Top Height grids
│   ├── era5_reanalysis/             # ERA5 vertical profiles
│   ├── gpm_dpr_2adpr/               # GPM 2A.DPR orbit overpasses
│   ├── imd_dwr/                     # IMD Radar grids (Mumbai, Goa, Kochi, Agartala)
│   └── srtm_dem/                    # SRTM South Asia DEM tiles
│
├── 02_standardized_grid/            # Data resampled onto a common grid (0.04° resolution)
│   ├── insat_0p04deg/
│   ├── era5_0p04deg/
│   └── srtm_0p04deg/
│
├── 03_intermediate/                 # Intermediate outputs of geometric solver
│   ├── viewing_angles/              # Satellite VZA, VAA, SZA maps
│   ├── cth_filled/                  # CTH with ERA5 fallback height values
│   └── ecef_coords/                 # Converted ECEF geocentric coordinates
│
├── 04_corrected_output/             # Final parallax-corrected products
│   ├── geotiff/
│   └── netcdf/
│
├── 05_validation/                   # Validation metrics and sensitivity runs
│   ├── gpm_colocation/              # GPM-DPR matched points stats
│   ├── imd_iou_results/             # Intersection over Union (IoU) with radars
│   ├── regional_stats/              # Partitioned statistics (Ghats, Himalayas, etc.)
│   └── monte_carlo_sensitivity/     # Uncertainty propagation runs
│
├── 06_deep_learning/                # Deep learning training experiments
│   ├── model_a_uncorrected/         # Models trained on uncorrected data
│   ├── model_b_corrected/           # Models trained on corrected data
│   └── eval_metrics/                # Model comparison charts
│
├── 07_figures/                      # Publication-ready plots
│
├── 08_manuscript/                   # LaTeX sources and submission versions
│   ├── latex_source/
│   └── submission_versions/
│
├── src/pygeoparallax/               # Installable Python package
│   ├── ingest/                      # Data parsers (HDF5, NetCDF, GRIB)
│   ├── geometry/                    # Ray-tracers, coordinate converters, solvers
│   ├── resample/                    # Regridding and interpolation algorithms
│   ├── validation/                  # Colocation, metrics and sensitivity analysis
│   ├── cloudheight.py               # Cloud-top height from BT / pressure
│   └── navigation.py                # Coastline-based geolocation correction
│
├── tests/                           # Unit tests (pytest)
├── scripts/                         # Standalone utilities (e.g. GPM overpass finder)
├── .github/workflows/               # CI: tests on every push
├── notebooks/                       # Exploratory Jupyter Notebooks
│
├── pyproject.toml                   # Package metadata and dependencies
├── LICENSE                          # MIT License
├── CHANGELOG.md                     # Release notes
├── environment.yml                  # Conda environment definition
└── README.md                        # Project readme (this file)
```

---

## Installation & Setup

1. **Prerequisites**: Install Anaconda or Miniconda.
2. **Environment Initialization**:
   Create the virtual environment using the provided `environment.yml` configuration:
   ```bash
   conda env create -f environment.yml
   conda activate pygeoparallax_in
   ```
   Without conda, a plain virtual environment works too:
   ```bash
   python -m venv .venv
   pip install -e ".[geo,download,plot,dev]"
   ```
   Run the tests with `pytest`.
3. **Register Credentials**:
   Follow instructions in [data_access_notes.md](00_Documentation/data_access_notes.md) to set up CDSAPI keys, NASA Earthdata logins, and MOSDAC logins.

---

## Basic Workflow

1. **Ingest Raw Data**: Standardize datasets to the 0.04-degree grid using the ingest scripts under `src/pygeoparallax/ingest/`.
2. **Compute Geometry & Fallbacks**: Calculate satellite viewing angles and perform ERA5 vertical interpolation for missing cloud heights under `src/pygeoparallax/geometry/`.
3. **Parallax Correction**: Run the ray-tracing ellipsoid solver to reposition pixels.
4. **Validation & Assessment**: Evaluate corrected outputs against GPM radar overpasses (and, in future, IMD ground radar) using the validation modules.

### Quick example: one INSAT-3DR L1C file

```python
from pygeoparallax import correct_scene
from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.ingest import read_insat_l1c
from pygeoparallax.resample import Grid

ds = read_insat_l1c("3RIMG_18AUG2024_2215_L1C_SGP_V01R00.h5", channels=("TIR1", "WV"),
                    bbox=(21, 29, 88, 97))
cth = cloud_top_height(ds["TIR1"].values)  # cloudy where BT < 270 K, NaN elsewhere
grid = Grid(21, 29, 88, 97, res=0.02)
channels = {"TIR1": ds["TIR1"].values, "WV": ds["WV"].values}
corrected = correct_scene(ds["lat"].values, ds["lon"].values, channels, cth, grid=grid)
uncorrected = correct_scene(ds["lat"].values, ds["lon"].values, channels, cth, grid=grid, correct=False)
```

### Lower-level example

```python
from pygeoparallax import correct_scene

# lat, lon: navigated pixel positions; tir1: brightness temperature [K];
# cth: cloud-top height above the ellipsoid [m], NaN for clear sky.
corrected = correct_scene(lat, lon, {"TIR1": tir1}, cth, surface_height=srtm_lookup)
uncorrected = correct_scene(lat, lon, {"TIR1": tir1}, cth, correct=False)  # same grid, no shift
corrected.to_netcdf("04_corrected_output/netcdf/scene.nc")
```

From the command line, using *standard scene* NetCDF files (2-D `lat`, `lon`, `cth` and channel variables, written by the ingest step):

```bash
pygeoparallax correct scene.nc scene_corrected.nc --dem srtm_0p04deg.nc
pygeoparallax batch "02_standardized_grid/insat_0p04deg/*.nc" -o 04_corrected_output/netcdf -j 8
pygeoparallax batch "02_standardized_grid/insat_0p04deg/*.nc" -o 04_corrected_output/uncorrected --no-correction
```

INSAT-3DR L1C geolocation can be off by up to ~15 km, varying by date and region (see `00_Documentation/navigation_check.md`). Measure a same-day correction from coastlines and apply it:

```bash
pygeoparallax navigation "datasets/3RIMG_15FEB2023_*_L1C_SGP_V01R00.h5" -o nav_15FEB2023.json
pygeoparallax correct scene.nc scene_corrected.nc --nav-correction nav_15FEB2023.json
```

This needs the Natural Earth 10 m land polygons at `01_raw_data/natural_earth/ne_10m_land.geojson` ([download](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson), public domain).

Validation helpers live in `pygeoparallax.validation`: `compare` (IoU, correlation, mutual information, residual offset), `points_to_grid`, `range_mask`, `nearest_time`, `regional_stats`, `monte_carlo_shift` and `bias_sweep`.

Each output has a `fill_flag` per cell: 0 = observed, 1 = interpolated from neighbours, 2 = empty (ground hidden behind a cloud). It also has `shift_km`, the parallax displacement.

---

## License

Released under the [MIT License](LICENSE).
