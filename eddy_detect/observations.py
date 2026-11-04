"""Copernicus Marine NRT ADT eddy detection and tracking, using GLOENS settings.

Example:
  python -m eddy_detect.observations detect ./data --start 2026-09-24 --end 2026-10-21
  python -m eddy_detect.observations track ./data --start 2026-09-24 --end 2026-10-21

Install: pip install copernicusmarine
Authenticate with 'copernicusmarine login' or supported environment credentials.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import xarray as xr

from eddy_detect.gloens_grid import geostrophic_velocity
from eddy_track.gloens_members import tracking_config, DEFAULT_TEMPLATE

DATASET_ID = "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D"


def date_strings(start, end):
    dates = np.arange(np.datetime64(start, "D"), np.datetime64(end, "D") + np.timedelta64(1, "D"))
    if not len(dates):
        raise ValueError("End date must not precede start date")
    return [np.datetime_as_string(d, unit="D").replace("-", "") for d in dates]


def detect(data_dir, start, end, lon_min=-80, lon_max=0, lat_min=20,
           lat_max=65, resolution=0.25, dataset_id=DATASET_ID):
    """Cache ADT subset and detect daily eddies on the matching 0.25-degree grid."""
    import copernicusmarine
    from eddy_detect.my_functions import compute_eddy
    from eddy_detect.namelist_detect import (
        SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX, AMP_MIN, WAVELENGTH, ORDER_FILTER,
    )

    if resolution <= 0 or lon_min >= lon_max or lat_min >= lat_max:
        raise ValueError("Invalid grid specification")
    root = Path(data_dir) / "GLOENS" / "OBS"
    raw = root / "SOURCE" / f"adt_{start}_{end}.nc"
    output = root / "DETECT"
    raw.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    dates = date_strings(start, end)

    if not raw.exists():
        print(f"Downloading {dataset_id} ADT for {start}..{end}", flush=True)
        with tempfile.TemporaryDirectory(prefix="obs-download-") as tmp:
            result = copernicusmarine.subset(
                dataset_id=dataset_id, variables=["adt"],
                minimum_longitude=lon_min, maximum_longitude=lon_max,
                minimum_latitude=lat_min, maximum_latitude=lat_max,
                start_datetime=start, end_datetime=end,
                output_directory=tmp, output_filename="adt.nc",
                force_download=True,
            )
            downloaded = Path(getattr(result, "file_path", Path(tmp) / "adt.nc"))
            if not downloaded.is_file():
                raise FileNotFoundError(f"Copernicus download not found: {downloaded}")
            shutil.copy2(downloaded, raw)

    lon = np.arange(lon_min, lon_max + resolution * 0.25, resolution)
    lat = np.arange(lat_min, lat_max + resolution * 0.25, resolution)
    with xr.open_dataset(raw) as ds:
        if "adt" not in ds:
            raise KeyError(f"{raw}: missing ADT. Variables: {list(ds.data_vars)}")
        if not {"time", "latitude", "longitude"}.issubset(ds["adt"].dims):
            raise ValueError(f"{raw}: expected ADT(time, latitude, longitude)")
        ds = ds.sortby("latitude").sortby("longitude")
        available = set(np.asarray(ds.time.values).astype("datetime64[D]"))
        for date in dates:
            anti = output / f"Anticyclonic_OBS_{date}.nc"
            cycl = output / f"Cyclonic_OBS_{date}.nc"
            if anti.exists() and cycl.exists():
                print(f"{date}: already detected; skipping", flush=True)
                continue
            day = np.datetime64(f"{date[:4]}-{date[4:6]}-{date[6:]}")
            if day not in available:
                raise ValueError(f"No ADT observation for {day} in {raw}")
            ssh = ds["adt"].sel(time=day).interp(longitude=lon, latitude=lat).values
            u, v = geostrophic_velocity(ssh, lon, lat)
            grid = xr.Dataset(
                {"zos": (("latitude", "longitude"), ssh.astype("float32")),
                 "uo": (("latitude", "longitude"), u.astype("float32")),
                 "vo": (("latitude", "longitude"), v.astype("float32"))},
                coords={"longitude": lon, "latitude": lat},
            )
            print(f"Detecting OBS {date}", flush=True)
            with tempfile.TemporaryDirectory(prefix="obs-detect-") as tmp:
                input_path = Path(tmp) / f"OBS_{date}.nc"
                grid.to_netcdf(input_path)
                compute_eddy(
                    str(input_path), "OBS", tmp, str(output) + "/",
                    "zos", "uo", "vo", SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX,
                    AMP_MIN, WAVELENGTH, ORDER_FILTER,
                )
    return output


def track(data_dir, start, end, template=DEFAULT_TEMPLATE, executable="EddyTracking"):
    """Track observations with exactly the same AreaTracker YAML as GLOENS."""
    command = shutil.which(executable)
    if command is None:
        raise FileNotFoundError(f"Missing executable: {executable}")
    root = Path(data_dir) / "GLOENS" / "OBS"
    input_dir = root / "DETECT"
    output_dir = root / "TRACK"
    dates = date_strings(start, end)
    for polarity in ("Cyclonic", "Anticyclonic"):
        for date in dates:
            path = input_dir / f"{polarity}_OBS_{date}.nc"
            if not path.exists():
                raise FileNotFoundError(f"Missing daily detection: {path}")
        output_dir.mkdir(parents=True, exist_ok=True)
        config = tracking_config(template, input_dir, output_dir, polarity)
        with tempfile.TemporaryDirectory(prefix="obs-track-") as tmp:
            config_path = Path(tmp) / f"{polarity}.yaml"
            config_path.write_text(config, encoding="utf-8")
            print(f"Tracking OBS {polarity}", flush=True)
            subprocess.run([command, str(config_path)], check=True)
    return output_dir


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("detect", "track"))
    parser.add_argument("data_dir")
    parser.add_argument("--start", default="2026-09-24")
    parser.add_argument("--end", default="2026-10-21")
    parser.add_argument("--lon-min", type=float, default=-80)
    parser.add_argument("--lon-max", type=float, default=0)
    parser.add_argument("--lat-min", type=float, default=20)
    parser.add_argument("--lat-max", type=float, default=65)
    parser.add_argument("--resolution", type=float, default=0.25)
    parser.add_argument("--dataset-id", default=DATASET_ID)
    args = parser.parse_args(argv)
    if args.command == "detect":
        detect(args.data_dir, args.start, args.end, args.lon_min, args.lon_max,
               args.lat_min, args.lat_max, args.resolution, args.dataset_id)
    else:
        track(args.data_dir, args.start, args.end)


if __name__ == "__main__":
    main()
