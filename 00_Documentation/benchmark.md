# Pipeline Benchmark (148 monsoon scenes)

**The full pipeline processed all 148 INSAT-3DR L1C scenes without a failure, in 1.8 s per scene (median) on a laptop, with about 450 MB of memory.** Corrected and uncorrected grids agree exactly in clear sky in every scene, which the U-Net comparison needs.

Run: `python scripts/benchmark_scenes.py --base <folder>`; per-scene results in `05_validation/benchmark/benchmark_scenes.csv`.

## Setup

- **Scenes:** every L1C SGP file in the validation case folders: 148 scenes on 50 days, June–September 2022–2024. Most are daytime 03:15–08:15 UTC scans (navigation scans); 30 are case scans at other times.
- **Per scene:**
  1. Read TIR1 and WV over 0–40°N, 60–100°E (1.35 million pixels), with the pooled monsoon navigation correction (−0.5 km E, +2.5 km N).
  2. Cloud-top height from TIR1 BT with the AFGL tropical profile; cloud mask from ISRO clear-sky BT when an L2B CTP file is present (27 scenes), else BT < 270 K (121 scenes).
  3. Parallax-correct and regrid to the 0.04° South Asia grid (1 million cells), and regrid the same pixels uncorrected.
- **Machine:** Windows laptop, 12 logical CPUs, Python 3.13, Numba kernel. One process; batch mode (`pygeoparallax batch -j N`) runs scenes in parallel.

## Speed and memory

| Stage | Median [s] | 95th percentile [s] | Max [s] |
| :--- | ---: | ---: | ---: |
| Read L1C (2 channels) | 0.47 | 0.53 | 0.73 |
| Cloud-top height | 0.02 | 0.75 | 0.93 |
| Parallax correction + regridding | 0.89 | 1.03 | 1.53 |
| Uncorrected regridding | 0.38 | 0.46 | 0.56 |
| **Total** | **1.78** | **2.62** | **3.23** |

Peak memory 454 MB (median), 469 MB (max). The 148 scenes took 4.7 minutes in total. Cloud-top height takes longer (0.75 s) only when a CTP file is present, for sampling ISRO's clear-sky BT.

## Data quality

| Measure | Median | Range |
| :--- | ---: | ---: |
| Cloudy pixels | 34 % | 18–62 % |
| Cloud-top height of cloudy pixels | 7.8 km | – |
| Parallax shift of cloudy cells, median per scene | 4.4 km | 3.0–5.5 km |
| Parallax shift, 95th percentile per scene | 9.0 km | 7.3–12.5 km |
| Cells observed (`fill_flag` 0) | 98.7 % | 98.2–99.5 % |
| Cells interpolated (`fill_flag` 1) | 1.3 % | 0.5–1.8 % |
| Cells left empty behind clouds (`fill_flag` 2) | 0.007 % | 0–0.03 % |
| Clear cells covered by a cloud moved onto them | 2.5 % | 0.7–5.0 % |
| Clear cells identical in corrected and uncorrected grids | 100 % | 100 % |

- At 0.04°, a 4 km pixel lands in about one cell, so gaps from correction are small: 1.3 % of cells are filled from neighbours, and almost none stay empty.
- Correction moves clouds onto 2.5 % of previously clear cells (median); those cells change value. All other clear cells are identical.

## Partial scans

**14 scenes, 11–14 June 2023, are partial scans:** up to 57 % of the TIR1 array is the fill value (only rows 665–1302 of 3207 hold data in the 12 June 04:15 file). The pipeline handles them (missing pixels stay missing). The two validation cases on these dates (South 12 Jun, Northeast 13 Jun 2023) are unaffected, because their storms lie in the scanned band and comparisons use only pixels with data.

## Designed test set (89 scenes)

A second, designed set is the U-Net test set and will repeat this benchmark: 2 days per month, June–September 2022–2024, at 00:15, 06:15, 12:15 and 18:15 UTC, avoiding the validation-case days (`scripts/design_benchmark_set.py`).

- **96 slots designed, 89 scenes available:** 81 as designed and 8 substitutes 30 min from the slot (`events/benchmark_substitutes.csv`). The final list is `events/benchmark_final.csv`.
- **7 slots have no scan at all:** 18:15 UTC on 5 and 9 Sep 2022, 3 and 4 Sep 2023, and 21 Aug, 9 and 12 Sep 2024. Neither the slot nor the scans 30 min either side exist on MOSDAC. They most likely reflect the equinox eclipse season (not confirmed against an ISRO schedule), when the satellite passes through Earth's shadow around local midnight at 74°E (about 19:00 UTC), so the 18:15 slot is under-represented (17 of 24 days).
- **Paired dataset:** Model A (uncorrected) and Model B (corrected) files for all 89 scenes in `04_corrected_output/paired/` (5 channels, `cth`, `fill_flag`, 0.04° grid; 3.2 GB). Every pair has the same grid and is identical in clear sky in all channels.

## Limits

- The 148-scene benchmark above is concentrated in daytime and on the 50 case-related days; the designed set fixes this.
- Times exclude writing NetCDF output.
