# Results and Discussion (draft)

*Draft of 26 Oct 2026, following `methods_draft.md` (Sections 2–4). Figures are `07_figures/paper/fig1`–`fig6`; citations as in the Methods reference list. All numbers come from `05_validation/` and match `pygeoparallax` v0.2.0. Offsets are GPM minus INSAT along the line of sight; positive means INSAT must move towards the satellite to match GPM.*

---

## 5 Results

### 5.1 Expected parallax over India

The parallax shift grows with distance from the sub-satellite point at 74°E (Fig. 1). For a 12 km cloud top it is about 2.5–3 km over the southern peninsula (VZA 12–15°), 5–7 km over central India (VZA 22–30°) and 8–9 km over the Himalaya and Northeast India (VZA 33–38°); for a 16 km top it reaches 11–12 km there. The shift points away from the satellite, which over India is roughly northwards; over the Northeast it turns towards the north-east (VAA up to 217°).

In the validation cases the correction moved deep convective cores (BT < 220 K) by a median of 4.2 km in South India, 7.3 km in Central India, 9.8 km over the Himalaya and 10.5 km over Northeast India (Table 2). These shifts follow tan(VZA) as expected; the solver itself agrees with pyproj, pyorbital and satpy to within 1 mm, 0.01° and 25 m respectively (Section 3).

### 5.2 INSAT-3DR navigation

Coastline matching shows that INSAT-3DR L1C positions carry a navigation error that changes with the season (Fig. 2). From late September to mid-March, positions need a correction of 7–20 km to the west; from mid-April to September the error is small. The switch near the equinoxes is consistent with the satellite's twice-yearly yaw flip.

During the monsoon the error cannot be measured reliably for a single day. Night-time matching fails because land and sea have almost the same TIR1 temperature (r < 0.4 for every night-time case scan). Daytime matching works, but the same coast in scans 1–2 h apart differs by about 9–10 km, and the best correlation is typically only 0.01–0.05 above the unshifted one. Of 199 daytime matches near the validation storms, 73 have r ≥ 0.6 and lie inside the search range. Pooling the 36 matches with r ≥ 0.7 gives a monsoon correction of −0.5 km east and +2.5 km north, which we adopt, with an uncertainty of about ±2 km. The median over all monsoon measurements across India (+1.8 km east, +4.8 km north) is used as a sensitivity test.

### 5.3 Validation cases

Of 33 coincident INSAT–GPM cases (GPM within 5 min of the INSAT scan at the storm; for the usable cases, median 1.3 min and at most 2.5 min), 30 could be processed. Of these, 9 had too little convection (fewer than 100 convective footprints in the main cluster) and 7 gave no reliable match; 14 cases were usable (Table 1). For the field measure, 12 cases give a reliable match in every correction state, and these 12 are used throughout.

**Table 1.** Validation cases.

| Region | VZA at storm | Cases | Not run (missing files) | Processed | Usable | Too little convection | No reliable match |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Northeast India | 31–39° | 11 | 1 | 10 | 5 | 3 | 2 |
| Himalaya | 29–37° | 12 | 1 | 11 | 4 | 6 | 1 |
| Central India | 24–26° | 4 | 0 | 4 | 2 | 0 | 2 |
| South India | 14–21° | 6 | 1 | 5 | 3 | 0 | 2 |
| **Total** | | **33** | **3** | **30** | **14** | **9** | **7** |

### 5.4 Effect of parallax correction

Parallax correction brings INSAT closer to GPM on average (Fig. 3, Table 2). For the storm-top field within 250 km of the main convective cluster, the median absolute offset falls from 5.5 km to 3.1 km and 10 of the 12 cases improve. The mean offset changes from +4.3 km to −0.9 km. Case by case, the absolute offset falls by a median of 1.6 km (95 % bootstrap interval 0.6–5.4 km); the improvement is significant by the sign test (p = 0.039) but not by the Wilcoxon signed-rank test (p = 0.13), so the evidence is moderate.

The correction acts only along the line of sight, as it should: the cross-look offset is the same before and after (median absolute 8.8 and 9.0 km; median change 0.0 km, 95 % interval −0.3 to +0.2 km). The cross-look scatter is therefore not a parallax effect but reflects storm structure, storm motion within the 1–2 min between the two observations, and the different quantities the two instruments see.

The gain is clearest at high viewing angles (Table 2). Over the Himalaya and Northeast India, where the deep cores moved by about 10 km, the mean offset moves from +2.0 and +5.2 km to −4.9 and −1.4 km. In South India, where the parallax is only 3–5 km, it changes from +6.2 to +4.9 km, within the case-to-case scatter.

**Table 2.** Line-of-sight offset (storm-top field, 250 km window) by region; mean over the cases valid in every state.

| Region | Cases | Mean VZA | Applied shift at deep cores, median [km] | Raw [km] | Parallax [km] | Navigation + parallax [km] |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| South India | 3 | 15° | 4.2 | +6.2 | +4.9 | +7.2 |
| Central India | 1 | 24° | 7.3 | +3.5 | −0.5 | +1.9 |
| Himalaya | 4 | 34° | 9.8 | +2.0 | −4.9 | −2.6 |
| Northeast India | 4 | 34° | 10.5 | +5.2 | −1.4 | −0.2 |
| **All** | **12** | | 9.8 | **+4.3** | **−0.9** | **+1.0** |

Applied shifts are medians over all 14 usable cases; offsets use the 12 cases valid in every state.

### 5.5 Parallax-only correction overshoots at storm cores

If the uncorrected offset were pure parallax, it would grow with tan(VZA), by about 10–12 km per unit tan(VZA) for deep convection. Across the 12 cases no such growth is visible (Spearman ρ = −0.03), but with so few cases the slope is poorly constrained (−4 km per unit tan(VZA), 95 % bootstrap interval −19 to +15 km), and a parallax-like trend cannot be excluded. The two offset measures give a clearer picture.

**Cell by cell** (Fig. 4), uncorrected INSAT cold cores already sit almost on top of GPM's deep-echo cells (median −0.1 km over 69 cells in 11 cases), and parallax correction moves them 5.7 km past (median −5.7 km; 95 % interval −8.2 to −2.2 km from a bootstrap that resamples cases, since cells of one storm are not independent). The **field correlation** sees the opposite sign before correction (+4.3 km) and lands near zero after it (−0.9 km). The two measures differ by a steady 4–5 km in every state. The field measure is driven by the large cold anvil against the rain area, the cell measure by the coldest tops against the tallest echoes.

Three sources of this behaviour were tested:

1. **GPM's slanted beam.** Placing storm tops on the slanted Ku beam instead of at the surface footprint (a median displacement of 1 km, up to 5 km) changes the cell medians by at most 0.6 km. It adds scatter, not bias.
2. **Cloud-top height.** In 95 matched cells, the BT-derived height of the INSAT cold core is 16.9 km (median), against a GPM maximum echo top of 12.45 km (Fig. 5); about half the cores sit at the tropopause. ERA5 profiles instead of the standard atmosphere give 16.75 km and change every offset by under 0.5 km. The gap between infrared cloud top and radar echo top is therefore physical: radar echo tops lie 1–3 km below the infrared top of deep convection. It accounts for about 1–2 km of the cell-measure overshoot.
3. **Navigation.** Adding the monsoon navigation correction moves the cell median from −5.7 to −4.1 km (per-case change +1.3 km, 95 % interval +0.5 to +1.9 km, Wilcoxon p = 0.002) and the field mean from −0.9 to +1.0 km (Fig. 4). Navigation thus accounts for about 1.5–3 km of the overshoot, depending on which monsoon estimate is used; the remaining cell overshoot (−4.1 km, interval −7.8 to −0.6 km) is still significant.

With navigation and parallax corrected together, the storm-top field gives the smallest median offset of any state: mean +1.0 km, median absolute 1.8 km (Table 3). This is a point estimate: with 12 cases it is not significantly better than parallax correction alone (4 of 12 cases improve; median change +1.1 km, 95 % interval −1.9 to +1.4 km; Wilcoxon p = 0.91), and its interval is wide (1.4–8.6 km). The cell measure remains at −4.1 km, so the two measures bracket zero, as they do only in the corrected states.

**Table 3.** Offsets in each correction state (12 cases for the field measure; 69–75 cells for the cell measure).

| State | Field mean [km] | Field median absolute [km] | Cases improved | Cells, median [km] |
| :--- | ---: | ---: | ---: | ---: |
| Raw | +4.3 | 5.5 | – | −0.1 |
| Navigation only | +6.3 | 7.6 | – | +0.1 |
| Parallax only | −0.9 | 3.1 | 10 of 12 | −5.7 |
| Navigation + parallax | **+1.0** | **1.8** | 7 of 12 | −4.1 |
| All-India navigation + parallax (sensitivity) | +3.8 | 4.7 | 6 of 12 | −3.3 |

### 5.6 Terrain

Terrain-aware correction with SRTM moves clear-sky ground by up to 3–4 km over the Himalaya and the Tibetan Plateau, 1–2 km over the Northeast hills and under 0.5 km over the Western Ghats and the Deccan (Fig. 6). In the Himalayan validation scenes, clear-sky ground pixels move by 1.3–2.5 km (median) and up to 5.8 km, and 9–19 % of grid cells change.

At the storms, terrain makes no difference: the field and cell offsets are identical to 0.1 km with and without it. Storm tops lie 10–17 km above the ground, so the height of the ground beneath them does not enter the correction.

### 5.7 Benchmark

The full pipeline processed all 148 available monsoon scenes without a failure. Per scene (reading two channels over 0–40°N, 60–100°E, cloud-top height, and the corrected and uncorrected grids at 0.04°) it took 1.8 s (median; 3.2 s at most) on a laptop, with about 450 MB of memory.

After correction, 98.7 % of grid cells hold an observed pixel, 1.3 % are filled from neighbours and 0.007 % stay empty behind tall clouds. Corrected clouds cover 2.5 % of previously clear cells (median). All other clear cells are identical in the corrected and uncorrected grids, so the two datasets differ only where clouds moved.

Fourteen scenes from 11–14 June 2023 turned out to be partial INSAT-3DR scans, with up to 57 % of the image missing. The pipeline handles them; the two validation cases on those dates are unaffected because their storms lie inside the scanned part.

---

## 6 Discussion

### 6.1 What the correction achieves

The ellipsoid ray-tracing correction is exact to well under the pixel size, and its effect on real data is the one geometry predicts: features move along the line of sight by h·tan(VZA), and nothing moves across it. Against GPM, the correction lowers the typical INSAT–radar offset from 5.5 to 3.1 km (10 of 12 cases improve; sign test p = 0.039), and together with the monsoon navigation correction gives a median of 1.8 km, although with 12 cases this further step is not statistically significant. The gain is largest where it matters most, over the Himalaya and Northeast India, where the parallax of deep convection (about 10 km) is two to three INSAT pixels.

### 6.2 Navigation partly masks the parallax

The most important finding for users of INSAT-3DR data is that a parallax-only correction overshoots at storm cores. In the monsoon, a navigation error of 2.5–5 km to the south partly offsets the northward parallax displacement, so uncorrected cold cores sit close to the radar cells (Section 5.5); the raw offset shows no visible growth with viewing angle, although 12 cases cannot exclude one.

Two practical consequences follow:
- Parallax and navigation should be corrected together. The navigation error is seasonal: small in the monsoon, but 7–20 km to the west from late September to mid-March, larger than the parallax itself. Users of INSAT-3DR outside the monsoon need the seasonal correction even more than the parallax correction.
- The monsoon navigation error cannot be measured for a single day from coastlines, because clouds hide the coasts and night-time land–sea contrast is too weak. A seasonal value, with its ±2 km uncertainty, is the best available. Other landmarks (lakes, rivers, islands) or ISRO's own navigation reports could reduce this uncertainty.

### 6.3 Which cloud height to use

Brightness-temperature heights put the coldest convective tops at the tropopause, about 4.4 km above the GPM echo tops, with either the standard atmosphere or ERA5. This is mainly physical: the infrared signal comes from the top of the cloud, while the radar sees large precipitation particles lower down. The consequence depends on the application:
- For **cloud products** (cloud masks, cloud-top properties), the infrared top is the right height, and the correction places the cloud where it is.
- For **precipitation products**, the rain-relevant level lies below the infrared top. Correcting with the full cloud-top height moves the cold signal slightly past the rain core, which may explain part of the remaining cell-measure offset. An effective height below the infrared top could fit precipitation better; we leave this to future work.

ISRO's operational cloud-top pressure product, by contrast, placed deep cores 2–3 km lower than the BT heights in our first case (Kochi, 6 June 2022; r = 0.86 overall) and was not used for the correction.

### 6.4 Terrain

Terrain does not affect the storm results but matters for anything observed at the ground in clear sky. Over the Himalaya, ellipsoid-navigated pixels of high terrain are misplaced by several kilometres; for land-surface temperature, snow cover or surface classification in mountains, terrain-aware correction should be standard.

### 6.5 Relation to earlier work

Vicente et al. (2002) showed that parallax and orographic corrections matter for satellite rainfall estimates from GOES; our results confirm the size of the effect for INSAT-3DR over India, where the high viewing angles over the Himalaya and the Northeast make it about 10 km for deep convection. The solver follows Bieliński (2020), extended here to terrain and to a navigation correction measured from coastlines. The GOES Hydro-Estimator has applied the Vicente et al. (2002) correction operationally since 2001, and satpy offers an open-source spherical-Earth correction for gridded geostationary data. To our knowledge, however, no parallax correction or validation has been published for INSAT-3D or INSAT-3DR.

ISRO's data-quality reports already measure INSAT-3DR geolocation error per image against ground control points; for a full-disk L1B image of 19 June 2020 they give a mean error of about 2.6 IR pixels to the north and 1.0 pixel to the west. Our coastline estimate for the 2022–2024 monsoon L1C data is smaller (2.5–5 km to the north) but has the same direction; the products, years and methods differ. What is new here is the multi-year seasonal behaviour of the L1C error and its interaction with the parallax: in the monsoon the two partly cancel, so a parallax-only correction overshoots, and the navigation error cannot be measured for a single day. *(See `00_Documentation/novelty_check.md`; confirm with a Google Scholar / Scopus search before submission.)*

### 6.6 Limitations

- **Sample size.** Fourteen usable cases (12 for the field measure) show that parallax correction improves the agreement (moderate evidence) and that it acts only along the line of sight (strong evidence). They are too few to show that adding the navigation correction improves the field measure further, to establish how the raw offset depends on viewing angle, or to give regional statistics; South and Central India have only 1–3 cases each.
- **One reference instrument.** Validation uses GPM only. GPM samples each storm once, in a 245 km swath, and its echo tops differ from infrared tops by definition. Ground-based radar (IMD Doppler Weather Radar) would add many more cases at fixed sites and is left for future work.
- **Two measures, one gap.** The field and cell measures differ by a steady 4–5 km because they compare different parts of the storm. We report both; the absolute residual offset is therefore uncertain by about ±2–3 km.
- **Navigation.** The monsoon navigation correction is a seasonal value with an uncertainty of about ±2 km; the yaw-flip explanation of its seasonal change is a hypothesis.
- **Cloud height.** Heights come from TIR1 brightness temperature, which underestimates thin cirrus and cannot resolve overshooting tops above the tropopause.

### 6.7 Effect on precipitation-type classification

*To be written after the U-Net comparison (Model A uncorrected vs Model B corrected, on the designed test set of 91 scenes).*

---

## Notes for revision

- Section 5.2: the 7–20 km winter value and the equinox timing come from `navigation_check.md`; cite the yaw-flip sources (ISRO, 2014; IMD SatMet SOP) as in the progress report.
- Section 6.3: the 1–3 km IR-top vs radar-echo-top difference needs a citation.
- Section 6.5: cite the MOSDAC DQE report (INSAT-3DR, 19 Jun 2020), the GOES Hydro-Estimator paper and satpy; check whether ISRO's Hydro-Estimator applies a parallax correction.
- Add Fig. 4 and Table 3 cross-references once the figure numbering is final.
