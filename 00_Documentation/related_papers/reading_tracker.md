# Reading Tracker: Parallax Correction Literature

Literature search: 20 Oct 2026. DOIs and links were checked during the search except where marked *unverified*.

## Core methods

| Paper | Method | Relevance | Access | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Vicente, Davenport & Scofield (2002)**, *Int. J. Remote Sens.* 23, 221–230. "The role of orographic and parallax corrections on real time high resolution satellite rainfall rate distribution" | Analytical GOES parallax correction (ellipsoid enlarged by cloud height) plus orographic adjustment inside the NESDIS Hydro-Estimator | Baseline method to cite | No open-access copy; get it through the IITH library. **[vicente_2002.pdf](vicente_2002.pdf) is a one-page placeholder, not the paper.** | ⏳ To Read |
| **[Bieliński (2020)](bielinski_2020.pdf)**, *Remote Sens.* 12(3), 365. [doi:10.3390/rs12030365](https://doi.org/10.3390/rs12030365) | Augmented Vicente/Koenig method (cm-level accuracy) and geodetic Newton iteration (near-zero error) | Main reference for the GEO-to-radar geometry | Local PDF / [MDPI](https://www.mdpi.com/2072-4292/12/3/365) | ⏳ To Read |
| **Kotarba (2026)**, *AMT* 19, 6193–6208. Preprint [doi:10.5194/egusphere-2026-1500](https://egusphere.copernicus.org/preprints/2026/egusphere-2026-1500/) | Cloud-top height from the 11 µm channel only (moist adiabat), for parallax correction | Candidate fallback height when INSAT CTH is missing (alternative or complement to the ERA5 fallback) | Open access; final DOI *unverified* | ⏳ To Read |
| **Wiltink, Deneke, van Heerwaarden & Meirink (2025)**, *AMT* 18, 3917–3936. [doi:10.5194/amt-18-3917-2025](https://doi.org/10.5194/amt-18-3917-2025) | Compares cloud-top-height parallax and shadow corrections for SEVIRI irradiance | Applying full CTH can over-correct; about 40–50% of CTH works best. Relevant to the sensitivity analysis | [Open access](https://amt.copernicus.org/articles/18/3917/2025/) | ⏳ To Read |

## Satellite–radar validation and impact on products

| Paper | Method | Relevance | Access | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Roebeling & Holleman (2009)**, *JGR* 114. [doi:10.1029/2009JD012102](https://doi.org/10.1029/2009JD012102) | SEVIRI rainfall checked against weather radar | Names parallax as a main source of satellite–radar mismatch | [KNMI](https://www.knmi.nl/research/publications/seviri-rainfall-retrieval-and-validation-using-weather-radar-observations) | ⏳ To Read |
| **Wang, Luo & Huang (2011)**, *JGR* 116, D17201. [doi:10.1029/2011JD016097](https://doi.org/10.1029/2011JD016097) | Parallax correction for CloudSat–MODIS collocation | Convective-top statistics change most for tops above 10–12 km. Relevant to deep monsoon convection | Open access *unverified* | ⏳ To Read |
| **Monsalve, Moreno, Goldenstern & Kummerow (2025)**, accepted in *J. Hydrometeorol.* [arXiv:2509.18695](https://arxiv.org/abs/2509.18695) | Parallax correction for GPM GMI/GPROF, using MRMS and ERA5 | Correction improves precipitation retrieval skill, mainly in summer and when the freezing level is high | arXiv | ⏳ To Read |
| **Harjupa, Nakakita, Sumida & Yamaguchi (~2017)**, *DPRI Annuals* 60 | Empirical Himawari-8 parallax fit against XRAIN radar | Radar-based empirical correction to compare against | [PDF](https://www.dpri.kyoto-u.ac.jp/nenpo/no60/ronbunB/a60b0p28.pdf) | ⏳ To Read |

## Deep learning with geostationary inputs and radar labels

| Paper | Method | Relevance | Access | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Lebedev et al. (2019)**, *KDD '19*, 2680–2688. [doi:10.1145/3292500.3330762](https://doi.org/10.1145/3292500.3330762) | Satellite-to-radar precipitation nowcasting | Reports up to about 3 px parallax shift; their correction attempt gave no gain. Key to cite and contrast with | [arXiv:1905.09932](https://arxiv.org/abs/1905.09932) | ⏳ To Read |
| **Lee, Kummerow & Ebert-Uphoff (2021)**, *AMT* 14, 2699–2716. [doi:10.5194/amt-14-2699-2021](https://doi.org/10.5194/amt-14-2699-2021) | CNN detects convection from GOES-16, with MRMS labels | Uses a fixed 10 km parallax shift but does not test it | [Open access](https://amt.copernicus.org/articles/14/2699/2021/) | ⏳ To Read |
| **Hilburn, Ebert-Uphoff & Miller (GREMLIN)**, *JAMC*. [arXiv:2004.07906](https://arxiv.org/abs/2004.07906) | CNN estimates radar reflectivity from GOES | Fixed 10 km parallax shift; journal DOI *unverified* | arXiv | ⏳ To Read |
| **Lagerquist et al. (2021)**, *Mon. Wea. Rev.* 149(12), 3897–3921 | U-Net convection nowcasting from Himawari-8 with Taiwan radar labels | Closest architecture to our U-Net experiment; how it handles parallax is unknown | *unverified* | ⏳ To Read |

## Indian region (none of these correct for parallax)

| Paper | Relevance | Status |
| :--- | :--- | :--- |
| **Mishra, Tomar, Kumar & Bhan (2023)**, *Weather*. [doi:10.1002/wea.4443](https://doi.org/10.1002/wea.4443) | Reconstructs radar reflectivity from INSAT-3D and GPM-DPR; no parallax step in the abstract | ⏳ To Read |
| **Kamath & Srinivasan (2020)**, *Solar Energy* 202, 45–54 | INSAT-3D irradiance; tagged with "satellite viewing parallax". **Check the full text: it is the closest possible prior work** | ⏳ To Read |

---

## Novelty check: findings

- **No published parallax correction found for INSAT-3D, INSAT-3DR, INSAT-3DS or Kalpana-1.**
  - Before claiming "first", still check SAC/ISRO grey literature, *Mausam*, *Current Science*, *JISRS*, and the full text of Kamath (2020).
- **satpy's `satpy.modifiers.parallax`:**
  - Uses a spherical Earth and a highest-cloud-wins `BucketResampler`.
  - Has **no terrain handling** and cites no papers.
  - Its INSAT-3D reader (`insat3d_img_l1b_h5`) is in beta, with "navigation still off".
  - Useful as a baseline to compare against.
- **No study found that compares an ML model trained on uncorrected vs parallax-corrected inputs.** This makes the U-Net experiment new.
- **INSAT-3DS** is at 82°E and operational. The tool could support it later.

## Check on MOSDAC

- Does `3RIMG_L2B_CTP` ("Cloud top properties") provide **height**, or only pressure/temperature?
- Is the archive complete for JJAS 2022–2024? Archive orders need a MOSDAC login.
