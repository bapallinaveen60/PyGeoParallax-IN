# Prior work on cloud parallax for Indian geostationary imagers (INSAT-3D/3DR/3DS, Kalpana-1, INSAT-2/3 VHRR)

Search date: 30 Oct 2026. Goal: try to falsify the manuscript claim that, to the authors' knowledge, no parallax correction or validation has been published for INSAT-3D or INSAT-3DR.

## Verdict (short)

**The claim is false as worded. It needs to be narrowed.**

1. **A parallax correction for INSAT-3D *is* documented.** The official ISRO/SAC *INSAT-3D ATBD Document, May 2015* (hosted on MOSDAC) describes the operational Hydro-Estimator rain product (3DIMG_L2B_HEM). Its section "(c) Orography and Parallax correction" says the HE "adjusts the horizontal location of the satellite pixel prior to rain rate computation, based on cloud height (using Tb and standard atmosphere) and satellite zenith angle" (after Vicente et al. 2002). Two IMD-authored papers repeat this: Malhan et al. 2022 (*Mausam*) and Singh et al. 2019 (*J. Hydrol.*).
2. **No validation or quantification was found.** None of the sources quantifies INSAT parallax displacement, validates a parallax-corrected INSAT product against radar, GPM or any other independent truth, or publishes a general-purpose correction (L1/L1C geometry). The same holds for Kalpana-1 and INSAT-3DS. The correction appears only as one internal step inside the HE rain algorithm, inherited from the NOAA H-E. It is never evaluated separately.
3. **There is an internal inconsistency in ISRO's own documents.** The later *revised* HEM ATBD (Varma & Gairola, SAC/EPSA/AOSG/SR/04/2015, March 2015) lists only warm-top and orographic corrections. It cites Vicente et al. (2002) for orography only and never describes a parallax step. Whether operational HEM actually applies parallax shifting today cannot be confirmed from public documents.
4. **Other Indian work only mentions parallax qualitatively.** This includes cyclone centre fixing and ADT (Goyal et al. 2017), TC energy metrics (Mohapatra & Vijay Kumar 2017), and Kalpana-1 vs MISR cloud-motion winds (Deb et al. 2015). Some studies use ad-hoc spatial buffers for "cloud–rain displacement" (Gogoi et al. 2026 preprint, up to 20 km).

**Suggested rewording:** "Apart from a geometric parallax shift described as an internal step of the operational INSAT-3D Hydro-Estimator rain algorithm (ISRO/SAC ATBD, 2015), which to our knowledge has never been separately documented, quantified or validated, we found no published parallax correction, parallax quantification, or validation of parallax-corrected INSAT-3D/3DR imagery against independent observations." The manuscript should cite the 2015 ATBD (and possibly Malhan et al. 2022) rather than claim absolute absence.

---

## A. Work that applies, or says it applies, a parallax correction to Indian GEO imagery

### A1. ISRO/SAC, *INSAT-3D ATBD Document*, May 2015: Hydro-Estimator chapter. **Key finding**
- URL: https://mosdac.gov.in/docs/INSAT_3D_ATBD_MAY_2015.pdf (379 pp.; linked from MOSDAC "INSAT-3D references" page https://www.mosdac.gov.in/insat-3d-references). Downloaded and text-searched.
- Chapter 4(B) "Rainfall Estimation – H-E Method", algorithm identifier `3DIMG_L2B_HEM`. Algorithm spec: "Version 1.0, 14.02.2007, Atul K. Varma, R M Gairola, QPE from HE Baseline Document".
- Section 4.4, item "(c) Orography and Parallax correction", pp. 75–76, verbatim:
  > "Orography adjustment is carried out using 850 hPa Winds and topography from a digital elevation model at 4 km resolution to derive vertical component of wind (Vicente et al., 2002). This vertical wind component is then scaled into a multiplicative adjustment to the rain rate.
  > The parallax correction described in the same paper, adjusts the horizontal location of the satellite pixel prior to rain rate computation, based on cloud height (using Tb and standard atmosphere) and satellite zenith angle."
- Nature of the correction: Tb → standard-atmosphere height → zenith-angle shift, applied before the rain-rate computation. There is no quantification of the shift magnitude and no validation of the shift itself; Section 4.6 validates rain totals only. The word "parallax" appears only in this paragraph and in the Vicente et al. reference.
- Same ATBD, GPI/IMSRA chapter (4A): **no parallax step** (negative result).
- Category: **applies (documented operational step); not quantified; not validated.**

### A2. Varma & Gairola (2015), revised HEM ATBD. Shows the inconsistency
- Varma, A. K. and Gairola, R. M., March 2015. *Algorithm Theoretical Basis Document: Hydro-Estimator (Modified)*. SAC/EPSA/AOSG/SR/04/2015, Space Applications Centre, ISRO, 29 pp. URL: https://dr.mosdac.gov.in/docs/HEM_rain-revised-atbd.pdf (dr.mosdac.gov.in timed out from curl; the same file was retrieved from https://mosdac.gov.in/docs/HEM_rain-revised-atbd.pdf).
- Corrections described: 2.2 warm-top modification and 2.3 orographic correction. Section 2.3 verbatim: "The orographic correction is carried out by determining by gradient of the elevations in the direction of the prevailing 850 mb level winds (Vicente et al., 2002)."
- The word "parallax" appears **only** in the reference title of Vicente et al. (2002). There is no description of a parallax step.
- Also cites an earlier ATBD: "Varma, A. K., and R.M. Gairola, 2007, Algorithm Theoretical Basis Document for Hydro-estimator Method, in 'INSAT Geophysical Parameter Retrieval System – ATBD Document', report# SAC/IMDPS/TN-05/Version-1, pp 62-78." Not found online. It is probably the origin of the A1 text.
- Category: **mentions only (citation)**. This reference weakens any claim that the operational HEM still applies parallax shifting.

### A3. Malhan, Sehgal, Giri, Mishra et al. (2022), *Mausam* 73(4): 833–842
- "Comparative analysis of sub-division wise rainfall INSAT-3D vs. Ground based observations." DOI: https://doi.org/10.54302/mausam.v73i4.5877 (full text PDF from mausamjournal.imd.gov.in, galley 5877/5557).
- Verbatim (introduction): "Hydro Estimator (HE) method involves both convective as well as non-convective type of precipitation environment with suitable corrections /adjustment for wet dry environment, warm top modification along with orography with parallax corrections with the help of temperature dependent parameter suitable for Indian domain."
- Category: **states that the operational INSAT-3D HE product includes parallax correction** (secondary description by IMD authors). Not quantified.

### A4. Singh, Tripathi, Singh, Singh & Sateesh (2019), *J. Hydrology* 575: 1371–1379
- "Comparison of different satellite-derived rainfall products with IMD gridded data over Indian meteorological subdivisions during Indian Summer Monsoon (ISM) 2016 at weekly temporal resolution." DOI: 10.1016/j.jhydrol.2019.02.016.
- Google Scholar snippet only (ScienceDirect returned 403): "…been applied to the estimates product such as parallax correction (satellite viewing angle), …" The context is the INSAT-3D HE/IMSRA description.
- Category: **states the correction is applied** (secondary). Full text not verified.

### A5. Kumar, Singh, Awasthi & Singh (2019), IGI Global book chapter
- "Natural Hazard: Tropical Cyclone – Evaluation of HE and IMSRA Over CS KYANT", in *Advances in Systems Analysis, Software Engineering, and HPC*, pp. 124–141. DOI: 10.4018/978-1-5225-7784-3.ch006.
- Scholar snippet only: "The various corrections and adjustments are applied to the estimates product such as parallax …"
- Category: **states it is applied** (secondary, same boilerplate as A4). Not verified beyond the snippet.

### A6. Singh, Singh, Singh, Tripathi, Kumar & Soni (2018), *J. Indian Soc. Remote Sens.* 46: 927–
- "A Case Study: Heavy Rainfall Event Comparison Between Daily Satellite Rainfall Estimation Products with IMD Gridded Rainfall Over Peninsular India During 2015 Winter Monsoon." DOI: 10.1007/s12524-018-0751-9.
- The Scholar snippet shows "INSAT … parallax …" in the INSAT-3D description. Paywalled; the context was not verified but is most likely the same HE boilerplate.
- Category: **probably mentions/describes the HE parallax step**. Unverified.

---

## B. Work that discusses parallax for Indian GEO imagery qualitatively (no correction, no numbers)

| # | Citation | What it says | Verified? |
|---|---|---|---|
| B1 | Goyal, S., Mohapatra, M., Kumari, P., Dube, S. K., Rajendra, K. (2017). Validation of Advanced Dvorak Technique (ADT) over north Indian Ocean. *Mausam* 68(4): 689–698. https://doi.org/10.54302/mausam.v68i4.768 | "While Meteosat-7 is located near 57.5° E, INSAT-3D is located near 82° E. The error for the TCs over the Arabian Sea may be due to different adjustments followed for avoiding parallax error. The parallax error can not only lead to error in estimation of location of center of TC, but also its intensity…" | Yes, full PDF |
| B2 | Mohapatra, M., Vijay Kumar, V. (2017). Interannual variation of tropical cyclone energy metrics over North Indian Ocean. *Clim. Dyn.* 48: 1431–. DOI 10.1007/s00382-016-3150-3 | Scholar snippet: "…geostationary satellite INSAT-3D, Kalpana-1, METEOSAT-7 have different resolutions, different orbital positions and different parallax errors etc." | Snippet only (paywall) |
| B3 | Deb, S. K., Kaur, I., Kishtawal, C. M., Pal, P. K. (2015). A comparative assessment of Kalpana-1 and MISR cloud tracked winds over the Indian Ocean region. *Theor. Appl. Climatol.* 121: 425–. DOI 10.1007/s00704-014-1246-4 | Scholar snippet: "The increase of errors in the meridional component is due to parallax and MISR orbit…" (MISR stereo-height context) | Snippet only |
| B4 | Ramachandran, M. P., Agarwal, M. K., Daniel, D. A. (2020). Efficient onboard image motion compensation for orbital inclination and eccentricity of geostationary weather satellites. *Proc. IMechE Part G* 234: 1311–. DOI 10.1177/0954410019900706 | Scholar snippet on INSAT-3DR: "…co-registers the images as done in INSAT 3DR… this causes a parallax effect in the cloud position…". This is orbit-inclination/registration geometry, not cloud-height parallax correction. | Snippet only (403) |
| B5 | Kiran Kumar, A. S. (2016). Tools from the Indian space programme for observing and forecasting extreme weather events – Retrospect and prospect. *Mausam* 67(1): 77–92. https://doi.org/10.54302/mausam.v67i1.1147 (OpenAlex lists the author as "Akhilesh Kumar"; the PDF says A. S. Kiran Kumar, ISRO) | Describes the HE corrections (orographic, warm-cloud). Cites Vicente et al. (2002) **only for orography**. "Parallax" appears only in the reference title. | Yes, full PDF |
| B6 | Sateesh, M., Khadke, C., Prasad, V. S., Goyal, S. (2021). Validation of satellite estimated convective rainfall products: a case study for the summer cyclone season of 2020. *Mausam* 72(1): 229–236. https://doi.org/10.54302/mausam.v72i1.137 | Describes the NWCSAF CRR (Meteosat-8 IODC) corrections and cites Vicente et al. (2002) for orography. "Parallax" appears only in the reference title. | Yes, full PDF |
| B7 | Gogoi, R. B., Singh, P. S., Kundu, A., Chaari, A., Srivastava, A., Sarma, K. (2026). Enhancing Thunderstorm Potential Area Detection over Northeast India Using INSAT series of Data: A Deep Learning Approach. Research Square preprint, doi:10.21203/rs.3.rs-10978955/v1 | INSAT-3D/3DR convective segmentation validated against IMERG and lightning "incorporating spatial tolerance (buffer distances up to 20 km) … to account for cloud–rain displacement". The ad-hoc buffer is an implicit acknowledgement of displacement. There is no parallax model, and parallax is not named. | Abstract verified |
| B8 | Chatterjee, K., Khan, M. S. R., Bala, B. et al. (2026). HoST: integrating Heuristic knowledge with attention-based LSTM networks for Thunderstorm prediction. *Sci. Rep.* doi:10.1038/s41598-026-57889-1 | Generic: "…parallax effects in geostationary imagery…" as a fusion challenge. INSAT-3D/3DR is listed only as *future work*. | Yes, HTML |

## C. Indian GEO–radar/LEO collocation studies checked that do not mention parallax (negative evidence)

These are the places where a correction would be expected. Each source was checked by full text where possible.

- **IMSRA calibration** (Kalpana-1 / INSAT-3D IR+WV collocated with TRMM-PR): Gairola et al. (2020), *Atmósfera* 33: 33–49, doi:10.20937/atm.52630, "Synergy between INSAT-3D infra-red and GPM microwave radiometer…". Its full text (SciELO) describes "a proper spatial and temporal collocation of Kalpana-1 IR BTs with TRMM-precipitation radar (PR) surface rain rate" and "collocated passes of GPM", with **no parallax mention**. The Atmósfera 2015 (28: 51–61) Kalpana-1 + gauge paper also has no parallax mention (redalyc PDF searched).
- **Prakash, Mahesh, Gairola & Pal (2010)**, *Meteorol. Atmos. Phys.* 110: 45–57, doi:10.1007/s00703-010-0106-8 (Kalpana-1 VHRR rainfall). It cites Vicente et al. (2002) in its references. Its abstract does not mention parallax, and the body is paywalled. **Caution:** a web-search summary attributed Vicente et al.'s abstract sentence ("step by step description of the procedure to correct … for parallax error and orographic effects") to this paper. That is a misattribution from a citation snippet.
- **Mishra et al. (2023)**, *Weather* 78: 224–227, doi:10.1002/wea.4443, and **Mishra et al. (2026)**, Springer Atmospheric Sciences chapter, doi:10.1007/978-981-95-5409-6_11. Both reconstruct radar reflectivity from INSAT-3D + GPM DPR. **Mishra, Chhari, Kumar, Shukla et al. (2025)**, *Theor. Appl. Climatol.* 156: 428, doi:10.1007/s00704-025-05650-5 (pySTEPS nowcasting of the satellite reflectivity). Full texts were paywalled or 403. The visible abstract and summary text did not mention parallax. Error sources listed: platform differences, resolution, shallow storms, terrain. **Not fully verified.** These are the most likely place for an undisclosed correction and are worth checking with institutional access.
- **Lima et al. (2019)**, *Remote Sens.* 11: 2811, doi:10.3390/rs11232811 (INSAT-3D CTT vs CALIOP/radiosonde). Full PDF searched: **no "parallax"**. The NRSC/NICES technical documents CTT50.pdf and cm4.pdf (cloud mask) also have none.
- **Kishtawal-group and IMD AMV documents**: Sant Prasad (IWW7, Kalpana CMV), Deb (IWW11, IWW13, IWW14 talks/papers on INSAT-3D/3DR AMVs). None mention parallax. Height assignment is discussed, but not parallax.
- **INSAT-3DR rapid-scan paper** (*Current Science* 120(6): 1026, 2021): no parallax or navigation mention.
- **Bhatt & Padmanabhan (2018)**, arXiv:1805.08706, "Automatic Data Registration of Geostationary Payloads for Meteorological Applications at ISRO": registration only, no cloud-height parallax.
- **IMD documents**: IMDPS lecture notes (imdpune LN_11_63), the IMD merged lightning + INSAT product description (internal.imd.gov.in/section/satmet/lightning/discription_file.pdf, which notes a ~1 h time mismatch but no parallax), and the *Mausam* 2024 HE block-level paper (75(3): 759–768). None mention parallax.
- **Other MOSDAC documents** searched in full: Incremental-ATBD-12Feb2020 (228 pp., INSAT-3D/3DR incremental products), INSAT3D_Products.pdf, ATBD_INSAT-3D_SST_REV_V1.1, INSAT_AOD_ATBD_revised, INSAT3D_COTS, V1_INSAT3D_ProductTypes, and INSAT_Product_Version_information_V01 (SAC/SIPG/ODPD/MMDRPS/TN-01/AUG-2022, a scanned PDF read visually). **None mention parallax.** No INSAT-3DS-specific ATBD was found on MOSDAC; the INSAT-3DS page links no ATBD.

## D. False positives and items worth noting but not relevant

- NWP SAF AMV Analysis Report AR11 (Etheridge et al. 2025, NWPSAF-MO-TR-044). The Scholar snippet merged an INSAT bias note with "linked to parallax correction", but the parallax sentence refers to **Metop LEO AMVs**, not INSAT (verified in the full PDF).
- Mahajan & Fataniya (2019/2020), *Complex Intell. Syst.*: the parallax mention is for Sentinel-2 Fmask, not INSAT.
- Rafi et al. (2026), Merged-IMSRA for an MCS over Bali (*GeoScienceEd*). This is Indonesian and applies the IMSRA method to non-Indian data; the parallax mention cites a EUMETSAT 2008 radar–satellite parallax paper. Full text was not retrievable.
- Mohan, M., Agarwal, V. K. (1990). "Stereo simulation of cloud images and the cloud depth retrieval using an …", Proc. Seminar on Advances in …, Indian Geophysical Union (Scholar citation only). This is early SAC work on stereo/parallax cloud-height *simulation*. It is not confirmed to involve INSAT; it may be worth an interlibrary request if completeness matters.
- Ilanthiryan, Mathur, Agarwal (1992), *J. Indian Soc. Remote Sens.*, doi:10.1007/BF02991885: ERS-1 ATSR stereo cloud height, which is LEO, not an Indian GEO imager.
- DebasishDhal/Thesis_Repository (GitHub, MSc thesis, INSAT-3DR + CloudSat collocation ML cloud-top height): no parallax handling mentioned in the README. A web-search summary quoted "potential of parallax bias" in INSAT-3D CTH work, but no source for that phrase could be found. Treat it as unverified or hallucinated.
- PyGeoParallax-IN itself (Zenodo doi:10.5281/zenodo.23666957, GitHub bapallinaveen60/PyGeoParallax-IN) is the only hit for "parallax" + "INSAT-3DR" in OpenAlex titles and abstracts.

---

## Databases and queries actually run

| Source | Status | Queries (examples) | Outcome |
|---|---|---|---|
| OpenAlex API (`search=`, `filter=fulltext.search:`, `title_and_abstract.search:`) | Worked (no API key; shared daily budget warning) | parallax INSAT; parallax Kalpana; parallax INSAT-3DR; parallax INSAT-3D; "parallax correction" INSAT; parallax MOSDAC; parallax "Hydro-Estimator" India; parallax INSAT radar / GPM / TRMM / cyclone; parallax Kalpana TRMM; parallax VHRR cloud; parallax INSAT-3DS (0 hits); "cloud top" displacement INSAT | Hits: Malhan 2022, Goyal 2017, Kiran Kumar 2016, Sateesh 2021, HoST 2026, Gogoi 2026 plus false positives. Title/abstract "parallax" + INSAT/Kalpana returns only PyGeoParallax-IN. |
| Google Scholar (HTML) | Worked for ~9 result pages, then redirected (likely bot check); stopped, no circumvention | parallax INSAT (pages 1–6); parallax "INSAT-3D" (pages 2–3); parallax "Kalpana-1" and parallax "INSAT-3DR" (few results / redirects) | Added Singh 2019 J Hydrol, Singh 2018 JISRS, Kumar 2019 IGI, Mohapatra 2017, Deb 2015, Ramachandran 2020, Mohan & Agarwal 1990 |
| Europe PMC full-text REST | Worked | parallax AND INSAT (0); parallax AND Kalpana (7, all irrelevant: ophthalmology, vision); parallax AND MOSDAC (0); "cloud top" AND displacement AND INSAT (2: Gogoi 2026, Jash 2026) | Gogoi preprint |
| CrossRef API | Worked (metadata only) | parallax INSAT; parallax Kalpana; parallax correction Indian geostationary satellite; INSAT cloud top height displacement | Only MOSDAC product DOIs (10.19038/sac/10/…) and non-Indian papers |
| Semantic Scholar API | **Blocked** (HTTP 429 on all attempts, including retries) | — | — |
| MOSDAC document library | Worked for www.mosdac.gov.in; dr.mosdac.gov.in timed out by curl and WebFetch | INSAT-3D/3DR reference pages; all linked ATBDs downloaded and text-searched | A1 (key), A2 |
| Mausam journal OJS search | Worked, metadata only | "parallax" → 0 results (metadata index) | Full-text hits came via OpenAlex/Scholar instead |
| ias.ac.in (JESS, Current Science archive) | **Blocked** (HTTP 403 for curl and WebFetch) | — | JESS papers (e.g. 130:0037 INSAT-3D IMSRA, 121:1113 Kalpana, SATCON 131:169) not text-searched |
| ScienceDirect, Wiley, SAGE full text | 403 / paywalled | — | Only Scholar snippets for A4, B4 |
| Springer full text | Paywalled (reference lists visible) | — | Prakash 2010 cites Vicente 2002; context not visible |
| ResearchGate | 403 | — | — |
| Shodhganga | Search page returned no parseable results; web searches found no relevant thesis | "Shodhganga thesis INSAT Kalpana rainfall parallax" | Negative |
| WebSearch (standard and extended), ~20 queries | Worked | INSAT-3D parallax correction cloud top height; Kalpana-1 parallax convective; INSAT-3D Hydro-Estimator ATBD parallax MOSDAC; INSAT parallax DWR collocation; Kalpana/INSAT parallax TRMM; INSAT-3DR nowcasting radar parallax deep learning; INSAT-3D AMV height parallax navigation; INSAT-3D navigation accuracy; INSAT/Kalpana lightning LIS parallax; INSAT-3D CALIPSO CloudSat parallax; stereo INSAT-3D INSAT-3DR; Kalpana HE Varma Gairola parallax; INSAT-3DS ATBD; IMD training notes parallax; EGU/AGU/IGARSS parallax Kalpana/INSAT; INSAT-3D GPM DPR reflectivity parallax; overshooting top / cloud-top cooling radar parallax India; Kalpana cyclone centre parallax; site:currentscience.ac.in, site:ias.ac.in, JISRS | No study quantifying or validating INSAT parallax. No INSAT-3D/3DR stereo study. No EGU/AGU/IGARSS/TROPMET/ISRS abstract found. |

### Gaps that remain
- Scopus and Web of Science were not available.
- JESS and Current Science full texts (ias.ac.in, 403) were not searched.
- The Mishra et al. INSAT-3D+GPM reflectivity papers (2023, 2025, 2026) are paywalled.
- The 2007 SAC/IMDPS/TN-05 HE ATBD is not online.
- TROPMET/ISRS proceedings are not indexed online.
- A Scopus full-text query `TITLE-ABS-KEY(parallax) AND ALL(INSAT OR Kalpana)` plus a check of the three Mishra papers would close most of the remaining risk.
