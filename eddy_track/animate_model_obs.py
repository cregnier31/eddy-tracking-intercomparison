"""Animate daily model and observed eddy detections for four forecasts.

Uses detection contours (effective contour when available); no center markers.
Writes GIFs via PillowWriter and uses Cartopy for land and coastlines.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import xarray as xr

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
except ImportError:
    ccrs = None
    cfeature = None

MODELS = {
    "GLONET": ("GLONET/20240717/DETECT", "GLONET", "2024-07-17", 10, "GLONET_20240717"),
    "GLOW": ("GLOW/20240717/DETECT", "GLOW", "2024-07-17", 9, "GLOW_20240717"),
    "GLO12": ("GLO12/20240717/DETECT", "GLO12", "2024-07-17", 10, "GLO12_20240717"),
    "GLOENS_MEAN": ("GLOENS/DETECT", "GLOENS", "2024-07-18", 28, "20240718_28d"),
}
POLARITIES = ("Cyclonic", "Anticyclonic")
COLORS = {"Cyclonic": "#2878b5", "Anticyclonic": "#d24a38"}


def read_detection(path: Path):
    """Return a list of valid contour polygons; fail if layout is unsupported."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing detection file: {path}")
    with xr.open_dataset(path) as ds:
        names = set(ds.variables)
        candidates = (
            ("contour_lon_e", "contour_lat_e"),
            ("contour_lon_s", "contour_lat_s"),
        )
        pair = next(((x, y) for x, y in candidates if x in names and y in names), None)
        if pair is None:
            raise ValueError(
                f"{path}: no recognized contour coordinates. "
                f"Available variables: {sorted(names)}"
            )
        xvar, yvar = ds[pair[0]], ds[pair[1]]
        x = np.asarray(xvar.values, dtype=float)
        y = np.asarray(yvar.values, dtype=float)
        if x.shape != y.shape:
            raise ValueError(f"{path}: contour longitude/latitude shapes differ: "
                             f"{x.shape} vs {y.shape}")
        if x.ndim == 1:
            x, y = x[None, :], y[None, :]
        elif x.ndim == 2:
            # py_eddy_tracker typically stores (observation, contour_sample).
            # Use dimension names when available to identify transposed arrays.
            first, second = xvar.dims
            if ("sample" in first.lower() or "point" in first.lower()
                    or "contour" in first.lower()) and (
                    "obs" in second.lower() or "eddy" in second.lower()):
                x, y = x.T, y.T
        else:
            raise ValueError(f"{path}: unsupported contour dimensions "
                             f"{xvar.dims} with shape {x.shape}")
        polygons = []
        for px, py in zip(x, y):
            good = np.isfinite(px) & np.isfinite(py)
            if good.sum() >= 3:
                polygons.append((px[good], py[good]))
        print(f"{path.name}: {len(polygons)} drawable contours "
              f"({pair[0]}, dims={xvar.dims}, shape={xvar.shape})", flush=True)
        return polygons


def draw_eddies(ax, polygons, polarity, observed):
    color = COLORS[polarity]
    for x, y in polygons:
        ax.plot(x, y, color=color, transform=ccrs.PlateCarree(),
                linewidth=1.1 if observed else .8,
                linestyle="-" if observed else "--",
                alpha=.85 if observed else .65, zorder=3)



def animate(data_dir: Path, comparison_dir: Path, output_dir: Path,
            models, fps: int, lon_min: float, lon_max: float,
            lat_min: float, lat_max: float):
    output_dir.mkdir(parents=True, exist_ok=True)
    for model in models:
        model_relative, model_tag, first_date, days, comparison_name = MODELS[model]
        matches_path = comparison_dir / comparison_name / "matched_positions.csv"
        if not matches_path.is_file():
            raise FileNotFoundError(f"Missing {matches_path}; run full-period comparison first")
        matched = pd.read_csv(matches_path)
        matched = matched[matched.model == model]
        dates = pd.date_range(first_date, periods=days, freq="D")
        frames = []
        for date in dates:
            date_text = date.strftime("%Y%m%d")
            per_day = {}
            for polarity in POLARITIES:
                model_file = (data_dir / model_relative /
                              f"{polarity}_{model_tag}_{date_text}.nc")
                obs_file = (data_dir / "GLOENS/OBS/DETECT" /
                            f"{polarity}_OBS_{date_text}.nc")
                per_day[(polarity, "model")] = read_detection(model_file)
                per_day[(polarity, "obs")] = read_detection(obs_file)
            if not any(per_day.values()):
                raise ValueError(f"{model} {date_text}: no drawable contours in either dataset")
            frames.append(per_day)
        if ccrs is None:
            raise ImportError("Cartopy is required for coastline maps. Check the existing environment with: python -c 'import cartopy'")
        projection = ccrs.PlateCarree()
        fig, ax = plt.subplots(figsize=(11, 7), constrained_layout=True,
                               subplot_kw={"projection": projection})
        legend = [
            Line2D([0], [0], color=COLORS[p], linewidth=2, label=p)
            for p in POLARITIES
        ] + [
            Line2D([0], [0], color="#444", linestyle="-", label="Observation contour"),
            Line2D([0], [0], color="#444", linestyle="--", label="Model contour"),
        ]

        def update(i):
            ax.clear()
            date = dates[i]
            day = frames[i]
            for polarity in POLARITIES:
                draw_eddies(ax, day[(polarity, "model")], polarity, False)
                draw_eddies(ax, day[(polarity, "obs")], polarity, True)
            ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=projection)
            ax.add_feature(cfeature.LAND.with_scale("110m"),
                           facecolor="#eeeeee", edgecolor="none", zorder=0)
            ax.coastlines(resolution="110m", linewidth=.65,
                          color="#777777", zorder=1)
            gl = ax.gridlines(draw_labels=True, linewidth=.45,
                              alpha=.35, linestyle=":")
            gl.top_labels = False
            gl.right_labels = False
            ax.legend(handles=legend, loc="upper right", fontsize=8,
                      framealpha=.93, ncol=2)
            ax.set_title(f"{model} vs Copernicus ADT | {date:%Y-%m-%d} | "
                         f"forecast day {i+1}/{days}\n"
                         "Detected eddy contours (no center markers)", fontsize=12)
            return []

        animation = FuncAnimation(fig, update, frames=days,
                                  interval=1000 / fps, blit=False, repeat=True)
        destination = output_dir / f"{model}_vs_OBS.gif"
        animation.save(destination, writer=PillowWriter(fps=fps), dpi=110)
        plt.close(fig)
        print(f"Saved {destination} ({days} frames)", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--comparison-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--models", nargs="+", choices=tuple(MODELS),
                        default=list(MODELS))
    parser.add_argument("--fps", type=int, default=2)
    parser.add_argument("--lon-min", type=float, default=-80)
    parser.add_argument("--lon-max", type=float, default=0)
    parser.add_argument("--lat-min", type=float, default=20)
    parser.add_argument("--lat-max", type=float, default=65)
    args = parser.parse_args()
    if args.fps < 1 or args.lon_min >= args.lon_max or args.lat_min >= args.lat_max:
        parser.error("Invalid fps or map bounds")
    animate(args.data_dir,
            args.comparison_dir or args.data_dir / "COMPARISON",
            args.output_dir or args.data_dir / "COMPARISON/ANIMATIONS",
            args.models, args.fps, args.lon_min, args.lon_max,
            args.lat_min, args.lat_max)


if __name__ == "__main__":
    main()
