# PyGeoParallax-IN

[![tests](https://github.com/bapallinaveen60/PyGeoParallax-IN/actions/workflows/tests.yml/badge.svg)](https://github.com/bapallinaveen60/PyGeoParallax-IN/actions/workflows/tests.yml)

PyGeoParallax-IN is a Python-based processing pipeline designed to correct **cloud parallax errors** in INSAT-3DR geostationary satellite observations over the Indian Subcontinent. By combining high-resolution Cloud-Top Height (CTH) datasets, ERA5 atmospheric reanalysis profiles, and the Shuttle Radar Topography Mission (SRTM) Digital Elevation Model (DEM), this toolkit performs precise ray-tracing and ellipsoid calculations to shift cloud-influenced observations back to their true geographical coordinates.

The corrected output is validated against ground-based Doppler Weather Radar (DWR) from the Indian Meteorological Department (IMD) and spaceborne Precipitation Radar (PR) overpasses from the Global Precipitation Measurement (GPM) mission.

---

## Folder Structure

The project is structured as follows:

```
PyGeoParallax-IN/
│
├── 00_Documentation/
│   ├── PROJECT_INDEX.md             # Guide to directory roles & workflow
│   ├── project_tracker.md           # 16-week project implementation tracker
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
│   └── validation/                  # Colocation and statistical computations
│
├── tests/                           # Unit tests (pytest)
├── scripts/                         # Standalone utilities (e.g. GPM overpass finder)
├── .github/workflows/               # CI: tests on every push
├── notebooks/                       # Exploratory Jupyter Notebooks
│
├── pyproject.toml                   # Package metadata and dependencies
├── LICENSE                          # MIT License
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
4. **Validation & Assessment**: Evaluate corrected outputs against IMD DWR and GPM radar overpasses using validation modules.

### Quick example

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

Validation helpers live in `pygeoparallax.validation`: `compare` (IoU, correlation, mutual information, residual offset), `points_to_grid`, `range_mask`, `nearest_time`, `regional_stats`, `monte_carlo_shift` and `bias_sweep`.

Each output has a `fill_flag` per cell: 0 = observed, 1 = interpolated from neighbours, 2 = empty (ground hidden behind a cloud). It also has `shift_km`, the parallax displacement.

---

## License

Released under the [MIT License](LICENSE).
