"""Download Meteosat SEVIRI Indian Ocean (IODC) images for the validation cases and crop them to the case region.

A second geostationary view separates the two explanations left for the
invisible INSAT parallax (paper Section 6.2): a real offset of the cold cloud
top from the radar echo would appear in Meteosat too, an INSAT navigation
error would not. Meteosat-8 (41.5 E) was the prime IODC satellite until
31 May 2022, Meteosat-9 (45.5 E) from 1 June 2022; the Data Store collection
covers both.

For each case, the two IODC repeat cycles (15 min) whose scan of the storm
latitude brackets the GPM overpass are downloaded from the EUMETSAT Data Store
(collection ``EO:EUM:DAT:MSG:HRSEVIRI-IODC``, native format). Each is cropped
with satpy to the case region (plus a margin), keeping the 10.8 um channel,
latitude, longitude and the acquisition time of each line, and written as a
small NetCDF file. The full-disk file is deleted unless ``--keep`` is given.

Credentials: register at https://eoportal.eumetsat.int, get a consumer key and
secret at https://api.eumetsat.int/api-key and store them once with
``eumdac set-credentials <key> <secret>``. This script reads them from the
file that command writes; it never prints them.

Usage:
    python scripts/download_seviri_iodc.py --dry-run               # list what would be downloaded
    python scripts/download_seviri_iodc.py --regions northeast himalaya
    python scripts/download_seviri_iodc.py --cases northeast_20240818
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import run_all_cases  # noqa: E402

COLLECTION = "EO:EUM:DAT:MSG:HRSEVIRI-IODC"
DEFAULT_OUT = Path("D:/Projects/@GeoVision/Insat_data/datasets/seviri_iodc")
MARGIN_DEG = 1.5
# SEVIRI scans from south to north; the Earth disc (about 81 S to 81 N) takes about 12 min of the 15 min cycle.
SCAN_MIN, SCAN_LAT = 12.0, (-81.0, 81.0)


def token():
    import eumdac
    from eumdac.config import get_credentials_path

    path = get_credentials_path()
    if not path.exists():
        raise SystemExit(f"no EUMETSAT credentials at {path}: run `eumdac set-credentials <key> <secret>` once "
                         "(key and secret from https://api.eumetsat.int/api-key)")
    key, secret = path.read_text().strip().split(",", 1)
    return eumdac.AccessToken((key, secret))


def storm_time(product_start, lat):
    """Approximate time at which SEVIRI scans ``lat`` in the cycle starting at ``product_start``."""
    frac = (lat - SCAN_LAT[0]) / (SCAN_LAT[1] - SCAN_LAT[0])
    return product_start + timedelta(minutes=SCAN_MIN * frac)


def bracketing(products, t_target, lat):
    """The last cycle that scans ``lat`` before ``t_target`` and the first after it."""
    timed = sorted(((storm_time(p.sensing_start.replace(tzinfo=None), lat), p) for p in products), key=lambda x: x[0])
    before = [x for x in timed if x[0] <= t_target]
    after = [x for x in timed if x[0] > t_target]
    return ([before[-1]] if before else []) + ([after[0]] if after else [])


def fetch_native(product, workdir):
    """Download the product's native (.nat) file into ``workdir`` and return its path."""
    entries = list(getattr(product, "entries", []) or [])
    nat = [e for e in entries if e.lower().endswith(".nat")]
    if nat:
        dst = Path(workdir) / Path(nat[0]).name
        with product.open(entry=nat[0]) as src, open(dst, "wb") as out:
            shutil.copyfileobj(src, out)
        return dst
    with product.open() as src:                     # whole product (a zip)
        dst = Path(workdir) / Path(src.name).name
        with open(dst, "wb") as out:
            shutil.copyfileobj(src, out)
    if zipfile.is_zipfile(dst):
        with zipfile.ZipFile(dst) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".nat"))
            z.extract(name, workdir)
            return Path(workdir) / name
    return dst


def crop_to_netcdf(nat_path, box, out_path):
    """Crop a SEVIRI native file to ``box`` (+ margin) with satpy; keep IR_108, lat, lon and line times."""
    import xarray as xr
    from satpy import Scene

    lat_min, lat_max, lon_min, lon_max = box
    scn = Scene(reader="seviri_l1b_native", filenames=[str(nat_path)])
    scn.load(["IR_108"])
    sub = scn.crop(ll_bbox=(lon_min - MARGIN_DEG, lat_min - MARGIN_DEG, lon_max + MARGIN_DEG, lat_max + MARGIN_DEG))
    da = sub["IR_108"]
    lons, lats = da.attrs["area"].get_lonlats()
    orbit = da.attrs.get("orbital_parameters", {})
    acq = da.coords["acq_time"].values if "acq_time" in da.coords else np.full(da.shape[0], np.datetime64("NaT"))
    ds = xr.Dataset(
        {"TIR1": (("y", "x"), da.values.astype(np.float32), {"units": "K", "long_name": "SEVIRI IR 10.8 um brightness temperature"}),
         "acq_time": (("y",), acq.astype("datetime64[ns]"))},
        coords={"lat": (("y", "x"), lats.astype(np.float64)), "lon": (("y", "x"), lons.astype(np.float64))},
        attrs={"platform_name": str(da.attrs.get("platform_name", "")),
               "sub_satellite_longitude": float(orbit.get("satellite_nominal_longitude", np.nan)),
               "satellite_actual_longitude": float(orbit.get("satellite_actual_longitude", np.nan)),
               "start_time": str(da.attrs.get("start_time", "")), "end_time": str(da.attrs.get("end_time", "")),
               "source_file": Path(nat_path).name},
    )
    lat_ok = np.isfinite(lats) & (np.abs(lats) <= 90)
    ds["lat"] = ds["lat"].where(lat_ok)
    ds["lon"] = ds["lon"].where(lat_ok)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(out_path, encoding={"TIR1": {"zlib": True}, "lat": {"zlib": True}, "lon": {"zlib": True}})
    return out_path


def case_targets(cases):
    """(case, region box, storm latitude, GPM time) for each case."""
    out = []
    for case in cases:
        d = json.loads((Path("05_validation/gpm_colocation") / f"{case}.json").read_text())
        box = run_all_cases.REGION_BOX[case.split("_")[0]]
        t = datetime.fromisoformat(d["gpm_time_at_convection"])
        out.append((case, box, (box[0] + box[1]) / 2, t))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="folder for the cropped files (one sub-folder per case)")
    ap.add_argument("--cases", nargs="+", help="only these cases")
    ap.add_argument("--regions", nargs="+", choices=["south", "central", "himalaya", "northeast"],
                    help="only cases in these regions")
    ap.add_argument("--dry-run", action="store_true", help="list the products without downloading")
    ap.add_argument("--keep", action="store_true", help="keep the full-disk .nat files next to the crops")
    args = ap.parse_args(argv)

    table = pd.read_csv("05_validation/gpm_colocation/all_cases.csv")
    usable = table[(table.nav == "no_nav") & table.status.str.startswith("usable")]["case"].tolist()
    cases = args.cases or [c for c in usable if not args.regions or c.split("_")[0] in args.regions]

    import eumdac

    store = eumdac.DataStore(token())
    coll = store.get_collection(COLLECTION)
    out = Path(args.out)
    for case, box, lat, t in case_targets(cases):
        products = list(coll.search(dtstart=t - timedelta(minutes=35), dtend=t + timedelta(minutes=20)))
        chosen = bracketing(products, t, lat)
        if not chosen:
            print(f"{case:22s} GPM {t:%Y-%m-%d %H:%M}  no IODC cycle found", flush=True)
            continue
        for t_scan, p in chosen:
            name = f"{case}_{t_scan:%Y%m%dT%H%M%S}.nc"
            dst = out / case / name
            tag = f"{case:22s} GPM {t:%H:%M:%S}  cycle {p.sensing_start:%H:%M}  storm scanned ~{t_scan:%H:%M:%S}"
            if dst.exists():
                print(f"{tag}  exists", flush=True)
                continue
            if args.dry_run:
                print(f"{tag}  {p}", flush=True)
                continue
            with tempfile.TemporaryDirectory(dir=out if out.exists() else None) as tmp:
                nat = fetch_native(p, tmp)
                crop_to_netcdf(nat, box, dst)
                if args.keep:
                    shutil.copy2(nat, out / case / nat.name)
            print(f"{tag}  -> {dst}", flush=True)


if __name__ == "__main__":
    main()
