# Case Study: Kochi, 6 June 2022 (first real-data run)

Reproduce with `python scripts/run_kochi_case.py --data datasets`. Outputs (all git-ignored):

- `05_validation/gpm_colocation/kochi_20220606.json`: all numbers
- `04_corrected_output/netcdf/kochi_20220606_{1645,1715}_{corrected,uncorrected}.nc`
- `07_figures/kochi_20220606.png`

## Data

| Source | Files | Time at Kochi (10N) |
| :--- | :--- | :--- |
| INSAT-3DR L1C | `3RIMG_06JUN2022_1645`, `_1715` | ~16:57 and ~17:27 UTC (estimated from scan start/end) |
| INSAT-3DR L2B CTP | same two times | — |
| GPM 2A Ku V07 | orbit 046997 | 17:12:52 UTC |

The two INSAT scans fall **16 min before and 14 min after** the GPM pass.

## Method

- **Cloud-top height:** TIR1 BT → AFGL tropical profile (`pygeoparallax.cloudheight`). Cloudy where BT is > 8 K below ISRO's clear-sky BT (`CSBT_TIR1`).
- **Correction:** parallax correction at 74.0E, with no terrain (no DEM yet). Regridded to 0.02°, along with an uncorrected copy on the same grid.
- **GPM:** footprints rasterised to the same grid (nearest footprint within 3.5 km).

## Results

### 1. Cloud-top height from BT works, and ISRO's CTP is too low for deep convection

| | 16:45 | 17:15 |
| :--- | :---: | :---: |
| Pixels compared with ISRO CTP→height | 24,564 | 24,611 |
| Correlation, BT height vs CTP height | 0.86 | 0.86 |
| Mean bias, BT − CTP | +0.45 km | +0.51 km |
| Deep cores (BT < 220 K): BT height | 15.2 km | 15.2 km |
| Deep cores (BT < 220 K): CTP height | 13.3 km | 12.4 km |

The two heights agree well overall. For deep cores, though, ISRO's CTP (37 km boxes in 25 hPa steps) is 2–3 km lower. GPM radar echo tops reach **16.9 km**, and an echo top is normally *below* the cloud top. So the BT-based 15 km is the more realistic of the two, and ISRO's CTP underestimates deep convective tops. This supports using per-pixel BT heights.

### 2. Parallax shift at Kochi is small

- Kochi VZA is **12.0°** and VAA is 193°, so the satellite is to the south-southwest.
- Deep-core displacement: median **3.9 km**, max 4.8 km. That is about one INSAT pixel.

### 3. GPM validation is inconclusive for this case

| Scan | IoU uncorrected → corrected | Pearson uncorrected → corrected |
| :--- | :---: | :---: |
| 16:45 | 0.1128 → 0.1129 | 0.265 → 0.260 |
| 17:15 | 0.1065 → 0.1048 | 0.232 → 0.224 |

Compensating for storm motion (shifting each scan to the GPM time) also changed the metrics by ≤ 0.004. **This case cannot resolve a ~4 km correction.** There are three reasons:

1. **Storm motion is larger than the shift.** Between the scans the storm moved south-west at ~27 km/h south and ~22 km/h west, about 7.5 km in the 14–16 min between each scan and GPM. That is twice the parallax shift, and in nearly the same direction (towards the satellite).
2. **The fields don't measure the same thing.** Most GPM "convective" footprints near Kochi are shallow and warm-topped (median storm top 3.9 km), so they never appear cold in TIR1. Meanwhile the big storm's cold anvil extends well beyond its convective core. IoU stays around 0.1 regardless of alignment.
3. **An unexplained north-east preference.** Every alignment search, with or without correction or motion compensation, prefers shifting INSAT north-east, often to the edge of the search range. This may be anvil asymmetry (convection sits on the storm's eastern side) or an INSAT navigation error. **It needs a proper navigation check before any validation numbers are trusted.**

## What this means for the study

- Kochi is a weak test case for the method: low VZA means a small shift. Prefer high-VZA sites, where 8–11 km shifts exceed motion errors: Agartala / Northeast India (VZA 34°) and the Himalayas (VZA ~36°).
- Match times more closely. Either pick GPM passes within ~5 min of the INSAT scan time at that latitude, or use motion compensation, as tried here.
- Validate with fields that relate more directly: e.g. INSAT deep cores vs GPM storm tops above 10 km, rather than BT vs near-surface reflectivity.
- Check INSAT navigation against a coastline dataset on a clear-sky scene. This comes first.
