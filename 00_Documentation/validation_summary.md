# GPM Validation Summary (high-VZA cases)

**Parallax correction removes 50–80 % of the INSAT–GPM offset along the satellite's line of sight in both Northeast India cases, and leaves the cross-look offset unchanged, as the geometry predicts.** In the Himalayan case there was almost no line-of-sight offset to remove, and the correction overshoots by ~5–6 km. Large cross-look mismatches (up to 18 km) remain. They are not parallax: navigation errors or storm structure are the candidates.

All cases ran with `scripts/run_validation_case.py`:
- 0.02° grid
- cloud-top height from TIR1 BT with the AFGL tropical profile
- GPM 2A Ku V08, nearest footprint within 3.5 km

The offset between INSAT cold cloud and GPM echoes is the best-correlation shift, refined to a fraction of a cell (`validation.subcell_displacement`). Numbers are **without** navigation correction unless stated. Per-case JSON is in `05_validation/gpm_colocation/` (git-ignored).

## Cases

| Case | Data | GPM convection | VZA | Δt GPM−INSAT | Deep-core shift | Usable |
| :--- | :--- | :--- | ---: | ---: | ---: | :--- |
| Northeast, 18 Aug 2024 | complete | 845 footprints, 23.3N 91.0E, tops to 17.4 km | 33.3° | −1.7 min | 10.5 km | yes |
| Northeast, 8 Jun 2024 | complete | 447 footprints, 25.3N 92.5E, tops to 18.1 km | 36.1° | −0.3 min | 11.8 km | yes |
| Himalaya (plains below the foothills), 30 Jun 2023 | complete | 548 footprints, 26.9N 83.8E, tops to 13.1 km | 33.2° | −1.9 min | 9.3 km | yes |
| Northeast, 13 Sep 2022 | CTP missing | only 37 footprints, tops to 12.2 km | 37.0° | −0.1 min | 10.8 km | no: almost no convection |
| Himalaya, 4 Sep 2024 | **case scan L1C and CTP still missing** (`3RIMG_04SEP2024_1815`) | — | — | — | — | not run |

## Offset along and across the line of sight

Each offset (the shift INSAT needs to match GPM) is split into:
- **along-look:** towards the satellite, the direction parallax acts. The satellite azimuth from the storm is 218° in the Northeast and 201° in the Himalaya.
- **cross-look:** perpendicular to it.

| Case | Within | Along-look, before → after [km] | Cross-look, before → after [km] |
| :--- | :--- | :--- | :--- |
| Northeast, 18 Aug 2024 | 150 km | 13.1 → **5.6** | 4.5 → 3.9 |
| | 250 km | 10.4 → **2.1** | 4.3 → 4.0 |
| Northeast, 8 Jun 2024 | 150 km | 11.7 → **2.5** | 14.7 → 15.4 |
| | 250 km | 4.9 → **−2.6** | 18.5 → 18.4 |
| Himalaya, 30 Jun 2023 | 150 km | −0.6 → **−5.2** | −5.2 → −4.7 |
| | 250 km | −1.2 → **−6.4** | −9.3 → −8.9 |

## Overlap and correlation near the storm (within 150 km)

| Case | Deep-core IoU (BT < 220 K vs echo top > 8 km) | Correlation (−BT vs Z) |
| :--- | :--- | :--- |
| Northeast, 18 Aug 2024 | 0.479 → 0.498 | 0.658 → 0.679 |
| Northeast, 8 Jun 2024 | 0.435 → 0.462 | 0.582 → 0.599 |
| Himalaya, 30 Jun 2023 | 0.520 → 0.520 | 0.573 → 0.565 |

Over each whole region, deep-core IoU rises in all three cases: +0.014, +0.010 and +0.019.

## Findings

1. **The line-of-sight offset drops by 50–80 % in both Northeast cases**: 13.1 → 5.6, 10.4 → 2.1, 11.7 → 2.5 and 4.9 → 2.6 km. Its size before correction (5–13 km) matches the computed parallax shift (10–12 km). The cross-look offset does not change. This is the signature of a correct parallax correction.
2. **Himalaya, 30 Jun 2023: overshoot.** Before correction there was almost no line-of-sight offset (about −1 km), and the 9 km correction leaves −5 to −6 km. Candidates:
   - **cloud-top heights too high for this weaker system.** GPM tops reach only 13.1 km, while BT gives 14.7 km for deep cores and ISRO's CTP 13.3 km.
   - **a navigation error along the line of sight** that happened to cancel the parallax.
   - **cloud-top vs echo geometry**, e.g. a tilted or sheared system.

   More Himalayan cases are needed.
3. **Large cross-look mismatches are not parallax.** They reach 15–18 km on 8 Jun 2024 and 5–9 km in the Himalaya. Navigation or storm structure are the candidates; neither could be pinned down:
   - On 30 Jun 2023 the only nearby navigation hints (Odisha −4.0 km E, Rakhine −3.5 km E; single scans, r 0.72–0.73, below the acceptance threshold) point **west**. A navigation explanation of the Himalayan eastward residual is therefore not supported. An earlier fixed-offset test with +6 to +10 km E improved that case's metrics, but it is not backed by a measurement.
4. **Same-day navigation corrections were unreliable** in all cases: monsoon mornings left only distant or suspect windows. They worsened 18 Aug 2024 and improved 8 Jun 2024, where the Odisha window gave a suspicious +13.5 km N. The headline results therefore use no navigation correction.
5. **Case selection:** 1 of 4 cases (13 Sep 2022) had almost no convection. Check convection before downloading INSAT data.

## Next

- **Missing files:** `3RIMG_04SEP2024_1815_L1C_SGP_V01R00.h5` and `3RIMG_04SEP2024_1815_L2B_CTP_V01R00.h5` (Himalaya 2024, the second Himalayan case).
- **More Himalayan and Northeast cases** from `validation_shortlist.csv`, to tell an overshoot from case-to-case scatter.
- **Cloud-top height for weaker systems:** compare BT height with GPM storm tops per case, and test ERA5 profiles in place of the standard atmosphere.
- **Paper figure:** the along-look/cross-look split is the clearest way to show the correction working.
