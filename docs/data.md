# Input data

This page describes every dataset PyGeoParallax-IN reads: what it is, which variables are used, known problems, where to get it, what registration it needs, and where the project expects it. Only the INSAT-3DR L1C file is required for a basic correction; everything else is optional or used for validation.

Never put account names, passwords, API keys or tokens in the repository, in notebooks or in these docs. Keep them in the per-user files each service expects (for example `~/.cdsapirc`), outside the project folder.

For how the data are used, see [concepts.md](concepts.md). For the readers, see [python_api.md](python_api.md#ingest). For installation of the optional packages (`cdsapi`, `rasterio`), see [installation.md](installation.md).

## Summary

| Dataset | Needed for | Reader or script | Source | Registration |
| :--- | :--- | :--- | :--- | :--- |
| INSAT-3DR Imager L1C SGP | every correction | `ingest.read_insat_l1c` | MOSDAC (ISRO) | free MOSDAC account |
| INSAT-3DR L2B CTP | optional clear-sky BT for the cloud mask; cross-check | `ingest.read_insat_csbt`, `ingest.read_insat_ctp` | MOSDAC (ISRO) | free MOSDAC account |
| GPM DPR 2A Ku V08 | validation | `ingest.read_gpm_2a` | NASA GES DISC | free NASA Earthdata Login |
| ERA5 pressure levels | optional cloud-top height profiles | `scripts/download_era5.py`, `ingest.read_era5_profiles` | Copernicus Climate Data Store | free CDS account and API key |
| SRTM GL1 | optional terrain-aware correction | `scripts/prepare_srtm.py`, `ingest.read_srtm` | OpenTopography | free OpenTopography account (API key for scripted downloads) |
| Natural Earth 10 m land | navigation correction | `navigation.load_land` | Natural Earth | none |

## Project layout

Raw inputs go under `01_raw_data/`. The folders exist in the repository (kept with `.gitkeep`); their contents are git-ignored.

```text
01_raw_data/
├── insat3dr_l1c/<YYYY>_JJAS/          INSAT-3DR L1C SGP files (3RIMG_*_L1C_SGP_V01R00.h5)
├── insat3dr_cth/<YYYY>_JJAS/          INSAT-3DR L2B CTP files (3RIMG_*_L2B_CTP_V01R00.h5)
├── gpm_dpr_2adpr/overpasses_2022_2024/ GPM 2A Ku orbits
├── era5_reanalysis/2022_2024_hourly/  ERA5 pressure-level NetCDF
├── srtm_dem/south_asia_tiles/         SRTM GL1 GeoTIFF tiles
├── natural_earth/ne_10m_land.geojson  Natural Earth 10 m land polygons
└── imd_dwr/<site>/                    IMD Doppler Weather Radar (agartala, goa, kochi, mumbai); not used yet
02_standardized_grid/
└── srtm_0p01deg.nc                    SRTM grid written by scripts/prepare_srtm.py
```

Fixed defaults in the code:

| Path | Used by |
| :--- | :--- |
| `01_raw_data/natural_earth/ne_10m_land.geojson` | default `--land` of `pygeoparallax navigation` |
| `02_standardized_grid/srtm_0p01deg.nc` | default `--out` of `scripts/prepare_srtm.py`; pass it to `--dem` |

The validation scripts (`scripts/run_all_cases.py` and others) do not use `01_raw_data/`. They expect one folder per case under a `--base` folder, named `<region>_<YYYYMMDD>` (for example `northeast_20240818`), holding all files of that case:

```text
northeast_20240818/
├── 3RIMG_18AUG2024_2215_L1C_SGP_V01R00.h5      case scan
├── 3RIMG_18AUG2024_2215_L2B_CTP_V01R00.h5      its CTP file
├── 3RIMG_18AUG2024_0415_L1C_SGP_V01R00.h5      daytime scans for navigation
├── ...                                          (case day and the days before and after)
├── 2A.GPM.Ku.V10-20251112.20240818-S215337-E232650.059478.V08A.nc
└── era5_pl_2024081822.nc                        from scripts/download_era5.py
```

The case scans are pinned in `00_Documentation/events/case_scans.csv`. See [validation.md](validation.md) for the order in which to run the scripts.

---

## INSAT-3DR Imager L1C SGP

INSAT-3DR is a geostationary satellite at 74.0° E. Its Imager scans the full disk every 30 minutes, with scans starting at HH:15 and HH:45 UTC. The Level-1C sector product (`L1C_SGP`) is already navigated and resampled by ISRO onto a Mercator grid. INSAT-3DR products use the INSAT-3D formats (SAC, 2014: *INSAT-3D data products format document*).

### File naming

```text
3RIMG_<DDMONYYYY>_<HHMM>_L1C_SGP_V01R00.h5
3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5      example: 1 Aug 2023, scan starting 18:15 UTC
```

`3R` is INSAT-3DR, `IMG` the Imager, `<HHMM>` the nominal scan start (UTC). The month is in capitals (`JAN` … `DEC`). A file is about 90–100 MB.

### Grid

- Mercator on WGS84, `lon_0` = 75° E (from the `Projection_Information` dataset), true scale at the equator.
- 3207 rows × 3062 columns covering 50° S–50° N, 20–130° E, about 4 km pixels.
- `X` and `Y` are projection coordinates [m]. The reader takes them as pixel centres; the first and last values coincide with the product's corner coordinates.
- Pixel centres are evenly spaced in longitude and in Mercator northing, so the grid is separable. `resample.NativeGrid` fits it (see [concepts.md](concepts.md#correction-on-the-native-pixel-grid)).

### Channels and lookup tables

Each channel is stored as 10-bit counts `IMG_<channel>` of shape `(1, 3207, 3062)`, with a 1024-entry lookup table that converts count to the physical value. The reader indexes the table with the count (`value = LUT[count]`) and sets fill values to NaN.

| Name in the reader | Count dataset | Lookup table | Output | Central wavelength [µm] | Count fill value |
| :--- | :--- | :--- | :--- | ---: | ---: |
| `VIS` | `IMG_VIS` | `IMG_VIS_ALBEDO` | albedo [%] | 0.65 | 0 |
| `SWIR` | `IMG_SWIR` | `IMG_SWIR_RADIANCE` | radiance [mW cm⁻² sr⁻¹ µm⁻¹] | 1.625 | 0 |
| `MIR` | `IMG_MIR` | `IMG_MIR_TEMP` | brightness temperature [K] | 3.907 | 1023 |
| `WV` | `IMG_WV` | `IMG_WV_TEMP` | brightness temperature [K] | 6.866 | 1023 |
| `TIR1` | `IMG_TIR1` | `IMG_TIR1_TEMP` | brightness temperature [K] | 10.785 | 1023 |
| `TIR2` | `IMG_TIR2` | `IMG_TIR2_TEMP` | brightness temperature [K] | 11.966 | 1023 |

Lookup-table entries equal to the table's own `_FillValue` (999) also become NaN. VIS and SWIR are sampled at 1 km at the sub-satellite point and the infrared channels at 4 km; in the L1C SGP product all channels share the same 4 km grid.

### Attributes used

| Attribute | Use |
| :--- | :--- |
| `Acquisition_Start_Time`, `Acquisition_End_Time` | `start_time`, `end_time`; `time` is their midpoint |
| `Nominal_Central_Point_Coordinates(degrees)_Latitude_Longitude` | `sub_satellite_longitude` (74.0 in L1C) |
| `Satellite_Name`, `Sensor_Name`, `Unique_Id` | `satellite`, `sensor`, `product` |

The full-disk scan runs north to south, 81° N to 81° S, in about 26.9 min (for example 18:15:26 to 18:42:20 UTC). The reader uses one time per file, the midpoint.

### Known quirks

- **Satellite angles are about 1° off.** The `Sat_Elevation` and `Sat_Azimuth` fields differ from the geometric values by about 1° in zenith and 1.1° in azimuth. At the sub-satellite point they give an elevation of 90.86°, which is impossible. The reader does not load them. Viewing angles are computed with `geometry.satellite_view_angles`, which agrees with pyorbital within 0.01°.
- **Sun angles** (`Sun_Elevation`, `Sun_Azimuth`) differ by up to several degrees from a single-time solar calculation, partly because of the 27-minute scan. They are not loaded; use `geometry.solar_angles`.
- **Navigation errors.** Positions can be wrong by up to 20 km, with a seasonal pattern: a 7–20 km westward correction is needed from late September to mid-March, and errors are small from mid-April to September. See [concepts.md](concepts.md#navigation-correction).
- **Partial scans.** 14 scenes from 11–14 June 2023 are partial: up to 57 % of the TIR1 array is fill (only rows 665–1302 hold data in the 12 June 04:15 file). Missing pixels stay NaN.
- **Missing scans.** The 18:15 UTC scan is often missing from the MOSDAC archive, in September (eclipse season) and at other times.
- **Truncated downloads** fail when read. Check file sizes (for example, a 30 MB file of an expected 88 MB) and download again. `pygeoparallax navigation` skips unreadable files with a message.
- **Pixel centres or edges.** If ISRO meant `X`/`Y` as edges, positions are off by at most half a pixel (2 km). The coastline check shows no such error.

### Where to get it

- **Source:** MOSDAC, Space Applications Centre, ISRO: <https://www.mosdac.gov.in>. Search for the INSAT-3DR Imager Level-1C sector product (`3RIMG_L1C_SGP`).
- **Registration:** a free MOSDAC account is needed to order and download. Archive orders are placed through the MOSDAC web interface; MOSDAC also offers a download API for scripted access (see the MOSDAC website for its current terms).
- **Where to put it:** `01_raw_data/insat3dr_l1c/<YYYY>_JJAS/`, or a case folder for validation.
- **Typical volume:** about 100 MB per scan, up to 48 scans per day.

---

## INSAT-3DR L2B CTP and clear-sky BT

The Level-2B cloud-top pressure product is optional. It contains **no cloud-top height**.

### File naming

```text
3RIMG_<DDMONYYYY>_<HHMM>_L2B_CTP_V01R00.h5
```

About 3 MB per scan, on the same time slots as L1C.

### Contents

The file has two grids, both in satellite projection over the full disk:

| Grid | Size | Variables | Read by |
| :--- | :--- | :--- | :--- |
| Cloud grid, about 37 km boxes over India | 313 × 312 | `CTP` cloud-top pressure [hPa, 25 hPa steps], `CTT` cloud-top temperature [K], `EFF_EMISS` effective emissivity; `Latitude`, `Longitude` | `read_insat_ctp` |
| Clear-sky grid | 325 × 325 | `CSBT_TIR1`, `CSBT_TIR2`, `CSBT_MIR`, `CSBT_WVR` clear-sky BT [K]; `CLRFR_*` clear fraction; `CSBT_Latitude`, `CSBT_Longitude` | `read_insat_csbt` |

Values are scaled integers or floats with `scale_factor`, `add_offset` and `_FillValue`; the readers apply them. The water-vapour channel is called `WVR` here, not `WV` as in L1C; `read_insat_csbt` accepts either name.

### Use in the project

- **Clear-sky BT** (`CSBT_TIR1`) is the reference for the cloud mask: a pixel is cloudy if its TIR1 BT is more than 8 K below it. It is sampled to the L1C pixels by nearest neighbour (`resample.sample_nearest`, 40 km in the validation scripts). Without it, the mask uses BT < 270 K. The `pygeoparallax l1c` command always uses the fixed threshold.
- **Cloud-top pressure** is used only as a cross-check, converted to height with `cloudheight.height_from_pressure`.

### Known quirks

- **82° E attribute.** The `Nominal_Central_Point_Coordinates(degrees)_Latitude_Longitude` attribute says 82° E. That is wrong for INSAT-3DR: the latitude/longitude arrays and the `SAT_ZEN` minimum are centred on about 74° E, consistent with the L1C files. The readers use the arrays and ignore that attribute. Do not take `sub_satellite_longitude` from an L2B file.
- The acquisition times differ slightly from those of the matching L1C file (for example 18:15:06 against 18:15:26).

### Where to get it

MOSDAC, as for L1C (product `3RIMG_L2B_CTP`), with the same account. Put the files in `01_raw_data/insat3dr_cth/<YYYY>_JJAS/` or in the case folder next to the L1C file of the same slot.

---

## GPM DPR 2A Ku V08

The GPM Core Observatory carries the Dual-frequency Precipitation Radar (DPR). The project uses the Ku-band Level-2A product, version V08, for validation only.

### File naming

```text
2A.GPM.Ku.V10-20251112.<YYYYMMDD>-S<HHMMSS>-E<HHMMSS>.<orbit>.V08A.nc
2A.GPM.Ku.V10-20251112.20240818-S215337-E232650.059478.V08A.nc
```

One file per orbit (about 1.5 h), about 400 MB. The `.nc` V08 files are NetCDF-4, which is HDF5 underneath; the reader opens them with h5py, as it does the older `.HDF5` V07 files. `read_gpm_2a` also reads `2A.GPM.DPR` files, which have the same `FS` layout.

### Variables used

All from the full-swath group `FS` (about 245 km wide, footprint about 5 km):

| Output name | Path in `FS` | Units |
| :--- | :--- | :--- |
| `lat`, `lon` | `Latitude`, `Longitude` | degrees (footprint at the surface) |
| `time` | `ScanTime/*` | per scan |
| `storm_top_height` | `PRE/heightStormTop` | m |
| `bright_band_height` | `CSF/heightBB` | m |
| `zero_deg_height` | `VER/heightZeroDeg` | m |
| `surface_elevation` | `PRE/elevation` | m |
| `z_near_surface` | `SLV/zFactorFinalNearSurface` | dBZ (corrected) |
| `precip_rate` | `SLV/precipRateNearSurface` | mm h⁻¹ |
| `precip_type` | `CSF/typePrecip` // 10 000 000 | 0 none, 1 stratiform, 2 convective, 3 other, −1 missing |
| `top_lat`, `top_lon` | from `navigation/scPos` | storm-top position on the beam |

Values of −1111.1 ("not applicable", for example no bright band) and −9999.9 (missing) become NaN.

### Storm tops on the slanted beam

GPM 2A gives each footprint's position at the surface. An echo at height $h$ lies on the slanted radar beam, displaced towards the spacecraft by about $h\tan\theta_{\mathrm{GPM}}$, where $\theta_{\mathrm{GPM}}$ is the local zenith angle of the beam. This is up to about 5 km for a 15 km storm top at the swath edge. The reader places each storm top on the beam (`top_lat`, `top_lon`) by intersecting the line from the footprint to the spacecraft (`navigation/scPos`) with the surface at height $h$, with Newton refinement. The median displacement in the validation cases is 1 km. Use `top_lat`/`top_lon` for storm tops and `lat`/`lon` for near-surface quantities.

### Where to get it

- **Source:** NASA Goddard Earth Sciences Data and Information Services Center (GES DISC), collection `GPM_2AKu`, version 08 (DOI 10.5067/GPM/DPR/Ku/2A/08). Search with NASA Earthdata Search (<https://search.earthdata.nasa.gov>) or GES DISC (<https://disc.gsfc.nasa.gov>).
- **Registration:** a free NASA Earthdata Login is needed to download. The catalogue search is public: `scripts/find_gpm_overpasses.py` and `scripts/find_validation_cases.py` query NASA's CMR to find overpasses without a login.
- **Where to put it:** `01_raw_data/gpm_dpr_2adpr/overpasses_2022_2024/`, or the case folder for validation.

---

## ERA5 pressure levels

ERA5 temperature and geopotential give per-pixel profiles for cloud-top height, as an alternative to the AFGL tropical standard atmosphere. They are optional: on the validation cases, ERA5 changed storm results by under 0.5 km.

### What is downloaded

`scripts/download_era5.py` requests, for each validation case folder:

| Item | Value |
| :--- | :--- |
| Dataset | `reanalysis-era5-pressure-levels` |
| Variables | `temperature`, `geopotential` |
| Levels | 29 levels: 1000, 975, 950, 925, 900, 875, 850, 825, 800, 775, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 225, 200, 175, 150, 125, 100, 70, 50 hPa |
| Time | the whole hour nearest the case scan, after adding 10 min (when INSAT reaches about 20–25° N) |
| Area | the case's region box padded by 1° |
| Format | NetCDF (0.25° grid) |
| Output | `<case folder>/era5_pl_<YYYYMMDDHH>.nc` |

```bash
pip install -e ".[download]"     # installs cdsapi
python scripts/download_era5.py --base <validation folder> --dry-run   # list the requests
python scripts/download_era5.py --base <validation folder>
python scripts/download_era5.py --base <validation folder> --only northeast_20240818
```

For a scene outside the case folders, request the same dataset, variables and levels for the hour and area you need (from the CDS web form or with `cdsapi`), and pass the file to `--era5` of `pygeoparallax l1c` or to `ingest.read_era5_profiles`. The area must cover the pixels you correct.

### Reading

`read_era5_profiles` accepts files with `t` and `z` on `pressure_level`, `latitude`, `longitude` and `valid_time` (or `time`). It converts geopotential to geometric height above mean sea level and orders levels from the surface up.

### Where to get it

- **Source:** Copernicus Climate Change Service, Climate Data Store (CDS): <https://cds.climate.copernicus.eu>. Dataset "ERA5 hourly data on pressure levels from 1940 to present" (DOI 10.24381/cds.bd0915c6).
- **Registration:**
  1. Create a free CDS account.
  2. Accept the dataset's licence on its download page (requests fail until you do).
  3. Copy your personal API key from your CDS profile into `~/.cdsapirc` (on Windows, `%USERPROFILE%\.cdsapirc`):
     ```text
     url: https://cds.climate.copernicus.eu/api
     key: <your API key>
     ```
     Keep this file outside the repository.
- **Where to put it:** the case folders (validation), or `01_raw_data/era5_reanalysis/2022_2024_hourly/`.


---

## SRTM elevation

SRTM GL1 heights give the ground height for terrain-aware correction. They are optional.

### Product

- SRTM GL1, 1 arcsecond (about 30 m) GeoTIFF tiles.
- Heights are above the EGM96 geoid, which lies 50–105 m below the WGS84 ellipsoid over India. The code uses them as they are (under 75 m change in the terrain correction at VZA 35°).
- The imager footprint is 4 km, so the tiles are block-averaged to 0.01° (about 1 km) while reading. Voids are ignored in the average; cells with no valid data are NaN and treated as sea level.

### Preparing the grid

`scripts/prepare_srtm.py` reads all tiles in a folder, mosaics and block-averages them, and writes one NetCDF with an `elevation` variable:

```bash
python scripts/prepare_srtm.py --tiles 01_raw_data/srtm_dem/south_asia_tiles \
    --out 02_standardized_grid/srtm_0p01deg.nc --res 0.01 --bbox 6 38 68 98
```

The defaults are `--res 0.01` and `--bbox 6 38 68 98` (6–38° N, 68–98° E). The script needs `rasterio` (`pip install rasterio`, or the `dev` extra). Damaged parts of a tile are skipped with a warning. Use the result with `--dem 02_standardized_grid/srtm_0p01deg.nc` on the command line, or `terrain.surface_height_from_dataset` in Python.

### Where to get it

- **Source:** OpenTopography (<https://opentopography.org>), dataset SRTM GL1 (global 30 m; API name `SRTMGL1`). Cite Farr et al. (2007).
- **Registration:** downloads through the web interface or the OpenTopography global DEM API need a free OpenTopography account. Scripted downloads use a personal API key from your account page; keep it out of the repository. The API limits the area per request, so India is downloaded as several rectangles.
- **Where to put it:** `01_raw_data/srtm_dem/south_asia_tiles/` (any GeoTIFF names; all `*.tif` in the folder are read). All tiles must have the same pixel size.

USGS EarthExplorer (<https://earthexplorer.usgs.gov>) offers the same 1 arcsecond SRTM data as 1° GeoTIFF tiles, with a free USGS account.

---

## Natural Earth 10 m land

Land polygons for the coastline-matching navigation correction.

- **File:** `ne_10m_land.geojson`, Natural Earth 1:10m physical vectors, land. Public domain, no registration.
- **Download:** <https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson>, or the "Land" layer of the 1:10m physical vectors at <https://www.naturalearthdata.com>.
- **Where to put it:** `01_raw_data/natural_earth/ne_10m_land.geojson` (the default of `pygeoparallax navigation --land`).

```bash
curl -L -o 01_raw_data/natural_earth/ne_10m_land.geojson \
    https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson
```

`navigation.load_land` merges all polygons into one geometry. The navigation code rasterises it at 0.005° and blurs it to the 4 km pixel footprint.

---

## Not used yet: IMD Doppler Weather Radar

The folders `01_raw_data/imd_dwr/{agartala,goa,kochi,mumbai}/` are reserved for India Meteorological Department radar data. Validation against ground radar is future work; the comparison functions in `pygeoparallax.validation` already accept any gridded radar field. Access is by request to IMD.
