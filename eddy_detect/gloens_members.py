"""Detect daily GLOENS eddies separately for each ensemble member.

Run one member first, then extend to all 50. Each member uses the same
regular grid and detection parameters as the ensemble-mean workflow.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np

from eddy_detect.gloens_grid import CurvilinearToRegular, regularize_ssh
from eddy_load.gloens_mean import DEFAULT_ENDPOINT, open_gloens_store


def member_indices(n_members, first_member=1, last_member=None):
    """Return zero-based indices for inclusive one-based member numbers."""
    last_member = n_members if last_member is None else last_member
    if not 1 <= first_member <= last_member <= n_members:
        raise ValueError(
            f"Member range must satisfy 1 <= first <= last <= {n_members}"
        )
    return range(first_member - 1, last_member)


def detection_paths(data_dir, member_number, date):
    output = Path(data_dir) / "GLOENS" / "MEMBERS" / f"member_{member_number:03d}" / "DETECT"
    return (
        output / f"Anticyclonic_GLOENS_{date}.nc",
        output / f"Cyclonic_GLOENS_{date}.nc",
    )


def detect_members(
    store, data_dir, lon_min=-80, lon_max=0, lat_min=20, lat_max=65,
    resolution=0.25, first_day=0, last_day=28, first_member=1,
    last_member=1, endpoint=DEFAULT_ENDPOINT, anonymous=True,
):
    """Detect GLOENS eddies per member and day; resume completed days.

    The source store and spatial triangulation are shared within the job.
    Temporary regular-grid files are removed after each detection.
    """
    if resolution <= 0 or lon_max <= lon_min or lat_max <= lat_min:
        raise ValueError("Invalid regular-grid bounds or resolution")
    lon = np.arange(lon_min, lon_max + resolution * 0.25, resolution)
    lat = np.arange(lat_min, lat_max + resolution * 0.25, resolution)

    # Import detection dependencies only when actually running detection.
    from eddy_detect.my_functions import compute_eddy
    from eddy_detect.namelist_detect import (
        SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX, AMP_MIN, WAVELENGTH, ORDER_FILTER,
    )

    with open_gloens_store(store, endpoint=endpoint, anonymous=anonymous) as ds:
        if "zos" not in ds or not {"time", "ens", "y", "x"}.issubset(ds["zos"].dims):
            raise ValueError("Expected zos with dimensions (time, ens, y, x)")
        n_members = ds.sizes["ens"]
        if n_members != 50:
            raise ValueError(f"Expected 50 members; found {n_members}")
        stop = ds.sizes["time"] if last_day is None else min(last_day, ds.sizes["time"])
        if not 0 <= first_day < stop:
            raise ValueError("Invalid forecast day range")

        source_lon = ds["longitude"].values
        source_lat = ds["latitude"].values
        interpolator = CurvilinearToRegular(source_lon, source_lat, lon, lat)

        for member_idx in member_indices(n_members, first_member, last_member):
            member_number = member_idx + 1
            for lead in range(first_day, stop):
                date = str(ds["time"].isel(time=lead).dt.strftime("%Y%m%d").item())
                anti, cycl = detection_paths(data_dir, member_number, date)
                if anti.exists() and cycl.exists():
                    print(f"Member {member_number:03d}, {date}: already detected; skipping")
                    continue

                anti.parent.mkdir(parents=True, exist_ok=True)
                print(f"Detecting member {member_number:03d}, {date} (lead {lead})", flush=True)
                ssh = ds["zos"].isel(ens=member_idx, time=lead).values
                grid = regularize_ssh(
                    ssh, source_lon, source_lat, lon, lat, interpolator=interpolator
                )
                with tempfile.TemporaryDirectory(prefix="gloens-member-") as tmp:
                    input_path = Path(tmp) / f"GLOENS_{date}.nc"
                    grid.to_netcdf(input_path)
                    compute_eddy(
                        str(input_path), "GLOENS", tmp, str(anti.parent) + "/",
                        "zos", "uo", "vo", SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX,
                        AMP_MIN, WAVELENGTH, ORDER_FILTER,
                    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("store", help="GLOENS 2DT-oce S3 Zarr URI")
    parser.add_argument("data_dir", help="Output root (e.g. ./data)")
    parser.add_argument("--lon-min", type=float, default=-80)
    parser.add_argument("--lon-max", type=float, default=0)
    parser.add_argument("--lat-min", type=float, default=20)
    parser.add_argument("--lat-max", type=float, default=65)
    parser.add_argument("--resolution", type=float, default=0.25)
    parser.add_argument("--first-day", type=int, default=0)
    parser.add_argument("--last-day", type=int, default=28, help="Exclusive lead index")
    parser.add_argument("--first-member", type=int, default=1, help="Inclusive, one-based")
    parser.add_argument("--last-member", type=int, default=1, help="Inclusive, one-based")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--authenticated", action="store_true")
    args = parser.parse_args(argv)
    detect_members(
        args.store, args.data_dir, lon_min=args.lon_min, lon_max=args.lon_max,
        lat_min=args.lat_min, lat_max=args.lat_max, resolution=args.resolution,
        first_day=args.first_day, last_day=args.last_day,
        first_member=args.first_member, last_member=args.last_member,
        endpoint=args.endpoint, anonymous=not args.authenticated,
    )


if __name__ == "__main__":
    main()
