# Troubleshooting

Common problems, what causes them and how to fix them. Installation problems are in [installation.md](installation.md#common-install-problems). If your problem is not here, see [reporting a problem](#reporting-a-problem).

## No input files matched

```
no input files matched
```

`l1c`, `batch` and `navigation` print this and exit with code 1 when no file matches the inputs. The commands expand glob patterns themselves, with Python's `glob`, so the cause is usually the pattern or the folder.

Check:

- **The current folder.** Relative patterns are relative to where you run the command. Try the absolute path.
- **Quoting.** Put patterns in double quotes. This works the same in bash, zsh, PowerShell and cmd:

  ```bash
  pygeoparallax l1c "L1C/3RIMG_*_L1C_SGP_V01R00.h5" -o corrected
  ```

  | Shell | `"L1C/*.h5"` | `'L1C/*.h5'` | `L1C/*.h5` (unquoted) |
  | :--- | :--- | :--- | :--- |
  | bash, zsh (Linux, macOS, Git Bash) | works | works | works, but the shell expands it first; very many files can give `Argument list too long` |
  | PowerShell | works | works | works (PowerShell passes it unchanged) |
  | cmd | works | **fails**: the quotes become part of the pattern | works |

- **Recursive patterns.** `**` is not recursive here; it behaves like `*`. List each folder, for example `"2023/*/*.h5"`.
- **Square brackets in paths.** `[` and `]` are glob character classes, so a folder like `data[2023]` never matches. Rename it, or write `data[[]2023[]]`.
- **Case.** On Linux, `3rimg_*.h5` does not match `3RIMG_*.h5`.
- **File names.** L1C sector files are named `3RIMG_<DDMONYYYY>_<HHMM>_L1C_SGP_V01R00.h5`. Files from other products (`L1B`, `L2B_CTP`) do not match `*_L1C_SGP*`.

`correct` takes a single file name and does not expand patterns.

## Truncated or damaged L1C downloads

A partial download fails when it is opened:

```
FAIL  3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5: Unable to synchronously open file (truncated file: eof = 40000000, sblock->base_addr = 0, stored_eof = 81643736)
```

- `l1c` reports the file as `FAIL`, continues with the other files and exits with 1 at the end. `navigation` skips it with `skip  <name>: ...`.
- The message gives the size on disk (`eof`) and the expected size (`stored_eof`). A full L1C SGP file is about 80–90 MB.
- Download the file again from MOSDAC ([data.md](data.md)). Then rerun the same command: finished files are skipped, so only the failed one is processed.

Some scans are complete files but **partial scans**: part of the image is fill values. For example, many scans of 11–14 June 2023 have up to 57 % missing rows. The pipeline handles them: missing pixels stay NaN in the channels. Check the fraction of NaN in TIR1 if results look odd.

## cth is all NaN and nothing moved

If `cth` is NaN everywhere, the scene is treated as completely clear and no pixel moves. `shift_km` is then 0 everywhere, and the corrected and uncorrected outputs are identical.

Possible causes:

| Cause | Check | Fix |
| :--- | :--- | :--- |
| The region really is clear | `float(ds["TIR1"].min())` above 270 K | Nothing to correct. |
| `--cloud-threshold` too low | The default is 270 K; a threshold of, say, 200 K leaves almost nothing cloudy | Use the default, or a value suited to your clouds. |
| A standard scene with no heights | `to_standard_scene(ds)` without `cth=` writes an all-NaN `cth` | Pass `cth=` (from `cloud_top_height`, the L2 product or ERA5). |
| TIR1 all NaN | Wrong `--bbox` (outside the scanned area) or a partial scan | Check the box and the file. |
| Heights in km instead of m | `cth` maximum around 17 instead of 17000 | Convert to metres. This does not give NaN, but shifts of a few metres, which look like nothing moved. |

## Night-time VIS and SWIR

VIS (albedo) and SWIR (radiance) measure reflected sunlight. At night they contain only noise (for example VIS albedo of 3–8 % everywhere at 18:15 UTC). `l1c` corrects them like any other channel when you ask for them with `--channels`, but the values have no meaning. Use them only for daytime scans, and check the solar zenith angle (`pygeoparallax.geometry.solar_angles`) near dawn and dusk.

Cloud-top height always comes from TIR1, so the correction itself works the same by day and by night.

## Water vapour in clear sky is not corrected

The WV channel (6.9 µm) sees the upper troposphere, around 6–10 km, even where there is no cloud. That signal also has a parallax. PyGeoParallax-IN moves pixels only by their cloud-top height, and clear-sky pixels have none (`cth` is NaN), so clear-sky WV structures stay at their apparent positions. WV over cloud is corrected with the cloud top.

For most work this is acceptable: clear-sky WV features are broad, so a few kilometres of displacement matter little. If you need it, correct WV separately with a fixed emission height, for example in Python with `correct_scene(lat, lon, {"WV": wv}, np.full(wv.shape, 8000.0))` (8 km chosen as an illustration). See [concepts.md](concepts.md).

## Thin cirrus heights are too low

Cloud-top height comes from the TIR1 brightness temperature. Thin cirrus is partly transparent, so the satellite also sees warmer layers below it. Its brightness temperature is warmer than its real top, its height comes out too low, and it is moved too little.

- The effect is largest for thin, high cloud at the edges of storms and in anvils.
- Thick convective tops are not affected.
- Very cold tops (overshooting tops, colder than the tropopause) are capped at the tropopause height, 17 km in the AFGL tropical profile.
- ERA5 profiles (`--era5`) improve the temperature profile but not the transparency problem.

See [concepts.md](concepts.md) and [validation.md](validation.md) for the size of these errors.

## Memory and speed

Measured on a Windows laptop, `-j 1`, four channels:

| Input | Time | Peak memory |
| :--- | :--- | :--- |
| `--bbox` 10° × 12° (306 × 334 pixels) | about 7 s | small |
| full L1C sector (3207 × 3062 pixels), default grid | about 20 s | about 1.5 GB |

Tips:

- **Read only what you need.** `--bbox` decodes only that part of the file, and without `--grid` the output grid covers the same box. Make the box about 0.2° larger than your area of interest, because pixels near the edge can move out of the box.
- **Fewer channels.** `--channels TIR1` is faster and smaller than the default four channels.
- **Parallel files.** `-j N` runs N files at once. Memory grows with N: with 16 GB of RAM, use `-j 4` to `-j 6` for full sectors. The default (`-j` = number of CPUs) can run out of memory on machines with many cores.
- **Threads.** The Numba solver uses all cores within each worker. With many workers, `NUMBA_NUM_THREADS=1` avoids oversubscription:

  ```bash
  NUMBA_NUM_THREADS=1 pygeoparallax l1c "L1C/*.h5" -o corrected -j 8
  ```

  In PowerShell: `$env:NUMBA_NUM_THREADS = 1` before the command.
- **Disk space.** Outputs are float64 with compression. A full-sector file on the default grid with four channels is about 18 MB. A full-sector `--native` file holds ten times as many pixels and is about 315 MB. Use `--bbox` and fewer `--channels` to keep native files small.

## Slow first run: Numba compilation

The ray-tracing solver is compiled by Numba the first time it is used and cached in the package's `__pycache__` folder. The first run is therefore a few seconds slower (about 3 s on a laptop); later runs load the cache.

If every run is slow, the cache cannot be written, for example when the package is installed in a read-only location. Set a writable cache folder:

```bash
export NUMBA_CACHE_DIR=$HOME/.cache/numba     # Linux, macOS
```

In PowerShell: `$env:NUMBA_CACHE_DIR = "$HOME\.cache\numba"`.

Each worker process loads the cache on its own, so `-j N` runs pay a short start-up per worker.

## Navigation correction problems

### The land file is missing

```
FileNotFoundError: [Errno 2] No such file or directory: '01_raw_data/natural_earth/ne_10m_land.geojson'
```

(On Windows the path is shown with backslashes.) `pygeoparallax navigation` needs the Natural Earth 10 m land polygons. The default path is relative to the current folder and only exists inside a clone of the repository. Download the file (public domain, about 10 MB) from <https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson> and pass it:

```bash
pygeoparallax navigation "L1C/3RIMG_15DEC2022_*.h5" -o nav_15DEC2022.json --land ne_10m_land.geojson
```

The land file is only needed to *measure* a correction. Applying one with `--nav-correction nav.json` needs only the JSON file.

### No correction

```
no correction: no usable coastline matches (weak, inconsistent between scans, or cloudy)
```

Every window was rejected. Common reasons:

- **Night scans.** At night matching uses TIR1 and needs land colder than sea, which rarely holds in the monsoon. Use daytime scans (about 03:15–09:15 UTC over India).
- **Clouds** over the coasts. Use another day, or several scans of the same day.
- **One scan only.** A window from a single scan is only accepted with r ≥ 0.75. Two or more scans of one day make the result more reliable.

[concepts.md](concepts.md) and [validation.md](validation.md) explain how large and how variable the INSAT-3DR navigation error is.

## No figure from the demo

```
matplotlib not installed: no figure (pip install matplotlib)
```

The demo still runs, checks the correction and writes the NetCDF files; only `demo.png` is missing. Install matplotlib (`pip install matplotlib`, or the `plot` extra), or use `--no-plot` to skip the figure without the message.

## Other questions

**The corrected and uncorrected images look the same.** At full-scene scale, shifts of 3–10 km are a pixel or two. Zoom into a storm edge, plot `shift_km`, or difference the two files ([outputs.md](outputs.md#using-fill_flag-to-mask-cells)). Also check that `cth` is not all NaN (above).

**Output files from an earlier run were skipped although I changed options.** `l1c` and `batch` skip outputs by file name only. Use a new output folder, or `--overwrite`. See [cli.md](cli.md#output-file-names-and-skipping).

**The output covers 0–40° N, 60–100° E although I used `--bbox`.** This happened before version 0.4.2, when `--bbox` limited only the reading. Now a `--bbox` region without `--grid` goes on a 0.04° grid over the box. With `correct` and `batch` (no `--bbox`), pass `--grid`.

**Clouds moved towards the satellite.** That is correct. The satellite at 74° E sees clouds displaced away from it (to the north-east over Northeast India). Correction moves them back towards the sub-satellite point.

**Corrected precipitation features are now on the other side of the radar echo.** The infrared cloud top is several kilometres above the precipitating layer. For precipitation work use `--height-offset 3` (km) or `--height-scale 0.7`. See [validation.md](validation.md).

**An error appears in one worker but the message is short.** In parallel runs only the exception message is printed. Rerun that one file with `-j 1` and `--overwrite`, or in Python with `pygeoparallax.cli.process_l1c(path, out)`, to see the full traceback.

## Reporting a problem

Open an issue at <https://github.com/bapallinaveen60/PyGeoParallax-IN/issues>. Please include:

- the command or a short code snippet;
- the input file name (for example `3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5`), or a description of the data if you cannot share it;
- the full error message, with the traceback;
- the output of `pygeoparallax --version` and `python --version`, and your operating system.

INSAT-3DR products change format occasionally. If the reader fails on a new file, an issue with the file name and the error is very helpful. Issues are usually answered within a week. Contributions are welcome; see [development.md](development.md) and `CONTRIBUTING.md`.
