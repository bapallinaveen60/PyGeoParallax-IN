# GPM Validation Summary (4 regions, 14 usable cases)

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

## For the paper

1. **Geometry verified:** pyproj, pyorbital and satpy agree. The correction moves features by the computed amount along the line of sight and leaves the cross-look offset unchanged, in every field, window and metric.
2. **Agreement with GPM improves on average** (storm top: median 5.4 → 3.0 km, 10 of 12 cases).
3. **In monsoon INSAT-3DR data the parallax displacement is partly masked by a navigation error of similar size.** Correct both; the absolute residual is uncertain by about ±3–4 km, and case scatter is 4–6 km.
4. **BT-based heights for the coldest tops sit at the tropopause, about 17 km, with either profile.** ERA5 instead of the standard atmosphere changes the offsets by under 0.5 km, so the IR–radar height gap is physical, not a profile error.

## Next

- **Navigation for the paper:** use the pooled near-storm correction (−0.5 km E, +2.5 km N) as the monsoon default and quote ±2 km; same-day corrections are not reliable in monsoon cloud.
- **More South and Central India cases** (only 2–3 usable each).
