"""Colocation with GPM-DPR / IMD DWR, alignment statistics and sensitivity analysis."""

from .colocate import nearest_time, points_to_grid, range_mask
from .metrics import best_displacement, compare, iou, mutual_information, pearson, subcell_displacement
from .regions import REGIONS, region_mask, regional_stats
from .sensitivity import bias_sweep, monte_carlo_shift

__all__ = [
    "REGIONS",
    "best_displacement",
    "bias_sweep",
    "compare",
    "iou",
    "monte_carlo_shift",
    "mutual_information",
    "nearest_time",
    "pearson",
    "points_to_grid",
    "range_mask",
    "region_mask",
    "regional_stats",
    "subcell_displacement",
]
