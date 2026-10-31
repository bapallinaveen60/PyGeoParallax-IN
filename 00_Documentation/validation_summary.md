# GPM Validation Summary

> This file records the validation as it grew, from the first 12–14 cases (2022–2024) to the full set of 63 cases, 38 usable (2018–2024). The opening sections describe the early cases; the final numbers are in the later sections on the full set and in `docs/validation.md`.

**The parallax correction is verified geometrically, and it improves INSAT–GPM alignment on average.** With the GPM storm-top field within 250 km, the median line-of-sight offset falls from 5.4 to 3.0 km and 10 of 12 cases improve; the cross-look offset is unchanged.

**In monsoon INSAT-3DR data, though, correcting parallax alone overshoots.** A cell-by-cell check puts uncorrected INSAT cold cores almost on top of GPM's deep-echo cells (median −0.1 km), and parallax correction moves them ~5.7 km past.

The overshoot breaks down roughly as follows:

| Source | Contribution |
| :--- | :--- |
| GPM's slanted beam | ~0 km (adds scatter only; now corrected) |
| BT cloud-top heights above the GPM echo tops | ~1–2 km |
| INSAT navigation error | ~3–4 km (consistent with the monsoon coastline measurements, ~5 km towards the satellite) |

Correcting navigation and parallax together is the most consistent choice. The two metrics then give +3.8 km (field) and −3.3 km (cells): they bracket zero, and the absolute residual is uncertain by about ±3–4 km.

## How to reproduce

```bash
python scripts/screen_gpm_convection.py --dir <folder> --cases <candidates.csv>
python scripts/run_all_cases.py --base <validation folder>
python scripts/test_navigation_parallax.py --base <validation folder>
python scripts/analyze_core_offsets.py --base <validation folder>
```

Outputs are in `05_validation/gpm_colocation/`: `all_cases.csv`, `nav_parallax_test.csv`, `core_offsets.csv` and `core_offsets_cells.csv`.

Setup:
- 0.02° grid
- cloud-top height from TIR1 BT with the AFGL tropical profile (capped at the 17 km tropopause)
- GPM 2A Ku V08, nearest footprint within 3.5 km
- **GPM storm tops placed on the slanted Ku beam** using the spacecraft position (`ingest.gpm.along_beam`; median 1 km, up to 5 km from the surface footprint)

Two independent offset metrics:
1. **Field correlation:** sub-cell best-correlation shift of −BT against GPM storm-top height (primary) or near-surface Z, within 150/250 km of the densest convective cluster. A result counts only if every match lies inside the ±10-cell search.
2. **Cell cores:** each GPM deep-echo cell (storm top > 10 km) paired with the INSAT cold core within 25 km.

## Cases (34 folders)

| Region | VZA | Usable | Too little convection | No reliable match | Not run |
| :--- | :--- | ---: | ---: | ---: | ---: |
| Northeast | 33–38° | 5 | 3 | 2 | 1 |
| Himalaya | 33–35° | 4 | 6 | 1 | 1 |
| Central India | 24–26° | 2 | 0 | 2 | 0 |
| South India | 14–17° | 3 | 0 | 2 | 1 |
| **Total** | | **14** | **9** | **7** | **3** |

Usable cases:
- **Northeast:** 18 Aug 2024, 8 Jun 2024, 7 Jun 2022, 20 Jul 2022, 13 Jun 2023
- **Himalaya:** 30 Jun 2023, 12 Sep 2023, 17 Sep 2023, 2 Jul 2024
- **Central:** 7 Sep 2023, 14 Jul 2024
- **South:** 11 Jul 2022, 11 Aug 2022, 12 Jun 2023

## Result 1: field correlation (parallax only)

| Field, window | Cases | Mean, raw → corrected [km] | Median absolute, raw → corrected [km] | Improved | Cross-look absolute, raw → corrected [km] |
| :--- | ---: | :--- | :--- | :--- | :--- |
| **Storm top, 250 km** | 12 | +4.3 → −0.9 | 5.4 → **3.0** | **10 of 12** | 7.8 → 7.9 |
| Storm top, 150 km | 11 | +5.3 → +0.4 | 5.4 → 4.1 | 7 of 11 | 6.9 → 6.8 |
| Rain Z, 250 km | 12 | +5.0 → −0.5 | 6.8 → 3.2 | 8 of 12 | 9.8 → 10.5 |
| Rain Z, 150 km | 10 | +5.2 → −0.2 | 5.8 → 3.4 | 7 of 10 | 8.4 → 8.3 |

Positive = INSAT must move towards the satellite to match GPM.

- **Viewing-angle dependence:** the raw offset does **not** grow with tan(VZA) (slope ≈ 0). By region (storm top, 250 km), raw → corrected:

  | Region | Raw [km] | Corrected [km] |
  | :--- | ---: | ---: |
  | South (~15°) | +6.0 | +4.9 |
  | Central (~25°) | +2.5 | −2.1 |
  | Himalaya (~34°) | +2.1 | −4.8 |
  | Northeast (~35°) | +5.5 | −1.1 |

  These are earlier-run means; they are similar in this run.
- **The gain is clearer at high VZA** (≥ 30°) than in South India, where the parallax is only 3–5 km.

## Result 2: cell cores (69–73 cells in 11 cases)

| State | Line-of-sight median [km] | Middle half of cells [km] | Cross-look median [km] |
| :--- | ---: | :--- | ---: |
| Raw | −0.1 | −5.7 … +7.0 | −0.7 |
| Navigation only | +0.9 | −3.7 … +8.2 | −0.6 |
| Parallax only | **−5.7** | −10.8 … +3.0 | −0.9 |
| Navigation + parallax | −3.3 | −8.5 … +5.7 | −0.8 |

## Result 3: navigation + parallax (field correlation, storm top, 250 km, 12 cases)

The navigation correction is the monsoon median: +1.8 km E, +4.8 km N.

| State | Mean [km] | Median absolute [km] |
| :--- | ---: | ---: |
| Raw | +4.3 | 5.4 |
| Navigation only | +9.2 | 10.4 |
| Parallax only | −0.9 | 3.0 |
| Both | +3.8 | 4.7 |

The two metrics differ by a steady 4–5 km. The field metric is driven by the cold anvil vs the rain area; the cell metric by the coldest tops vs the echo-top cells. Across them:
- **raw:** +4.3 / −0.1 km
- **parallax only:** −0.9 / −5.7 km
- **both:** +3.8 / −3.3 km, the only state that brackets zero.

## Explaining the overshoot

| Check | Result |
| :--- | :--- |
| **L1C pixel convention** | X/Y span the stated corners with one value per pixel (CF centres). A half-pixel corner error would show as a steady south-east correction in the coastline check; it does not. **Ruled out.** |
| **GPM slanted beam** | Storm tops now placed on the beam. Cell medians barely change (−0.2 → −0.1 raw, −5.1 → −5.7 corrected). **Scatter only, not a bias.** |
| **Cloud-top heights** | In 95 matched cells, INSAT cold-core height is 17.0 km (median; 52 % of cells at the 17 km cap, minimum BT ~193 K) against a GPM maximum echo top of 12.4 km: **+3.2 km**. Part of this is physical, since radar echo tops lie 1–3 km below IR cloud tops. At most it accounts for **~1.7 km** of extra shift. |
| **Navigation** | The monsoon coastline measurements give ~5 km towards the satellite along the line of sight. That matches the remaining ~3–4 km. Applying it (cells: −5.7 → −3.3 km) moves the offset the right way. |

## ERA5 profiles instead of the standard atmosphere

Cloud-top heights were recomputed with ERA5 temperature and geopotential (hour nearest the case scan, 29 levels 1000–50 hPa, interpolated to each pixel; `scripts/download_era5.py`, `compare_variants.py --variant era5`). **ERA5 does not change the result.**

| Measure | AFGL | ERA5 |
| :--- | ---: | ---: |
| INSAT cold-core height, median of 95 cells [km] | 16.9 | 16.75 |
| GPM maximum echo top, same cells [km] | 12.45 | 12.45 |
| Applied shift at deep cores, median [km] | 9.8 | 10.2 |
| Field, storm top 250 km (12 cases): parallax only, mean / median absolute [km] | −0.9 / 3.1 | −1.4 / 3.2 |
| Field, storm top 250 km: navigation + parallax, mean / median absolute [km] | +3.8 / 4.7 | +3.4 / 4.5 |
| Cells: parallax only, median [km] | −5.7 | −5.9 |
| Cells: navigation + parallax, median [km] | −3.3 | −3.2 |
| Cases improved by parallax correction (250 km) | 10 of 12 | 10 of 12 |

(AFGL medians differ by 0.1 km from the tables above because a case now counts only if both profiles give a valid match.)

- **Deep cores:** the coldest tops are colder than the ERA5 cold-point tropopause too, so both profiles put them at about 17 km. The standard atmosphere's cap is therefore not the cause of the high INSAT heights.
- **Mid-level clouds:** ERA5 puts them about 0.9 km higher than AFGL (Northeast 18 Aug 2024: bias against ISRO CTP −0.26 → +0.65 km). These do not drive the storm-core offsets.
- **So** the ~4.4 km gap between IR cloud tops and GPM echo tops is physical (radar echo tops lie below the IR top) rather than a profile error. The navigation error stays the main remaining uncertainty.

## Terrain (SRTM)

Terrain-aware correction (SRTM block-averaged to 0.01°; `scripts/prepare_srtm.py`, `compare_variants.py --variant dem`) **changes nothing at the storms**: field offsets (12 cases) and cell offsets (69–73 cells) are identical to 0.1 km in every state. Storm tops are 10–17 km above the ground, so the ground height under them does not matter. Terrain does move clear-sky ground: in Himalayan scenes by 1.3–2.5 km (median) and up to ~5.8 km, changing 9–19% of grid cells; in Central India by only ~0.15 km (median), up to 0.65 km.

Case scans are pinned in `00_Documentation/events/case_scans.csv`. Case folders now also hold navigation scans from neighbouring days, and a file-name rule alone picked a wrong scan for two cases without a CTP file.

## Navigation near the storms

Coastline matching was repeated on 57 extra daytime scans (case day 03:15–08:15 UTC, and the days before and after), in the four coastal windows nearest each case region (`scripts/near_storm_navigation.py`; all matches in `05_validation/nav_corrections/near_storm_matches.csv`).

- **Night scans do not work in the monsoon:** land and sea have nearly the same TIR1 temperature (r < 0.4 or search-edge matches on every night case scan). Only VIS matches are usable.
- **Per-case corrections are not reliable.** Of 199 daytime matches, 73 have r ≥ 0.6 and are not at the search edge, but the same coast in scans 1–2 h apart differs by ~9–10 km (robust spread), and the best correlation is typically only 0.01–0.05 above the unshifted one. Per-case medians correlate weakly with each case's leftover offset (r = 0.22 field, 0.26 cells) and do not reduce it.
- **Pooled, the near-storm matches give a smaller error than the monsoon median:** −0.5 km E, +2.5 km N (36 matches with r ≥ 0.7, not at the edge, |offset| ≤ 25 km), against +1.8 km E, +4.8 km N.

Re-running all cases with the pooled near-storm correction (`near_storm_pooled.json`, runs `<case>_pnav`):

| State | Field mean [km] | Field median absolute [km] | Improved vs raw | Cells median [km] |
| :--- | ---: | ---: | ---: | ---: |
| Raw | +4.3 | 5.5 | – | −0.1 |
| Parallax only | −0.9 | 3.1 | 10 of 12 | −5.7 |
| Monsoon navigation + parallax | +3.8 | 4.7 | 6 of 12 | −3.3 |
| **Near-storm navigation + parallax** | **+1.0** | **1.8** | 7 of 12 | −4.1 |

The near-storm correction with parallax gives the closest field agreement so far (median 1.8 km), while the cell measure moves from −5.7 to −4.1 km. The steady 4–5 km gap between the two measures remains; it comes from what each measures (anvil vs coldest tops), not from navigation. **The monsoon navigation error is 2.5–5 km north, uncertain by about ±2 km, and cannot be fixed per day from coastlines.** Navigation therefore explains roughly 1.5–3 km of the cell overshoot, BT heights 1–2 km, and the rest is the field-vs-cell definition.

## Statistics (12 cases)

`scripts/validation_statistics.py`: 95 % bootstrap intervals (10 000 resamples of cases), Wilcoxon signed-rank and exact sign tests on paired absolute offsets; for cells, a cluster bootstrap over cases (cells of one storm are not independent). Output: `05_validation/statistics/statistics.json`.

| Comparison (field measure, storm top 250 km) | Median change in absolute offset [km] | 95 % interval | Improved | Wilcoxon p | Sign p |
| :--- | ---: | :--- | ---: | ---: | ---: |
| Raw → parallax | −1.6 | −5.4 … −0.6 | 10 of 12 | 0.13 | **0.039** |
| Raw → navigation + parallax | −2.3 | −4.3 … +1.3 | 7 of 12 | 0.23 | 0.77 |
| Parallax → navigation + parallax | +1.1 | −1.9 … +1.4 | 4 of 12 | 0.91 | 0.39 |
| Cross-look, raw → parallax | 0.0 | −0.3 … +0.2 | – | 0.91 | – |

| State | Field median absolute [km] (95 % interval) | Cells median [km] (95 % interval, cluster bootstrap) |
| :--- | :--- | :--- |
| Raw | 5.5 (4.2–7.9) | −0.1 (−3.6 … +4.7) |
| Parallax only | 3.1 (0.4–7.6) | −5.7 (−8.2 … −2.2) |
| Navigation + parallax | 1.8 (1.4–8.6) | −4.1 (−7.8 … −0.6) |

- **Supported:** the cross-look offset does not change (strong); parallax correction improves the field measure (moderate: the bootstrap interval excludes zero and the sign test is significant, the Wilcoxon test is not); in the cell measure, parallax correction overshoots significantly and adding navigation reduces the overshoot significantly (per-case change +1.3 km, p = 0.002) without removing it.
- **Not supported with 12 cases:** that navigation + parallax is better than parallax alone in the field measure (4 of 12 improve), and that the raw offset does not grow with viewing angle (Spearman ρ = −0.03, but the slope interval, −19 … +15 km per unit tan VZA, still includes the ~10 km expected from parallax alone).
- **Consequence:** report 1.8 km as a point estimate, not as a demonstrated improvement over parallax correction; more cases (batch 4) are needed to resolve the navigation and viewing-angle questions.

## Full set: 38 usable cases (2018–2024)

Batch 4 added 2018–2021 cases over South and Central India (50 GPM passes screened, 37 passed, 33 runnable, 24 usable). Totals: **63 cases processed, 38 usable** (South 14, Central 15, Himalaya 4, Northeast 5); 30 give a reliable field match in every state, 27–28 have matched cells. Navigation is now each year's pooled monsoon value from daytime coastline matches near the cases (`scripts/yearly_navigation.py`; 2018 has too few matches and uses the all-years value, +0.5 km E, +1.5 km N). The per-year values are small: east −2.0 … +3.0 km, north −0.8 … +2.5 km.

| Measure | Raw | Parallax only | Navigation + parallax |
| :--- | :--- | :--- | :--- |
| Field, median absolute [km] (95 % interval), 30 cases | 5.1 (3.4–7.0) | 3.8 (2.6–6.7) | 4.3 (3.0–6.5) |
| Field, cases improved vs raw | – | 18 of 30 (sign p = 0.36) | 15 of 30 |
| Cells, median [km] (cluster bootstrap), 27–28 cases | −0.1 (−2.7 … +3.5) | **−4.7 (−6.8 … −0.9)** | −3.3 (−5.9 … +0.2) |
| Cross-look change, raw → parallax [km] | – | 0.0 (−0.2 … +0.2) | – |

- **The correction acts only along the line of sight** (cross-look unchanged): confirmed.
- **Parallax correction does not significantly improve the field agreement** with 30 cases (18 of 30 improve; median change −1.1 km, interval −1.6 … +1.2). The earlier 12 cases (10 of 12 improved) were favourable; the new Central India cases are not (6 of 12).
- **Uncorrected INSAT cold cores already sit on the GPM deep-echo cells**, in both periods (2018–21: −1.1 km; 2022–24: +0.8 km) and in every region, and parallax correction moves them 4–7 km past (p < 0.001).
- **Only about 5 % of the computed parallax is visible** between uncorrected cold cores and GPM cells (median of the per-case ratio of raw cell offset to applied shift: 0.05, 95 % interval −0.47 … +0.55). The raw field offset does not grow with viewing angle (slope −0.8 km per unit tan VZA, interval −12.9 … +9.4), which now **excludes** the ~10–12 km expected for deep convection.
- **Navigation does not explain it:** the measured monsoon navigation error is ~1–2.5 km, far smaller than the 4–10 km of parallax that is not visible.
- **The L1C metadata gives no hint of a parallax or height correction** in ISRO's processing (WGS84 datum, nominal altitude 36 000 km).

### Investigation (26 Oct 2026)

1. **The comparison method is correct.** A synthetic storm with a known parallax, put through the same gridding and cell-matching code, gives a raw offset equal to the full parallax (+10.9 km measured vs +10.5 km expected at VZA 35°; +9.1 vs +8.6; +3.5 vs +3.9 at VZA 15°) and about 0 after correction. INSAT and GPM grids share the same row order, and the sign chain (VAA = bearing to the satellite; along-look positive = INSAT must move towards the satellite) is consistent.
2. **Overlays confirm it visually** (`scripts/check_parallax_visibility.py`, `07_figures/checks/*_visibility.png`): uncorrected cold cloud masses sit on the GPM deep-echo cells, not ~10 km away from the satellite where geometry places them; after correction the cells lie on the clouds' far edges. Raw cold cores are closer to the GPM cells than to the expected apparent positions in every case with matched cells.
3. **The monsoon coastline navigation cannot fix the north–south component.** North estimates from different coasts range from −2.5 km (Chennai) to +8.8 km (Kutch), with 5–8 km spread within a coast. A south bias of ~7 km would cancel the median applied shift (7.2 km).
4. **ISRO's own geolocation checks support a large navigation error towards the satellite.** MOSDAC data-quality reports for five INSAT-3DR full-disk L1B images on 19 June 2020 (ground control points north-west of India) give positions that must move **1.7–2.7 IR pixels north and 1.0–3.3 pixels west**, i.e. roughly 7–11 km north and 4–13 km west (4 km IR pixels). Our coastline value for the 2020 monsoon is −1.0 km E, 0.0 km N. (L1B vs our L1C, and control points outside the storm regions, so this is supporting evidence, not proof.)
5. **GPM itself gives a navigation estimate:** after parallax correction the cells are offset by −4.7 km (95 % interval −6.8 … −0.9) along the line of sight, i.e. INSAT positions sit ~5 km towards the satellite.

6. **Navigation measured against GPM, tested leave-one-case-out** (`scripts/gpm_navigation.py`, runs `<case>_gnav`): the median cell offset after parallax correction of all *other* cases gives +5.0 km E (95 % interval +1.4 … +5.8) and +5.8 km N (+2.9 … +8.7). Applied to each case:

   | | Raw | Parallax only | GPM navigation + parallax |
   | :--- | ---: | ---: | ---: |
   | Cells, median [km] | −0.1 | −4.7 | −0.5 (−2.6 … +2.9) |
   | Field, median absolute [km] (31 cases) | 4.8 | 3.7 | 6.0 (4.1 … 7.8) |
   | Field, cases improved vs raw | – | 18 of 31 | 10 of 31 (Wilcoxon p = 0.027, worse) |

   It centres the cell measure but makes the field measure significantly worse. A real navigation error would shift both measures together, so **the ~5 km gap between them is not navigation.** (The east component also disagrees with ISRO's June 2020 reports, which point west.)

**Conclusion of the investigation:** the INSAT–GPM comparison is limited by storm structure, not by the correction or by navigation alone. At the scale of the whole storm (field measure), parallax correction removes the bias (mean +2.1 → −1.9 km) but the per-case improvement is not significant. At the scale of the coldest cores (cell measure), uncorrected cold cores already coincide with the radar's deep-echo cells, and correcting them with the full brightness-temperature height (median 16.6 km over 206 cells, 46 % at the 17 km cap) overshoots by ~5 km. The coldest infrared tops and the deepest radar echoes are not the same physical target, and the ~5 km difference between the two measures is as large as the parallax being tested. A GPM-based validation of absolute position is therefore limited to about ±3–5 km for monsoon convection.

**Status:** this is the most important result of the validation. The paper is reframed around it (26 Oct 2026): title "Parallax correction of INSAT-3DR imagery over India: an open-source tool and the limits of validation against GPM radar"; Results 5.4–5.6 and Discussion 6.1–6.3 rewritten for the 38 cases; new Fig. 3 (raw offset against applied shift) and Fig. 4 with the GPM-navigation state; statistics in `05_validation/statistics/statistics_ynav.json` and `statistics_gnav.json`. Candidate explanations to test: (1) an undocumented height reference or correction in INSAT-3DR L1C geolocation; (2) a systematic storm-structure offset between the coldest IR tops and the radar's deep-echo cells along the line of sight; (3) a problem in the comparison method. Checks: visual overlays of raw INSAT and GPM for high-VZA cases; an independent geostationary view of the same storms (e.g. Meteosat IODC at 45.5°E, which sees the parallax in a different direction); asking ISRO/SAC how L1C geolocation is done.

## For the paper (38 cases; manuscript reframed 26 Oct 2026)

1. **Geometry verified:** pyproj, pyorbital and satpy agree. The correction moves features only along the line of sight (cross-look change 0.0 km, −0.2 … +0.2).
2. **Storm scale:** the mean field offset reverses (+2.2 → −1.9 km), but the per-case gain is not significant (18 of 30, sign p = 0.36).
3. **Cores:** uncorrected cold cores already sit on the GPM cells (−0.1 km); only ~5 % of the computed parallax is visible; correction overshoots by ~4.7 km.
4. **Navigation alone cannot explain it:** the field and cell measures differ by 2–3 km (coastline navigation) and ~5 km once navigation is fitted to the cells; no single translation centres both. GPM validation of absolute position is limited to about ±3–5 km.
5. **Heights:** IR cold-core heights (16.6 km median) lie ~3.2 km above the GPM echo tops with either profile; ERA5 and SRTM change the storm results by < 0.5 km (14 cases of 2022–2024).

## Next

- U-Net Model A vs Model B (Colab) as the application test.
- More Himalaya and Northeast cases (4–5 usable each).
- An independent view (Meteosat IODC at 45.5°E) or ground radar to separate storm structure from navigation.
