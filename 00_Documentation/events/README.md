# Validation Event Candidates

`gpm_overpasses_jjas_2022_2024.csv` lists every GPM 2A.DPR (V08) orbit whose swath passed within 150 km of an IMD radar site during JJAS 2022–2024. It was generated with:

```bash
python scripts/find_gpm_overpasses.py --years 2022 2023 2024 --out 00_Documentation/events/gpm_overpasses_jjas_2022_2024.csv
```

| Column | Meaning |
| :--- | :--- |
| `overpass_utc` | Estimated time of closest approach, accurate to about 1 minute. Use the 2A.DPR scan time once the file is downloaded. |
| `nadir_dist_km` | Distance from the radar site to the GPM ground track. |
| `site_in_swath` | `True` if the site is within the ~245 km Ku-band swath (≤ 122.5 km from nadir). |
| `url` | GES DISC download link (needs an Earthdata login). |

Radar coordinates in the script are approximate; check them against IMD metadata.

**Next step:** filter the `site_in_swath == True` rows down to raining overpasses. This means downloading those granules and checking `typePrecip` / `precipRateNearSurface` near each site. Then confirm that INSAT-3DR L1C and CTH exist on MOSDAC for each chosen time.
