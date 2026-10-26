# Results and Discussion (draft)

*Draft of 26 Oct 2026, reframed for the full set of 38 usable cases (2018–2024), following `methods_draft.md` (Sections 2–4). Figures are `07_figures/paper/fig1`–`fig6`; citations as in the Methods reference list. Numbers come from `05_validation/` (statistics: `05_validation/statistics/statistics_ynav.json` and `statistics_gnav.json`) and `pygeoparallax` v0.2.1. Offsets are GPM minus INSAT along the line of sight; positive means INSAT must move towards the satellite to match GPM.*

---

## 5 Results

### 5.1 Expected parallax over India

The parallax shift grows with distance from the sub-satellite point at 74°E (Fig. 1). For a 12 km cloud top:

- about 2.5–3 km over the southern peninsula (VZA 12–15°);
- 5–7 km over central India (VZA 22–30°);
- 8–9 km over the Himalaya and Northeast India (VZA 33–38°); for a 16 km top it reaches 11–12 km there.

The shift points away from the satellite, which over India is roughly northwards; over the Northeast it turns towards the north-east (VAA up to 217°).

In the validation cases the correction moved deep convective cores (BT < 220 K) by a median of:

- 3.9 km in South India;
- 7.3 km in Central India;
- 9.8 km over the Himalaya;
- 10.5 km over Northeast India.

The median over all usable cases is 7.2 km. These shifts follow tan(VZA) as expected. The solver itself agrees with pyproj, pyorbital and satpy to within 1 mm, 0.01° and 25 m respectively (Section 3).

### 5.2 INSAT-3DR navigation

Coastline matching shows that INSAT-3DR L1C positions carry a navigation error that changes with the season (Fig. 2). From late September to mid-March, positions need a correction of 7–20 km to the west. From mid-April to September the error is small. The switch near the equinoxes is consistent with the yaw flip of the INSAT-3D-series spacecraft, a 180° rotation about the yaw axis in March and September of every year [Prakash et al., 2014].

During the monsoon the error cannot be measured reliably for a single day:

- Night-time matching fails because land and sea have almost the same TIR1 temperature (r < 0.4 for every night-time case scan).
- Daytime matching works, but the same coast in scans 1–2 h apart differs by about 9–10 km. The best correlation is typically only 0.01–0.05 above the unshifted one.

Pooling the reliable daytime matches near the validation storms of each monsoon gives small corrections: −2.0 to +3.0 km east and −0.8 to +2.5 km north. 2018 had too few matches, so it uses the all-years value, +0.5 km east and +1.5 km north. These per-year values are used as the navigation correction.

The north component, which matters most for the parallax over India, is only weakly constrained. Individual coasts give anything from −2.5 km (Chennai) to +8.8 km (Kutch), with 5–8 km spread within one coast.

### 5.3 Validation cases

We processed 63 coincident INSAT–GPM cases from the monsoons of 2018–2024. GPM was within 5 min of the INSAT scan at the storm; for the usable cases the median was 1.0 min and the maximum 2.9 min.

- 38 cases are usable (Table 1).
- 9 had too little convection (fewer than 100 convective footprints in the main cluster).
- 16 gave no reliable match in any field or window.

The usable cases span all seven years (3–7 per year). In the field measure, 30 cases give a reliable match in every correction state, and these 30 are used for paired comparisons. In the cell measure, 157–167 GPM deep-echo cells in 27–28 cases are matched to an INSAT cold core in each state.

**Table 1.** Validation cases, 2018–2024.

| Region | VZA at storm | Processed | Usable | Too little convection | No reliable match |
| :--- | :--- | ---: | ---: | ---: | ---: |
| South India | 9–21° | 17 | 14 | 0 | 3 |
| Central India | 22–33° | 25 | 15 | 0 | 10 |
| Himalaya | 29–37° | 11 | 4 | 6 | 1 |
| Northeast India | 31–38° | 10 | 5 | 3 | 2 |
| **Total** | | **63** | **38** | **9** | **16** |

### 5.4 Storm-scale offsets

The correction acts only along the line of sight, as it should. The cross-look offset does not change (median change 0.0 km, 95 % interval −0.2 to +0.2 km, 30 cases). Cross-look scatter therefore reflects storm structure, storm motion within the up to 3 min between the two observations, and the different quantities the two instruments see. It is not a parallax effect.

Along the line of sight, parallax correction reverses the mean storm-top field offset (Table 2): the mean moves from +2.2 km (95 % interval +0.1 to +4.2 km) to −1.9 km (−4.2 to +0.3 km). The median absolute offset falls from 5.1 to 3.8 km. Case by case, however, the improvement is not significant:

- 18 of 30 cases improve;
- the median change is −1.1 km (95 % interval −1.6 to +1.2 km);
- sign test p = 0.36, Wilcoxon signed-rank p = 0.66.

Adding the per-year coastline navigation changes little: the mean is −1.0 km and the median absolute offset 4.3 km, with 17 of 30 cases better than parallax alone (p = 0.58).

**Table 2.** Mean line-of-sight offset of the storm-top field (250 km window) by region; cases valid in every state.

| Region | Cases | Mean VZA | Applied shift at deep cores, median [km] | Raw [km] | Parallax [km] | Navigation + parallax [km] |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| South India | 10 | 15° | 3.9 | +2.6 | +1.1 | +1.8 |
| Central India | 12 | 27° | 7.3 | +0.9 | −3.5 | −2.7 |
| Himalaya | 4 | 34° | 9.8 | +2.0 | −4.9 | −4.3 |
| Northeast India | 4 | 34° | 10.5 | +5.2 | −1.4 | +0.8 |
| **All** | **30** | | 7.2 | **+2.2** | **−1.9** | **−1.0** |

Applied shifts are medians over all 38 usable cases; offsets use the 30 cases valid in every state.

### 5.5 Most of the expected parallax is not visible against GPM

If the uncorrected INSAT–GPM offset were pure parallax, it would equal the shift that the correction applies. It would grow from about 4 km in South India to about 10 km over the Himalaya and the Northeast. Neither measure shows this (Fig. 3).

- **Field measure.** The raw offset does not grow with viewing angle: Spearman ρ = −0.01, slope −0.8 km per unit tan(VZA), 95 % interval −12.9 to +9.4 km. With 30 cases the upper bound (+9.4 km) lies just below the 10–12 km per unit tan(VZA) expected for deep convection. Against the applied shift, the fitted slope is −0.03 (Fig. 3a).
- **Cell measure.** Uncorrected INSAT cold cores already sit almost on top of GPM's deep-echo cells: median −0.1 km, 95 % interval −2.7 to +3.5 km, from a cluster bootstrap over cases. Regional medians stay within ±3 km of zero (South −2.6, Central +1.7, Himalaya −1.6, Northeast +0.4 km), and so do both periods (2018–2021 and 2022–2024). Parallax correction moves them past the cells to −4.7 km (−6.8 to −0.9 km); the per-case change is −4.5 km (p < 0.001). The median per-case ratio of raw cell offset to applied shift is 0.05 (95 % interval −0.47 to +0.55): only about 5 % of the computed parallax is visible. A least-squares fit of the case medians against the applied shift has a slope of +0.22 (Fig. 3b; the median of the case medians is +0.1 km).

Table 3 summarises both measures in each correction state.

**Table 3.** Offsets in each correction state (30–31 cases for the field measure; 157–167 cells in 27–28 cases for the cell measure).

| State | Field mean [km] | Field median absolute [km] | Field cases improved vs raw | Cells, median [km] (95 % interval) |
| :--- | ---: | ---: | ---: | :--- |
| Raw | +2.2 | 5.1 | – | −0.1 (−2.7 … +3.5) |
| Parallax only | −1.9 | 3.8 | 18 of 30 | −4.7 (−6.8 … −0.9) |
| Coastline navigation + parallax | −1.0 | 4.3 | 15 of 30 | −3.3 (−5.9 … +0.2) |
| GPM navigation + parallax (leave one out) | +4.9 | 6.0 | 10 of 31 | −0.5 (−2.6 … +2.9) |

The GPM-navigation row uses the 31 cases valid in its own states; in that set the raw field offset is +2.1 km (median absolute 4.8 km) and the parallax-only offset −1.9 km (3.7 km).

### 5.6 Why the parallax is not visible

We tested four explanations in turn.

1. **The comparison method.** We put a synthetic storm with a known parallax through the same gridding and cell-matching code. The raw offset equals the full parallax: +10.9 km measured against +10.5 km expected at VZA 35°, and +3.5 against +3.9 km at VZA 15°. After correction it is about zero. Overlays of uncorrected INSAT on GPM storm tops for six high-angle cases show the same as the statistics: the cold cloud masses sit on the deep-echo cells, not 8–10 km beyond them. The method detects parallax when it is there.
2. **GPM's slanted beam.** Placing storm tops on the slanted Ku beam instead of at the surface footprint changes the cell medians by at most 0.6 km. This displacement has a median of 1 km and reaches 5 km. It adds scatter, not bias.
3. **Cloud-top height.** In 206 matched cells (29 cases) the BT-derived height of the INSAT cold core has a median of 16.6 km, and 46 % of the cores reach the 17 km tropopause cap. The GPM maximum echo top in the same cells has a median of 11.9 km, and the median difference per cell is 3.2 km (Fig. 5). In the 14 cases of 2022–2024, ERA5 profiles instead of the standard atmosphere changed cold-core heights by −0.15 km and every offset by less than 0.5 km. The gap between infrared top and radar echo top is therefore physical: GPM's storm top is the highest range bin with echo above the Ku-band detection threshold (about 14.5–18 dBZ) [Hou et al., 2014; Toyoshima et al., 2015], and the small ice particles at the top of deep convection lie below it. The gap inflates the shift at the rain core by about 1–2 km. It cannot hide 4–10 km.
4. **Navigation.** A navigation error towards the satellite would cancel part of the parallax and shift both measures by the same amount.
   - **Coastline values.** The per-year values are only −0.8 to +2.5 km to the north.
   - **ISRO's data-quality reports.** For five full-disk L1B images of 19 June 2020, measured at ground control points north-west of India, positions must move 1.7–2.7 IR pixels north and 1.0–3.3 pixels west. With 4 km IR pixels that is roughly 7–11 km north, enough to cancel most of the parallax.
   - **Navigation fitted to GPM.** We tested this directly by estimating the navigation from GPM itself. Each case got the median cell offset after parallax correction of all other cases (leave one out): +5.0 km east (95 % interval +1.4 to +5.8 km) and +5.8 km north (+2.9 to +8.7 km).

   The GPM-fitted navigation centres the cell measure (−0.5 km) but pushes the field measure to +4.9 km and makes it worse than uncorrected (Table 3, Fig. 4):
   - median absolute offset 6.0 km;
   - 10 of 31 cases better than raw;
   - Wilcoxon p = 0.027, sign test p = 0.07; against parallax only, p = 0.28.

   **No single translation centres both measures.** The field and cell measures differ by 2–3 km in the raw and coastline-navigation states, and by about 5 km once the navigation is fitted to the cells. Navigation alone therefore cannot explain the result; we attribute the difference mainly to storm structure. The east component of the fitted value also disagrees with ISRO's reports, which point west.

The two measures compare different parts of the storm. The field measure is driven by the large cold anvil against the radar's rain area, and the cell measure by the coldest tops against the tallest echoes. Their difference, 2–3 km and up to about 5 km depending on the navigation applied, is comparable to the parallax over South India and a third to a half of it at higher viewing angles. At the scale of the storm, parallax correction reverses the mean bias, and the corrected mean is not significantly different from zero. At the scale of the convective core, uncorrected cold cores already coincide with the radar cells, and correcting them with the full infrared height overshoots.

### 5.7 Terrain

Terrain-aware correction with SRTM moves clear-sky ground by:

- up to 3–4 km over the Himalaya and the Tibetan Plateau;
- 1–2 km over the Northeast hills;
- under 0.5 km over the Western Ghats and the Deccan (Fig. 6).

In the Himalayan validation scenes, clear-sky ground pixels move by 1.3–2.5 km (median) and up to 5.8 km, and 9–19 % of grid cells change.

At the storms (14 cases of 2022–2024), terrain makes no difference: the field and cell offsets are identical to 0.1 km with and without it. Storm tops lie 10–17 km above the ground, so the height of the ground beneath them does not enter the correction.

### 5.8 Benchmark

The full pipeline processed all 148 available monsoon scenes without a failure. Each scene took 1.8 s (median; 3.2 s at most) on a laptop, with about 450 MB of memory. Processing includes reading two channels over 0–40°N, 60–100°E, cloud-top height, and the corrected and uncorrected grids at 0.04°.

After correction:

- 98.7 % of grid cells hold an observed pixel, 1.3 % are filled from neighbours and 0.007 % stay empty behind tall clouds;
- corrected clouds cover 2.5 % of previously clear cells (median);
- all other clear cells are identical in the corrected and uncorrected grids, so the two datasets differ only where clouds moved.

Fourteen scenes from 11–14 June 2023 turned out to be partial INSAT-3DR scans, with up to 57 % of the image missing. The pipeline handles them. The two validation cases on those dates are unaffected because their storms lie inside the scanned part.

---

## 6 Discussion

### 6.1 What the correction does, and what GPM can verify

The ellipsoid ray-tracing correction is exact to well under the pixel size, and on real data it does what geometry predicts. Features move along the line of sight by h·tan(VZA), and nothing moves across it: the cross-look offset changes by a median of 0.0 km (95 % interval −0.2 to +0.2 km). At the scale of whole storms it reverses the mean INSAT–GPM bias, from +2.2 to −1.9 km.

What GPM cannot do is confirm that the corrected positions are more accurate than the uncorrected ones. With 38 usable cases over seven monsoons:

- the per-case improvement in the field measure is not significant;
- the cell measure says the uncorrected cores were already in place.

The two measures disagree with each other by 2–3 km, and by about 5 km once navigation is fitted to one of them, so a GPM-based validation of absolute position is limited to about ±3–5 km for monsoon deep convection. That is comparable to the parallax over South and Central India, and a third to a half of it over the Himalaya and the Northeast. The 12-case result we obtained first (10 of 12 cases improving) did not hold up in the larger sample. This is a caution for validation studies based on a few overpasses.

### 6.2 Why the coldest tops and the deepest echoes coincide

For the uncorrected cold cores to sit on the radar cells, the coldest infrared top of a cell must lie, on average, a parallax-sized distance towards the satellite (south) of the deep echo beneath it. We see three non-exclusive explanations:

- **Storm structure.** Monsoon convection over India is organised in large systems whose deep echoes reach 17 km and whose stratiform and anvil regions extend over hundreds of kilometres [Houze et al., 2007; Romatschke & Houze, 2011]. The coldest top of such a system need not lie vertically above its deepest radar echo: updraft tilt in the strong easterly shear of the monsoon, and anvil spreading, could displace it by several kilometres. A systematic southward component would cancel the northward parallax. We are not aware of a measurement of this offset for monsoon storms, so it remains a hypothesis.
- **Effective height.** The cold core seen at 10.8 µm is the cloud top at the tropopause (16.6 km median), about 3 km (median 3.2 km) above the radar echo top. If the radiating top of the core is spatially offset from the echo core, the full infrared height is the wrong height for matching rain.
- **Navigation.** ISRO's own geolocation checks for June 2020 point to an error of 7–11 km towards the north, which would hide most of the parallax. Coastlines cannot confirm it in monsoon cloud, and fitting the navigation to GPM breaks the field measure. We cannot exclude a navigation contribution, but navigation alone cannot reconcile the two measures.

An independent geostationary view of the same storms, for example Meteosat IODC at 45.5°E, which sees the parallax in a different direction, would separate these explanations. So would ground radar at known positions. Both are left for future work.

### 6.3 Navigation

The INSAT-3DR L1C navigation error is seasonal: 7–20 km to the west from late September to mid-March. This is larger than the parallax, and outside the monsoon it is the dominant geolocation error. In the monsoon the coastline method gives small values (−2.0 to +3.0 km east, −0.8 to +2.5 km north per year) but cannot constrain the north component better than several kilometres, and it cannot be applied per day. Users should apply the seasonal correction outside the monsoon, and should not fit navigation to radar cells: Section 5.6 shows that doing so absorbs storm structure into the navigation and degrades storm-scale agreement.

### 6.4 Which cloud height to use

Brightness-temperature heights put the coldest convective tops at the tropopause, a median 3.2 km above the GPM echo tops, with either the standard atmosphere or ERA5. This is mainly physical: the infrared signal comes from the top of the cloud, while the Ku-band radar detects only precipitation-sized particles, with a threshold of about 14.5–18 dBZ [Toyoshima et al., 2015].

- For **cloud products** (cloud masks, cloud-top properties), the infrared top is the right height, and the correction places the cloud top where geometry says it is.
- For **precipitation products**, the rain-relevant level lies below the infrared top, and our cell results suggest that correcting cores with the full infrared height moves the cold signal past the rain. An effective height between the echo top and the infrared top could suit precipitation better.

The effect on a precipitation-type classifier is being tested (Section 6.8).

ISRO's operational cloud-top pressure product placed deep cores 2–3 km lower than the BT heights in our first case (Kochi, 6 June 2022; r = 0.86 overall). It was not used for the correction.

### 6.5 Terrain

Terrain does not affect the storm results but matters for anything observed at the ground in clear sky. Over the Himalaya, ellipsoid-navigated pixels of high terrain are misplaced by several kilometres. For land-surface temperature, snow cover or surface classification in mountains, terrain-aware correction should be standard.

### 6.6 Relation to earlier work

Vicente et al. (2002) showed that parallax and orographic corrections matter for satellite rainfall estimates from GOES. Since 2001, the GOES Hydro-Estimator has applied their correction operationally. Bieliński (2020) derived the ellipsoid solution that our solver follows; we extend it to terrain and to a navigation correction. satpy offers an open-source spherical-Earth correction for gridded geostationary data. For Meteosat SEVIRI, Wiltink et al. (2025) compared geometric parallax correction with an empirical shift that maximises the correlation with ground observations, the idea behind our field measure. To our knowledge, no parallax correction or validation has been published for INSAT-3D or INSAT-3DR.

Our results add a caution to radar-based validation of geostationary parallax correction. Where the expected parallax is a few kilometres, as for most of India, the measured improvement depends on which part of the storm is compared. Cell-scale comparisons can show the opposite of storm-scale ones. ISRO's data-quality reports already measure INSAT-3DR geolocation error per image against ground control points (for example, for 19 June 2020). Their June 2020 values point in the same northward direction as our cell result, but they are for L1B images, at control points outside the storm regions, and in one year.

### 6.7 Limitations

- **Reference instrument.** Validation uses GPM only. GPM samples each storm once, in a 245 km swath. Its echo tops differ from infrared tops by definition, and the two offset measures differ by 2–5 km depending on the navigation applied. Ground-based radar (IMD Doppler Weather Radar) at fixed sites, or a second geostationary view, would be needed to verify absolute positions to better than this.
- **Sample by region.** South and Central India have 14–15 usable cases each, but the Himalaya and Northeast India only 4–5. Regional means at high viewing angles rest on few cases.
- **Navigation.** The monsoon navigation correction is a per-year value whose north component is uncertain by several kilometres. The link between the seasonal change and the yaw flip rests on timing only.
- **Sensitivity tests.** ERA5 profiles and SRTM terrain were tested on the 14 cases of 2022–2024 only.
- **Cloud height.** Heights come from TIR1 brightness temperature. This underestimates thin cirrus, caps overshooting tops at the tropopause, and does not give the effective height relevant for precipitation.

### 6.8 Effect on precipitation-type classification

*In progress.* The group's attention U-Net for precipitation type is trained on 128 × 128 patches of four INSAT-3DR channels (TIR1, TIR2, WV, MIR), with GPM DPR precipitation type as label. It is being retrained twice, with identical architecture, labels, pixel mask, initial weights and training schedule:

- **Model A** on the original (uncorrected) patches;
- **Model B** on the same patches after parallax correction on their own pixel grid.

The data are 5,082 training patches from 823 scenes (2018, 2021–2023) and 2,197 test patches from 347 scenes (September 2023, 2024). The correction moves cloud by a median of 4.4 km per patch, about one pixel, and changes TIR1 by more than 1 K on 34 % of pixels. Because GPM labels are at ground positions, only the input differs between A and B. The comparison (accuracy, macro F1, per-class CSI, with a paired bootstrap over test scenes) is the application test of Section 6.4. Results will be added here.

---

## Notes for revision

- Section 6.6: check whether ISRO's Hydro-Estimator applies a parallax correction (MOSDAC ATBD); run a Google Scholar / Scopus novelty search.
- Section 6.8: fill in after the Colab runs (`compare_unet_ab.py` output).
