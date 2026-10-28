"""A satellite product's own pixel grid, e.g. the INSAT-3DR L1C Mercator grid.

Correcting on the native grid keeps the output pixel-for-pixel aligned with
the input: same shape, same pixel centres. This is what a model trained on L1C
patches needs (corrected and uncorrected inputs on identical pixels).

The grid must be separable and regular: latitude depends only on the row and
longitude only on the column, with constant steps in Mercator northing
(ellipsoidal WGS84, as in L1C products) or, failing that, in latitude itself.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .grid import Grid

#: WGS84 first eccentricity.
WGS84_E = 0.0818191908426


def mercator_y(lat):
    """Ellipsoidal (WGS84) Mercator northing for a unit equatorial radius."""
    phi = np.radians(np.asarray(lat, float))
    es = WGS84_E * np.sin(phi)
    return np.log(np.tan(np.pi / 4 + phi / 2) * ((1 - es) / (1 + es)) ** (WGS84_E / 2))


def mercator_lat(y, iterations=6):
    """Inverse of :func:`mercator_y` [degrees]."""
    t = np.exp(-np.asarray(y, float))
    phi = np.pi / 2 - 2 * np.arctan(t)
    for _ in range(iterations):
        es = WGS84_E * np.sin(phi)
        phi = np.pi / 2 - 2 * np.arctan(t * ((1 - es) / (1 + es)) ** (WGS84_E / 2))
    return np.degrees(phi)


@dataclass(frozen=True)
class NativeGrid:
    """A separable pixel grid: ``v(row) = v0 + row * dv`` and ``lon(col) = lon0 + col * dlon``.

    ``v`` is Mercator northing (``kind="mercator"``) or latitude
    (``kind="latlon"``). Rows and columns index pixel centres.
    """

    v0: float
    dv: float
    lon0: float
    dlon: float
    shape: tuple[int, int]
    kind: str = "mercator"

    @classmethod
    def from_coords(cls, lat_1d, lon_1d, tolerance=0.01):
        """Fit the grid to the pixel-centre latitudes of the rows and longitudes of the columns.

        Raises ``ValueError`` if neither Mercator northing nor latitude is
        regular to within ``tolerance`` pixels.
        """
        lat_1d = np.asarray(lat_1d, float)
        lon_1d = np.asarray(lon_1d, float)
        if lat_1d.size < 2 or lon_1d.size < 2:
            raise ValueError("a native grid needs at least 2 rows and 2 columns")
        shape = (lat_1d.size, lon_1d.size)
        col = np.arange(lon_1d.size)
        dlon, lon0 = np.polyfit(col, lon_1d, 1)
        if np.max(np.abs(lon0 + col * dlon - lon_1d)) / abs(dlon) > tolerance:
            raise ValueError("longitudes are not evenly spaced")
        row = np.arange(lat_1d.size)
        for kind, v in (("mercator", mercator_y(lat_1d)), ("latlon", lat_1d)):
            dv, v0 = np.polyfit(row, v, 1)
            if np.max(np.abs(v0 + row * dv - v)) / abs(dv) <= tolerance:
                return cls(float(v0), float(dv), float(lon0), float(dlon), shape, kind)
        raise ValueError("latitudes are evenly spaced neither in Mercator northing nor in degrees")

    @classmethod
    def from_2d(cls, lat, lon, tolerance=0.01):
        """Like :meth:`from_coords`, from 2-D ``lat``/``lon`` arrays (checked to be separable)."""
        lat = np.asarray(lat, float)
        lon = np.asarray(lon, float)
        if not (np.allclose(lat, lat[:, :1]) and np.allclose(lon, lon[:1, :])):
            raise ValueError("lat must vary along rows only and lon along columns only; "
                             "pass the grid explicitly if the positions were shifted")
        return cls.from_coords(lat[:, 0], lon[0, :], tolerance)

    @property
    def lats(self) -> np.ndarray:
        """Pixel-centre latitude of each row."""
        v = self.v0 + np.arange(self.shape[0]) * self.dv
        return mercator_lat(v) if self.kind == "mercator" else v

    @property
    def lons(self) -> np.ndarray:
        """Pixel-centre longitude of each column."""
        return self.lon0 + np.arange(self.shape[1]) * self.dlon

    def fractional_index(self, lat, lon):
        """Row and column of each position, as floats; pixel centres are whole numbers."""
        v = mercator_y(lat) if self.kind == "mercator" else np.asarray(lat, float)
        return (v - self.v0) / self.dv, (np.asarray(lon, float) - self.lon0) / self.dlon

    def index_space(self):
        """Positions -> ``(pseudo_lat, pseudo_lon)`` and a :class:`Grid` with one cell per pixel.

        Returns ``(to_index, grid)``: ``to_index(lat, lon)`` maps positions so
        that ``grid.cell_index`` finds the pixel containing them. This lets the
        bucket resampler work on the native grid unchanged.
        """
        grid = Grid(lat_min=-float(self.shape[0]), lat_max=0.0, lon_min=0.0, lon_max=float(self.shape[1]), res=1.0)

        def to_index(lat, lon):
            row, col = self.fractional_index(lat, lon)
            return -(row + 0.5), col + 0.5

        return to_index, grid
