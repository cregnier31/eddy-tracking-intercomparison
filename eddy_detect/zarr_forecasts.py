"""Detect SSH-contour eddies from GLONET, GLOW or GLO12 daily forecast Zarr.

Uses the existing GLOENS 0.25-degree SSH/geostrophic-velocity preparation
and py-eddy-tracker detector. Reads only the requested geographic subset.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
import xarray as xr
import s3fs

from eddy_detect.gloens_grid import geostrophic_velocity

ENDPOINT = "https://s3.waw3-1.cloudferro.com"
MODELS = {
    "GLONET": ("public/ml-forecast-outputs/glonet", "longitude", "latitude"),
    "GLOW": ("dev/ml-forecast-outputs/glowcascade_v5_ring", "lon", "lat"),
    "GLO12": ("public/GLO12", "longitude", "latitude"),
}
BUCKET = "oceanbench-bucket"


def detect(model, init_date, data_dir, first_day=0, last_day=9,
           lon_min=-80, lon_max=0, lat_min=20, lat_max=65,
           resolution=0.25, endpoint=ENDPOINT, assume_ssh_metres=False):
    model = model.upper()
    if model not in MODELS:
        raise ValueError(f"Unknown model {model}; choose {list(MODELS)}")
    if not 0 <= first_day < last_day or resolution <= 0:
        raise ValueError("Invalid lead-day range or resolution")
    if not lon_min < lon_max or not lat_min < lat_max:
        raise ValueError("Invalid geographic bounds")
    if model == "GLOW" and not assume_ssh_metres:
        raise ValueError("GLOW zos has no units metadata; verify metres and pass --assume-ssh-metres")
    from eddy_detect.my_functions import compute_eddy
    from eddy_detect.namelist_detect import (
        SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX, AMP_MIN, WAVELENGTH, ORDER_FILTER,
    )

    prefix, lon_name, lat_name = MODELS[model]
    store = f"{BUCKET}/{prefix}/{init_date}.zarr"
    fs = s3fs.S3FileSystem(anon=True, client_kwargs={"endpoint_url": endpoint})
    mapper = s3fs.S3Map(root=store, s3=fs, check=False)
    output = Path(data_dir) / model / init_date / "DETECT"
    output.mkdir(parents=True, exist_ok=True)
    lon = np.arange(lon_min, lon_max + 0.25 * resolution, resolution)
    lat = np.arange(lat_min, lat_max + 0.25 * resolution, resolution)

    print(f"Opening {store}", flush=True)
    with xr.open_zarr(mapper, consolidated=False) as ds:
        if "zos" not in ds:
            raise KeyError(f"{model}: no zos in store")
        if ds["zos"].attrs.get("units") not in ("m", "metre", "meter", "metres", "meters", None):
            raise ValueError(f"Unexpected SSH units: {ds['zos'].attrs.get('units')}")
        if ds["zos"].attrs.get("units") is None and not assume_ssh_metres:
            raise ValueError("SSH units missing; verify metres and pass --assume-ssh-metres")
        stop = min(last_day, ds.sizes["time"])
        if stop <= first_day:
            raise ValueError(f"Only {ds.sizes['time']} forecast days available")
        if stop < last_day:
            print(f"Warning: requested {last_day} days, only {stop} available", flush=True)
        # Normalize 0..360 longitude into -180..180, avoiding global loads.
        src_lon = np.asarray(ds[lon_name].values)
        src_lat = np.asarray(ds[lat_name].values)
        if src_lon.ndim != 1 or src_lat.ndim != 1:
            raise ValueError("This reader expects one-dimensional regular coordinates")
        lon_180 = ((src_lon + 180) % 360) - 180
        lon_idx = np.flatnonzero((lon_180 >= lon_min - 1) & (lon_180 <= lon_max + 1))
        lat_idx = np.flatnonzero((src_lat >= lat_min - 1) & (src_lat <= lat_max + 1))
        if len(lon_idx) < 3 or len(lat_idx) < 3:
            raise ValueError("Not enough source grid cells within requested domain")
        src_lon_subset = lon_180[lon_idx]
        lon_order = np.argsort(src_lon_subset)
        src_lon_subset = src_lon_subset[lon_order]
        lat_order = np.argsort(src_lat[lat_idx])
        for lead in range(first_day, stop):
            timestamp = np.datetime64(ds["time"].values[lead])
            date = np.datetime_as_string(timestamp, unit="D").replace("-", "")
            anti = output / f"Anticyclonic_{model}_{date}.nc"
            cycl = output / f"Cyclonic_{model}_{date}.nc"
            if anti.exists() and cycl.exists():
                print(f"{model} {date}: already detected; skipping", flush=True)
                continue
            print(f"{model} lead {lead}: {timestamp}", flush=True)
            # .isel subsets before reading array chunks; no full-global SSH load.
            ssh = ds["zos"].isel(time=lead, **{
                lon_name: lon_idx, lat_name: lat_idx,
            }).transpose(lat_name, lon_name).values
            ssh = np.asarray(ssh)[lat_order][:, lon_order]
            source = xr.DataArray(ssh, dims=("latitude", "longitude"),
                                  coords={"latitude": src_lat[lat_idx][lat_order],
                                          "longitude": src_lon_subset})
            target = source.interp(longitude=lon, latitude=lat).values
            u, v = geostrophic_velocity(target, lon, lat)
            grid = xr.Dataset(
                {"zos": (("latitude", "longitude"), target.astype("float32")),
                 "uo": (("latitude", "longitude"), u.astype("float32")),
                 "vo": (("latitude", "longitude"), v.astype("float32"))},
                coords={"longitude": lon, "latitude": lat},
                attrs={"source_model": model, "source_store": store,
                       "forecast_timestamp": str(timestamp)},
            )
            grid.zos.attrs["units"] = "m"
            grid.uo.attrs["units"] = "m/s"
            grid.vo.attrs["units"] = "m/s"
            with tempfile.TemporaryDirectory(prefix=f"{model.lower()}-detect-") as tmp:
                input_path = Path(tmp) / f"{model}_{date}.nc"
                grid.to_netcdf(input_path)
                compute_eddy(
                    str(input_path), model, tmp, str(output) + "/",
                    "zos", "uo", "vo", SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX,
                    AMP_MIN, WAVELENGTH, ORDER_FILTER,
                )
    print(f"Detection complete: {output}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=sorted(MODELS))
    parser.add_argument("init_date", help="Forecast initialization YYYYMMDD")
    parser.add_argument("data_dir")
    parser.add_argument("--first-day", type=int, default=0)
    parser.add_argument("--last-day", type=int, default=9, help="Exclusive lead index")
    parser.add_argument("--lon-min", type=float, default=-80)
    parser.add_argument("--lon-max", type=float, default=0)
    parser.add_argument("--lat-min", type=float, default=20)
    parser.add_argument("--lat-max", type=float, default=65)
    parser.add_argument("--resolution", type=float, default=0.25)
    parser.add_argument("--endpoint", default=ENDPOINT)
    parser.add_argument("--assume-ssh-metres", action="store_true",
                        help="Explicitly confirm missing SSH units are metres")
    args = parser.parse_args()
    detect(args.model, args.init_date, args.data_dir, args.first_day, args.last_day,
           args.lon_min, args.lon_max, args.lat_min, args.lat_max,
           args.resolution, args.endpoint, args.assume_ssh_metres)


if __name__ == "__main__":
    main()
