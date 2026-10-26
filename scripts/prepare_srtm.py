"""Build the South Asia SRTM elevation grid used for terrain-aware correction.

Reads the SRTM GeoTIFF tiles (``read_srtm``), block-averages them to
``--res`` degrees over ``--bbox`` and writes one NetCDF that
``pygeoparallax correct --dem`` and ``run_validation_case.py --dem`` read.

Usage:
    python scripts/prepare_srtm.py --tiles D:/Projects/@GeoVision/Insat_data/SRTM_DEM \
        --out 02_standardized_grid/srtm_0p01deg.nc
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pygeoparallax.ingest import read_srtm


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--tiles", required=True, help="folder, glob or files of SRTM GeoTIFF tiles")
    ap.add_argument("--out", default="02_standardized_grid/srtm_0p01deg.nc")
    ap.add_argument("--res", type=float, default=0.01)
    ap.add_argument("--bbox", nargs=4, type=float, default=(6.0, 38.0, 68.0, 98.0),
                    metavar=("LAT_MIN", "LAT_MAX", "LON_MIN", "LON_MAX"))
    args = ap.parse_args(argv)
    dem = read_srtm(args.tiles, bbox=tuple(args.bbox), res=args.res)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    dem.to_netcdf(out, encoding={"elevation": {"zlib": True, "complevel": 4}})
    e = dem["elevation"]
    print(f"wrote {out}: {e.shape[0]} x {e.shape[1]} cells, max {float(e.max()):.0f} m, "
          f"{float(e.isnull().mean()) * 100:.1f}% without data")


if __name__ == "__main__":
    main()
