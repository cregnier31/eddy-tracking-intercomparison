"""Compute daily ensemble-mean GLOENS sea-surface height from an S3 Zarr store.

Input: GLOENS 2DT-oce forecast with dims (time, ens, y, x) and 2D latitude/longitude.
Output: one GLOENS_YYYYMMDD.nc per day in <output_root>/GLOENS/.

This stage deliberately does not perform spatial regridding. The model grid has
2D geographic coordinates, whereas py-eddy-tracker RegularGridDataset requires a
regular lon/lat grid. Regrid separately before running eddy detection.
"""
from __future__ import annotations

import argparse
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


def export_daily_mean(store: str, output_root: str, endpoint: str = DEFAULT_ENDPOINT,
                      anonymous: bool = True, first_day: int = 0, last_day: int | None = None):
    output = Path(output_root) / "GLOENS"
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
            dest = output / f"GLOENS_{date}.nc"
            if dest.exists():
                print(f"Skipping existing {dest}")
                continue
            result = xr.Dataset(
                {"zos": day.astype("float32")},
                coords={"latitude": ds["latitude"], "longitude": ds["longitude"]},
                attrs={"source_store": store, "processing": "mean(zos, dim='ens', skipna=True)"},
            )
            # One daily slice computed at a time; do not load the 68 GB source.
            result.to_netcdf(dest, encoding={"zos": {"zlib": True, "complevel": 3}})
            print(f"Wrote {dest}")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("store", help="S3 Zarr path: s3://MOISICEEF/...2DT-oce...zarr")
    parser.add_argument("output_root", help="Directory containing the GLOENS subdirectory")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--authenticated", action="store_true", help="Use environment/IAM credentials")
    parser.add_argument("--first-day", type=int, default=0, help="Zero-based first lead to export")
    parser.add_argument("--last-day", type=int, help="Exclusive end lead; default all leads")
    args = parser.parse_args(argv)
    export_daily_mean(args.store, args.output_root, endpoint=args.endpoint,
                      anonymous=not args.authenticated, first_day=args.first_day,
                      last_day=args.last_day)


if __name__ == "__main__":
    main()
