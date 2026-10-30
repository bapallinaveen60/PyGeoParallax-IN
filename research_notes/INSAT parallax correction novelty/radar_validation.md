# Prior work: validating geostationary parallax correction against radar / lightning / ground truth

Compiled 2026-10-30 for the INSAT-3DR parallax manuscript (38 monsoon cases vs GPM DPR).

## Verdict (read this first)

1. **"First validation of INSAT parallax correction against spaceborne radar": the claim holds as far as I could find, but word it carefully.**
   - I found no paper, report or ATBD that compares parallax-corrected and uncorrected INSAT/Kalpana imagery against GPM DPR, TRMM PR, CloudSat or Indian DWRs.
   - There are three caveats.
     - The operational **INSAT-3D Hydro-Estimator already applies a Vicente et al. (2002) parallax correction**, with height taken from Tb and a standard atmosphere, before computing rain rate (SAC ISRO ATBD, 2015). So "first parallax correction for INSAT" would be false. "First validation of an INSAT parallax correction against spaceborne radar" still looks safe.
     - IMD has already **collocated INSAT-3D with GPM DPR**: Mishra et al. 2023 *Weather*, and Mishra et al. 2025 *TAAC*. They do not appear to treat parallax, but I checked only the abstracts.
     - Even for *any* geostationary satellite, I found **no multi-case, before/after validation of parallax correction against spaceborne radar**. Kotarba (2026, AMT) says explicitly that CloudSat/CALIPSO "cannot ... anchor the parallax-correction step itself". The closest work is Sun et al. 2024: Himawari-8 and FY-4A overshooting tops (OTs) vs GPM KuPR OTs. They parallax-correct with a fixed 14 km height, but they never test whether the correction helps. The broader claim "first validation of GEO parallax against spaceborne radar" may therefore also be defensible, but it carries more risk; I recommend stating it as "to our knowledge".
   - Prior radar validations against *ground* radar exist only as single-case or few-case demonstrations (Bieliński 2020; Radová & Seidl 2008; Harjupa et al. 2017; BMKG 2022/23). Bieliński's result is r 0.556 → 0.683 for **one** SEVIRI scene.
2. **"Measure-dependent result": the ingredients are known, but I found no paper that states or quantifies it.**
   - Known already:
     - Wiltink et al. 2025: the benefit of correction depends on the correction variant, cloud regime and resolution, and parallax-only correction can *increase* error. An empirical optimal shift beats geometric correction.
     - Monsalve et al. 2026 (JHM): correcting with the IR cloud-top height *worsens* RMSE against MRMS (+7.3 %), while correcting with the freezing level improves it (−3.95 %), and the sign flips by event and season.
     - Coldest IR tops can be displaced from radar cores by storm structure: Bluestein et al. 2019 (~10 km), cold-ring and enhanced-V storms (Setvák et al. 2010; Heymsfield et al. 1983), and false OTs from cold outflow (Cooney et al. 2021).
     - IR cloud top sits several km above the radar storm top: Song et al. 2020 (2.7–5.5 km) and Liu & Zipser 2007.
   - Not found: any paper reporting that a storm-scale field-correlation measure and a cell-scale cold-core-to-deep-echo measure disagree by a few km for the *same* storms and correction. That framing appears new.
   - **Tension to flag:** most prior cell-scale case studies report a *visible* uncorrected offset that correction removes.
     - BMKG Himawari: OT to extreme-weather site ~13 km uncorrected, <3 km corrected.
     - Harjupa et al.: Himawari coldest-BT to XRAIN max, offsets large enough to regress against BT.
     - Radová & Seidl: large before/after difference for an Austrian storm.
   - The manuscript's finding that only ~5 % of the computed parallax is visible at cores therefore conflicts with these. Discuss why (tropical monsoon storms, 4 km pixels, DPR 5 km footprint, near-nadir geometry at 74°E, case selection).
3. **IR cloud-top height ~3.2 km above the Ku storm top is consistent with prior TRMM results.** Song et al. 2020 report a CTH−SH difference of 2.7–5.5 km by region for heavy-rain pixels. Cite it as corroboration, not as a novel finding.
4. **Effective height below cloud top** has precedents that should be cited:
   - Monsalve et al. 2026 (freezing level, for passive microwave).
   - Wiltink et al. 2025 (40–50 % of Hc best for parallax-only; 70–90 % for combined correction).
   - Virts & Koshak 2020 (GLM optimal emitter height lower than the cloud-top ellipsoid; ellipsoid lowered from 16 to 14 km).
   - Fixed-height conventions: GREMLIN uses 10 km; Sun et al. 2024, Bedka 2011 and Dworak 2012 use 14 km.

---

## A. Studies comparing parallax-corrected vs uncorrected GEO imagery with radar or other ground truth

| # | Study | Satellite | Truth | Method | Quantitative result | Relevance |
|---|---|---|---|---|---|---|
| A1 | **Bieliński, T. (2020)** A Parallax Shift Effect Correction Based on Cloud Height for Geostationary Satellites and Radar Observations. *Remote Sens.* 12, 365. doi:10.3390/rs12030365 | MSG SEVIRI | Polish ground radar | Geometric (ellipsoid) correction. Pearson r between log(COT) and dBZ before and after correction | **One stormy scene (25 Jul 2015 13:00 UTC): r = 0.556 uncorrected, 0.683 corrected.** No multi-case statistics and no significance test. Residual differences attributed to <15 min time offset, sensor physics and resampling | Closest GEO-vs-radar before/after test. Single case, field-correlation measure only |
| A2 | **Radová, M., Seidl, J. (2008)** Parallax applications when comparing radar and satellite data. Proc. EUMETSAT Met. Sat. Conf., Darmstadt. PDF: eumetsat.int (pdf_conf_p_s5_22_radova_p.pdf) | MSG-1 SEVIRI | Austrian radar, CAPPI 15 km | Radar reprojected to GEO view at a height level. Cold-ring storm, 21–22 Jun 2006 | Parallax table for 48.5°N: 16.4 km at 10 km height, 24.7 km at 15 km, 28.0 km at 17 km. **Qualitative only:** "large difference in the relative location" with and without correction | Cell-scale overlay. Coldest pixels form a ring around a warm spot, not over the radar core |
| A3 | **Harjupa, W., Nakakita, E., Sumida, Y., Yamaguchi, K. (2017)** Preliminary investigation of generation of guerilla-heavy rainfall using Himawari-8 and XRAIN information in Kinki region. *DPRI Annuals* No. 60B, 575–583 (kyoto-u.ac.jp/nenpo/no60/ronbunB/a60b0p28.pdf) | Himawari-8 | XRAIN X-band radar | **Empirical shift:** distance from the lowest-BT pixel to the highest radar echo for 16 heavy-rain events, regressed on BT | Distance = −0.77·BT + 25.5 (R² = 0.874; the paper says "meter", almost certainly km). Corrected BT field sits over the rain echo | Direct precedent for an empirical **cold-core to radar-maximum** offset estimator. In Japan the uncorrected cold core was clearly displaced (NW) from the radar maximum |
| A4 | **Pandjaitan, B. S. et al. (BMKG)** Parallax correction methods and objective detection of overshooting cloud tops surrounding extreme weather events location in Indonesia. AOMSUC-12 abstract S41-14 (data.jma.go.jp/mscweb/en/aomsuc12/abstract/abst_S41_14.pdf) | Himawari-8 | Extreme-weather report sites (not radar) | Three height methods: lapse-rate proxy with fixed or ERA5 surface temperature, and JMA cloud-top height | OT to event distance **~13 km uncorrected, <3 km after all methods, <1 km for the lapse-rate methods**. One case study, Java | Cell-scale improvement reported, in contrast to the manuscript's "~5 % visible" |
| A5 | **Setiowati, A. O. (BMKG)** AOMSUC-13 presentation S2-07 (nmsc.kma.go.kr …/S2-07_Setiowati.pdf) | Himawari | Radar (planned) | CTH plus cloud type for Cb shift | Shifts ~6–10 km ENE. Adjusting against radar positions listed as future work | Gray literature; no scores |
| A6 | **Zhang, Y. et al. (2023)** A Parallax Shift Effect Correction Based on Cloud Top Height for FY-4A LMI. *Remote Sens.* 15, 4856. doi:10.3390/rs15194856 | FY-4A LMI (lightning), AGRI CTH | BLNET lightning network, radar | Ellipsoid CTH correction (ECPC) | Max deviation over Beijing 13.16 km at 12 km CTH. Corrected LMI is "closer" to BLNET with "higher consistency with radar" (no single score in the abstract) | Lightning analogue |
| A7 | **Zhang, Y., Qie, X. et al. (2026)** Corrected event dataset of FY-4A LMI, 2019–2023. *ESSD* 18, 5773–5791. doi:10.5194/essd-18-5773-2026 | FY-4A LMI | WWLLN (>9 M pairs), BLNET | CTH parallax correction, then spline correction curves | After parallax-only correction: 36.0 % of events within 15 km and 58.2 % within 20 km of WWLLN. After spline: 51.7 % and 74.8 %. Authors note CTH errors of ~1 km and 15 min sampling limit the geometric step | **Geometric CTH correction alone leaves large residuals.** Empirical correction adds most of the gain |
| A8 | **Virts, K. S., Koshak, W. J. (2020)** Mitigation of Geostationary Lightning Mapper Geolocation Errors. *JTECH* 37, 1725–1736. doi:10.1175/JTECH-D-19-0100.1 | GOES-16/17 GLM | Ground lightning networks | Optimal assumed emitter height | Original 16/6 km ellipsoid gave 20–30+ km errors near the limb. Lowered to 14/6 km in 2018, which "slightly improves" accuracy. Optimal heights vary by region and season and **~double the near-limb area with errors < ½ pixel** | **Effective height lower than cloud top**, found empirically |
| A9 | **Monsalve, A. F., Moreno, H. A., Goldenstern, E., Kummerow, C. D. (2026)** Quantifying the Effect of a Parallax-Correcting Algorithm for Passive Microwave Satellite Precipitation Retrievals across the Conterminous United States. *JHM* 27, 153–165. doi:10.1175/JHM-D-24-0060.1 (preprint arXiv:2509.18695) | GPM GMI / GPROF (plus GOES-16 cloud-top test) | GV-MRMS radar | Freezing-level (FL) height correction; 13 candidate heights FL ± 3 km | CONUS annual RMSE −1.6 %. July −3.95 %, ρ up by about 0.05. **Correcting with GOES-16 cloud-top height *raised* RMSE by 7.29 % (July 2020), while FL correction lowered it by 3.95 %.** Event-level changes range from −39 % to **+53 %**. No gain for winter or stratiform rain | Strongest precedent for (a) small or mixed gains, (c) a sign that depends on height choice and event, and an **effective height below cloud top** |
| A10 | **Wiltink, J. I., Deneke, H., van Heerwaarden, C. C., Meirink, J. F. (2025)** Evaluating parallax and shadow correction methods for global horizontal irradiance retrievals from Meteosat SEVIRI. *AMT* 18, 3917–3936. doi:10.5194/amt-18-3917-2025 (**citation confirmed**) | SEVIRI (SR and HRV) | 99 pyranometers (HOPE, Jülich, Apr–Jul 2013) | Parallax only, shadow only, combined, and **empirical optimal collocation shift** (daily and per time step) | Combined correction: HR RMSE −11.7 W m⁻² (−10.8 %). **Time-step optimal empirical shift is best: −15.6 W m⁻² (−14.5 %) HR, −8.1 W m⁻² (−7.6 %) SR.** Parallax-only can *increase* error depending on regime and resolution. Best height is **40–50 % of Hc for parallax-only** and 70–90 % for combined (not significant). Area-based Hc beats pixel-based Hc | Precedent for an empirical shift beating geometric correction, a reduced effective height, and regime and measure dependence |
| A11 | **Vicente, G. A., Davenport, J. C., Scofield, R. A. (2002)** The role of orographic and parallax corrections on real time high resolution satellite rainfall rate distribution. *IJRS* 23, 221–230. doi:10.1080/01431160010006935 | GOES (Auto-Estimator / Hydro-Estimator) | (Reportedly radar; **not verified**) | Tb → height via US Standard Atmosphere, then shift | Abstract gives no scores. A secondary snippet says radar max-correlation matching was used; **unverified** | Origin of the operational method, also used in the INSAT-3D HE (see D1) |
| A12 | **Roebeling, R. A., Holleman, I. (2009)** SEVIRI rainfall retrieval and validation using weather radar observations. *JGR* 114, D21202. doi:10.1029/2009JD012102 | SEVIRI | Dutch radar | Retrieval validation, no correction | Spatial-extent r ≈ 0.90; mean rain-rate r ≈ 0.63. Part of the differences attributed to "collocation errors and parallax shifts" | Shows that parallax limits scores; no correction test |
| A13 | **Bluestein, H. B., Lindsey, D. T., Bikos, D., Reif, D. W., Wienhoff, Z. B. (2019)** The Relationship between Overshooting Tops in a Tornadic Supercell and Its Radar-Observed Evolution. *MWR* 147, 4151–4176. doi:10.1175/MWR-D-19-0159.1 | GOES-16 | Mobile X-band and WSR-88D | Cloud tops parallax-corrected using radar echo-top height + 500 m | **Highest radar echo top displaced ~10 km (N/NE) from the main updraft and cloud top** during the supercell phase, then they converged. A 1 km height error gives a 1.1 km shift at that location. OT was "~10 km upstream" of the echo top | (b): cell-scale offsets from storm structure, comparable to the parallax itself |
| A14 | **Bernal Ayala, A. C., Gerth, J. J., Schmit, T. J., Lindstrom, S. S., Nelson, J. P. (2023)** Parallax Shift in GOES ABI Data. *J. Operational Meteor.* 11. doi:10.15191/nwajom.2023.1102 | GOES-16/17 ABI | NEXRAD, GLM | Uniform vs computed CTH; two cases | Qualitative; the hailstorm case shows a shift relative to NEXRAD and GLM | Operational guidance |
| A15 | **Sun, L., Zhuge, X., Zhu, S. (2024)** Geostationary Satellite-Based Overshooting Top Detections and Their Relationship to Severe Weather over Eastern China. *Remote Sens.* 16, 2015. doi:10.3390/rs16112015 | Himawari-8, FY-4A | **GPM KuPR-derived OTs** | Fixed **14 km** parallax correction; **10 km match radius** "for storm motion, parallax correction and other errors" | Best IR-contour algorithm: POD 62.1 %, FAR 36.6 %. Correction effect not tested | Only GEO-vs-spaceborne-radar convective comparison found with parallax correction, but it **does not validate the correction** |
| A16 | **Dworak, R., Bedka, K., Brunner, J., Feltz, W. (2012)** Comparison between GOES-12 Overshooting-Top Detections, WSR-88D Radar Reflectivity, and Severe Storm Reports. *WAF* 27, 684–699. doi:10.1175/WAF-D-11-00070.1 | GOES-12 | WSR-88D | OT vs composite reflectivity | "An OT often corresponds with the highest radar echo top and reflectivity maximum aloft". FAR 16 %, most accurate for BT < 200 K. (Fixed-height parallax treatment not verified; Sun et al. 2024 cite it for the 14 km convention) | (b): OT ≈ radar core, consistent with "cold cores sit on deep echoes" |
| A17 | **Cooney, J. W., Bedka, K. M., Bowman, K. P., Khlopenkov, K., Itterly, K. F. (2021)** Comparing Tropopause-Penetrating Convection Identifications Derived From NEXRAD and GOES Over the CONUS. *JGR* 126, e2020JD034319. doi:10.1029/2020JD034319 | GOES-13/16 | GridRad NEXRAD OTs | Large matched OT dataset | Detection rate ~60 % (G13) vs ~75 % (G16). **False detections are unavoidable because cold outflow from nearby or decayed OTs can be colder than the tropopause** | (b): coldest IR is not always over the active radar core. Full text (parallax and match radius) not accessed (403) |
| A18 | **Khlopenkov, K. et al. (2021)** Recent Advances in Detection of Overshooting Cloud Tops From Longwave IR Imagery. *JGR* 126, e2020JD034359. doi:10.1029/2020JD034359 | GOES-13/16 | Human and radar OTs | — | AUC 0.94 (G16) vs 0.78 (G13) | Context |
| A19 | **Hilburn, K., Ebert-Uphoff, I., Miller, S. D. (2021)** GREMLIN. *JAMC* 60, 3–21. doi:10.1175/JAMC-D-20-0084.1 | GOES-16 ABI and GLM | MRMS | CNN; training data parallax-corrected with a **fixed 10 km height** (Dryad dataset doc) | — | Effective-height convention below deep-convective tops |
| A20 | **Cintineo, J. L. et al. (2020)** A Deep-Learning Model for Automated Detection of Intense Midlatitude Convection Using Geostationary Satellite Images. *WAF* 35, 2567–2588. doi:10.1175/WAF-D-20-0028.1 | GOES-16 | Radar-labelled storms | No explicit correction | The model "learned the parallax relationship"; ICP contours are displaced S/E at high view angles. **No with/without test.** Metzl et al. (DLR, AMS preprint ~2025) cite it as showing parallax "exert[s] minimal influence on model performance" and skip correction | Relevant to the U-Net A/B: ML may absorb parallax |
| A21 | **D'Adderio, L. P. et al. (2023)** A First Step towards MTG Day-2 Precipitation Rate Product: Deep Learning … *Remote Sens.* 15, 5662. doi:10.3390/rs15245662 | MSG SEVIRI IR | H SAF / IMERG references | U-Net | Abstract says the U-Net "is able to account for and correct the parallax displacement" | ML absorbs parallax |
| A22 | **Brempong et al. (Oya, Google, ~2025)** | Global GEO | GPM | Added CTH, angles and lat/lon inputs to address parallax | "did not perform better" than GEO-only inputs | (a): no gain from explicit parallax information in ML |
| A23 | **Yang, Chen, Kuo (CSU, ~2024)** Deep learning precipitation retrieval using combined GOES-16 and GOES-18 (NSF PAR 10595764) | GOES-16/18 | — | Dual-view to address parallax | Claims superiority to RRQPE (conference paper) | Alternative to geometric correction |
| A24 | **Wang, J., Haijiang Wang et al. (2026)** Joint Hail Detection from Satellite and Radar Observations with Spatially Adaptive Alignment… *Remote Sens.* 18, 1743. doi:10.3390/rs18111743 | Chinese GEO | Radar | Learned deformable alignment | Notes that the satellite–radar offset comes from **parallax *and* storm tilt and varies across a storm**. The alignment module gives the largest gain | (b) stated explicitly; empirical alignment |

## B. Coldest IR tops vs radar cores: storm-structure offsets (question b)

- **Bluestein et al. 2019 (A13):** echo top displaced ~10 km from the updraft and cloud top, after parallax correction. Offset evolves through the storm life cycle (cyclic mesocyclogenesis).
- **Dworak et al. 2012 (A16):** OTs "often" coincide with the highest echo top and reflectivity maximum aloft. Supports "uncorrected or corrected cold cores sit on deep echoes" only after the right correction; not quantified in km.
- **Heymsfield, G. M., Blackmer, R. H., Schotz, S. (1983)** Upper-level structure of Oklahoma tornadic storms on 2 May 1979. I: Radar and satellite observations. *J. Atmos. Sci.* 40, 1740–1755.
  - A warm area forms inside a V of minimum Tb after tropopause penetration and moves with the 9–14 km winds, 10–20 m s⁻¹ slower.
  - A NASA 1983 aircraft IR study (NTRS 19830058463) reports that the IR cold point aligns with the low-level radar maximum when the updraft is intense and shifts downwind into anvil debris as the updraft weakens. Only the abstract was seen.
- **Setvák, M. et al. (2010)** Satellite-observed cold-ring-shaped features atop deep convective clouds. *Atmos. Res.* 97, 80–96. doi:10.1016/j.atmosres.2010.03.009. Tops reach 16–17 km per C-band radar. Coldest pixels form a ring; satellite CTH has significant errors for these storms.
- **JAS enhanced-V paper (search snippet; unverified):** coldest IR points nearly coincide with the radar OT, and the warmest spots lie 25–30 km downstream.
- **Cooney et al. 2021 (A17):** cold outflow can mimic OTs, so the coldest IR is not always the active core.
- **Liu, C., Zipser, E. J., Nesbitt, S. W. (2007)** Global Distribution of Tropical Deep Convection: Different Perspectives from TRMM Infrared and Radar Data. *J. Climate* 20, 489–503. doi:10.1175/JCLI4023.1
  - Only 35 % (57 %) of the area with TB11 ≤ 235 K (210 K) has PR-detected near-surface rain.
  - Only ~1 % of the TB11 ≤ 210 K area has 20 dBZ reaching 14 km.
  - The IR-top to 20 dBZ echo-top distance is smaller over land than over ocean.
  - Implication: cold cloud ≠ radar core at the field scale, through the non-raining anvil. This is relevant to the storm-scale measure.
- **Harjupa et al. 2017 (A3):** measured the cold-core to radar-maximum distance directly and attributed all of it to parallax (Japan, NW offset).
- **Wang, J. (2026) HailDeformer (A24):** parallax plus tilt; offset varies within the storm.
- **Gap:** no study found that reports, statistically, the fraction of the computed parallax that is visible as a cold-core to deep-echo offset, as in the manuscript's ~5 %.

## C. IR cloud-top height vs radar storm-top height (spaceborne radar)

- **Song, H.-J., Kim, S., Roh, S., Lee, H. (2020)** Difference Between Cloud Top Height and Storm Height for Heavy Rainfall Using TRMM Measurements. *JMSJ* 98(5), 901–914. doi:10.2151/jmsj.2020-044
  - Heavy rain (> 40 mm h⁻¹), Jun–Aug 2002–2013. Mean CTH−SH: **NW Pacific 5.5 km; Central Africa 3.9 km; USA 2.7 km; Korea/Japan ≈ 4.3 km** (computed from 12.6 − 8.3 km).
  - Share of cases with CTH−SH ≥ 4 km: 74 %, 59 %, 51 % and 24 %.
  - **No parallax correction** ("parallax correction between two sensors is not considered here"). CTH from VIRS 10.8 µm and ERA-Interim, constrained to SH ≤ CTH ≤ tropopause.
  - The manuscript's 3.2 km falls inside this range. Cite as consistent.
- **Liu, Zipser & Nesbitt 2007:** the IR-top minus 20 dBZ echo-top gap is a convective-intensity proxy, larger over ocean.
- **Kotarba, A. Z. (2026)** Evaluation of a moist-adiabat cloud-top height retrieval for parallax correction of deep convective clouds across Meteosat generations. *AMT* 19, 6193–6208. doi:10.5194/amt-19-6193-2026
  - Moist-adiabat CTH is 2.7 km (18 %) below CloudSat/CALIPSO 2B-GEOPROF-LIDAR. Mean displacement vector 32.5 km.
  - 84 % of pixels agree with the CLAAS-3-based correction (96.7 % within CLAAS uncertainty).
  - **No radar or surface validation of the parallax step.** Quote: independent verification against surface-based signatures "remains a valuable, though non-trivial, direction for future work".
  - Useful for the novelty argument.
- **Kumar, S., Silva, Y. (2019)** DPR-based Cb tower definition (20 dBZ at 12 km) over South and Southeast Asia. Context only; not verified in detail.
- A Himawari-8 IR CTH vs GPM comparison (*Infrared* (China) 43(9), 2022, researching.cn) reports r ≈ 0.9. Units and details are unclear.

## D. Effective height for parallax correction of precipitation (question on effective height)

- **D1. INSAT-3D Hydro-Estimator (operational).**
  - The SAC ISRO ATBD (*INSAT-3D ATBD Document*, May 2015, HE section; also Varma & Gairola, *ATBD Hydro-Estimator (Modified)*, SAC/EPSA/AOSG/SR/04/2015) states: "The parallax correction described in [Vicente et al. 2002] adjusts the horizontal location of the satellite pixel prior to rain rate computation, based on cloud height (using Tb and standard atmosphere) and satellite zenith angle."
  - **So INSAT rainfall already includes a cloud-top parallax correction.** I found no radar validation of that step.
  - The manuscript should mention this and avoid implying that no INSAT parallax correction exists.
- **Monsalve et al. 2026 (A9):** freezing level beats IR cloud top for passive microwave rain. The cloud-top correction *degraded* RMSE.
- **Wiltink et al. 2025 (A10):** 40–50 % of Hc is best for parallax-only correction of irradiance.
- **Virts & Koshak 2020 (A8):** optimal GLM emitter height is below the nominal cloud-top ellipsoid.
- **Fixed-height conventions:** 10 km in GREMLIN (A19); 14 km for OT matching (Sun et al. 2024; Bedka 2011 *Atmos. Res.* 99, 175–189; Dworak et al. 2012). Bluestein et al. 2019 used the radar echo top + 0.5 km.
- **NWC SAF CRR (EUMETRAIN training material):** a parallax shift is applied per precipitating pixel. Validation of the parallax step against radar is not documented in the sources found.
- **Not found:** a paper that tunes the parallax height for IR rainfall against spaceborne radar (DPR/PR). The manuscript's "effective height" analysis appears new for GEO IR vs DPR. Monsalve et al. is the closest analogue, for passive microwave vs MRMS.

## E. Wiltink et al. (2025): citation confirmed

Wiltink, J. I., Deneke, H., van Heerwaarden, C. C., and Meirink, J. F.: Evaluating parallax and shadow correction methods for global horizontal irradiance retrievals from Meteosat SEVIRI, *Atmos. Meas. Tech.*, 18, 3917–3936, https://doi.org/10.5194/amt-18-3917-2025, 2025. The preprint was egusphere-2024-4139.

Similar empirical-shift approaches:
- Harjupa et al. 2017: BT-regressed shift calibrated on radar.
- Zhang et al. 2026 ESSD: spline correction curves against WWLLN.
- Virts & Koshak 2020: optimal emitter height.
- Learned alignment (HailDeformer 2026; Cintineo 2020 implicit).
- Roebeling: LWP pattern-matching shift, cited in Bieliński 2020 as working for storms but failing for homogeneous fields.

## F. Other related items

- **Wang, C., Luo, Z. J., Huang, X. (2011)** Parallax correction in collocating CloudSat and MODIS observations: Method and application to convection study. *JGR* 116, D17201. doi:10.1029/2011JD016097
  - LEO–LEO, not GEO.
  - Correction lowers convective CTT, more so for taller clouds, and reduces CTT spread. It changes the buoyancy statistics most for tops above 10–12 km.
  - Notes that earlier "flat-top" selection, used to avoid parallax, biases samples toward mature or dissipating convection.
- **Mishra, A. K., Tomar, C. S., Kumar, G., Bhan, S. C. (2023)** Reconstructing radar reflectivity by integrating GPM and INSAT-3D observations for near real-time monitoring of convective storms over India. *Weather* 78, 224–227. doi:10.1002/wea.4443. r = 0.81 vs DPR. Parallax not mentioned in the abstract.
- **Mishra, A. K. et al. (2025)** Next-gen storm nowcasting: harnessing satellite-based radar reflectivity over India. *Theor. Appl. Climatol.* 156. doi:10.1007/s00704-025-05650-5.
- A 2026 Springer book chapter on the same INSAT3D+GPM topic: doi:10.1007/978-981-95-5409-6_11.
- **Cite all three as prior INSAT–DPR collocation work.** I did not check their full texts for parallax handling.
- **Reger, R. S. et al. (2026)** Source Speed as a Driver of GLM Location Offsets. *JGR* 131. doi:10.1029/2024JD042772. GLM–LMA offsets come from altitude-dependent optical propagation, residual parallax and source motion.
- **Piskala Gvoždíková, B. et al. (2026)** Lightning2EarthCARE. *ESSD Discuss.* doi:10.5194/essd-2026-470. In core-dominated storms, GEO lightning maxima align with EarthCARE CPR strong-convection signatures. Parallax handling not checked.
- **Brüning, S. et al. (2024)** *AMT* 17, 961–978. doi:10.5194/amt-17-961-2024. AI 3D cloud tomography from SEVIRI vs CloudSat. Lists parallax correction (Bieliński 2020) as future work.
- **Pfreundschuh, S. et al. (2022) Hydronn** *AMT* 15, 5033. GOES-16 vs GPM CMB over Brazil. **No mention of parallax** (full text grep) — a negative result.
- The GPROF-IR preprint (arXiv:2605.07167) could not be checked.
- **Satpy ParallaxCorrectionModifier (since v0.37, 2022):** documented as experimental, with no validation reported in the docs.
- **ISPRS 2026 (Ponte Lira et al.):** terrain parallax for MTG FRP. Not cloud parallax.

## Queries tried (and outcomes)

WebSearch:
1. parallax correction geostationary satellite validation radar GPM DPR (extended) → Bieliński, Monsalve, own repo
2. parallax correction SEVIRI convective cells radar comparison displacement km → Kotarba, Wiltink
3. INSAT-3D parallax correction → nothing INSAT-specific (negative)
4. Vicente Davenport Scofield 2002 … → IJRS citation, HE operational
5. Bieliński 2020 … correlation → metadata (numbers from the PDF)
6. Kalpana-1 OR INSAT parallax error Doppler weather radar → negative
7. overshooting top location offset radar reflectivity … (extended) → Bluestein 2019, enhanced-V, NASA 1983
8. parallax Himawari-8 GPM DPR convective core … → negative for direct match
9. GOES-16 ABI parallax correction MRMS … → negative
10. Roebeling Holleman 2009 … → JGR citation
11. Wang 2011 CloudSat MODIS parallax → found
12. GLM ABI parallax … → Virts & Koshak, FY-4A ESSD
13. Peterson 2023 "Mitigation…" → actually Virts & Koshak 2020
14. parallax correction height lower than cloud top precipitation … (extended) → nothing direct
15. NWC SAF parallax RDT CRR … → EUMETRAIN, no parallax validation
16. Mikuš Mahović 2013 … → no parallax or radar in the abstract
17. min IR Tb location radar core distance MCS … (extended) → negative
18. GPM DPR storm top vs IR CTH … → Song et al. 2020 JMSJ
19. Himawari-8 radar reflectivity DL GPM DPR parallax → negative
20. GREMLIN … parallax → 10 km fixed height
21. OT detection validation NEXRAD parallax GOES-16 (extended) → Khlopenkov, Cooney
22. Sandmæl 2019 … → not retrieved
23. "parallax correction" … "did not improve" (extended) → no direct hit
24. GK-2A AMI parallax radar → negative
25. FY-4A AGRI parallax radar → LMI only
26. Heymsfield 1983 …; Setvák 2010 … → found
27. satellite IR rainfall parallax … Meteosat (extended) → nothing quantitative
28. Pfreundschuh … parallax → Hydronn (no parallax)
29. satpy parallax Holl → docs only
30. Himawari parallax Indonesia radar → BMKG and Kyoto items
31. optimal shift satellite radar cross-correlation … (extended) → HailDeformer
32. CloudSat geostationary collocation parallax → Wang 2011, Kotarba
33. TRMM PR Meteosat/GOES parallax → negative
34. INSAT-3D/3DR DWR comparison …; INSAT-3DR GPM DPR … → Mishra et al.
35. Cintineo 2020 parallax → found (implicit learning)
36. FSS/object-based parallax … → negative
37. Himawari GPM DPR OT parallax Sun Zhuge … → BMKG abstract
38. Cooney 2021 parallax distance → abstract only
39. IR Tb min not collocated with radar core TRMM … → negative
40. "parallax" storm tilt upshear … → CIMSS GOES-11/12/13 example (OT 5 km SE vs 22 km W vs 12 km NW of Ardmore, depending on satellite)
41. parallax INSAT/Kalpana/Meteosat-8 India DWR (extended) → negative

OpenAlex API (reachable): searches on "parallax correction geostationary radar", "… satellite precipitation radar", "parallax Himawari radar", "parallax GOES radar convective", "parallax correction SEVIRI", "parallax FY-4", "parallax correction GPM", "parallax correction INSAT" (only the user's own Zenodo record, doi:10.5281/zenodo.23666957), "parallax error convective cloud radar", "parallax corrected brightness temperature radar reflectivity", "parallax shift satellite lightning", "parallax correction GK-2A", "parallax nowcasting satellite radar", "parallax geostationary GPM dual-frequency precipitation radar", "parallax correction Meteosat Indian Ocean", "… effective height", "… lightning imager MTG"; DOI lookups for abstracts.

Databases and sites:
- **Reachable:** OpenAlex (full); Copernicus (AMT/ESSD), arXiv, J-STAGE, NOAA IR, EUMETSAT CDN, mdpi-res CDN, Dryad.
- **Blocked (403):** mdpi.com HTML, journals.ametsoc.org, agupubs/Wiley, ScienceDirect, nwas.org.
- **Rate-limited (429):** Semantic Scholar API.
- **DNS failure:** pub.pg.edu.pl.
- Full texts read: Bieliński 2020, Bluestein et al. 2019, Radová & Seidl 2008, Harjupa et al. 2017, Sun et al. 2024, Cintineo et al. 2020, Hydronn 2022, and the INSAT-3D/HE ATBDs.

## Not verified / uncertain

- Whether Vicente et al. 2002 compared against radar.
- Dworak et al. 2012 and Cooney et al. 2021: parallax-height and match-radius details.
- Sandmæl et al. 2019.
- Whether Mishra et al. 2023/2025 parallax-correct INSAT before matching to DPR.
- The enhanced-V JAS "25–30 km downstream" figure (search snippet only).
- The Applied Energy 2025 tropical Meteosat-8 parallax/shadow irradiance paper (ScienceDirect S0306261925011870): authors and numbers not accessed.
