"""Download ERA5 pressure-level temperature and geopotential for each validation case.

For every case folder under ``--base`` (named ``<region>_<YYYYMMDD>``), this
requests the ERA5 hour nearest the INSAT case scan, over the case's region box
padded by 1 degree, and saves it in the folder as ``era5_pl_<YYYYMMDDHH>.nc``.
Folders that already have the file are skipped.

Needs a Copernicus CDS account and ``~/.cdsapirc``:

    url: https://cds.climate.copernicus.eu/api
    key: <your key>

Usage:
    python scripts/download_era5.py --base D:/Projects/@GeoVision/Insat_data/datasets/validation
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_all_cases import REGION_BOX, case_scan  # noqa: E402

#: 1000-50 hPa: the troposphere and the tropical tropopause (~100 hPa) with room above.
LEVELS = [1000, 975, 950, 925, 900, 875, 850, 825, 800, 775, 750, 700, 650, 600, 550,
          500, 450, 400, 350, 300, 250, 225, 200, 175, 150, 125, 100, 70, 50]
#: Minutes after the scan start when INSAT reaches the middle of India (~20-25N).
SCAN_OFFSET_MIN = 10


def era5_hour(scan):
    """Nearest whole hour to the case scan, e.g. ``18AUG2024_2215`` -> 2024-08-18 22:00."""
    t = datetime.strptime(scan, "%d%b%Y_%H%M") + timedelta(minutes=SCAN_OFFSET_MIN)
    return (t + timedelta(minutes=30)).replace(minute=0, second=0, microsecond=0)


def request(hour, box, pad=1.0):
    lat0, lat1, lon0, lon1 = box
    return {
        "product_type": ["reanalysis"],
        "variable": ["temperature", "geopotential"],
        "pressure_level": [str(p) for p in LEVELS],
        "year": [f"{hour:%Y}"], "month": [f"{hour:%m}"], "day": [f"{hour:%d}"], "time": [f"{hour:%H}:00"],
        "area": [lat1 + pad, lon0 - pad, lat0 - pad, lon1 + pad],  # N, W, S, E
        "data_format": "netcdf",
        "download_format": "unarchived",
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--only", nargs="+", help="only these case folders")
    ap.add_argument("--dry-run", action="store_true", help="list the requests without downloading")
    args = ap.parse_args(argv)

    client = None
    for folder in sorted(p for p in Path(args.base).iterdir() if p.is_dir()):
        region = folder.name.split("_")[0]
        if region not in REGION_BOX or (args.only and folder.name not in args.only):
            continue
        scan = case_scan(folder)
        if scan is None:
            print(f"{folder.name}: no case scan, skipped")
            continue
        hour = era5_hour(scan)
        out = folder / f"era5_pl_{hour:%Y%m%d%H}.nc"
        if out.exists():
            print(f"{folder.name}: {out.name} exists")
            continue
        print(f"{folder.name}: scan {scan} -> ERA5 {hour:%Y-%m-%d %H}:00", flush=True)
        if args.dry_run:
            continue
        if client is None:
            import cdsapi

            client = cdsapi.Client(quiet=True)
        tmp = out.with_suffix(".part")
        client.retrieve("reanalysis-era5-pressure-levels", request(hour, REGION_BOX[region]), str(tmp))
        tmp.replace(out)
        print(f"  wrote {out.name} ({out.stat().st_size / 1e6:.1f} MB)", flush=True)


if __name__ == "__main__":
    main()
