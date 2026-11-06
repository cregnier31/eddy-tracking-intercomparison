"""Four model-vs-observation contour animations using the project's existing map style.

Uses eddy_plot.gloens_detection_animation.read_contours and
eddy_plot.obs_detection_animation.frames_from_tracks for identical shape handling.
No center markers or correspondence lines.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import numpy as np
import xarray as xr
from eddy_plot.gloens_detection_animation import read_contours, POLARITIES
from eddy_plot.obs_detection_animation import frames_from_tracks

MODELS = {
    "GLONET": ("GLONET/20240717", "GLONET", "2024-07-17", 10),
    "GLOW": ("GLOW/20240717", "GLOW", "2024-07-17", 9),
    "GLO12": ("GLO12/20240717", "GLO12", "2024-07-17", 10),
    "GLOENS_MEAN": ("GLOENS", "GLOENS", "2024-07-18", 28),
}


def model_frames(root, dates, polarity, min_days):
    """Extract shapes from tracked observations, requiring consecutive real days."""
    from eddy_plot.obs_detection_animation import frames_from_tracks
    return frames_from_tracks(root, dates, "shape", min_days)


def animate(data_dir, models, output_dir, min_days, fps, dpi, bounds):
    projection = ccrs.PlateCarree()
    output_dir.mkdir(parents=True, exist_ok=True)
    for model in models:
        relative, tag, start, days = MODELS[model]
        root = data_dir / relative
        dates = [(np.datetime64(start) + np.timedelta64(i, "D")).astype(str).replace("-", "")
                 for i in range(days)]
        if min_days > days:
            raise ValueError(f"{model} only has {days} days; --min-consecutive-days {min_days} is impossible")
        obs_root = data_dir / "GLOENS/OBS"
        if min_days:
            model_data = model_frames(root, dates, None, min_days)
            obs_data = frames_from_tracks(obs_root, dates, "shape", min_days)
        else:
            model_data, obs_data = [], []
            for date in dates:
                model_data.append({p: read_contours(root / "DETECT" / f"{p}_{tag}_{date}.nc")
                                   for p, _ in POLARITIES})
                obs_data.append({p: read_contours(obs_root / "DETECT" / f"{p}_OBS_{date}.nc")
                                 for p, _ in POLARITIES})
        if not any(model_data[0][p] or obs_data[0][p] for p, _ in POLARITIES):
            raise ValueError(f"{model}: no shapes in first frame; inspect detection/track files")
        fig = plt.figure(figsize=(13.5, 8), facecolor="white")
        ax = fig.add_axes((0.065, 0.12, 0.88, 0.75), projection=projection)
        ax.set_extent(bounds, crs=projection)
        ax.set_facecolor("white")
        ax.add_feature(cfeature.LAND.with_scale("10m"), facecolor="#eeeeee",
                       edgecolor="none", zorder=9)
        ax.coastlines(resolution="10m", linewidth=.75, color="#777777", zorder=10)
        gl = ax.gridlines(crs=projection, draw_labels=True, linewidth=.5,
                          alpha=.35, color="#999999", linestyle="--")
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {"size": 9, "color": "#444444"}
        gl.ylabel_style = {"size": 9, "color": "#444444"}
        fig.text(.065, .94, f"{model} | Model vs Observed Eddy Shapes",
                 fontsize=19, fontweight="bold", color="#222222")
        fig.text(.065, .90, f"{start} | {days} forecast days | "
                 f"minimum persistence {min_days} days", fontsize=11, color="#555555")
        artists = {}
        for p, color in POLARITIES:
            for source, linestyle, alpha, width in (
                ("OBS", "solid", .85, 1.0), ("MODEL", "dashed", .65, .8)
            ):
                artist = LineCollection([], colors=[color], linestyles=linestyle,
                                        linewidths=width, alpha=alpha,
                                        transform=projection, zorder=7)
                ax.add_collection(artist)
                artists[(p, source)] = artist
        legend = [Line2D([0], [0], color=color, label=p) for p, color in POLARITIES]
        legend += [Line2D([0], [0], color="#555555", linestyle="solid", label="OBS"),
                   Line2D([0], [0], color="#555555", linestyle="dashed", label="Model")]
        ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(0, -.065),
                  ncol=4, facecolor="white", edgecolor="none", frameon=False, fontsize=11)
        label = ax.text(.985, -.065, "", transform=ax.transAxes, ha="right", va="top",
                        fontsize=10, color="#222222",
                        bbox=dict(boxstyle="round,pad=0.45", facecolor="white",
                                  edgecolor="#cccccc", alpha=.96), zorder=12)
        def update(i):
            for p, _ in POLARITIES:
                artists[(p, "OBS")].set_segments(obs_data[i][p])
                artists[(p, "MODEL")].set_segments(model_data[i][p])
            label.set_text(f"{model} vs OBS | {dates[i]}\n" +
                           "  ".join(f"{p}: model {len(model_data[i][p])} / "
                                    f"obs {len(obs_data[i][p])}" for p, _ in POLARITIES))
            return (*artists.values(), label)
        animation = FuncAnimation(fig, update, frames=days, interval=1000/fps,
                                  blit=False, repeat=True)
        path = output_dir / f"{model}_vs_OBS_shapes.gif"
        try:
            animation.save(path, writer=PillowWriter(fps=fps), dpi=dpi)
        finally:
            plt.close(fig)
        print(f"Saved {days} frames to {path}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--models", nargs="+", choices=tuple(MODELS), default=list(MODELS))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--min-consecutive-days", type=int, default=0)
    parser.add_argument("--fps", type=float, default=2)
    parser.add_argument("--dpi", type=int, default=130)
    parser.add_argument("--lon-min", type=float, default=-80)
    parser.add_argument("--lon-max", type=float, default=0)
    parser.add_argument("--lat-min", type=float, default=20)
    parser.add_argument("--lat-max", type=float, default=65)
    args = parser.parse_args()
    if args.fps <= 0 or args.min_consecutive_days < 0:
        parser.error("fps must be positive and min-consecutive-days nonnegative")
    animate(args.data_dir, args.models,
            args.output_dir or args.data_dir / "COMPARISON/ANIMATIONS",
            args.min_consecutive_days, args.fps, args.dpi,
            [args.lon_min, args.lon_max, args.lat_min, args.lat_max])


if __name__ == "__main__":
    main()
