# GPM Validation Cases (high-VZA, monsoon)

> **Status:** case 1 (Northeast, 18 Aug 2024) is done. Correction cut the INSAT–GPM offset near the storm from ~12 km to ~4 km; see `case_northeast_20240818.md`. Run further cases with `scripts/run_validation_case.py`.

Generated with:

```bash
python scripts/find_validation_cases.py --years 2022 2023 2024
```

## Search

- **Regions:**
  - Northeast India: 22–29N, 89–97E (VZA ~33–38°)
  - Himalaya: 27–33N, 75–89E (VZA ~31–41°)

  Expected parallax shift for a 12–16 km top: **8–12 km**, 2–3× the Kochi case.
- **Season:** 1 Jun – 20 Sep 2022, 2023 and 2024. This keeps all cases in the summer yaw-flip state, where navigation errors are small (see `navigation_check.md`).
- **Selection:** GPM 2A Ku V08 orbits whose swath centre line crosses a region box.
- **INSAT timing:** the time INSAT-3DR scans the crossing latitude is estimated assuming scans start at HH:15/HH:45 and sweep 81N→81S in 26.9 min. Crossings within 5 min were kept.

| Stage | Northeast | Himalaya | Total |
| :--- | ---: | ---: | ---: |
| GPM crossings found | 339 | 506 | 845 |
| Within 5 min of an INSAT scan (`validation_candidates.csv`) | 115 | 177 | 292 |
| Also ≥ 300 km of track in the region and within 3 min (`validation_shortlist.csv`) | 53 | 88 | 141 |
| Priority set (`validation_priority.csv`) | 5 | 6 | 11 |

The priority set favours:
- **night to early morning** (16–02 UTC), when monsoon convection peaks over both regions;
- **June, August and early September**, when same-day navigation corrections worked (July had none);
- **within 2 min** of the INSAT scan;
- **≥ 500 km of track** in the region;
- **at most 2 cases per region and year.**

Whether a case actually contains convection is only known after downloading its GPM file. Expect roughly half to be useful. Replacements can be taken from `validation_shortlist.csv`.

## Priority cases and files to download

| Region | GPM time (UTC) | Δt GPM−INSAT [min] | VZA [°] | Track in region [km] | GPM 2A Ku (GES DISC, `GPM_2AKu.08`) | INSAT case scan (MOSDAC) | INSAT navigation scans (same day) |
| :--- | :--- | ---: | ---: | ---: | :--- | :--- | :--- |
| himalaya | 2022-06-03 18:23 | +0.5 | 36.2 | 740 | `2A.GPM.Ku.V10-20251112.20220603-S175214-E192443.046951.V08A.nc` | `3RIMG_03JUN2022_1815_L1C_SGP_V01R00.h5`<br>`3RIMG_03JUN2022_1815_L2B_CTP_V01R00.h5` | `3RIMG_03JUN2022_0415` and `_0615` L1C |
| himalaya | 2022-08-10 22:53 | -0.3 | 35.8 | 586 | `2A.GPM.Ku.V10-20251112.20220810-S222108-E235341.048012.V08A.nc` | `3RIMG_10AUG2022_2245_L1C_SGP_V01R00.h5`<br>`3RIMG_10AUG2022_2245_L2B_CTP_V01R00.h5` | `3RIMG_10AUG2022_0415` and `_0615` L1C |
| himalaya | 2023-06-30 23:23 | +0.0 | 37.2 | 740 | `2A.GPM.Ku.V10-20251112.20230630-S225144-E002417.053054.V08A.nc` | `3RIMG_30JUN2023_2315_L1C_SGP_V01R00.h5`<br>`3RIMG_30JUN2023_2315_L2B_CTP_V01R00.h5` | `3RIMG_30JUN2023_0415` and `_0615` L1C |
| himalaya | 2023-09-17 00:53 | -0.3 | 35.6 | 740 | `2A.GPM.Ku.V10-20251112.20230917-S002125-E015356.054269.V08A.nc` | `3RIMG_17SEP2023_0045_L1C_SGP_V01R00.h5`<br>`3RIMG_17SEP2023_0045_L2B_CTP_V01R00.h5` | `3RIMG_17SEP2023_0415` and `_0615` L1C |
| himalaya | 2024-06-25 01:23 | -0.4 | 34.9 | 698 | `2A.GPM.Ku.V10-20251112.20240625-S002144-E015456.058630.V08A.nc` | `3RIMG_25JUN2024_0115_L1C_SGP_V01R00.h5`<br>`3RIMG_25JUN2024_0115_L2B_CTP_V01R00.h5` | `3RIMG_25JUN2024_0415` and `_0615` L1C |
| himalaya | 2024-09-04 18:23 | +0.4 | 36.1 | 740 | `2A.GPM.Ku.V10-20251112.20240904-S175155-E192508.059738.V08A.nc` | `3RIMG_04SEP2024_1815_L1C_SGP_V01R00.h5`<br>`3RIMG_04SEP2024_1815_L2B_CTP_V01R00.h5` | `3RIMG_04SEP2024_0415` and `_0615` L1C |
| northeast | 2022-06-07 16:24 | +0.5 | 36.1 | 882 | `2A.GPM.Ku.V10-20251112.20220607-S155417-E172646.047012.V08A.nc` | `3RIMG_07JUN2022_1615_L1C_SGP_V01R00.h5`<br>`3RIMG_07JUN2022_1615_L2B_CTP_V01R00.h5` | `3RIMG_07JUN2022_0415` and `_0615` L1C |
| northeast | 2022-09-13 21:54 | +0.3 | 36.4 | 881 | `2A.GPM.Ku.V10-20251112.20220913-S205220-E222453.048540.V08A.nc` | `3RIMG_13SEP2022_2145_L1C_SGP_V01R00.h5`<br>`3RIMG_13SEP2022_2145_L2B_CTP_V01R00.h5` | `3RIMG_13SEP2022_0415` and `_0615` L1C |
| northeast | 2023-08-12 20:22 | -1.6 | 37.1 | 884 | `2A.GPM.Ku.V10-20251112.20230812-S192028-E205257.053721.V08A.nc` | `3RIMG_12AUG2023_2015_L1C_SGP_V01R00.h5`<br>`3RIMG_12AUG2023_2015_L2B_CTP_V01R00.h5` | `3RIMG_12AUG2023_0415` and `_0615` L1C |
| northeast | 2024-06-08 18:54 | +0.5 | 36.4 | 884 | `2A.GPM.Ku.V10-20251112.20240608-S182407-E195720.058379.V08A.nc` | `3RIMG_08JUN2024_1845_L1C_SGP_V01R00.h5`<br>`3RIMG_08JUN2024_1845_L2B_CTP_V01R00.h5` | `3RIMG_08JUN2024_0415` and `_0615` L1C |
| northeast | 2024-08-18 22:24 | +0.0 | 35.9 | 882 | `2A.GPM.Ku.V10-20251112.20240818-S215337-E232650.059478.V08A.nc` | `3RIMG_18AUG2024_2215_L1C_SGP_V01R00.h5`<br>`3RIMG_18AUG2024_2215_L2B_CTP_V01R00.h5` | `3RIMG_18AUG2024_0415` and `_0615` L1C |

- **Sizes:** each GPM orbit file is ~400 MB, each L1C ~100 MB and each CTP ~3 MB. About 700 MB per case, ~7.5 GB for all 11.
- **Suggested start (≈ 4 GB):** two cases per region:
  - Himalaya: 30 Jun 2023 23:23 and 4 Sep 2024 18:23
  - Northeast: 13 Sep 2022 21:54 and 18 Aug 2024 22:24
- **Where to put them:** `datasets/validation/<region>_<YYYYMMDD>/`.
- **Format:** the V07 HDF5 version of the same orbit (`2A.GPM.Ku.V9-*.V07A.HDF5`) works too, since the reader was tested on V07. V08 `.nc` files will be checked when the first one arrives.
- **Timing check:** the INSAT scan-time model (linear 81N→81S) is an estimate. Check it on the first real case.
