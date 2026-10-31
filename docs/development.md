# Development

This page is for people who work on PyGeoParallax-IN itself: the repository layout, the development setup, the tests, CI, code style, the release process and the manuscript builds. To contribute, also read [CONTRIBUTING.md](../CONTRIBUTING.md).

## Repository structure

### Package and tools

| Path | Content |
| :--- | :--- |
| `src/pygeoparallax/` | the package (version in `__init__.py`) |
| `src/pygeoparallax/geometry/` | WGS84 constants, ECEF conversion, viewing and solar angles, the parallax solver (`parallax.py`, with a Numba backend in `_parallax_numba.py`) |
| `src/pygeoparallax/ingest/` | readers: INSAT-3DR L1C (`insat.py`) and L2B CTP (`insat_ctp.py`), GPM 2A Ku (`gpm.py`), ERA5 (`era5.py`), SRTM (`srtm.py`) |
| `src/pygeoparallax/resample/` | output grids (`grid.py`), the occlusion-aware bucket resampler (`bucket.py`), native L1C grids (`native.py`), nearest-neighbour sampling (`nearest.py`) |
| `src/pygeoparallax/validation/` | colocation, alignment metrics, regional statistics, sensitivity |
| `src/pygeoparallax/cloudheight.py` | cloud-top height from BT or pressure (AFGL tropical profile, ERA5 profiles), effective height |
| `src/pygeoparallax/navigation.py` | coastline matching and `NavigationCorrection` |
| `src/pygeoparallax/terrain.py` | surface height from a DEM |
| `src/pygeoparallax/pipeline.py` | `correct_scene` and `correct_native` |
| `src/pygeoparallax/cli.py` | the `pygeoparallax` command (`demo`, `l1c`, `correct`, `batch`, `navigation`) |
| `src/pygeoparallax/demo.py` | the synthetic self-test |
| `tests/` | the pytest suite (synthetic data only) |
| `scripts/` | research scripts: GPM validation ([validation.md](validation.md)) and U-Net A/B ([unet.md](unet.md)) |
| `notebooks/quickstart.ipynb` | tutorial from one L1C file to corrected output |
| `colab/` | `try_pygeoparallax.ipynb` (try the tool in the browser) and `unet_ab_colab.ipynb` (U-Net training) |

The user-facing pages are [installation.md](installation.md), [quickstart.md](quickstart.md), [cli.md](cli.md), [python_api.md](python_api.md), [outputs.md](outputs.md), [concepts.md](concepts.md), [data.md](data.md) and [troubleshooting.md](troubleshooting.md).

### Research folders

| Path | Content |
| :--- | :--- |
| `00_Documentation/` | project notes: validation summary, navigation check, benchmark, case notes, `events/` (candidate lists and `case_scans.csv`) |
| `01_raw_data/` … `07_figures/` | data and results; see [validation.md](validation.md#folder-layout). Only `.gitkeep` files are tracked. |
| `08_manuscript/` | manuscript drafts (Markdown), build scripts and LaTeX sources |
| `paper/` | JOSS paper draft (`paper.md`, `paper.bib`) |
| `reports/`, `research_notes/` | literature and novelty notes |

### Not in git

`.gitignore` excludes:

- everything in `01_raw_data/` to `07_figures/` except `.gitkeep`;
- data formats anywhere: `*.nc`, `*.h5`, `*.hdf5`, `*.tif`, `*.zip` and others;
- `datasets/` (local sample downloads);
- `U_net_info/` (the group's U-Net package, 2.4 GB);
- LaTeX build outputs, the Copernicus class files in `08_manuscript/amt_source/` and the zip files in `08_manuscript/submission_versions/`.

## Development setup

Python 3.10 or newer is required (`requires-python = ">=3.10"`).

```bash
git clone https://github.com/bapallinaveen60/PyGeoParallax-IN.git
cd PyGeoParallax-IN
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[geo,download,plot,dev]"
```

The extras, from `pyproject.toml`:

| Extra | Packages | Needed for |
| :--- | :--- | :--- |
| (core) | numpy, scipy, pandas, xarray, netcdf4, h5py, pyproj, numba, shapely | the package |
| `geo` | rioxarray, geopandas, cartopy | GeoTIFF output, maps |
| `download` | cdsapi, requests | ERA5 download |
| `plot` | matplotlib | figures, `pygeoparallax demo` figure |
| `dev` | pytest, pyorbital, satpy, ipykernel, rasterio | tests (reference comparisons, SRTM tiles) |

`environment.yml` builds the same set as a conda environment (`pygeoparallax_in`, Python 3.10) and installs the package in editable mode.

Some scripts need packages outside the extras: `benchmark_scenes.py` needs `psutil`, and the U-Net training scripts need TensorFlow (see [unet.md](unet.md)).

Check the installation:

```bash
pygeoparallax --version
pygeoparallax demo
```

## Tests

```bash
pytest            # all tests; configured in pyproject.toml (testpaths = ["tests"])
pytest -q tests/test_parallax.py
pytest -k navigation
```

The suite has 68 tests. Without data, 67 run and 1 is skipped. They use synthetic data and need no downloads. A full run takes about 1 min on a laptop.

The skipped test, `tests/test_ingest.py::test_real_sample_files`, reads real files. Set `PYGEOPARALLAX_SAMPLE_DATA` to a folder with INSAT-3DR L1C (`3RIMG_*_L1C_SGP_*.h5`) or GPM (`2A.GPM.*.HDF5`) files to run it:

```bash
PYGEOPARALLAX_SAMPLE_DATA=datasets pytest tests/test_ingest.py
```

### What the tests cover

| File | Tests | Covers |
| :--- | ---: | :--- |
| `test_cli.py` | 4 | `correct` and `batch` commands; `--dem`, no-correction mode and navigation correction |
| `test_cloudheight.py` | 7 | height from temperature and pressure, cloud mask, nearest sampling, the CTP reader, ERA5 profiles (single profile and per-pixel profiles agree) |
| `test_demo.py` | 3 | the simulated scene is displaced away from the satellite; `run_demo` passes and writes files; the `demo` command |
| `test_geometry.py` | 8 | geodetic ↔ ECEF against pyproj, round trip, geostationary altitude, satellite zenith at the sub-satellite point, azimuth directions, satellite and solar angles against pyorbital, solar noon at the equinox |
| `test_ingest.py` | 8 | INSAT and GPM readers on synthetic HDF5 files, position offsets and callable corrections, the slanted GPM beam, SRTM mosaicking and averaging, a damaged SRTM tile; one test on real files (skipped by default) |
| `test_native.py` | 7 | Mercator round trip, native grid fit, against an L1C-style file, `correct_native` (identity without cloud, cloud moved by its parallax), effective height, the `l1c` command |
| `test_navigation.py` | 4 | coastline matching recovers a known offset, the correction field, the acceptance rules of `from_matches`, east-only windows |
| `test_package.py` | 2 | version string, sub-packages import |
| `test_parallax.py` | 9 | corrected point lies on the line of sight at cloud height, no shift at zero height or at the sub-satellite point, direction and flat-Earth magnitude, NaN handling, navigation on terrain, terrain clamping and clear-sky terrain shift, convergence on slopes, agreement with satpy within the spherical-Earth error, Numba and NumPy backends agree |
| `test_resample.py` | 7 | grid geometry, highest pixel wins a collision, IDW fill rules, large gaps stay empty, a synthetic cloud moves towards the satellite, terrain scene flags, clear pixels identical with and without correction |
| `test_validation.py` | 9 | IoU and Pearson, mutual information, best and sub-cell displacement recover known shifts, correction improves alignment with a synthetic radar, gridding and range mask, nearest time, regional statistics, sensitivity follows tan(VZA) |

The scripts in `scripts/` have no tests. `scripts/test_navigation_parallax.py` is a validation script, not a pytest test; pytest does not collect it because `testpaths` is `tests`.

## Continuous integration

`.github/workflows/tests.yml` runs on every push to `main` and on every pull request.

| OS | Python |
| :--- | :--- |
| ubuntu-latest | 3.10, 3.12 |
| windows-latest | 3.12 |

Each job:

1. checks out the code and sets up Python with pip caching;
2. installs the package with `pip install -e ".[dev]"`;
3. runs `pytest -q --junitxml=pytest-report.xml`;
4. on failure, turns each failed test in the JUnit report into a GitHub `::error` annotation (last 3,000 characters of the message).

`fail-fast` is off, so all three jobs finish even if one fails. A pull request must pass all three.

## Code style

There is no formatter or linter configuration in the repository. The code follows these conventions; please keep them.

- **Module docstrings** explain what the module or script does and why, with numbered steps for multi-step processing. Scripts end their docstring with a `Usage:` block.
- **NumPy-style docstrings** (`Parameters`, `Returns`) with units in brackets, for example `[K]`, `[m]`, `[km]`.
- **Units in names:** `_km`, `_m`, `_deg`, `_s`, for example `shift_km`, `max_distance_km`, `t_read_s`.
- **Comments** give units and reasons: `height: np.ndarray  # m above sea level`.
- `from __future__ import annotations` at the top of every module.
- **Scripts:** a `main(argv=None)` function with `argparse`, `description=__doc__.split("\n\n")[0]`, and `if __name__ == "__main__": main()`. Scripts that import other scripts insert `scripts/` into `sys.path` and mark the following imports with `# noqa: E402`.
- **Constants** in capitals at module level, often with a `#:` comment (for example `#: AFGL tropical standard atmosphere.`).
- **Small functions** that can be tested on their own.
- **Lines** up to about 120 characters.
- **Outputs** are written to a temporary name and then renamed, so an interrupted run leaves no broken file. Long batch scripts skip finished outputs so they can resume.

Changes to results (the solver, cloud-top height, resampling or navigation) need a test against an independent reference (pyproj, pyorbital, satpy) or a synthetic case with a known answer.

## Release process

Releases follow semantic versioning. This is the process used for 0.1.0 to 0.4.1:

1. **Bump the version** in `src/pygeoparallax/__init__.py` (`__version__ = "X.Y.Z"`). `pyproject.toml` reads it from there (`version = { attr = "pygeoparallax.__version__" }`).
2. **CHANGELOG.md:** rename the `## Unreleased` heading to `## X.Y.Z (YYYY-MM-DD)`. Each release has a one-line summary and `### Added` (and, where relevant, `### Findings`) sections.
3. **CITATION.cff:** set `version: X.Y.Z` and `date-released: YYYY-MM-DD`. The `doi` stays the concept DOI.
4. **README.md:** update the status heading (`## Status (vX.Y.Z)`).
5. **Commit** as `Release X.Y.Z`.
6. **Tag** with an annotated tag and push:

   ```bash
   git tag -a vX.Y.Z -m "PyGeoParallax-IN X.Y.Z"
   git push origin main vX.Y.Z
   ```

7. **GitHub release** titled `PyGeoParallax-IN X.Y.Z` on the tag, with the CHANGELOG entry as notes. For example:

   ```bash
   gh release create vX.Y.Z --title "PyGeoParallax-IN X.Y.Z" --notes-file <notes.md>
   ```

8. **Zenodo** archives the release automatically through its GitHub integration, using the metadata in `.zenodo.json`. Each release gets its own version DOI (for example 0.3.0: [10.5281/zenodo.23672246](https://doi.org/10.5281/zenodo.23672246)). The concept DOI, which always resolves to the latest version, is [10.5281/zenodo.23666957](https://doi.org/10.5281/zenodo.23666957). Cite the version DOI in the manuscript for a specific version.

## Building the manuscripts

The Markdown drafts in `08_manuscript/` are the source of the main sections. The article-class LaTeX in `latex_source/` is the master copy; the journal versions are generated from it.

```text
methods_draft.md, results_discussion_draft.md
        |  md_to_latex.py (pandoc)
        v
latex_source/sections/{data,method,validation,results,discussion}.tex   + hand-written sections
        |  make_amt.py                       |  make_ieee.py
        v                                    v
amt_source/ (Copernicus AMT)           ieee_source/ (IEEEtran)
```

### Article version (`latex_source/`)

`08_manuscript/md_to_latex.py` splits `methods_draft.md` (Sections 2–4) and `results_discussion_draft.md` (Sections 5–6) at their top-level headings and converts each with pandoc. It turns the draft citations `[Author, year]` into natbib `\citep` and `\citet` commands, and drops the drafting notes and the Markdown reference list. It writes `data.tex`, `method.tex`, `validation.tex`, `results.tex` and `discussion.tex` to `latex_source/sections/`. It needs `pandoc` on the path.

The abstract, introduction, conclusions and figure sections (`abstract.tex`, `introduction.tex`, `conclusions.tex`, `figure_schematic.tex`, `figures.tex`) are edited in LaTeX directly. The bibliography is `latex_source/references.bib`, and `main.tex` uses the `article` class with `plainnat`. Figures are PDFs in `latex_source/figures/`; copy them from `07_figures/paper/` after running `scripts/make_paper_figures.py`.

```bash
python 08_manuscript/md_to_latex.py
cd 08_manuscript/latex_source && latexmk -pdf main.tex
```

A new citation in a draft must also be added to the `CITATIONS` table in `md_to_latex.py` and to `references.bib`.

### Copernicus AMT version (`amt_source/`)

`08_manuscript/make_amt.py` converts the sections in `latex_source/` to the Copernicus template (`copernicus.cls`, `amt` journal, `manuscript` option with line numbers). It uses the template's `\introduction` and `\conclusions` headings, turns pandoc's `longtable` tables into `table*` floats with the template's rules, floats figures at the top of the page, writes the Copernicus back matter and uses `copernicus.bst`. It copies the figures and `references.bib` and writes `amt_source/manuscript.tex`.

The Copernicus class files are not in the repository. Download the [Copernicus LaTeX package](https://publications.copernicus.org/Copernicus_LaTeX_Package.zip) and pass the unpacked folder once with `--template`; the files are then copied into `amt_source/`.

```bash
python 08_manuscript/md_to_latex.py
python 08_manuscript/make_amt.py --template <copernicus package folder>   # --template only the first time
cd 08_manuscript/amt_source && latexmk -pdf manuscript.tex
```

Edit `latex_source/` (or the Markdown drafts), never `amt_source/`; the generated files say so in their header.

### IEEE version (`ieee_source/`)

The IEEE two-column version is being added as `08_manuscript/make_ieee.py`, which writes `ieee_source/` in `IEEEtran` journal layout from the same `latex_source/` sections. The script in progress has no options; IEEEtran ships with TeX Live and MiKTeX.

```bash
python 08_manuscript/md_to_latex.py
python 08_manuscript/make_ieee.py
cd 08_manuscript/ieee_source && latexmk -pdf manuscript.tex
```

Packaged submission versions are kept as zip files in `08_manuscript/submission_versions/` (not in git).

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to report a problem, the contribution steps and the code of conduct. In short:

1. Fork the repository and branch from `main`.
2. Set up the environment as above.
3. Make the change in the style of the surrounding code.
4. Add or update tests in `tests/` and run `pytest`.
5. Describe the change in `CHANGELOG.md` under `## Unreleased`.
6. Open a pull request against `main`; CI must pass.

Issues: <https://github.com/bapallinaveen60/PyGeoParallax-IN/issues>. If a reader fails on a new INSAT-3DR file, report the file name and the full error.
