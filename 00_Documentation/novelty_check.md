# Novelty Check (26 Oct 2026)

**Two of the four claims hold as written and two need narrowing. No published parallax correction or parallax validation for INSAT-3D/3DR was found. INSAT-3DR geolocation error, however, is already measured routinely by ISRO, and open-source parallax correction exists in satpy.**

Searched: web search over Mausam, Current Science, Journal of the Indian Society of Remote Sensing, MOSDAC/ISRO documents, Copernicus journals and software documentation, with queries combining INSAT-3D/3DR, Kalpana-1, parallax, navigation, geolocation, GPM/DPR and Hydro-Estimator. This is a web search, not a database search: **a Google Scholar / Scopus check of "INSAT" + "parallax" is still needed before submission.**

## Claims

| Claim in the draft | Verdict | Evidence | How to write it |
| :--- | :--- | :--- | :--- |
| First quantified parallax correction for INSAT-3D/3DR imagery | **Holds (no prior work found)** | No INSAT/Kalpana parallax study found in Indian journals or MOSDAC documents. The GOES Hydro-Estimator has applied the Vicente et al. (2002) parallax correction since 2001 (NOAA/NESDIS AMS paper); ISRO adapted the Hydro-Estimator for Kalpana/INSAT, but whether the INSAT version keeps the parallax step is not documented in what was found. | "To our knowledge, the first quantified parallax correction and validation for INSAT-3DR imagery." Add: check ISRO's Hydro-Estimator ATBD. |
| First validation of INSAT parallax against spaceborne radar (GPM) | **Holds** | Indian GPM work found concerns ground-radar calibration (Saini et al., URSI 2023), reflectivity reconstruction from the INSAT-3D storm index (Mishra et al., 2023) and parallax-aligned ground radar vs TRMM (Sharma & Kannan poster); none corrects INSAT parallax. | As written. |
| INSAT-3DR navigation error affects parallax validation | **Narrow it** | ISRO's MOSDAC Data Quality Evaluation reports measure geolocation error per image against ground control points. INSAT-3DR full disk L1B, 19 Jun 2020 12:15 UTC: mean error 2.6 IR pixels north and 1.0 pixel west (CE90 3.9 pixels; points 4.6–16.7 km north). INSAT-3D, Feb 2017: CE90 about 13–19 km. So the **existence** of km-scale geolocation error is known. | Claim the new parts only: (1) a multi-year (2022–2024) characterisation of the L1C error from coastlines, with its **seasonal switch**; (2) the finding that in the monsoon it partly **cancels the parallax**, so parallax-only correction overshoots; (3) that per-day correction is not possible in monsoon cloud. Cite the MOSDAC DQE reports as the operational baseline. |
| Seasonal (yaw-flip) pattern of the error | **Partly supported, still a hypothesis** | The 2019 vs 2020 DQE reports show different yaw residuals (~0.02° vs ~0.2°), consistent with a date-dependent attitude bias, but no document found describes a seasonal yaw flip for INSAT-3DR. | Keep "consistent with the twice-yearly yaw flip" as a hypothesis; ask ISRO/SAC or check the IMD SatMet SOP. |
| Open-source tool | **Narrow it** | satpy has an open-source parallax correction (`satpy.modifiers.parallax`: spherical Earth, gridded height data, no terrain, not applied by default); wradlib corrects spaceborne-radar parallax (a different problem). | Claim what satpy lacks: an INSAT-3DR-specific pipeline (L1C/CTP/GPM readers), ellipsoid solver with terrain, navigation correction, occlusion-aware resampling with paired uncorrected/corrected output, and the validation tools. |

## Consequences for the paper

- **Introduction:** cite Vicente et al. (2002) and the GOES Hydro-Estimator as precedent, satpy as the existing open-source correction, and the MOSDAC DQE reports as the operational geolocation baseline. State the gap: no correction or validation for INSAT-3DR, and no assessment of how its navigation error interacts with parallax.
- **Comparison with ISRO's DQE:** ISRO's June 2020 L1B error (about 10 km north) is larger than our 2022–2024 monsoon L1C estimate (2.5–5 km north). The products, years and methods differ (L1B vs L1C; GCP chips vs coastlines). Worth one sentence in the Discussion.
- **Still to check:** Google Scholar / Scopus; ISRO's Hydro-Estimator ATBD (does it correct parallax?).

## Follow-up (26 Oct 2026)

- **ISRO Hydro-Estimator ATBD:** found — "Hydro-Estimator (Modified)", Varma & Gairola, SAC/EPSA/AOSG/SR/04/2015 (https://dr.mosdac.gov.in/docs/HEM_rain-revised-atbd.pdf). The MOSDAC server did not respond to automated download, so whether it applies a parallax correction is **not yet checked**; open it in a browser and search for "parallax". MOSDAC's product page says the INSAT implementation follows the NOAA/NESDIS Hydro-Estimator (which uses the Vicente et al. 2002 correction).
- **INSAT-3DS:** no parallax or geolocation-correction study found for INSAT-3DS (2024–2025). The closest INSAT work is an EGU 2026 abstract on INSAT-3D cloud-fraction biases (Ramachandran & Dey), which does not address parallax. The claim "no published parallax correction for INSAT-3D/3DR" can be extended to INSAT-3DS.
- **Related method worth citing:** Wiltink, Deneke, van Heerwaarden & Meirink (2025), "Evaluating parallax and shadow correction methods for global horizontal irradiance retrievals from Meteosat SEVIRI", AMT 18, 3917–3936, https://doi.org/10.5194/amt-18-3917-2025 (verified in Crossref). It compares geometric parallax correction with an empirical shift that maximises correlation with ground observations — the same idea as our field-correlation offset measure.

## Sources

- MOSDAC DQE report, INSAT-3DR IMG full disk, 19 Jun 2020 12:15 UTC: https://www.mosdac.gov.in/filebrowser/download/2042/11318?fid=11318
- MOSDAC DQE reports, INSAT-3D IMG, Feb 2017 (e.g.): https://www.mosdac.gov.in/filebrowser/download/2042/8275?fid=8275
- satpy parallax module: https://satpy.readthedocs.io/en/latest/api/satpy.modifiers.parallax.html
- wradlib `correct_parallax`: https://docs.wradlib.org/projects/old-docs/en/1.19.0/generated/wradlib.georef.satellite.correct_parallax.html
- GOES Hydro-Estimator and its Vicente et al. parallax correction (NOAA/NESDIS, AMS): https://ams.confex.com/ams/pdfpapers/134462.pdf
- INSAT Hydro-Estimator (ISRO/SAC): https://dr.mosdac.gov.in/HeavyRain_Insat3D/assets/documents/HE-intense-rain.pdf
- Bieliński (2020), Remote Sensing 12(3), 365: https://doi.org/10.3390/rs12030365
- Saini, Das & Jha, URSI GASS 2023 (ground radar vs GPM over India): https://2021.ursi.org/proceedings/procGA23/papers/YSASummarySainiShrutiC.pdf
- Sharma & Kannan, IIT Bhubaneswar poster (ground radar vs TRMM with parallax alignment): https://old.iitbbs.ac.in/national-science-day-2020/posters/Alok%20Sharma.pdf
- Mishra et al. (2023), reconstructed radar reflectivity from GPM DPR and the INSAT-3D storm index: https://bibliotheque.meteo.fr/pub/DOC00056463-reconstructing-radar-reflectivity-integrating-gpm.html
