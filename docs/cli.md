# Command-line reference

The package installs one command, `pygeoparallax`, with five subcommands:

| Command | What it does | Input |
| :--- | :--- | :--- |
| [`demo`](#demo) | Self-test on a synthetic scene; writes a before/after figure | none |
| [`l1c`](#l1c) | Corrects INSAT-3DR L1C files directly | L1C HDF5 files |
| [`correct`](#correct) | Corrects one standard-scene file | one NetCDF file |
| [`batch`](#batch) | Corrects many standard-scene files in parallel | NetCDF files |
| [`navigation`](#navigation) | Measures a geolocation correction from coastlines | L1C HDF5 files |

Most users only need `l1c`. Use `correct` and `batch` when you already have pixel positions and cloud-top heights from another source (for example ISRO's L2 cloud product or your own retrieval), written in the [standard scene](#standard-scene-files) layout.

The option lists on this page are transcribed from `pygeoparallax <command> --help` for version 0.4.1. Python 3.13 prints short and long flags as `-o, --output-dir OUTPUT_DIR`; older Python versions print `-o OUTPUT_DIR, --output-dir OUTPUT_DIR`. The meaning is the same.

## Top level

```
usage: pygeoparallax [-h] [--version] {demo,l1c,correct,batch,navigation} ...

Cloud parallax correction for INSAT-3DR.
```

| Option | Description |
| :--- | :--- |
| `-h`, `--help` | Show the help message and exit. |
| `--version` | Show the version (`pygeoparallax 0.4.1`) and exit. |

`pygeoparallax <command> --help` shows the options of one command.

## Conventions

These apply to all commands.

- **Units.** Latitude and longitude in degrees (north and east positive). Heights in the files are metres; the `--height-offset` option is in kilometres. Shifts are in kilometres. Brightness temperatures are in kelvin.
- **Region arguments.** `--bbox` takes 4 numbers and `--grid` takes 5, in the order latitude minimum, latitude maximum, longitude minimum, longitude maximum (and resolution in degrees). Example: `--grid 20 30 85 97 0.04`.
- **Grid edges.** `--grid` bounds are the outer cell edges. `--grid 20 30 85 97 0.04` gives 250 × 300 cells with centres from 29.98° N down to 20.02° N and from 85.02° E to 96.98° E. Rows run north to south.
- **Default grid.** Without `--grid`, regular-grid output covers 0–40° N, 60–100° E at 0.04° (1000 × 1000 cells, about 4.4 km); with `l1c --bbox`, it covers the box at 0.04°.
- **Glob patterns.** Commands that take several inputs expand glob patterns themselves (Python `glob`), so quote the pattern: `"L1C/*.h5"`. In cmd on Windows use double quotes; single quotes are not quote characters there. `**` is not recursive. See [troubleshooting.md](troubleshooting.md#no-input-files-matched).

## demo

```
usage: pygeoparallax demo [-h] [-o OUTPUT_DIR] [--no-plot]
```

Self-test on a synthetic scene (no data needed); saves a before/after figure.

| Option | Default | Description |
| :--- | :--- | :--- |
| `-o`, `--output-dir OUTPUT_DIR` | `pygeoparallax_demo` | Where to write the demo files. Created if missing. |
| `--no-plot` | off | Skip the figure (no matplotlib needed). |

Three storms with flat tops at 16, 12 and 8 km are placed at known positions over Northeast India. The demo simulates what INSAT-3DR sees, derives cloud-top height from the brightness temperature, corrects the scene on its own pixel grid and checks that each storm is within one pixel (4 km) of its true position. It writes `demo_uncorrected.nc`, `demo_corrected.nc` and, unless `--no-plot` is given or matplotlib is missing, `demo.png`. [quickstart.md](quickstart.md#run-the-demo) explains the printed table and the figure.

Exit code: 0 if the check passes, 1 if it fails.

Examples:

```bash
# run the self-test in the current folder
pygeoparallax demo

# write elsewhere, without matplotlib
pygeoparallax demo -o /tmp/pgp_demo --no-plot
```

## l1c

```
usage: pygeoparallax l1c [-h] -o OUTPUT_DIR [-j WORKERS] [--overwrite]
                         [--channels CHANNELS [CHANNELS ...]]
                         [--bbox LAT_MIN LAT_MAX LON_MIN LON_MAX] [--native]
                         [--fill-empty] [--era5 ERA5]
                         [--cloud-threshold CLOUD_THRESHOLD] [--dem DEM]
                         [--dem-var DEM_VAR] [--no-correction]
                         [--grid LAT_MIN LAT_MAX LON_MIN LON_MAX RES]
                         [--fill-radius FILL_RADIUS]
                         [--nav-correction NAV_CORRECTION]
                         [--height-scale HEIGHT_SCALE] [--height-offset KM]
                         inputs [inputs ...]
```

Correct INSAT-3DR L1C files (HDF5) directly. For each file it:

1. reads the requested channels (only the `--bbox` region, if given) and the pixel positions;
2. applies the navigation correction, if `--nav-correction` is given;
3. derives cloud-top height from TIR1: brightness temperature below `--cloud-threshold` is cloud, and its height is looked up in the AFGL tropical atmosphere, or in the ERA5 profile with `--era5`;
4. turns it into an effective height, if `--height-scale` or `--height-offset` is given;
5. corrects for parallax (and terrain, with `--dem`) and resamples onto the regular grid, or onto the file's own pixel grid with `--native`;
6. writes one NetCDF file per input ([outputs.md](outputs.md)).

| Argument or option | Default | Description |
| :--- | :--- | :--- |
| `inputs` | required | `3RIMG_*_L1C_SGP*.h5` files or glob patterns. One or more. |
| `-o`, `--output-dir OUTPUT_DIR` | required | Folder for the output files. Created if missing. |
| `-j`, `--workers WORKERS` | 4, or the CPU count if lower | Parallel processes. A full L1C sector needs about 1.5 GB per process. |
| `--overwrite` | off | Redo files whose output already exists. |
| `--channels CHANNELS [CHANNELS ...]` | `TIR1 TIR2 WV MIR` | Channels to correct. Also `VIS`, `SWIR`. TIR1 is always read, for the cloud-top height, but is only written if listed. |
| `--bbox LAT_MIN LAT_MAX LON_MIN LON_MAX` | whole file | Read only this region of the file. The box is in the file's own (uncorrected) coordinates. |
| `--native` | off | Keep the file's own pixel grid instead of regridding to a regular lat/lon grid. |
| `--fill-empty` | off | With `--native`: fill cells no pixel reached with the nearest corrected value. |
| `--era5 ERA5` | AFGL tropical | ERA5 pressure-level NetCDF for cloud-top height. The profile nearest to the scan time is used. |
| `--cloud-threshold CLOUD_THRESHOLD` | `270.0` | TIR1 BT below this is cloud [K]. |
| `--dem DEM` | none | DEM NetCDF on a regular lat/lon grid, for terrain-aware correction. |
| `--dem-var DEM_VAR` | `elevation` | Elevation variable in the DEM file [m]. |
| `--no-correction` | off | Regrid without parallax correction (uncorrected baseline). |
| `--grid LAT_MIN LAT_MAX LON_MIN LON_MAX RES` | 0–40° N, 60–100° E, 0.04° | Target grid without `--native`. Ignored with `--native`. |
| `--fill-radius FILL_RADIUS` | `1` | Largest gap in cells to interpolate (0 = none). |
| `--nav-correction NAV_CORRECTION` | none | Navigation correction JSON from `pygeoparallax navigation`. |
| `--height-scale HEIGHT_SCALE` | `1.0` | Correct with height-scale × cloud-top height − height-offset. |
| `--height-offset KM` | `0.0` | Subtract this from the cloud-top height [km], e.g. 3 for precipitation. |

Notes:

- **Regular grid and `--bbox`.** Without `--grid`, a `--bbox` region is written on a 0.04° grid over that box only (for example `--bbox 20 30 85 97` gives 250 × 300 cells). Pass `--grid` for a different resolution or extent.
- **Edges of a box.** Pixels near the edge of a `--bbox` region can be moved out of it, and pixels outside it are not there to move in. Make the box about 0.2° larger than the area you need, or ignore cells with `fill_flag` 2 near the edges.
- **File size with `--native`.** A full L1C sector on its own grid (3207 × 3062 pixels, four channels) gives an output of about 315 MB, against about 18 MB on the default 0.04° grid. Use `--bbox` for native output when you can.
- **`--native` with `--nav-correction`.** The output keeps the file's original pixel grid; the navigation correction only changes where pixels land on it.
- **Effective height.** `--height-offset 3` corrects with the cloud-top height minus 3 km (never below 0 m); `--height-scale 0.7` with 70 % of it. Both together give `scale × cth − offset`. Use this for precipitation products: in this project's GPM validation, the infrared cloud top was a median 3.2 km above the radar storm top. The `cth` variable in the output then holds the effective height, and the attribute `effective_height` records the formula. See [concepts.md](concepts.md) and [validation.md](validation.md).
- **VIS and SWIR at night** contain no useful signal. They are corrected like any other channel, but the values are noise.

Examples:

```bash
# one file, a region, on a 0.04 deg grid over the same region
pygeoparallax l1c 3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5 -o corrected --bbox 20 30 85 97 --grid 20 30 85 97 0.04

# all files of a folder, on their own pixel grid, gaps filled, 4 processes
pygeoparallax l1c "L1C/3RIMG_*_L1C_SGP_V01R00.h5" -o corrected_native --native --fill-empty -j 4

# precipitation work: navigation correction and a height 3 km below the cloud top,
# plus the uncorrected baseline on the same grid
pygeoparallax l1c "L1C/*.h5" -o corrected_rain --nav-correction nav_15DEC2022.json --height-offset 3
pygeoparallax l1c "L1C/*.h5" -o uncorrected --no-correction
```

## correct

```
usage: pygeoparallax correct [-h] [--channels CHANNELS [CHANNELS ...]]
                             [--sat-lon SAT_LON] [--dem DEM]
                             [--dem-var DEM_VAR] [--no-correction]
                             [--grid LAT_MIN LAT_MAX LON_MIN LON_MAX RES]
                             [--fill-radius FILL_RADIUS]
                             [--nav-correction NAV_CORRECTION]
                             [--height-scale HEIGHT_SCALE]
                             [--height-offset KM]
                             input output
```

Correct one [standard-scene](#standard-scene-files) NetCDF file and write the result on a regular lat/lon grid.

| Argument or option | Default | Description |
| :--- | :--- | :--- |
| `input` | required | Standard-scene NetCDF file. |
| `output` | required | Output NetCDF file. Its folder is created if missing. An existing file is overwritten. |
| `--channels CHANNELS [CHANNELS ...]` | all 2-D variables | Channel variables to carry. By default, every data variable other than `lat`, `lon` and `cth` that has the same shape as `lat`. |
| `--sat-lon SAT_LON` | file attribute or INSAT-3DR 74.0 | Sub-satellite longitude [degrees east]. Read from the `sub_satellite_longitude` global attribute if present. |
| `--dem DEM` | none | DEM NetCDF on a regular lat/lon grid, for terrain-aware correction. |
| `--dem-var DEM_VAR` | `elevation` | Elevation variable in the DEM file [m]. |
| `--no-correction` | off | Regrid without parallax correction (uncorrected baseline). |
| `--grid LAT_MIN LAT_MAX LON_MIN LON_MAX RES` | 0–40° N, 60–100° E, 0.04° | Target grid. |
| `--fill-radius FILL_RADIUS` | `1` | Largest gap in cells to interpolate (0 = none). |
| `--nav-correction NAV_CORRECTION` | none | Navigation correction JSON from `pygeoparallax navigation`. |
| `--height-scale HEIGHT_SCALE` | `1.0` | Correct with height-scale × cloud-top height − height-offset. |
| `--height-offset KM` | `0.0` | Subtract this from the cloud-top height [km], e.g. 3 for precipitation. |

`correct` has no `--native` option; native-grid output is only available from `l1c` and from Python (`correct_native`). On success it prints `wrote <output>` and exits with 0. On an error (missing file, missing variable) it prints a one-line `error: <file>: <message>` and exits with 1.

Examples:

```bash
# correct one scene onto a regional 0.04 deg grid
pygeoparallax correct scenes/scene_20230801_1815.nc scene_corrected.nc --grid 20 30 85 97 0.04

# only TIR1, corrected with a height 3 km below the cloud top
pygeoparallax correct scenes/scene_20230801_1815.nc scene_eff.nc --grid 20 30 85 97 0.04 --channels TIR1 --height-offset 3

# terrain-aware correction with an SRTM DEM on a regular grid (variable "elevation", see data.md)
pygeoparallax correct scenes/scene_20230801_1815.nc scene_terrain.nc --grid 20 30 85 97 0.04 --dem srtm_0p01deg.nc
```

## batch

```
usage: pygeoparallax batch [-h] -o OUTPUT_DIR [-j WORKERS] [--overwrite]
                           [--channels CHANNELS [CHANNELS ...]]
                           [--sat-lon SAT_LON] [--dem DEM] [--dem-var DEM_VAR]
                           [--no-correction]
                           [--grid LAT_MIN LAT_MAX LON_MIN LON_MAX RES]
                           [--fill-radius FILL_RADIUS]
                           [--nav-correction NAV_CORRECTION]
                           [--height-scale HEIGHT_SCALE] [--height-offset KM]
                           inputs [inputs ...]
```

Correct many standard-scene files in parallel. Each file is processed exactly as by `correct`.

| Argument or option | Default | Description |
| :--- | :--- | :--- |
| `inputs` | required | Input files or glob patterns. One or more. |
| `-o`, `--output-dir OUTPUT_DIR` | required | Folder for the output files. Created if missing. |
| `-j`, `--workers WORKERS` | 4, or the CPU count if lower | Parallel processes. A full L1C sector needs about 1.5 GB per process. |
| `--overwrite` | off | Redo scenes whose output already exists. |
| `--channels`, `--sat-lon`, `--dem`, `--dem-var`, `--no-correction`, `--grid`, `--fill-radius`, `--nav-correction`, `--height-scale`, `--height-offset` | | As for [`correct`](#correct). |

Examples:

```bash
# all scenes of a folder, on a regional grid, 8 processes
pygeoparallax batch "scenes/*.nc" -o batch_corrected --grid 20 30 85 97 0.04 -j 8

# the uncorrected baseline on the same grid
pygeoparallax batch "scenes/*.nc" -o batch_uncorrected --grid 20 30 85 97 0.04 --no-correction

# several patterns at once, with a navigation correction
pygeoparallax batch "scenes/scene_202308*.nc" "scenes/scene_202309*.nc" -o batch_nav --grid 20 30 85 97 0.04 --nav-correction nav_15DEC2022.json
```

## navigation

```
usage: pygeoparallax navigation [-h] -o OUTPUT [--land LAND]
                                [--windows WINDOWS [WINDOWS ...]]
                                [--min-r MIN_R]
                                inputs [inputs ...]
```

Measure an INSAT L1C geolocation correction by coastline matching. INSAT-3DR L1C positions can be off by up to about 15 km, varying with season and region. This command compares the image with Natural Earth coastlines in 13 coastal windows around India and writes a smooth, position-dependent correction as JSON. Use it with `--nav-correction` in `l1c`, `correct` and `batch`.

| Argument or option | Default | Description |
| :--- | :--- | :--- |
| `inputs` | required | L1C files or glob patterns (e.g. all scans of one day). |
| `-o`, `--output OUTPUT` | required | Correction JSON to write. Its folder is created if missing. |
| `--land LAND` | `01_raw_data/natural_earth/ne_10m_land.geojson` | Land polygons GeoJSON (Natural Earth 10 m land). The default is relative to the current folder. |
| `--windows WINDOWS [WINDOWS ...]` | all | Coastal windows to use. Unknown names are ignored without a warning. |
| `--min-r MIN_R` | `0.6` | Reject matches weaker than this correlation. |

The windows are `kutch`, `saurashtra`, `konkan`, `goa_karnataka`, `kerala`, `sri_lanka`, `chennai`, `andhra`, `odisha`, `andaman`, `rakhine`, `chittagong` and `sundarbans`.

How it works, in short:

- Daytime windows (solar zenith angle below 75°) are matched in the VIS channel; night windows in TIR1, with land colder than sea. Night matching usually fails in the monsoon.
- Each window needs enough clear land and sea. Cloudy windows are skipped.
- For each scan and window the command prints one line: scan, window, channel, the east and north offsets [km], and the correlation before and after the shift (`r 0.71->0.75`). `(rejected)` marks matches that are weaker than `--min-r` or at the edge of the search range.
- The correction keeps windows with offsets of at most 25 km that agree within 5 km between two scans, or single scans with r ≥ 0.75. Some windows (for example `sundarbans`) only constrain the east–west offset; their north offset is `NaN`.
- Use several daytime scans of one day (for example 04:15, 06:15 and 08:15 UTC) for a stable result.

The Natural Earth 10 m land file is public domain. Download it from <https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson> and pass its path with `--land`, or save it at the default path.

Unreadable inputs (for example truncated downloads) are skipped with a message. If no match is accepted, it prints `no correction: ...` and exits with 1.

Examples:

```bash
# measure a correction from the daytime scans of one day
pygeoparallax navigation "datasets/insat_nav/3RIMG_15DEC2022_*_L1C_SGP_V01R00.h5" -o nav_15DEC2022.json

# only the east-coast windows, with the land file elsewhere
pygeoparallax navigation "L1C/3RIMG_15FEB2023_*.h5" -o nav.json --land ne_10m_land.geojson --windows chennai andhra odisha

# apply it
pygeoparallax l1c "L1C/3RIMG_15DEC2022_*.h5" -o corrected --nav-correction nav_15DEC2022.json
```

Example output (two scans of 15 December 2022, shortened):

```
3RIMG_15DEC2022_0615_SGP   odisha         VIS  E  -12.5  N   +1.5  r 0.81->0.88
3RIMG_15DEC2022_0615_SGP   chittagong     VIS  E  +32.0  N   +nan  r 0.33->0.43  (rejected)
3RIMG_15DEC2022_0815_SGP   odisha         VIS  E  -15.0  N   +3.0  r 0.76->0.84

windows used: chennai (-9.8 E, +2.8 N), goa_karnataka (+1.5 E, -2.0 N), kerala (-4.0 E, -3.5 N), odisha (-13.8 E, +2.2 N), rakhine (-10.2 E, +1.0 N), sri_lanka (-8.8 E, -0.2 N), sundarbans (-10.5 E, +nan N)
wrote nav_15DEC2022.json
```

Negative east values mean the L1C positions are too far east and are moved west.

## Standard scene files

`correct` and `batch` read *standard scene* NetCDF files. A standard scene is one satellite scan before correction, on its pixel grid:

| Content | Kind | Requirement |
| :--- | :--- | :--- |
| `lat` | 2-D data variable | Navigated (apparent) pixel latitude [degrees north]. |
| `lon` | 2-D data variable | Pixel longitude [degrees east]. Same shape as `lat`. |
| `cth` | 2-D data variable | Cloud-top height above the WGS84 ellipsoid [m]. NaN for clear sky. Same shape. |
| channels, e.g. `TIR1`, `WV` | 2-D data variables | Any number, same shape as `lat`. Carried through the correction. |
| `sub_satellite_longitude` | global attribute, optional | Satellite longitude [degrees east]. Default 74.0 (INSAT-3DR). |
| `time`, `start_time`, `satellite` | global attributes, optional | Copied to the output. |

The dimension names do not matter. `lat` and `lon` may be data variables (as written by `to_standard_scene`) or 2-D coordinates. A NaN `cth` everywhere is valid and means nothing moves (see [troubleshooting.md](troubleshooting.md#cth-is-all-nan-and-nothing-moved)).

Make one from an L1C file in Python:

```python
from pathlib import Path

from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.ingest import read_insat_l1c, to_standard_scene

ds = read_insat_l1c("3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", channels=("TIR1", "WV"), bbox=(20, 30, 85, 97))
scene = to_standard_scene(ds, cth=cloud_top_height(ds["TIR1"].values))
Path("scenes").mkdir(exist_ok=True)
scene.to_netcdf("scenes/scene_20230801_1815.nc")
```

This is the file used in the `correct` examples above.

Replace `cloud_top_height(...)` with heights from any other source on the same pixels. More in [python_api.md](python_api.md).

## Output file names and skipping

`l1c` and `batch` name each output after its input file:

| Mode | Output name |
| :--- | :--- |
| corrected (default) | `<input stem>_corrected.nc` |
| `--no-correction` | `<input stem>_uncorrected.nc` |

The stem is the file name without its last extension. `3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5` becomes `3RIMG_01AUG2023_1815_L1C_SGP_V01R00_corrected.nc`. `correct` writes to the name you give.

Before starting, `l1c` and `batch` check each output. If it already exists, they print `skip  <name> (exists)` and do not redo it. This makes interrupted runs cheap to resume. Notes:

- The check is by file name only. Output made earlier with different options (another `--grid`, `--native`, `--height-offset`) is still skipped. Use a new output folder per configuration, or pass `--overwrite`.
- A file left half-written by a crash is also skipped. Delete it, or use `--overwrite`.
- Two inputs with the same file name in different folders map to the same output name. Process them into separate output folders.
- Corrected and uncorrected outputs have different names, so they can share a folder.

## Parallel workers

`l1c` and `batch` process files in separate worker processes. `-j N` sets the number; the default is the number of logical CPUs. Each file runs in one worker.

- Memory: a full INSAT-3DR sector with the four default channels peaks at about 1.5 GB per worker (measured on 3RIMG_01AUG2023_1815, default grid). A `--bbox` region needs much less. With 16 GB of RAM, `-j 4` to `-j 6` is safe for full sectors. Reduce `-j` if the machine starts swapping.
- Workers start with the "spawn" method on every platform, which avoids crashes on Linux when Numba's thread pool is already running. Each worker re-imports the package, which takes a few seconds.
- The Numba solver is itself multithreaded. With many workers, set `NUMBA_NUM_THREADS=1` (or 2) to avoid oversubscribing the CPU.
- A file that fails does not stop the others. It is reported as `FAIL  <name>: <error>` on standard error.
- Lines appear as files finish (`done  <name>`), not in input order. The last line is `<done>/<attempted> scenes in <seconds> s`.

Timing on a laptop, `-j 1`: about 7 s for a 10° × 12° `--bbox` region and about 20 s for a full L1C sector (3207 × 3062 pixels), including process start-up.

## Exit codes

| Code | Meaning |
| :--- | :--- |
| 0 | Success. For `l1c` and `batch`: no file failed (also when every output was skipped). For `demo`: the check passed. |
| 1 | `l1c`, `batch`, `navigation`: `no input files matched`, or at least one file failed. `navigation`: no usable correction. `demo`: the check failed. `correct`: any error (one-line message). `navigation`: an unknown `--windows` name. |
| 2 | Invalid command line (unknown option, missing argument). argparse prints the usage. |

Use the exit code in scripts:

```bash
pygeoparallax l1c "L1C/*.h5" -o corrected -j 4 || echo "some scenes failed; see the FAIL lines"
```
