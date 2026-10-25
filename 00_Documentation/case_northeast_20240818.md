# Case Study: Northeast India, 18 August 2024 (first high-VZA GPM case)

**Result: parallax correction removes about two-thirds of the INSAT–GPM offset around the storm.** Within 250 km of the convection, the offset shrinks from ~12 km to ~4 km, and every overlap and correlation metric improves.

Reproduce with:

```bash
pygeoparallax navigation "<case dir>/3RIMG_18AUG2024_0[46]15_L1C_SGP_V01R00.h5" -o 05_validation/nav_corrections/18AUG2024.json
```
```bash
python scripts/run_validation_case.py --dir <case dir> --case northeast_20240818 --scan 18AUG2024_2215 --bbox 21 29 88 97 --nav 05_validation/nav_corrections/18AUG2024.json
```

Outputs (git-ignored): `05_validation/gpm_colocation/northeast_20240818.json`, `04_corrected_output/netcdf/northeast_20240818_*`, `07_figures/northeast_20240818_{no_nav,nav}.png`.

## Data

| Source | File | Time |
| :--- | :--- | :--- |
| GPM 2A Ku V08 | orbit 059478 (`2A.GPM.Ku.V10-20251112.20240818-S215337-E232650.059478.V08A.nc`) | over the convection at 22:23:28 UTC |
| INSAT-3DR L1C + L2B CTP | `3RIMG_18AUG2024_2215` | scan reached 23.3°N at ~22:25:11 UTC (estimated) |
| INSAT-3DR L1C (navigation) | `3RIMG_18AUG2024_0415`, `_0615` | morning |

- **Timing:** GPM was **1.7 min** before INSAT at the convection, so storm motion is negligible (< 1 km).
- **The GPM V08 `.nc` file** has the same layout as V07, and `read_gpm_2a` reads it unchanged.

## The storm

- **GPM:** 845 convective footprints in the region, centred at **23.26°N, 91.00°E** (near Agartala and the Bangladesh–Tripura border), with storm tops up to **17.4 km**.
- **INSAT 22:15:** 15 % of 22–29°N, 89–97°E is colder than 220 K. The coldest tops are at 180 K, the lookup-table floor.
- **Viewing angle at the convection:** 33.3°. The expected shift for a 15 km top is **9.8 km**, and the median shift of the corrected deep cores is **10.5 km**.

## Cloud-top height check

BT height vs ISRO CTP height over ~62,000 cloudy pixels: **r = 0.94**, mean difference −0.26 km. For deep cores, BT gives 17.0 km against 16.6 km from ISRO's CTP. In this storm ISRO's CTP reaches the deep tops; in the Kochi case it did not.

## Results (no navigation correction)

**Whole region (22–29°N, 89–97°E), within the GPM swath:**

| Metric | Uncorrected | Corrected |
| :--- | ---: | ---: |
| IoU, BT < 235 K vs Z > 25 dBZ | 0.451 | 0.461 |
| Pearson, −BT vs Z | 0.680 | 0.688 |
| Mutual information (normalised) | 0.127 | 0.131 |
| IoU, deep cores (BT < 220 K) vs convective rain | 0.159 | 0.162 |
| IoU, deep cores vs deep echoes (storm top > 8 km) | 0.514 | 0.529 |
| Best-match offset (rows S, cols E; 0.02° cells) | (+2, −6) | (0, −4) |

**Near the convection**, the comparison is restricted to a circle around the GPM convection centre:

| Within | Offset uncorrected → corrected | Pearson | Deep-core IoU |
| :--- | :--- | :--- | :--- |
| 150 km | (+3, −6) ≈ 14 km → (+1, −3) ≈ **6.5 km** | 0.658 → 0.679 | 0.479 → 0.498 |
| 250 km | (+3, −5) ≈ 12 km → (0, −2) ≈ **4 km** | 0.628 → 0.633 | 0.527 → 0.540 |

(One cell is 2.2 km north–south and 2.0 km east–west here.)

## Navigation correction

- **The same-day correction came only from distant coasts.** The usable windows were Andhra (+2.0 E, +6.5 N), Chennai (+4.5, +4.2) and Konkan (−2.5, +9.2). Rakhine, the nearest window to the Northeast, was too cloudy. The field therefore interpolates about **+1.7 km E, +6.4 km N** over the Northeast, from coasts more than 1,000 km away.
- **Applying it made every metric slightly worse.** For example, the 250 km offset went from (+3, −5) to (+5, −5) uncorrected, and correlation dropped by 0.01–0.02. Its north component pushes INSAT the wrong way here.
- **Conclusion:** don't apply a correction interpolated from distant coasts. For Northeast cases, use a Northeast window (Rakhine, or a Bangladesh/Sundarbans window still to be added), or run without navigation correction and quote the monsoon navigation uncertainty (~5 km).

## Interpretation

1. **This is the first real-data evidence that the correction works.** The offset between INSAT cold cores and GPM echoes shrinks by ~60–65 %, and the north–south part disappears almost entirely. The direction and size fit a ~10 km correction towards the satellite (south-west).
2. **A residual of 2–3 cells (4–7 km) remains, pointing west.** Possible causes:
   - cloud tops higher than the 17 km tropopause cap (overshooting), which the correction cannot see;
   - a local navigation error in the Northeast;
   - the cold anvil spreading east of the precipitation cores.

   More cases will tell these apart.
3. **The headline metric changes are small** (IoU +0.01) because most of the region is either clear or uniformly cold. The offset and the near-storm metrics show the effect much more clearly; use them in the paper.

## Next

- Run the other three priority cases (Northeast 13 Sep 2022; Himalaya 30 Jun 2023 and 4 Sep 2024) the same way.
- Add a Bangladesh/Sundarbans coastal window, so Northeast cases get a nearby navigation measurement.
