"""On-demand GLOENS SSH regridding and geostrophic currents for eddy detection.

SSH is a scalar: it is interpolated, not rotated. East/north geostrophic
velocities are derived on the regular grid from SSH gradients, so no
native-grid vector rotation is necessary for the 2DT-oce zos-only store.
"""
from __future__ import annotations

import numpy as np
import xarray as xr
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import Delaunay

EARTH_RADIUS = 6371000.0
OMEGA = 7.2921159e-5
GRAVITY = 9.80665


def rotate_grid_vectors(u_grid, v_grid, angle_radians):
    """Rotate native grid-aligned velocities into geographic east/north.

    angle_radians is the counterclockwise angle from east to grid x.
    Only applicable when grid-aligned U/V fields and a valid grid-angle
    field are available; do not apply to SSH or already east/north U/V.
    """
    angle = np.asarray(angle_radians)
    return (u_grid * np.cos(angle) - v_grid * np.sin(angle),
            u_grid * np.sin(angle) + v_grid * np.cos(angle))


class CurvilinearToRegular:
    """Build triangulation once and reuse it across forecast days."""

    def __init__(self, longitude, latitude, lon_regular, lat_regular):
        self.lon = np.asarray(lon_regular, dtype=float)
        self.lat = np.asarray(lat_regular, dtype=float)
        if self.lon.ndim != 1 or self.lat.ndim != 1:
            raise ValueError("Regular longitude and latitude must be 1D")
        source_lon = np.asarray(longitude, dtype=float)
        source_lat = np.asarray(latitude, dtype=float)
        if source_lon.shape != source_lat.shape or source_lon.ndim != 2:
            raise ValueError("GLOENS longitude/latitude must be matching 2D arrays")
        self.source_shape = source_lon.shape
        self.valid_coordinates = np.isfinite(source_lon) & np.isfinite(source_lat)
        if np.count_nonzero(self.valid_coordinates) < 3:
            raise ValueError("At least three valid source grid points are needed")
        self.points = np.column_stack(
            (source_lon[self.valid_coordinates], source_lat[self.valid_coordinates])
        )
        self.target_lon, self.target_lat = np.meshgrid(self.lon, self.lat)
        self.triangulation = Delaunay(self.points)

    def scalar(self, field):
        values = np.asarray(field, dtype=float)
        if values.shape != self.source_shape:
            raise ValueError(f"Expected field shape {self.source_shape}, got {values.shape}")
        selected = values[self.valid_coordinates]
        # Avoid contaminating triangles across land or missing SSH values.
        # LinearNDInterpolator propagates NaNs for invalid vertices.
        result = LinearNDInterpolator(self.triangulation, selected, fill_value=np.nan)(
            self.target_lon, self.target_lat
        )
        return result


def geostrophic_velocity(ssh, longitude, latitude, min_abs_latitude=5.0):
    """Return geographic eastward/northward geostrophic currents (m/s).

    u_g = -g/f * d(SSH)/dy, v_g = g/f * d(SSH)/dx.
    Undefined within +/- min_abs_latitude degrees of the equator.
    """
    lon = np.asarray(longitude, dtype=float)
    lat = np.asarray(latitude, dtype=float)
    z = np.asarray(ssh, dtype=float)
    if z.shape != (lat.size, lon.size):
        raise ValueError("SSH shape must be (latitude, longitude)")
    if lat.size < 3 or lon.size < 3:
        raise ValueError("Need at least three points along each axis")
    if not (np.all(np.diff(lon) > 0) and np.all(np.diff(lat) > 0)):
        raise ValueError("Longitude and latitude must be strictly increasing")
    latitude_rad = np.deg2rad(lat)
    longitude_rad = np.deg2rad(lon)
    dz_dlat, dz_dlon = np.gradient(z, latitude_rad, longitude_rad, edge_order=2)
    coriolis = 2 * OMEGA * np.sin(latitude_rad)[:, None]
    coslat = np.cos(latitude_rad)[:, None]
    with np.errstate(divide="ignore", invalid="ignore"):
        u = -GRAVITY * dz_dlat / (coriolis * EARTH_RADIUS)
        v = GRAVITY * dz_dlon / (coriolis * EARTH_RADIUS * coslat)
    invalid = (np.abs(lat) < min_abs_latitude) | (np.abs(coslat[:, 0]) < 1e-6)
    u[invalid, :] = np.nan
    v[invalid, :] = np.nan
    return u, v


def regularize_ssh(ssh, longitude, latitude, lon_regular, lat_regular,
                   interpolator=None, min_abs_latitude=5.0):
    """Prepare a single day's mean zos for RegularGridDataset."""
    interpolator = interpolator or CurvilinearToRegular(
        longitude, latitude, lon_regular, lat_regular
    )
    zos = interpolator.scalar(ssh)
    u, v = geostrophic_velocity(zos, lon_regular, lat_regular, min_abs_latitude)
    return xr.Dataset(
        {"zos": (("latitude", "longitude"), zos.astype("float32")),
         "uo": (("latitude", "longitude"), u.astype("float32")),
         "vo": (("latitude", "longitude"), v.astype("float32"))},
        coords={"latitude": np.asarray(lat_regular), "longitude": np.asarray(lon_regular)},
        attrs={"note": "SSH scalar interpolation; east/north geostrophic currents derived from SSH"},
    )


def iter_gloens_detection_grids(store, cache_root, lon_regular, lat_regular,
                                endpoint=None, anonymous=True):
    """Yield (date, regular-grid Dataset) lazily, caching mean SSH per lead."""
    from eddy_load.gloens_mean import (
        DEFAULT_ENDPOINT, get_or_compute_mean, open_gloens_store,
    )
    endpoint = DEFAULT_ENDPOINT if endpoint is None else endpoint
    with open_gloens_store(store, endpoint=endpoint, anonymous=anonymous) as ds:
        interp = CurvilinearToRegular(
            ds["longitude"].values, ds["latitude"].values, lon_regular, lat_regular
        )
        for lead in range(ds.sizes["time"]):
            with get_or_compute_mean(ds, store, cache_root, lead, endpoint=endpoint) as mean:
                date = str(mean.time.dt.strftime("%Y%m%d").item())
                regular = regularize_ssh(
                    mean["zos"].isel(time=0).values,
                    ds["longitude"].values, ds["latitude"].values,
                    lon_regular, lat_regular, interpolator=interp,
                )
                yield date, regular


def detect_gloens(store, data_dir, lon_min, lon_max, lat_min, lat_max,
                  resolution=0.25, endpoint=None, anonymous=True):
    """Run daily eddy detection directly from GLOENS, with mean SSH cache.

    Intermediate regular-grid files are temporary, not a preprocessing product.
    The existing py-eddy-tracker detection code is reused unchanged.
    """
    import tempfile
    from pathlib import Path
    from eddy_detect.my_functions import compute_eddy
    from eddy_detect.namelist_detect import (
        SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX, AMP_MIN, WAVELENGTH, ORDER_FILTER,
    )
    if resolution <= 0 or lon_max <= lon_min or lat_max <= lat_min:
        raise ValueError("Invalid regular-grid bounds or resolution")
    lon = np.arange(lon_min, lon_max + resolution * 0.25, resolution)
    lat = np.arange(lat_min, lat_max + resolution * 0.25, resolution)
    output = Path(data_dir) / "GLOENS" / "DETECT"
    output.mkdir(parents=True, exist_ok=True)
    for date, grid in iter_gloens_detection_grids(
        store, data_dir, lon, lat, endpoint=endpoint, anonymous=anonymous
    ):
        anticyclonic = output / f"Anticyclonic_GLOENS_{date}.nc"
        cyclonic = output / f"Cyclonic_GLOENS_{date}.nc"
        if anticyclonic.exists() and cyclonic.exists():
            print(f"Detection exists for {date}; skipping")
            continue
        with tempfile.TemporaryDirectory(prefix="gloens-detect-") as temporary:
            path = Path(temporary) / f"GLOENS_{date}.nc"
            grid.to_netcdf(path)
            compute_eddy(
                str(path), "GLOENS", temporary, str(output) + "/",
                "zos", "uo", "vo", SHAPE_ERROR, PIXEL_MIN, PIXEL_MAX,
                AMP_MIN, WAVELENGTH, ORDER_FILTER,
            )
