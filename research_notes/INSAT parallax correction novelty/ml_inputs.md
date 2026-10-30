# ML/DL models trained on uncorrected vs parallax-corrected geostationary input

Searched 2026-10-30. This note tests the earlier claim: "No study compares an ML model trained on uncorrected versus corrected geostationary inputs."

## Verdict

**The claim is falsified. Do not use it in the manuscript.**

At least one peer-reviewed study runs the same A/B experiment as our Model A / Model B design:

- **D'Adderio, Casella, Dietrich, Panegrossi & Sanò (2023)**, *Remote Sensing* 15(24), 5662, https://doi.org/10.3390/rs15245662
- **Setup.** A U-Net retrieves precipitation rate from MSG SEVIRI IR, trained against GPM DPR-GMI 2B-CMB. The authors parallax-shifted the SEVIRI inputs using NWC SAF CTH. They then trained a second U-Net "with the same architecture and hyperparameter[s]" and compared the two against DPR on the test set.
- **Result.** The uncorrected U-Net was better: "the not-parallax-corrected U-Net outperformed the parallax-corrected U-Net in terms of accuracy (RMSE, MAE) and detection of precipitation (POD, FAR, CSI)."
- This is the same direction as our result (no gain, convective CSI slightly worse).

How our study still differs (these are the defensible novelty points):

1. Satellite and region: INSAT-3DR over India/Indian Ocean, not SEVIRI.
2. Task: a four-class precipitation-type target (stratiform/convective, rain/no-rain), not a rain-rate regression.
3. Attention U-Net.
4. Physically rigorous parallax correction (ray-traced ellipsoid with effective height), not a simple Δx = CTH·tanθ shift.
5. Quantified reporting. D'Adderio et al. give the A/B result in one qualitative paragraph (Section 3.3), with no numbers, no confidence intervals and no per-class breakdown.
6. Controlled design: identical labels, splits and seed.

Other relevant evidence:

- **Implicit-learning argument:** made by at least 3 papers (Hilburn et al. 2020/21; D'Adderio et al. 2023; Metzl et al. 2025, which cites Cintineo et al. 2020).
- **Parallax-aware alternatives that did not help:** Oya (2025) added CTH and viewing-geometry inputs and saw no gain.
- **Learned alignment instead of geometric correction:** HailDeformer (2026), whose ablation shows the alignment module helps most.
- **Explicit input correction, no ablation:** Beusch et al. 2018 (SEVIRI ANN), Hilburn et al. (fixed 10 km), and the LightningCast output.
- **Indian INSAT-3D/3DR DL work:** none found that applies or tests parallax correction.

Suggested replacement wording for the manuscript:

> "To our knowledge, only one previous study has compared a deep-learning model trained on uncorrected versus parallax-corrected geostationary input (D'Adderio et al., 2023, SEVIRI U-Net for rain rate), and it likewise found the uncorrected model performed better; ours is the first such controlled comparison for INSAT-3DR, for precipitation type, and with quantified per-class metrics."

Caveat: "first for INSAT-3DR / precipitation type" holds only for the searches recorded below. I cannot rule out non-indexed theses or conference papers.

---

## A. Explicit with-vs-without parallax ablations of an ML model

### A1. D'Adderio et al. 2023: direct A/B, uncorrected model wins (KEY PAPER)

- **Citation:** D'Adderio, L. P., Casella, D., Dietrich, S., Panegrossi, G., Sanò, P. (2023). "A First Step towards Meteosat Third Generation Day-2 Precipitation Rate Product: Deep Learning for Precipitation Rate Retrieval from Geostationary Infrared Measurements." *Remote Sensing* 15(24), 5662. https://doi.org/10.3390/rs15245662. Published 7 Dec 2023. Open access (CC BY).
- **Data:**
  - Meteosat-10 SEVIRI IR channels.
  - Ancillary inputs: lat/lon, surface type, and NWC SAF GEO v2021 cloud-top height (CTH).
  - Reference: GPM DPR-GMI 2B-CMB precipitation.
  - Model: U-Net.
- **Section 3.3, "Parallax Displacement Error" (verbatim, read from the MDPI full text):**
  - "A very significant result obtained is that the trained U-Net is able to correct (or at least mitigate) the parallax error without being trained against a dataset already corrected for parallax displacement."
  - "As a comparative test, a simple parallax correction tool has been developed. The SEVIRI data used in the TDR have been corrected by applying a shift Δx to each pixel and channel proportional to the CTH as (3) where θ is the MSG satellite viewing angle. The direction of the shift was defined by the azimuth of MSG. This correction has been used to build a new training dataset that has been exploited for training an additional U-Net, with the same architecture and hyperparameter of the U-Net used within this study. The precipitation rates predicted by the two U-Nets have been compared with the reference DPR precipitation in the TD. The results showed how the not-parallax-corrected U-Net outperformed the parallax-corrected U-Net in terms of accuracy (RMSE, MAE) and detection of precipitation (POD, FAR, CSI)."
- **Abstract:** "the U-Net is able to account for and correct the parallax displacement that affects the measurement as the satellite viewing angle increases."
- **Evidence shown:** Figure 8 shows a case (12 July 2020, NE full disc) where the U-Net's rain maxima are displaced to the SW of the coldest TBs. The displacement agrees with DPR.
- **Limitations relative to ours:**
  - No numbers are reported for the A/B comparison.
  - The correction is a crude Δx shift, and the authors note the "hole" problem.
  - CTH is also a network input, so the uncorrected model is given the information it needs to learn the shift.
  - Rain-rate regression, not classification.
  - Single seed and repeatability are not discussed.

### A2. Brempong et al. 2025 (Oya): parallax-related extra inputs, no gain

- **Citation:** Brempong, E. A., Hassen, M. A., MohamedKhair, M. E., et al. (2025). "Oya: Deep Learning for Accurate Global Precipitation Estimation." arXiv:2511.10562 (v2, 26 Nov 2025). Preprint; I found no journal version.
- **Setup:** Two-stage U-Net on GEO VIS/IR (Meteosat 0° and others), trained against GPM CORRA.
- **Quotes (Section 4.2):**
  - "Another likely cause is parallax shift, which causes misplacement of high elevation cloudtops."
  - "We experimented with additional inputs that could help the model deal with the parallax effect. These include cloud top height, latitude and latitude coordinates, azimuth and zenith angles and elevation. Yet, the models trained with these additional inputs did not perform better than the models trained only with GEO inputs."
- **Assessment:** This is an ablation of parallax-aware inputs, not of geometric correction of the inputs. It supports the "no gain" finding. The conclusion lists "mitigating parallax ... at higher latitudes" as an open challenge.

### A3. Wang et al. 2026 (HailDeformer): learned alignment, not geometric correction

- **Citation:** Wang, J., Wang, H., Li, J., Liu, T., Gu, T., Xue, Y. (2026). "Joint Hail Detection from Satellite and Radar Observations with Spatially Adaptive Alignment and Wavelet-Gated Refinement." *Remote Sensing* 18(11), 1743. https://doi.org/10.3390/rs18111743 (published 29 May 2026).
- **Data:** FY-4A AGRI + CINRAD radar.
- **Quotes:**
  - "the real bottleneck is the spatial mismatch from parallax and storm tilt, not the fusion step itself."
  - Ablation: removing the deformable alignment module (DSDCA) drops F1 from 0.864 to 0.836 and mAP@0.5 from 0.916 to 0.896.
- **Assessment:** The alignment is learned and the offsets are explicitly "without imposing a geometric parallax direction or magnitude." There is no geometric parallax-correction arm. This is evidence for category (c), learned displacement, with a with/without-alignment ablation.

### A4. Yang, Chen & Kuo 2024 (IGARSS): dual-GEO input to "address" parallax, no ablation

- **Citation:** Yang, Y., Chen, H., Kuo, K.-S. (2024). "Deep Learning for Precipitation Retrievals Using Combined Measurements from GOES-16 and GOES-18 Satellites." *IGARSS 2024*, pp. 1292–1295. https://doi.org/10.1109/IGARSS53475.2024.10641567. Full text read via par.nsf.gov/servlets/purl/10595764.
- **Quotes:**
  - "the framework in [5] overlooked the parallax shift issue of ABI measurement."
  - "we propose a DL framework ... leveraging the combined observations from the duo GOES satellites ... to address the parallax shift."
- **Assessment:** The paper compares only against the operational RRQPE. There is no single-satellite vs dual-satellite ablation and no geometric correction. Not a with/without study.
- Ref [5] is Yang, Chen, Hilburn, Kuligowski, Cifelli (2023), IEEE TGRS 61, which per [4] did not handle parallax. I did not verify its DOI.
- The related CSU dissertation (Yang 2026, "Continual learning for geostationary satellite remote sensing of precipitation", https://doi.org/10.25675/3.027523) has an abstract that does not mention parallax. I did not read the full text.

## B. Papers arguing the network learns the displacement implicitly (category c)

| Paper | Quote | What they did |
|---|---|---|
| Hilburn, Ebert-Uphoff & Miller, "Development and Interpretation of a Neural Network-Based Synthetic Radar Reflectivity Estimator Using GOES-R Satellite Observations", arXiv:2004.07906 (2020); published in *J. Appl. Meteor. Climatol.* 60(1), 2021, doi 10.1175/JAMC-D-20-0084.1 (journal DOI from memory, please verify) | "To remove parallax offsets to first order, we assumed a height of 10 km." / "the CNN seems to learn to apply additional spatial displacements on its own based on what it sees in the training data." | GREMLIN CNN (GOES ABI+GLM → MRMS). Inputs corrected with a fixed 10 km height. No ablation. |
| D'Adderio et al. 2023 (A1) | "able to correct (or at least mitigate) the parallax error without being trained against a dataset already corrected" | A/B ablation (see A1). |
| Metzl, Vahid Yousefnia, Müller, Poli, Celano, Bölle (2025), "Physical Scales Matter: The Role of Receptive Fields and Advection in Satellite-Based Thunderstorm Nowcasting with CNNs", *AIES*, https://doi.org/10.1175/AIES-D-25-0035.1 (arXiv:2504.09994) | "Prior work (Cintineo et al. 2020) has demonstrated that for applications combining satellite imagery with ground-based observations in ML models, parallax effects exert minimal influence on model performance. Thus, no parallax correction is applied in this study." | MSG SEVIRI + LINET ResU-Net. No correction, justified by a citation. |
| Cintineo et al. (2020), "A Deep-Learning Model for Automated Detection of Intense Midlatitude Convection Using Geostationary Satellite Images", *Wea. Forecasting* 35, 2567–2588, https://doi.org/10.1175/WAF-D-20-0028.1 | **Not verified.** The AMS and NOAA-repository full texts were blocked for me, so I could not read what Cintineo et al. actually say about parallax. Metzl et al. cite it as evidence of "minimal influence". | CNN on ABI + GLM with human labels. **Action: check the full text before citing it as a parallax result.** |
| Li et al. (2026), "Video Diffusion for Satellite-based High-Dynamical-Fidelity Precipitation (HiDFiP) Field Generation", arXiv:2608.21812 | The diffusion model is claimed to correct "part of the systematic position/timing offsets inherent in satellite retrievals, such as parallax shift" | Implicit claim. No ablation. |

## C. ML studies that explicitly parallax-correct inputs or labels (no with/without test)

- **Beusch, Foresti, Gabella & Hamann (2018)**, "Satellite-Based Rainfall Retrieval: From Generalized Linear Models to Artificial Neural Networks", *Remote Sensing* 10(6), 939, https://doi.org/10.3390/rs10060939.
  - SEVIRI → Swiss radar using GLM and ANN models.
  - "All of these predictors are available during both day- and nighttime and they were all parallax corrected based on the NWC-SAF cloud top height."
  - The CPP product was also "parallax corrected ... with PyTroll."
  - No ablation.
- **Hilburn et al. 2020/21:** fixed 10 km height (see B).
- **Cintineo et al. 2022, ProbSevere LightningCast:** *Wea. Forecasting* 37, doi 10.1175/WAF-D-22-0019.1 (DOI from memory, please verify).
  - Training input and output parallax handling not verified.
  - The operational CSPP-Geo package offers optional parallax correction of the output. The CIMSS QuickGuide notes the displayed data are parallax-corrected.
  - A NWS HWT blog post ("Utility of Parallax Corrected LightningCast Versus Non-Corrected within DDC", inside.nssl.noaa.gov/ewp) compares corrected and uncorrected display for forecasters. That is a post-processing comparison, not an ML training ablation.
- **Leinonen, Hamann, Germann & Mecikalski (2022)**, *NHESS* 22, 577–597, https://doi.org/10.5194/nhess-22-577-2022. The only parallax sentence is "The GLM L2 data are provided with parallax correction already performed, obviating the need for this step." The paper says nothing on ABI parallax.
- **Xu et al. (2026)**, "Cloud-top infrared observations reveal the four-dimensional precipitation structure", arXiv:2605.07499. FY-4B → DPR profiles. "To mitigate parallax effects and displacement errors in convective systems, we developed a robust spatiotemporal matching framework based on a KD-tree nearest-neighbour algorithm." This is matching tolerance, not geometric correction, and there is no ablation.
- **Brüning et al. (2024)**, AMT 17, 961–978, https://doi.org/10.5194/amt-17-961-2024 (SEVIRI → CloudSat 3D tomography). Future work only: "addressing the cloud parallax shift in high-angle satellite observations could enhance the results."

## D. Major ML GEO works checked whose full text does NOT mention parallax (negative results)

Each full text was grepped for "parallax" and nothing was found:

- **Lee, Kummerow & Ebert-Uphoff (2021)**, AMT 14, 2699, https://doi.org/10.5194/amt-14-2699-2021. GOES-16 convection CNN with MRMS labels.
- **Pfreundschuh et al. (2022) Hydronn**, AMT 15, 6907, https://doi.org/10.5194/amt-15-6907-2022. GOES-16 CNN trained on GPM CMB over Brazil. This is the closest analogue to our GPM-label design, and it makes no mention of parallax.
- **Leinonen et al. (2023)**, GRL, https://doi.org/10.1029/2022GL101626 (arXiv:2211.01001). Multi-hazard DL nowcasting.
- **Stock et al., SRViT**, arXiv:2406.16955. Successor to GREMLIN.
- **Moraux et al. (2021)**, "A Deep Learning Multimodal Method for Precipitation Estimation", *Remote Sensing* 13(16), 3278. SEVIRI + OPERA + gauges.
- **Himawari-8 U-Net reflectivity reconstruction**, *Remote Sensing* 13(16), 3330, https://doi.org/10.3390/rs13163330. Uses band 16 as a cloud-height proxy, but has no parallax text.
- **Huang (2026)**, Chalmers MSc thesis on CHIMP / MTG-FCI deep-learning precipitation.
- **Andrychowicz et al. Global MetNet**, arXiv:2510.13050 (checked via WebFetch). Its GEO-mosaic ablation does not address parallax.

Abstract-only checks found no parallax mention:

- PERSIANN-CNN (Sadeghi et al. 2019) and the Himawari PERSIANN-CNN adaptation
- FY-4A SW-Net, RF and LightGBM QPE papers
- GK-2A IR2Rain cGAN and Pix2Pix rainfall (*Remote Sensing* 18, 188)
- GK-2A proxy radar (ECSS2023-77)
- Itterly/Scarino hail DNN (AIES 2023, 10.1175/AIES-D-22-0042.1; the NTRS preprint full text has no parallax mention)
- GROMIT (IPWG 2026 slides; IR + DPR convective probability)

## E. India: INSAT-3D/3DR/Kalpana deep learning

- No published DL/ML study on INSAT-3D/3DR (rainfall, precipitation type, convection or nowcasting) was found that applies or tests parallax correction.
- **IIT Hyderabad project (2024–26)**, "Precipitation type classification from INSAT-3D/3DR satellite observations using explainable AI/ML (XAI/ML)".
  - Listed on indiascienceandtechnology.gov.in; the page fetch failed on a certificate error, so I saw only the search snippet.
  - It targets an ML convective/stratiform product. It is the closest Indian competitor to our task.
  - I found no publication, and the snippet has no parallax mention. **Watch this one.**
- Other Indian work found, none with parallax:
  - Nath et al. 2008 ANN on INSAT QPE (*Geofizika*)
  - INSAT-3DR TIR LSTM nowcasting (*MAUSAM*, IMD)
  - R2-UNet INSAT-3D frame prediction (project page)
  - EGU24-19394 NE India U-Net
  - Springer chapter on INSAT-3D CNN cyclone intensity
- Non-ML INSAT/GPM collocation work (e.g., the INSAT-3D/GPM synergy paper on redalyc) uses ±10 min matching with no parallax step.
- The only INSAT parallax + DL hit is the user's own repo, PyGeoParallax-IN on GitHub.

## Queries tried

**WebSearch:**
- deep learning geostationary satellite parallax correction ablation precipitation (extended)
- "parallax" CNN GOES-16 ABI radar reflectivity synthetic
- "parallax correction" machine learning SEVIRI convection nowcasting
- INSAT-3D deep learning precipitation GPM DPR parallax
- "Meteosat Third Generation Day-2 Precipitation Rate" U-Net parallax corrected
- Himawari-8 deep learning radar reflectivity parallax CTH
- GK-2A AMI deep learning precipitation parallax
- INSAT-3DR deep learning rainfall CNN India
- Lee Kummerow Ebert-Uphoff convection GOES-16 parallax
- LightningCast Cintineo parallax GLM
- Leinonen thunderstorm nowcasting parallax
- Pfreundschuh GOES Brazil parallax
- "parallax" "neural network" geostationary "learn" displacement (extended)
- FY-4A AGRI DL precipitation parallax
- convective initiation ML Himawari SEVIRI parallax labels
- INSAT-3D GPM DPR precipitation type ML
- "Physical Scales Matter" ...
- Cintineo 2020 intense convection parallax (standard and extended)
- PERSIANN-CNN/CCS parallax
- hail detection DL geostationary parallax
- Kalpana/INSAT-3D nowcasting U-Net parallax
- U-Net SEVIRI OPERA parallax
- GOES IR-to-radar U-Net "parallax-corrected" MRMS
- Himawari-8 CNN precipitation parallax Japan
- CHIMP Pfreundschuh parallax
- convective/stratiform GEO IR DL GPM DPR parallax (extended)
- INSAT-3DR ML rainfall GPM parallax CTH collocation (extended)

**APIs:**
- OpenAlex `search=parallax deep learning geostationary` and `parallax neural network satellite precipitation` (about 100 titles screened).
- Semantic Scholar paper lookup for 10.3390/rs15245662.
- The Semantic Scholar snippet-search API returned HTTP 429 every time, so no full-text snippet search was possible.

**Full texts grepped for "parallax":**
- D'Adderio 2023 (MDPI HTML)
- Hilburn arXiv 2004.07906
- Oya
- Yang IGARSS 2024
- Lee 2021
- Hydronn
- Leinonen 2022 and 2023
- Metzl 2025
- Brüning 2024
- HiDFiP
- Himawari CREF 2021
- SRViT
- Moraux 2021
- Huang 2026 thesis
- Xu 2026
- Itterly hail DNN
- HailDeformer
- Beusch 2018
- GROMIT slides

**Blocked or unread:**
- AMS journals (Cintineo 2020 and 2022, Metzl AIES version)
- NOAA repository PDF of Cintineo 2020
- IIT Hyderabad project page
