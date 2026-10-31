# GPM validation

This page explains how to reproduce the validation of PyGeoParallax-IN against the GPM Ku-band radar. It covers the folder layout, every validation script in `scripts/`, the order to run them, the two offset measures, the correction states, the statistics and the results.

The results are summarised from `00_Documentation/validation_summary.md` and `08_manuscript/results_discussion_draft.md` (Sections 5–6). For the correction method itself, see [concepts.md](concepts.md). For the input data and where to download it, see [data.md](data.md).

## Before you start

- Install the package with the extras the scripts need (see [installation.md](installation.md)):

  ```bash
  pip install -e ".[geo,download,plot,dev]"
  ```

  `download_era5.py` needs `cdsapi` and a Copernicus CDS account. `benchmark_scenes.py` needs `psutil`, which is not in any extra.
- **Run every script from the repository root.** The scripts read and write relative paths such as `05_validation/gpm_colocation/` and `00_Documentation/events/case_scans.csv`.
- The data folders `01_raw_data/` to `07_figures/` are not in git. Only their `.gitkeep` files are. To reproduce the results you must download the data again.
- The case data live in a separate **validation folder**, passed to most scripts as `--base`. In the project this was `D:/Projects/@GeoVision/Insat_data/datasets/validation`.

## Folder layout

### Repository folders

| Folder | What the validation keeps there |
| :--- | :--- |
| `00_Documentation/events/` | Candidate lists (`validation_candidates*.csv`, `validation_gpm_batch*.csv`), screening results (`*_screened.csv`), the pinned case scans (`case_scans.csv`) and the benchmark scene lists. |
| `01_raw_data/natural_earth/` | `ne_10m_land.geojson`, the Natural Earth 10 m land polygons. All coastline-navigation scripts read it (`--land`). |
| `01_raw_data/srtm_dem/`, `gpm_dpr_2adpr/`, `insat3dr_l1c/`, `insat3dr_cth/`, `era5_reanalysis/` | Raw downloads. The case scripts read their inputs from the validation folder instead. |
| `01_raw_data/imd_dwr/` | IMD Doppler Weather Radar data. Not used in the GPM validation. |
| `02_standardized_grid/` | `srtm_0p01deg.nc`, the SRTM grid from `prepare_srtm.py`. |
| `03_intermediate/` | Not written by the validation scripts. |
| `04_corrected_output/netcdf/` | Gridded INSAT fields per case run: `<case>_<tag>_corrected.nc` and `<case>_<tag>_uncorrected.nc`. |
| `04_corrected_output/paired/` | The paired Model A / Model B dataset from `build_paired_dataset.py`. |
| `05_validation/gpm_colocation/` | One JSON per case run, `all_cases.csv`, `nav_parallax_test.csv`, `core_offsets*.csv`, `era5_comparison.csv`, `dem_comparison.csv`. |
| `05_validation/nav_corrections/` | Navigation corrections (JSON) and the match tables. |
| `05_validation/statistics/` | `statistics_<nav-tag>.json` and `field_offsets_by_case_<nav-tag>.csv` (the project has `_ynav` and `_gnav`). |
| `05_validation/benchmark/` | `benchmark_scenes.csv`. |
| `05_validation/navigation_check*.json` | Coastline checks from `check_navigation.py`. |
| `06_deep_learning/` | Empty placeholders. The U-Net runs are described in [unet.md](unet.md). |
| `07_figures/` | One PNG per case run (`<case>_<tag>.png`), `checks/` (overlays) and `paper/` (manuscript figures). |

### The validation folder

Each case is one sub-folder named `<region>_<YYYYMMDD>`, for example `northeast_20240818`. The region is one of `northeast`, `himalaya`, `central` or `south`. Folders with other names (for example `gpm_screen`) are ignored. A case folder holds:

- one GPM 2A Ku orbit file (`2A.GPM.*`);
- the INSAT-3DR case scan: `3RIMG_<DDMMMYYYY>_<HHMM>_L1C_SGP_V01R00.h5`, and the matching `..._L2B_CTP_V01R00.h5` if it exists;
- daytime L1C scans for navigation: 03:15–08:15 UTC on the case day, and on the days before and after;
- optionally `era5_pl_<YYYYMMDDHH>.nc` from `download_era5.py`.

Example (`northeast_20240818`):

```text
2A.GPM.Ku.V10-20251112.20240818-S215337-E232650.059478.V08A.nc
3RIMG_17AUG2024_0515_L1C_SGP_V01R00.h5
3RIMG_18AUG2024_0315_L1C_SGP_V01R00.h5
...
3RIMG_18AUG2024_2215_L1C_SGP_V01R00.h5      <- case scan
3RIMG_18AUG2024_2215_L2B_CTP_V01R00.h5
3RIMG_19AUG2024_0515_L1C_SGP_V01R00.h5
era5_pl_2024081822.nc
```

**Case scans are pinned** in `00_Documentation/events/case_scans.csv` (columns `case`, `insat_scan`). The folders also hold navigation scans from other times and days, so a rule on file names alone can pick the wrong scan. `run_all_cases.case_scan()` uses the pinned scan first. If a case is not listed, it takes the stamp of a CTP file on the case date, and then an L1C on the case date that is not in a navigation slot (`_0315`, `_0415`, `_0515`, `_0615`, `_0815`).

### Region boxes

Two sets of boxes are used. The search boxes find GPM crossings. The analysis boxes are wider and set the grid of each case run.

| Region | Search box, `find_validation_cases.py` [lat, lon] | Analysis box, `run_all_cases.py` [lat, lon] | VZA at the storms |
| :--- | :--- | :--- | :--- |
| `south` | 8–17° N, 74–80.5° E | 7–18° N, 73–82° E | 9–21° |
| `central` | 19–26° N, 76–85° E | 18–27° N, 75–86° E | 22–33° |
| `himalaya` | 27–33° N, 75–89° E | 24–33° N, 74–90° E | 29–37° |
| `northeast` | 22–29° N, 89–97° E | 21–29° N, 88–97° E | 31–38° |

The VZA ranges are those of the usable cases (manuscript Table 1).

## Order of the steps

| Step | Script | Main output |
| :--- | :--- | :--- |
| 1. Find candidates | `find_validation_cases.py` (and `find_gpm_overpasses.py` for radar sites) | candidate CSV |
| 2. Screen GPM for convection | `screen_gpm_convection.py` | screened CSV |
| 3. Download INSAT and build case folders | by hand; pin scans in `case_scans.csv` | validation folder |
| 4. Ancillary data (optional) | `download_era5.py`, `prepare_srtm.py` | `era5_pl_*.nc`, `srtm_0p01deg.nc` |
| 5. Run all cases | `run_all_cases.py` (calls `run_validation_case.py`) | case JSON, `all_cases.csv` |
| 6. Monsoon-median navigation runs | `test_navigation_parallax.py` | `<case>_mnav` runs, `nav_parallax_test.csv` |
| 7. Per-year navigation | `yearly_navigation.py` | `pooled_<year>.json` |
| 8. Navigation-state runs | `run_navigation_states.py` | `<case>_ynav`, `<case>_mnav` runs |
| 9. Cell offsets | `analyze_core_offsets.py` (`--nav-tag mnav`, then `ynav`) | `core_offsets*.csv` |
| 10. GPM-derived navigation | `gpm_navigation.py`, then `run_navigation_states.py --tags gnav`, then `analyze_core_offsets.py --nav-tag gnav` | `gpm_loo_<case>.json`, `<case>_gnav` runs |
| 11. Statistics | `validation_statistics.py` | `statistics_<nav-tag>.json` |
| 12. Sensitivity | `compare_variants.py` (`era5`, `dem`), `analyze_core_offsets.py --suffix` | `*_comparison.csv` |
| 13. Diagnostics | `check_parallax_visibility.py`, `near_storm_navigation.py`, `check_navigation.py` | overlays, match tables |
| 14. Figures | `make_paper_figures.py` | `07_figures/paper/` |

Separate from the GPM cases: `run_kochi_case.py` (the first case study), `design_benchmark_set.py` and `benchmark_scenes.py` (the benchmark), and `build_paired_dataset.py` (the paired dataset).

A complete run, with `<base>` the validation folder:

```bash
# 1-2: candidates and screening
python scripts/find_validation_cases.py --years 2022 2023 2024 --out 00_Documentation/events/validation_candidates.csv
python scripts/screen_gpm_convection.py --dir <folder with GPM files> --cases 00_Documentation/events/validation_gpm_batch2.csv

# 4: ancillary data
python scripts/download_era5.py --base <base>
python scripts/prepare_srtm.py --tiles <SRTM tile folder> --out 02_standardized_grid/srtm_0p01deg.nc

# 5-10: case runs, navigation states and cell offsets
python scripts/run_all_cases.py --base <base>
python scripts/test_navigation_parallax.py --base <base>
python scripts/yearly_navigation.py --base <base>
python scripts/run_navigation_states.py --base <base>
python scripts/analyze_core_offsets.py --base <base>
python scripts/analyze_core_offsets.py --base <base> --nav-tag ynav
python scripts/gpm_navigation.py
python scripts/run_navigation_states.py --base <base> --tags gnav
python scripts/analyze_core_offsets.py --base <base> --nav-tag gnav

# 11-14: statistics, sensitivity, diagnostics, figures
python scripts/validation_statistics.py --nav-tag ynav
python scripts/compare_variants.py --base <base> --variant era5
python scripts/compare_variants.py --base <base> --variant dem --dem 02_standardized_grid/srtm_0p01deg.nc
python scripts/analyze_core_offsets.py --base <base> --suffix _era5
python scripts/analyze_core_offsets.py --base <base> --suffix _dem
python scripts/check_parallax_visibility.py --base <base> --cases northeast_20230613
python scripts/make_paper_figures.py
```

`gpm_navigation.py` and `make_paper_figures.py` take no options. Running them with `--help` runs them in full.

## The scripts

All options below are quoted from each script's `argparse`. Defaults are in brackets.

### Finding and screening cases

#### `find_gpm_overpasses.py`

Finds GPM 2A.DPR orbits whose swath passes within `--radius-km` of an IMD radar site (Mumbai, Goa, Kochi, Agartala) in June–September. It queries NASA's CMR catalogue, which needs no Earthdata login. The overpass time is interpolated along the swath centre line and is accurate to about 1 min. This list was made for the planned IMD radar validation; the GPM validation uses `find_validation_cases.py`.

| Option | Meaning |
| :--- | :--- |
| `--years` | years to search [2022 2023 2024] |
| `--sites` | radar sites [all four] |
| `--radius-km` | search radius around each radar [150.0 km] |
| `--version` | 2A.DPR product version [08] |
| `--out` | output CSV [`gpm_overpasses.csv`] |

Output columns: `site`, `site_lat`, `site_lon`, `overpass_utc`, `nadir_dist_km`, `site_in_swath` (within 122.5 km of nadir), `orbit`, `granule`, `url`. The project's list is `00_Documentation/events/gpm_overpasses_jjas_2022_2024.csv`.

#### `find_validation_cases.py`

Finds GPM Ku passes over the four high-VZA regions with an INSAT-3DR scan close in time. It only searches 1 June – 20 September, the summer navigation state. For each orbit whose centre line crosses a region box, it takes the time at the middle of the crossing. It then estimates when the INSAT full-disk scan reaches that latitude: scans start at HH:15 and HH:45 and sweep from 81° N to 81° S in 26.9 min. Crossings within `--max-dt` of an INSAT scan are kept.

| Option | Meaning |
| :--- | :--- |
| `--years` | [2022 2023 2024] |
| `--regions` | [all four] |
| `--max-dt` | largest \|GPM − INSAT\| time at the crossing [5.0 min] |
| `--product` | CMR short name [`GPM_2AKu`] |
| `--version` | [08] |
| `--out` | [`00_Documentation/events/validation_candidates.csv`] |

Output columns include `region`, `gpm_time_utc`, `dt_min_gpm_minus_insat`, the INSAT file names `insat_l1c` and `insat_ctp`, `crossing_lat`, `crossing_lon`, `vza_deg`, `track_km_in_region`, `orbit`, `granule` and `url`. Rows are sorted by \|dt\|. Whether a case has convection is known only after the GPM file is downloaded.

#### `screen_gpm_convection.py`

Checks downloaded GPM 2A Ku files for convection before INSAT data are ordered. For each candidate it counts the convective footprints (`precip_type == 2`) in the region box and the size of the densest convective cluster. The cluster is centred on the densest 1° bin and includes footprints within 1.35° (about 150 km), the same rule as `run_validation_case.py`. A case is marked `download INSAT` if its cluster has at least 100 convective footprints.

| Option | Meaning |
| :--- | :--- |
| `--dir` | folder with the GPM files, searched recursively (required) |
| `--cases` | candidate CSV with `region`, `gpm_time_utc`, `insat_l1c`, `granule` [`00_Documentation/events/validation_gpm_batch2.csv`] |
| `--out` | [`00_Documentation/events/validation_gpm_batch2_screened.csv`] |

Output columns: `convective`, `raining_pct`, `storm_top_max_km`, `cluster`, `cluster_lat`, `cluster_lon`, `verdict`.

#### `design_benchmark_set.py`

Chooses a stratified set of INSAT-3DR scenes for the benchmark and the U-Net test set. It draws 2 days per month, June–September of 2022, 2023 and 2024 (24 days), from days 3–28 (3–18 in September, before the navigation state changes around 20 September). Days within 2 days of a validation case and the partial-scan days 11–14 June 2023 are excluded. Each day gets 4 scans: 00:15, 06:15, 12:15 and 18:15 UTC.

| Option | Meaning |
| :--- | :--- |
| `--out` | [`00_Documentation/events/benchmark_scenes.csv`] |
| `--seed` | random seed [2026] |

It reads `00_Documentation/events/case_scans.csv` to exclude the case days. Output columns: `date`, `utc`, `l1c_file`, `ctp_file`.

### Ancillary data

#### `download_era5.py`

Downloads ERA5 pressure-level temperature and geopotential for each case folder. It requests the whole hour nearest the case scan, taking the scan start plus 10 min as the time INSAT reaches central India. The area is the case's analysis box padded by 1°. There are 29 levels from 1000 to 50 hPa. Folders that already have the file are skipped. Needs `cdsapi` and `~/.cdsapirc`.

| Option | Meaning |
| :--- | :--- |
| `--base` | validation folder (required) |
| `--only` | only these case folders |
| `--dry-run` | list the requests without downloading |

Output: `<case folder>/era5_pl_<YYYYMMDDHH>.nc`.

#### `prepare_srtm.py`

Reads SRTM GeoTIFF tiles, block-averages them and writes one NetCDF grid. `pygeoparallax correct --dem` and `run_validation_case.py --dem` read it.

| Option | Meaning |
| :--- | :--- |
| `--tiles` | folder, glob or files of SRTM GeoTIFF tiles (required) |
| `--out` | [`02_standardized_grid/srtm_0p01deg.nc`] |
| `--res` | grid spacing [0.01°] |
| `--bbox LAT_MIN LAT_MAX LON_MIN LON_MAX` | [6 38 68 98] |

### Running the cases

#### `run_validation_case.py`

Runs one case: INSAT-3DR against GPM 2A Ku, before and after parallax correction.

1. Reads the INSAT case scan (TIR1 and WV) over the box padded by 1°. With `--nav`, it applies a navigation correction from a JSON file.
2. Computes cloud-top height from TIR1: AFGL tropical profile, or ERA5 with `--profile era5`. The cloud mask uses ISRO's clear-sky BT from the CTP file. Without a CTP file the cloud mask is BT < 270 K and the check against ISRO's CTP height is skipped.
3. Parallax-corrects and regrids to `--res`, and also regrids an uncorrected copy on the same grid. With `--dem` the correction is terrain-aware.
4. Places the GPM footprints on the grid: nearest footprint within 3.5 km. Storm tops are placed on the slanted Ku beam, not at the surface footprint.
5. Computes the metrics (below) and the INSAT scan time at the convection's latitude.

| Option | Meaning |
| :--- | :--- |
| `--dir` | folder with the case's INSAT and GPM files (required) |
| `--case` | case name, used in output names (required) |
| `--scan` | INSAT scan stamp, e.g. `18AUG2024_2215` (required) |
| `--bbox LAT_MIN LAT_MAX LON_MIN LON_MAX` | grid box (required) |
| `--res` | grid spacing [0.02°] |
| `--nav` | navigation correction JSON; the case is also run without it |
| `--nav-only` | with `--nav`, skip the run without navigation |
| `--profile` | `afgl` or `era5` [`afgl`] |
| `--dem` | DEM NetCDF for terrain-aware correction |
| `--max-lag` | lag search for the whole-box metrics [8 grid cells] |
| `--out` | output root [`.`] |

Outputs, under `--out`:

- `05_validation/gpm_colocation/<case>.json`: the summary. `runs` has one entry per navigation state (`no_nav`, `nav`). Each holds the time difference, the height check against ISRO CTP, the median shift of deep cores (BT < 220 K), the whole-box metrics (`uncorrected`, `corrected`) and the near-storm metrics (`near_150km`, `near_250km`).
- `04_corrected_output/netcdf/<case>_<tag>_corrected.nc` and `..._uncorrected.nc`, with `<tag>` = `no_nav` or `nav`.
- `07_figures/<case>_<tag>.png`: uncorrected and corrected TIR1 with GPM convection, and the parallax displacement.

Example:

```bash
python scripts/run_validation_case.py --dir <base>/northeast_20240818 --case northeast_20240818 \
    --scan 18AUG2024_2215 --bbox 21 29 88 97 --nav 05_validation/nav_corrections/18AUG2024.json
```

#### `run_all_cases.py`

Runs every case folder under `--base` and builds the case table.

1. Finds the case scan (see [the validation folder](#the-validation-folder)).
2. Measures a same-day navigation correction from the 04:15 and 06:15 UTC L1C scans, if a coastal window passes the acceptance rules. It is written to `05_validation/nav_corrections/<DDMMMYYYY>.json`.
3. Calls `run_validation_case.py` with the analysis box, with and without that correction.
4. Writes `05_validation/gpm_colocation/all_cases.csv`.

| Option | Meaning |
| :--- | :--- |
| `--base` | validation folder (required) |
| `--land` | [`01_raw_data/natural_earth/ne_10m_land.geojson`] |
| `--only` | run only these case folders |
| `--tabulate-only` | rebuild the CSV from the existing case JSON |

`all_cases.csv` has one row per case and navigation state. It holds the cluster size, the storm top, VZA, the time difference, the deep-core shift, and the along- and cross-look offsets before and after correction for both windows and both fields. The `status` column decides which cases are used later:

- `excluded: no GPM convection in region`;
- `excluded: <n> convective footprints (< 100)`;
- `excluded: no reliable match in any field or window`;
- `usable: <fields>`, listing the fields and windows whose matches lie inside the search (`z150`, `z250`, `top150`, `top250`);
- `skipped: no case scan`.

All later scripts take the usable cases from the `no_nav` rows of this file.

#### `run_kochi_case.py`

The first case study: deep convection over Kochi on 6 June 2022, GPM orbit 046997 overhead at about 17:13 UTC. It is not part of the batch. It processes the 16:45 and 17:15 UTC INSAT scans on a 0.02° grid over 6–14° N, 72–80.5° E. It checks the BT heights against ISRO's CTP, compares with GPM before and after correction, and estimates storm motion between the two scans.

| Option | Meaning |
| :--- | :--- |
| `--data` | folder searched recursively for the files [`datasets`] |
| `--out` | output root [`.`] |
| `--nav-offset EAST_KM NORTH_KM` | navigation correction to apply |

Outputs: `05_validation/gpm_colocation/kochi_20220606[_nav...].json`, the gridded NetCDF files in `04_corrected_output/netcdf/`, and `07_figures/kochi_20220606[_nav...].png`.

### Navigation

All navigation corrections are written as `NavigationCorrection` JSON files and are the correction to *add* to INSAT positions. See [concepts.md](concepts.md) for the coastline method and [cli.md](cli.md) for `pygeoparallax navigation`.

#### `check_navigation.py`

Checks INSAT-3DR L1C geolocation against the Natural Earth 10 m coastline. For each coastal window and scan, it rasterises the land at 0.005°, blurs it to the 4 km pixel footprint, keeps clear-sky pixels, and correlates the image with the land fraction at trial offsets (2 km steps, refined to 0.5 km). In daytime (solar zenith < 75°) it uses VIS; at night TIR1, with the sign reversed.

| Option | Meaning |
| :--- | :--- |
| `--data` | folder searched recursively [`datasets`] |
| `--land` | [`01_raw_data/natural_earth/ne_10m_land.geojson`] |
| `--out` | [`05_validation/navigation_check.json`] |
| `--min-r` | ignore matches weaker than this [0.5] |
| `--offset EAST_KM NORTH_KM` | apply this correction first; the result is then the residual error |
| `--files` | glob for L1C files under `--data` [`3RIMG_*_L1C_SGP_*.h5`] |
| `--windows` | only these coastal windows |

The JSON holds every match, the median and interquartile range of the good matches, and medians by window.

#### `test_navigation_parallax.py`

Writes `05_validation/nav_corrections/monsoon_median.json` (+1.8 km E, +4.8 km N, the all-India monsoon median from coastline matching) and runs every usable case with it (`<case>_mnav`, navigation only). It then tabulates the line-of-sight offset in four states (raw, parallax, navigation, both), for both fields and both windows.

| Option | Meaning |
| :--- | :--- |
| `--base` | validation folder (required) |
| `--rerun` | re-run cases whose navigation result already exists |

Output: `05_validation/gpm_colocation/nav_parallax_test.csv` (`valid` is true when all four matches lie inside the search).

#### `yearly_navigation.py`

Builds one navigation correction per monsoon year. Night-time matching fails in the monsoon and single-day daytime matches scatter by about 10 km, so matches are pooled over a season. For every case folder, it measures the coastline offset in each daytime L1C scan (03:15–08:15 UTC) in the four coastal windows nearest the region. It keeps matches with r ≥ 0.7, not at the search edge, and both components within 25 km. A year with fewer than 8 such matches gets the all-years value.

| Option | Meaning |
| :--- | :--- |
| `--base` | validation folder (required) |
| `--land` | [`01_raw_data/natural_earth/ne_10m_land.geojson`] |
| `--rerun` | re-measure folders already in `yearly_matches.csv` |

Outputs in `05_validation/nav_corrections/`: `pooled_<year>.json`, `yearly_matches.csv`, `yearly_summary.csv`.

Coastal windows used per region (from `near_storm_navigation.NEAR`):

| Region | Windows |
| :--- | :--- |
| `northeast` | chittagong, sundarbans, rakhine, odisha |
| `himalaya` | kutch, saurashtra, sundarbans, odisha |
| `central` | odisha, andhra, konkan, saurashtra |
| `south` | kerala, goa_karnataka, chennai, sri_lanka |

#### `run_navigation_states.py`

Re-runs every usable case with whole-scene navigation corrections (`--nav-only`, so only the `nav` state is computed):

| Tag | Correction |
| :--- | :--- |
| `ynav` | the year's pooled value, `nav_corrections/pooled_<year>.json` |
| `mnav` | the all-India monsoon median, `nav_corrections/monsoon_median.json` (+1.8 km E, +4.8 km N; created if missing) |
| `gnav` | the GPM-derived, leave-one-case-out value, `nav_corrections/gpm_loo_<case>.json` |

| Option | Meaning |
| :--- | :--- |
| `--base` | validation folder (required) |
| `--rerun` | re-run existing runs |
| `--tags` | states to run, from `ynav`, `mnav`, `gnav` [`ynav mnav`] |

A case whose JSON for a state is missing is skipped with a message.

#### `gpm_navigation.py`

Estimates the INSAT navigation error from GPM itself. After parallax correction, the offset between an INSAT cold core and its GPM deep-echo cell is, to first order, the navigation error. For each case it takes the median cell offset in the corrected state and converts it to east/north. Each usable case then gets the median of the *other* cases (leave one case out).

It has no options. It reads `core_offsets_cells.csv`, `all_cases.csv` and the case JSON files. It writes `05_validation/nav_corrections/gpm_loo_<case>.json` and `gpm_navigation_by_case.csv`, and prints the pooled value with a bootstrap interval (10 000 resamples, seed 2026), and the medians by year and by region.

#### `near_storm_navigation.py`

Measures a navigation correction near each storm from daytime coastline matches (03:15–08:15 UTC on the case day and the days before and after) in the four nearest coastal windows. It builds a correction per case with `NavigationCorrection.from_matches`.

| Option | Meaning |
| :--- | :--- |
| `--base` | validation folder (required) |
| `--land` | [`01_raw_data/natural_earth/ne_10m_land.geojson`] |
| `--run` | re-run each case with its correction (`<case>_snav`) |

Outputs in `05_validation/nav_corrections/`: `near_<case>.json`, `near_storm_matches.csv`, `near_storm_summary.csv`. Per-case corrections turned out not to be reliable (see [results](#navigation-results)).

### Offsets, statistics and sensitivity

#### Meteosat IODC comparison (`download_seviri_iodc.py`, `compare_seviri_insat.py`)

A second geostationary view separates the two explanations left after the storm-tilt test: a real offset of the cold cloud top from the radar echo appears in Meteosat too, while an INSAT navigation error does not. Meteosat-8 (41.5° E) was the prime Indian Ocean (IODC) satellite until 31 May 2022, and Meteosat-9 (45.5° E) from 1 June 2022.

Setup, once:

1. Register at the EUMETSAT Earth Observation Portal (<https://eoportal.eumetsat.int>), free.
2. Get your consumer key and secret at <https://api.eumetsat.int/api-key>.
3. Store them on your own machine (never in the repository):
   ```bash
   eumdac set-credentials <consumer-key> <consumer-secret>
   ```
   `eumdac` comes with the `download` extra (`pip install -e ".[download]"`).

Then:

```bash
python scripts/download_seviri_iodc.py --dry-run --regions northeast himalaya   # list the cycles
python scripts/download_seviri_iodc.py --regions northeast himalaya             # download and crop
python scripts/compare_seviri_insat.py --base <validation folder>
```

`download_seviri_iodc.py` downloads, for each case, the two 15-min IODC cycles whose scan of the storm latitude brackets the GPM overpass (collection `EO:EUM:DAT:MSG:HRSEVIRI-IODC`, native format), crops them with satpy to the case region and keeps only the 10.8 µm channel, positions and line times (`--keep` keeps the full-disk files). `compare_seviri_insat.py` corrects each Meteosat cycle for its own parallax onto the case grid, measures storm motion between the two cycles, and reports (1) the INSAT minus Meteosat displacement of the corrected cloud field near the storm, the decisive number, and (2) the cold-core offsets from the GPM cells for both satellites. Outputs are in `05_validation/seviri/`. At Meteosat's viewing angle over Northeast India (about 60°) the parallax is large and a 1 km height error moves a corrected pixel by about 1.7 km, so the Northeast and Himalaya cases are the most informative but also the most sensitive to cloud height.

#### `analyze_storm_tilt.py`

Measures how far the deep convective cells lean, from GPM Ku 3-D reflectivity (`SLV/zFactorFinal`, with `PRE/height` and the spacecraft position to place every range bin on its slanted beam). For each usable case it takes the deep cells (storm top above 10 km) near the convective cluster and computes the reflectivity-weighted centroid of the 2–4 km core and of higher layers (5–7, 8–10, 11–13 km and the echo top). It reports their displacement towards the satellite and across the line of sight.

| Option | Meaning |
| :--- | :--- |
| `--base` | validation folder (required) |
| `--radius` | km around the GPM convective cluster [250] |
| `--min-footprints` | smallest deep cell, in GPM footprints [2] |
| `--grow` | footprints added around each deep cell [2] |
| `--core-dbz` | threshold of the 2–4 km core [30 dBZ] |
| `--echo-dbz` | threshold in the upper layers [20 dBZ] |
| `--cases` | only these cases |

It writes `05_validation/gpm_colocation/storm_tilt_cells.csv` and `storm_tilt.csv`. Result: the cells lean 1.5 km westward between the core and the echo top, but only +0.8 km (−0.9 to +1.4 km) towards the satellite, far less than the about 6 km of parallax that the cell measure does not see (paper Section 5.6, Table 5).

#### `analyze_core_offsets.py`

Measures the cell-scale offset (see [the two offset measures](#the-two-offset-measures)) for every usable case.

| Option | Meaning |
| :--- | :--- |
| `--base` | validation folder (required) |
| `--radius` | window around the GPM cluster [250.0 km] |
| `--search` | distance around each GPM cell to look for the cold core [25.0 km] |
| `--min-cells` | smallest deep-echo cell [8 grid cells of 0.02°] |
| `--suffix` | case-name suffix of the runs to analyse, e.g. `_era5` [none] |
| `--nav-tag` | navigation runs for the navigation states: `<case><suffix>_<tag>_nav_*.nc` [`mnav`] |

It reads the gridded NetCDF files of the base runs (`<case><suffix>_no_nav_*.nc`) and, where present, of the navigation runs. Outputs in `05_validation/gpm_colocation/`:

- `core_offsets<tag>.csv`: per case, the median along- and cross-look offset in each state (`uncorrected`, `corrected`, `nav_only`, `nav_parallax`);
- `core_offsets<tag>_cells.csv`: per cell, the offsets (`kind` = state) and, with `kind == "heights"`, the INSAT cold-core height and the GPM maximum and 90th-percentile echo top.

`<tag>` is the suffix, plus `_<nav-tag>` unless the nav tag is `mnav`. So the default run writes `core_offsets.csv`, and `--nav-tag ynav` writes `core_offsets_ynav.csv`.

#### `validation_statistics.py`

Confidence intervals and paired tests (see [statistics](#statistics)).

| Option | Meaning |
| :--- | :--- |
| `--n-boot` | bootstrap resamples [10000] |
| `--seed` | [2026] |
| `--nav-tag` | navigation runs for the navigation states [`ynav`] |

It needs the base, `_mnav` and `_<nav-tag>` case JSON files, `core_offsets_cells.csv` and `core_offsets_<nav-tag>_cells.csv`. It writes `05_validation/statistics/statistics_<nav-tag>.json` and `field_offsets_by_case_<nav-tag>.csv`, and prints the tables. The project keeps two runs, `ynav` (per-year coastline navigation) and `gnav` (GPM-fitted navigation), with the printed tables saved as `.txt`:

```bash
python scripts/validation_statistics.py --nav-tag ynav > 05_validation/statistics/statistics_ynav.txt
python scripts/validation_statistics.py --nav-tag gnav > 05_validation/statistics/statistics_gnav.txt
```

#### `compare_variants.py`

Re-runs every usable case with a processing variant and compares it with the baseline:

- `era5`: cloud-top heights from ERA5 profiles (`--profile era5`); cases without `era5_pl_*.nc` are skipped;
- `dem`: terrain-aware correction (`--dem`).

Each case is run without and with the monsoon-median navigation (`<case>_<variant>`, `<case>_<variant>_mnav`). Run `test_navigation_parallax.py` first, because it writes `monsoon_median.json` and the baseline `_mnav` runs.

| Option | Meaning |
| :--- | :--- |
| `--base` | validation folder (required) |
| `--variant` | `era5` or `dem` (required) |
| `--dem` | DEM NetCDF, required for `--variant dem` |
| `--rerun` | re-run existing variant runs |

Output: `05_validation/gpm_colocation/<variant>_comparison.csv`, with the storm-top field offsets in four states for the baseline and the variant. A case and window count only if all eight matches lie inside the search. For cell offsets of a variant, run `analyze_core_offsets.py --suffix _<variant>`.

#### `check_parallax_visibility.py`

Draws diagnostic overlays around the main GPM convective cluster: uncorrected (left) and corrected (right) INSAT TIR1 with GPM storm-top contours at 10 and 13 km. On each GPM deep-echo cell (storm top > 10 km) it marks the cell centroid, the INSAT cold core within 25 km, and where geometry says the uncorrected cold core should appear.

| Option | Meaning |
| :--- | :--- |
| `--base` | validation folder (required) |
| `--cases` | case names (required) |
| `--half-width` | half-width of the map around the cluster centre [1.3°] |

It needs the `no_nav` NetCDF files of each case. Output: `07_figures/checks/<case>_visibility.png`, and a printed median distance from the raw cold core to the GPM cell and to the expected apparent position.

### Benchmark and datasets

#### `benchmark_scenes.py`

Runs the full pipeline on many L1C scenes and records the time of each stage, peak memory, missing data, cloud fraction, parallax shift, fill statistics and clear-cell changes. It reads TIR1 and WV over the 0.04° South Asia grid with a fixed navigation correction (−0.5 km E, +2.5 km N). Failures are recorded, not raised.

| Option | Meaning |
| :--- | :--- |
| `--base` | folder searched recursively for `3RIMG_*_L1C_SGP_*.h5` (required) |
| `--limit` | process only the first N scenes |

Output: `05_validation/benchmark/benchmark_scenes.csv`. Needs `psutil`.

#### `build_paired_dataset.py`

Writes the paired uncorrected / corrected dataset on one grid for every L1C file under `--input`: `<out>/uncorrected/<scene>.nc` (Model A input) and `<out>/corrected/<scene>.nc` (Model B input), plus `<out>/manifest.csv`. Both files use the same navigation, cloud-top heights and resampling, so clear cells are identical. Scenes whose two files exist are skipped.

| Option | Meaning |
| :--- | :--- |
| `--input` | folder searched recursively for L1C files (required) |
| `--out` | [`04_corrected_output/paired`] |
| `--channels` | [TIR1 TIR2 WV MIR VIS] |
| `--grid LAT_MIN LAT_MAX LON_MIN LON_MAX RES` | [0 40 60 100 0.04] |
| `--nav` | `pooled` (−0.5 km E, +2.5 km N), `none`, or a navigation JSON [`pooled`] |
| `--era5` | ERA5 file or folder of `era5_pl_*.nc`; the hour nearest the scan, within 3 h |
| `--dem` | DEM NetCDF for terrain-aware correction (corrected files only) |
| `--list` | CSV with an `l1c_file` column: process only these files |
| `-j`, `--workers` | parallel processes [1] |

The U-Net experiment did not use this dataset; it used corrected copies of the group's own patches (see [unet.md](unet.md)).

### Figures

#### `make_paper_figures.py`

Writes the manuscript figures to `07_figures/paper/` as PNG (300 dpi) and PDF. It has no options. `main()` makes:

| Figure | Content | Inputs |
| :--- | :--- | :--- |
| `fig1_geometry` | VZA and the parallax shift of a 12 km cloud top over India, with the four regions | geometry only |
| `fig2_navigation` | navigation offsets from coastline matching, 2022–2024 | `nav_corrections/<DDMMMYYYY>.json` |
| `fig3_cases` | uncorrected line-of-sight offset per case against the applied shift | `all_cases.csv`, `core_offsets_cells.csv` |
| `fig4_states` | cell offsets in four states, with the field mean | `core_offsets_cells.csv`, `core_offsets_ynav_cells.csv`, `core_offsets_gnav_cells.csv`, case JSON with `_mnav`, `_ynav`, `_gnav` |
| `fig5_heights` | INSAT cold-core height against GPM maximum echo top per cell | `core_offsets_cells.csv` |
| `fig6_terrain` | clear-sky terrain parallax from SRTM | `02_standardized_grid/srtm_0p01deg.nc` (skipped if missing) |

The ray-tracing schematic, `fig0_schematic()`, is in the same file but is not called by `main()`.

## The two offset measures

Both measures are GPM minus INSAT, split into a component along the line of sight (along-look) and one across it (cross-look). The split uses the viewing azimuth at the GPM convection centre. **Positive along-look means INSAT must move towards the satellite to match GPM.** Parallax displaces clouds away from the satellite, so an uncorrected scene should give a positive along-look offset equal to the parallax shift. Parallax correction should not change the cross-look offset.

### Storm-scale field correlation

Computed in `run_validation_case.py` (`near_metrics`):

1. Find the densest GPM convective cluster: the 1° bin with the most convective footprints, and all convective footprints within 1.35° (about 150 km) of its centre. Its mean position is the convection centre.
2. Take the grid cells inside the GPM swath and within 150 km or 250 km of the centre.
3. Find the shift that best correlates the two fields, refined to a fraction of a cell with a parabola fit. The search is ±10 cells of 0.02°, about ±22 km.
   - **Storm-top field (primary):** −TIR1 BT against GPM storm-top height. Both describe the same storm tops.
   - **Rain field (secondary):** −TIR1 BT against GPM near-surface reflectivity Z.
4. A match counts only if both components lie inside the search (\|lag\| < 9.5 cells).

The main results use the storm-top field in the 250 km window. The measure is driven by the large cold anvil against the radar's rain area.

The whole-box metrics in the same JSON (`uncorrected`, `corrected`) use cold cloud BT < 235 K against echo Z > 25 dBZ for IoU, Pearson correlation, mutual information and best lag (`--max-lag`, default 8 cells). They also give the IoU of deep cores (BT < 220 K) against GPM convective rain and against deep echoes (storm top > 8 km).

### Cell-scale cold core against deep echo

Computed in `analyze_core_offsets.py`:

1. Inside the GPM swath and within `--radius` (250 km) of the convection centre, label each GPM deep-echo cell: connected cells with storm top > 10 km and at least `--min-cells` (8) grid cells.
2. Around each cell's centroid, take the INSAT pixels within `--search` (25 km). The cold core is the centroid of those within 3 K of the local minimum BT.
3. The cell offset is the GPM centroid minus the cold core, split into along- and cross-look. The case value is the median over its cells.

This measure compares the coldest tops with the tallest echoes. Whole-window centroids do not work, because a 150 km window holds several cells.

## Correction states

| State | Name in the scripts | Navigation | Parallax | Run |
| :--- | :--- | :--- | :--- | :--- |
| Raw | `raw`, `uncorrected` | none | no | `<case>`, `no_nav` |
| Parallax only | `parallax`, `corrected` | none | yes | `<case>`, `no_nav` |
| Navigation only | `nav`, `nav_only` | per-year pooled (`ynav`) | no | `<case>_ynav` |
| Navigation + parallax | `both`, `nav_parallax` | per-year pooled (`ynav`) | yes | `<case>_ynav` |
| All-India navigation + parallax | `both_allindia` | +1.8 km E, +4.8 km N (`mnav`) | yes | `<case>_mnav` |
| GPM navigation + parallax | `both_gpm` | leave-one-case-out from GPM (`gnav`) | yes | `<case>_gnav` |

The all-India value is a sensitivity test. The GPM-derived state tests whether a single translation can centre both measures.

## Statistics

`validation_statistics.py` computes:

- **Field measure** (storm-top field, 250 km, only cases valid in every state): per state, the median absolute and the mean along-look offset, with 95 % percentile-bootstrap intervals (cases resampled with replacement).
- **Paired comparisons** (raw → parallax, raw → navigation + parallax, parallax → navigation + parallax, raw → all-India navigation + parallax): median change in absolute offset with a bootstrap interval, the Wilcoxon signed-rank test on the paired absolute offsets, and the exact sign test on the number of cases that improve. The cross-look offset gets the same paired test for raw → parallax.
- **Viewing-angle dependence** of the raw offset: Spearman correlation with tan(VZA), and the least-squares slope against tan(VZA) with a bootstrap interval. Pure parallax of deep convection would give a slope of about 10–12 km per unit tan(VZA).
- **Cell measure**: cells of one storm are not independent, so the interval of the median comes from a cluster bootstrap that resamples cases and keeps all their cells. Paired tests use per-case medians (Wilcoxon).

Defaults: 10 000 resamples, seed 2026.

## Results

All numbers below come from `00_Documentation/validation_summary.md` and `08_manuscript/results_discussion_draft.md`. Offsets are GPM minus INSAT along the line of sight.

### Cases

63 cases from the monsoons of 2018–2024 were processed. GPM was within 5 min of the INSAT scan at the storm; for the usable cases the median was 1.0 min and the maximum 2.9 min.

| Region | VZA at storm | Processed | Usable | Too little convection | No reliable match |
| :--- | :--- | ---: | ---: | ---: | ---: |
| South India | 9–21° | 17 | 14 | 0 | 3 |
| Central India | 22–33° | 25 | 15 | 0 | 10 |
| Himalaya | 29–37° | 11 | 4 | 6 | 1 |
| Northeast India | 31–38° | 10 | 5 | 3 | 2 |
| **Total** | | **63** | **38** | **9** | **16** |

In the field measure, 30 cases give a reliable match in every state; these are used for paired comparisons. In the cell measure, 157–167 GPM deep-echo cells in 27–28 cases are matched to an INSAT cold core in each state.

The correction moved deep cores (BT < 220 K) by a median of 3.9 km in South India, 7.3 km in Central India, 9.8 km over the Himalaya and 10.5 km over Northeast India (7.2 km over all usable cases).

### Offsets by state

| State | Field mean [km] | Field median absolute [km] | Field cases improved vs raw | Cells, median [km] (95 % interval) |
| :--- | ---: | ---: | ---: | :--- |
| Raw | +2.2 | 5.1 | – | −0.1 (−2.7 … +3.5) |
| Parallax only | −1.9 | 3.8 | 18 of 30 | −4.7 (−6.8 … −0.9) |
| Coastline navigation + parallax | −1.0 | 4.3 | 15 of 30 | −3.3 (−5.9 … +0.2) |
| GPM navigation + parallax (leave one out) | +4.9 | 6.0 | 10 of 31 | −0.5 (−2.6 … +2.9) |

Field: 30 cases (31 for the GPM-navigation row). Cells: 157–167 cells in 27–28 cases, intervals from the cluster bootstrap.

### What the results show

- **The correction acts only along the line of sight.** The cross-look offset does not change: median change 0.0 km, 95 % interval −0.2 to +0.2 km (30 cases).
- **Storm scale.** Parallax correction reverses the mean field offset, from +2.2 km (+0.1 to +4.2) to −1.9 km (−4.2 to +0.3). The per-case gain is not significant: 18 of 30 cases improve, median change −1.1 km (−1.6 to +1.2), sign test p = 0.36, Wilcoxon p = 0.66.
- **Cell scale.** Uncorrected cold cores already sit on the GPM deep-echo cells (−0.1 km). Parallax correction moves them 4.7 km past; the per-case change is −4.5 km (p < 0.001).
- **Only about 5 % of the computed parallax is visible.** The median per-case ratio of raw cell offset to applied shift is 0.05 (95 % interval −0.47 to +0.55). The raw field offset does not grow with viewing angle: Spearman ρ = −0.01, slope −0.8 km per unit tan(VZA), 95 % interval −12.9 to +9.4 km.
- **The comparison method detects parallax when it is there.** A synthetic storm through the same gridding and matching code gives a raw offset of +10.9 km against +10.5 km expected at VZA 35°, and +3.5 km against +3.9 km at VZA 15°.
- **No single translation centres both measures.** Navigation fitted to the GPM cells centres the cell measure but makes the field measure worse than raw (Wilcoxon p = 0.027). The two measures differ by 2–3 km with coastline navigation and by about 5 km once navigation is fitted to the cells.
- **Conclusion:** GPM-based validation of absolute position is limited to about ±3–5 km for monsoon deep convection. The two measures differ because they compare different parts of the storm. The tilt of the convective column, measured from GPM's 3-D reflectivity, is too small towards the satellite (+0.8 km) to hide the parallax; an offset of the cold top above the radar's view or a northward navigation error remain possible.

### Navigation results

- Coastline matching shows a seasonal navigation error: 7–20 km to the west from late September to mid-March, small from mid-April to September.
- In the monsoon, night-time matching fails (r < 0.4 on every night-time case scan), and daytime matches of the same coast 1–2 h apart differ by about 9–10 km. Per-case corrections are therefore not reliable.
- The per-year pooled values are small: −2.0 to +3.0 km east and −0.8 to +2.5 km north. 2018 has too few matches and uses the all-years value, +0.5 km E, +1.5 km N.
- Individual coasts give north values from −2.5 km (Chennai) to +8.8 km (Kutch), with 5–8 km spread within one coast.
- Navigation fitted to GPM (leave one case out): +5.0 km E (95 % interval +1.4 to +5.8) and +5.8 km N (+2.9 to +8.7).

### Heights, ERA5 and terrain

- In 206 matched cells (29 cases), the BT height of the INSAT cold core has a median of 16.6 km, and 46 % of the cores reach the 17 km tropopause cap. The GPM maximum echo top in the same cells has a median of 11.9 km. The median difference per cell is 3.2 km.
- ERA5 profiles instead of the AFGL atmosphere (14 cases of 2022–2024) changed cold-core heights by −0.15 km and every offset by less than 0.5 km.
- Terrain-aware correction with SRTM (14 cases of 2022–2024) leaves field and cell offsets identical to 0.1 km. It does move clear-sky ground in the Himalayan scenes by 1.3–2.5 km (median), up to 5.8 km, changing 9–19 % of grid cells.
- Placing GPM storm tops on the slanted Ku beam changes the cell medians by at most 0.6 km.

### Benchmark

The pipeline processed all 148 monsoon scenes without a failure: 1.8 s per scene (median; 3.2 s at most) on a laptop, with about 450 MB of memory. After correction, 98.7 % of grid cells hold an observed pixel, 1.3 % are filled from neighbours and 0.007 % stay empty. Corrected clouds cover 2.5 % of previously clear cells (median). Fourteen scenes of 11–14 June 2023 are partial scans, with up to 57 % of the image missing.

### Earlier 12-case result

With the first 12 cases (2022–2024), parallax correction improved the field measure in 10 of 12 cases (sign test p = 0.039). This did not hold in the full set of 38 cases. Older tables in `validation_summary.md` (sections "Result 1" to "Statistics (12 cases)") refer to that earlier set.

## See also

- [unet.md](unet.md): the U-Net A/B experiment on precipitation type.
- [outputs.md](outputs.md): the variables in the corrected NetCDF files.
- [troubleshooting.md](troubleshooting.md): common reader and data problems.
- [development.md](development.md): repository structure and tests.
