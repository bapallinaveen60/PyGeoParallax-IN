# Installation

PyGeoParallax-IN is a pure-Python package with a command-line tool, `pygeoparallax`. It installs with pip or conda. No compiler is needed: the fast ray-tracing kernel is compiled by Numba the first time it runs.

If you only want to see what the tool does, you can skip installation and use the [Colab notebook](https://colab.research.google.com/github/bapallinaveen60/PyGeoParallax-IN/blob/main/colab/try_pygeoparallax.ipynb) (see [quickstart.md](quickstart.md)).

## Requirements

- Python 3.10 or newer. The test suite runs on Python 3.10 and 3.12 (Ubuntu) and 3.12 (Windows); development uses 3.13.
- `git`, if you install directly from GitHub.
- Up to about 1.5 GB of free memory per full L1C sector processed at the same time; much less with a region (`--bbox`). See [troubleshooting.md](troubleshooting.md#memory-and-speed).

### Core dependencies

These are installed automatically. Minimum versions are from `pyproject.toml`.

| Package | Minimum | Used for |
| :--- | :--- | :--- |
| numpy | 1.22 | arrays |
| scipy | 1.8 | gap filling, interpolation of profiles and DEMs |
| pandas | 1.4 | tables in the validation helpers |
| xarray | 2022.03 | datasets and NetCDF input/output |
| netcdf4 | 1.5.8 | NetCDF backend for xarray |
| h5py | 3.6 | reading INSAT-3DR L1C HDF5 files |
| pyproj | 3.3 | L1C Mercator projection, geodesic shifts |
| numba | 0.56 | fast parallax solver (0.5 s per full disk) |
| shapely | 2.0 | coastline matching in `pygeoparallax navigation` |

### Optional extras

Extras add packages that only some features need. Install them with `pip install "<source>[extra1,extra2]"`.

| Extra | Packages | Needed for |
| :--- | :--- | :--- |
| `plot` | matplotlib >= 3.5 | the before/after figure of `pygeoparallax demo`, and plotting your output. Without it the demo still runs and passes, but writes no figure. |
| `geo` | rioxarray >= 0.11, rasterio >= 1.3, geopandas >= 0.10, cartopy >= 0.20 | reading SRTM GeoTIFF tiles with `read_srtm` (needs rasterio), and maps with coastlines in your own analysis. The correction itself does not need them. |
| `download` | cdsapi >= 0.5.1, requests >= 2.28 | downloading ERA5 profiles (`scripts/download_era5.py`) and other data. See [data.md](data.md). |
| `dev` | pytest >= 7.0, pyorbital >= 1.8, satpy >= 0.50, ipykernel >= 6.9, rasterio >= 1.3 | running the tests (pyorbital and satpy are independent references), the notebooks, and `read_srtm`. See [development.md](development.md). |

For most users, `plot` is the only extra worth adding at first.

## Install options

### From GitHub with pip

This is the simplest way for users.

```bash
pip install git+https://github.com/bapallinaveen60/PyGeoParallax-IN.git
```

With the plotting extra:

```bash
pip install "pygeoparallax-in[plot] @ git+https://github.com/bapallinaveen60/PyGeoParallax-IN.git"
```

Install into a virtual environment, not into the system Python:

```bash
python -m venv pgp-env
source pgp-env/bin/activate        # Linux and macOS
# pgp-env\Scripts\activate         # Windows (cmd or PowerShell)
pip install git+https://github.com/bapallinaveen60/PyGeoParallax-IN.git
```

### Editable install for development

Use this if you want to change the code or run the tests and scripts. Changes to the source take effect without reinstalling.

```bash
git clone https://github.com/bapallinaveen60/PyGeoParallax-IN.git
cd PyGeoParallax-IN
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[geo,download,plot,dev]"
pytest
```

Activate the environment before `pip install`. Otherwise pip installs into whichever Python is first on your `PATH`. See [development.md](development.md) for the rest of the developer setup.

### Conda environment

`environment.yml` in the repository root creates an environment called `pygeoparallax_in` with Python 3.10, all optional packages from conda-forge, and the package itself as an editable install. Run it from the repository root, because it installs `-e .`:

```bash
git clone https://github.com/bapallinaveen60/PyGeoParallax-IN.git
cd PyGeoParallax-IN
conda env create -f environment.yml
conda activate pygeoparallax_in
```

Conda is the easiest route on Windows if you want cartopy, geopandas or rasterio, which bring compiled GDAL and PROJ libraries.

## Checking the install

Print the version:

```bash
pygeoparallax --version
```

```
pygeoparallax 0.4.1
```

Run the self-test. It needs no data and takes about 10 s:

```bash
pygeoparallax demo
```

It prints a table of three synthetic storms and ends with `check: PASSED`. The exit code is 0 when the check passes and 1 when it fails. [quickstart.md](quickstart.md#run-the-demo) explains the output.

From Python:

```python
import pygeoparallax
print(pygeoparallax.__version__)        # 0.4.1

from pygeoparallax.demo import run_demo
result = run_demo("pygeoparallax_demo", plot=False)
print(result["passed"])                 # True
```

The first run takes a few seconds longer than later runs, because Numba compiles the solver and caches it (about 3 s on a laptop).

## Windows notes

- **Quoting file patterns.** In PowerShell and cmd, put glob patterns in double quotes: `"L1C\*.h5"`. In cmd, single quotes are not quotes: `'L1C\*.h5'` matches nothing. The tool expands the pattern itself, so it works the same on every shell. Details: [troubleshooting.md](troubleshooting.md#no-input-files-matched).
- **Activating a venv in PowerShell** may be blocked by the execution policy. Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or call the tools by full path, for example `.venv\Scripts\pygeoparallax.exe demo`.
- **Parallel processing** uses separate processes (the "spawn" start method). If you call `pygeoparallax.cli.process_l1c` from your own script inside a process pool, guard the script with `if __name__ == "__main__":`.
- **Paths with square brackets** (for example `D:\data[2023]\`) are read as glob character classes. Rename the folder, or escape the brackets as `[[]` and `[]]`.
- **cartopy, geopandas, rasterio:** if pip fails to build or install them, use the conda environment instead.
- The test suite runs on Windows in CI (Python 3.12), so the core package is supported there.

## Common install problems

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `ERROR: Package 'pygeoparallax-in' requires a different Python` | Python older than 3.10 | Use Python 3.10 or newer. |
| `pygeoparallax: command not found` / `'pygeoparallax' is not recognized` | The environment is not activated, or its `Scripts`/`bin` folder is not on `PATH` | Activate the environment, or run `python -m pygeoparallax.cli --help`. |
| `git` not found during `pip install git+https://...` | git is not installed | Install git, or download the repository as a ZIP and run `pip install <unzipped folder>`. |
| Numba fails to install | No wheel for your Python version yet (common right after a new Python release) | Use a Python version that Numba supports, or the conda environment. |
| `ImportError` for netCDF4 or h5py on import | Broken binary wheels or mixed conda and pip packages | Reinstall in a fresh environment; do not mix `conda install` and `pip install` for the same package. |
| `pip show pygeoparallax-in` reports an older version than `pygeoparallax --version` | An old editable install; the metadata is only refreshed on reinstall | Run `pip install -e .` again. |
| `matplotlib not installed: no figure` from the demo | The `plot` extra is missing | `pip install matplotlib`. |

More problems and their fixes: [troubleshooting.md](troubleshooting.md). Next step: [quickstart.md](quickstart.md).
