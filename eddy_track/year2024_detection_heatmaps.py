"""2024 North Atlantic heatmaps from daily DETECTION files, not tracks.

Seven forecast configurations and OBS, 52 weekly cycles, common 9 forecast
days. Each grid cell is the mean number of detected eddy centers per forecast
day, with cyclonic and anticyclonic detections combined. Repeated observation
dates are weighted by the corresponding forecast exposure.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from eddy_track.year2024_sixway import SOURCES, LABELS, cycle_dates

POLARITIES = ("Cyclonic", "Anticyclonic")
BOUNDS = (-80., 0., 20., 65.)

def read_centers(path):
    """Return longitude, latitude, effective radius (km), amplitude (cm)."""
    try:
        with xr.open_dataset(path) as ds:
            required = ("longitude", "latitude", "effective_radius", "amplitude")
            for variable in required:
                if variable not in ds:
                    raise ValueError(f"{path}: missing {variable}")
            lon = np.asarray(ds["longitude"].values).ravel()
            lat = np.asarray(ds["latitude"].values).ravel()
            radius = np.asarray(ds["effective_radius"].values).ravel() / 1000.
            amplitude = np.asarray(ds["amplitude"].values).ravel() * 100.
    except Exception as exc:
        raise RuntimeError(f"Cannot read detection file {path}") from exc
    if len({lon.size, lat.size, radius.size, amplitude.size}) != 1:
        raise ValueError(f"{path}: inconsistent detection variable lengths")
    lon = ((lon + 180.) % 360.) - 180.
    valid = np.isfinite(lon) & np.isfinite(lat)
    return lon[valid], lat[valid], radius[valid], amplitude[valid]

def detect_dir(root, cycle, model, init):
    base = root / "CYCLES" / cycle
    if model == "GLOENS_MEAN":
        return base / "GLOENS" / "DETECT", "GLOENS"
    return base / model / init / "DETECT", model

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-root", type=Path, default=Path("data_2024"))
    p.add_argument("--native-root", type=Path, default=Path("data_2024_glo12_native"))
    p.add_argument("--filtered-root", type=Path, default=Path("data_2024_lp15_cons"))
    p.add_argument("--conservative-root", type=Path)
    p.add_argument("--native45-root", type=Path, default=None,
                   help="Include native GLO12 with minimum 45 pixels")
    p.add_argument("--native45-lp15-root", type=Path, default=None,
                   help="Include native GLO12 45 pixels with Gaussian sigma 15 km")
    p.add_argument("--obs-root", type=Path, default=Path("data_2024/OBS_FULL"))
    p.add_argument("--output-root", type=Path, default=Path("data_2024_sevenway"))
    p.add_argument("--cell-deg", type=float, default=2.0)
    p.add_argument("--max-color", type=float, default=None,
                   help="Optional fixed upper limit for all maps; default: shared observed maximum")
    args = p.parse_args()
    if args.cell_deg <= 0 or (args.max_color is not None and args.max_color <= 0):
        p.error("--cell-deg and --max-color must be positive")
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
    except ImportError as exc:
        raise SystemExit("Cartopy required for continents: conda install -c conda-forge cartopy") from exc

    roots = {"base": args.base_root, "native": args.native_root, "filtered": args.filtered_root}
    sources = dict(SOURCES)
    labels = dict(LABELS)
    if args.conservative_root is not None:
        roots["conservative"] = args.conservative_root
        sources["GLO12_CONS"] = ("conservative", "GLO12", 10)
        labels["GLO12_CONS"] = "GLO12 conservative 0.25° (no Gaussian)"
    if args.native45_root is not None:
        roots["native45"] = args.native45_root
        sources["GLO12_NATIVE45"] = ("native45", "GLO12", 10)
        labels["GLO12_NATIVE45"] = "GLO12 native 1/12° (45 pixels)"
    if args.native45_lp15_root is not None:
        roots["native45_lp15"] = args.native45_lp15_root
        sources["GLO12_NATIVE45_LP15"] = ("native45_lp15", "GLO12", 10)
        labels["GLO12_NATIVE45_LP15"] = "GLO12 native 1/12° (45 px, Gaussian 15 km)"
    labels["OBS_WED"] = "AVISO / OBS (Wednesday)"
    labels["OBS_THU"] = "AVISO / OBS (Thursday)"
    names = list(sources) + ["OBS_WED", "OBS_THU"]

    lon_edges = np.linspace(-80, 0, int(np.ceil(80 / args.cell_deg)) + 1)
    lat_edges = np.linspace(20, 65, int(np.ceil(45 / args.cell_deg)) + 1)
    counts = {name: np.zeros((len(lat_edges)-1, len(lon_edges)-1), dtype=float)
              for name in names}
    radius_sums = {name: np.zeros_like(counts[name]) for name in names}
    radius_counts = {name: np.zeros_like(counts[name]) for name in names}
    amplitude_sums = {name: np.zeros_like(counts[name]) for name in names}
    amplitude_counts = {name: np.zeros_like(counts[name]) for name in names}
    exposures = {name: 0 for name in names}
    obs_dir = args.obs_root / "GLOENS" / "OBS" / "DETECT"

    def add_day(name, folder, prefix, date):
        lon_parts, lat_parts, radius_parts, amplitude_parts = [], [], [], []
        for polarity in POLARITIES:
            file = folder / f"{polarity}_{prefix}_{date}.nc"
            if not file.is_file():
                raise FileNotFoundError(f"Missing detection: {file}")
            lon, lat, radius, amplitude = read_centers(file)
            lon_parts.append(lon)
            lat_parts.append(lat)
            radius_parts.append(radius)
            amplitude_parts.append(amplitude)
        lon = np.concatenate(lon_parts)
        lat = np.concatenate(lat_parts)
        radius = np.concatenate(radius_parts)
        amplitude = np.concatenate(amplitude_parts)
        histogram, _, _ = np.histogram2d(lat, lon, bins=(lat_edges, lon_edges))
        counts[name][:] += histogram
        for values, sums, valid_counts in (
            (radius, radius_sums, radius_counts),
            (amplitude, amplitude_sums, amplitude_counts),
        ):
            valid = np.isfinite(values) & (values >= 0)
            weighted, _, _ = np.histogram2d(
                lat[valid], lon[valid], bins=(lat_edges, lon_edges),
                weights=values[valid])
            n_valid, _, _ = np.histogram2d(
                lat[valid], lon[valid], bins=(lat_edges, lon_edges))
            sums[name][:] += weighted
            valid_counts[name][:] += n_valid
        exposures[name] += 1

    for cycle, wed, thu in cycle_dates():
        for name, (key, model, _) in sources.items():
            init = thu if model == "GLOENS_MEAN" else wed
            folder, prefix = detect_dir(roots[key], cycle, model, init.strftime("%Y%m%d"))
            for lead in range(9):
                day = (init + pd.Timedelta(days=lead)).strftime("%Y%m%d")
                add_day(name, folder, prefix, day)
        for label, init in (("OBS_WED", wed), ("OBS_THU", thu)):
            for lead in range(9):
                day = (init + pd.Timedelta(days=lead)).strftime("%Y%m%d")
                add_day(label, obs_dir, "OBS", day)
        print(f"Detection heatmaps: processed {cycle}", flush=True)

    density = {name: counts[name] / exposures[name] for name in names}
    def cell_means(sums, valid_counts):
        return {
            name: np.divide(sums[name], valid_counts[name],
                            out=np.full_like(sums[name], np.nan),
                            where=valid_counts[name] > 0)
            for name in names
        }
    mean_radius = cell_means(radius_sums, radius_counts)
    mean_amplitude = cell_means(amplitude_sums, amplitude_counts)
    output = args.output_root / "COMPARISON_FULL" / "FIGURES"
    output.mkdir(parents=True, exist_ok=True)
    lon_centers = (lon_edges[:-1] + lon_edges[1:]) / 2
    lat_centers = (lat_edges[:-1] + lat_edges[1:]) / 2
    for prefix, values in (
        ("year2024_detection_heatmap", density),
        ("year2024_detection_radius", mean_radius),
        ("year2024_detection_amplitude", mean_amplitude),
    ):
        for name in names:
            pd.DataFrame(values[name], index=lat_centers, columns=lon_centers).to_csv(
                output / f"{prefix}_{name}.csv")

    def decorate(ax):
        ax.set_extent(BOUNDS, crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND.with_scale("110m"),
                       facecolor="#f2e9dd", edgecolor="none", zorder=3)
        ax.coastlines(resolution="110m", color="#252525", linewidth=0.65, zorder=4)
        grid = ax.gridlines(draw_labels={"bottom": True, "left": True},
                            linewidth=0.35, alpha=0.35, linestyle="--")
        grid.top_labels = False
        grid.right_labels = False
        grid.xlabel_style = {"size": 7}
        grid.ylabel_style = {"size": 7}

    cmap = plt.get_cmap("jet").copy()
    cmap.set_bad("#f2e9dd")
    projection = ccrs.PlateCarree()

    def plot_maps(values, prefix, title, color_label, max_value=None):
        if max_value is None:
            finite_max = [
                float(np.nanmax(a)) for a in values.values()
                if np.isfinite(a).any()
            ]
            if not finite_max:
                raise ValueError(f"No valid detection values for {prefix}")
            max_value = max(finite_max)
        max_value = max(max_value, 1e-12)
        ncols = 3
        nrows = int(np.ceil(len(names) / ncols))
        fig, axes = plt.subplots(nrows, ncols, figsize=(18, 4.4*nrows),
                                 subplot_kw={"projection": projection})
        for ax, name in zip(axes.flat, names):
            im = ax.pcolormesh(lon_edges, lat_edges, values[name], cmap=cmap,
                               vmin=0, vmax=max_value, transform=projection,
                               shading="auto", rasterized=True)
            decorate(ax)
            ax.set_title(labels.get(name, name), fontsize=10)
        for ax in list(axes.flat)[len(names):]:
            ax.set_visible(False)
        fig.colorbar(im, ax=[ax for ax in axes.flat if ax.get_visible()],
                     shrink=0.67, pad=0.025, label=color_label)
        fig.suptitle(f"2024 North Atlantic {title} — 52 cycles, 9 common days",
                     fontsize=16)
        fig.savefig(output / f"{prefix}_all.png", dpi=200, bbox_inches="tight")
        plt.close(fig)
        for name in names:
            fig, ax = plt.subplots(figsize=(12, 7),
                                   subplot_kw={"projection": projection})
            im = ax.pcolormesh(lon_edges, lat_edges, values[name], cmap=cmap,
                               vmin=0, vmax=max_value, transform=projection,
                               shading="auto", rasterized=True)
            decorate(ax)
            ax.set_title(f"2024 {title} — {labels.get(name, name)}")
            fig.colorbar(im, ax=ax, shrink=0.75, label=color_label)
            fig.savefig(output / f"{prefix}_{name}.png", dpi=220,
                        bbox_inches="tight")
            plt.close(fig)
        print(f"Saved {prefix}: {len(names)} maps and one comparison panel")

    plot_maps(density, "year2024_detection_heatmaps",
              "eddy detection density",
              "Mean detected eddy centers per grid cell per day",
              max_value=args.max_color)
    plot_maps(mean_radius, "year2024_detection_radius",
              "mean detected eddy effective radius",
              "Mean effective radius (km)")
    plot_maps(mean_amplitude, "year2024_detection_amplitude",
              "mean detected eddy amplitude",
              "Mean amplitude (cm)")
    print(f"All outputs saved to {output}")
    print("Each configuration uses 468 detection days (52 cycles x 9 days).")
    print("Radius and amplitude averages use valid detections within each cell.")
    print("OBS days are repeated across overlapping forecast windows by design.")

if __name__ == "__main__":
    main()
