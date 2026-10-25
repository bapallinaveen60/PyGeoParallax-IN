# GPM Validation Summary (high-VZA cases)

**Across 5 usable cases, parallax correction halves the INSAT–GPM offset along the satellite's line of sight: mean 6.6 → 3.1 km within 150 km of the storm, 5.9 → 2.7 km within 250 km. The cross-look offset is unchanged (8.7 → 8.5 km).** That is the signature the geometry predicts. The offset falls in 4 of the 5 cases; the fifth (Himalaya, 30 Jun 2023) overshoots. **Matching against GPM storm-top height instead of rain intensity gives the same result** (mean 6.1 → 2.0 km within 250 km), so the finding does not depend on the choice of radar field.

Reproduce with:

```bash
python scripts/run_all_cases.py --base <validation folder>
```

`--tabulate-only` rebuilds `05_validation/gpm_colocation/all_cases.csv` from existing results. For each case folder, the script:
1. measures a same-day navigation correction from the 04:15/06:15 scans;
2. runs `run_validation_case.py` with and without it;
3. splits the near-storm offset into along-look and cross-look parts.

Setup:
- 0.02° grid
- cloud-top height from TIR1 BT with the AFGL tropical profile
- GPM 2A Ku V08, nearest footprint within 3.5 km
- offset = sub-cell best-correlation shift of −BT against near-surface Z, within 150/250 km of the densest GPM convective cluster
- headline numbers are **without** navigation correction (see below)

## Cases (11 folders)

| Case | Status | Convective footprints (cluster) | Storm top max | VZA | Δt GPM−INSAT |
| :--- | :--- | ---: | ---: | ---: | ---: |
| Northeast, 18 Aug 2024 | usable | 309 | 17.4 km | 32.7° | −1.9 min |
| Northeast, 8 Jun 2024 | usable | 258 | 18.1 km | 35.2° | −0.4 min |
| Northeast, 7 Jun 2022 | usable | 230 | 16.8 km | 34.0° | −0.8 min |
| Himalaya, 17 Sep 2023 | usable | 205 | 15.5 km | 33.6° | −1.4 min |
| Himalaya (plains below), 30 Jun 2023 | usable | 368 | 13.1 km | 33.5° | −1.8 min |
| Himalaya, 10 Aug 2022 | excluded: no reliable match (one uniform cold cloud shield, storm near the box edge) | 346 | 15.4 km | 36.6° | −0.3 min |
| Northeast, 12 Aug 2023 | excluded: no reliable match (most GPM convection under warm tops, outside the cold storm) | 138 | 14.6 km | 37.7° | −2.2 min |
| Himalaya, 25 Jun 2024 | excluded: too little convection | 50 | 10.8 km | 32.2° | −0.5 min |
| Northeast, 13 Sep 2022 | excluded: too little convection | 19 | 12.2 km | 37.4° | −0.1 min |
| Himalaya, 3 Jun 2022 | excluded: too little convection | 6 | 7.8 km | 35.3° | −0.1 min |
| Himalaya, 4 Sep 2024 | not run: case scan `3RIMG_04SEP2024_1815` (L1C + CTP) missing | — | — | — | — |

Excluded means: fewer than 100 convective GPM footprints in the main cluster, or a best-match offset at the edge of the search, i.e. no reliable match (≥ 22 km).

## Offset along the line of sight (usable cases, no navigation correction)

| Case | Within 150 km: before → after [km] | Within 250 km: before → after [km] | Cross-look, 150 km: before → after [km] |
| :--- | :--- | :--- | :--- |
| Northeast, 18 Aug 2024 | 8.3 → **0.4** | 7.9 → **0.2** | 3.3 → 2.4 |
| Northeast, 7 Jun 2022 | 10.4 → **3.0** | 9.7 → **2.6** | −1.1 → −1.0 |
| Northeast, 8 Jun 2024 | 5.4 → **−3.2** | 4.6 → **−3.3** | 19.6 → 19.5 |
| Himalaya, 17 Sep 2023 | 7.4 → **−2.1** | 6.7 → **−3.1** | 14.8 → 15.0 |
| Himalaya, 30 Jun 2023 | −1.3 → **−6.7** | 0.8 → **−4.3** | −4.7 → −4.5 |
| **Mean of absolute values** | **6.6 → 3.1** | **5.9 → 2.7** | **8.7 → 8.5** |

### Robustness: storm-top height as the radar field

Rain intensity at the surface (above) and cloud-top temperature do not always mark the same place. GPM's **storm-top height** describes the same storm tops that TIR1 sees, so it was used as a second, independent field for the same offset:

| Case | Along-look within 250 km, storm-top field: before → after [km] |
| :--- | :--- |
| Northeast, 18 Aug 2024 | 7.4 → **0.4** |
| Northeast, 7 Jun 2022 | 9.4 → **0.8** |
| Northeast, 8 Jun 2024 | 3.4 → **−4.3** |
| Himalaya, 17 Sep 2023 | 5.4 → **−3.5** |
| Himalaya, 30 Jun 2023 | 4.9 → **−1.0** |
| **Mean of absolute values** | **6.1 → 2.0** |

- **Within 150 km:** 6.1 → 3.1 km.
- **Cross-look offset:** unchanged, 8.4 → 8.6 km.
- **Cases improved:** 4 of 5 with either field. With the storm-top field the Himalayan overshoot disappears, and Northeast 8 Jun 2024 overshoots slightly instead.

Positive = INSAT has to move towards the satellite (south-west) to match GPM, as uncorrected parallax predicts. The computed deep-core shift is 9.9–11.8 km in these cases.

**Within 250 km of the storm**, deep-core IoU (BT < 220 K vs echo top > 8 km) rises in 4 of 5 cases:

| Case | Deep-core IoU before → after |
| :--- | :--- |
| Northeast, 18 Aug 2024 | 0.541 → 0.551 |
| Northeast, 7 Jun 2022 | 0.367 → 0.401 |
| Northeast, 8 Jun 2024 | 0.439 → 0.449 |
| Himalaya, 30 Jun 2023 | 0.478 → 0.496 |
| Himalaya, 17 Sep 2023 | 0.640 → 0.636 |

Correlation (−BT vs Z) rises in 3 cases and is flat in 2.

## Findings

1. **The parallax signal is clear along the line of sight.** Uncorrected INSAT sits 5–10 km towards the satellite's far side of GPM in 4 of 5 cases, about the computed shift. Correction removes most of it, and the cross-look offset does not move.
2. **One overshoot (Himalaya, 30 Jun 2023).** It had almost no line-of-sight offset to begin with, and correction leaves −4 to −7 km. It is also the shallowest usable storm (GPM tops 13.1 km), where BT-based heights may be too high (14.7 km for deep cores against 13.3 km from ISRO's CTP).
3. **Cross-look offsets of up to 20 km remain** (Northeast 8 Jun 2024, Himalaya 17 Sep 2023). They are not parallax. Navigation error or storm structure (e.g. anvil spreading) are the candidates.
4. **Same-day navigation corrections were not used.** On monsoon mornings they rest on distant or suspect windows, and they made some cases better and others worse (both variants are in `all_cases.csv`).
5. **Case yield:** 5 of 10 runnable cases were usable. Three had too little convection in the GPM swath, and two gave no reliable match.

## Next

- **Missing files:** `3RIMG_04SEP2024_1815_L1C_SGP_V01R00.h5` and `3RIMG_04SEP2024_1815_L2B_CTP_V01R00.h5`.
- **More usable cases:** at least 10 for a paper statistic. Use `validation_shortlist.csv`, and check GPM for convection before downloading INSAT data.
- **The two search-edge cases cannot be recovered.** A box extended north, a ±15-cell search and the storm-top field were all tried, and both still have no match inside 33 km. Their satellite and radar fields do not correspond (see the case table).
- **Overshoot in shallow storms:** compare BT heights with GPM storm tops per case, and try ERA5 profiles.
- **Paper figure:** along-look offset before vs after, per case, with the cross-look offset beside it.
