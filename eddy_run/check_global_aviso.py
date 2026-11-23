"""Check daily local AVISO delayed-time files for the 2024 global experiment.

Inventory only: no NetCDF data are loaded or modified.
"""
from __future__ import annotations
import argparse
from datetime import date, timedelta
from pathlib import Path

DEFAULT_ROOT = Path("/data/rd_exchange/cregnier/Rappat/SEALEVEL_GLO_PHY_L4_MY_008_047/cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D_202411")


def dates(start, end):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--inspect-samples", action="store_true", help="Open January/July 2024 and January 2025 sample NetCDF files to inspect ADT and coordinates")
    parser.add_argument("--start", type=date.fromisoformat, default=date(2024, 1, 3))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2025, 1, 22))
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must not precede --start")
    missing, ambiguous, found = [], [], 0
    for day in dates(args.start, args.end):
        directory = args.source_root / f"{day:%Y}" / f"{day:%m}"
        candidates = sorted(directory.glob(f"dt_global_allsat_phy_l4_{day:%Y%m%d}_*.nc"))
        if not candidates:
            missing.append(day.isoformat())
        elif len(candidates) > 1:
            ambiguous.append((day.isoformat(), [str(x) for x in candidates]))
        else:
            found += 1
    print(f"AVISO root: {args.source_root}")
    print(f"Date range: {args.start} through {args.end} (inclusive)")
    print(f"Found: {found}; missing: {len(missing)}; ambiguous: {len(ambiguous)}")
    for day in missing:
        print(f"MISSING {day}")
    for day, paths in ambiguous:
        print(f"AMBIGUOUS {day}: {'; '.join(paths)}")
    if missing or ambiguous:
        raise SystemExit(1)
    print("All daily paths present. ADT variable, grid, masks, and file integrity NOT yet validated.")
    if args.inspect_samples:
        import numpy as np
        import xarray as xr
        samples = (date(2024, 1, 3), date(2024, 7, 3), date(2025, 1, 22))
        for day in samples:
            if not args.start <= day <= args.end:
                continue
            matches = sorted((args.source_root / f"{day:%Y}" / f"{day:%m}").glob(
                f"dt_global_allsat_phy_l4_{day:%Y%m%d}_*.nc"))
            if len(matches) != 1:
                raise ValueError(f"{day}: expected exactly one file, got {len(matches)}")
            with xr.open_dataset(matches[0]) as ds:
                if "adt" not in ds:
                    raise ValueError(f"{matches[0]}: missing adt; available: {list(ds.data_vars)}")
                da = ds["adt"]
                if not {"longitude", "latitude"}.issubset(da.dims):
                    raise ValueError(f"{matches[0]}: unexpected ADT dimensions {da.dims}")
                lon = np.asarray(ds.longitude.values)
                lat = np.asarray(ds.latitude.values)
                if lon.ndim != 1 or lat.ndim != 1 or not (np.diff(lon) > 0).all() or not (np.diff(lat) > 0).all():
                    raise ValueError(f"{matches[0]}: longitude/latitude must be strictly increasing 1D coordinates")
                if float(lat.min()) > -70 or float(lat.max()) < 70:
                    raise ValueError(f"{matches[0]}: latitude does not cover 70S to 70N")
                if float(lon.max() - lon.min()) < 359:
                    raise ValueError(f"{matches[0]}: longitude does not cover the globe")
                if "time" in ds.coords:
                    observed = np.asarray(ds.time.values).astype("datetime64[D]")
                    if np.datetime64(day.isoformat()) not in observed:
                        raise ValueError(f"{matches[0]}: time coordinate does not contain {day}")
                print(f"SAMPLE {day}: ADT dims={da.dims}, shape={da.shape}, units={da.attrs.get('units', 'UNKNOWN')}, "
                      f"lon=[{lon.min():g},{lon.max():g}], lat=[{lat.min():g},{lat.max():g}]")
        print("Sample metadata validated. Full daily-file integrity and mask still require checking.")


if __name__ == "__main__":
    main()
