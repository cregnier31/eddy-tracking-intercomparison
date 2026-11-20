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
    try:
        with xr.open_dataset(path) as ds:
            if "longitude" not in ds or "latitude" not in ds:
                raise ValueError(f"{path}: longitude/latitude variables missing")
            lon = np.asarray(ds["longitude"].values).ravel()
            lat = np.asarray(ds["latitude"].values).ravel()
    except Exception as exc:
        raise RuntimeError(f"Cannot read detection file {path}") from exc
    if lon.size != lat.size:
        raise ValueError(f"{path}: inconsistent longitude/latitude sizes")
    lon = ((lon + 180.) % 360.) - 180.
    ok = np.isfinite(lon) & np.isfinite(lat)
    return lon[ok], lat[ok]

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
    labels["OBS_WED"] = "AVISO / OBS (Wednesday)"
    labels["OBS_THU"] = "AVISO / OBS (Thursday)"
    names = list(sources) + ["OBS_WED", "OBS_THU"]

    lon_edges = np.linspace(-80, 0, int(np.ceil(80 / args.cell_deg)) + 1)
    lat_edges = np.linspace(20, 65, int(np.ceil(45 / args.cell_deg)) + 1)
    counts = {name: np.zeros((len(lat_edges)-1, len(lon_edges)-1), dtype=float)
              for name in names}
    exposures = {name: 0 for name in names}
    obs_dir = args.obs_root / "GLOENS" / "OBS" / "DETECT"

    def add_day(name, folder, prefix, date):
        lon_parts, lat_parts = [], []
        for polarity in POLARITIES:
            file = folder / f"{polarity}_{prefix}_{date}.nc"
            if not file.is_file():
                raise FileNotFoundError(f"Missing detection: {file}")
            lon, lat = read_centers(file)
            lon_parts.append(lon)
            lat_parts.append(lat)
        lon = np.concatenate(lon_parts)
        lat = np.concatenate(lat_parts)
        histogram, _, _ = np.histogram2d(lat, lon, bins=(lat_edges, lon_edges))
        counts[name][:] += histogram
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
    maximum = args.max_color or max(float(np.max(x)) for x in density.values())
    maximum = max(maximum, 1e-12)
    output = args.output_root / "COMPARISON_FULL" / "FIGURES"
    output.mkdir(parents=True, exist_ok=True)
    lon_centers = (lon_edges[:-1] + lon_edges[1:]) / 2
    lat_centers = (lat_edges[:-1] + lat_edges[1:]) / 2
    for name in names:
        pd.DataFrame(density[name], index=lat_centers, columns=lon_centers).to_csv(
            output / f"year2024_detection_heatmap_{name}.csv")

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
    fig, axes = plt.subplots(3, 3, figsize=(18, 13),
                             subplot_kw={"projection": projection})
    for ax, name in zip(axes.flat, names):
        im = ax.pcolormesh(lon_edges, lat_edges, density[name], cmap=cmap,
                           vmin=0, vmax=maximum, transform=projection,
                           shading="auto", rasterized=True)
        decorate(ax)
        ax.set_title(labels.get(name, name), fontsize=10)
    for ax in list(axes.flat)[len(names):]:
        ax.set_visible(False)
    fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.67, pad=0.025,
                 label="Mean detected eddy centers per grid cell per day")
    fig.suptitle("2024 North Atlantic eddy detection density — 52 cycles, 9 common days",
                 fontsize=16)
    fig.savefig(output / "year2024_detection_heatmaps_all.png",
                dpi=200, bbox_inches="tight")
    plt.close(fig)

    for name in names:
        fig, ax = plt.subplots(figsize=(12, 7), subplot_kw={"projection": projection})
        im = ax.pcolormesh(lon_edges, lat_edges, density[name], cmap=cmap,
                           vmin=0, vmax=maximum, transform=projection,
                           shading="auto", rasterized=True)
        decorate(ax)
        ax.set_title(f"2024 eddy detection density — {labels.get(name, name)}")
        fig.colorbar(im, ax=ax, shrink=0.75,
                     label="Mean detected eddy centers per grid cell per day")
        fig.savefig(output / f"year2024_detection_heatmap_{name}.png",
                    dpi=220, bbox_inches="tight")
        plt.close(fig)
    print(f"Saved {len(names)} heatmaps + comparison panel to {output}")
    print("Each configuration uses 468 detection days (52 cycles x 9 days).")
    print("OBS days are repeated across overlapping forecast windows by design.")

if __name__ == "__main__":
    main()
