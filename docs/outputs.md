# Output files

Every correction writes one NetCDF file (or returns one `xarray.Dataset` in Python). There are two layouts:

| Layout | Made by | Dimensions | Coordinates |
| :--- | :--- | :--- | :--- |
| Regular grid | `pygeoparallax l1c` (default), `correct`, `batch`; `correct_scene()` in Python | `(lat, lon)` | 1-D `lat`, `lon`: cell centres |
| Native grid | `pygeoparallax l1c --native`, `pygeoparallax demo`; `correct_native()` in Python | `(y, x)` | 2-D `lat`, `lon`: pixel centres of the input file |

Both layouts hold the same variables and nearly the same attributes. Everything on this page was checked against files made with version 0.4.1 from `3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5` and from the demo.

## Example

```bash
pygeoparallax l1c 3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5 -o corrected --bbox 20 30 85 97 --grid 20 30 85 97 0.04
```

```python
import xarray as xr

ds = xr.open_dataset("corrected/3RIMG_01AUG2023_1815_L1C_SGP_V01R00_corrected.nc")
print(ds)
```

```
<xarray.Dataset> Size: 5MB
Dimensions:    (lat: 250, lon: 300)
Coordinates:
  * lat        (lat) float64 2kB 29.98 29.94 29.9 29.86 ... 20.1 20.06 20.02
  * lon        (lon) float64 2kB 85.02 85.06 85.1 85.14 ... 96.9 96.94 96.98
Data variables:
    TIR1       (lat, lon) float64 600kB ...
    TIR2       (lat, lon) float64 600kB ...
    WV         (lat, lon) float64 600kB ...
    MIR        (lat, lon) float64 600kB ...
    cth        (lat, lon) float64 600kB ...
    shift_km   (lat, lon) float64 600kB ...
    height     (lat, lon) float64 600kB ...
    count      (lat, lon) int32 300kB ...
    fill_flag  (lat, lon) uint8 75kB ...
Attributes: (12/14)
    title:                    PyGeoParallax-IN gridded scene
    software:                 pygeoparallax 0.4.1
    sub_satellite_longitude:  74.0
    parallax_corrected:       1
    terrain_corrected:        0
    grid_resolution_deg:      0.04
    ...                       ...
    product:                  3RIMG_01AUG2023_1815_SGP
    start_time:               2023-08-01T18:15:26
    end_time:                 2023-08-01T18:42:20
    time:                     2023-08-01T18:28:53
    source_file:              3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5
    cloud_top_height:         TIR1 BT < 270 K, AFGL tropical atmosphere
```

The same file from `--native` has dimensions `(y: 306, x: 334)` and 2-D `lat`/`lon` coordinates.

## Dimensions and coordinates

### Regular grid

- Dimensions `lat` and `lon`. Rows run north to south, columns west to east.
- `lat` [degrees_north] and `lon` [degrees_east] are the cell centres. With `--grid 20 30 85 97 0.04`, `lat` runs from 29.98 to 20.02 and `lon` from 85.02 to 96.98.
- The default grid is 0–40° N, 60–100° E at 0.04° (1000 × 1000 cells). Cells outside the data (outside a `--bbox` region, or off the Earth disc) are empty (`fill_flag` 2).

### Native grid

- Dimensions `y` (rows, north to south) and `x` (columns, west to east), with the shape of the input region.
- `lat` and `lon` are 2-D coordinates holding the pixel centres of the input file's grid, before any navigation correction. They do not change with the correction: corrected values are placed onto these fixed pixels.
- The L1C grid is regular in WGS84 Mercator northing and in longitude (about 4 km at the equator). The global attribute `grid` records this, for example `native (mercator), 306 x 334 pixels`.
- Corrected and uncorrected native files from the same input have identical `lat`/`lon`.

## Data variables

| Variable | Type | Units | Present | Meaning |
| :--- | :--- | :--- | :--- | :--- |
| channels (`TIR1`, `TIR2`, `WV`, `MIR`, `VIS`, `SWIR`, or any names you pass) | float64 | see below | always | The channel values at the corrected positions. |
| `cth` | float64 | m | always | Height used for the correction, above the WGS84 ellipsoid. NaN for clear sky. |
| `shift_km` | float64 | km | corrected output only | How far the pixel in this cell was moved. |
| `height` | float64 | m | always | Height that decided which pixel won the cell. |
| `count` | int32 | pixels | always | Number of corrected pixels that landed in the cell (`long_name: number of pixels that landed in the cell`). |
| `fill_flag` | uint8 | – | always | 0 observed, 1 interpolated, 2 empty. |

The CLI writes all data variables with zlib compression (level 4). NaN is the missing value for the float variables. `count` and `fill_flag` have no missing values.

### Channels

From `pygeoparallax l1c` the channels keep the attributes of the L1C reader:

| Channel | Central wavelength | Quantity | `units` |
| :--- | :--- | :--- | :--- |
| `TIR1` | 10.8 µm | brightness temperature | K |
| `TIR2` | 12.0 µm | brightness temperature | K |
| `WV` | 6.9 µm | brightness temperature | K |
| `MIR` | 3.9 µm | brightness temperature | K |
| `VIS` | 0.65 µm | albedo | % |
| `SWIR` | 1.6 µm | radiance | mW.cm-2.sr-1.micron-1 |

Each channel has the attributes `long_name` (for example `TIR1 brightness temperature`), `units` and `central_wavelength_um` (the exact value from the file, for example 10.785 for TIR1).

From `correct`, `batch`, `correct_scene()` and `correct_native()` the channels have no attributes; units are those of your input.

Every channel is moved with its pixel, using the cloud-top height derived from TIR1. This is right for channels that see the cloud top (TIR1, TIR2, MIR, and VIS/SWIR in daytime). See [troubleshooting.md](troubleshooting.md#water-vapour-in-clear-sky-is-not-corrected) for WV in clear sky.

### `cth`

Height used to correct the pixel [m above the WGS84 ellipsoid]. Attributes: `units: m`, `long_name: cloud-top height` (or `effective height used for the correction (...)` when an effective height was used).

- With `l1c`, it comes from the TIR1 brightness temperature: pixels colder than the cloud threshold (270 K by default) are cloudy, and their height is looked up in the AFGL tropical atmosphere or ERA5 profiles. The global attribute `cloud_top_height` records which. Very cold tops are capped at the tropopause (17 km in the AFGL profile).
- NaN means clear sky. Clear-sky pixels are not moved by the cloud correction.
- With `--height-scale` or `--height-offset`, `cth` holds the **effective** height that was used, not the original cloud-top height. For example, with `--height-offset 3` the largest value is 14000 m instead of 17000 m. Its `long_name` says so, and the global attribute `effective_height` gives the formula.
- On the regular grid, `cth` is the value of the winning (highest) pixel in the cell.

### `shift_km`

Ground distance [km] between the apparent (as navigated) and corrected position of the winning pixel. Attributes: `units: km`, `long_name: parallax displacement of the pixel`. Only in corrected output; `--no-correction` output has no `shift_km`.

- Clear sky without a DEM: 0 km (the pixel is on the ellipsoid and does not move).
- Clear sky with `--dem`: the terrain parallax, usually under 1 km but several kilometres on high mountains.
- Cloudy: typically 3–10 km over India, up to about 15 km for deep storms in the northeast. In the example scene the median for cloudy cells is 6.6 km and the maximum 14.7 km.
- It does not include the navigation correction.

### `height`

The height [m] used to decide which pixel wins a cell when several land in it. Attributes: `units: m`, `long_name: height used for occlusion (highest pixel in cell)`.

- Cloudy: the same as `cth`. With `--dem`, clouds are clamped so they are never below the ground under them.
- Clear sky: 0 m without a DEM; the terrain height at the corrected position with `--dem`.

The highest pixel wins because a high cloud hides whatever is below it from the satellite.

### `count`

Number of corrected pixels that landed in the cell. No attributes.

- 0 in interpolated and empty cells.
- 1 in most observed cells.
- More than 1 where pixels pile up, typically on the side of a tall cloud that faces the satellite. Only the highest of them is kept.

On a 0.04° grid, `count` is often 2 or more even in clear sky. Over India the L1C pixels are slightly smaller in degrees than 0.04° cells (about 0.036° in longitude, less in latitude), so some cells receive two or more pixels. In the example region, clear observed cells hold 1 to 4 pixels.

### `fill_flag`

Which of three cases each cell is. Attributes: `flag_values: [0, 1, 2]`, `flag_meanings: observed interpolated empty`.

| Value | Name | What happened | Values in the cell |
| :--- | :--- | :--- | :--- |
| 0 | observed | At least one corrected pixel landed in the cell. | From the highest of those pixels. Real measurements. |
| 1 | interpolated | No pixel landed, but an observed cell lies within `--fill-radius` cells (default 1). | Inverse-distance weighted from the observed neighbours. If most of the neighbour weight is clear sky, `cth` stays NaN so a clear gap stays clear. |
| 2 | empty | No pixel landed and no observed cell is near. | NaN, except `count` (0). With `--native --fill-empty`, the channels are filled with the nearest corrected value; `cth`, `shift_km` and `height` stay NaN. |

Physical meaning:

- **Observed (0).** The satellite saw this place, after the cloud was moved to where it really is.
- **Interpolated (1).** A sampling gap. Moving pixels by different distances spreads some of them apart, leaving one-cell holes, mostly along the edges of moved clouds and where cloud height changes sharply. The interpolated value is a good estimate but not a measurement.
- **Empty (2).** Usually ground hidden behind a tall cloud. Once the cloud is moved back towards the satellite, the place it used to cover in the image is ground the satellite never saw, because the cloud blocked the view. Empty cells also appear outside the data: off the edge of a `--bbox` region, outside the L1C sector, or where the file has fill values.

Typical fractions on a 0.04° grid (148 monsoon scenes, [benchmark](../00_Documentation/benchmark.md)): 98.7 % observed, 1.3 % interpolated, 0.007 % empty inside the data. In the example scene (20–30° N, 85–97° E, 86 % cloudy), the 0.04° grid has 97.2 % observed, 2.5 % interpolated and 0.3 % empty cells. The native grid, whose pixels are smaller than 0.04° cells, has 93.6 % observed, 5.9 % interpolated and 0.5 % empty pixels; all its empty pixels lie within 5 pixels of the box edges.

The uncorrected output (`--no-correction`) also has `fill_flag`. There it only marks the sampling gaps of regridding.

## Global attributes

| Attribute | Example | Written by | Meaning |
| :--- | :--- | :--- | :--- |
| `title` | `PyGeoParallax-IN gridded scene` | all | |
| `software` | `pygeoparallax 0.4.1` | all | Package version that made the file. |
| `sub_satellite_longitude` | `74.0` | all | Satellite longitude used [degrees east]. From the L1C file, the standard scene or `--sat-lon`. |
| `parallax_corrected` | `1` | all | 1 corrected, 0 uncorrected baseline. |
| `terrain_corrected` | `0` | all | 1 if the correction used a DEM (`--dem`), else 0. Always 0 in uncorrected output. |
| `grid_resolution_deg` | `0.04` | regular grid | Cell size [degrees]. |
| `grid` | `native (mercator), 306 x 334 pixels` | native grid | Grid type and shape. |
| `satellite` | `INSAT-3DR` | `l1c`; `correct`/`batch` if in the input | |
| `sensor` | `IMAGER` | `l1c` | |
| `product` | `3RIMG_01AUG2023_1815_SGP` | `l1c` | Product ID from the L1C file. |
| `start_time`, `end_time` | `2023-08-01T18:15:26` | `l1c` (`start_time` also from `correct`/`batch` if in the input) | Scan start and end, UTC. |
| `time` | `2023-08-01T18:28:53` | `l1c`; `correct`/`batch` if in the input | Scan midpoint, UTC. Stored as a string. |
| `source_file` | `3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5` | CLI | Input file name. |
| `cloud_top_height` | `TIR1 BT < 270 K, AFGL tropical atmosphere` | `l1c` | How `cth` was derived (`ERA5 profile` with `--era5`). |
| `effective_height` | `1 * cloud-top height - 3 km` | CLI, only with `--height-scale`/`--height-offset` | Formula used to turn the cloud-top height into the correction height. |
| `empty_cells_filled` | `nearest` | `--native --fill-empty` (`correct_native(..., fill_empty=True)`) | Channels in empty cells were filled with the nearest corrected value; the cells keep `fill_flag` 2. |
| `navigation_correction` | `nav_15DEC2022.json` | CLI, only with `--nav-correction` | File name of the navigation correction applied. |

Notes:

- Python functions (`correct_scene`, `correct_native`) only write the first six or seven attributes (`title` to `grid_resolution_deg` or `grid`). Add your own with `ds.attrs[...] = ...`.
- The demo's `demo_corrected.nc` has the native-grid attributes and nothing from an L1C file.
- `time` is a string. Convert it with `numpy.datetime64(ds.attrs["time"])`.

## Using fill_flag to mask cells

For statistics, decide which cells to trust:

- `fill_flag == 0`: only real observations. Use this for validation, error statistics and anything sensitive to small displacements.
- `fill_flag <= 1`: observations and one-cell interpolations. Good for maps and for models that need a complete field.
- Exclude `fill_flag == 2` always, unless you filled it on purpose with `--fill-empty`.

```python
import xarray as xr

ds = xr.open_dataset("corrected/3RIMG_01AUG2023_1815_L1C_SGP_V01R00_corrected.nc")

observed = ds["fill_flag"] == 0          # a pixel landed in the cell
usable = ds["fill_flag"] <= 1            # observed or interpolated from neighbours
tir1_obs = ds["TIR1"].where(observed)    # NaN everywhere else

for k, name in enumerate(["observed", "interpolated", "empty"]):
    print(f"{name:13s} {float((ds['fill_flag'] == k).mean()):6.2%}")

cold = (ds["TIR1"] < 220) & observed
print(f"cold cloud tops (observed cells only): {int(cold.sum())} cells")
print(f"mean TIR1, observed cells: {float(tir1_obs.mean()):.1f} K")
```

```
observed      97.18%
interpolated   2.53%
empty          0.30%
cold cloud tops (observed cells only): 19871 cells
mean TIR1, observed cells: 239.3 K
```

To compare corrected and uncorrected scenes, use only cells observed in both:

```python
import xarray as xr

cor = xr.open_dataset("corrected/3RIMG_01AUG2023_1815_L1C_SGP_V01R00_corrected.nc")
raw = xr.open_dataset("uncorrected/3RIMG_01AUG2023_1815_L1C_SGP_V01R00_uncorrected.nc")

both = (cor["fill_flag"] == 0) & (raw["fill_flag"] == 0)
diff = (cor["TIR1"] - raw["TIR1"]).where(both)
changed = abs(diff) > 0.01
print(f"cells observed in both: {float(both.mean()):.1%}")
print(f"of those, changed by the correction: {float(changed.sum() / both.sum()):.1%}")
```

```
cells observed in both: 97.2%
of those, changed by the correction: 77.9%
```

Most cells change in this scene because it is 86 % cloudy; in a mostly clear scene only the cloudy cells and the cells they move onto change.

To keep only cloudy cells, combine with `cth`:

```python
cloudy_obs = ds["cth"].notnull() & (ds["fill_flag"] == 0)
```

## Regular grid or native grid?

| | Regular grid | Native grid |
| :--- | :--- | :--- |
| Shape | Set by `--grid` | Same as the input region |
| Good for | Comparing with other gridded data (radar, models), maps, time series on fixed cells | Models trained on L1C tiles; corrected and uncorrected pixel-for-pixel |
| Coordinates | 1-D `lat`, `lon` | 2-D `lat`, `lon` |
| Gaps | Fewer interpolated cells, because 0.04° cells are a little larger than the pixels | More interpolated pixels (about 6 % in the example); option `--fill-empty` for a complete image |
| Available from | `l1c`, `correct`, `batch`, `correct_scene()` | `l1c --native`, `correct_native()` |

More on the method behind these variables: [concepts.md](concepts.md). Python details: [python_api.md](python_api.md).
