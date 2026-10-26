# Methods (draft)

*Draft of 26 Oct 2026 for the PyGeoParallax-IN paper. Equations are in LaTeX math; citations are [Author, year], listed at the end. All numbers match `pygeoparallax` v0.3.0.*

---

## 2 Data

### 2.1 INSAT-3DR Imager

INSAT-3DR is a geostationary satellite at 74.0°E. Its Imager scans the full disk every 30 minutes (scans start at HH:15 and HH:45) in six channels: visible (VIS, 0.65 µm), shortwave infrared (SWIR, 1.6 µm), mid-wave infrared (MIR, 3.9 µm), water vapour (WV, 6.8 µm) and two thermal infrared channels (TIR1, 10.8 µm; TIR2, 12.0 µm). The sampling interval is 1 km for VIS and SWIR and 4 km for the infrared channels at the sub-satellite point. We used the Level-1C sector product (`3RIMG_*_L1C_SGP`) from MOSDAC; INSAT-3DR products use the INSAT-3D formats [SAC, 2014]. It is on a Mercator grid (`lon_0 = 75°E`) with pixel-centre coordinates. Calibrated counts are converted to brightness temperature (BT) or albedo through the lookup tables in each file.

The full-disk scan runs north to south, from 81°N to 81°S, in about 26.9 min (from the file start and end times). We estimate the scan time at a given latitude by linear interpolation along this sweep.

We did not use the satellite elevation and azimuth angles in the L1C files: they differ from the geometric values by about 1°. Viewing angles are computed directly (Section 3.1).

The Level-2B cloud-top pressure product (`3RIMG_*_L2B_CTP`) gives cloud-top pressure and temperature in coarse boxes (about 37 km) and a clear-sky brightness temperature (CSBT) per channel. It contains no cloud-top height. We use its CSBT as the clear-sky reference for the cloud mask (Section 3.2) and its cloud-top pressure only as a cross-check. Its sub-satellite longitude attribute (82°E) is incorrect for INSAT-3DR and is ignored.

### 2.2 GPM Dual-frequency Precipitation Radar

GPM Core Observatory carries the Dual-frequency Precipitation Radar (DPR) [Hou et al., 2014]. We used the Ku-band Level-2A product (`2A.GPM.Ku`, version V08 [Iguchi & Meneghini, 2026]; algorithm in Iguchi et al. [2021]) from NASA GES DISC, full-swath (`FS`) group, about 245 km wide with a footprint of about 5 km. Variables read: storm-top height, near-surface corrected reflectivity, near-surface precipitation rate, precipitation type, bright-band height and the spacecraft position.

GPM 2A gives each footprint's position at the surface. An echo at height $h$ lies on the slanted radar beam, displaced towards the spacecraft by about $h\tan\theta_{\mathrm{GPM}}$, where $\theta_{\mathrm{GPM}}$ is the local zenith angle of the beam. This displacement is up to about 5 km for a 15 km storm top at the swath edge. We place storm tops on the beam by intersecting the line from the footprint to the spacecraft with the ellipsoid surface at height $h$, using the same Newton refinement as in Section 3.3. The median displacement in our cases is 1 km.

### 2.3 Ancillary data

- **Coastlines:** Natural Earth 10 m land polygons (public domain) [Natural Earth], used for the navigation check (Section 3.6).
- **Atmospheric profiles:** AFGL tropical standard atmosphere [Anderson et al., 1986], 0–25 km at 1 km resolution; and ERA5 reanalysis [Hersbach et al., 2020; C3S, 2018] temperature and geopotential on 29 pressure levels (1000–50 hPa, 0.25°), at the hour nearest each case scan.
- **Terrain:** SRTM GL1 [Farr et al., 2007], 1 arcsecond tiles block-averaged to 0.01° (about 1 km). Heights are above the EGM96 geoid, which lies 50–105 m below the ellipsoid over India; this changes the terrain correction by under 75 m at VZA 35°, so heights are used as they are.

### 2.4 Study period and regions

Validation cases come from the monsoon seasons (June–September) of 2018–2024, in four regions that span the range of INSAT-3DR viewing angles over India. The navigation series (Section 3.6) covers March 2022 to December 2024.

**Table R.** Validation regions.

| Region | Box (lat, lon) | Viewing zenith angle |
| :--- | :--- | :--- |
| South India (Kerala, Karnataka, Tamil Nadu) | 7–18°N, 73–82°E | 8–23° |
| Central India (Madhya Pradesh, Chhattisgarh) | 18–27°N, 75–86°E | 21–34° |
| Himalaya (Uttarakhand, Himachal, Nepal) | 24–33°N, 74–90°E | 28–42° |
| Northeast India and Bangladesh | 21–29°N, 88–97°E | 29–42° |

---

## 3 Parallax correction method

### 3.1 Viewing geometry

All positions are geodetic coordinates on the WGS84 ellipsoid [NIMA, 2000]. A surface point at latitude $\varphi$, longitude $\lambda$ and ellipsoidal height $h$ has Earth-centred, Earth-fixed (ECEF) coordinates

$$
\mathbf{p} = \begin{pmatrix} (N + h)\cos\varphi\cos\lambda \\ (N + h)\cos\varphi\sin\lambda \\ \left(N(1 - e^2) + h\right)\sin\varphi \end{pmatrix},
\qquad N = \frac{a}{\sqrt{1 - e^2\sin^2\varphi}},
$$

with semi-major axis $a$ and eccentricity $e$. The inverse transform uses three fixed-point iterations on latitude. Both directions agree with pyproj [Snow et al.] to better than 1 mm.

The satellite is at $\mathbf{s} = R_{\mathrm{geo}}(\cos\lambda_s, \sin\lambda_s, 0)$, with $R_{\mathrm{geo}} = 42\,164$ km and $\lambda_s = 74.0^\circ$. The unit line-of-sight vector from the ground to the satellite is $\hat{\mathbf{d}} = (\mathbf{s} - \mathbf{p})/\lVert\mathbf{s} - \mathbf{p}\rVert$. The viewing zenith angle (VZA) is the angle between $\hat{\mathbf{d}}$ and the local vertical; the viewing azimuth angle (VAA) comes from its east and north components. These agree with pyorbital [Raspaud et al., 2018] within 0.01°.

A cloud at height $h$ appears displaced away from the satellite (Fig. S) by approximately

$$
\Delta \approx h \tan(\mathrm{VZA}).
$$

Uncorrected, this displacement misplaces satellite rainfall estimates by several kilometres, especially for deep convection at high viewing angles [Vicente et al., 2002]. Over India the displacement is mostly northward. For a 12 km cloud top it is about 2.6 km at Kochi (VZA 12°) and 8–9 km over Northeast India and the Himalaya (VZA 34–36°).

### 3.2 Cloud-top height

Cloud-top height is estimated per pixel from TIR1 brightness temperature. For an opaque cloud, TIR1 BT is close to the cloud-top temperature, so the cloud-top height is the height at which the reference profile has that temperature.

1. **Cloud mask.** A pixel is cloudy if its BT is more than 8 K below the ISRO clear-sky BT, sampled to the pixel by nearest neighbour. Where no clear-sky BT is available, a pixel is cloudy if BT < 270 K. Clear pixels get no height and are not moved.
2. **Height lookup.** BT is interpolated linearly in the AFGL tropical profile between the surface and the cold-point tropopause (17 km, 194.8 K). BT colder than the tropopause minimum, as in overshooting tops, is assigned the tropopause height.

As an alternative, ERA5 profiles are interpolated bilinearly to each pixel, with geopotential converted to geometric height. The lookup then runs downwards from each column's cold-point tropopause (searched up to 70 hPa), so low-level inversions cannot capture high clouds. On the first 14 validation cases (2022–2024), ERA5 changes cold-core heights by −0.15 km (median) and the INSAT–GPM offsets by under 0.5 km relative to the standard atmosphere.

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

Unlike the spherical-Earth correction in satpy [Raspaud et al., 2018], this solver works on the ellipsoid and allows a non-zero reference height. The two agree within 25 m.

### 3.4 Terrain

Ellipsoid-navigated data misplace not only clouds but also elevated ground: over the Himalaya or the Western Ghats a 2 km ridge is displaced by about 1–1.5 km. With a digital elevation model, the solver:

- **cloudy pixels:** uses $\max(h_{\mathrm{cloud}}, h_{\mathrm{ground}})$, so no cloud is placed below the ground;
- **clear pixels:** moves them to where the line of sight meets the terrain (terrain parallax).

The ground height must be taken at the corrected position, which is not known in advance. We solve this by fixed-point iteration (three steps): look up the ground at the current position, correct, and repeat. The iteration converges where the terrain is less steep than the line of sight, which holds for VZA below about 70°.

With SRTM over India, the ground shift reaches 3–4 km over the Himalaya and the Tibetan Plateau, 1–2 km over the Northeast hills and under 0.5 km over the Western Ghats and Deccan. Cloud tops are far above the ground, so terrain changes the position of storm cores negligibly; in the first 14 validation cases the offsets with and without terrain are identical to 0.1 km. In clear sky, ground pixels in Himalayan scenes move by 1.3–2.5 km (median), up to about 6 km.

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

**Seasonal behaviour.** Measurements from March 2022 to December 2024 show two states. From late September to mid-March, positions need a 7–20 km westward correction. From mid-April to September the error is small. The switch near the equinoxes is consistent with the yaw flip of the INSAT-3D-series spacecraft, a 180° rotation about the yaw axis in March and September of every year [Prakash et al., 2014]. During the monsoon the error is small and cannot be measured reliably for a single day: night-time matching fails because land and sea have nearly the same TIR1 temperature, and daytime matches from scans 1–2 h apart scatter by about 9–10 km. We therefore apply one correction per monsoon: the median of that year's daytime matches near the validation storms, from scans of the case days and the days before and after (2018–2024) (r ≥ 0.7, not at the search edge, both components within 25 km). The values are small, −2.0 to +3.0 km east and −0.8 to +2.5 km north. A year with fewer than 8 such matches (2018, with 2) uses the value pooled over all years, +0.5 km east and +1.5 km north. The north component is uncertain by several kilometres: different coasts give −2.5 to +8.8 km.

### 3.7 Implementation

The method is implemented in the open-source Python package `pygeoparallax` (v0.3.0, MIT licence; Zenodo DOI 10.5281/zenodo.23672246). The solver has a vectorised NumPy reference and a parallel Numba kernel [Lam et al., 2015] with identical results. The Numba kernel corrects a full disk in 0.5 s on a laptop (the NumPy version takes about 9 s); a 1-million-pixel India scene, including resampling, takes about 2 s. Unit tests (57) run on Linux and Windows under continuous integration. A command-line interface handles single scenes, parallel batches and navigation measurement.

---

## 4 Validation design

### 4.1 Case selection

1. **Coincident overpasses.** For every GPM orbit whose swath centre line crosses a region box between 1 June and 20 September, we estimate when the INSAT-3DR scan reaches that latitude (Section 2.1). Crossings within 5 min of an INSAT scan are kept.
2. **Convection screening.** Each candidate GPM file is screened for convection before INSAT data are downloaded. The densest convective cluster is found by counting GPM convective footprints in 1° bins and taking all convective footprints within about 150 km of the densest bin. A case needs at least 100 convective footprints in this cluster.
3. **Files per case:** the GPM 2A Ku orbit, the INSAT L1C scan nearest in time with its L2B CTP file, and daytime L1C scans of the case day and the days before and after for navigation.

Cases were selected in two rounds: 2022–2024 for all four regions, then 2018–2021 for South and Central India, where the first round had few usable cases. In total 63 cases were processed.

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

Each case is run in four main states:

**Table S.** Correction states.

| State | Navigation correction | Parallax correction |
| :--- | :--- | :--- |
| Raw | no | no |
| Coastline navigation only | per-year monsoon correction (Section 3.6) | no |
| Parallax only | no | yes |
| Coastline navigation + parallax | per-year monsoon correction | yes |

Two further tests address the residual offset:

- **Navigation from GPM.** If the residual cell offset after parallax correction were a navigation error, a single translation fitted to it should centre both offset measures. For each case we take the median cell offset (converted to east and north) of all *other* cases and apply it with parallax correction (leave one out, so no case is corrected with its own data).
- **Synthetic storm.** A storm with known height and position is displaced by its computed parallax and put through the same gridding and matching code, to check that the method recovers the full parallax and zero after correction.

To separate sources of residual offset, we also compare INSAT cold-core heights with GPM maximum echo-top heights in each matched cell, and repeat the cell analysis with GPM storm tops at their surface footprints instead of on the beam.

### 4.6 Sensitivity

An error $\delta h$ in cloud-top height shifts the corrected position by about $\delta h\tan(\mathrm{VZA})$: about 0.4 km per km of height error at Mumbai and 0.7 km at Agartala. We quantify this with Monte Carlo perturbations of cloud-top height (standard deviation 1 km, 100 members) and with fixed biases of ±1 and ±2 km.

### 4.7 Statistics

Uncertainties are 95 % percentile bootstrap intervals from 10 000 resamples. For the field measure, cases are resampled; for the cell measure, cases are resampled with all their cells (a cluster bootstrap), because cells of one storm are not independent. Paired comparisons between correction states use the absolute offset of each case: the median change with its bootstrap interval, the Wilcoxon signed-rank test and the exact sign test on the number of cases that improve. For the cell measure the paired test uses the per-case medians. The dependence of the raw offset on viewing angle is tested with the Spearman rank correlation and the least-squares slope against tan(VZA), with a bootstrap interval.

---

## Notes for revision

- Validation is against GPM only. In the Discussion, name ground-radar (IMD DWR) validation as future work: denser sampling in time and fixed sites at known viewing angles.

---

## References

- Anderson, G. P., Clough, S. A., Kneizys, F. X., Chetwynd, J. H., & Shettle, E. P. (1986). *AFGL atmospheric constituent profiles (0–120 km)*. AFGL-TR-86-0110, Air Force Geophysics Laboratory, Hanscom AFB, MA.
- Bieliński, T. (2020). A parallax shift effect correction based on cloud height for geostationary satellites and radar observations. *Remote Sensing*, 12(3), 365. https://doi.org/10.3390/rs12030365
- C3S (Copernicus Climate Change Service) (2018). ERA5 hourly data on pressure levels from 1940 to present. Copernicus Climate Change Service Climate Data Store. https://doi.org/10.24381/cds.bd0915c6
- Farr, T. G., et al. (2007). The Shuttle Radar Topography Mission. *Reviews of Geophysics*, 45(2), RG2004. https://doi.org/10.1029/2005RG000183
- Hersbach, H., et al. (2020). The ERA5 global reanalysis. *Quarterly Journal of the Royal Meteorological Society*, 146(730), 1999–2049. https://doi.org/10.1002/qj.3803
- Hou, A. Y., et al. (2014). The Global Precipitation Measurement Mission. *Bulletin of the American Meteorological Society*, 95(5), 701–722. https://doi.org/10.1175/BAMS-D-13-00164.1
- Iguchi, T., & Meneghini, R. (2026). GPM DPR Ku Precipitation Profile 2A 1.5 hours 5 km V08. NASA Goddard Earth Sciences Data and Information Services Center (GES DISC). https://doi.org/10.5067/GPM/DPR/Ku/2A/08
- Iguchi, T., Seto, S., Meneghini, R., Yoshida, N., Awaka, J., Le, M., Chandrasekar, V., Brodzik, S., Kubota, T., & Takahashi, N. (2021). *GPM/DPR Level-2 Algorithm Theoretical Basis Document*, version 07A. NASA GSFC / JAXA. https://gpm.nasa.gov/sites/default/files/2022-06/ATBD_DPR_V07A.pdf
- Lam, S. K., Pitrou, A., & Seibert, S. (2015). Numba: a LLVM-based Python JIT compiler. In *Proceedings of the Second Workshop on the LLVM Compiler Infrastructure in HPC* (pp. 1–6). https://doi.org/10.1145/2833157.2833162
- Natural Earth. 1:10m physical vectors: land. Public domain. https://www.naturalearthdata.com
- NIMA (2000). *Department of Defense World Geodetic System 1984: its definition and relationships with local geodetic systems*. Technical Report TR8350.2, 3rd ed., amendment 1. National Imagery and Mapping Agency.
- Raspaud, M., et al. (2018). PyTroll: an open-source, community-driven Python framework to process Earth observation satellite data. *Bulletin of the American Meteorological Society*, 99(7), 1329–1336. https://doi.org/10.1175/BAMS-D-17-0277.1
- SAC (2014). *INSAT-3D data products format document*, version 1.1, SAC/IMDPS/SIPA/DPSG/MSDPD/TN-01. Space Applications Centre, ISRO. https://www.mosdac.gov.in/docs/INSAT3D_Products.pdf
- Snow, A. D., et al. pyproj: Python interface to PROJ. Zenodo. https://doi.org/10.5281/zenodo.2592232
- Vicente, G. A., Davenport, J. C., & Scofield, R. A. (2002). The role of orographic and parallax corrections on real time high resolution satellite rainfall rate distribution. *International Journal of Remote Sensing*, 23(2), 221–230. https://doi.org/10.1080/01431160010006935
