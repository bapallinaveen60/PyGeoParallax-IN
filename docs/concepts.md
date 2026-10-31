# Concepts and algorithms

This page explains what PyGeoParallax-IN computes, how, and where the method stops being reliable. It is written for a scientist who wants to judge the output, not only run the code. The authoritative description is the methods section of the paper (`08_manuscript/methods_draft.md`); numbers on this page come from it, from `00_Documentation/validation_summary.md`, `00_Documentation/benchmark.md` or from the code.

For the functions named here, see [python_api.md](python_api.md). For the input files, see [data.md](data.md). For the validation results in full, see [validation.md](validation.md).

Conventions used throughout:

- Positions are geodetic latitude and longitude on the WGS84 ellipsoid, in degrees.
- Heights are in metres above the ellipsoid unless stated otherwise. Shifts are in km.
- INSAT-3DR is at 74.0° E (`SATELLITE_LONGITUDES["INSAT-3DR"]`). The orbit radius is 42 164.16 km (`GEO_RADIUS`).
- A NaN cloud-top height means clear sky or unknown. Such pixels are not moved (unless a DEM is given, see [Terrain](#terrain-aware-correction)).

## Contents

1. [Parallax geometry](#parallax-geometry)
2. [Cloud-top height from brightness temperature](#cloud-top-height-from-brightness-temperature)
3. [The ray-tracing solver](#the-ray-tracing-solver)
4. [Terrain-aware correction](#terrain-aware-correction)
5. [Occlusion-aware resampling](#occlusion-aware-resampling)
6. [Correction on the native pixel grid](#correction-on-the-native-pixel-grid)
7. [Effective height](#effective-height)
8. [Navigation correction](#navigation-correction)
9. [Known limitations](#known-limitations)

---

## Parallax geometry

INSAT-3DR geolocates every pixel where its line of sight meets the ellipsoid surface. This is the *apparent* (navigated) position. A cloud top at height $h$ lies on the same line of sight, but nearer the satellite. Seen from the satellite, the cloud therefore appears displaced **away from the sub-satellite point** (74° E, 0° N), by approximately

$$
\Delta \approx h \tan(\mathrm{VZA}),
$$

where VZA is the viewing zenith angle. The correction moves the pixel back **towards** the satellite along the line of sight, by the same amount.

The viewing zenith angle (VZA) and viewing azimuth angle (VAA) are computed from the geometry, not read from the L1C file (see [data.md](data.md) for why). With $\mathbf{p}$ the ECEF position of the ground point and $\mathbf{s} = R_{\mathrm{geo}}(\cos\lambda_s, \sin\lambda_s, 0)$ the satellite, the unit line of sight is $\hat{\mathbf{d}} = (\mathbf{s} - \mathbf{p})/\lVert\mathbf{s} - \mathbf{p}\rVert$. VZA is the angle between $\hat{\mathbf{d}}$ and the local vertical. VAA is the bearing of $\hat{\mathbf{d}}$ from north, so it points **towards** the satellite. The angles agree with pyorbital within 0.01°.

Over India the satellite is to the south (and, in the east, to the south-west), so the apparent displacement is mostly northward, and north-eastward over Northeast India.

### Typical magnitudes

Shift of a 12 km cloud top at a few places, from `satellite_view_angles`, `parallax_correct` and `parallax_shift` (see [python_api.md](python_api.md#geometry)):

| Place | VZA [°] | VAA [°] | Corrected position moves towards [°] | Shift for $h$ = 12 km [km] |
| :--- | ---: | ---: | ---: | ---: |
| Kochi | 12.0 | 193.0 | 193.0 | 2.6 |
| Mumbai | 22.4 | 176.6 | 176.6 | 4.9 |
| Delhi | 33.5 | 186.7 | 186.7 | 7.9 |
| Agartala | 34.0 | 217.6 | 217.6 | 8.1 |
| Guwahati | 36.4 | 216.0 | 216.0 | 8.8 |

By validation region (VZA ranges from the methods, Table R; shifts from $h\tan(\mathrm{VZA})$):

| Region | Box | VZA [°] | Shift, $h$ = 12 km [km] | Shift, $h$ = 16 km [km] |
| :--- | :--- | :--- | :--- | :--- |
| South India | 7–18° N, 73–82° E | 8–23 | 1.7–5.1 | 2.2–6.8 |
| Central India | 18–27° N, 75–86° E | 21–34 | 4.6–8.1 | 6.1–10.8 |
| Himalaya | 24–33° N, 74–90° E | 28–42 | 6.4–10.8 | 8.5–14.4 |
| Northeast India and Bangladesh | 21–29° N, 88–97° E | 29–42 | 6.7–10.8 | 8.9–14.4 |

On 148 monsoon scenes over 0–40° N, 60–100° E, the median shift of cloudy cells was 4.4 km per scene (range 3.0–5.5 km) and the 95th percentile 9.0 km (range 7.3–12.5 km). The INSAT-3DR infrared pixel is about 4 km at the sub-satellite point, so the shift is one to three pixels.

The sensitivity to a height error $\delta h$ follows from the same relation: the corrected position moves by about $\delta h\tan(\mathrm{VZA})$, about 0.4 km per km of height error at Mumbai and 0.7 km at Agartala.

---

## Cloud-top height from brightness temperature

INSAT-3DR L1C files have no cloud-top height, and the ISRO L2B CTP product has none either (see [data.md](data.md)). Height is therefore derived per pixel from the TIR1 (10.8 µm) brightness temperature (BT). For an opaque cloud, TIR1 BT is close to the cloud-top temperature, so the cloud-top height is the height at which a reference temperature profile has that temperature.

### Cloud mask

A pixel is cloudy if (`cloudheight.cloud_mask`):

- its BT is more than $\delta$ = 8 K below the clear-sky BT, where a clear-sky BT is available (ISRO's L2B `CSBT_TIR1`, sampled to the pixel by nearest neighbour); or
- its BT is below 270 K, where no clear-sky BT is available.

Clear pixels get NaN height and are not moved. The `pygeoparallax l1c` command uses the fixed 270 K threshold only (option `--cloud-threshold`). The clear-sky reference is available from Python: see [python_api.md](python_api.md#cloudheight).

### Standard atmosphere

The default profile is the AFGL tropical standard atmosphere (`cloudheight.TROPICAL`), 0–25 km at 1 km spacing. BT is interpolated linearly in height between the surface (299.7 K) and the cold-point tropopause (17 km, 194.8 K):

- BT colder than 194.8 K, as in overshooting tops, is assigned the tropopause height, 17 km. This is the **tropopause cap**.
- BT warmer than the surface value gives 0 m.

### ERA5 profiles

As an alternative, ERA5 temperature and geopotential on pressure levels (`ingest.read_era5_profiles`, `cloudheight.cloud_top_height_profiles`):

1. Geopotential $\Phi$ is converted to geometric height: $z = R\,(\Phi/g_0)/(R - \Phi/g_0)$, with $g_0$ = 9.80665 m s⁻² and $R$ = 6 371 008.8 m. This differs from geopotential height by about 45 m at 17 km.
2. Profiles are interpolated bilinearly to each pixel.
3. The lookup starts at each column's cold-point tropopause, searched no higher than 70 hPa (`min_pressure`), and runs **downwards**. It takes the first level at least as warm as the BT and interpolates linearly. Searching from the top keeps low-level inversions from capturing high clouds.
4. BT colder than the cold point gets the cold-point height.

On the first 14 validation cases (2022–2024), ERA5 changed cold-core heights by −0.15 km (median) and the INSAT–GPM offsets by under 0.5 km relative to the standard atmosphere. Deep cores are colder than the ERA5 cold point too, so both profiles put them at about 17 km. ERA5 puts mid-level clouds about 0.9 km higher than AFGL.

### Height reference

Profile heights are above mean sea level. The code treats them as ellipsoidal heights. The difference, the geoid undulation of about −50 to −100 m over India, changes the shift by less than 1 %.

### Limits of the BT method

- **Thin cirrus:** semi-transparent cloud lets warmer radiation from below through. Its BT is warmer than its true top, so its height is underestimated and it is corrected too little.
- **Overshooting tops:** capped at the tropopause height.
- **Profile error:** the standard atmosphere differs from the real one by a few hundred metres.
- **IR top vs precipitation:** the infrared top is not where the rain is (see [Effective height](#effective-height)).

---

## The ray-tracing solver

The corrected position is the point on the line of sight whose geodetic height equals the cloud height $h$:

$$
\mathbf{q}(t) = \mathbf{p}_0 + t\,\hat{\mathbf{d}},
$$

where $\mathbf{p}_0$ is the apparent position at the navigation reference height $h_0$ ($h_0$ = 0 for L1C data; argument `h0` of `parallax_correct`). The solver follows Bieliński (2020) in two steps.

**1. Enlarged ellipsoid.** Intersect the line with the ellipsoid of semi-axes $a + h$ and $b + h$:

$$
\frac{q_x^2 + q_y^2}{(a + h)^2} + \frac{q_z^2}{(b + h)^2} = 1 .
$$

This is a quadratic $A t^2 + B t + C = 0$. The code takes the root closest to the apparent point, using the numerically stable form $t = C/q$ or $q/A$ with $q = -\tfrac{1}{2}\left(B + \operatorname{sign}(B)\sqrt{B^2 - 4AC}\right)$. The enlarged ellipsoid is not a surface of constant geodetic height. The error is about 1 cm for a 12 km cloud over India.

**2. Newton refinement.** One step on the true geodetic height (`newton_iterations=1`):

$$
t \leftarrow t + \frac{h - h_{\mathrm{geod}}(\mathbf{q}(t))}{\hat{\mathbf{d}}\cdot\hat{\mathbf{u}}(\mathbf{q}(t))},
$$

where $\hat{\mathbf{u}}$ is the local vertical at $\mathbf{q}$. This brings the error below 1 mm. ECEF-to-geodetic conversion uses Bowring's method with three iterations and agrees with pyproj to better than 1 mm.

Output is NaN where the height is NaN, where the point is behind the Earth's limb (line of sight below the local horizon), or where the quadratic has no real root.

### Accuracy and comparison

| Check | Agreement |
| :--- | :--- |
| ECEF transforms against pyproj | < 1 mm |
| VZA and VAA against pyorbital | < 0.01° |
| Corrected positions against satpy (spherical Earth) | within 25 m |
| Enlarged ellipsoid alone (no Newton step), 12 km cloud over India | about 1 cm |
| With one Newton step | < 1 mm |

### Backends and speed

`parallax_correct(..., backend="numba")` (the default) runs a parallel compiled kernel that processes each pixel in one pass, without large temporary arrays. `backend="numpy"` is the vectorised reference implementation. Both give identical results.

| Task | Time (laptop) |
| :--- | :--- |
| Full disk, Numba kernel | 0.5 s |
| Full disk, NumPy backend | about 9 s |
| 1-million-pixel India scene, correction and resampling | about 2 s |
| Full pipeline per scene (read 2 channels, height, correct, regrid corrected and uncorrected), 148 scenes | 1.8 s median, 3.2 s max |

The first Numba call in a new process compiles the kernel. The compiled code is cached on disk (`cache=True`), so later processes start faster.

---

## Terrain-aware correction

Ellipsoid-navigated data misplace elevated ground as well as clouds: over the Himalaya or the Western Ghats a 2 km ridge is displaced by about 1–1.5 km. With a DEM (`surface_height=` in `correct_scene`, `correct_native` or `parallax_correct_terrain`), the solver:

- **cloudy pixels:** uses $\max(h_{\mathrm{cloud}}, h_{\mathrm{ground}})$, so no cloud is placed below the ground;
- **clear pixels:** moves them to where the line of sight meets the terrain. This is clear-sky terrain parallax.

The ground height is needed at the *corrected* position, which is not known in advance. The code solves this by fixed-point iteration (`terrain_iterations`, default 3), starting at the apparent position:

$$
h^{(k)} = \max\!\left(h_{\mathrm{cloud}},\ z_g(\varphi^{(k)}, \lambda^{(k)})\right), \qquad
(\varphi^{(k+1)}, \lambda^{(k+1)}) = \mathrm{solve}\!\left(h^{(k)}\right).
$$

It converges where the terrain is less steep than the line of sight, which holds for VZA below about 70°.

The DEM lookup (`terrain.surface_height_from_dataset`) is bilinear. Points outside the DEM and NaN voids (open sea) are 0 m. SRTM heights are above the EGM96 geoid, which lies 50–105 m below the ellipsoid over India. This changes the terrain correction by under 75 m at VZA 35°, so heights are used as they are.

With SRTM over India:

| Where | Ground shift |
| :--- | :--- |
| Himalaya and Tibetan Plateau | 3–4 km |
| Northeast hills | 1–2 km |
| Western Ghats and Deccan | < 0.5 km |
| Clear-sky ground in Himalayan validation scenes | 1.3–2.5 km median, up to about 6 km |
| Clear-sky ground in Central India scenes | about 0.15 km median, up to 0.65 km |

Storm tops are 10–17 km above the ground, so terrain does not change storm positions measurably: in the first 14 validation cases the offsets with and without terrain are identical to 0.1 km.

Without a DEM, the ground is the ellipsoid and clear pixels stay where they are.

---

## Occlusion-aware resampling

After correction, pixels no longer lie on a regular grid. Several may land in one cell and some cells receive none. `resample.resample` (used by `correct_scene` and `correct_native`) applies three rules.

1. **Collisions: the highest wins.** When several pixels fall in one cell, the pixel with the greatest height keeps the cell. The satellite sees the highest cloud; lower cloud or ground beneath it is hidden. Clear pixels take part with height 0 m (or the ground height, with a DEM), so a cloud moved onto a clear cell replaces it.
2. **Small gaps: IDW filling.** Cells that receive no pixel because neighbouring pixels spread apart are filled by inverse-distance weighting from observed cells within `fill_radius` cells (default 1):
   $$
   v = \frac{\sum_i w_i v_i}{\sum_i w_i}, \qquad w_i = d_i^{-2},
   $$
   with $d_i$ the distance in cells. A filled cell stays clear (NaN `cth`) if more than half of its neighbour weight comes from observed clear cells. Clear-sky gaps therefore stay clear.
3. **Large gaps: left empty.** Cells behind tall clouds, which the satellite never saw, stay NaN.

Each output cell carries `fill_flag`:

| `fill_flag` | Constant | Meaning |
| ---: | :--- | :--- |
| 0 | `OBSERVED` | at least one pixel landed in the cell |
| 1 | `INTERPOLATED` | filled from neighbours |
| 2 | `EMPTY` | no pixel and no observed neighbour within `fill_radius` |

Analyses that need only real observations can exclude flags 1 and 2. The `count` variable gives the number of pixels that landed in each cell, and `height` the winning height.

On the default 0.04° grid (0–40° N, 60–100° E, 1000 × 1000 cells), a 4 km pixel lands in about one cell. In 148 monsoon scenes, 98.7 % of cells were observed, 1.3 % interpolated and 0.007 % empty. Correction moved cloud onto 2.5 % (median) of previously clear cells. On a grid finer than the pixel (for example the 0.02° grid used for validation) most cells receive no pixel even without correction, so a large share of cells is flagged 1.

The uncorrected dataset (`correct=False`) is made by the same resampling at the apparent positions. Corrected and uncorrected outputs therefore share exactly the same grid, and in 148 scenes every clear cell not covered by moved cloud was identical in both.

---

## Correction on the native pixel grid

`correct_native` puts the corrected scene back on the input's own pixel grid: same shape, same pixel centres, dimensions `(y, x)`. It uses the same correction and occlusion rules as `correct_scene`.

The L1C SGP product is on an ellipsoidal Mercator projection (WGS84). Its pixel centres are evenly spaced in longitude along columns and in **Mercator northing** along rows, not in latitude. For a unit equatorial radius, the northing is

$$
y(\varphi) = \ln\!\left[\tan\!\left(\frac{\pi}{4} + \frac{\varphi}{2}\right)\left(\frac{1 - e\sin\varphi}{1 + e\sin\varphi}\right)^{e/2}\right],
$$

with $e$ the WGS84 first eccentricity (`resample.mercator_y`; the inverse is `mercator_lat`). `NativeGrid.from_2d` or `NativeGrid.from_coords` fits $y = y_0 + \text{row}\cdot\Delta y$ and $\lambda = \lambda_0 + \text{col}\cdot\Delta\lambda$ to the pixel centres. The fit must hold to within 0.01 pixel (`tolerance`). If the rows are not regular in Mercator northing, the fit tries latitude itself (`kind="latlon"`), and raises `ValueError` if neither works. Each corrected position is then mapped to a fractional row and column, and the bucket resampler runs in this index space, one cell per pixel.

If positions were shifted by a navigation correction, they are no longer separable. Pass the grid of the original file explicitly (`grid=NativeGrid.from_2d(file_lat, file_lon)`).

`fill_empty=True` fills cells that no pixel reached (`fill_flag` 2, behind tall clouds or at the edges) with the nearest corrected value. The cells keep `fill_flag` 2.

### Why it matters for machine learning

A model trained on L1C tiles expects inputs on the L1C pixel grid. Regridding to a lat/lon grid changes the sampling, so a comparison between models trained on uncorrected and corrected input would mix the resampling with the parallax effect. On the native grid:

- uncorrected and corrected inputs line up pixel for pixel, and in clear sky they are identical;
- labels that are already on the ground (for example GPM precipitation type matched to each pixel) stay where they are, while the input moves.

In the precipitation-type U-Net experiment (see [unet.md](unet.md)), the correction moved cloud by a median of 4.4 km, about one pixel, and changed TIR1 by more than 1 K on 34 % of pixels. Cells that received no corrected pixel were 0.06 % of labelled pixels; they were filled with the nearest corrected value and their labels dropped for both models.

---

## Effective height

The BT-derived height is the top of the cloud. That is right for cloud products. Precipitation sits lower: against GPM DPR over India, the coldest convective tops were a median 3.2 km above the Ku-band storm top in the same cell (206 cells, 2018–2024; the medians of the two heights were 16.6 km and 11.9 km, and 46 % of the INSAT cold cores were at the 17 km cap). Part of this gap is physical: radar echo tops lie 1–3 km below the infrared cloud top.

For rain-related products the correction can use a lower, *effective* height (`cloudheight.effective_height`):

$$
h_{\mathrm{eff}} = \max(s\,h - o,\ 0),
$$

with scale $s$ (`scale`, default 1) and offset $o$ (`offset`, metres, default 0). NaN stays NaN. A starting point is $o \approx$ 3000 m or $s \approx$ 0.7. These are not a calibration. On the command line the options are `--height-offset` (km) and `--height-scale` (see [cli.md](cli.md)). The effective height is used both for the correction and for occlusion in the resampling.

---

## Navigation correction

Parallax correction assumes the navigated positions are right. Matching INSAT-3DR images to coastlines shows errors of up to 20 km that vary with season (`pygeoparallax.navigation`; full record in `00_Documentation/navigation_check.md`). Offsets are the correction to **add** to INSAT positions to reach the true ground location, in km east and km north.

### Measurement

There are 13 coastal windows (`navigation.WINDOWS`) around India, Sri Lanka, Bangladesh and Myanmar:

| Window | Box (lat, lon) | Window | Box (lat, lon) |
| :--- | :--- | :--- | :--- |
| kutch | 22.0–23.8° N, 68.3–70.8° E | chennai | 12.0–14.5° N, 79.0–81.0° E |
| saurashtra | 20.0–23.0° N, 68.5–71.8° E | andhra | 15.0–17.8° N, 80.0–83.0° E |
| konkan | 17.5–20.5° N, 71.5–74.0° E | odisha | 19.0–22.0° N, 85.0–88.0° E |
| goa_karnataka | 13.5–16.5° N, 72.5–75.5° E | andaman | 10.5–13.8° N, 92.0–93.6° E |
| kerala | 8.0–11.5° N, 74.5–77.5° E | rakhine | 16.5–20.5° N, 92.5–95.5° E |
| sri_lanka | 5.8–10.0° N, 79.0–82.2° E | chittagong (east only) | 20.7–22.9° N, 91.2–92.6° E |
| | | sundarbans (east only) | 21.0–22.9° N, 88.0–90.6° E |

In each window (`measure_scan`, `measure_window`):

1. A land-fraction map is made from Natural Earth 10 m land polygons, rasterised at 0.005° and box-filtered to the 4 km pixel footprint.
2. The image is chosen by the solar zenith angle (SZA) at the window centre:
   - **day** (SZA < 75°): VIS albedo, using clear pixels with VIS < 30 % and TIR1 > 285 K;
   - **night:** TIR1 with the sign reversed (land colder than sea), using pixels with TIR1 > 285 K.
3. A window is used only if it has at least 300 clear pixels, including at least 50 land pixels (land fraction > 0.9) and 50 sea pixels (< 0.1).
4. Trial shifts cover ±30 km, first in 2 km steps, then in 0.5 km steps within ±2 km of the best coarse shift. The shift with the highest Pearson correlation $r$ is the window's offset.
5. Chittagong and Sundarbans (`navigation.EAST_ONLY`) search east–west only. Their coasts run roughly north–south or are blurred by estuaries, so a north–south match runs to the search edge. Their north offset is NaN.

### Acceptance rules

`NavigationCorrection.from_matches` keeps a window only if:

- $r \ge$ 0.6 (`min_r`), the best shift is not at the search edge, and both components are within 25 km (`max_offset_km`);
- if the window was matched in two or more scans (for example 04:15 and 06:15 UTC of one day), they agree within 5 km in both components (`agree_km`); the median of the matches is used;
- if it was matched in only one scan, $r \ge$ 0.75 (`single_min_r`).

These rules reject matches distorted by cloud, which are common in the monsoon. Pass all scans of one day together, so that the two-scan check can work.

### Correction field

Accepted window offsets are spread over the scene by inverse-distance weighting:

$$
\Delta_E(\mathbf{x}) = \frac{\sum_i w_i\,\Delta_{E,i}}{\sum_i w_i}, \qquad w_i = \max(d_i, 1\ \mathrm{km})^{-2},
$$

with $d_i$ the great-circle distance to window $i$. The north component uses only windows that measured it (it is 0 if none did). Close to a window the field equals that window's offset; far from all windows it is a weighted mean. The east and north offsets are added to each pixel's position (a geodesic move on WGS84, `ingest.insat.shift_positions`) **before** cloud-top height and parallax correction.

Tested on the winter matches: a window left out and predicted from the others on the same day had a median error of 4.3 km (8.8 km uncorrected). A field from another season made the error much worse (15.1 km, against 4.2 km uncorrected, when a February field was applied to 6 June).

### Seasonal behaviour

Measurements from March 2022 to December 2024 show two states:

| Period | Error state | Correction to apply |
| :--- | :--- | :--- |
| Late September to mid-March | "winter" | 7–20 km **westward**; about 0 along Konkan–Goa, largest over Odisha |
| Mid-April to September | "summer" | small; up to about 10 km eastward in mid-April, about 0–3 km by May–June |

The switch near the equinoxes is consistent with the yaw flip of the INSAT-3D-series spacecraft, a 180° rotation about the yaw axis in March and September. Never apply a correction measured in one state to a scene in the other.

### Monsoon values

During the monsoon the error is small and cannot be measured reliably for a single day:

- night-time matching fails, because land and sea have nearly the same TIR1 temperature;
- daytime matches from scans 1–2 h apart scatter by about 9–10 km;
- in July 2023 and July 2024 no window gave a reliable match.

The validation therefore applies one correction per monsoon: the median of that year's daytime matches near the validation storms, from scans of the case days and the days before and after (2018–2024; $r \ge$ 0.7, not at the search edge, both components within 25 km). The values are small: −2.0 to +3.0 km east and −0.8 to +2.5 km north. A year with fewer than 8 such matches (2018, with 2) uses the value pooled over all years, +0.5 km east and +1.5 km north. The north component is uncertain by several kilometres: different coasts give −2.5 to +8.8 km.

---

## Known limitations

**Cloud-top height**

- Thin cirrus is under-corrected, because its BT is warmer than its top.
- Overshooting tops are capped at the tropopause (17 km with AFGL).
- The method assumes a single opaque layer. Multi-layer scenes take the height of whatever dominates the TIR1 signal.
- The fixed 270 K threshold misses low warm cloud. Low cloud also moves little, since the shift scales with height.
- The standard atmosphere differs from the real one by a few hundred metres. ERA5 changes storm results by under 0.5 km.

**What the correction targets**

- The correction places the infrared cloud top. Radar echo tops and rain lie lower (median 3.2 km in the GPM comparison). For precipitation work consider an [effective height](#effective-height).
- In the GPM validation (63 cases, 38 usable), uncorrected cold cores already sat on the GPM deep-echo cells, and only about 5 % of the computed parallax was visible there. Full correction moved them about 4.7 km past the cells. At storm scale the mean offset reversed (+2.2 to −1.9 km), but the per-case improvement was not significant (18 of 30 cases). GPM can verify absolute position only to about ±3–5 km for monsoon convection. See [validation.md](validation.md).

**Navigation**

- L1C navigation errors (7–20 km westward from late September to mid-March) can be larger than the parallax itself. Measure a same-day correction where coasts are clear.
- In the monsoon, a per-day correction is not possible from coastlines. The north component is uncertain by several kilometres.
- The correction field is interpolated between coastal windows. Inland and far from any window (for example the Himalaya) it is an extrapolated weighted mean.

**Geometry and data**

- The satellite is assumed at its nominal position (74.0° E, on the equator, 42 164.16 km from the Earth's centre).
- One time is used per scan (the midpoint of the file's start and end times). The full disk takes about 26.9 min, north to south. This matters only for solar angles (navigation day/night choice) and for time matching with other data, not for the parallax geometry.
- L1C `X`/`Y` coordinates are taken as pixel centres. If ISRO meant edges, positions are off by at most half a pixel (2 km). The coastline check shows no sign of such an error.
- Heights above mean sea level (profiles, SRTM) are used as ellipsoidal heights; the error is under 1 % of the shift.
- Without a DEM, clear ground is not moved. With a DEM, the fixed-point iteration needs VZA below about 70°.

**Resampling**

- Interpolated cells (`fill_flag` 1) are not observations. On grids finer than the 4 km pixel they are the majority.
- Cells behind tall clouds are empty (`fill_flag` 2). `fill_empty=True` fills them for models that need a complete image, but the values are not observations.
