# Python API

A guided tour of the `pygeoparallax` package (version 0.4.1), module by module, with working examples. Every example on this page was run against the package source and the data files named in it. For the science behind each step, see [concepts.md](concepts.md). For the command-line interface, see [cli.md](cli.md). For the output variables, see [outputs.md](outputs.md).

Conventions:

- Latitude and longitude in degrees; heights in metres above the WGS84 ellipsoid; shifts in km (except `parallax_shift`, which returns metres).
- A NaN cloud-top height means clear sky or unknown. Those pixels are not moved.
- Functions accept NumPy arrays (or anything `np.asarray` accepts) and return NumPy arrays or `xarray.Dataset` objects.
- INSAT-3DR is at 74.0° E: `pygeoparallax.geometry.SATELLITE_LONGITUDES["INSAT-3DR"]`.

## Contents

1. [Example data](#example-data)
2. [Top level: correct_scene and correct_native](#top-level-correct_scene-and-correct_native)
3. [ingest](#ingest)
4. [cloudheight](#cloudheight)
5. [geometry](#geometry)
6. [resample](#resample)
7. [terrain](#terrain)
8. [navigation](#navigation)
9. [validation](#validation)
10. [demo](#demo)
11. [Recipes](#recipes)

## Example data

The examples use these files. Put them in the working directory, or change the paths. Where to get each one is described in [data.md](data.md).

| File | Used for |
| :--- | :--- |
| `3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5` | INSAT-3DR L1C scan, 1 Aug 2023 18:15 UTC (night) |
| `3RIMG_01AUG2023_1815_L2B_CTP_V01R00.h5` | the matching L2B CTP file (clear-sky BT) |
| `3RIMG_18AUG2024_2215_L1C_SGP_V01R00.h5` | the Northeast validation case scan, 18 Aug 2024 22:15 UTC |
| `era5_pl_2024081822.nc` | ERA5 pressure levels for that case (from `scripts/download_era5.py`) |
| `2A.GPM.Ku.V10-20251112.20240818-S215337-E232650.059478.V08A.nc` | GPM 2A Ku V08 orbit for that case |
| `3RIMG_07SEP2023_0415/0515/0615_L1C_SGP_V01R00.h5` | three daytime scans for the navigation example |
| `01_raw_data/natural_earth/ne_10m_land.geojson` | Natural Earth 10 m land |
| `01_raw_data/srtm_dem/south_asia_tiles/` | SRTM GL1 GeoTIFF tiles |
| `02_standardized_grid/srtm_0p01deg.nc` | SRTM grid made by `scripts/prepare_srtm.py` |

The [demo](#demo) and most of the [geometry](#geometry) and [resample](#resample) examples need no data.

---

## Top level: correct_scene and correct_native

```python
from pygeoparallax import correct_scene, correct_native, __version__
```

Both run the whole correction for one scene: parallax (and optional terrain) correction of every pixel, then occlusion-aware resampling. They differ only in the output grid.

```text
correct_scene(lat, lon, channels, cth, sat_lon=74.0, grid=SOUTH_ASIA_0P04, surface_height=None,
              correct=True, fill_radius=1, terrain_iterations=3) -> xarray.Dataset

correct_native(lat, lon, channels, cth, sat_lon=74.0, grid=None, surface_height=None,
               correct=True, fill_radius=1, fill_empty=False, terrain_iterations=3) -> xarray.Dataset
```

| Argument | Meaning |
| :--- | :--- |
| `lat`, `lon` | navigated (apparent) pixel positions [degrees], after any navigation correction |
| `channels` | dict of name to array, the values to carry, e.g. `{"TIR1": bt, "WV": wv}` |
| `cth` | cloud-top height above the ellipsoid [m]; NaN for clear sky |
| `sat_lon` | sub-satellite longitude [° E] |
| `grid` | `correct_scene`: a `resample.Grid` (default 0–40° N, 60–100° E at 0.04°). `correct_native`: a `resample.NativeGrid` (default: fitted to `lat`/`lon`) |
| `surface_height` | callable `f(lat, lon) -> m`, e.g. from `terrain.surface_height_from_dataset`; enables terrain-aware correction |
| `correct` | `False` regrids at the apparent positions: the uncorrected baseline on the same grid |
| `fill_radius` | largest gap in cells to fill by inverse-distance weighting (0 disables) |
| `fill_empty` | `correct_native` only: fill cells no pixel reached with the nearest corrected value (they keep `fill_flag` 2) |
| `terrain_iterations` | fixed-point iterations for the ground-height lookup |

Output variables: the channels, `cth`, `height` (the winning height in each cell), `count` (pixels per cell), `fill_flag` (0 observed, 1 interpolated, 2 empty) and, when `correct=True`, `shift_km`. `correct_scene` has 1-D `lat`/`lon` coordinates (rows north to south). `correct_native` has dimensions `(y, x)` and 2-D `lat`/`lon` coordinates at the pixel centres.

### Example: one L1C scene on a lat/lon grid

```python
import numpy as np
from pygeoparallax import correct_scene
from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.ingest import read_insat_l1c
from pygeoparallax.resample import Grid

bbox = (21.0, 29.0, 88.0, 97.0)  # Northeast India and Bangladesh
ds = read_insat_l1c("3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", channels=("TIR1", "WV"), bbox=bbox)
lat, lon = ds["lat"].values, ds["lon"].values
bt = ds["TIR1"].values
cth = cloud_top_height(bt)  # m; cloudy where BT < 270 K, NaN elsewhere
channels = {"TIR1": bt, "WV": ds["WV"].values}

grid = Grid(21.0, 29.0, 88.0, 97.0, res=0.02)
corrected = correct_scene(lat, lon, channels, cth, grid=grid)
uncorrected = correct_scene(lat, lon, channels, cth, grid=grid, correct=False)

print(corrected.sizes)                       # lat: 400, lon: 450
print(sorted(corrected.data_vars))           # TIR1, WV, count, cth, fill_flag, height, shift_km
print(sorted(uncorrected.data_vars))         # the same without shift_km
cloudy = corrected["cth"] > 0
print(float(corrected["shift_km"].where(cloudy).median()))  # about 5 km
```

The global attributes record `software`, `sub_satellite_longitude`, `parallax_corrected`, `terrain_corrected` and `grid_resolution_deg`. Write the result with `corrected.to_netcdf("scene_corrected.nc")`.

The 0.02° grid here is finer than the 4 km pixel, so many cells are filled from neighbours (`fill_flag` 1). On the default 0.04° grid almost all cells are observed.

### Example: the same scene on its own pixel grid

```python
import numpy as np
from pygeoparallax import correct_native
from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.ingest import read_insat_l1c

ds = read_insat_l1c("3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", channels=("TIR1", "WV"),
                    bbox=(21.0, 29.0, 88.0, 97.0))
lat, lon = ds["lat"].values, ds["lon"].values
channels = {"TIR1": ds["TIR1"].values, "WV": ds["WV"].values}
cth = cloud_top_height(ds["TIR1"].values)

native = correct_native(lat, lon, channels, cth, fill_empty=True)
baseline = correct_native(lat, lon, channels, cth, correct=False)

print(native.sizes, native.attrs["grid"])          # y: 244, x: 250; native (mercator), 244 x 250 pixels
print(np.abs(native["lat"].values - lat).max())    # ~1e-12: same pixel centres as the input
print(np.bincount(native["fill_flag"].values.ravel(), minlength=3))
```

If the positions were moved by a navigation correction, they are no longer a separable grid. Build the grid from the file's own positions and pass it:

```python
from pygeoparallax import correct_native
from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.ingest import read_insat_l1c
from pygeoparallax.resample import NativeGrid

path, bbox = "3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", (21.0, 29.0, 88.0, 97.0)
raw = read_insat_l1c(path, channels=("TIR1",), bbox=bbox)
grid = NativeGrid.from_2d(raw["lat"].values, raw["lon"].values)

nav = read_insat_l1c(path, channels=("TIR1",), bbox=bbox, position_offset_km=(0.5, 1.5))
out = correct_native(nav["lat"].values, nav["lon"].values, {"TIR1": nav["TIR1"].values},
                     cloud_top_height(nav["TIR1"].values), grid=grid)
print(out.sizes)
```

Without `grid=`, `correct_native` raises `ValueError` for shifted positions.

---

## ingest

```python
from pygeoparallax.ingest import (read_insat_l1c, to_standard_scene, read_insat_ctp, read_insat_csbt,
                                  read_era5_profiles, read_srtm, read_gpm_2a,
                                  NO_RAIN, STRATIFORM, CONVECTIVE, OTHER)
```

| Function | Signature |
| :--- | :--- |
| `read_insat_l1c` | `read_insat_l1c(path, channels=("TIR1", "TIR2", "WV", "MIR", "VIS"), bbox=None, position_offset_km=None)` |
| `to_standard_scene` | `to_standard_scene(ds, cth=None)` |
| `read_insat_ctp` | `read_insat_ctp(path)` |
| `read_insat_csbt` | `read_insat_csbt(path, channel="TIR1")` |
| `read_era5_profiles` | `read_era5_profiles(path, time=None)` |
| `read_srtm` | `read_srtm(paths, bbox=None, res=0.01, band_rows=20)` |
| `read_gpm_2a` | `read_gpm_2a(path, swath="FS", bbox=None)` |

`bbox` is always `(lat_min, lat_max, lon_min, lon_max)` in degrees.

### INSAT-3DR L1C

`read_insat_l1c` decodes the 10-bit counts through each file's lookup tables: brightness temperature [K] for `TIR1`, `TIR2`, `WV` and `MIR`, albedo [%] for `VIS`, radiance for `SWIR`. Fill values become NaN. With `bbox`, only that part of the file is decoded, which is much faster than reading the whole sector. The box selects in the file's own (uncorrected) coordinates.

```python
from pygeoparallax.ingest import read_insat_l1c

ds = read_insat_l1c("3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", channels=("TIR1", "VIS"),
                    bbox=(21.0, 29.0, 88.0, 97.0))
print(ds.sizes)                          # y: 244, x: 250
print(ds["TIR1"].attrs)                  # long_name, units 'K', central_wavelength_um 10.785
print(ds.attrs["start_time"], ds.attrs["end_time"], ds.attrs["time"])  # time = scan midpoint
print(ds.attrs["sub_satellite_longitude"])  # 74.0
```

`position_offset_km` applies a navigation correction [km east, km north] to every pixel, as a geodesic move on WGS84. It is either a fixed pair or a callable `f(lat, lon) -> (east, north)`, such as a [`NavigationCorrection`](#navigation):

```python
from pygeoparallax.ingest import read_insat_l1c

ds = read_insat_l1c("3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", channels=("TIR1",),
                    bbox=(21.0, 29.0, 88.0, 97.0), position_offset_km=(-2.0, 1.0))  # 2 km west, 1 km north
print(ds.attrs["position_offset_km"])    # [-2.0, 1.0]
```

The reader does not load ISRO's `Sat_Elevation`/`Sat_Azimuth` fields; they are about 1° off. Use [`geometry.satellite_view_angles`](#geometry) instead.

`to_standard_scene` turns the result into the *standard scene* layout read by `pygeoparallax correct` and `batch` (2-D `lat`, `lon`, `cth` and channel variables):

```python
from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.ingest import read_insat_l1c, to_standard_scene

ds = read_insat_l1c("3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", channels=("TIR1", "WV"),
                    bbox=(21.0, 29.0, 88.0, 97.0))
scene = to_standard_scene(ds, cth=cloud_top_height(ds["TIR1"].values))
print(list(scene.data_vars))             # TIR1, WV, lat, lon, cth
scene.to_netcdf("scene.nc")
```

Without `cth`, the `cth` variable is all NaN and a later correction leaves the scene unchanged.

### INSAT-3DR L2B CTP and clear-sky BT

The L2B CTP file holds cloud-top pressure and temperature on coarse boxes (about 37 km) and clear-sky BT on a separate grid. It contains no height.

```python
import numpy as np
from pygeoparallax.ingest import read_insat_csbt, read_insat_ctp

path = "3RIMG_01AUG2023_1815_L2B_CTP_V01R00.h5"
ctp = read_insat_ctp(path)       # ctp [hPa], ctt [K], emissivity on (row, col); 2-D lat/lon, NaN off the disk
csbt = read_insat_csbt(path)     # clear_sky_bt [K] and clear_fraction for TIR1
print(ctp.sizes, csbt.sizes)     # row: 313, col: 312 and row: 325, col: 325
print(float(np.nanmedian(ctp["ctp"])))
```

`channel` is the suffix of the file's `CSBT_*` variable: `"TIR1"`, `"TIR2"`, `"MIR"` or `"WVR"` (the water-vapour channel is `WVR` in L2B, not `WV`). To use the clear-sky BT as a cloud-mask reference, see [cloudheight](#cloudheight).

### ERA5 profiles

`read_era5_profiles` reads a CDS pressure-level NetCDF with `t` and `z` and returns `temperature` [K] and geometric `height` [m above mean sea level] on `(level, lat, lon)`, surface first. `time` selects the nearest time; by default the first.

```python
from pygeoparallax.ingest import read_era5_profiles

era5 = read_era5_profiles("era5_pl_2024081822.nc", time="2024-08-18T22:00")
print(era5.sizes)                # level: 29, lat: 41, lon: 45
print(era5["level"].values[:3])  # [1000. 975. 950.] hPa
print(era5.attrs["time"])
```

### SRTM

`read_srtm` mosaics SRTM GeoTIFF tiles (a folder, a glob or a list of files) and block-averages them to `res` degrees while reading. It needs `rasterio`. A damaged part of a tile is skipped with a warning.

```python
from pygeoparallax.ingest import read_srtm

dem = read_srtm("01_raw_data/srtm_dem/south_asia_tiles", bbox=(26.0, 29.0, 88.0, 92.0), res=0.01)
print(dem.sizes)                       # lat: 300, lon: 400
print(float(dem["elevation"].max()))   # m above the EGM96 geoid
```

`res` must be a whole multiple of the tile pixel size. For the whole of South Asia, use `scripts/prepare_srtm.py` once and read its NetCDF (see [terrain](#terrain)).

### GPM 2A Ku

`read_gpm_2a` reads a GPM 2A Ku (or DPR) file. With `bbox`, it keeps the scans that have at least one footprint in the box (and all footprints of those scans).

```python
from pygeoparallax.ingest import CONVECTIVE, read_gpm_2a

gpm = read_gpm_2a("2A.GPM.Ku.V10-20251112.20240818-S215337-E232650.059478.V08A.nc",
                  bbox=(21.0, 29.0, 88.0, 97.0))
print(gpm.sizes)                 # scan: 230, ray: 49
print(sorted(gpm.data_vars))     # bright_band_height, precip_rate, precip_type, storm_top_height,
                                 # surface_elevation, z_near_surface, zero_deg_height
print(list(gpm.coords))          # lat, lon, time, top_lat, top_lon
print(int((gpm["precip_type"] == CONVECTIVE).sum()))
```

`top_lat`/`top_lon` are the storm-top positions on the slanted radar beam, computed from the spacecraft position. Use them, not `lat`/`lon`, to place storm tops. `precip_type` codes: `NO_RAIN` 0, `STRATIFORM` 1, `CONVECTIVE` 2, `OTHER` 3, and −1 for missing.

---

## cloudheight

```python
from pygeoparallax.cloudheight import (cloud_mask, cloud_top_height, cloud_top_height_profiles,
                                       height_from_temperature, height_from_pressure,
                                       height_from_temperature_profiles, effective_height,
                                       Profile, TROPICAL)
```

| Function | Signature |
| :--- | :--- |
| `cloud_mask` | `cloud_mask(bt, clear_sky_bt=None, delta=8.0, threshold=270.0)` |
| `cloud_top_height` | `cloud_top_height(bt, clear_sky_bt=None, profile=TROPICAL, **mask_kwargs)` |
| `cloud_top_height_profiles` | `cloud_top_height_profiles(bt, lat, lon, profiles, clear_sky_bt=None, min_pressure=70.0, **mask_kwargs)` |
| `height_from_temperature` | `height_from_temperature(temperature, profile=TROPICAL)` |
| `height_from_pressure` | `height_from_pressure(pressure, profile=TROPICAL)` |
| `height_from_temperature_profiles` | `height_from_temperature_profiles(temperature, profile_t, profile_z, min_pressure_index=None)` |
| `effective_height` | `effective_height(cth, scale=1.0, offset=0.0)` |

`**mask_kwargs` are passed to `cloud_mask` (`delta`, `threshold`).

### Profile lookups

```python
from pygeoparallax.cloudheight import TROPICAL, Profile, height_from_pressure, height_from_temperature

print(height_from_temperature([290.0, 250.3, 220.0, 190.0]))  # [1617. 8000. 12545. 17000.] m
print(height_from_pressure([850.0, 500.0, 200.0]))             # [1531. 5874. 12400.] m (log-pressure)
print(TROPICAL.tropopause_height)                              # 17000.0 m (194.8 K)

# any profile, surface first: height [m], temperature [K], pressure [hPa]
warmer = Profile(height=TROPICAL.height, temperature=TROPICAL.temperature + 2.0,
                 pressure=TROPICAL.pressure)
print(height_from_temperature(250.3, warmer))                  # about 8300 m
```

BT colder than the tropopause gives the tropopause height (17 km for AFGL). BT warmer than the surface gives 0 m.

### Cloud mask and height

```python
import numpy as np
from pygeoparallax.cloudheight import cloud_mask, cloud_top_height

bt = np.array([300.0, 275.0, 265.0, 230.0, 195.0, np.nan])
print(cloud_mask(bt))                         # [F F T T T F]: BT < 270 K
print(cloud_top_height(bt))                   # [nan nan 5791. 11015. 16909. nan] m
print(cloud_mask(bt, clear_sky_bt=np.full(6, 280.0)))  # cloudy if BT < clear-sky BT - 8 K
print(cloud_top_height(bt, threshold=260.0))  # a different fixed threshold
```

With ISRO's clear-sky BT as the reference, sample it to the pixels with [`resample.sample_nearest`](#resample):

```python
import numpy as np
from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.ingest import read_insat_csbt, read_insat_l1c
from pygeoparallax.resample import sample_nearest

ds = read_insat_l1c("3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", channels=("TIR1",),
                    bbox=(21.0, 29.0, 88.0, 97.0))
lat, lon, bt = ds["lat"].values, ds["lon"].values, ds["TIR1"].values

csbt = read_insat_csbt("3RIMG_01AUG2023_1815_L2B_CTP_V01R00.h5")
clear_bt = sample_nearest(csbt["lat"].values, csbt["lon"].values, csbt["clear_sky_bt"].values,
                          lat, lon, max_distance_km=40.0)
cth = cloud_top_height(bt, clear_sky_bt=clear_bt)  # fixed 270 K where clear_bt is NaN
print(float(np.isfinite(cth).mean()))              # cloudy fraction
```

### ERA5 profiles

```python
import numpy as np
from pygeoparallax.cloudheight import cloud_top_height, cloud_top_height_profiles
from pygeoparallax.ingest import read_era5_profiles, read_insat_l1c

ds = read_insat_l1c("3RIMG_18AUG2024_2215_L1C_SGP_V01R00.h5", channels=("TIR1",),
                    bbox=(21.0, 29.0, 88.0, 97.0))
lat, lon, bt = ds["lat"].values, ds["lon"].values, ds["TIR1"].values
profiles = read_era5_profiles("era5_pl_2024081822.nc", time=np.datetime64(ds.attrs["time"]))

cth_era5 = cloud_top_height_profiles(bt, lat, lon, profiles, min_pressure=70.0)
cth_afgl = cloud_top_height(bt)
print(float(np.nanmedian(cth_era5 - cth_afgl)))  # ERA5 minus AFGL [m]
```

The ERA5 box must cover the pixels: outside it, profiles are extrapolated. `scripts/download_era5.py` pads each region box by 1°.

### Effective height

```python
import numpy as np
from pygeoparallax.cloudheight import effective_height

h = np.array([16600.0, 8000.0, 2000.0, np.nan])
print(effective_height(h, offset=3000.0))   # [13600. 5000. 0. nan]
print(effective_height(h, scale=0.7))       # [11620. 5600. 1400. nan]
```

Pass the result as `cth` to `correct_scene` or `correct_native`. See [concepts.md](concepts.md#effective-height) for where the 3 km comes from.

---

## geometry

```python
from pygeoparallax.geometry import (parallax_correct, parallax_correct_terrain, parallax_shift,
                                    satellite_view_angles, solar_angles,
                                    geodetic_to_ecef, ecef_to_geodetic, enu_basis,
                                    GEO_RADIUS, SATELLITE_LONGITUDES)
```

| Function | Signature | Returns |
| :--- | :--- | :--- |
| `parallax_correct` | `parallax_correct(lat, lon, height, sat_lon, h0=0.0, sat_radius=GEO_RADIUS, newton_iterations=1, backend="numba")` | `lat_c, lon_c` [degrees]; NaN where the height is NaN or the point is not visible |
| `parallax_correct_terrain` | `parallax_correct_terrain(lat, lon, cth, sat_lon, surface_height, cloudy=None, iterations=3, **kwargs)` | `lat_c, lon_c, height` |
| `parallax_shift` | `parallax_shift(lat, lon, lat_c, lon_c)` | distance [**m**] and azimuth [degrees from north] from apparent to corrected position |
| `satellite_view_angles` | `satellite_view_angles(lat, lon, sat_lon, h=0.0, sat_radius=GEO_RADIUS)` | `vza, vaa` [degrees]; VAA points towards the satellite |
| `solar_angles` | `solar_angles(time, lat, lon)` | `sza, saa` [degrees] |
| `geodetic_to_ecef` | `geodetic_to_ecef(lat, lon, h=0.0)` | `x, y, z` [m] |
| `ecef_to_geodetic` | `ecef_to_geodetic(x, y, z, iterations=3)` | `lat, lon, h` |
| `enu_basis` | `enu_basis(lat, lon)` | `east, north, up` unit vectors, each of shape `(3, ...)` |

`GEO_RADIUS` is 42 164 160 m. `SATELLITE_LONGITUDES` is `{"INSAT-3DR": 74.0, "INSAT-3DS": 82.0}`.

### Viewing angles and the size of the shift

```python
import numpy as np
from pygeoparallax.geometry import SATELLITE_LONGITUDES, parallax_correct, parallax_shift, satellite_view_angles

sat_lon = SATELLITE_LONGITUDES["INSAT-3DR"]
places = {"Kochi": (9.97, 76.28), "Mumbai": (19.08, 72.88), "Delhi": (28.61, 77.21),
          "Agartala": (23.83, 91.28), "Guwahati": (26.14, 91.74)}
lat = np.array([p[0] for p in places.values()])
lon = np.array([p[1] for p in places.values()])

vza, vaa = satellite_view_angles(lat, lon, sat_lon)
lat_c, lon_c = parallax_correct(lat, lon, np.full(lat.shape, 12000.0), sat_lon)  # a 12 km cloud top
dist_m, azimuth = parallax_shift(lat, lon, lat_c, lon_c)
for name, z, d, az in zip(places, vza, dist_m / 1000.0, azimuth):
    print(f"{name:9s} VZA {z:4.1f} deg  shift {d:3.1f} km towards {az:5.1f} deg")
# Kochi     VZA 12.0 deg  shift 2.6 km towards 193.0 deg
# Mumbai    VZA 22.4 deg  shift 4.9 km towards 176.6 deg
# Delhi     VZA 33.5 deg  shift 7.9 km towards 186.7 deg
# Agartala  VZA 34.0 deg  shift 8.1 km towards 217.6 deg
# Guwahati  VZA 36.4 deg  shift 8.8 km towards 216.0 deg
```

The corrected position moves towards the satellite, along the VAA.

### Backends, reference height and refinement

```python
import numpy as np
from pygeoparallax.geometry import parallax_correct

lat, lon, h = np.array([23.83, 9.97]), np.array([91.28, 76.28]), np.array([12000.0, 16000.0])
a = parallax_correct(lat, lon, h, 74.0)                     # Numba kernel (default)
b = parallax_correct(lat, lon, h, 74.0, backend="numpy")    # vectorised reference
print(np.abs(a[0] - b[0]).max(), np.abs(a[1] - b[1]).max())  # 0.0 0.0

c = parallax_correct(lat, lon, h, 74.0, newton_iterations=0)  # enlarged ellipsoid only (~1 cm error)
d = parallax_correct(lat, lon, h, 74.0, h0=2000.0)            # navigation referenced to 2 km terrain
print(d)
```

Scalars and arrays broadcast against each other. The first Numba call in a process compiles the kernel (cached on disk afterwards).

### Terrain-aware correction

`surface_height` is any callable `f(lat, lon) -> m` that accepts arrays. Here a made-up 3 km plateau north of 27° N:

```python
import numpy as np
from pygeoparallax.geometry import parallax_correct_terrain, parallax_shift

def plateau(lat, lon):
    return np.where(np.asarray(lat) > 27.0, 3000.0, 0.0)

lat = np.array([27.5, 27.5, 26.0])
lon = np.array([88.0, 88.0, 88.0])
cth = np.array([np.nan, 15000.0, np.nan])        # clear ground, a cloud, clear lowland
lat_c, lon_c, height = parallax_correct_terrain(lat, lon, cth, 74.0, plateau)
print(height)                                    # [3000. 15000. 0.]
print(parallax_shift(lat, lon, lat_c, lon_c)[0] / 1000.0)  # [2.15 10.73 0.] km
```

For a real DEM, see [terrain](#terrain).

### Solar angles and coordinate transforms

```python
import numpy as np
from pygeoparallax.geometry import ecef_to_geodetic, enu_basis, geodetic_to_ecef, solar_angles

sza, saa = solar_angles(np.datetime64("2023-08-01T06:15"), np.array([9.97, 23.83]), np.array([76.28, 91.28]))
print(sza.round(1))                              # [13.8 6.6]

x, y, z = geodetic_to_ecef(23.83, 91.28, 12000.0)
print(ecef_to_geodetic(x, y, z))                 # (23.83, 91.28, 12000.0)
east, north, up = enu_basis(23.83, 91.28)
```

---

## resample

```python
from pygeoparallax.resample import (Grid, SOUTH_ASIA_0P04, NativeGrid, resample, bucket_max_height,
                                    idw_fill, sample_nearest, mercator_y, mercator_lat,
                                    OBSERVED, INTERPOLATED, EMPTY)
```

| Name | Signature |
| :--- | :--- |
| `Grid` | `Grid(lat_min, lat_max, lon_min, lon_max, res)`; properties `shape`, `lats`, `lons`; method `cell_index(lat, lon)` |
| `SOUTH_ASIA_0P04` | `Grid(0.0, 40.0, 60.0, 100.0, 0.04)`, 1000 × 1000 cells |
| `resample` | `resample(grid, lat, lon, height, values, fill_radius=1, power=2.0, attrs=None)` |
| `bucket_max_height` | `bucket_max_height(grid, lat, lon, height, values)` |
| `idw_fill` | `idw_fill(field, observed, fill_radius=1, power=2.0)` |
| `NativeGrid` | `NativeGrid.from_2d(lat, lon, tolerance=0.01)`, `NativeGrid.from_coords(lat_1d, lon_1d, tolerance=0.01)`; properties `lats`, `lons`; methods `fractional_index(lat, lon)`, `index_space()` |
| `mercator_y`, `mercator_lat` | `mercator_y(lat)`, `mercator_lat(y, iterations=6)` |
| `sample_nearest` | `sample_nearest(src_lat, src_lon, values, dst_lat, dst_lon, max_distance_km=50.0)` |
| `OBSERVED`, `INTERPOLATED`, `EMPTY` | `fill_flag` values 0, 1, 2 |

### Grid

Bounds are the outer cell edges. Rows run north to south, columns west to east.

```python
from pygeoparallax.resample import SOUTH_ASIA_0P04, Grid

grid = Grid(lat_min=20.0, lat_max=20.3, lon_min=80.0, lon_max=80.3, res=0.1)
print(grid.shape, grid.lats, grid.lons)   # (3, 3) [20.25 20.15 20.05] [80.05 80.15 80.25]
row, col, valid = grid.cell_index([20.25, 19.0], [80.05, 80.05])
print(row, col, valid)                    # [0 0] [0 0] [ True False]
print(SOUTH_ASIA_0P04.shape)              # (1000, 1000)
```

### Occlusion-aware resampling

`resample` is what `correct_scene` uses internally. The highest pixel in a cell wins; small gaps are filled; `fill_flag` says which.

```python
import numpy as np
from pygeoparallax.resample import Grid, resample

grid = Grid(20.0, 20.3, 80.0, 80.3, res=0.1)
lat = np.array([20.25, 20.26, 20.05])
lon = np.array([80.05, 80.06, 80.25])
height = np.array([2000.0, 12000.0, np.nan])        # NaN height counts as lowest
ds = resample(grid, lat, lon, height, {"TIR1": np.array([280.0, 220.0, 300.0])}, fill_radius=1)
print(ds["TIR1"].values[0, 0])   # 220.0: the 12 km cloud hides the 2 km one
print(ds["count"].values)        # [[2 0 0] [0 0 0] [0 0 1]]
print(ds["fill_flag"].values)    # [[0 1 2] [1 1 1] [2 1 0]]
```

The two steps are also available on their own:

```python
import numpy as np
from pygeoparallax.resample import Grid, bucket_max_height, idw_fill

grid = Grid(20.0, 20.3, 80.0, 80.3, res=0.1)
out = bucket_max_height(grid, [20.25, 20.05], [80.05, 80.25], [12000.0, 0.0],
                        {"TIR1": [220.0, 300.0]})
print(sorted(out))                                   # ['TIR1', 'count', 'height']
filled, was_filled = idw_fill(out["TIR1"], out["count"] > 0, fill_radius=1)
print(int(was_filled.sum()))                         # 5 cells filled
```

### Native grid

```python
import numpy as np
from pygeoparallax.ingest import read_insat_l1c
from pygeoparallax.resample import NativeGrid, mercator_lat, mercator_y

ds = read_insat_l1c("3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", channels=("TIR1",),
                    bbox=(21.0, 29.0, 88.0, 97.0))
grid = NativeGrid.from_2d(ds["lat"].values, ds["lon"].values)
print(grid.kind, grid.shape)                          # mercator (244, 250)
print(np.allclose(grid.lats, ds["lat"].values[:, 0]))  # True
row, col = grid.fractional_index(25.0, 92.0)          # pixel centres are whole numbers
print(mercator_lat(mercator_y(23.8)))                 # 23.8
```

`NativeGrid.from_coords(lat_1d, lon_1d)` does the same from the row latitudes and column longitudes. `index_space()` returns `(to_index, grid)`, which `correct_native` uses to run the bucket resampler with one cell per pixel.

### Nearest-neighbour sampling

`sample_nearest` brings a coarse product onto other points (for example L2B clear-sky BT onto L1C pixels). Destinations farther than `max_distance_km` from any source get NaN.

```python
import numpy as np
from pygeoparallax.resample import sample_nearest

src_lat, src_lon = np.meshgrid(np.arange(20, 30, 0.5), np.arange(85, 95, 0.5), indexing="ij")
field = src_lat * 10.0
print(sample_nearest(src_lat, src_lon, field, np.array([25.1, 40.0]), np.array([90.1, 90.0]),
                     max_distance_km=50.0))   # [250. nan]
```

---

## terrain

```python
from pygeoparallax.terrain import surface_height_from_dataset
```

`surface_height_from_dataset(dem, var="elevation")` builds the `surface_height` callable from a DEM on a regular lat/lon grid: a path or an `xarray.Dataset`. The lookup is bilinear; points outside the DEM and NaN voids are 0 m.

```python
import numpy as np
from pygeoparallax import correct_scene
from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.ingest import read_insat_l1c, read_srtm
from pygeoparallax.resample import Grid
from pygeoparallax.terrain import surface_height_from_dataset

# from the prepared South Asia grid (scripts/prepare_srtm.py) ...
ground = surface_height_from_dataset("02_standardized_grid/srtm_0p01deg.nc")
print(ground(np.array([27.99, 20.0]), np.array([86.93, 78.0])))   # m

# ... or straight from tiles
bbox = (26.0, 30.0, 85.0, 92.0)
ground = surface_height_from_dataset(read_srtm("01_raw_data/srtm_dem/south_asia_tiles", bbox=bbox))

ds = read_insat_l1c("3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", channels=("TIR1",), bbox=bbox)
out = correct_scene(ds["lat"].values, ds["lon"].values, {"TIR1": ds["TIR1"].values},
                    cloud_top_height(ds["TIR1"].values), grid=Grid(*bbox, res=0.04), surface_height=ground)
clear = out["cth"].isnull() & (out["fill_flag"] == 0)
print(out.attrs["terrain_corrected"], float(out["shift_km"].where(clear).median()))  # clear ground moves too
```

---

## navigation

```python
from pygeoparallax.navigation import (load_land, land_fraction_interpolator, measure_scan, measure_window,
                                      NavigationCorrection, WINDOWS, EAST_ONLY)
```

| Name | Signature |
| :--- | :--- |
| `load_land` | `load_land(path)`: union of the land polygons in a GeoJSON file |
| `land_fraction_interpolator` | `land_fraction_interpolator(land, bbox, pixel_km=4.0, fine=0.005, pad=0.5)` |
| `measure_scan` | `measure_scan(path, land, windows=None, interps=None, **kwargs)`: one dict per usable window |
| `measure_window` | `measure_window(lat, lon, image, interp, sign=1.0, clear=None, max_km=30.0, coarse_km=2.0, fine_km=0.5, min_pixels=300, min_side=50, east_only=False)` |
| `NavigationCorrection` | `NavigationCorrection(lat, lon, east_km, north_km, power=2.0, meta={})`; `from_matches(matches, min_r=0.6, power=2.0, max_offset_km=25.0, agree_km=5.0, single_min_r=0.75)`; `from_json(path)`; `to_json(path)`; call as `corr(lat, lon) -> (east_km, north_km)` |
| `WINDOWS`, `EAST_ONLY` | the 13 coastal windows; the two that measure only east–west |

Offsets are the correction to **add** to INSAT positions [km east, km north].

### Measure and apply a correction

Measure all daytime scans of one day together, so that the two-scan agreement rule can work. Each scan takes a few seconds per window.

```python
import glob
import numpy as np
from pygeoparallax.ingest import read_insat_l1c
from pygeoparallax.navigation import WINDOWS, NavigationCorrection, land_fraction_interpolator, load_land, measure_scan

land = load_land("01_raw_data/natural_earth/ne_10m_land.geojson")
scans = sorted(glob.glob("3RIMG_07SEP2023_0[4-6]15_L1C_SGP_V01R00.h5"))

windows = {k: WINDOWS[k] for k in ("kutch", "saurashtra", "konkan", "goa_karnataka")}  # or all of WINDOWS
interps = {k: land_fraction_interpolator(land, box) for k, box in windows.items()}      # reuse across scans
matches = []
for path in scans:
    for m in measure_scan(path, land, windows=windows, interps=interps):
        print(m["scan"], m["window"], m["channel"], m["east_km"], m["north_km"],
              round(m["r_zero"], 2), round(m["r_best"], 2), m["on_edge"])
        matches.append(m)

try:
    corr = NavigationCorrection.from_matches(matches)
    print(corr.meta["windows"], corr.east_km, corr.north_km)
    corr.to_json("nav_07SEP2023.json")
except ValueError as exc:      # no window passed the acceptance rules (common in monsoon cloud)
    print("no correction:", exc)
```

Each match has `east_km`, `north_km`, `r_best`, `r_zero` (correlation without a shift), `on_edge`, pixel counts (`clear_pixels`, `land`, `sea`), `window`, `lat`/`lon` (window centre), `channel` (`VIS` by day, `TIR1` by night), `sza`, `scan` and `time`.

Check the accepted windows and their values before you apply a correction. In monsoon scenes a single cloudy window can pass the rules with an implausible offset.

Apply it while reading, or to any positions:

```python
import numpy as np
from pygeoparallax.ingest import read_insat_l1c
from pygeoparallax.ingest.insat import shift_positions
from pygeoparallax.navigation import NavigationCorrection

# a correction from fixed values, e.g. a seasonal median
corr = NavigationCorrection(lat=[20.0], lon=[75.0], east_km=[1.8], north_km=[4.8])
east, north = corr(np.array([19.08, 23.83]), np.array([72.88, 91.28]))
print(east, north)                               # one point: the same everywhere

ds = read_insat_l1c("3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", channels=("TIR1",),
                    bbox=(21.0, 29.0, 88.0, 97.0), position_offset_km=corr)
print(ds.attrs["position_offset_km"], ds.attrs["navigation_correction"])  # mean shift, 'position-dependent'

lat2, lon2 = shift_positions(np.array([23.83]), np.array([91.28]), east[1], north[1])  # the same move by hand
```

`NavigationCorrection.from_json("nav_07SEP2023.json")` reloads a saved correction, including one written by `pygeoparallax navigation` (see [cli.md](cli.md)).

### One window by hand

```python
import glob
from pygeoparallax.ingest import read_insat_l1c
from pygeoparallax.navigation import WINDOWS, land_fraction_interpolator, load_land, measure_window

land = load_land("01_raw_data/natural_earth/ne_10m_land.geojson")
box = WINDOWS["saurashtra"]
ds = read_insat_l1c(sorted(glob.glob("3RIMG_07SEP2023_0[4-6]15_L1C_SGP_V01R00.h5"))[-1],
                    channels=("TIR1", "VIS"), bbox=box)
vis, tir = ds["VIS"].values, ds["TIR1"].values
result = measure_window(ds["lat"].values, ds["lon"].values, vis, land_fraction_interpolator(land, box),
                        sign=1.0, clear=(vis < 30.0) & (tir > 285.0))
print(result)   # None if too few clear land or sea pixels
```

---

## validation

```python
from pygeoparallax.validation import (compare, iou, pearson, mutual_information, best_displacement,
                                      subcell_displacement, points_to_grid, range_mask, nearest_time,
                                      REGIONS, region_mask, regional_stats, monte_carlo_shift, bias_sweep)
```

| Name | Signature |
| :--- | :--- |
| `compare` | `compare(sat, radar, sat_threshold, radar_threshold, sat_below=True, valid=None, max_lag=5, bins=32)` |
| `iou` | `iou(a, b, valid=None)` |
| `pearson` | `pearson(a, b, valid=None)` |
| `mutual_information` | `mutual_information(a, b, bins=32, valid=None, normalized=False)` [bits] |
| `best_displacement` | `best_displacement(a, b, max_lag=5, valid=None)` -> `dy, dx, r` (whole cells; positive = move `a` south / east) |
| `subcell_displacement` | `subcell_displacement(a, b, max_lag=5, valid=None)` -> `dy, dx, r` (fractional) |
| `points_to_grid` | `points_to_grid(grid, lat, lon, values, how="mean")` (`"mean"` or `"max"`) |
| `range_mask` | `range_mask(grid, lat0, lon0, range_km)` |
| `nearest_time` | `nearest_time(times, target, max_dt="15min")` -> index, or −1 |
| `REGIONS`, `region_mask`, `regional_stats` | `region_mask(lat, lon, box)`, `regional_stats(ds, variable, regions=None, mask=None)` |
| `monte_carlo_shift` | `monte_carlo_shift(lat, lon, cth, sat_lon, sigma=1000.0, n=100, seed=0, **kwargs)` |
| `bias_sweep` | `bias_sweep(lat, lon, cth, sat_lon, offsets=(-2000.0, -1000.0, 1000.0, 2000.0), **kwargs)` |

### INSAT against GPM

```python
import numpy as np
from pygeoparallax import correct_scene
from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.ingest import read_gpm_2a, read_insat_l1c
from pygeoparallax.resample import Grid
from pygeoparallax.validation import compare, nearest_time, points_to_grid, range_mask

bbox = (21.0, 29.0, 88.0, 97.0)
grid = Grid(*bbox, res=0.02)
ds = read_insat_l1c("3RIMG_18AUG2024_2215_L1C_SGP_V01R00.h5", channels=("TIR1",), bbox=bbox)
bt = ds["TIR1"].values
cth = cloud_top_height(bt)
raw = correct_scene(ds["lat"].values, ds["lon"].values, {"TIR1": bt}, cth, grid=grid, correct=False)
cor = correct_scene(ds["lat"].values, ds["lon"].values, {"TIR1": bt}, cth, grid=grid)

gpm = read_gpm_2a("2A.GPM.Ku.V10-20251112.20240818-S215337-E232650.059478.V08A.nc", bbox=bbox)
print(nearest_time(gpm["time"].values, np.datetime64(ds.attrs["time"]), max_dt="30min"))  # -1 if too far apart

z = points_to_grid(grid, gpm["lat"].values, gpm["lon"].values, gpm["z_near_surface"].values)
top = points_to_grid(grid, gpm["top_lat"].values, gpm["top_lon"].values,
                     gpm["storm_top_height"].values, how="max")       # storm tops on the beam
in_swath = np.isfinite(points_to_grid(grid, gpm["lat"].values, gpm["lon"].values, np.ones(gpm["lat"].shape)))
valid = in_swath & range_mask(grid, 23.83, 91.28, 250.0)             # within 250 km of Agartala

for name, sat in (("raw", raw), ("corrected", cor)):
    print(name, compare(sat["TIR1"].values, z, sat_threshold=235.0, radar_threshold=25.0,
                        valid=valid, max_lag=10))
```

`compare` returns `iou`, `pearson`, `mutual_info` (normalised), `lag_dy`, `lag_dx` (whole cells), `lag_dy_sub`, `lag_dx_sub` (sub-cell) and `lag_r`. With `sat_below=True` (the default), the correlation and the lag use the negated satellite field, so a good match is a positive correlation. The lag is the shift of the satellite field that best matches the radar, in cells (positive = south and east).

The single metrics take any two fields on the same grid:

```python
import numpy as np
from pygeoparallax.validation import best_displacement, iou, mutual_information, pearson, subcell_displacement

rng = np.random.default_rng(0)
b = rng.normal(size=(60, 60))
a = np.roll(b, shift=(2, -1), axis=(0, 1))            # a is b moved 2 rows south, 1 column west
print(best_displacement(a, b, max_lag=3))             # (-2, 1, 1.0): move a 2 north, 1 east
print(subcell_displacement(a, b, max_lag=3)[:2])
print(iou(a > 1, b > 1), pearson(a, b), mutual_information(a, b, normalized=True))
```

### Regional statistics

```python
import numpy as np
from pygeoparallax import correct_scene
from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.ingest import read_insat_l1c
from pygeoparallax.validation import REGIONS, region_mask, regional_stats

ds = read_insat_l1c("3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", channels=("TIR1",), bbox=(5.0, 37.0, 68.0, 98.0))
out = correct_scene(ds["lat"].values, ds["lon"].values, {"TIR1": ds["TIR1"].values},
                    cloud_top_height(ds["TIR1"].values))
print(REGIONS)        # western_ghats, himalayas, northeast, central_india boxes
print(regional_stats(out, "shift_km", mask=out["fill_flag"].values == 0))  # n, mean, std, median, p90, max
print(int(region_mask(out["lat"].values, out["lon"].values, REGIONS["northeast"]).sum()))
```

The `REGIONS` boxes are simple rectangles, not the validation regions of the paper.

### Sensitivity to cloud-top height errors

```python
import numpy as np
from pygeoparallax.validation import bias_sweep, monte_carlo_shift

lat, lon = np.array([23.83, 9.97]), np.array([91.28, 76.28])   # Agartala, Kochi
cth = np.array([12000.0, 12000.0])
mc = monte_carlo_shift(lat, lon, cth, 74.0, sigma=1000.0, n=100)
print(mc["shift_km"], mc["position_rmse_km"], mc["position_p95_km"])  # [8.07 2.55] [0.65 0.2] [1.28 0.35]
print(bias_sweep(lat, lon, cth, 74.0))  # mean, p95 and max position error [km] per offset [m]
```

---

## demo

```python
from pygeoparallax.demo import run_demo, simulate_scene, temperature_at, STORMS
```

| Name | Signature |
| :--- | :--- |
| `run_demo` | `run_demo(out_dir="pygeoparallax_demo", plot=True, verbose=True)` -> dict with `storms`, `passed`, `out_dir`, `figure` |
| `simulate_scene` | `simulate_scene(seed=0)` -> `lat, lon, bt, truth` |
| `temperature_at` | `temperature_at(height)`: AFGL tropical temperature [K] at a tropospheric height [m] |
| `STORMS` | the three synthetic storms: `(name, lat, lon, height [m], radius [km])` |

`run_demo` builds a synthetic INSAT-3DR-like scene over Northeast India with three flat-topped storms (16, 12 and 8 km) at known positions. It traces each pixel's line of sight to simulate what the satellite sees, then corrects the scene the normal way (height from BT, `correct_native`) and checks that every storm returns to within one pixel (4 km) of its true position. It writes `demo_uncorrected.nc`, `demo_corrected.nc` and, with `plot=True` (needs matplotlib), `demo.png`.

```python
from pygeoparallax.demo import run_demo

result = run_demo("pygeoparallax_demo", plot=False)
# storm                                 top   uncorrected   corrected
# deep storm near Agartala             16 km       10.9 km      1.2 km
# storm over Bangladesh                12 km        8.4 km      1.2 km
# shallow storm over West Bengal        8 km        5.0 km      1.1 km
print(result["passed"])                  # True
```

The synthetic scene is also a convenient test input:

```python
import numpy as np
from pygeoparallax import correct_native
from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.demo import simulate_scene

lat, lon, bt, truth = simulate_scene(seed=0)     # truth: which storm (1, 2, 3) lies under each pixel, 0 none
out = correct_native(lat, lon, {"TIR1": bt}, cloud_top_height(bt), fill_empty=True)
print(lat.shape, float(np.nanmax(out["shift_km"])))   # (91, 112), about 11 km
```

The same check runs from the command line as `pygeoparallax demo` (see [quickstart.md](quickstart.md)).

---

## Recipes

### Corrected and uncorrected pairs for a model

```python
from pygeoparallax import correct_native
from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.ingest import read_insat_l1c

ds = read_insat_l1c("3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5", channels=("TIR1", "TIR2", "WV", "MIR"),
                    bbox=(5.0, 37.0, 68.0, 98.0))
lat, lon = ds["lat"].values, ds["lon"].values
channels = {c: ds[c].values for c in ("TIR1", "TIR2", "WV", "MIR")}
cth = cloud_top_height(ds["TIR1"].values)
model_a = correct_native(lat, lon, channels, cth, correct=False)              # uncorrected
model_b = correct_native(lat, lon, channels, cth, fill_empty=True)            # corrected, complete image
print(model_a["TIR1"].shape == model_b["TIR1"].shape == ds["TIR1"].shape)    # True
```

See [unet.md](unet.md) for the full experiment.

### Navigation, ERA5 heights, terrain and an effective height together

```python
import numpy as np
from pygeoparallax import correct_scene
from pygeoparallax.cloudheight import cloud_top_height_profiles, effective_height
from pygeoparallax.ingest import read_era5_profiles, read_insat_l1c
from pygeoparallax.navigation import NavigationCorrection
from pygeoparallax.resample import Grid
from pygeoparallax.terrain import surface_height_from_dataset

bbox = (21.0, 29.0, 88.0, 97.0)
nav = NavigationCorrection(lat=[20.0], lon=[80.0], east_km=[0.5], north_km=[1.5])  # pooled monsoon value
ds = read_insat_l1c("3RIMG_18AUG2024_2215_L1C_SGP_V01R00.h5", channels=("TIR1", "WV"), bbox=bbox,
                    position_offset_km=nav)                                  # 1. navigation first
lat, lon, bt = ds["lat"].values, ds["lon"].values, ds["TIR1"].values
profiles = read_era5_profiles("era5_pl_2024081822.nc", time=np.datetime64(ds.attrs["time"]))
cth = cloud_top_height_profiles(bt, lat, lon, profiles)                      # 2. height from ERA5
h = effective_height(cth, offset=3000.0)                                     # 3. lower, for rain work
ground = surface_height_from_dataset("02_standardized_grid/srtm_0p01deg.nc")
out = correct_scene(lat, lon, {"TIR1": bt, "WV": ds["WV"].values}, h,
                    grid=Grid(*bbox, res=0.04), surface_height=ground)       # 4. terrain-aware correction
out.attrs["effective_height"] = "cth - 3 km"
out.to_netcdf("northeast_20240818_2215_corrected.nc")
```
