# INSAT-3DR L1C Navigation Check (20 Oct 2026)

> **Update (second run, 12 more scans):** the error is **time-dependent and region-dependent**. On 6 Jun 2022 it was ~0 (±3 km) everywhere. From 30 Sep 2022 to 15 Feb 2023 it was a stable west correction of 8–15 km in most regions, but ~0 along the Konkan–Goa coast. See *Second run* below. The first-run text is kept for the record.

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

## Second run: 12 more scans (Jun 2022, Nov 2022 – Feb 2023)

- **New scans:** `datasets/insat_nav/`, i.e. 6 Jun 2022 0515 and 0715; 15 Nov 2022 0415, 0615 and 0815; 15 Dec 2022 0615 and 0815; 15 Jan 2023 0415 and 0815; 15 Feb 2023 0415 and 0815; plus a complete re-download of 30 Sep 2022 1315.
- **New windows:** Kutch, Chennai, Andaman and Rakhine (Myanmar) were added.
- **Match quality:** the winter scenes are clear, with r up to 0.96 (summer r is 0.5–0.8). Results are in `05_validation/navigation_check_nav.json`.

East correction [km] per scan and window (`.` = no usable match):

| Scan | Kutch | Saurashtra | Konkan | Goa | Kerala | Sri Lanka | Chennai | Andhra | Odisha | Rakhine |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 06 Jun 2022 0515 | +3 | +2 | 0 | . | . | . | . | . | . | −3 |
| 06 Jun 2022 0715 | +3 | +2 | . | . | . | +2 | . | . | +2 | −2 |
| 30 Sep 2022 (median of 8 scans) | . | −9 | −1 | . | −5 | −8 | . | . | −12 | . |
| 15 Nov 2022 0415 / 0615 / 0815 | −7 / −8 / −9 | −6 / −8 / −8 | +3 / −1 / −2 | +1 / 0 / 0 | 0 / −7 / +1 | −9 / −7 / . | . / −6 / −4 | −14 / −10 / −10 | −16 / −17 / −15 | . / −10 / −8 |
| 15 Dec 2022 0615 / 0815 | −5 / . | −4 / . | 0 / −4 | +3 / 0 | −3 / −5 | −6 / −11 | −8 / −11 | −8 / −13 | −12 / −15 | −8 / −12 |
| 15 Jan 2023 0415 / 0815 | −9 / −9 | −8 / −9 | 0 / −1 | . / 0 | . | −10 / −12 | −10 / −13 | −11 / −13 | . | −11 / −10 |
| 15 Feb 2023 0415 / 0815 | −8 / −11 | −8 / −10 | −1 / −6 | +1 / −3 | . | −9 / −15 | −11 / −15 | . / −16 | −17 / −19 | −10 / −14 |

North corrections are small: median −1 km, mostly within ±5 km.

### Findings

1. **The error changed with time.** On 6 Jun 2022 every usable window (Kutch, Saurashtra, Konkan, Sri Lanka, Odisha, Rakhine) gives −3 to +3 km. The June matches are strong (Saurashtra: 8,000 clear pixels, r = 0.79). From 30 Sep 2022 on, the same windows give −8 to −19 km. Something in INSAT-3DR navigation or ISRO's L1C processing changed between June and September 2022.
2. **From Sep 2022 to Feb 2023 the pattern is stable but not uniform.**
   - ~0 km along Konkan and Goa (73–74°E)
   - −8 km in Kutch and Saurashtra (~70°E)
   - −9 to −12 km in Sri Lanka, Chennai, Andhra and Rakhine
   - −15 km in Odisha

   A single offset cannot correct this. A smooth correction field (or a per-region correction) is needed.
3. **Possible time-of-day effect.** In Dec, Jan and Feb the 08:15 scans are 1–5 km more negative than the 04:15/06:15 scans. In Nov there is no trend. This needs more data to confirm.
4. **Kochi case is consistent.** 6 Jun 2022 had ~0 navigation error, so running it without an offset was right. That is also why applying the September −8 km offset made it worse.

### What this means for validation

- **Never assume a fixed navigation offset.** Measure it on clear coastlines **for the same day** (ideally the same scan) and apply it with `position_offset_km`. For a region far from any measured coast, interpolate between windows.
- For monsoon cases with few clear coasts, use the clearest scan of that day, or the nearest clear day.
- **Next check:** mid-month scans for **Jul and Aug 2022** (e.g. 15 JUL and 15 AUG at 0615) to find when the change happened, and one clear day in **2023–2024** (e.g. 15 DEC 2023 0615) to see whether it persists.

## Scans to download for the next check

`3RIMG_<DDMONYYYY>_<HHMM>_L1C_SGP_V01R00.h5`, into `datasets/insat_nav/`:

| Date | Times (UTC) | Purpose |
| :--- | :--- | :--- |
| 15 NOV 2022, 15 DEC 2022, 15 JAN 2023, 15 FEB 2023 | 0415, 0615, 0815 | Clear winter days: is the offset stable across months, within a day, and across regions (incl. the Northeast and Bay of Bengal coasts)? |
| 06 JUN 2022 | 0515, 0715 | Same day as the Kochi case |
| 30 SEP 2022 | 1315 | Replace the truncated file |

Minimum set: 15 DEC 2022 and 15 FEB 2023 at 0415 and 0815.
