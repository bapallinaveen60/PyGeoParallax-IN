# Quickstart

This page takes about five minutes. It runs the built-in demo, then corrects one real INSAT-3DR L1C file from the command line and from Python, and plots the result. Install the package first ([installation.md](installation.md)), or use the Colab notebook below.

Why parallax matters, in one paragraph: INSAT-3DR sits above 74° E. It sees a tall cloud at a slant, so the cloud top appears displaced away from the satellite. Over India the displacement is typically 3–10 km and reaches about 15 km for deep storms in the northeast. PyGeoParallax-IN estimates each cloud's top height from its 10.8 µm brightness temperature, traces the line of sight back to that height, and puts the pixel where the cloud really is. [concepts.md](concepts.md) explains the method.

## Run the demo

The demo needs no data and no internet access.

```bash
pygeoparallax demo
```

It builds a synthetic INSAT-3DR scene over Northeast India with three storms at known positions. Their flat tops are at 16, 12 and 8 km. It simulates exactly what the satellite sees, then corrects the image the normal way: cloud-top height from the brightness temperature, then ray tracing and resampling on the scene's own pixel grid. Finally it measures how far each storm is from its true position.

Output:

```
PyGeoParallax-IN demo: synthetic INSAT-3DR scene over Northeast India (satellite at 74 E)
storm                                 top   uncorrected   corrected
deep storm near Agartala             16 km       10.9 km      1.2 km
storm over Bangladesh                12 km        8.4 km      1.2 km
shallow storm over West Bengal        8 km        5.0 km      1.1 km
offset = distance of the storm in the image from its true position (observed cells)
check: PASSED (every corrected storm within 4 km, one pixel)
wrote pygeoparallax_demo\demo_uncorrected.nc, pygeoparallax_demo\demo_corrected.nc, pygeoparallax_demo\demo.png
```

How to read the table:

| Column | Meaning |
| :--- | :--- |
| `top` | True cloud-top height of the storm [km]. |
| `uncorrected` | Distance [km] from the storm's true centre to the centre of the cold pixels in the image as the satellite sees it. This is the parallax error. It grows with height. |
| `corrected` | The same distance after correction, using only cells that a pixel actually landed in (`fill_flag` 0). |

The check passes when every corrected storm is within one pixel (4 km) of its true position. The remaining 1 km comes from the 4 km pixel size and from the cloud-top height being estimated from a noisy brightness temperature. The exit code is 0 on pass and 1 on fail.

The demo writes three files to `pygeoparallax_demo/` (change the folder with `-o`):

| File | Content |
| :--- | :--- |
| `demo_uncorrected.nc` | The simulated TIR1 image, as seen by the satellite. |
| `demo_corrected.nc` | The corrected image, in the same layout as `pygeoparallax l1c --native` output ([outputs.md](outputs.md)). |
| `demo.png` | The before/after figure. Needs matplotlib; skip it with `--no-plot`. |

The figure has three panels. Left: the image as the satellite sees it. Middle: after correction. Right: how far each pixel was moved [km]. The red circles are the true storm outlines. Before correction, each storm sits north-east of its circle, away from the satellite, and the higher storm is displaced further. After correction the storms sit on their circles. The right panel shows shifts of about 5, 8 and 11 km for the 8, 12 and 16 km storms; clear-sky pixels are not moved.

## Try it in Colab

The notebook [colab/try_pygeoparallax.ipynb](https://colab.research.google.com/github/bapallinaveen60/PyGeoParallax-IN/blob/main/colab/try_pygeoparallax.ipynb) runs in the browser. Nothing is installed on your computer. Choose **Runtime → Run all**. It:

1. installs the package from GitHub (about 1 minute);
2. runs the demo and shows the figure;
3. optionally asks you to upload one INSAT-3DR L1C file (about 80–90 MB), corrects the region 20–30° N, 85–97° E on the file's own pixel grid, shows uncorrected and corrected TIR1 side by side, and offers the corrected NetCDF for download.

Change `BBOX` in the third cell to correct another region.

## Correct a real L1C file from the command line

You need an INSAT-3DR Imager L1C sector file, named like `3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5`. They are free from [MOSDAC](https://www.mosdac.gov.in) after registration ([data.md](data.md)). The examples below use that file; replace the name with yours.

### On a regular lat/lon grid

```bash
pygeoparallax l1c 3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5 -o corrected --bbox 20 30 85 97 --grid 20 30 85 97 0.04
```

```
done  3RIMG_01AUG2023_1815_L1C_SGP_V01R00_corrected.nc
1/1 scenes in 7.1 s
```

- `--bbox 20 30 85 97` reads only 20–30° N, 85–97° E from the file. This is much faster than the full sector (about 7 s instead of 20 s).
- `--grid 20 30 85 97 0.04` puts the result on a 0.04° grid over the same box (250 × 300 cells). Without `--grid`, a `--bbox` region is put on a 0.04° grid over that box, so this is the same as leaving `--grid` out.
- The output is `corrected/3RIMG_01AUG2023_1815_L1C_SGP_V01R00_corrected.nc`, with the channels TIR1, TIR2, WV and MIR, the cloud-top height and the shift.

Make the uncorrected baseline on exactly the same grid, for comparison:

```bash
pygeoparallax l1c 3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5 -o uncorrected --bbox 20 30 85 97 --grid 20 30 85 97 0.04 --no-correction
```

This writes `uncorrected/3RIMG_01AUG2023_1815_L1C_SGP_V01R00_uncorrected.nc`. Clear-sky cells are identical in the two files; only cloudy cells and the cells they move onto differ.

### On the file's own pixel grid

```bash
pygeoparallax l1c 3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5 -o corrected_native --bbox 20 30 85 97 --native --fill-empty
```

With `--native`, the output has the same pixels as the input (here 306 × 334 pixels of about 4 km), so corrected and uncorrected images line up pixel for pixel. `--fill-empty` fills the few pixels that no corrected pixel reached (behind tall clouds) with the nearest value, which is useful for models that need a complete image. Those pixels stay marked in `fill_flag`.

### Many files

Give a quoted glob pattern and a number of parallel processes:

```bash
pygeoparallax l1c "L1C/3RIMG_*_L1C_SGP_V01R00.h5" -o corrected -j 4
```

Existing outputs are skipped, so you can rerun the command after an interruption. All options are in [cli.md](cli.md).

## Correct a real L1C file in Python

The same two paths, from Python:

```python
from pygeoparallax import correct_native, correct_scene
from pygeoparallax.cloudheight import cloud_top_height
from pygeoparallax.ingest import read_insat_l1c
from pygeoparallax.resample import Grid

path = "3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5"
ds = read_insat_l1c(path, channels=("TIR1", "WV"), bbox=(20, 30, 85, 97))
lat, lon = ds["lat"].values, ds["lon"].values
cth = cloud_top_height(ds["TIR1"].values)          # m above the ellipsoid, NaN = clear sky
channels = {"TIR1": ds["TIR1"].values, "WV": ds["WV"].values}

# regular grid: lat_min, lat_max, lon_min, lon_max, res [degrees]
grid = Grid(20, 30, 85, 97, res=0.04)
corrected = correct_scene(lat, lon, channels, cth, grid=grid)
uncorrected = correct_scene(lat, lon, channels, cth, grid=grid, correct=False)
corrected.to_netcdf("scene_corrected.nc")

# the file's own pixel grid
native = correct_native(lat, lon, channels, cth, fill_empty=True)
native.to_netcdf("scene_native_corrected.nc")
```

`cloud_top_height` marks pixels with TIR1 brightness temperature below 270 K as cloud and looks up their height in the AFGL tropical atmosphere. Other choices (ERA5 profiles, clear-sky BT mask, terrain, navigation correction) are in [python_api.md](python_api.md).

## Open and plot the output

Each output is a NetCDF file that xarray opens directly. This example uses the regular-grid files from the command-line section above:

```python
import matplotlib.pyplot as plt
import xarray as xr

cor = xr.open_dataset("corrected/3RIMG_01AUG2023_1815_L1C_SGP_V01R00_corrected.nc")
raw = xr.open_dataset("uncorrected/3RIMG_01AUG2023_1815_L1C_SGP_V01R00_uncorrected.nc")
print(cor.attrs["time"], cor.attrs["parallax_corrected"], cor.sizes)

cloudy = cor["cth"].notnull()
print(f"cloudy cells: {float(cloudy.mean()):.0%}")
print(f"median shift of cloudy cells: {float(cor['shift_km'].where(cloudy).median()):.1f} km")

fig, ax = plt.subplots(1, 3, figsize=(16, 4.5), constrained_layout=True)
raw["TIR1"].plot(ax=ax[0], cmap="Greys", vmin=190, vmax=300)
cor["TIR1"].plot(ax=ax[1], cmap="Greys", vmin=190, vmax=300)
cor["shift_km"].where(cloudy).plot(ax=ax[2], cmap="viridis")
ax[0].set_title("TIR1, uncorrected")
ax[1].set_title("TIR1, corrected")
ax[2].set_title("shift [km]")
fig.savefig("tir1_before_after.png", dpi=100)
```

```
2023-08-01T18:28:53 1 Frozen({'lat': 250, 'lon': 300})
cloudy cells: 86%
median shift of cloudy cells: 6.6 km
```

With the `Greys` colour map, cold cloud tops are light and the warm surface is dark. Differences between the two TIR1 panels are small at this scale (a few kilometres); zoom into a storm edge to see them, or look at the shift panel.

For a native-grid file, `lat` and `lon` are 2-D coordinates. Plot with them explicitly:

```python
import matplotlib.pyplot as plt
import xarray as xr

nat = xr.open_dataset("corrected_native/3RIMG_01AUG2023_1815_L1C_SGP_V01R00_corrected.nc")
nat["TIR1"].plot(x="lon", y="lat", cmap="Greys", vmin=190, vmax=300)
plt.savefig("tir1_native.png", dpi=100)
```

Before using the values for statistics, read [outputs.md](outputs.md), in particular how to use `fill_flag` to exclude interpolated and empty cells.

## Next steps

- All command-line options: [cli.md](cli.md).
- Every output variable and attribute: [outputs.md](outputs.md).
- Python functions: [python_api.md](python_api.md).
- Where to get L1C, ERA5, SRTM and GPM data: [data.md](data.md).
- What the correction does and does not do: [concepts.md](concepts.md) and [validation.md](validation.md).
- Something went wrong: [troubleshooting.md](troubleshooting.md).
