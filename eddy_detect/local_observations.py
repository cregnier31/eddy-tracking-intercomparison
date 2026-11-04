"""Detect eddies from locally stored Copernicus Marine daily ADT NetCDF files.

Point --source to the 2026 directory containing 09/ and 10/, or to 10/
(the parent year directory is then used automatically).
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
import xarray as xr

from eddy_detect.gloens_grid import geostrophic_velocity
from eddy_detect.observations import date_strings


def detect_local(data_dir, source, start, end, lon_min=-80, lon_max=0,
                 lat_min=20, lat_max=65, resolution=0.25):
    from eddy_detect.my_functions import compute_eddy
    from eddy_detect.namelist_detect import (
        SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX, AMP_MIN, WAVELENGTH, ORDER_FILTER,
    )
    source = Path(source)
    if source.name in [f"{i:02d}" for i in range(1, 13)]:
        source = source.parent
    if not source.is_dir():
        raise NotADirectoryError(source)
    if resolution <= 0 or lon_min >= lon_max or lat_min >= lat_max:
        raise ValueError("Invalid grid specification")
    dates = date_strings(start, end)
    files = sorted(source.rglob("*.nc"))
    if not files:
        raise FileNotFoundError(f"No .nc files under {source}")
    print(f"Scanning {len(files)} NetCDF files in {source}", flush=True)
    lookup = {}
    requested = set(dates)
    for file in files:
        with xr.open_dataset(file) as ds:
            if "adt" not in ds or "time" not in ds:
                continue
            for day in np.asarray(ds.time.values).astype("datetime64[D]"):
                date = np.datetime_as_string(day, unit="D").replace("-", "")
                if date in requested:
                    if date in lookup and lookup[date] != file:
                        raise ValueError(f"Duplicate observation for {date}: {lookup[date]}, {file}")
                    lookup[date] = file
    missing = sorted(requested - lookup.keys())
    if missing:
        raise FileNotFoundError(
            f"Missing observational days: {', '.join(missing)}; "
            f"check that 2026/09 and 2026/10 are present under {source}"
        )
    output = Path(data_dir) / "GLOENS" / "OBS" / "DETECT"
    output.mkdir(parents=True, exist_ok=True)
    lon = np.arange(lon_min, lon_max + resolution * 0.25, resolution)
    lat = np.arange(lat_min, lat_max + resolution * 0.25, resolution)
    for date in dates:
        if all((output / f"{polarity}_OBS_{date}.nc").exists()
               for polarity in ("Cyclonic", "Anticyclonic")):
            print(f"{date}: already detected; skipping", flush=True)
            continue
        file = lookup[date]
        day = np.datetime64(f"{date[:4]}-{date[4:6]}-{date[6:]}")
        with xr.open_dataset(file) as ds:
            ds = ds.sortby("latitude").sortby("longitude")
            indices = np.flatnonzero(
                np.asarray(ds.time.values).astype("datetime64[D]") == day
            )
            if len(indices) != 1:
                raise ValueError(f"Expected one ADT observation for {date} in {file}")
            field = ds.adt.isel(time=int(indices[0])).sel(
                longitude=slice(lon_min - 1, lon_max + 1),
                latitude=slice(lat_min - 1, lat_max + 1),
            )
            ssh = field.interp(longitude=lon, latitude=lat).values
        u, v = geostrophic_velocity(ssh, lon, lat)
        grid = xr.Dataset(
            {"zos": (("latitude", "longitude"), ssh.astype("float32")),
             "uo": (("latitude", "longitude"), u.astype("float32")),
             "vo": (("latitude", "longitude"), v.astype("float32"))},
            coords={"longitude": lon, "latitude": lat},
        )
        print(f"Detecting {date} from {file}", flush=True)
        with tempfile.TemporaryDirectory(prefix="obs-local-") as tmp:
            input_file = Path(tmp) / f"OBS_{date}.nc"
            grid["zos"].attrs["units"] = "m"
            grid["uo"].attrs["units"] = "m/s"
            grid["vo"].attrs["units"] = "m/s"
            grid.to_netcdf(input_file)
            compute_eddy(
                str(input_file), "OBS", tmp, str(output) + "/",
                "zos", "uo", "vo", SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX,
                AMP_MIN, WAVELENGTH, ORDER_FILTER,
            )
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--start", default="2026-09-24")
    parser.add_argument("--end", default="2026-10-21")
    parser.add_argument("--lon-min", type=float, default=-80)
    parser.add_argument("--lon-max", type=float, default=0)
    parser.add_argument("--lat-min", type=float, default=20)
    parser.add_argument("--lat-max", type=float, default=65)
    parser.add_argument("--resolution", type=float, default=0.25)
    args = parser.parse_args(argv)
    detect_local(args.data_dir, args.source, args.start, args.end,
                 args.lon_min, args.lon_max, args.lat_min, args.lat_max,
                 args.resolution)


if __name__ == "__main__":
    main()
