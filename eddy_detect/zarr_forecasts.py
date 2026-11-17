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
from scipy.ndimage import gaussian_filter1d


def gaussian_lowpass_ssh(ssh, longitude, latitude, sigma_km):
    """NaN-normalized separable Gaussian in physical kilometres on a regular lat/lon grid.

    Longitude kernel varies by latitude; latitude kernel uses constant meridional spacing.
    Original land mask is retained. This smooths SSH, not derived currents.
    """
    if sigma_km <= 0:
        raise ValueError("sigma_km must be positive")
    z = np.asarray(ssh, dtype=np.float64)
    lon = np.asarray(longitude, dtype=float)
    lat = np.asarray(latitude, dtype=float)
    if z.shape != (len(lat), len(lon)) or len(lat) < 3 or len(lon) < 3:
        raise ValueError("SSH and coordinates have incompatible dimensions")
    if not (np.all(np.diff(lat) > 0) and np.all(np.diff(lon) > 0)):
        raise ValueError("Coordinates must be increasing")
    dx_deg = float(np.median(np.diff(lon)))
    dy_km = 111.195 * float(np.median(np.diff(lat)))
    valid = np.isfinite(z)
    numerator = np.where(valid, z, 0.0)
    weights = valid.astype(float)
    # Row-wise zonal smoothing with latitude-dependent physical grid spacing.
    for j, latitude in enumerate(lat):
        dx_km = 111.195 * dx_deg * np.cos(np.deg2rad(latitude))
        if dx_km <= 0:
            raise ValueError("Invalid latitude for zonal filtering")
        sx = sigma_km / dx_km
        numerator[j] = gaussian_filter1d(numerator[j], sx, mode="nearest", truncate=4)
        weights[j] = gaussian_filter1d(weights[j], sx, mode="nearest", truncate=4)
    sy = sigma_km / dy_km
    numerator = gaussian_filter1d(numerator, sy, axis=0, mode="nearest", truncate=4)
    weights = gaussian_filter1d(weights, sy, axis=0, mode="nearest", truncate=4)
    out = np.divide(numerator, weights, out=np.full_like(z, np.nan), where=weights >= 0.5)
    out[~valid] = np.nan
    return out


def _cell_edges(centers):
    centers = np.asarray(centers, dtype=float)
    if centers.ndim != 1 or len(centers) < 2 or np.any(np.diff(centers) <= 0):
        raise ValueError("Grid centers must be strictly increasing")
    mid = (centers[:-1] + centers[1:]) / 2
    return np.r_[centers[0] - (mid[0] - centers[0]), mid,
                 centers[-1] + (centers[-1] - mid[-1])]


def _overlap_weights(src_edges, dst_edges):
    """Exact 1D interval-overlap lengths; used in longitude and sin(latitude)."""
    from scipy.sparse import csr_matrix
    rows, cols, vals = [], [], []
    for i in range(len(dst_edges) - 1):
        left, right = dst_edges[i:i + 2]
        lo = max(0, np.searchsorted(src_edges, left, side="right") - 1)
        hi = min(len(src_edges) - 1, np.searchsorted(src_edges, right, side="left") + 1)
        for j in range(lo, hi):
            overlap = min(right, src_edges[j + 1]) - max(left, src_edges[j])
            if overlap > 0:
                rows.append(i)
                cols.append(j)
                vals.append(overlap)
    return csr_matrix((vals, (rows, cols)),
                      shape=(len(dst_edges) - 1, len(src_edges) - 1))


def conservative_regrid_ssh(ssh, src_lon, src_lat, dst_lon, dst_lat,
                            min_ocean_fraction=0.5):
    """Area-weighted first-order conservative regrid on regular spherical grids.

    Each destination cell averages source-cell values weighted by spherical
    overlap area. Missing source cells do not contribute; cells with insufficient
    valid ocean area remain NaN. For complete coverage the area integral is
    conserved (up to floating-point precision).
    """
    z = np.asarray(ssh, dtype=float)
    if z.shape != (len(src_lat), len(src_lon)):
        raise ValueError("SSH shape does not match source coordinates")
    if not 0 < min_ocean_fraction <= 1:
        raise ValueError("min_ocean_fraction must be in (0, 1]")
    lon_src = np.deg2rad(_cell_edges(src_lon))
    lon_dst = np.deg2rad(_cell_edges(dst_lon))
    lat_src = np.sin(np.deg2rad(np.clip(_cell_edges(src_lat), -90, 90)))
    lat_dst = np.sin(np.deg2rad(np.clip(_cell_edges(dst_lat), -90, 90)))
    wx = _overlap_weights(lon_src, lon_dst)
    wy = _overlap_weights(lat_src, lat_dst)
    valid = np.isfinite(z)
    numerator = (wy @ np.where(valid, z, 0.0)) @ wx.T
    ocean_area = (wy @ valid.astype(float)) @ wx.T
    full_area = np.outer(np.diff(lat_dst), np.diff(lon_dst))
    with np.errstate(divide="ignore", invalid="ignore"):
        fraction = np.divide(ocean_area, full_area,
                             out=np.zeros_like(ocean_area), where=full_area > 0)
        result = np.divide(numerator, ocean_area,
                           out=np.full_like(ocean_area, np.nan),
                           where=(ocean_area > 0) & (fraction >= min_ocean_fraction))
    return result


from eddy_detect.gloens_grid import geostrophic_velocity

ENDPOINT = "https://s3.waw3-1.cloudferro.com"
MODELS = {
    "GLONET": ("public/ml-forecast-outputs/glonet", "longitude", "latitude"),
    "GLOW": ("dev/ml-forecast-outputs/glowcascade_v5_ring", "lon", "lat"),
    "GLO12": ("public/GLO12", "longitude", "latitude"),
}
BUCKET = "oceanbench-bucket"


def detect(model, init_date, data_dir, first_day=0, last_day=None,
           lon_min=-80, lon_max=0, lat_min=20, lat_max=65,
           resolution=0.25, endpoint=ENDPOINT, assume_ssh_metres=False,
           gaussian_sigma_km=None, regrid_method="linear"):
    model = model.upper()
    if model not in MODELS:
        raise ValueError(f"Unknown model {model}; choose {list(MODELS)}")
    if first_day < 0 or (last_day is not None and last_day <= first_day) or resolution <= 0:
        raise ValueError("Invalid lead-day range or resolution")
    if not lon_min < lon_max or not lat_min < lat_max:
        raise ValueError("Invalid geographic bounds")
    if gaussian_sigma_km is not None and (model != "GLO12" or gaussian_sigma_km <= 0):
        raise ValueError("--gaussian-sigma-km requires GLO12 and a positive scale")
    if regrid_method not in ("linear", "conservative"):
        raise ValueError("Unknown regrid method")
    if regrid_method == "conservative" and model != "GLO12":
        raise ValueError("Conservative regridding is currently supported for GLO12 only")
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
        stop = ds.sizes["time"] if last_day is None else min(last_day, ds.sizes["time"])
        if stop <= first_day:
            raise ValueError(f"Only {ds.sizes['time']} forecast days available")
        if last_day is not None and stop < last_day:
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
            if gaussian_sigma_km is not None:
                ssh = gaussian_lowpass_ssh(ssh, src_lon_subset, src_lat[lat_idx][lat_order], gaussian_sigma_km)
            source = xr.DataArray(ssh, dims=("latitude", "longitude"),
                                  coords={"latitude": src_lat[lat_idx][lat_order],
                                          "longitude": src_lon_subset})
            if regrid_method == "conservative":
                target = conservative_regrid_ssh(ssh, src_lon_subset,
                                                 src_lat[lat_idx][lat_order], lon, lat)
            else:
                target = source.interp(longitude=lon, latitude=lat).values
            u, v = geostrophic_velocity(target, lon, lat)
            grid = xr.Dataset(
                {"zos": (("latitude", "longitude"), target.astype("float32")),
                 "uo": (("latitude", "longitude"), u.astype("float32")),
                 "vo": (("latitude", "longitude"), v.astype("float32"))},
                coords={"longitude": lon, "latitude": lat},
                attrs={"source_model": model, "source_store": store,
                       "forecast_timestamp": str(timestamp),
                       "gaussian_lowpass_sigma_km": (float(gaussian_sigma_km) if gaussian_sigma_km is not None else 0.0),
                       "regrid_method": regrid_method},
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
    parser.add_argument("--last-day", type=int, default=None, help="Exclusive lead index; default: all available days")
    parser.add_argument("--lon-min", type=float, default=-80)
    parser.add_argument("--lon-max", type=float, default=0)
    parser.add_argument("--lat-min", type=float, default=20)
    parser.add_argument("--lat-max", type=float, default=65)
    parser.add_argument("--resolution", type=float, default=0.25)
    parser.add_argument("--regrid-method",choices=("linear","conservative"),default="linear",
                        help="GLO12: area-weighted conservative regridding or existing linear interpolation")
    parser.add_argument("--gaussian-sigma-km", type=float, default=None,
                        help="GLO12 only: NaN-aware Gaussian SSH low-pass on native grid, before regridding (km)")
    parser.add_argument("--endpoint", default=ENDPOINT)
    parser.add_argument("--assume-ssh-metres", action="store_true",
                        help="Explicitly confirm missing SSH units are metres")
    args = parser.parse_args()
    detect(args.model, args.init_date, args.data_dir, args.first_day, args.last_day,
           args.lon_min, args.lon_max, args.lat_min, args.lat_max,
           args.resolution, args.endpoint, args.assume_ssh_metres,
           args.gaussian_sigma_km, args.regrid_method)


if __name__ == "__main__":
    main()
