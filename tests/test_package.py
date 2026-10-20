import importlib

import pygeoparallax


def test_version():
    assert pygeoparallax.__version__


def test_subpackages_import():
    for name in ("geometry", "ingest", "resample", "validation"):
        importlib.import_module(f"pygeoparallax.{name}")
