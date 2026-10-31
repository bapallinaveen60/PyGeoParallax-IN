# PyGeoParallax-IN documentation

PyGeoParallax-IN corrects INSAT-3DR geostationary imagery for cloud parallax. The satellite, at 74° E, sees tall clouds along a slanted line of sight, so they appear displaced away from it: by about 4 km over South India and 8–12 km over the Himalaya and Northeast India for deep convection. The package moves each cloudy pixel back to where the cloud really is, and writes corrected and uncorrected images on the same grid so that the effect of the correction can be measured.

This documentation covers version 0.4.1. A PDF version of all pages can be built with `python docs/build_manual.py` (see [Development](development.md)).

## Where to start

| If you want to | Read |
| :--- | :--- |
| install the package and check that it works | [Installation](installation.md) |
| see the correction work in five minutes, with no data | [Quickstart](quickstart.md) |
| correct INSAT-3DR files from the command line | [Command-line reference](cli.md) |
| use the package from Python | [Python API](python_api.md) |
| understand what is in the output files | [Output files](outputs.md) |
| understand the method and its limits | [Concepts and algorithms](concepts.md) |
| find and download the input data | [Input data](data.md) |
| reproduce the GPM validation of the paper | [GPM validation](validation.md) |
| reproduce the U-Net experiment | [U-Net A/B experiment](unet.md) |
| fix a problem | [Troubleshooting](troubleshooting.md) |
| contribute, test or release | [Development](development.md) and [CONTRIBUTING.md](../CONTRIBUTING.md) |

## The pages

**Using the tool**

1. [Installation](installation.md): requirements, install options, checking the install.
2. [Quickstart](quickstart.md): the demo, the Colab notebook and a first real file.
3. [Command-line reference](cli.md): `demo`, `l1c`, `correct`, `batch` and `navigation`, with every option.
4. [Python API](python_api.md): a guided tour of every module, with working examples.
5. [Output files](outputs.md): variables, flags and attributes of the corrected NetCDF files.
6. [Troubleshooting](troubleshooting.md): common problems and questions.

**Background**

7. [Concepts and algorithms](concepts.md): parallax geometry, cloud-top height, the ray-tracing solver, terrain, occlusion-aware resampling, the native grid, effective height, navigation correction and known limitations.
8. [Input data](data.md): INSAT-3DR L1C and L2B, GPM DPR, ERA5, SRTM and Natural Earth: contents, quirks and where to get them.

**Research workflows**

9. [GPM validation](validation.md): the scripts, their order and the results of the 63-case validation.
10. [U-Net A/B experiment](unet.md): retraining a precipitation-type U-Net on uncorrected and corrected input.
11. [Development](development.md): repository structure, tests, continuous integration, releases and building the manuscripts.

## At a glance

```bash
pip install git+https://github.com/bapallinaveen60/PyGeoParallax-IN.git
pygeoparallax demo                                              # self-test, no data needed
pygeoparallax l1c "3RIMG_*_L1C_SGP_V01R00.h5" -o corrected/      # correct L1C files
```

## Citing

If you use PyGeoParallax-IN, please cite the software (concept DOI [10.5281/zenodo.23666957](https://doi.org/10.5281/zenodo.23666957), which always resolves to the latest version) and the version you used; see [CITATION.cff](../CITATION.cff).

## Help

Questions and bug reports: [GitHub issues](https://github.com/bapallinaveen60/PyGeoParallax-IN/issues). The source code, changelog and licence (MIT) are in the [repository](https://github.com/bapallinaveen60/PyGeoParallax-IN).
