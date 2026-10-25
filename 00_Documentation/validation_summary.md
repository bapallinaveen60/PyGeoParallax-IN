# GPM Validation Summary (high-VZA cases)

Of four selected cases, two could be analysed:
- **Northeast India, 18 Aug 2024:** parallax correction clearly improves agreement with GPM, removing ~2/3 of the INSAT–GPM offset near the storm.
- **Himalayan foothills, 30 Jun 2023:** the effect is neutral. Its mismatch is dominated by a 6–10 km east–west navigation error, which parallax correction cannot fix.

More cases, and a sub-cell offset estimate, are needed before a general claim.

All cases ran with `scripts/run_validation_case.py`:
- 0.02° grid
- cloud-top height from TIR1 BT with the AFGL tropical profile
- GPM 2A Ku V08, rasterised by nearest footprint within 3.5 km

Numbers are from runs **without** navigation correction unless stated; same-day corrections were either unavailable or measured only on coasts more than 1,000 km away. Per-case JSON is in `05_validation/gpm_colocation/` (git-ignored).

## Cases

| Case | Data status | GPM convection | VZA | Δt GPM−INSAT | Deep-core shift | Outcome |
| :--- | :--- | :--- | ---: | ---: | ---: | :--- |
| Northeast, 18 Aug 2024 | complete | 845 footprints at 23.3N 91.0E, tops to 17.4 km | 33.3° | −1.7 min | 10.5 km | **Improves**: near-storm offset 12 → 4 km (250 km), 14 → 6.5 km (150 km) |
| Himalaya, 30 Jun 2023 | 06:15 L1C truncated (navigation from 04:15 only; no usable correction) | 548 footprints at 26.9N 83.8E (plains below the foothills), tops to 13.1 km | 33.2° | −1.9 min | 9.3 km | **Neutral**; mismatch dominated by an E–W navigation error |
| Northeast, 13 Sep 2022 | CTP missing (cloud mask BT < 270 K) | only 37 footprints, tops to 12.2 km | 37.0° | −0.1 min | 10.8 km | **Not usable**: almost no convection in the swath (IoU 0.06) |
| Himalaya, 4 Sep 2024 | **case scan L1C and CTP missing** (`3RIMG_04SEP2024_1815`) | — | — | — | — | Not run |

## Detail: Himalaya, 30 Jun 2023

Analysis box 24–32N, 79–88E. A first run with 26–34N cut off the storm's southern half and was discarded.

| Run | Within | Offset uncorrected → corrected | Correlation | Deep-core IoU |
| :--- | :--- | :--- | :--- | :--- |
| No navigation | whole box | (+1, +5) → (−1, +6) cells | 0.658 → 0.654 | 0.472 → 0.491 |
| No navigation | 250 km | 10.2 → 10.2 km | 0.598 → 0.592 | 0.477 → 0.497 |
| No navigation | 150 km | 6.4 → 6.4 km | 0.573 → 0.565 | 0.520 → 0.520 |
| +6 km E navigation (test) | 250 km | 4.5 → 4.5 km | 0.613 → 0.610 | 0.488 → 0.505 |
| +10 km E navigation (test) | 250 km | 2.2 → 2.2 km | 0.614 → 0.613 | 0.484 → 0.504 |

- At 84°E the satellite is almost due south, so parallax correction moves clouds mostly south. The dominant residual is **east–west** (INSAT needs ~6–12 km east), which parallax cannot address.
- **Applying +6 to +10 km east** (a sensitivity test; no same-day measurement) removes that residual and improves all metrics. This fits the summer-state navigation error seen elsewhere: +3.5 to +6 km E in June, +10 km in April.
- **After that, parallax correction flips the north–south offset** from 1 cell south to 1 cell north. It is the same size either way, at the 2.2 km grid limit, so the integer-cell offset search cannot tell whether correction helped. Deep-core IoU still rises by ~0.02 across the region.
- **Cloud-top check:** BT height vs ISRO CTP r = 0.86. Deep cores are 14.7 km by BT against 13.3 km by CTP.

## What we learn

1. **Where convection is deep and well timed, correction helps clearly** (Northeast 2024: tops to 17 km, shift 10.5 km). The north–south part of the offset is removed in both analysable cases.
2. **Navigation error can be as large as the parallax shift, and in a different direction.** In the Himalaya case it was mostly east–west. Without a same-day measurement close by, it can hide the parallax effect. Monsoon mornings were too cloudy for nearby coastal windows in all three cases.
3. **The offset metric is too coarse.** Integer 0.02° cells (2.0–2.2 km) cannot resolve the remaining 1–2 km. A sub-cell estimate (fitting a parabola to the correlation peak) or a 0.01° grid is needed.
4. **Case selection needs a convection check before download.** 1 of 3 selected cases (13 Sep 2022) had almost none in the swath.

## Next

- **Missing files:** `3RIMG_04SEP2024_1815_L1C_SGP_V01R00.h5` and `3RIMG_04SEP2024_1815_L2B_CTP_V01R00.h5` (Himalaya 2024 case).
- **Optional:**
  - a complete `3RIMG_30JUN2023_0615_L1C` (for navigation);
  - `3RIMG_13SEP2022_2145_L2B_CTP` (only if that case is kept; it lacks convection).
- **Replacement Northeast case** from `validation_priority.csv`, e.g. 8 Jun 2024 18:54 or 12 Aug 2023 20:22.
- **Code:**
  - sub-cell offset estimate in `best_displacement`;
  - a navigation sensitivity option in `run_validation_case.py`, to report results over a range of navigation offsets rather than one.
