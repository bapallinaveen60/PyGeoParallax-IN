# Novelty of the INSAT-3DR parallax manuscript: literature check

Manuscript: *Parallax correction of INSAT-3DR imagery over India: an open-source tool and the limits of validation against GPM radar*

Based on: four research notes dated 30 Oct 2026 (`research_notes/INSAT parallax correction novelty/`: `indian_imagers.md`, `radar_validation.md`, `ml_inputs.md`, `tools_navigation.md`). They extend the web-only check of 26 Oct 2026 (`00_Documentation/novelty_check.md`). The searches used OpenAlex, Google Scholar (about 9 result pages before a bot check), Europe PMC, CrossRef, the MOSDAC document library, GitHub, publisher sites and about 100 web searches. **Scopus and Web of Science were not available.** See Section 10.

Marking used below:
- **[verified]**: the full text or the stated page was read.
- **[snippet]**: only a search snippet or an abstract was seen.
- **[verify before citing]**: the DOI, the bibliographic data or the content is uncertain, was flagged as from memory, or the notes contradict each other.

---

## 1. Executive summary

Two claims hold with careful wording: no one has validated an INSAT parallax correction against radar (claim 2), and the results support a measure-dependent framing (claim 5). Three claims hold only in a narrower form: claim 1 (absence of INSAT parallax work), claim 3 (the tool) and claim 4 (the navigation error). One claim must be dropped: claim 6, that no study compares ML trained on uncorrected and corrected input. **D'Adderio et al. (2023) ran the same A/B test and got the same result.** Claim 7 is not new as a finding, so present it as corroboration and cite the precedents.

| # | Claim | Verdict | Key evidence | Suggested wording (short) |
|---|---|---|---|---|
| 1 | No published parallax correction or validation for INSAT-3D/3DR | **Narrow** | ISRO/SAC *INSAT-3D ATBD* (May 2015), Hydro-Estimator chapter, item "(c) Orography and Parallax correction": a Vicente et al. (2002) shift is documented as an internal step of the operational rain product. IMD papers repeat it (Malhan et al. 2022). No quantification or validation was found anywhere. | "Apart from a parallax shift described as an internal step of the INSAT-3D Hydro-Estimator (ISRO/SAC, 2015), which to our knowledge has never been separately quantified or validated, we found no published parallax correction, quantification or validation for INSAT-3D/3DR imagery." |
| 2 | First validation of INSAT parallax correction against spaceborne radar | **Holds (with "to our knowledge")** | Nothing found for INSAT or Kalpana. Even for any GEO, there is no multi-case before/after test against spaceborne radar: Sun et al. (2024) apply a fixed 14 km correction but do not test it, and Kotarba (2026) says CloudSat/CALIPSO cannot anchor the parallax step. Mishra et al. (2023, 2025, 2026) collocate INSAT-3D with DPR, but their full texts were not checked. | "To our knowledge, the first evaluation of parallax correction of INSAT imagery against spaceborne radar, and among the first multi-case before/after tests of geostationary parallax correction against spaceborne radar for any satellite." |
| 3 | Open-source tool (ellipsoid ray tracing, terrain, occlusion-aware regridding, native-grid correction, effective height, coastline navigation correction) | **Narrow** | Satpy's parallax modifier is open source but spherical, with no terrain handling. Satpy also has an INSAT-3D/3DR L1B reader. Two ellipsoidal open-source codes exist (pyparallax, JParallaxCorrect). goes-ortho handles DEM line-of-sight for surface terrain. No tool combines all the listed components or targets INSAT-3DR L1C. | "An open-source tool designed for INSAT-3DR L1C that combines ellipsoid ray tracing with terrain, occlusion-aware regridding, native-grid output, an effective-height option and coastline-based navigation correction." Do not say "first ellipsoidal" or "no tool can process INSAT". |
| 4 | INSAT-3DR L1C navigation error is seasonal (7–20 km west, late Sep to mid Mar, linked to the yaw flip) | **Narrow; cite the precedent** | Jindal et al. (2014) measured INSAT-3D geolocation error with land–sea GCPs, showed diurnal variation and compared dates before and after a yaw flip. The MOSDAC DQE reports give per-image errors. No multi-year seasonal bias for 3DR has been published. | "A multi-year characterisation of a seasonal, yaw-flip-linked westward bias in INSAT-3DR L1C geolocation, extending the pre/post-yaw-flip comparison of Jindal et al. (2014) for INSAT-3D." |
| 5 | Measured benefit depends on the comparison measure (field vs cell scale disagree by 2–5 km; ~5 % of the parallax is visible at cells) | **Holds as a framing; discuss the tension** | The ingredients are known: Wiltink et al. 2025, Monsalve et al. 2026, Bluestein et al. 2019 and Liu et al. 2007. No paper quantifies a disagreement between a field-scale and a cell-scale measure for the same storms. Several cell-scale case studies, however, see a large offset that correction removes. | "We show, for the same storms and correction, that a storm-scale field measure and a cell-scale cold-core measure give estimates of the benefit that differ by 2–5 km." Cite the ingredients and discuss the conflicting case studies. |
| 6 | "No study compares an ML model trained on uncorrected versus corrected geostationary inputs" | **Drop** | D'Adderio et al. (2023): a SEVIRI U-Net trained against GPM 2B-CMB was retrained on parallax-shifted input, and "the not-parallax-corrected U-Net outperformed the parallax-corrected U-Net". Oya (2025) found that adding parallax-related inputs gave no gain. | "To our knowledge, only one previous study has made this comparison (D'Adderio et al., 2023), and it also found the uncorrected model better. Ours is the first such controlled comparison for INSAT-3DR and for precipitation type, with per-class metrics." |
| 7 | IR cold-core tops ~3.2 km above GPM Ku storm tops; an effective lower height may suit precipitation | **Holds as corroboration, not as a new finding** | Song et al. (2020): CTH − storm height is 2.7–5.5 km by region (TRMM). Lower effective heights: Monsalve et al. 2026 (freezing level), Wiltink et al. 2025 (40–50 % of Hc), Virts & Koshak 2020 (GLM), and the fixed 10 km and 14 km conventions. No study tunes the height for GEO IR against DPR. | "The 3.2 km offset lies within the 2.7–5.5 km range reported from TRMM (Song et al., 2020). Consistent with Monsalve et al. (2026) and Wiltink et al. (2025), an effective height below the IR cloud top may suit precipitation. We are not aware of an earlier tuning against DPR." |

---

## 2. Claim 1: no parallax correction or validation published for INSAT-3D/3DR

**Verdict: false as worded. Narrow it.**

### Evidence that a correction is documented

**ISRO/SAC (2015), *INSAT-3D ATBD Document*, May 2015** [verified]
- URL: https://mosdac.gov.in/docs/INSAT_3D_ATBD_MAY_2015.pdf (379 pp.). It is linked from https://www.mosdac.gov.in/insat-3d-references.
- Location: Chapter 4(B), "Rainfall Estimation – H-E Method", product `3DIMG_L2B_HEM`, Section 4.4, item "(c) Orography and Parallax correction", pp. 75–76.
- Verbatim: "The parallax correction described in the same paper, adjusts the horizontal location of the satellite pixel prior to rain rate computation, based on cloud height (using Tb and standard atmosphere) and satellite zenith angle." The "same paper" is Vicente et al. (2002).
- What the document does not contain: no shift magnitudes, and no validation of the shift itself. Section 4.6 validates rain totals only. The GPI/IMSRA chapter (4A) has no parallax step.

**Malhan et al. (2022), *Mausam* 73(4): 833–842** [verified]
- Title: "Comparative analysis of sub-division wise rainfall INSAT-3D vs. Ground based observations." DOI: https://doi.org/10.54302/mausam.v73i4.5877
- Verbatim: "…warm top modification along with orography with parallax corrections with the help of temperature dependent parameter suitable for Indian domain."

**Secondary descriptions with the same boilerplate**
- Singh et al. (2019), *J. Hydrol.* 575: 1371–1379, doi:10.1016/j.jhydrol.2019.02.016 [snippet; verify before citing].
- Kumar et al. (2019), IGI Global chapter, doi:10.4018/978-1-5225-7784-3.ch006 [snippet].
- Singh et al. (2018), *JISRS* 46: 927, doi:10.1007/s12524-018-0751-9 [snippet, context unverified].

### Inconsistency inside ISRO's own documents

**Varma & Gairola (March 2015), *ATBD Hydro-Estimator (Modified)*, SAC/EPSA/AOSG/SR/04/2015** [verified]
- URL: https://mosdac.gov.in/docs/HEM_rain-revised-atbd.pdf
- It describes only the warm-top and orographic corrections. "Parallax" appears only in the title of the cited Vicente et al. reference.
- So whether today's operational HEM applies the shift cannot be confirmed from public documents.
- Note on the notes themselves: `radar_validation.md` (D1) attributes the parallax sentence to this document too. `indian_imagers.md` read both documents and places the sentence only in the May 2015 ATBD. **Follow `indian_imagers.md`.**

### Negative evidence

These studies collocated INSAT or Kalpana data with other observations and do not mention parallax:
- IMSRA calibration against TRMM PR and GPM: Gairola et al. (2020), *Atmósfera* 33: 33–49, doi:10.20937/atm.52630 [verified].
- Lima et al. (2019), *Remote Sens.* 11: 2811, doi:10.3390/rs11232811, INSAT-3D CTT vs CALIOP [verified].
- MOSDAC ATBDs for other INSAT-3D/3DR products [verified].
- INSAT-3D/3DR AMV documents.

Other Indian work mentions parallax only qualitatively: Goyal et al. (2017), *Mausam* 68(4): 689–698, https://doi.org/10.54302/mausam.v68i4.768 [verified], on ADT and TC centre fixing. In OpenAlex, the only record pairing "parallax" with "INSAT-3DR" in its title or abstract is PyGeoParallax-IN itself (doi:10.5281/zenodo.23666957).

### Suggested wording (Introduction and Conclusions)

> "Apart from a geometric parallax shift described as an internal step of the operational INSAT-3D Hydro-Estimator rain algorithm (ISRO/SAC, 2015; after Vicente et al., 2002), which to our knowledge has never been separately documented, quantified or validated, we found no published parallax correction, parallax quantification, or validation of parallax-corrected INSAT-3D/3DR imagery against independent observations."

Optionally extend this to INSAT-3DS and Kalpana-1. Nothing was found for either.

---

## 3. Claim 2: first validation against spaceborne radar

**Verdict: holds. Keep "to our knowledge" and phrase it as validation, not as "first correction".**

### What was not found

No paper, report or ATBD compares parallax-corrected and uncorrected INSAT or Kalpana imagery against GPM DPR, TRMM PR, CloudSat or Indian DWRs.

### Closest work for any geostationary satellite

**Sun, Zhuge & Zhu (2024)**, "Geostationary Satellite-Based Overshooting Top Detections and Their Relationship to Severe Weather over Eastern China", *Remote Sens.* 16, 2015, doi:10.3390/rs16112015 [verified]
- Himawari-8 and FY-4A overshooting tops compared with GPM KuPR-derived overshooting tops.
- Parallax correction with a fixed 14 km height and a 10 km match radius.
- **They do not test whether the correction helps.**

**Kotarba (2026)**, "Evaluation of a moist-adiabat cloud-top height retrieval for parallax correction of deep convective clouds across Meteosat generations", *AMT* 19, 6193–6208, doi:10.5194/amt-19-6193-2026 [verified]
- The CloudSat/CALIPSO comparison "cannot … anchor the parallax-correction step itself".
- Independent surface verification "remains a valuable, though non-trivial, direction for future work".

**Bieliński (2020)**, "A Parallax Shift Effect Correction Based on Cloud Height for Geostationary Satellites and Radar Observations", *Remote Sens.* 12, 365, doi:10.3390/rs12030365 [verified]
- Compared with ground radar for one SEVIRI scene: r = 0.556 uncorrected, 0.683 corrected.
- This is also the method basis of the tool.

Other ground-radar demonstrations, each one or a few cases:
- Radová & Seidl (2008), EUMETSAT conference [verified].
- Harjupa et al. (2017), *DPRI Annuals* 60B [verified].
- BMKG AOMSUC-12 abstract (Pandjaitan et al.) [verified abstract].

### Must cite: earlier INSAT–DPR collocation work

Parallax handling in these papers has **not been verified**; the full texts were paywalled.
- Mishra, A. K., Tomar, C. S., Kumar, G., Bhan, S. C. (2023), *Weather* 78, 224–227, doi:10.1002/wea.4443.
- Mishra et al. (2025), *Theor. Appl. Climatol.* 156: 428, doi:10.1007/s00704-025-05650-5.
- Mishra et al. (2026), Springer chapter, doi:10.1007/978-981-95-5409-6_11.

### Suggested wording

> "To our knowledge, this is the first evaluation of parallax correction of INSAT imagery against spaceborne radar. It is also one of very few multi-case before/after tests of geostationary parallax correction against any radar: earlier tests used one or a few cases and ground radar (Bieliński, 2020; Radová and Seidl, 2008), or applied a fixed-height correction to spaceborne-radar comparisons without testing it (Sun et al., 2024)."

A broader "first for any GEO against spaceborne radar" claim may be defensible, but it carries more risk. Use it only with "to our knowledge".

---

## 4. Claim 3: open-source tool

**Verdict: narrow it. Claim the combination and the INSAT-3DR L1C target, not any single component.**

### Existing open-source parallax codes [verified READMEs and source]

| Tool | Earth model | Terrain | Occlusion | Notes |
|---|---|---|---|---|
| Satpy `satpy.modifiers.parallax` (GPL-3.0) | Sphere. The source says: "This function assumes a spherical Earth." | No | Invisible pixels get NaN | Experimental since v0.37. Community default, used by Wiltink et al. 2025 and Kotarba 2026 |
| Satpy reader `insat3d_img_l1b_h5` | — | — | — | INSAT-3D/3DR **L1B**, status "Beta, navigation still off" |
| pyparallax (tsukada-cs, GPL-3.0) | WGS84 ellipsoid | Not mentioned | Not mentioned | Generic GEO |
| JParallaxCorrect(.jl) (Tsujino, LGPL-2.1, Zenodo 10.5281/zenodo.18870145) | Rotational ellipsoid, "without any mathematical approximation" | Not mentioned | Not mentioned | Himawari |
| goes-ortho (GPL-3.0) | Ellipsoid heights | DEM line-of-sight (SRTM 30 m) | Mentions obscured terrain | **Surface** terrain parallax, GOES ABI |
| GOES_cloud_parallax_shift (MIT); satellite-resources `plax` | Not stated / sphere | No | No | GOES-16 |
| NWC SAF NWC/GEO PLAX option | — | — | — | Free to registered users, not open source. **Unverified** (the PDF could not be opened) |

Terrain parallax precedents for geostationary imagers:
- Deng & Ma (2025), *Sci. Remote Sens.*, doi:10.1016/j.srs.2025.100348, FY-4B ray-tracing orthorectification [snippet; abstract via OpenAlex].
- Lira et al. (2026), ISPRS Arch. XLVIII-M-13-2026, 49–55, MTG FCI fire pixels [snippet].

None of the 32 GitHub repositories tagged "insat-3dr" performs parallax or navigation correction.

### Suggested wording

> "We release an open-source tool designed for INSAT-3DR L1C imagery. It combines ellipsoidal ray tracing to the cloud top with terrain handling, occlusion-aware regridding, native-grid output, an effective-height option and coastline-based navigation correction. Existing open-source parallax codes are either spherical and without terrain handling (Satpy) or ellipsoidal but generic and without terrain or occlusion handling (pyparallax; JParallaxCorrect). Terrain line-of-sight correction has so far been applied to surface features (goes-ortho; Deng and Ma, 2025), not to cloud tops."

Avoid "first ellipsoidal open-source parallax tool". Also avoid saying that no open-source tool can process INSAT data: Satpy has an INSAT L1B reader.

---

## 5. Claim 4: seasonal navigation error

**Verdict: new in its specific form. Narrow it and cite the ISRO precedent.**

### Main precedent

**Jindal, Prakash, Sanghvi, Kartikeyan, Gopala Krishna (2014)**, "INSAT-3D Quality Analysis System (i3dQAS)", ISPRS Archives XL-8, 257–263, doi:10.5194/isprsarchives-XL-8-257-2014 [verified]
- Ground control points: "prominent features (eg. Land-sea boundary) are identified as ground control points (GCPs)". The reference image was downsampled IRS-AWiFS.
- Fig. 12 shows the "diurnal variation of geo-location error … for 1st March and 14th July 2014. These dates are selected to compare system behavior pre and post yaw-flip".
- Accuracy, Apr–Jun 2014: by day, ">97% of products have accuracy better than 5 IR pixels"; by night, "about 90 %".
- Limits: covers INSAT-3D, not 3DR, over a few months only, and does not describe a multi-year seasonal sign pattern.

### Operational baseline

**MOSDAC DQE reports** give a per-image, GCP-based location accuracy.
- Examples: INSAT-3DR, 19 Jun 2020 (from the 26 Oct check), and 3RIMG_13JAN2018_1545.
- Values were extracted from garbled PDF text. **Check the units and table layout before quoting numbers.**

### The yaw flip itself

- The bi-annual yaw rotation is documented by eoPortal (INSAT-3D/3DS) and on the MOSDAC INSAT-3DR spacecraft page ("biannual yaw rotation").
- This updates the 26 Oct note, which found no such document for 3DR.
- **No flip dates were found.** Linking the late-September to mid-March regime to the flip therefore remains an inference.

### Comparable analyses for other satellites (methods precedent)

- **Deng & Ma (2025), FY-4B.** One year of geolocation error. E–W offsets "between ±5 and ±10 pixels (reaching ±15 pixels) due to diurnal thermal deformation and operational maneuvers". This is the closest non-INSAT analogue.
- **JMA Himawari** coastline matching.
- **GOES-R IPATS:** Tan et al. (2020), *J. Appl. Remote Sens.* 14(3): 032405, doi:10.1117/1.JRS.14.032405.
- **Takenaka et al. (2020)**, *Remote Sens.* 12(15): 2472, doi:10.3390/rs12152472.

### Suggested wording

> "We give a multi-year characterisation of INSAT-3DR L1C geolocation error from coastline matching. It reveals a seasonal westward bias of 7–20 km from late September to mid-March, which we attribute to the bi-annual yaw flip. This extends the pre/post-yaw-flip comparison of Jindal et al. (2014) for INSAT-3D and the per-image MOSDAC quality reports."

Keep "attribute" or "consistent with" unless ISRO confirms the flip dates.

---

## 6. Claim 5: the result depends on the comparison measure

**Verdict: the framing appears new. Its ingredients are not, and published case studies point the other way at the cell scale.**

### Prior work that supports parts of the claim

**Wiltink, Deneke, van Heerwaarden & Meirink (2025)**, "Evaluating parallax and shadow correction methods for global horizontal irradiance retrievals from Meteosat SEVIRI", *AMT* 18, 3917–3936, https://doi.org/10.5194/amt-18-3917-2025 [verified; citation confirmed in Crossref]
- An empirical, time-step-optimal shift beats geometric correction: −14.5 % RMSE versus −10.8 % for the combined correction (high resolution).
- Parallax-only correction can increase the error, depending on regime and resolution.

**Monsalve, Moreno, Goldenstern & Kummerow (2026)**, "Quantifying the Effect of a Parallax-Correcting Algorithm for Passive Microwave Satellite Precipitation Retrievals across the Conterminous United States", *JHM* 27, 153–165, doi:10.1175/JHM-D-24-0060.1 [verified via preprint arXiv:2509.18695]
- Correcting with the GOES-16 cloud-top height raised RMSE by 7.29 % (July 2020). Correcting with the freezing level lowered it by 3.95 %.
- Event-level changes range from −39 % to +53 %.

**Coldest IR is not always over the radar core:**
- **Bluestein et al. (2019)**, *MWR* 147, 4151–4176, doi:10.1175/MWR-D-19-0159.1 [verified]: the highest echo top was displaced about 10 km from the updraft and cloud top after parallax correction.
- **Setvák et al. (2010)**, *Atmos. Res.* 97, 80–96, doi:10.1016/j.atmosres.2010.03.009: cold-ring storms.
- **Heymsfield et al. (1983)**, *J. Atmos. Sci.* 40, 1740–1755: enhanced-V storms.
- **Cooney et al. (2021)**, *JGR* 126, e2020JD034319, doi:10.1029/2020JD034319: cold outflow can mimic overshooting tops [abstract only].
- **Wang, J. et al. (2026)**, HailDeformer, *Remote Sens.* 18, 1743, doi:10.3390/rs18111743 [verified]: "the real bottleneck is the spatial mismatch from parallax and storm tilt".

**Liu, Zipser & Nesbitt (2007)**, *J. Climate* 20, 489–503, doi:10.1175/JCLI4023.1
- Only 35 % (57 %) of the area with TB11 ≤ 235 K (210 K) has PR near-surface rain.
- Cold cloud is therefore not the same as the radar core at field scale, because of the non-raining anvil.

**Not found:** any paper that reports the disagreement between field-scale and cell-scale measures for the same storms and the same correction, or the fraction of the computed parallax that is visible at cells.

### Suggested wording

> "For the same storms and the same correction, a storm-scale field-correlation measure and a cell-scale cold-core-to-deep-echo measure disagree by 2–5 km about the residual offset, and only about 5 % of the computed parallax is visible as a cold-core offset. This is consistent with reports that the benefit of correction depends on regime, height choice and measure (Wiltink et al., 2025; Monsalve et al., 2026), and that storm structure can displace cold tops from radar cores by distances comparable to the parallax (Bluestein et al., 2019)."

The tension with case studies must be discussed. See Section 9.

---

## 7. Claim 6: no ML study compares uncorrected and corrected input

**Verdict: falsified. Drop it.**

### Direct precedent

**D'Adderio, L. P., Casella, D., Dietrich, S., Panegrossi, G., Sanò, P. (2023)**, "A First Step towards Meteosat Third Generation Day-2 Precipitation Rate Product: Deep Learning for Precipitation Rate Retrieval from Geostationary Infrared Measurements", *Remote Sensing* 15(24), 5662, https://doi.org/10.3390/rs15245662 [verified; open-access full text, Section 3.3]

Setup:
- Meteosat-10 SEVIRI IR and NWC SAF cloud-top height as inputs; GPM DPR-GMI 2B-CMB as the reference; a U-Net.
- The inputs were shifted by Δx ∝ CTH·tanθ.
- A second U-Net was trained "with the same architecture and hyperparameter".

Verbatim result:

> "The results showed how the not-parallax-corrected U-Net outperformed the parallax-corrected U-Net in terms of accuracy (RMSE, MAE) and detection of precipitation (POD, FAR, CSI)."

Limits compared with our study:
- No numbers are given for the A/B comparison.
- The shift is crude, and the authors note the "hole" problem.
- CTH is also a network input.
- Regression, not classification. Seeds and repeatability are not discussed.

### Related work

- **Brempong et al. (2025)**, "Oya: Deep Learning for Accurate Global Precipitation Estimation", arXiv:2511.10562 (preprint) [verified]. Adding CTH, viewing angles, coordinates and elevation as inputs: the models "did not perform better than the models trained only with GEO inputs".
- **Hilburn, Ebert-Uphoff & Miller (2021)**, GREMLIN, *JAMC* 60, 3–21, doi:10.1175/JAMC-D-20-0084.1. **Verify before citing:** the DOI was flagged as from memory in `ml_inputs.md`. Content verified from arXiv:2004.07906: the inputs were corrected with a fixed 10 km height, and "the CNN seems to learn to apply additional spatial displacements on its own".
- **Metzl et al. (2025)**, *AIES*, https://doi.org/10.1175/AIES-D-25-0035.1 (arXiv:2504.09994) [verified]. They skip correction because "parallax effects exert minimal influence on model performance", citing Cintineo et al. (2020).
- **Cintineo et al. (2020)**, *Wea. Forecasting* 35, 2567–2588, doi:10.1175/WAF-D-20-0028.1. **Verify before citing:** `radar_validation.md` lists its full text as read and reports that the model "learned the parallax relationship", while `ml_inputs.md` says the full text was blocked. Read it before attributing a parallax result to it.
- **Beusch et al. (2018)**, *Remote Sensing* 10(6), 939, doi:10.3390/rs10060939: corrected inputs, no ablation.
- **Wang et al. (2026)**, HailDeformer: learned alignment beats no alignment (F1 0.864 versus 0.836 without the alignment module).

### Indian ML work

No INSAT-3D/3DR deep-learning study applying or testing parallax correction was found. One possible competitor should be watched: an **IIT Hyderabad project (2024–26)** on INSAT-3D/3DR precipitation-type classification with XAI/ML [snippet only; no publication found].

### Suggested wording

> "To our knowledge, only one previous study has compared a deep-learning model trained on uncorrected versus parallax-corrected geostationary input (D'Adderio et al., 2023, a SEVIRI U-Net for rain rate), and it likewise found the uncorrected model performed better. Ours is the first such controlled comparison for INSAT-3DR and for precipitation type, using a ray-traced ellipsoidal correction, identical labels, splits and seed, and per-class metrics."

Also correct the progress report, which contains the falsified sentence.

---

## 8. Claim 7: IR tops ~3.2 km above Ku storm tops; effective height

**Verdict: corroborates earlier work and is not a new finding. The tuning against DPR appears new.**

### Height offset between IR tops and radar storm tops

**Song, Kim, Roh & Lee (2020)**, "Difference Between Cloud Top Height and Storm Height for Heavy Rainfall Using TRMM Measurements", *JMSJ* 98(5), 901–914, doi:10.2151/jmsj.2020-044 [verified]
- Mean CTH − storm height for heavy rain: NW Pacific 5.5 km, Central Africa 3.9 km, USA 2.7 km, Korea/Japan about 4.3 km.
- No parallax correction was applied: "parallax correction between two sensors is not considered here".
- The manuscript's 3.2 km lies inside this range.

Also relevant:
- **Liu, Zipser & Nesbitt (2007):** the gap between IR top and 20 dBZ echo top is a proxy for convective intensity.
- **Kotarba (2026):** moist-adiabat CTH is 2.7 km below the CloudSat/CALIPSO cloud top.

### Effective heights below the cloud top

- **Monsalve et al. (2026):** the freezing level beats the IR cloud top for passive-microwave rain.
- **Wiltink et al. (2025):** 40–50 % of Hc works best for parallax-only correction; 70–90 % for the combined correction (not significant).
- **Virts & Koshak (2020)**, "Mitigation of Geostationary Lightning Mapper Geolocation Errors", *JTECH* 37, 1725–1736, doi:10.1175/JTECH-D-19-0100.1 [verified]: the GLM ellipsoid was lowered from 16 km to 14 km, and the optimal heights vary by region and season.
- **Fixed-height conventions:** 10 km in GREMLIN (Hilburn et al., 2021) and 14 km in Sun et al. (2024), Bedka (2011, *Atmos. Res.* 99, 175–189) and Dworak et al. (2012, *WAF* 27, 684–699, doi:10.1175/WAF-D-11-00070.1).
- **The operational INSAT-3D HE** uses a Tb plus standard-atmosphere height (ISRO/SAC, 2015).

Not found: a study that tunes the parallax height for GEO IR rainfall or precipitation against DPR or PR.

### Suggested wording

> "IR cold-core tops lie about 3.2 km above GPM Ku storm tops, within the 2.7–5.5 km range reported from TRMM for heavy rain (Song et al., 2020). Consistent with lower effective heights found for passive-microwave precipitation (Monsalve et al., 2026), irradiance (Wiltink et al., 2025) and lightning (Virts and Koshak, 2020), an effective height below the IR cloud top may suit precipitation applications. We are not aware of an earlier tuning of this height for geostationary IR against spaceborne radar."

---

## 9. Results in the literature that support or challenge ours

| Our result | Supporting literature | Challenging literature | What the paper should say |
|---|---|---|---|
| U-Net A/B: no gain, convective CSI slightly lower with corrected input | D'Adderio et al. 2023 (same direction, SEVIRI); Oya 2025 (no gain from parallax inputs); Hilburn et al. 2021 and Metzl et al. 2025 (networks learn the shift) | HailDeformer 2026: explicit, learned alignment helps (F1 +0.028). Hilburn et al. still pre-corrected with 10 km | Networks absorb a consistent displacement. A geometric pre-correction adds holes and duplicate pixels (occlusion) and CTH errors, and our labels may share the displacement. Learned alignment is a different kind of intervention. |
| Small or mixed benefit of geometric correction at the field scale | Monsalve et al. 2026 (cloud-top correction degraded RMSE by 7.3 %; events ranged from −39 % to +53 %); Wiltink et al. 2025 (parallax-only can increase error); Zhang et al. 2026 *ESSD* 18, 5773–5791, doi:10.5194/essd-18-5773-2026 (CTH parallax alone leaves large residuals: 36.0 % of events within 15 km versus 51.7 % after the empirical spline) | Bieliński 2020 (r 0.556 → 0.683, one scene) | Single-scene gains are not comparable with multi-case statistics. Height choice drives the sign. |
| Only ~5 % of the computed parallax is visible at cells; cold cores already sit near deep echoes | Bluestein et al. 2019 (storm-structure offsets of ~10 km); Setvák et al. 2010; Cooney et al. 2021; Dworak et al. 2012 ("an OT often corresponds with the highest radar echo top"); Liu et al. 2007 | **BMKG / Pandjaitan et al. (AOMSUC-12):** overshooting top to event site ~13 km uncorrected, <3 km corrected, one Java case. **Harjupa et al. 2017:** the coldest-BT pixel is clearly NW of the XRAIN maximum, with distance = −0.77·BT + 25.5 (R² = 0.874) over 16 events. **Radová & Seidl 2008:** "large difference in the relative location". Bernal Ayala et al. 2023: visible shift against NEXRAD and GLM | **This tension must be discussed.** Candidate explanations from the notes: tropical monsoon storms (different from midlatitude supercells or Japanese local storms); 4 km INSAT pixels and the ~5 km DPR footprint; near-nadir geometry at 74°E over India (Harjupa and Radová work at much higher view angles, e.g. 16–28 km parallax at 48.5°N); case selection; navigation error partly cancelling parallax in the monsoon season (26 Oct check). Most of these case studies have no or few statistics. |
| IR top ~3.2 km above the Ku top | Song et al. 2020; Liu et al. 2007; Kotarba 2026 | — | Present as consistent with earlier results. |
| Empirical or effective shift beats nominal geometry | Wiltink et al. 2025; Harjupa et al. 2017; Virts & Koshak 2020; Zhang et al. 2026 | — | Place the effective-height option and the field-correlation offset measure in this tradition. |

---

## 10. Concrete manuscript edits

| Section | Current claim | New wording / action |
|---|---|---|
| Introduction (novelty paragraph), Sec. 6.6, Conclusions | "To our knowledge no parallax correction or validation has been published for INSAT-3D or INSAT-3DR." | Use the claim 1 wording (Section 2). Cite ISRO/SAC (2015) ATBD, Vicente et al. (2002) and Malhan et al. (2022). Mention in a footnote or sentence that the revised HEM ATBD (Varma & Gairola, 2015) does not describe the step. |
| Introduction, Sec. 6.6, Abstract | "First validation of INSAT parallax correction against spaceborne radar" | Keep, adding "to our knowledge". Add a sentence citing Mishra et al. (2023, 2025, 2026) as earlier INSAT–DPR collocation, and Sun et al. (2024), Kotarba (2026) and Bieliński (2020) for the GEO context. |
| Introduction / Methods (tool) | "An open-source tool …" (any implied "first" or "only") | Use the claim 3 wording (Section 4). Cite Satpy (parallax modifier and INSAT reader), pyparallax, JParallaxCorrect, goes-ortho, Deng & Ma (2025) and Bieliński (2020). |
| Results / Discussion (navigation) | "INSAT-3DR L1C navigation errors are seasonal (7–20 km west…, linked to the yaw flip)" | Use the claim 4 wording (Section 5). Cite Jindal et al. (2014) and the MOSDAC DQE reports. Keep "consistent with" or "attributed to" for the yaw-flip link. Optionally cite Deng & Ma (2025) and Tan et al. (2020) for methods. |
| Discussion (Sec. 6.x, measures) | Measure dependence (2–5 km; ~5 %) | Use the claim 5 wording (Section 6). **Add a paragraph on the conflicting case studies** (Section 9, third row). |
| Methods 4.8 / Discussion 6.8 (U-Net) | Implicit or explicit novelty of the A/B design | Cite D'Adderio et al. (2023) as the precedent with the same outcome, and Oya (2025), Hilburn et al. (2021) and Metzl et al. (2025) for implicit learning. Frame the novelty as INSAT-3DR, precipitation type, a ray-traced ellipsoidal correction, a controlled design and per-class metrics. |
| Progress report | "No study compares an ML model trained on uncorrected versus corrected geostationary inputs" | **Delete.** Replace with the claim 6 wording (Section 7). |
| Results / Discussion (heights) | IR cold-core tops ~3.2 km above Ku tops; effective height | Present as consistent with Song et al. (2020). Cite Monsalve et al. (2026), Wiltink et al. (2025), Virts & Koshak (2020) and the fixed-height conventions (Hilburn et al., 2021; Sun et al., 2024) for the effective height. |
| Discussion (ISRO DQE comparison; carried over from 26 Oct) | — | One sentence comparing the MOSDAC L1B DQE errors with the L1C coastline estimates, noting that the products, years and methods differ. |

### Must-cite reference list

Format: Authors (Year). Title. *Venue*, volume, pages. DOI/URL. Items marked † need checking before citing.

1. Bieliński, T. (2020). A parallax shift effect correction based on cloud height for geostationary satellites and radar observations. *Remote Sensing*, 12(3), 365. https://doi.org/10.3390/rs12030365
2. Bluestein, H. B., Lindsey, D. T., Bikos, D., Reif, D. W., Wienhoff, Z. B. (2019). The relationship between overshooting tops in a tornadic supercell and its radar-observed evolution. *Monthly Weather Review*, 147, 4151–4176. https://doi.org/10.1175/MWR-D-19-0159.1
3. Brempong, E. A., Hassen, M. A., MohamedKhair, M. E., et al. (2025). Oya: Deep learning for accurate global precipitation estimation. arXiv:2511.10562 (preprint).
4. D'Adderio, L. P., Casella, D., Dietrich, S., Panegrossi, G., Sanò, P. (2023). A first step towards Meteosat Third Generation Day-2 precipitation rate product: deep learning for precipitation rate retrieval from geostationary infrared measurements. *Remote Sensing*, 15(24), 5662. https://doi.org/10.3390/rs15245662
5. Deng & Ma (2025). [FY-4B AGRI ray-tracing orthorectification and POC navigation correction]. *Science of Remote Sensing*. https://doi.org/10.1016/j.srs.2025.100348 † (full author names and title not in the notes)
6. Goyal, S., Mohapatra, M., Kumari, P., Dube, S. K., Rajendra, K. (2017). Validation of Advanced Dvorak Technique (ADT) over north Indian Ocean. *Mausam*, 68(4), 689–698. https://doi.org/10.54302/mausam.v68i4.768
7. Harjupa, W., Nakakita, E., Sumida, Y., Yamaguchi, K. (2017). Preliminary investigation of generation of guerilla-heavy rainfall using Himawari-8 and XRAIN information in Kinki region. *DPRI Annuals*, No. 60B, 575–583.
8. Hilburn, K. A., Ebert-Uphoff, I., Miller, S. D. (2021). Development and interpretation of a neural-network-based synthetic radar reflectivity estimator using GOES-R satellite observations. *Journal of Applied Meteorology and Climatology*, 60, 3–21. https://doi.org/10.1175/JAMC-D-20-0084.1 † (DOI from memory; arXiv:2004.07906 verified)
9. ISRO/SAC (2015). *INSAT-3D ATBD Document*, May 2015, Chapter 4(B) Hydro-Estimator, Sec. 4.4(c), pp. 75–76. https://mosdac.gov.in/docs/INSAT_3D_ATBD_MAY_2015.pdf
10. Jindal, D., Prakash, …, Sanghvi, …, Kartikeyan, B., Gopala Krishna, B. (2014). INSAT-3D Quality Analysis System (i3dQAS). *ISPRS Archives*, XL-8, 257–263. https://doi.org/10.5194/isprsarchives-XL-8-257-2014 † (complete the initials)
11. Kotarba, A. Z. (2026). Evaluation of a moist-adiabat cloud-top height retrieval for parallax correction of deep convective clouds across Meteosat generations. *Atmospheric Measurement Techniques*, 19, 6193–6208. https://doi.org/10.5194/amt-19-6193-2026
12. Liu, C., Zipser, E. J., Nesbitt, S. W. (2007). Global distribution of tropical deep convection: different perspectives from TRMM infrared and radar data. *Journal of Climate*, 20, 489–503. https://doi.org/10.1175/JCLI4023.1
13. Malhan, …, Sehgal, …, Giri, …, Mishra, … et al. (2022). Comparative analysis of sub-division wise rainfall INSAT-3D vs. ground based observations. *Mausam*, 73(4), 833–842. https://doi.org/10.54302/mausam.v73i4.5877 † (complete the author list)
14. Mishra, A. K., Tomar, C. S., Kumar, G., Bhan, S. C. (2023). Reconstructing radar reflectivity by integrating GPM and INSAT-3D observations for near real-time monitoring of convective storms over India. *Weather*, 78, 224–227. https://doi.org/10.1002/wea.4443
15. Mishra, A. K., Chhari, …, Kumar, …, Shukla, … et al. (2025). Next-gen storm nowcasting: harnessing satellite-based radar reflectivity over India. *Theoretical and Applied Climatology*, 156, 428. https://doi.org/10.1007/s00704-025-05650-5 † (author list)
16. Mishra, A. K. et al. (2026). [INSAT-3D + GPM chapter]. Springer Atmospheric Sciences. https://doi.org/10.1007/978-981-95-5409-6_11 † (title not in the notes)
17. Monsalve, A. F., Moreno, H. A., Goldenstern, E., Kummerow, C. D. (2026). Quantifying the effect of a parallax-correcting algorithm for passive microwave satellite precipitation retrievals across the conterminous United States. *Journal of Hydrometeorology*, 27, 153–165. https://doi.org/10.1175/JHM-D-24-0060.1
18. Radová, M., Seidl, J. (2008). Parallax applications when comparing radar and satellite data. *Proc. EUMETSAT Meteorological Satellite Conference*, Darmstadt.
19. Satpy developers (Pytroll). `satpy.modifiers.parallax` (experimental since v0.37) and reader `insat3d_img_l1b_h5`. https://github.com/pytroll/satpy (cite the version used; a software DOI is not in the notes)
20. Song, H.-J., Kim, S., Roh, S., Lee, H. (2020). Difference between cloud top height and storm height for heavy rainfall using TRMM measurements. *Journal of the Meteorological Society of Japan*, 98(5), 901–914. https://doi.org/10.2151/jmsj.2020-044
21. Sun, L., Zhuge, X., Zhu, S. (2024). Geostationary satellite-based overshooting top detections and their relationship to severe weather over eastern China. *Remote Sensing*, 16, 2015. https://doi.org/10.3390/rs16112015
22. Tsujino, T. (tomonori-93). JParallaxCorrect / JParallaxCorrect.jl (software, LGPL-2.1). https://doi.org/10.5281/zenodo.18870145
23. Tsukada (tsukada-cs). pyparallax (software, GPL-3.0). https://github.com/tsukada-cs/pyparallax † (Zenodo DOI not in the notes)
24. Varma, A. K., Gairola, R. M. (2015). *Algorithm Theoretical Basis Document: Hydro-Estimator (Modified)*. SAC/EPSA/AOSG/SR/04/2015, Space Applications Centre, ISRO. https://mosdac.gov.in/docs/HEM_rain-revised-atbd.pdf
25. Vicente, G. A., Davenport, J. C., Scofield, R. A. (2002). The role of orographic and parallax corrections on real time high resolution satellite rainfall rate distribution. *International Journal of Remote Sensing*, 23, 221–230. https://doi.org/10.1080/01431160010006935
26. Virts, K. S., Koshak, W. J. (2020). Mitigation of Geostationary Lightning Mapper geolocation errors. *Journal of Atmospheric and Oceanic Technology*, 37, 1725–1736. https://doi.org/10.1175/JTECH-D-19-0100.1
27. Wiltink, J. I., Deneke, H., van Heerwaarden, C. C., Meirink, J. F. (2025). Evaluating parallax and shadow correction methods for global horizontal irradiance retrievals from Meteosat SEVIRI. *Atmospheric Measurement Techniques*, 18, 3917–3936. https://doi.org/10.5194/amt-18-3917-2025

Recommended, not mandatory:
- Pandjaitan, B. S. et al. (BMKG), AOMSUC-12 abstract S41-14.
- Setvák et al. (2010), doi:10.1016/j.atmosres.2010.03.009.
- Heymsfield et al. (1983), *J. Atmos. Sci.* 40, 1740–1755.
- Cooney et al. (2021), doi:10.1029/2020JD034319.
- Dworak et al. (2012), doi:10.1175/WAF-D-11-00070.1.
- Zhang, Y., Qie, X. et al. (2026), *ESSD* 18, 5773–5791, doi:10.5194/essd-18-5773-2026.
- Wang, J. et al. (2026), HailDeformer, doi:10.3390/rs18111743.
- Metzl et al. (2025), doi:10.1175/AIES-D-25-0035.1.
- Beusch et al. (2018), doi:10.3390/rs10060939.
- goes-ortho (https://github.com/spestana/goes-ortho).
- Takenaka et al. (2020), doi:10.3390/rs12152472.
- Tan et al. (2020), doi:10.1117/1.JRS.14.032405.
- Gairola et al. (2020), doi:10.20937/atm.52630, as an example of INSAT–GPM collocation without parallax.

---

## 11. Coverage and remaining risk

### Sources reached

- OpenAlex (full, including full-text search filters).
- Google Scholar, about 9 result pages before a redirect; the bot check was not circumvented.
- Europe PMC full text and CrossRef metadata.
- The MOSDAC document library (www.mosdac.gov.in; dr.mosdac.gov.in timed out).
- Copernicus (AMT, ESSD), arXiv, J-STAGE, the EUMETSAT and MDPI content delivery networks, Dryad, GitHub and the Mausam OJS metadata search.

### Sources blocked or unavailable

- **Scopus and Web of Science** were not available.
- Semantic Scholar returned HTTP 429 throughout, so no full-text snippet search was possible.
- ias.ac.in (JESS, Current Science), ScienceDirect, Wiley/AGU, AMS journals, SAGE, ResearchGate and the mdpi.com HTML pages returned 403.
- TROPMET and ISRS proceedings are not indexed online.
- The 2007 SAC/IMDPS/TN-05 HE ATBD is not online.

### What a manual Scopus / institutional check should still cover

1. **The Mishra et al. INSAT-3D + GPM DPR papers** (*Weather* 2023; *TAAC* 2025; Springer 2026). Do they parallax-correct INSAT before matching to DPR? They are the most likely place for an undisclosed correction and the main residual risk to claim 2.
2. Scopus query: `TITLE-ABS-KEY(parallax) AND ALL(INSAT OR Kalpana)`. Also run `TITLE-ABS-KEY(parallax AND (geostationary OR SEVIRI OR Himawari OR GOES) AND (GPM OR DPR OR "precipitation radar"))`, to test the broader "any GEO against spaceborne radar" statement.
3. JESS and Current Science full texts (e.g. JESS 130:0037 on INSAT-3D IMSRA, and SATCON 131:169).
4. Full texts of the snippet-only items: Singh et al. 2019 (*J. Hydrol.*), Singh et al. 2018 (*JISRS*), Kumar et al. 2019 (IGI) and Mohapatra & Vijay Kumar 2017.
5. Cintineo et al. (2020): what does it actually say about parallax? The notes disagree.
6. The DOI of Hilburn et al. (2021) and the Hydronn citation. The notes give two different page numbers: *AMT* 15, 5033 (`radar_validation.md`) and *AMT* 15, 6907 (`ml_inputs.md`).
7. Whether Vicente et al. (2002) validated their correction against radar. A secondary snippet says so; it is unverified.
8. The NWC SAF PLAX tool documentation (Earth model, terrain handling).
9. INSAT-3DR yaw-flip dates (ISRO/SAC or the IMD SatMet SOP), and units in the MOSDAC DQE reports.
10. Watch for publications from the IIT Hyderabad INSAT-3D/3DR precipitation-type ML project.

### Residual risk by claim

| Claim | Risk |
|---|---|
| 1 | Low after rewording. |
| 2 | Low to moderate, mainly the Mishra papers. |
| 3 | Low after rewording. |
| 4 | Low to moderate: internal ISRO reports may exist that are not indexed. |
| 5 | Low for the framing; the risk is that reviewers raise the cell-scale case studies if the paper does not discuss them. |
| 6 | Resolved: drop the claim. |
| 7 | Low when presented as corroboration. |
