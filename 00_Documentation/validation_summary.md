# GPM Validation Summary (high-VZA cases)

**Across 10 usable cases, parallax correction moves INSAT cloud tops about 7 km towards the GPM echoes along the satellite's line of sight, and leaves the cross-look offset unchanged.** That is the signature the geometry predicts.
- Storm-top field, within 250 km: the median line-of-sight offset falls from 5.5 to 2.8 km, and 6 of 8 cases improve.
- Uncorrected offsets are smaller than the ~10 km parallax shift (mean +3.8 km), and corrected ones overshoot slightly (mean −3.0 km). This fits the independently measured monsoon navigation error of ~5 km towards the satellite. **In raw monsoon imagery, parallax and navigation errors partly cancel.**

Reproduce with:

```bash
python scripts/screen_gpm_convection.py --dir <validation folder>
python scripts/run_all_cases.py --base <validation folder>
```

`--tabulate-only` rebuilds `05_validation/gpm_colocation/all_cases.csv`.

Setup:
- 0.02° grid
- cloud-top height from TIR1 BT with the AFGL tropical profile
- GPM 2A Ku V08, nearest footprint within 3.5 km
- offset = sub-cell best-correlation shift of −BT against a GPM field, within 150/250 km of the densest convective cluster
- **storm-top height is the primary field** (the same storm tops TIR1 sees; correlation 0.53–0.75); near-surface reflectivity Z is the secondary field
- a field/window result counts only if its best match lies inside the ±10-cell (~22 km) search
- headline numbers are without navigation correction

## Cases (24 folders)

| Outcome | Cases |
| :--- | :--- |
| **Usable (10)** | Northeast: 18 Aug 2024, 8 Jun 2024, 7 Jun 2022, 20 Jul 2022, 13 Jun 2023. Himalaya: 30 Jun 2023, 12 Sep 2023, 17 Sep 2023, 2 Jul 2024 (each with at least one valid field/window; see the CSV) |
| Too little convection (< 100 convective footprints in the main cluster) (9) | Himalaya: 3 Jun 2022, 13 Jul 2022, 18 Jul 2022, 27 Aug 2023, 14 Jun 2024, 25 Jun 2024. Northeast: 13 Sep 2022, 17 Jul 2023, 27 Jul 2024 |
| No reliable match in any field (3) | Himalaya 10 Aug 2022 (uniform cold shield), Northeast 12 Aug 2023 (convection outside the cold storm), Northeast 2 Aug 2022 |
| Not run (2) | Himalaya 4 Sep 2024 (case scan missing; anyway only 15 convective footprints), Northeast 29 Aug 2024 (no 19:15 scan on MOSDAC) |

Screening GPM first (`screen_gpm_convection.py`) predicted which new cases had enough convection: 5 of 12 in the second batch.

## Line-of-sight offset, storm-top field, within 250 km (8 valid cases)

Positive = INSAT must move towards the satellite (south-west) to match GPM.

| Case | Before [km] | After [km] | Cross-look before [km] |
| :--- | ---: | ---: | ---: |
| Northeast, 7 Jun 2022 | +9.4 | **+0.8** | +2.1 |
| Northeast, 13 Jun 2023 | +10.0 | **+4.1** | +9.0 |
| Northeast, 18 Aug 2024 | +7.4 | **+0.4** | +3.1 |
| Himalaya, 30 Jun 2023 | +4.9 | **−1.0** | −10.4 |
| Himalaya, 12 Sep 2023 | +3.4 | **−2.0** | +4.9 |
| Himalaya, 17 Sep 2023 | +5.4 | **−3.5** | +3.7 |
| Northeast, 20 Jul 2022 | −4.9 | −9.9 | −8.3 |
| Himalaya, 2 Jul 2024 | −5.5 | −12.8 | +2.7 |
| **Signed mean** | **+3.8** | **−3.0** | |
| **Median of absolute values** | **5.5** | **2.8** | |

## All fields and windows

| Field, window | Valid cases | Signed mean before → after [km] | Median absolute before → after [km] | Improved |
| :--- | ---: | :--- | :--- | :--- |
| Storm top, 250 km | 8 | +3.8 → −3.0 | 5.5 → 2.8 | 6 of 8 |
| Storm top, 150 km | 6 | +4.6 → −2.5 | 5.0 → 2.8 | 4 of 6 |
| Rain Z, 250 km | 7 | +3.3 → −3.6 | 6.7 → 3.3 | 4 of 7 |
| Rain Z, 150 km | 6 | +5.3 → −2.1 | 6.4 → 3.1 | 4 of 6 |

- **The shift from correction is consistent:** −6.8 to −7.4 km along the line of sight in every field and window. The computed deep-core shift is ~10 km; the match uses the whole cloud, including lower tops.
- **Cross-look offsets do not change** (mean absolute values 4.4–7.6 km before and after).

## Findings

1. **Correction does what the geometry predicts.** It shifts the INSAT–GPM offset by ~7 km along the line of sight and leaves the cross-look component untouched, in all four field/window combinations.
2. **Parallax and navigation partly cancel in monsoon data.** The coastline check measured a median monsoon navigation correction of +1.8 km E, +4.8 km N. Projected on the line of sight (satellite azimuth ~200–218°), that is **~5 km towards the satellite**.
   - Expected uncorrected offset: parallax (~+7 to +10 km) minus navigation (~5 km), i.e. about +3 to +5 km. Observed: **+3.3 to +5.3 km**.
   - Expected after parallax correction: about −5 km. Observed: **−2 to −4 km**.

   So parallax correction alone leaves a small overshoot. The two cases that got worse (Northeast 20 Jul 2022, Himalaya 2 Jul 2024) already started with a negative offset, i.e. a larger navigation error on those days.
3. **Rain intensity vs storm top:** the storm-top field matches more cases and correlates better with TIR1, and is the more appropriate validation field. Both fields give the same picture.

## Test: parallax and navigation together

`scripts/test_navigation_parallax.py` re-ran the usable cases with the monsoon median navigation correction (+1.8 km E, +4.8 km N), applied the same way to all of them, and compared four states. Results are in `05_validation/gpm_colocation/nav_parallax_test.csv`. Only field/windows where all four matches lie inside the search are counted.

Line-of-sight offset, mean ± standard error (RMS), in km:

| Field, window | Cases | Raw | Parallax only | Navigation only | Both |
| :--- | ---: | :--- | :--- | :--- | :--- |
| Storm top, 250 km | 8 | +3.8 ± 2.1 (6.7) | −3.0 ± 2.0 (6.1) | **+8.7 ± 2.0** (10.3) | **+1.7 ± 1.9** (5.4) |
| Storm top, 150 km | 6 | +4.6 ± 2.1 (6.6) | −2.5 ± 1.6 (4.3) | **+9.6 ± 2.1** (10.7) | **+2.5 ± 1.6** (4.4) |
| Rain Z, 250 km | 6 | +3.1 ± 2.6 (6.6) | −3.7 ± 2.3 (6.3) | **+8.1 ± 2.6** (10.0) | **+1.3 ± 2.2** (5.0) |
| Rain Z, 150 km | 5 | +5.2 ± 2.2 (6.9) | −1.9 ± 1.7 (3.9) | **+10.3 ± 2.2** (11.3) | **+3.1 ± 1.6** (4.5) |

What it shows:

1. **The cancellation is real.** With navigation corrected and parallax not, the offset grows to **+8.1 to +10.3 km**, which matches the computed parallax shift (~10 km). Raw monsoon INSAT imagery looks closer to the radar than it really is, because its ~5 km navigation error (towards the satellite) hides about half of the parallax displacement.
2. **Both corrections together** bring the mean to +1.3 to +3.1 km. Parallax only gives −1.9 to −3.7 km. The bias shrinks at 250 km but not at 150 km, and the RMS is similar (4.4–5.4 vs 3.9–6.3 km).
3. **Neither variant is distinguishable from zero.** With 5–8 cases, each is within ~1.5 standard errors. The true navigation error on each day probably differs from the monsoon median, so the best estimate lies between the two.
4. **Case-to-case scatter (SD 4–6 km) is now the limiting factor,** not the method. Tightening it needs more cases, and same-day navigation measurements near each storm.

**For the paper:**
- The parallax correction is verified: it shifts the offset by the expected ~7 km along the line of sight and leaves the cross-look offset unchanged.
- In monsoon INSAT-3DR data, a ~5 km navigation error partly masks parallax. Correct both, and quote a residual uncertainty of a few km.

## Next

- **Reduce the scatter:** more usable cases (Central and South India too), and same-day navigation where clear coasts exist.
- **Add Central India** (VZA ~23–27°) and **South India** (VZA ~10–16°) cases. The uncorrected offset should grow with tan(VZA); that trend is a further test.
- **Paper figure:** per-case line-of-sight offset before/after, with the navigation-only expectation marked.
