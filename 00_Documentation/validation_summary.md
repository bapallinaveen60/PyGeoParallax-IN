# GPM Validation Summary (4 regions, 15 usable cases)

**Parallax correction improves INSAT–GPM alignment on average.** With the storm-top field within 250 km, the median line-of-sight offset falls from 5.4 to 3.5 km and 9 of 13 cases improve; the cross-look offset is unchanged. The effect is strongest at high viewing angles (VZA ≥ 30°: 5.5 → 2.8 km, 6 of 8 improve).

**But the uncorrected offset does not grow with viewing angle.** All four regions show a positive line-of-sight offset of about +2 to +6 km before correction, including South India, where parallax is only ~3–5 km. So part of the INSAT–GPM offset is a viewing-angle-independent bias of unknown cause, not parallax. The earlier explanation (parallax and navigation errors cancelling) is incomplete. Claims in the paper should be stated with this residual bias (~±3–5 km) and case scatter (4–6 km) in mind.

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
- **Paper:** report the improvement in aggregate, the cross-look invariance, and the VZA-independent bias as an open finding.
