# Prior art: open-source parallax tools and INSAT-3D/3DR navigation accuracy

Compiled 2026-10-30. Sources were opened and checked unless marked otherwise. Quotes are short and verbatim.

## Verdict

**(A) "Open-source parallax tool" claim: this holds if worded narrowly. Two claims need rewording.**
- I found no open-source tool that does all of these together: ellipsoid ray tracing to the cloud top, plus terrain (DEM), plus occlusion-aware regridding, plus INSAT-specific I/O.
- Several ellipsoidal open-source parallax codes now exist, so "first ellipsoidal open-source parallax tool" is **not** a safe claim:
  - **pyparallax** (tsukada-cs, GPL-3.0, WGS84, Python with Fortran extension, last pushed 2026-09-16).
  - **JParallaxCorrect / JParallaxCorrect.jl** (tomonori-93, i.e. Tsujino; LGPL-2.1; rotational ellipsoid; "without any mathematical approximation"; Zenodo 10.5281/zenodo.18870145; last pushed 2026-09-25).
- **Satpy has an INSAT-3D/3DR L1B reader** (`insat3d_img_l1b_h5`, status "Beta, navigation still off"). In principle, satpy's spherical parallax modifier can already be chained to INSAT data. The manuscript should not say "no open-source tool can handle INSAT". A safer wording is "no tool is designed or validated for INSAT-3DR L1C, with ellipsoid geometry, terrain and occlusion handling".
- Terrain-aware geostationary orthorectification exists as open source: **goes-ortho** (GPL-3.0, GOES ABI, line-of-sight intersection with a DEM). It handles **surface** terrain parallax, not cloud tops. Two other works also do terrain-parallax correction for geostationary imagers: FY4B/AGRI (Deng & Ma 2025, ray-tracing orthorectification) and MTG FRP (Lira et al. 2026). Cite them as precedent for the terrain component.

**(B) "Seasonal navigation error" claim: novel in its specific form. There is a close ISRO precedent that must be cited.**
- **Jindal et al. (2014, ISPRS Archives XL-8, SAC/ISRO), the i3dQAS paper:**
  - Measured INSAT-3D Imager geolocation error with **land-sea boundary GCPs** against an AWiFS reference.
  - Showed the **diurnal variation** of geolocation error.
  - Explicitly compared dates "**pre and post yaw-flip**" (1 Mar and 14 Jul 2014).
  - Reported day versus night RMS statistics and attitude residuals.
  - This is the closest prior work. It establishes that ISRO knew geolocation error varies diurnally and with yaw-flip state. It does **not** report a multi-year seasonal westward bias, and it covers INSAT-3D, not 3DR.
- MOSDAC DQE reports (per image, GCP-based) are already known.
- I found **no** published paper reporting a seasonal (yaw-flip-linked) westward bias of 7–20 km in INSAT-3DR L1C. Recommendation: present the result as a "multi-year characterisation of a yaw-flip-linked seasonal bias in INSAT-3DR L1C", and cite Jindal et al. 2014 as the first indication of yaw-flip dependence.
- Precedent for methods (coastline or landmark matching, multi-month error analysis): JMA Himawari coastline matching, GOES-R IPATS, EUMETSAT FCI coastline edge-matching, Takenaka et al. 2020 (phase-only correlation, Himawari), and Deng & Ma 2025 (FY4B, a full year, E–W offsets of 5–15 pixels from diurnal thermal deformation and manoeuvres). The FY4B paper is the closest non-INSAT analogue of the seasonal/temporal navigation analysis.

---

## A. Parallax-correction codes and published methods

| Tool / work | Licence / availability | Earth model | Terrain | Occlusion | Satellites | Notes |
|---|---|---|---|---|---|---|
| **Satpy `satpy.modifiers.parallax`** (pytroll) | GPL-3.0, PyPI | **Sphere** | No | Bucket resampler keeps max \|shift\|; invisible pixels → NaN | Any GEO AreaDefinition (SEVIRI/NWCSAF example) | Experimental since v0.37 |
| **pyparallax** (tsukada-cs) | GPL-3.0, GitHub + Zenodo | **WGS84 ellipsoid** (geodetic↔geocentric) | Not mentioned | Not mentioned | Generic GEO; also LEO with per-pixel sat position | Created 2025-10, v0.2 geodetic fix 2026-09 |
| **JParallaxCorrect(.jl)** (tomonori-93 / Tsujino) | LGPL-2.1, Zenodo 10.5281/zenodo.18870145 | **Rotational ellipsoid**, "without any mathematical approximation" | Not mentioned | Not mentioned | Himawari-8 (inferred from Tsujino et al. 2021 JGR) | Formulation in Tsujino et al. 2026 SOLA SI |
| **DLFinney/GOES_cloud_parallax_shift** | MIT | Not stated | No | Not mentioned | GOES-16 (DCMEX campaign) | Per-pixel CTH-based |
| **jlc248/satellite-resources `plax`** | Not stated | Sphere (haversine, R = 6371009 m) | No (constant 9 km cloud) | No | GOES-16 ABI | Tutorial code |
| **goes-ortho** (spestana) | GPL-3.0, Zenodo | Ellipsoid heights (unnamed ellipsoid) | **DEM LOS intersection (SRTM 30 m)** | Mentions obscured terrain; method not described | GOES-16/17 ABI | **Surface** terrain parallax only, not clouds |
| **wradlib `georef.satellite.correct_parallax`** | MIT | n/a | n/a | n/a | TRMM/GPM spaceborne radar | Not a GEO-imager tool |
| **NWC SAF NWC/GEO**: PC-Ph parallax option; "PLAX" tool | Free to registered users, not open-source | Not verified | Uses NWP/climatological profile | Not verified | MSG, MTG, others | PLAX existence comes from search snippets of the SW User Manual (v1.3.2) and the v2021.2 release note ("additional options in PLAX tool for parallax correction of visible channels"). **I could not open the PDF (connection refused), so this is unverified.** |
| **McIDAS-X `PLAX` command** (SSEC) | McIDAS licence | Not stated | No | No | GOES etc. | Calculates parallax at cursor position. CIMSS web app uses a fixed cloud height |
| Bieliński 2020, *Remote Sensing* 12(3):365 | Paper (no code found) | Ellipsoid; Vicente/Koenig + Newton method on geodetic coordinates | No | No | MSG SEVIRI + radar | Method basis of PyGeoParallax-IN |
| FY-4A LMI CTH parallax (ResearchGate 374562918) | Paper | Ellipsoidal CTH model referenced | No | n/a | FY-4A LMI | Not opened in full |
| Deng & Ma 2025, *Sci. Remote Sens.* 10.1016/j.srs.2025.100348 | Paper | Ray-tracing orthorectification | **Yes (terrain)** | Not stated | FY4B AGRI | Terrain parallax plus POC navigation correction |
| Lira et al. 2026, ISPRS Arch. XLVIII-M-13-2026, 49–55 | Paper/product | Not stated | **Yes (terrain-corrected FRP coords)** | Not stated | MTG FCI | Fire pixels, not clouds |
| Wiltink et al. 2025, AMT 18:3917 | Uses Satpy 0.49 | Sphere (via Satpy) | No | Notes "blank pixels" problem | SEVIRI | Parallax plus shadow correction for GHI |
| Kotarba 2026, AMT 19:6193 | Uses Satpy 0.55 | Sphere (via Satpy) | No | — | Meteosat generations | Shows Satpy is the community default |
| Bernal Ayala et al. 2023, *J. Oper. Meteor.* 11(2) 10.15191/nwajom.2023.1102 | Paper | — | — | — | GOES-16/17 | Descriptive/forecaster-oriented |

Key quotes:
- Satpy source (main branch, checked 2026-10-30): "This function assumes a spherical Earth." The code uses `Geod(ellps="sphere")`. Its terrain comment: "could be a problem for high resolution imagery in mountainous or high elevation terrain". Its occlusion behaviour: "Pixels that are invisible after parallax correction are not retained but get geolocation NaN." https://github.com/pytroll/satpy/blob/main/satpy/modifiers/parallax.py ; https://satpy.readthedocs.io/en/latest/_modules/satpy/modifiers/parallax.html
- Satpy INSAT reader: `insat3d_img_l1b_h5.yaml`, "status: Beta, navigation still off". The file pattern `{platform:2s}` matches both 3D and 3R. https://github.com/pytroll/satpy/blob/main/satpy/etc/readers/insat3d_img_l1b_h5.yaml
- pyparallax README: "The internal formulae work in geocentric latitude and the conversion is done for you". The `ellps="WGS84"` example. https://github.com/tsukada-cs/pyparallax
- JParallaxCorrect README: "Calculation of the parallax based on formulations without any mathematical approximation." https://github.com/tomonori-93/JParallaxCorrect ; https://github.com/tomonori-93/JParallaxCorrect.jl
- goes-ortho README: the method computes "the intersection of line of sight (LOS) vectors with a DEM surface". https://github.com/spestana/goes-ortho
- GOES_cloud_parallax_shift: https://github.com/DLFinney/GOES_cloud_parallax_shift
- satellite-resources: https://satellite-resources.readthedocs.io/en/latest/Parallax.html
- wradlib: https://docs.wradlib.org/en/latest/_modules/wradlib/georef/satellite.html
- NWC SAF PC-Ph: https://www.nwcsaf.org/pc-ph_description ; SW UM: https://www.nwcsaf.org/Downloads/GEO/2025.2/Documents/Scientific_Docs/NWC-CDOP3-MTG-AEMET-SW-UM_v1.3.2.pdf (not opened)
- CIMSS parallax web app (made with McIDAS-X, fixed cloud height): https://cimss.ssec.wisc.edu/goes/webapps/parallax/notes_parallax.html ; McIDAS PLAX: https://www.ssec.wisc.edu/mcidas/doc/users_guide/2022.1/plax.html
- Bieliński 2020: https://doi.org/10.3390/rs12030365
- Deng & Ma 2025 abstract (OpenAlex): "east-west offsets (COFF) frequently fluctuated between ±5 and ±10 pixels (reaching ±15 pixels) due to diurnal thermal deformation and operational maneuvers". It also says orthorectification "eliminated terrain-induced parallax distortions exceeding 3 pixels in high-altitude regions". https://doi.org/10.1016/j.srs.2025.100348
- Lira et al. 2026: https://isprs-archives.copernicus.org/articles/XLVIII-M-13-2026/49/2026/
- Wiltink et al. 2025: https://amt.copernicus.org/articles/18/3917/2025/
- Kotarba 2026: https://amt.copernicus.org/articles/19/6193/2026/

INSAT-specific GitHub search: none of the 32 "insat-3dr" repos does parallax or navigation. Examples include santacodes/COG, pyINSAT, Pseudo-Cloud-Height and sacsazid/INSAT-3D-Utility-Software. The only INSAT parallax repo found is PyGeoParallax-IN itself (Zenodo 10.5281/zenodo.23666957).

## B. INSAT-3D/3DR/3DS navigation (INR) accuracy

1. **Jindal, Prakash, Sanghvi, Kartikeyan, Gopala Krishna (2014). "INSAT-3D Quality Analysis System (i3dQAS)."** ISPRS Archives XL-8, 257–263. doi:10.5194/isprsarchives-XL-8-257-2014. PDF opened.
   - Method: "prominent features (eg. Land-sea boundary) are identified as ground control points (GCPs)". The reference was "downsampled IRS-AWIFS data". The paper estimates geo-location error, internal distortion, scale and residual attitude.
   - Yaw flip: lists the "bi-annual yaw-flip" as a design feature, and mentions "pre/post yaw flip testing" campaigns.
   - Fig. 12 shows the "diurnal variation of geo-location error ... for 1st March and 14th July 2014. These dates are selected to compare system behavior pre and post yaw-flip".
   - Apr–Jun 2014 accuracy: day ">97% of products have accuracy better than 5 IR pixels"; night "about 90% ... less than 5 IR pixels".
   - Attitude residuals: roll ±0.1°, pitch ±0.25°, yaw ±0.2°, "except for 3:00, 9:30 and 15:30 hours where high residuals (upto 0.6 deg)".
   - **This is the most important precedent for (B).** It covers INSAT-3D (not 3DR), a few months in 2014, and compares two dates around a yaw flip. It does not report a multi-year seasonal sign pattern.
2. **MOSDAC DQE reports** (per-image location accuracy, GCP-based). Example: 3RIMG_13JAN2018_1545 used 10 GCPs, with mean radial error 6.958, CE90 7.716, RMS along/across ≈ 2.7/6.5. The units are given as IR pixels, but the PDF text extraction is jumbled, so the layout needs checking. Attitude residuals in that report: pitch 0.041°, roll 0.014°, yaw −0.001°. https://mosdac.gov.in/filebrowser/download/2042/13826?fid=13826 . Many similar reports exist at mosdac.gov.in/filebrowser/download/2042/… . These are snapshots and contain no seasonal analysis.
3. **eoPortal INSAT-3D/3DS.** Navigation stability requirement: "2 visible pixels (56 µrad) and 4 visible pixels (112 µrad)". Also describes the bi-annual yaw rotation to keep the cooler out of the Sun, and ground-computed attitude-correction uploads. https://www.eoportal.org/satellite-missions/insat-3d
4. **MOSDAC INSAT-3DR spacecraft page.** Lists "biannual yaw rotation" for IR detector thermal management. https://mosdac.gov.in/insat-3dr-spacecraft?language=en
5. **Subbiah, Dhar, Ramamoorthy (2018), JISRS.** "Automatic Registration of INSAT-3D Daily Images Using Mutual Information…", doi:10.1007/s12524-018-0820-0. Image-to-image registration without GCPs. Accuracy numbers not seen.
6. **Manthira Moorthi & Sivakumar (2018), ICTACT J. Image Video Process.** doi:10.21917/ijivp.2018.0243. Land-water boundary plus phase correlation coregistration of INSAT-3D for sub-pixel accuracy. Mentions "navigation data uncertainties".
7. **Bhatt & Padmanabhan (2018), arXiv:1805.08706.** Automatic GCP-based registration at SAC for Kalpana-1/INSAT-3A. Abstract only; no seasonal analysis seen.
8. **Radiometric Quality Evaluation of INSAT-3D Imager Data** (ISPRS Arch. XL-8-299-2014). Compares pre/post yaw-flip data (1 Mar vs 14 Jul 2014), but radiometrically. Not opened in full.
9. Not found: any Current Science, JISRS, IEEE, SPIE or ISPRS paper reporting INSAT-3DR navigation accuracy over a full year or several years, a seasonal or yaw-flip-linked E–W bias, or INSAT-3DS INR performance.

## C. Precedent: landmark/coastline navigation assessment at other agencies

- **JMA Himawari.** Accuracy is evaluated "by comparing coastlines recognized in Himawari images with those on referential maps". Accuracy is ~0.3 km. Daily monitoring: https://ds.data.jma.go.jp/mscweb/data/monitoring/navigation.html ; health check: https://www.data.jma.go.jp/mscweb/en/oper/healthcheck/AHI9_INR_cal_val_basedon_HealthCheck201810_rev0804.pdf ; MTSAT guide: https://ds.data.jma.go.jp/mscweb/data/monitoring/outline2.html
- **GOES-R IPATS.** Tan et al. 2020, *J. Appl. Remote Sens.* 14(3):032405, doi:10.1117/1.JRS.14.032405. Five INR metrics, using Landsat-derived chips reprojected to the GOES view.
- **EUMETSAT MTG FCI.** Coastline database plus Sobel edges matched to landmark coastlines (search snippet from a preprints.org manuscript 202505.2304; not opened). MTG INR page: https://www.eumetsat.int/MTG-INR-observations
- **Takenaka et al. 2020, *Remote Sensing* 12(15):2472.** Phase-only-correlation geolocation correction for Himawari, "basic data underlying physical analysis, parallax correction". doi:10.3390/rs12152472
- **Deng & Ma 2025.** FY4B: a full year of geolocation error, with diurnal thermal and manoeuvre-driven E–W offsets of 5–15 pixels, corrected by POC. (see A)
- **Hou et al. 2020, ISPRS Arch. XLII-3-W10, 569.** Multi-level-grid coastline landmark matching under cloud. doi:10.5194/isprs-archives-xlii-3-w10-569-2020
- FY-4A thermal deformation driving diurnal navigation bias: GI 8:161 (2019), https://gi.copernicus.org/articles/8/161/2019/ . A reviewer reply in the preprint mentions "nearly 10 kilometers navigation bias", but that is not verified in the final paper.
- Coastline inflection method for microwave imagers (FY-3D MWRI): doi:10.3390/rs15030813 (LEO, not GEO).

## Queries tried (including negative results)

- WebSearch: open-source GEO parallax github; satpy parallax docs; NWCSAF parallax (×2); pyresample/pyorbital/wradlib parallax; github INSAT/Himawari parallax with DEM; Bieliński 2020; pyparallax Tsukada; R/MATLAB/Earth Engine parallax. The R/MATLAB/Earth Engine search was **negative**: no packages found.
- WebSearch: INSAT-3DR INR accuracy; INSAT-3D yaw flip seasonal geolocation (**negative** for a seasonal-bias paper); INSAT-3D INR star sensor landmark (**negative** for a dedicated INR paper); MOSDAC DQE; INSAT-3DR yaw flip announcement (**negative**: no flip dates found); INSAT geolocation coastline correction (**negative** apart from PyGeoParallax-IN); INSAT-3D Current Science navigation spec (**negative**); INSAT parallax lightning (**negative**).
- WebSearch: GOES-R INR IPATS; FY-4A navigation seasonal; Himawari JMA coastline; EUMETSAT FCI landmark.
- OpenAlex: "INSAT-3D navigation", "INSAT-3DR geolocation", "INSAT-3D image navigation registration", "INSAT-3D geometric accuracy", "INSAT yaw flip", "INSAT-3DS navigation", "INSAT-3D landmark", "Kalpana image navigation", "geostationary parallax correction software", "parallax correction terrain geostationary".
- Semantic Scholar: "INSAT-3DS image navigation" and "INSAT-3D image registration geolocation". Other queries were rate-limited (HTTP 429).
- GitHub API: "parallax correction" (only JParallaxCorrect plus unrelated results); "insat-3dr" (32 repos, none relevant); "parallax insat" / "parallax himawari" / "parallax seviri" (0 results). Some later queries were rate-limited.

## Uncertainties

- NWC SAF PLAX tool details (Earth model, terrain handling) are unverified because the PDF was unreachable.
- I did not check pyparallax and JParallaxCorrect code for terrain or occlusion handling beyond their READMEs.
- MOSDAC DQE table values come from garbled PDF text extraction.
- Possible ISRO internal or IMD reports on INSAT-3DR seasonal navigation may exist without being indexed.
