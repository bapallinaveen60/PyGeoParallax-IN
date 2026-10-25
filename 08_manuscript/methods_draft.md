# Methods (draft)

*Draft of 25 Oct 2026 for the PyGeoParallax-IN paper. Equations are in LaTeX math; references in [brackets] are placeholders to be completed. All numbers match `pygeoparallax` v0.1.0.*

---

## 2 Data

### 2.1 INSAT-3DR Imager

INSAT-3DR is a geostationary satellite at 74.0°E. Its Imager scans the full disk every 30 minutes (scans start at HH:15 and HH:45) in six channels: visible (VIS, 0.65 µm), shortwave infrared (SWIR, 1.6 µm), mid-wave infrared (MIR, 3.9 µm), water vapour (WV, 6.8 µm) and two thermal infrared channels (TIR1, 10.8 µm; TIR2, 12.0 µm). The sampling interval is 1 km for VIS and SWIR and 4 km for the infrared channels at the sub-satellite point. We used the Level-1C sector product (`3RIMG_*_L1C_SGP`) from MOSDAC [ref]. It is on a Mercator grid (`lon_0 = 75°E`) with pixel-centre coordinates. Calibrated counts are converted to brightness temperature (BT) or albedo through the lookup tables in each file.

The full-disk scan runs north to south, from 81°N to 81°S, in about 26.9 min (from the file start and end times). We estimate the scan time at a given latitude by linear interpolation along this sweep.

We did not use the satellite elevation and azimuth angles in the L1C files: they differ from the geometric values by about 1°. Viewing angles are computed directly (Section 3.1).

The Level-2B cloud-top pressure product (`3RIMG_*_L2B_CTP`) gives cloud-top pressure and temperature in coarse boxes (about 37 km) and a clear-sky brightness temperature (CSBT) per channel. It contains no cloud-top height. We use its CSBT as the clear-sky reference for the cloud mask (Section 3.2) and its cloud-top pressure only as a cross-check. Its sub-satellite longitude attribute (82°E) is incorrect for INSAT-3DR and is ignored.

### 2.2 GPM Dual-frequency Precipitation Radar

GPM Core Observatory carries the Dual-frequency Precipitation Radar (DPR) [ref]. We used the Ku-band Level-2A product (`2A.GPM.Ku`, version V08) from NASA GES DISC, full-swath (`FS`) group, about 245 km wide with a footprint of about 5 km. Variables read: storm-top height, near-surface corrected reflectivity, near-surface precipitation rate, precipitation type, bright-band height and the spacecraft position.

GPM 2A gives each footprint's position at the surface. An echo at height $h$ lies on the slanted radar beam, displaced towards the spacecraft by about $h\tan\theta_{\mathrm{GPM}}$, where $\theta_{\mathrm{GPM}}$ is the local zenith angle of the beam. This displacement is up to about 5 km for a 15 km storm top at the swath edge. We place storm tops on the beam by intersecting the line from the footprint to the spacecraft with the ellipsoid surface at height $h$, using the same Newton refinement as in Section 3.3. The median displacement in our cases is 1 km.

### 2.3 Ancillary data

- **Coastlines:** Natural Earth 10 m land polygons (public domain) [ref], used for the navigation check (Section 3.6).
- **Atmospheric profiles:** AFGL tropical standard atmosphere [Anderson et al., 1986], 0–25 km at 1 km resolution; and ERA5 reanalysis [Hersbach et al., 2020] temperature and geopotential on 29 pressure levels (1000–50 hPa, 0.25°), at the hour nearest each case scan.
- **Terrain:** the solver accepts any digital elevation model on a regular grid. SRTM [ref] will be used for the terrain-aware runs (not included in the results here).

### 2.4 Study period and regions

The study covers the monsoon season (June–September) of 2022, 2023 and 2024. Validation cases come from four regions that span the range of INSAT-3DR viewing angles over India:

| Region | Box (lat, lon) | Viewing zenith angle |
| :--- | :--- | :--- |
| South India (Kerala, Karnataka, Tamil Nadu) | 8–17°N, 74–80.5°E | 9–20° |
| Central India (Madhya Pradesh, Chhattisgarh) | 19–26°N, 76–85°E | 21–30° |
| Himalaya (Uttarakhand, Himachal, Nepal) | 27–33°N, 75–89°E | 31–38° |
| Northeast India and Bangladesh | 22–29°N, 89–97°E | 33–37° |

---

## 3 Parallax correction method

### 3.1 Viewing geometry

All positions are geodetic coordinates on the WGS84 ellipsoid. A surface point at latitude $\varphi$, longitude $\lambda$ and ellipsoidal height $h$ has Earth-centred, Earth-fixed (ECEF) coordinates

$$
\mathbf{p} = \begin{pmatrix} (N + h)\cos\varphi\cos\lambda \\ (N + h)\cos\varphi\sin\lambda \\ \left(N(1 - e^2) + h\right)\sin\varphi \end{pmatrix},
\qquad N = \frac{a}{\sqrt{1 - e^2\sin^2\varphi}},
$$

with semi-major axis $a$ and eccentricity $e$. The inverse transform uses three fixed-point iterations on latitude. Both directions agree with pyproj [ref] to better than 1 mm.

The satellite is at $\mathbf{s} = R_{\mathrm{geo}}(\cos\lambda_s, \sin\lambda_s, 0)$, with $R_{\mathrm{geo}} = 42\,164$ km and $\lambda_s = 74.0°$. The unit line-of-sight vector from the ground to the satellite is $\hat{\mathbf{d}} = (\mathbf{s} - \mathbf{p})/\lVert\mathbf{s} - \mathbf{p}\rVert$. The viewing zenith angle (VZA) is the angle between $\hat{\mathbf{d}}$ and the local vertical; the viewing azimuth angle (VAA) comes from its east and north components. These agree with pyorbital [ref] within 0.01°.

A cloud at height $h$ appears displaced away from the satellite by approximately

$$
\Delta \approx h \tan(\mathrm{VZA}).
$$

Over India the displacement is mostly northward. For a 12 km cloud top it is about 2.6 km at Kochi (VZA 12°) and 8–9 km over Northeast India and the Himalaya (VZA 34–36°).

### 3.2 Cloud-top height

Cloud-top height is estimated per pixel from TIR1 brightness temperature. For an opaque cloud, TIR1 BT is close to the cloud-top temperature, so the cloud-top height is the height at which the reference profile has that temperature.

1. **Cloud mask.** A pixel is cloudy if its BT is more than 8 K below the ISRO clear-sky BT, sampled to the pixel by nearest neighbour. Where no clear-sky BT is available, a pixel is cloudy if BT < 270 K. Clear pixels get no height and are not moved.
2. **Height lookup.** BT is interpolated linearly in the AFGL tropical profile between the surface and the cold-point tropopause (17 km, 194.8 K). BT colder than the tropopause minimum, as in overshooting tops, is assigned the tropopause height.

As an alternative, ERA5 profiles are interpolated bilinearly to each pixel, with geopotential converted to geometric height. The lookup then runs downwards from each column's cold-point tropopause (searched up to 70 hPa), so low-level inversions cannot capture high clouds. On the 14 validation cases, ERA5 changes cold-core heights by −0.15 km (median) and the INSAT–GPM offsets by under 0.5 km relative to the standard atmosphere.

Profile heights are above mean sea level. We treat them as ellipsoidal heights. The difference (the geoid undulation, −50 to −100 m over India) changes the shift by less than 1%.

The approach has known limits: semi-transparent cirrus appears warmer than its true top, so its height is underestimated; and the standard atmosphere differs from the real one by a few hundred metres.

### 3.3 Ray-tracing solver

The navigated (apparent) position of a pixel is where its line of sight meets the ellipsoid. A cloud at height $h$ lies on the same line of sight, nearer the satellite. The corrected position is therefore the point

$$
\mathbf{q}(t) = \mathbf{p}_0 + t\,\hat{\mathbf{d}}
$$

on the line of sight whose geodetic height equals $h$. Here $\mathbf{p}_0$ is the apparent position at the navigation reference height $h_0$ ($h_0 = 0$ for L1C data).

We follow Bieliński [2020] in two steps:

1. **Enlarged ellipsoid.** Intersect the line with the ellipsoid of semi-axes $a + h$ and $b + h$:
   $$
   \frac{q_x^2 + q_y^2}{(a + h)^2} + \frac{q_z^2}{(b + h)^2} = 1.
   $$
   This is a quadratic in $t$, $A t^2 + B t + C = 0$. We take the root closest to the apparent point, using the numerically stable form $t = C/q$ or $q/A$ with $q = -\tfrac{1}{2}\left(B + \operatorname{sign}(B)\sqrt{B^2 - 4AC}\right)$. The enlarged ellipsoid is not a surface of constant geodetic height, but the error is only about 1 cm for a 12 km cloud over India.
2. **Newton refinement.** One step on the true geodetic height,
   $$
   t \leftarrow t + \frac{h - h_{\mathrm{geod}}(\mathbf{q}(t))}{\hat{\mathbf{d}}\cdot\hat{\mathbf{u}}(\mathbf{q}(t))},
   $$
   where $\hat{\mathbf{u}}$ is the local vertical at $\mathbf{q}$. This brings the error below 1 mm.

Points the satellite cannot see (line of sight below the local horizon) and pixels without a height are returned as missing. The corrected position is $\mathbf{q}(t)$ converted back to geodetic coordinates.

Unlike the spherical-Earth correction in satpy [ref], this solver works on the ellipsoid and allows a non-zero reference height. The two agree within 25 m.

### 3.4 Terrain

Ellipsoid-navigated data misplace not only clouds but also elevated ground: over the Himalaya or the Western Ghats a 2 km ridge is displaced by about 1–1.5 km. With a digital elevation model, the solver:

- **cloudy pixels:** uses $\max(h_{\mathrm{cloud}}, h_{\mathrm{ground}})$, so no cloud is placed below the ground;
- **clear pixels:** moves them to where the line of sight meets the terrain (terrain parallax).

The ground height must be taken at the corrected position, which is not known in advance. We solve this by fixed-point iteration (three steps): look up the ground at the current position, correct, and repeat. The iteration converges where the terrain is less steep than the line of sight, which holds for VZA below about 70°.

### 3.5 Resampling onto a regular grid

After correction, pixels no longer lie on a regular grid: several may land in one grid cell and some cells receive none. We resample with three rules:

1. **Collisions:** when several pixels fall in one cell, the pixel with the greatest height wins. The satellite sees the highest cloud; lower ones beneath it are hidden.
2. **Small gaps:** cells that receive no pixel because neighbouring pixels spread apart are filled by inverse-distance weighting (power 2) from observed cells within one cell. A filled cell stays clear (no cloud-top height) if most of its neighbour weight comes from clear cells.
3. **Large gaps:** cells behind tall clouds, which the satellite never saw, are left empty.

Each output cell carries a flag: 0 observed, 1 interpolated, 2 empty. Later analysis can exclude flags 1 and 2. The default grid is 0.04° (0–40°N, 60–100°E); validation uses 0.02°.

The uncorrected dataset is produced by the same resampling with the apparent positions. Both datasets therefore share exactly the same grid, which is required for the downstream model comparison.

### 3.6 Navigation correction

Parallax correction assumes the navigated positions are correct. We checked this by matching INSAT-3DR images to coastlines, and found errors of up to 20 km that vary with season.

**Measurement.** In each of 13 coastal windows around India, Sri Lanka, Bangladesh and Myanmar, we correlate the image with a land-fraction map. The map is made from Natural Earth polygons, blurred to the 4 km pixel footprint.

- **Day** (solar zenith angle < 75°): VIS albedo, using clear pixels (VIS < 30% and TIR1 > 285 K).
- **Night:** TIR1 with the sign reversed, since land is colder than sea, using pixels with TIR1 > 285 K.

A window is used only if it has at least 300 clear pixels, including at least 50 land and 50 sea pixels. Trial shifts cover ±30 km: first in 2 km steps, then in 0.5 km steps around the best value. The shift with the highest Pearson correlation $r$ is the window's offset. Two windows whose coasts run roughly north–south or are blurred by estuaries (Chittagong, Sundarbans) measure only the east–west offset.

**Acceptance.** A window's measurement is kept only if:

- $r \ge 0.6$, the best shift is not at the search edge, and both components are within 25 km;
- if the window was matched in two or more scans of the same day (for example 04:15 and 06:15 UTC), they agree within 5 km in both components, and their median is used;
- if it was matched in only one scan, $r \ge 0.75$.

These rules reject matches distorted by cloud, which are common in the monsoon.

**Correction field.** Accepted window offsets are spread over the scene by inverse-distance weighting (power 2, great-circle distance, minimum distance 1 km). The north component uses only windows that measured it. The resulting east and north offsets are added to each pixel's position before cloud-top height and parallax correction.

**Seasonal behaviour.** Measurements from March 2022 to December 2024 show two states. From late September to mid-March, positions need a 7–20 km westward correction. From mid-April to September the error is small. The switch near the equinoxes is consistent with the satellite's yaw flip. For the monsoon we use the median of all accepted measurements, +1.8 km east and +4.8 km north. A same-day correction was possible on 5 of 7 tested monsoon days.

### 3.7 Implementation

The method is implemented in the open-source Python package `pygeoparallax` (v0.1.0, MIT licence) [repository link]. The solver has a vectorised NumPy reference and a parallel Numba kernel with identical results. The Numba kernel corrects a full disk in 0.5 s on a laptop (the NumPy version takes about 9 s); a 1-million-pixel India scene, including resampling, takes about 2 s. Unit tests (52) run on Linux and Windows under continuous integration. A command-line interface handles single scenes, parallel batches and navigation measurement.

---

## 4 Validation design

### 4.1 Case selection

1. **Coincident overpasses.** For every GPM orbit whose swath centre line crosses a region box between 1 June and 20 September, we estimate when the INSAT-3DR scan reaches that latitude (Section 2.1). Crossings within 5 min of an INSAT scan are kept.
2. **Convection screening.** Each candidate GPM file is screened for convection before INSAT data are downloaded. The densest convective cluster is found by counting GPM convective footprints in 1° bins and taking all convective footprints within about 150 km of the densest bin. A case needs at least 100 convective footprints in this cluster.
3. **Files per case:** the GPM 2A Ku orbit, the INSAT L1C scan nearest in time with its L2B CTP file, and the day's 04:15 and 06:15 UTC L1C scans for navigation.

### 4.2 Colocation

Each case is processed on a 0.02° grid over its region box. INSAT data are corrected (Section 3) and also resampled uncorrected. GPM footprints are assigned to grid cells by nearest neighbour within 3.5 km; storm tops use their slanted-beam positions (Section 2.2). Only cells inside the GPM swath are compared. Analysis is limited to within 150 km and 250 km of the centre of the densest convective cluster.

### 4.3 Offset measures

Because the correction is a displacement, we measure displacements directly, using two independent methods.

**Field correlation.** We find the shift of the INSAT field that best correlates with the GPM field:

- primary pair: $-$BT against GPM storm-top height (both describe storm tops);
- secondary pair: $-$BT against near-surface reflectivity.

Integer shifts up to ±10 cells (±20 km) are tested, and the best one is refined to a fraction of a cell by fitting a parabola through the correlation at the peak and its two neighbours, separately along each axis.

**Cell cores.** Each GPM deep-echo cell (connected cells with storm top > 10 km, at least 8 grid cells) is paired with the INSAT cold core within 25 km of its centroid. The cold core is the centroid of pixels within 3 K of the local minimum BT. The case value is the median over its cells. This measure does not depend on the shape or extent of the anvil.

**Along and across the line of sight.** Each offset is split into a component along the line of sight (positive when INSAT must move towards the satellite to match GPM) and a component across it, using the VAA at the cluster centre. Parallax correction should change only the along-look component. The cross-look component is a control.

**Overlap scores.** We also report:

- intersection over union (IoU) between INSAT deep cores (BT < 220 K) and GPM deep echoes (storm top > 8 km);
- Pearson correlation and mutual information between cold cloud (BT < 235 K) and echo (reflectivity > 25 dBZ).

### 4.4 Usable cases

A case is usable if its convective cluster has at least 100 footprints and at least one field and window gives a reliable match. A match is reliable when the best shift is inside the search range (below 9.5 cells) both before and after correction. Matches at the edge of the search usually mean the two fields describe different parts of the storm.

### 4.5 Experiments

Each case is run in four states:

| State | Navigation correction | Parallax correction |
| :--- | :--- | :--- |
| Raw | no | no |
| Navigation only | monsoon median (+1.8 km E, +4.8 km N) | no |
| Parallax only | no | yes |
| Navigation + parallax | monsoon median | yes |

To separate sources of residual offset, we also compare INSAT cold-core heights with GPM maximum echo-top heights in each matched cell, and repeat the cell analysis with GPM storm tops at their surface footprints instead of on the beam.

### 4.6 Sensitivity

An error $\delta h$ in cloud-top height shifts the corrected position by about $\delta h\tan(\mathrm{VZA})$: about 0.4 km per km of height error at Mumbai and 0.7 km at Agartala. We quantify this with Monte Carlo perturbations of cloud-top height (standard deviation 1 km, 100 members) and with fixed biases of ±1 and ±2 km.

---

## Notes for revision

- Add references: MOSDAC product guide, GPM DPR ATBD, Natural Earth, pyproj, pyorbital, satpy, Vicente et al. (2002), Bieliński (2020), Anderson et al. (1986).
- Section 3.4 needs the SRTM runs before it can report results.
- Confirm the INSAT-3DR yaw-flip dates from IMD's SatMet SOP before stating them as fact.
- The U-Net comparison (Model A uncorrected, Model B corrected) will need its own section.
