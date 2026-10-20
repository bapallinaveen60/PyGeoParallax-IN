# INSAT-3DR L1C Navigation Check (20 Oct 2026)

Reproduce with `python scripts/check_navigation.py`. Results are in `05_validation/navigation_check.json` (git-ignored).

## Method

- **Coastline:** Natural Earth 10 m land polygons (public domain), saved to `01_raw_data/natural_earth/`. Rasterised at 0.005° and blurred to the 4 km pixel footprint to give an expected land fraction per INSAT pixel.
- **Clear-sky pixels:** daytime pixels with VIS albedo < 30 % and TIR1 > 285 K.
- **Matching:** the coastline was shifted by ±20 km in 1 km steps. The best offset maximises the correlation between INSAT VIS albedo and the expected land fraction.
- **Sign convention:** the offset is the correction to **add** to INSAT positions to reach the true ground location.
- **Data:** 7 coastal windows × 21 scans (19 from 30 Sep 2022, 2 from 6 Jun 2022). A match counts if r ≥ 0.5 and the best offset is not at the search edge.
  - That left 34 daytime VIS matches.
  - The night and evening TIR1 matches (land–sea contrast too weak) and the cloudy 6 Jun night scans all failed this test.
- `3RIMG_30SEP2022_1315_L1C_SGP_V01R00.h5` is a **truncated download** (30 MB of 88 MB) and was skipped. Re-download it if needed.

## Results

| Window | Matches | East correction (km), one per scan | North correction (km) | Clear pixels |
| :--- | :---: | :--- | :--- | :---: |
| **Saurashtra** | 9 | −5, −10, −4, −9, −9, −9, −7, −10, −9 | +5, −1, +3, +3, +6, +3, 0, +3, +6 | ~8,100 |
| **Sri Lanka** | 8 | −5, −9, −6, −9, −7, −9, −8, −10 | −1, −3, −3, −1, 0, 0, −4, +1 | ~3,600 |
| Kerala | 6 | −13, −4, +8, −2, −8, −7 | scattered | ~3,100 |
| Konkan | 5 | −1, −2, −1, −1, −1 | +4 … +17 (unconstrained: N–S coast) | ~4,500 |
| Goa–Karnataka | 4 | +14, +3, 0, +15 | scattered | ~860 |
| Odisha | 2 | −15, −10 | +6, +11 | ~2,900 |

Overall (34 matches): median correction **E −7 km, N +1 km** (IQR E −9 … −1 km, N −1 … +5 km).

## Interpretation

- **Reliable windows:** Saurashtra and Sri Lanka have the most clear pixels and coastlines in several orientations. Both are consistent across 8–9 independent scans: **INSAT positions are ~7–9 km too far east** (the true location is west of where L1C puts it), and north–south error is ≤ ~3 km. That is about **2 pixels**, the same size as the parallax shifts this project corrects (3–11 km).
- **Not one constant offset:** Konkan says only −1 km east, consistently in 5 scans, and Goa (few clear pixels) points the other way. The error may vary across the disk, or the method may struggle on those coasts (creeks and haze near Mumbai, small clear areas at Goa). Correlation gains are small (0.01–0.04), so a single window's estimate is uncertain to a few km. Only consistency across scans makes the Saurashtra and Sri Lanka results convincing.
- **Kochi case:** the alignment tests there kept preferring a **north-east** shift of INSAT. Navigation points the other way (west), so that preference was **not** a navigation error. It most likely reflects the storm's structure (GPM convection on the anvil's eastern side).

## Consequences

1. Validation numbers depend on this. An uncorrected ~8 km east error is larger than the Kochi parallax shift. It does not cancel in an uncorrected-vs-corrected comparison: it biases both versions equally, but it changes which version matches radar better.
2. Before running validation cases, either:
   - estimate the offset per scan with this coastline match and apply it with `position_offset_km` (see below), or
   - restrict validation to regions whose local offset has been measured.
3. To pin down the pattern, run this check on more clear-sky days (e.g. Oct–Mar, when India is mostly cloud-free) and more windows, including the Northeast and Bay of Bengal coasts used for high-VZA validation.

## Applying a measured offset (added 20 Oct 2026)

- `read_insat_l1c(..., position_offset_km=(east, north))` shifts every pixel by a measured correction, using geodesic displacement on WGS84.
  - `scripts/check_navigation.py --offset E N` reports the **residual** error after applying it.
  - `scripts/run_kochi_case.py --nav-offset E N` re-runs the case with it.
- **Sign check:** with `--offset -8 0` on the 04:15–07:45 scans, Saurashtra and Sri Lanka leave a residual of **E −1 km, N 0 km** (12 matches). The convention is confirmed: the offset is added to INSAT positions.
- **Kochi with −8 km east applied:** every metric got slightly worse. IoU fell 0.005–0.011 in both scans, corrected and uncorrected. So the 30 Sep Saurashtra/Sri Lanka offset should **not** be assumed for Kerala in June. The Kerala window was scattered (median −5.5 km), and the offset may change with region or season. A clear-sky check on scans from the same days is needed (see the download list below).

## Scans to download for the next check

`3RIMG_<DDMONYYYY>_<HHMM>_L1C_SGP_V01R00.h5`, into `datasets/insat_nav/`:

| Date | Times (UTC) | Purpose |
| :--- | :--- | :--- |
| 15 NOV 2022, 15 DEC 2022, 15 JAN 2023, 15 FEB 2023 | 0415, 0615, 0815 | Clear winter days: is the offset stable across months, within a day, and across regions (incl. the Northeast and Bay of Bengal coasts)? |
| 06 JUN 2022 | 0515, 0715 | Same day as the Kochi case |
| 30 SEP 2022 | 1315 | Replace the truncated file |

Minimum set: 15 DEC 2022 and 15 FEB 2023 at 0415 and 0815.
