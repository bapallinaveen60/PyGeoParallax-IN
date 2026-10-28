# API Reference (v0.4.0)

Public functions of the `pygeoparallax` package, grouped by module. Each function has a full docstring with parameters and units; this page is the map.

Conventions:
- Latitude and longitude in degrees; heights in metres above the WGS84 ellipsoid; shifts in km.
- INSAT-3DR sits at 74.0°E (`SATELLITE_LONGITUDES["INSAT-3DR"]`).
- NaN cloud-top height means clear sky (or unknown); those pixels are not moved.

## Top level

| Name | Purpose |
| :--- | :--- |
| `correct_scene(lat, lon, channels, cth, sat_lon=74.0, grid=SOUTH_ASIA_0P04, surface_height=None, correct=True, fill_radius=1)` | Whole pipeline for one scene: parallax (and optional terrain) correction, then occlusion-aware regridding. Returns an `xarray.Dataset` with the channels, `cth`, `shift_km`, `height`, `count` and `fill_flag`. `correct=False` gives the uncorrected scene on the same grid. |
| `correct_native(lat, lon, channels, cth, sat_lon=74.0, grid=None, surface_height=None, correct=True, fill_radius=1, fill_empty=False)` | The same correction, put back on the input's own pixel grid (dims `y`, `x`; same shape and pixel centres). The grid defaults to that of `lat`/`lon` (an L1C file read without navigation correction); pass a `NativeGrid` if the positions were shifted. `fill_empty=True` fills cells no pixel reached with the nearest corrected value (they keep `fill_flag` 2). |

## `pygeoparallax.ingest`

| Name | Purpose |
| :--- | :--- |
| `read_insat_l1c(path, channels, bbox=None, position_offset_km=None)` | INSAT-3DR Imager L1C SGP sector: BT [K] for IR channels, albedo [%] for VIS, 2-D `lat`/`lon`. `bbox` decodes only a region. `position_offset_km` applies a navigation correction: a fixed `(east, north)` pair or a callable such as `NavigationCorrection`. |
| `to_standard_scene(ds, cth=None)` | Turn an L1C dataset into the *standard scene* NetCDF layout used by the CLI. |
| `read_insat_ctp(path)` | L2B cloud-top pressure/temperature product (coarse boxes; no height). |
| `read_insat_csbt(path, channel="TIR1")` | Clear-sky BT from the same L2B product, for the cloud mask. |
| `read_era5_profiles(path, time=None)` | ERA5 pressure-level temperature and geopotential (CDS NetCDF) as `temperature` and geometric `height` on `(level, lat, lon)`, surface first. |
| `read_srtm(paths, bbox=None, res=0.01)` | SRTM GeoTIFF tiles (folder, glob or list) mosaicked and block-averaged to `res` degrees as `elevation` [m above EGM96]; damaged parts of a tile are skipped with a warning. |
| `read_gpm_2a(path, swath="FS", bbox=None)` | GPM 2A Ku/DPR: near-surface reflectivity and rain rate, storm-top height, precipitation type, scan times. Adds `top_lat`/`top_lon`: storm tops placed on the slanted radar beam. |
| `CONVECTIVE`, `STRATIFORM`, `OTHER`, `NO_RAIN` | GPM precipitation-type codes. |

## `pygeoparallax.cloudheight`

| Name | Purpose |
| :--- | :--- |
| `cloud_top_height(bt, clear_sky_bt=None, profile=TROPICAL)` | Height [m] where cloudy, NaN elsewhere. Cloudy means BT below clear-sky BT by 8 K, or below 270 K when no clear-sky BT is given. |
| `cloud_top_height_profiles(bt, lat, lon, profiles, clear_sky_bt=None, min_pressure=70)` | Same with gridded profiles (e.g. ERA5), interpolated to each pixel; the lookup runs down from each column's cold point. |
| `height_from_temperature(t, profile)`, `height_from_pressure(p, profile)` | Profile lookups (AFGL tropical by default, capped at the 17 km tropopause). |
| `cloud_mask(bt, clear_sky_bt=None, delta=8.0, threshold=270.0)` | The cloud mask on its own. |
| `effective_height(cth, scale=1.0, offset=0.0)` | `scale * cth - offset` [m], floored at 0, NaN kept: a lower height for precipitation work (offset about 3000 m, or scale about 0.7, from the GPM comparison). |
| `Profile`, `TROPICAL` | Atmospheric profile type and the default profile. |

## `pygeoparallax.geometry`

| Name | Purpose |
| :--- | :--- |
| `parallax_correct(lat, lon, height, sat_lon, h0=0.0, backend="numba")` | Ray intersection with the ellipsoid enlarged by the cloud height, refined by Newton steps (< 1 mm). Numba by default (0.5 s per full disk); `backend="numpy"` takes ~9 s. Returns corrected lat/lon. |
| `parallax_correct_terrain(lat, lon, cth, sat_lon, surface_height, ...)` | Same, with a DEM: clouds clamped to the ground, clear-sky terrain parallax corrected. |
| `parallax_shift(lat, lon, lat_c, lon_c)` | Displacement [km] between apparent and corrected positions. |
| `satellite_view_angles(lat, lon, sat_lon, h=0.0)` | Viewing zenith and azimuth angles [degrees]. |
| `solar_angles(time, lat, lon)` | Solar zenith and azimuth angles. |
| `geodetic_to_ecef`, `ecef_to_geodetic`, `enu_basis` | WGS84 coordinate transforms. |
| `GEO_RADIUS`, `SATELLITE_LONGITUDES` | Geostationary orbit radius; sub-satellite longitudes (INSAT-3DR 74.0°E, INSAT-3DS 82.0°E). |

## `pygeoparallax.resample`

| Name | Purpose |
| :--- | :--- |
| `Grid(lat_min, lat_max, lon_min, lon_max, res)` | Regular lat/lon grid. `SOUTH_ASIA_0P04` is 0–40°N, 60–100°E at 0.04°. |
| `resample(grid, lat, lon, height, values, fill_radius=1)` | Bucket resampling: the highest cloud wins each cell; small gaps are filled by IDW. |
| `bucket_max_height`, `idw_fill` | The two steps on their own. |
| `NativeGrid.from_2d(lat, lon)`, `NativeGrid.from_coords(lat_1d, lon_1d)` | A product's own separable pixel grid, regular in WGS84 Mercator northing (L1C) or in latitude. `fractional_index(lat, lon)` gives row/column; `index_space()` lets `resample` work on it. |
| `mercator_y(lat)`, `mercator_lat(y)` | Ellipsoidal (WGS84) Mercator northing and its inverse. |
| `sample_nearest(src_lat, src_lon, values, dst_lat, dst_lon, max_distance_km=50)` | Nearest-neighbour lookup between grids (e.g. clear-sky BT onto L1C pixels). |
| `OBSERVED`, `INTERPOLATED`, `EMPTY` | `fill_flag` values 0, 1, 2. |

## `pygeoparallax.terrain`

| Name | Purpose |
| :--- | :--- |
| `surface_height_from_dataset(dem, var="elevation")` | Callable `f(lat, lon) -> m` from a DEM on a regular grid, for `surface_height=`. |

## `pygeoparallax.navigation`

| Name | Purpose |
| :--- | :--- |
| `load_land(path)` | Load land polygons (Natural Earth 10 m GeoJSON). |
| `WINDOWS`, `EAST_ONLY` | The 13 coastal windows; the ones that only constrain east–west. |
| `measure_scan(path, land, windows=None)` | Coastline matching on one L1C scan: east/north offsets and correlation per window. |
| `measure_window(...)` | The same for one window and image. |
| `NavigationCorrection.from_matches(matches, min_r=0.6, ...)` | Smooth IDW correction from accepted matches (offsets ≤ 25 km, two-scan agreement within 5 km, single scans r ≥ 0.75). Callable as `f(lat, lon) -> (east_km, north_km)`; `to_json` / `from_json`. |

## `pygeoparallax.validation`

| Name | Purpose |
| :--- | :--- |
| `compare(sat, radar, sat_threshold, radar_threshold, ...)` | IoU, Pearson r, mutual information and best displacement in one call. |
| `iou`, `pearson`, `mutual_information` | Single metrics. |
| `best_displacement(a, b, max_lag=5)`, `subcell_displacement(a, b, max_lag=5)` | Shift (whole cells, or sub-cell by parabolic peak fit) that best aligns two fields. |
| `points_to_grid(grid, lat, lon, values, how="mean")` | Grid radar footprints. |
| `range_mask(grid, lat0, lon0, range_km)`, `nearest_time(times, target, max_dt="15min")` | Colocation helpers. |
| `REGIONS`, `region_mask`, `regional_stats` | Statistics by region. |
| `monte_carlo_shift`, `bias_sweep` | Sensitivity of the shift to cloud-top height errors. |

## Command line

```bash
pygeoparallax l1c "<L1C glob>" -o <dir> [-j N] [--native [--fill-empty]] [--bbox LAT0 LAT1 LON0 LON1] [--channels TIR1 TIR2 WV MIR]
                  [--era5 era5_pl.nc] [--cloud-threshold 270] [--height-offset KM] [--height-scale S] [--dem DEM.nc] [--nav-correction nav.json] [--no-correction] [--grid ...] [--overwrite]
pygeoparallax correct <in.nc> <out.nc> [--dem DEM.nc] [--nav-correction nav.json] [--no-correction] [--grid LAT0 LAT1 LON0 LON1 RES] [--height-offset KM] [--height-scale S]
pygeoparallax batch "<glob>" -o <dir> [-j N] [--overwrite] [same options]
pygeoparallax navigation "<L1C glob>" -o nav.json [--land ne_10m_land.geojson] [--windows ...] [--min-r 0.6]
pygeoparallax --version
```

Validation scripts (not part of the package) are in `scripts/`; see `validation_summary.md` for the order to run them.
