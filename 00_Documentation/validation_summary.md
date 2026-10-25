# GPM Validation Summary (4 regions, 15 usable cases)

**Parallax correction improves INSAT–GPM alignment on average.** With the storm-top field within 250 km, the median line-of-sight offset falls from 5.4 to 3.5 km and 9 of 13 cases improve; the cross-look offset is unchanged. The effect is strongest at high viewing angles (VZA ≥ 30°: 5.5 → 2.8 km, 6 of 8 improve).

**But the uncorrected offset does not grow with viewing angle,** and a cell-by-cell check finds INSAT's coldest pixels already sitting on GPM's deep-echo cells **before** correction (median −0.2 km); parallax correction alone moves them ~5 km past (−5.1 km). Both methods agree that, in monsoon INSAT-3DR data, parallax correction alone overshoots relative to GPM. Only "parallax + navigation" falls on opposite sides of zero in the two methods (+3.7 / −3.2 km). The two methods differ by a steady ~4–5 km, so the absolute residual is uncertain by about ±3–4 km. See *Cell-by-cell check* below.

**Also:** the uncorrected offset All four regions show a positive line-of-sight offset of about +2 to +6 km before correction, including South India, where parallax is only ~3–5 km. So part of the INSAT–GPM offset is a viewing-angle-independent bias of unknown cause, not parallax. The earlier explanation (parallax and navigation errors cancelling) is incomplete. Claims in the paper should be stated with this residual bias (~±3–5 km) and case scatter (4–6 km) in mind.

Reproduce with:

```bash
python scripts/screen_gpm_convection.py --dir <folder> --cases <candidates.csv>
python scripts/run_all_cases.py --base <validation folder>
python scripts/test_navigation_parallax.py --base <validation folder>
```

Outputs: `05_validation/gpm_colocation/all_cases.csv` and `nav_parallax_test.csv`.

Setup:
- 0.02° grid
- cloud-top height from TIR1 BT with the AFGL tropical profile
- GPM 2A Ku V08, nearest footprint within 3.5 km
- offset = sub-cell best-correlation shift of −BT against a GPM field, within 150/250 km of the densest convective cluster
- **storm-top height is the primary field**; near-surface reflectivity Z is secondary
- a result counts only if every match it uses lies inside the ±10-cell search

## Cases (34 folders)

| Region | VZA | Usable | Excluded: too little convection | Excluded: no reliable match | Not run |
| :--- | :--- | ---: | ---: | ---: | ---: |
| Northeast | 33–38° | 5 | 3 | 2 | 1 |
| Himalaya | 33–35° | 4 | 6 | 1 | 1 |
| Central India | 24–26° | 2 (7 Sep 2023, 14 Jul 2024) | 0 | 2 | 0 |
| South India | 14–17° | 3 (11 Jul 2022, 11 Aug 2022, 12 Jun 2023) | 0 | 2 | 1 (25 Aug 2023: no 18:15 scan on MOSDAC) |

Usable Northeast and Himalaya cases are as in earlier runs: Northeast 18 Aug 2024, 8 Jun 2024, 7 Jun 2022, 20 Jul 2022, 13 Jun 2023; Himalaya 30 Jun 2023, 12 Sep 2023, 17 Sep 2023, 2 Jul 2024. Screening GPM first predicted convection correctly, but 6 of 15 screened cases with convection still gave no reliable match.

## Line-of-sight offset by region (storm-top field, 250 km)

Positive = INSAT must move towards the satellite to match GPM. Values are means per region.

| Region | Valid cases | VZA | Expected parallax shift (deep cores) | Raw | After parallax correction |
| :--- | ---: | ---: | :--- | ---: | ---: |
| South India | 3 | 15° | ~3–5 km | **+6.0** | +4.9 |
| Central India | 2 | 25° | ~7 km | +2.5 | −2.1 |
| Himalaya | 4 | 34° | ~9–10 km | +2.1 | −4.8 |
| Northeast | 4 | 35° | ~10–11 km | +5.5 | −1.1 |

Regressed against tan(VZA), the raw offset has slope ≈ 0 (r −0.1 to −0.4 across fields and windows). If parallax alone caused the raw offset, it would rise with tan(VZA) by roughly the cloud-top height (~10–15 km per unit of tan VZA). It does not.

## All cases, all fields

| Field, window | Cases | Mean raw → parallax-corrected [km] | Median absolute raw → corrected [km] | Improved | Cross-look absolute, raw → corrected [km] |
| :--- | ---: | :--- | :--- | :--- | :--- |
| Storm top, 250 km | 13 | +4.1 → −1.0 | 5.4 → **3.5** | 9 of 13 | 8.7 → 8.7 |
| Storm top, 150 km | 11 | +5.5 → +0.5 | 5.4 → 4.3 | 8 of 11 | 7.2 → 7.2 |
| Rain Z, 250 km | 10 | +3.9 → −1.7 | 6.8 → **2.9** | 6 of 10 | 7.7 → 8.6 |
| Rain Z, 150 km | 9 | +5.1 → +0.1 | 6.3 → 3.5 | 6 of 9 | 7.2 → 7.0 |

Split by viewing angle (storm top, 250 km):
- **VZA ≥ 30°** (8 cases): median 5.5 → 2.8 km, 6 of 8 improve.
- **VZA < 30°** (5 cases): median 3.9 → 3.7 km, 3 of 5 improve.

## Navigation test (monsoon median correction +1.8 km E, +4.8 km N)

Storm top, 250 km, 13 cases:

| State | Mean offset |
| :--- | ---: |
| Raw | +4.1 km |
| Navigation only | **+9.1 km** |
| Parallax only | −1.0 km |
| Both | +3.7 km |

- **High-VZA cases** (8): navigation alone gives +8.7 km, close to the parallax shift. That is what supported the "cancellation" idea.
- **Low-VZA cases:** navigation alone gives +6 to +16 km there too, far more than their parallax (3–7 km). So the navigation-corrected offset is **also roughly constant across viewing angles** (intercept ~+10 km, slope ≈ 0).
- **Conclusion:** either the monsoon navigation correction is wrong in its north component, or there is a separate, VZA-independent offset between INSAT cold cloud and GPM echoes. The north estimates came mostly from windows already flagged as suspect (Andhra, Goa: +12 km N in the monsoon). Earlier runs suggested the first explanation; this run cannot tell them apart.

## Cell-by-cell check (`scripts/analyze_core_offsets.py`)

This check is independent of field correlation:
- each GPM deep-echo cell (storm top > 10 km, ≥ 8 grid cells, inside the swath, within 250 km of the convective cluster) is paired with the INSAT cold core within 25 km (pixels within 3 K of the local minimum BT);
- the offset (GPM minus INSAT) is split along and across the line of sight.

68–73 cells in 11 cases; the two South India shallow-convection cases and Central 7 Sep 2023 had no deep cells.

| State | Line-of-sight median [km] | Middle half of cells [km] | Cross-look median [km] |
| :--- | ---: | :--- | ---: |
| Raw | −0.2 | −5.2 … +6.9 | −0.1 |
| Navigation only | +1.2 | −3.5 … +8.3 | −0.9 |
| Parallax only | **−5.1** | −10.6 … +2.6 | −0.7 |
| Navigation + parallax | −3.2 | −8.0 … +6.3 | −0.7 |

Side by side with the field correlation (storm top, 250 km, means):

| State | Field correlation [km] | Cell cores [km] |
| :--- | ---: | ---: |
| Raw | +4.1 | −0.2 |
| Parallax only | −1.0 | −5.1 |
| Navigation + parallax | +3.7 | −3.2 |

- **The methods differ by a steady 4–5 km.** The field correlation is dominated by the cold anvil vs the rain area; the cell method by the coldest tops vs echo-top cells. The absolute offset is therefore uncertain by about ±3–4 km.
- **Both say parallax correction alone overshoots.** Uncorrected INSAT cold tops are closer to GPM than the ~7–11 km geometry predicts.
- **Navigation + parallax** brackets zero across the two methods. Correcting both is the most consistent choice, but not a demonstrated improvement.
- **Raw vs tan(VZA)** at the cell level: slope +5 km per unit, r = 0.13. No clear viewing-angle dependence here either.

## Pixel-position convention (checked)

- **The L1C `X`/`Y` coordinates** run exactly from the stated corners (20–130°E, 50°S–50°N), with n − 1 intervals for n pixels. They are per-pixel coordinates, read as pixel centres per CF-1.6.
- **If they were pixel corners instead,** positions would be 2 km too far north-west. The coastline check measures absolute position and would then show a steady south-east correction. It does not: near zero on 6 Jun 2022, and a northward correction in the monsoon median. A half-pixel convention error is not supported.

## Not yet checked

**GPM's own viewing geometry:**
- GPM 2A positions are at the surface footprint, while a storm top at height h along a slanted Ku beam (incidence up to ~17°) sits up to h·tan(θ) ≈ 3–5 km towards GPM.
- The direction depends on the side of the GPM swath, so this mostly adds scatter rather than a bias. It affects the storm-top field and the cell check, but not near-surface Z.

## Findings

1. **The parallax correction works as designed.** It moves cloud tops by the geometrically expected amount (more at higher VZA) and leaves the cross-look offset unchanged.
2. **On average it improves agreement with GPM:** median 5.4 → 3.5 km (storm top) and 6.8 → 2.9 km (rain Z), clearly at VZA ≥ 30° and marginally below 30°.
3. **An along-look offset of ~+2 to +6 km exists in every region and does not scale with viewing angle.** Its cause is open. Candidates:
   - **Storm structure:** INSAT cold cloud tops sit systematically north/north-east of the GPM echo cores. Anvil spreading would be the mechanism, but upper-level monsoon easterlies would push anvils west, so this needs checking.
   - **Navigation north error:** the monsoon N estimate is uncertain.
   - **Geolocation convention:** a half-pixel or projection offset in the L1C grid (~2 km). The coastline navigation check should already include this, but its north estimates are weak in the monsoon.
4. **Case scatter of 4–6 km** limits single-case conclusions. Results are robust in aggregate, not per case.

## Next

- **Pin down the north–south geolocation in the monsoon:** clear-sky coastline checks with east-west coasts (Gulf of Kutch, Gulf of Mannar, Bay of Bengal head) on monsoon break days.
- **Look for storm-structure offsets directly:** compare GPM convective cores with the coldest INSAT pixels per storm, independent of the field correlation.
- **More South and Central India cases,** to firm up the regional means (only 2–3 cases each now).
- **GPM slant-beam correction:** place storm tops along the Ku beam (using the scan angle) before matching, to remove up to 3–5 km of scatter.
- **Cloud-top height check:** compare BT-derived heights with GPM storm tops per cell. If BT heights (capped at 17 km) are too high for the coldest tops, the correction overshoots.
- **Paper:** report that the geometry is verified, that the correction moves features by the expected amount without touching the cross-look offset, and that in monsoon INSAT-3DR data the absolute residual (±3–4 km) depends on navigation, which must be corrected together with parallax.
