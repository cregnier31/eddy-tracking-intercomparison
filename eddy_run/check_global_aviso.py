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


if __name__ == "__main__":
    main()
