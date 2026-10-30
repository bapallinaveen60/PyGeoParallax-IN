---
title: 'PyGeoParallax-IN: cloud parallax correction for INSAT-3DR geostationary imagery'
tags:
  - Python
  - remote sensing
  - geostationary satellite
  - parallax correction
  - INSAT-3DR
  - Indian monsoon
authors:
  - name: Naveen Bapalli
    affiliation: 1
affiliations:
  - name: Independent researcher, India
    index: 1
date: 30 October 2026
bibliography: paper.bib
---

# Summary

Weather satellites in geostationary orbit photograph the same part of the Earth every few minutes from about 36,000 km above the equator. Their images are mapped onto the ground as if everything they see lay on the Earth's surface. A tall cloud, however, is seen along a slanted line of sight, so it appears displaced away from the point below the satellite. This *parallax* displacement grows with cloud height and with the viewing angle. India's operational imager, INSAT-3DR, sits at 74° E, close to the western edge of the country. It sees monsoon storms over the Himalaya and Northeast India, whose tops reach 15–17 km, displaced by 8–12 km, two to three image pixels.

PyGeoParallax-IN is a Python package that moves each cloudy pixel of an INSAT-3DR image back to where the cloud actually is. It reads ISRO's Level-1C files, estimates cloud-top height from the 10.8 µm channel, traces each line of sight to the cloud top on the WGS84 ellipsoid (with terrain if a digital elevation model is given), optionally applies a navigation correction measured from coastlines, and writes the corrected scene to NetCDF. A single command, `pygeoparallax l1c`, does this for a whole archive of files.

# Statement of need

Products built from INSAT-3DR imagery, such as rainfall estimates, cloud masks and machine-learning classifications of precipitation type, inherit the parallax displacement. Comparisons with radar or rain gauges then mix it with any real error. Correcting for parallax is routine for some other satellites: the GOES Hydro-Estimator has applied the correction of @vicente2002 operationally since 2001 [@scofield2003], and @bielinski2020 derived an exact solution on the ellipsoid. For INSAT, ISRO's Hydro-Estimator applies a parallax shift as an internal step of one rain product [@sac2015atbd], but no general, documented tool exists that corrects INSAT-3D/3DR imagery, quantifies the displacement or produces corrected and uncorrected datasets for comparison.

The target users are researchers and operational scientists who work with INSAT-3D/3DR imagery over South Asia: for satellite–radar comparisons, for rainfall and convection studies, and for training machine-learning models on satellite input. The package gives them corrected imagery, the displacement of every pixel, a flag for cells hidden behind tall clouds, and an uncorrected baseline on exactly the same grid, so that the effect of the correction can be measured rather than assumed.

# State of the field

Satpy [@raspaud2018; @satpy_parallax] offers an open-source parallax correction for gridded geostationary data. It assumes a spherical Earth, does not handle terrain and is marked experimental; its INSAT-3D/3DR reader is in beta. Two newer open-source codes, pyparallax [@pyparallax] and JParallaxCorrect [@tsujino2026], solve the geometry on the ellipsoid but handle neither terrain nor occlusion, and neither is tailored to INSAT data. None of them addresses INSAT-3DR's navigation error, which we found to be seasonal and, outside the monsoon, larger than the parallax itself.

We considered contributing to satpy instead of writing a separate package. Three needs argued against it: an exact ellipsoidal solver with a non-zero reference height and terrain, occlusion-aware regridding that can also return the image on its native L1C pixel grid, and an INSAT-specific navigation correction. Each changes satpy's data model or scope. PyGeoParallax-IN therefore builds on the same scientific Python stack (NumPy, SciPy, xarray, pyproj, Numba) [@harris2020; @virtanen2020; @hoyer2017; @pyproj; @lam2015] and uses satpy and pyorbital only as independent checks in its test suite.

# Software design

The package is organised as small, separately testable steps that mirror the physical problem:

- **Readers** (`pygeoparallax.ingest`) for INSAT-3DR L1C and L2B, GPM DPR, ERA5 and SRTM, returning xarray datasets.
- **Cloud-top height** (`cloudheight`) from brightness temperature through the AFGL tropical atmosphere or per-pixel ERA5 profiles. An *effective height* option lowers the correction height, because the infrared cloud top lies about 3 km above the rain-relevant level of deep convection.
- **Geometry** (`geometry`): the line of sight is intersected with an ellipsoid enlarged by the cloud height, then refined by Newton steps to below 1 mm. The solver has a vectorised NumPy reference and a parallel Numba kernel that corrects a full disk in 0.5 s. A terrain-aware variant iterates the ground height at the corrected position.
- **Resampling** (`resample`): corrected pixels land irregularly. When several fall in one cell, the highest cloud wins, because it hides the others from the satellite; small gaps are filled by inverse-distance weighting and cells never seen are flagged. The same scheme works on a regular lat/lon grid or, through a separable `NativeGrid`, back on the file's own Mercator pixel grid.
- **Navigation** (`navigation`): clear-sky coastlines are matched against a land mask to measure and apply a position correction.

The main trade-off was accuracy against speed. An exact ellipsoidal solver costs little once compiled with Numba, so we did not use the spherical or flat-Earth approximations. A second choice was to always produce the uncorrected baseline with the same resampling code (`correct=False`). Corrected and uncorrected datasets are then identical in clear sky, and any difference is due to the parallax step alone. The package has 64 tests, which compare the geometry with pyproj (below 1 mm), pyorbital (0.01°) and satpy (25 m). It also includes a command-line interface, a tutorial notebook and an API reference.

# Research impact statement

PyGeoParallax-IN was developed for, and used in, a validation of INSAT-3DR parallax correction against GPM Ku-band radar in 63 monsoon cases from 2018 to 2024, with a manuscript prepared for *Atmospheric Measurement Techniques*. That study used the package to show that the correction moves features only along the line of sight, to measure how much of the computed parallax a spaceborne radar can verify, and to characterise a seasonal westward bias of 7–20 km in INSAT-3DR L1C navigation. The package also produced the matched uncorrected and corrected training data for a precipitation-type U-Net experiment, using its native-grid correction. On 148 monsoon scenes the full pipeline ran without failure at 1.8 s per India scene. The validation scripts, case lists and archived releases [@pygeoparallax] make these analyses reproducible.

# AI usage disclosure

Generative AI was used throughout this project. Claude (Anthropic; Claude Opus 5.5, used through Claude Code in 2026) assisted with code generation, refactoring, test scaffolding, documentation, analysis scripts and drafting and copy-editing of this paper. The author reviewed, edited and validated all AI-assisted output, defined the research questions and made the core design decisions. Correctness was checked with the automated test suite, with comparisons against independent implementations (pyproj, pyorbital, satpy) and a synthetic storm with known parallax, and with end-to-end runs on real INSAT-3DR and GPM data.

# Acknowledgements

INSAT-3D and INSAT-3DR data were provided by MOSDAC, Space Applications Centre, ISRO; GPM data by NASA and JAXA through the NASA GES DISC; ERA5 by ECMWF through the Copernicus Climate Change Service; and SRTM data by NASA and USGS through OpenTopography. This work received no external funding.

# References
