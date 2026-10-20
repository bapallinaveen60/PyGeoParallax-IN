"""Regular latitude/longitude target grid."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Grid:
    """A regular lat/lon grid; rows run north to south, columns west to east.

    The bounds are the outer cell edges in degrees, and ``res`` is the cell size.
    """

    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    res: float

    @property
    def shape(self) -> tuple[int, int]:
        return (
            int(round((self.lat_max - self.lat_min) / self.res)),
            int(round((self.lon_max - self.lon_min) / self.res)),
        )

    @property
    def lats(self) -> np.ndarray:
        """Cell-centre latitudes, north to south."""
        return self.lat_max - (np.arange(self.shape[0]) + 0.5) * self.res

    @property
    def lons(self) -> np.ndarray:
        """Cell-centre longitudes, west to east."""
        return self.lon_min + (np.arange(self.shape[1]) + 0.5) * self.res

    def cell_index(self, lat, lon):
        """Row and column of the cell containing each point, and an in-domain mask.

        Points outside the grid, or with NaN coordinates, get ``valid=False``
        and row/col 0.
        """
        lat = np.asarray(lat, float)
        lon = np.asarray(lon, float)
        with np.errstate(invalid="ignore"):
            row = np.floor((self.lat_max - lat) / self.res)
            col = np.floor((lon - self.lon_min) / self.res)
            valid = (row >= 0) & (row < self.shape[0]) & (col >= 0) & (col < self.shape[1])
        row = np.where(valid, row, 0).astype(np.intp)
        col = np.where(valid, col, 0).astype(np.intp)
        return row, col, valid


#: Project default: 0.04 degree grid over the Indian subcontinent (1000 x 1000 cells).
SOUTH_ASIA_0P04 = Grid(lat_min=0.0, lat_max=40.0, lon_min=60.0, lon_max=100.0, res=0.04)
