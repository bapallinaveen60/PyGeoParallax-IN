"""PyGeoParallax-IN: cloud parallax correction for INSAT-3DR imagery over India."""

__version__ = "0.2.1"

from .pipeline import correct_scene  # noqa: E402

__all__ = ["correct_scene", "__version__"]
