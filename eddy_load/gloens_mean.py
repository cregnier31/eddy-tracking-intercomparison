"""Compute daily ensemble-mean GLOENS sea-surface height from an S3 Zarr store.

Input: GLOENS 2DT-oce forecast with dims (time, ens, y, x) and 2D latitude/longitude.
Output: one GLOENS_YYYYMMDD.nc per day in a store-specific cache directory.

This stage deliberately does not perform spatial regridding. The model grid has
2D geographic coordinates, whereas py-eddy-tracker RegularGridDataset requires a
regular lon/lat grid. Regrid separately before running eddy detection.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

import s3fs
import xarray as xr


DEFAULT_ENDPOINT = "https://s3.waw3-1.cloudferro.com"


def open_gloens_store(store: str, endpoint: str = DEFAULT_ENDPOINT, anonymous: bool = True):
    """Open only metadata initially; array computation remains lazy."""
    fs = s3fs.S3FileSystem(anon=anonymous, client_kwargs={"endpoint_url": endpoint})
    path = store.removeprefix("s3://").rstrip("/")
    mapper = s3fs.S3Map(root=path, s3=fs, check=False)
    return xr.open_zarr(mapper, consolidated=False, chunks="auto")


def ensemble_mean_ssh(ds: xr.Dataset) -> xr.DataArray:
    """Mean across available ensemble members, retaining time and spatial grid."""
    if "zos" not in ds:
        raise KeyError("Missing GLOENS sea surface height variable 'zos'")
    zos = ds["zos"]
    expected_dims = {"time", "ens", "y", "x"}
    if not expected_dims.issubset(zos.dims):
        raise ValueError(f"Expected zos dimensions {sorted(expected_dims)}; got {zos.dims}")
    if ds.sizes["ens"] != 50:
        raise ValueError(f"Expected 50 GLOENS ensemble members; found {ds.sizes['ens']}")
    mean = zos.astype("float32").mean(dim="ens", skipna=True, keep_attrs=True)
    mean.attrs["long_name"] = "GLOENS ensemble mean sea surface height"
    mean.attrs["ensemble_members"] = 50
    return mean


def cache_directory(store: str, output_root: str, endpoint: str = DEFAULT_ENDPOINT) -> Path:
    """Keep different GLOENS forecast runs and remote locations separate."""
    source = endpoint.rstrip("/") + "/" + store.removeprefix("s3://").rstrip("/")
    store_name = store.removeprefix("s3://").rstrip("/").split("/")[-1]
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
    return Path(output_root) / "GLOENS" / f"{store_name}_{digest}"


def cached_mean_path(store: str, output_root: str, date: str,
                     endpoint: str = DEFAULT_ENDPOINT) -> Path:
    return cache_directory(store, output_root, endpoint) / f"GLOENS_{date}.nc"


def load_cached_mean(path: Path) -> xr.Dataset:
    """Open the persisted mean lazily; caller should close the dataset."""
    return xr.open_dataset(path, chunks={})


def get_or_compute_mean(ds: xr.Dataset, store: str, output_root: str, day_index: int,
                        endpoint: str = DEFAULT_ENDPOINT, force: bool = False) -> xr.Dataset:
    """Return one day's cached or newly computed ensemble-mean SSH.

    Called *inside* the detection workflow. The caller must close the returned
    dataset. No standalone preprocessing invocation is required.
    """
    date = str(ds["time"].isel(time=day_index).dt.strftime("%Y%m%d").item())
    dest = cached_mean_path(store, output_root, date, endpoint)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        try:
            cached = load_cached_mean(dest)
            if (cached.attrs.get("source_store") == store
                    and cached.attrs.get("source_endpoint") == endpoint
                    and cached.attrs.get("processing") == "mean(zos, dim='ens', skipna=True)"
                    and "zos" in cached
                    and cached.sizes.get("time") == 1
                    and cached.sizes.get("y") == ds.sizes["y"]
                    and cached.sizes.get("x") == ds.sizes["x"]
                    and str(cached.time.dt.strftime("%Y%m%d").item()) == date):
                print(f"Reusing cached ensemble mean: {dest}")
                return cached
            cached.close()
        except (OSError, ValueError, KeyError):
            pass
    if "latitude" not in ds or "longitude" not in ds:
        raise KeyError("GLOENS requires 2D latitude/longitude coordinates")
    mean = ensemble_mean_ssh(ds).isel(time=slice(day_index, day_index + 1))
    result = xr.Dataset(
        {"zos": mean},
        coords={"latitude": ds["latitude"], "longitude": ds["longitude"]},
        attrs={"source_store": store, "source_endpoint": endpoint,
               "processing": "mean(zos, dim='ens', skipna=True)"},
    )
    temp = dest.with_suffix(".nc.partial")
    try:
        result.to_netcdf(temp, encoding={"zos": {"zlib": True, "complevel": 3}})
        os.replace(temp, dest)
    finally:
        if temp.exists():
            temp.unlink()
    print(f"Computed and cached ensemble mean: {dest}")
    return load_cached_mean(dest)


def export_daily_mean(store: str, output_root: str, endpoint: str = DEFAULT_ENDPOINT,
                      anonymous: bool = True, first_day: int = 0, last_day: int | None = None,
                      force: bool = False):
    """Reuse existing daily products and compute only missing days.

    Each output is written to a temporary file and then atomically moved into
    place, so a failed or interrupted write never masquerades as a valid cache.
    """
    output = cache_directory(store, output_root, endpoint)
    output.mkdir(parents=True, exist_ok=True)
    with open_gloens_store(store, endpoint=endpoint, anonymous=anonymous) as ds:
        if "latitude" not in ds or "longitude" not in ds:
            raise KeyError("Expected 2D latitude/longitude coordinates in the GLOENS Zarr store")
        mean = ensemble_mean_ssh(ds)
        total = mean.sizes["time"]
        stop = total if last_day is None else min(last_day, total)
        if not 0 <= first_day < stop:
            raise ValueError(f"Invalid day slice [{first_day}:{stop}] for {total} forecast days")
        for i in range(first_day, stop):
            day = mean.isel(time=i)
            date = str(day.time.dt.strftime("%Y%m%d").item())
            dest = cached_mean_path(store, output_root, date, endpoint)
            if dest.exists() and not force:
                # Validate the cache metadata before trusting an existing file.
                try:
                    with load_cached_mean(dest) as cached:
                        if (cached.attrs.get("source_store") == store
                                and cached.attrs.get("source_endpoint") == endpoint
                                and cached.attrs.get("processing") == "mean(zos, dim='ens', skipna=True)"
                                and "zos" in cached
                                and cached.sizes.get("time") == 1
                                and cached.sizes.get("y") == ds.sizes["y"]
                                and cached.sizes.get("x") == ds.sizes["x"]
                                and str(cached.time.dt.strftime("%Y%m%d").item()) == date):
                            print(f"Using cached mean: {dest}")
                            continue
                except (OSError, ValueError, KeyError):
                    pass
                print(f"Cache invalid; recomputing: {dest}")
            result = xr.Dataset(
                {"zos": day.astype("float32")},
                coords={"latitude": ds["latitude"], "longitude": ds["longitude"]},
                attrs={"source_store": store, "source_endpoint": endpoint,
                       "processing": "mean(zos, dim='ens', skipna=True)"},
            )
            temp = dest.with_suffix(".nc.partial")
            try:
                result.to_netcdf(temp, encoding={"zos": {"zlib": True, "complevel": 3}})
                os.replace(temp, dest)
            finally:
                if temp.exists():
                    temp.unlink()
            print(f"Saved ensemble mean: {dest}")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("store", help="S3 Zarr path: s3://MOISICEEF/...2DT-oce...zarr")
    parser.add_argument("output_root", help="Directory containing the GLOENS subdirectory")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--authenticated", action="store_true", help="Use environment/IAM credentials")
    parser.add_argument("--first-day", type=int, default=0, help="Zero-based first lead to export")
    parser.add_argument("--last-day", type=int, help="Exclusive end lead; default all leads")
    parser.add_argument("--force", action="store_true", help="Recompute cached means")
    args = parser.parse_args(argv)
    export_daily_mean(args.store, args.output_root, endpoint=args.endpoint,
                      anonymous=not args.authenticated, first_day=args.first_day,
                      last_day=args.last_day, force=args.force)


if __name__ == "__main__":
    main()
