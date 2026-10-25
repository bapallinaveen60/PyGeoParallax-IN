"""Readers for INSAT-3DR L1C/CTH (HDF5), ERA5 (NetCDF/GRIB), GPM 2A.DPR and SRTM."""

from .era5 import read_era5_profiles
from .gpm import CONVECTIVE, NO_RAIN, OTHER, STRATIFORM, read_gpm_2a
from .insat import read_insat_l1c, to_standard_scene
from .insat_ctp import read_insat_csbt, read_insat_ctp

__all__ = [
    "CONVECTIVE",
    "NO_RAIN",
    "OTHER",
    "STRATIFORM",
    "read_era5_profiles",
    "read_gpm_2a",
    "read_insat_csbt",
    "read_insat_ctp",
    "read_insat_l1c",
    "to_standard_scene",
]
