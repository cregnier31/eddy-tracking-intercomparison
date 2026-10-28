"""Discover a GLOENS forecast Zarr for a specified initialization date."""
from __future__ import annotations

import argparse
import re

import s3fs

from eddy_detect.gloens_grid import detect_gloens
from eddy_load.gloens_mean import DEFAULT_ENDPOINT


def find_gloens_store(run_date: str, bucket: str = "MOISICEEF",
                      endpoint: str = DEFAULT_ENDPOINT, anonymous: bool = True) -> str:
    if not re.fullmatch(r"\d{8}", run_date):
        raise ValueError("run_date must use YYYYMMDD")
    fs = s3fs.S3FileSystem(
        client_kwargs={"endpoint_url": endpoint}, anon=anonymous
    )
    # List metadata only; no forecast data downloaded during discovery.
    candidates = [
        path for path in fs.ls(bucket)
        if path.endswith(".zarr")
        and "2DT-oce" in path
        and (f"_R{run_date}.zarr" in path or f"_{run_date}-" in path)
    ]
    if not candidates:
        raise FileNotFoundError(
            f"No 2DT-oce GLOENS Zarr for {run_date} in {bucket}. "
            "Check the bucket inventory and available forecast dates."
        )
    exact = [path for path in candidates if f"_R{run_date}.zarr" in path]
    if len(exact) == 1:
        return "s3://" + exact[0]
    if len(candidates) == 1:
        return "s3://" + candidates[0]
    raise ValueError(
        f"Multiple candidate stores for {run_date}: {candidates}. "
        "Pass the chosen Zarr store directly to eddy_detect.gloens_grid."
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_date", help="GLOENS initialization date, YYYYMMDD")
    parser.add_argument("data_dir")
    parser.add_argument("--bucket", default="MOISICEEF")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--authenticated", action="store_true")
    parser.add_argument("--lon-min", type=float, default=-19)
    parser.add_argument("--lon-max", type=float, default=5)
    parser.add_argument("--lat-min", type=float, default=26)
    parser.add_argument("--lat-max", type=float, default=56)
    parser.add_argument("--resolution", type=float, default=0.25)
    parser.add_argument("--first-day", type=int, default=0)
    parser.add_argument("--last-day", type=int, default=1)
    args = parser.parse_args(argv)
    anonymous = not args.authenticated
    store = find_gloens_store(
        args.run_date, bucket=args.bucket, endpoint=args.endpoint, anonymous=anonymous
    )
    print(f"Found GLOENS forecast: {store}")
    detect_gloens(
        store, args.data_dir, args.lon_min, args.lon_max, args.lat_min,
        args.lat_max, resolution=args.resolution, endpoint=args.endpoint,
        anonymous=anonymous, first_day=args.first_day, last_day=args.last_day,
    )


if __name__ == "__main__":
    main()
