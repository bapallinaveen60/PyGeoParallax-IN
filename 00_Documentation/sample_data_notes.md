# Sample Data Notes (checked 20 Oct 2026)

Local folder `datasets/` (git-ignored, 3.2 GB).

## What is there

| Data | Files | Coverage |
| :--- | :--- | :--- |
| INSAT-3DR Imager L1C sector (`3RIMG_*_L1C_SGP_V01R00.h5`) | 19 scans | **30 Sep 2022**, 03:45–23:45 UTC (gaps between scans) |
| GPM 2A Ku V07 (`2A.GPM.Ku.V9-20211125.*.V07A.HDF5`) | 3 orbits | **1, 3 and 6 Jun 2022** |

The INSAT and GPM files **share no date**, so they cannot be colocated yet.

## Matching INSAT scans to download

Read from the GPM files themselves (time the orbit crosses India, and where the convection is):

| GPM orbit | Over India (UTC) | Convection | Download from MOSDAC |
| :--- | :--- | :--- | :--- |
| 046997 | 6 Jun 2022 17:11–17:20 | **Over Kochi** (10.0N 76.2E), tops up to 16.9 km; passes almost directly over the Kochi DWR | `3RIMG_06JUN2022_1645` and `_1715` L1C, plus CTH |
| 046911 | 1 Jun 2022 05:10–05:20 | Bay of Bengal (17.6N 87.0E), tops up to 17.4 km | `3RIMG_01JUN2022_0445` and `_0515` L1C, plus CTH |
| 046950 | 3 Jun 2022 16:44–16:47 | Andaman Sea only (11.8N 96.7E) | Low priority |

Kochi on 6 Jun is the best case: deep convection right over a radar site, with GPM directly overhead. Kochi has a small VZA (12°), so the expected shift is small (~3 km for a 15 km top).

For 30 Sep 2022, the only GPM pass near a radar site in the overpass list is orbit 048795 at ~06:44 UTC, 186 km from Agartala and outside the Ku swath. The matching INSAT file (`0645`) is already here.

## The L1C file format (now read by `pygeoparallax.ingest.read_insat_l1c`)

- **Grid:** Mercator on WGS84, `lon_0 = 75`, true scale at the equator, ~4 km pixels. 3207 × 3062 pixels covering 50S–50N, 20–130E.
- **Channels:** 10-bit counts with 1024-entry lookup tables.
  - TIR1, TIR2, WV and MIR → brightness temperature [K]
  - VIS → albedo [%]
  - SWIR → radiance
- **No cloud-top height in L1C.** ISRO's `3RIMG_L2B_CTP` was checked on 6 Jun 2022 and has **no height either**. It gives CTP [hPa, 25 hPa steps], CTT and emissivity on ~37 km boxes, plus clear-sky BTs. Its `Nominal_Central_Point` attribute says 82E, which is wrong: its lat/lon arrays are centred on 74E. The pipeline derives height per pixel from TIR1 BT instead (see `case_kochi_20220606.md`).
- **ISRO's angle fields are offset.** `Sat_Elevation`/`Sat_Azimuth` disagree with our geometry by ~1° VZA and ~1.1° azimuth. At the sub-satellite point they give elevation 90.86°, which is impossible. Our angles agree with pyorbital to 0.01°, so the reader ignores ISRO's angle fields.
- `Sun_Elevation`/`Sun_Azimuth` also differ by up to several degrees from a single-time solar calculation. Part of this is the ~27-minute scan time, which the reader does not model per row yet.

## Still to check

- **Navigation accuracy:** checked (see `navigation_check.md`). Positions are ~7–9 km too far east in the most reliable windows, and the error may vary by region.
- `3RIMG_30SEP2022_1315_L1C_SGP_V01R00.h5` is a truncated download (30 MB of 88 MB); re-download it if needed.
- Whether `X`/`Y` are pixel centres or edges. Assumed centres; the difference is at most 2 km.
