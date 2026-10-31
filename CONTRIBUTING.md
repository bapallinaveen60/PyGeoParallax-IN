# Contributing to PyGeoParallax-IN

Thank you for your interest. Bug reports, questions, data-format reports and code contributions are all welcome.

## Reporting a problem or asking a question

Open an issue at <https://github.com/bapallinaveen60/PyGeoParallax-IN/issues>. Please include:

- what you ran (the command or a short code snippet);
- the input file name (for example `3RIMG_01AUG2023_1815_L1C_SGP_V01R00.h5`), or a description of the data if you cannot share it;
- the full error message, and the output of `pygeoparallax --version` and `python --version`.

INSAT-3DR products change format occasionally. If a reader fails on a new file, an issue with the file name and the error is very helpful.

## Contributing code

1. Fork the repository and create a branch from `main`.
2. Set up a development environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -e ".[geo,download,plot,dev]"
   ```
3. Make your change. Follow the style of the surrounding code: NumPy-style docstrings with units, and small functions that can be tested on their own.
4. Add or update tests in `tests/`, and run the whole suite with `pytest`. Tests run on synthetic data and need no downloads.
5. Describe the change in `CHANGELOG.md` under an "unreleased" heading.
6. Open a pull request against `main`. The test workflow runs on Ubuntu (Python 3.10 and 3.12) and Windows (Python 3.12) and must pass.

New features that change results (the solver, cloud-top height, resampling or navigation) should come with a test against an independent reference or a synthetic case with a known answer.

## Support and maintenance

PyGeoParallax-IN is maintained by Naveen Bapalli. Issues are usually answered within a week. Releases follow semantic versioning and are archived on Zenodo (concept DOI [10.5281/zenodo.23666957](https://doi.org/10.5281/zenodo.23666957)); changes are listed in [CHANGELOG.md](CHANGELOG.md).

## Code of conduct

Be respectful and constructive. Harassment or personal attacks are not tolerated in issues, pull requests or any other project space.
