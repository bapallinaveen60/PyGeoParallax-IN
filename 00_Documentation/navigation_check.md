# INSAT-3DR L1C Navigation Check (20 Oct 2026)

> **Latest (fourth run, 6 more scans): the error is seasonal.** It switches between two states around the equinoxes, consistent with INSAT's twice-yearly yaw flip. Late Sep to mid Mar: a 7–20 km **west** correction. Mid Apr to Jun: ~0 to +10 km **east**. Konkan–Goa stays ≈ 0 throughout. See *Seasonal pattern* at the end.
>
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

## Automatic per-scan correction (`pygeoparallax.navigation`)

The coastline matching is now part of the package:

```bash
# 1. Measure: one correction per day, from all of that day's scans (~7 s per scan)
pygeoparallax navigation "datasets/insat_nav/3RIMG_15FEB2023_*_L1C_SGP_V01R00.h5" -o 05_validation/nav_corrections/15FEB2023.json
# 2. Apply: when processing standard scenes
pygeoparallax correct scene.nc out.nc --nav-correction 05_validation/nav_corrections/15FEB2023.json
```

In Python, `read_insat_l1c(path, position_offset_km=NavigationCorrection.from_json(...))` applies it per pixel.

- **How the field is built:**
  - Each window's offset is measured with a 2 km coarse search over ±30 km, refined to 0.5 km.
  - Weak (r < 0.6) and edge-of-search matches are dropped. r < 0.6 matches in cloudy monsoon scenes produced implausible offsets, e.g. +24.5 km E and +28.5 km N in Kerala on 15 Jul 2022.
  - Matches for the same window from several scans are combined by median.
  - Between windows the correction is inverse-distance weighted (power 2).
- **How well it works (re-using the matches in this document):**

  | Test | Median error after correction | Uncorrected |
  | :--- | :---: | :---: |
  | Same day, window left out and predicted from the others (n = 50) | **4.3 km** (p90 9.3) | 8.8 km |
  | Previous month's field applied (Nov→Dec, Dec→Jan, Jan→Feb) | 3.5–4.8 km | 8.1–10.7 km |
  | Sep→Nov (Sep field had no east-coast windows) | 7.9 km | 8.2 km |
  | **Wrong period:** Feb 2023 field applied to 6 Jun 2022 | **15.1 km** | 4.2 km |

- **Use a same-day correction whenever possible.**
  - At measured coasts it removes the error almost entirely (residual ~1 km).
  - Between coasts it roughly halves it.
  - A field from another period can make things much worse.
- **Example (15 Feb 2023):** the correction is E −3.5 km at Mumbai, −9.8 km at Kochi and −13.5 km at Agartala. Kochi and Agartala are interpolated, since Kerala and the Northeast had no usable window that day. North components were −2.5 to −7 km.

## Timeline: Jun 2022 – Dec 2024 (third run)

Four more 06:15 UTC scans were downloaded: 15 Jul 2022, 15 Aug 2022, 15 Dec 2023 and 15 Dec 2024. Corrections were measured with `pygeoparallax navigation` (±30 km search, r ≥ 0.6) and saved to `05_validation/nav_corrections/` (git-ignored).

| Date | Confidence | East correction by window [km] | Reading |
| :--- | :--- | :--- | :--- |
| 6 Jun 2022 | good (r 0.67–0.79) | Kutch +3, Saurashtra +2, Konkan 0, Rakhine −2/−3 | ≈ 0 everywhere |
| 15 Jul 2022 | **none**: monsoon cloud, no window reached r 0.6 | — | unknown |
| 15 Aug 2022 | poor: 2 windows that disagree, implausible N +14 | Odisha −6, Rakhine +8 | unknown |
| 30 Sep 2022 – 15 Feb 2023 | good | Konkan/Goa ≈ 0; Kutch/Saurashtra −8; Sri Lanka/Chennai/Andhra/Rakhine −9 … −12; Odisha −15 | west correction, growing away from ~73–74°E |
| 15 Dec 2023 | good (r 0.70–0.88) | Goa +4.5, Kutch −5, Saurashtra −4.5, Rakhine −6.5, Odisha −12 | same pattern, **~4 km smaller** in the west |
| 15 Dec 2024 | good (r 0.79–0.91) | Goa 0, Konkan −2.5, Saurashtra −9.5, Kutch −10.5, Odisha −20 | same pattern as Dec 2022, **as large or larger** |

North corrections are −1 to −6.5 km in the winter scans. They are larger than in the first runs, partly because of the finer 0.5 km refinement.

### Findings

1. **The error persists.** The same spatial pattern appears in every clear scan from Sep 2022 to Dec 2024: ~0 near Konkan–Goa, a westward correction growing to the west (Kutch) and especially to the east (Odisha). It is not a one-off glitch.
2. **Its size changes.** Dec 2023 is ~4 km smaller in the west than Dec 2022 or Dec 2024. Odisha ranges from −12 to −20 km.
3. **When it started is still unknown.** The two monsoon scans (Jul, Aug 2022) are too cloudy. June 2022 was ≈ 0. Two explanations remain:
   - a **step change** in navigation/processing between Jun and Sep 2022, or
   - a **seasonal** effect (near zero in summer, large in winter).

   The data so far cannot tell these apart.
4. **For processing:** always measure a same-day correction. In the monsoon season, clear coastlines may be too scarce for one, so plan validation cases with that in mind or use the nearest clear day.

### Next download to separate "step change" from "seasonal"

Clear pre-monsoon and post-monsoon months (06:15 UTC, `3RIMG_<date>_0615_L1C_SGP_V01R00.h5`):

| Date | Why |
| :--- | :--- |
| 15 MAR 2022, 15 APR 2022, 15 MAY 2022 | Before June 2022. If these are ≈ 0, a step change after June is likely. |
| 15 APR 2023, 15 MAY 2023 | The same season a year later. If they are also ≈ 0, the effect is seasonal. |
| 15 OCT 2023 | Post-monsoon, completes the seasonal cycle |

## Seasonal pattern (fourth run)

Six more 06:15 UTC scans: 15 Mar, 15 Apr and 15 May 2022; 15 Apr, 15 May and 15 Oct 2023. Same method (±30 km, r ≥ 0.6). East correction [km]:

| Date | Kutch | Saurashtra | Konkan | East coast (Andhra / Chennai / Odisha) | Rakhine |
| :--- | ---: | ---: | ---: | :--- | ---: |
| 15 Mar 2022 | −15 | −14 | −7 | −16.5 / −15.5 / −20.5 | −14 |
| **15 Apr 2022** | **+9.5** | **+9** | −0.5 | +1 / +6 / . | **+10** |
| 15 May 2022 | +3.5 | +2.5 | (noisy) | +0.5 / −6 / −6 | . |
| 6 Jun 2022 | +3 | +2 | 0 | . | −2 |
| 30 Sep 2022 – 15 Feb 2023 | −5 … −11 | −4 … −10 | ≈ 0 | −8 … −19 | −8 … −14 |
| **15 Apr 2023** | **+10** | **+9.5** | 0 | +3 / +4.5 / +5 | . |
| 15 May 2023 | +1.5 | +1 | (noisy) | (noisy) | . |
| 15 Oct 2023 | −8 | −7.5 | +2.5 | −9 / −9.5 / −14.5 | −12 |
| 15 Dec 2023 | −5 | −4.5 | . | . / . / −12 | −6.5 |
| 15 Dec 2024 | −10.5 | −9.5 | −2.5 | . / . / −20 | . |

North corrections are mostly within ±5 km. Larger values come from noisy, cloud-limited windows.

### Findings

1. **It is seasonal, not a one-time change.** Spring 2022 and spring 2023 agree (Kutch/Saurashtra +9 to +10 km in mid April), and so do autumn 2022 and autumn 2023 (−7.5 to −8 km in Oct). The sign flips between 15 Mar (−15) and 15 Apr (+10).
2. **Two states that switch around the equinoxes:**
   - **"Winter" state**, from late Sep (after the ~23 Sep equinox) to mid Mar: west correction of 7–20 km, largest over Odisha.
   - **"Summer" state**, from mid Apr (after the ~20 Mar equinox) to at least early Jun: east correction of up to ~10 km in mid Apr, shrinking to ~0–3 km by May–June.
   - Konkan–Goa is close to zero in both states.
3. **A likely cause is the yaw flip** that INSAT-3D-series satellites perform around the equinoxes. ISRO's INSAT-3D evaluation compares data before and after the yaw flip ([ISPRS 2014](https://isprs-archives.copernicus.org/articles/XL-8/299/2014/isprsarchives-XL-8-299-2014.pdf)), and IMD's INSAT-3DR/3DS procedures treat the Sep→Mar and Mar→Sep equinox transitions separately ([IMD SatMet SOP](https://mausam.imd.gov.in/imd_latest/contents/pdf/satmet_sop.pdf)). This is a hypothesis: the flip dates and any navigation updates have not been confirmed from ISRO documentation.

### Consequences for the monsoon (JJAS) study

- **June to about 20 September is in the summer state,** where errors are small (~0–3 km in May–June). Jul–Aug could not be measured (cloud), but they lie in the same state.
- **The last week of September is in the winter state** (−8 km or more). Treat monsoon cases after the September equinox separately and always correct them.
- **Keep measuring a same-day correction** where coasts are clear. When they aren't, use the nearest clear day **in the same yaw-flip state**, never one from the other half of the year.

### Optional checks

- **Pin down the switch dates:** scans just before and after each equinox, e.g. 15 SEP 2022, 25 SEP 2022, 15 MAR 2023 and 31 MAR 2023 (all 0615).
- **Read the equinox sections of the IMD SatMet SOP** for the operational yaw-flip dates.
