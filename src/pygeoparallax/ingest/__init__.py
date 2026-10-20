"""Readers for INSAT-3DR L1C/CTH (HDF5), ERA5 (NetCDF/GRIB), GPM 2A.DPR and SRTM."""

from .gpm import CONVECTIVE, NO_RAIN, OTHER, STRATIFORM, read_gpm_2a
from .insat import read_insat_l1c, to_standard_scene

__all__ = [
    "CONVECTIVE",
    "NO_RAIN",
    "OTHER",
    "STRATIFORM",
    "read_gpm_2a",
    "read_insat_l1c",
    "to_standard_scene",
]
