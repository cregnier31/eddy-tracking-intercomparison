"""Animate daily GLOENS detections across ensemble members.

Example:
  python -m eddy_plot.gloens_detection_animation ./data --format gif

Uses Cartopy for land, coastlines, and labeled map gridlines. GIF uses Pillow.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import xarray as xr
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter

POLARITIES = (("Cyclonic", "tab:blue"), ("Anticyclonic", "tab:red"))


def detection_inventory(data_dir, first_member=1, last_member=50):
    """Map YYYYMMDD to polarity-specific file lists across members."""
    if not 1 <= first_member <= last_member <= 50:
        raise ValueError("Member range must be within 1..50")
    inventory = defaultdict(lambda: defaultdict(list))
    for member in range(first_member, last_member + 1):
        folder = Path(data_dir) / "GLOENS" / "MEMBERS" / f"member_{member:03d}" / "DETECT"
        for polarity, _ in POLARITIES:
            for path in sorted(folder.glob(f"{polarity}_GLOENS_????????.nc")):
                date = path.stem.rsplit("_", 1)[-1]
                inventory[date][polarity].append(path)
    return dict(sorted(inventory.items()))


def read_centers(path):
    """Read center coordinates from a py-eddy-tracker detection NetCDF."""
    with xr.open_dataset(path) as ds:
        if "longitude" not in ds or "latitude" not in ds:
            raise KeyError(f"{path}: expected longitude and latitude variables")
        lon = np.asarray(ds["longitude"].values, dtype=float).ravel()
        lat = np.asarray(ds["latitude"].values, dtype=float).ravel()
    if lon.shape != lat.shape:
        raise ValueError(f"{path}: mismatched center coordinate shapes")
    valid = np.isfinite(lon) & np.isfinite(lat)
    lon = ((lon[valid] + 180) % 360) - 180
    return np.column_stack((lon, lat))


def animate_detections(
    data_dir, output=None, first_member=1, last_member=50,
    lon_min=-80, lon_max=0, lat_min=20, lat_max=65,
    fps=2, dpi=130, fmt="gif", strict=True,
):
    """Create one animation frame per date, aggregating member detections."""
    if fps <= 0:
        raise ValueError("fps must be positive")
    if fmt not in ("gif", "mp4"):
        raise ValueError("format must be gif or mp4")
    inventory = detection_inventory(data_dir, first_member, last_member)
    if not inventory:
        raise FileNotFoundError("No GLOENS member detections found")

    dates = list(inventory)
    expected = last_member - first_member + 1
    if strict:
        incomplete = [
            (date, polarity, len(inventory[date].get(polarity, [])))
            for date in dates for polarity, _ in POLARITIES
            if len(inventory[date].get(polarity, [])) != expected
        ]
        if incomplete:
            date, polarity, found = incomplete[0]
            raise ValueError(
                f"Incomplete detections on {date}: {found}/{expected} {polarity} files"
            )

    # Load only small eddy-center arrays, not the SSH fields.
    frames = []
    for date in dates:
        centers = {}
        for polarity, _ in POLARITIES:
            chunks = [read_centers(path) for path in inventory[date].get(polarity, [])]
            centers[polarity] = np.concatenate(chunks) if chunks else np.empty((0, 2))
        frames.append(centers)
        print(f"{date}: " + ", ".join(
            f"{polarity}={len(centers[polarity])}" for polarity, _ in POLARITIES
        ), flush=True)

    # White scientific map: hollow eddy circles and subtle continental outlines.
    projection = ccrs.PlateCarree()
    fig = plt.figure(figsize=(13.5, 8), facecolor="white")
    ax = fig.add_axes((0.065, 0.12, 0.88, 0.75), projection=projection)
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=projection)
    ax.set_facecolor("white")
    ax.add_feature(cfeature.LAND.with_scale("110m"),
                   facecolor="#eeeeee", edgecolor="none", zorder=1)
    ax.coastlines(resolution="110m", linewidth=0.75,
                  color="#777777", zorder=5)
    gridlines = ax.gridlines(crs=projection, draw_labels=True,
                             linewidth=0.5, alpha=0.35,
                             color="#999999", linestyle="--")
    gridlines.top_labels = False
    gridlines.right_labels = False
    gridlines.xlabel_style = {"size": 9, "color": "#444444"}
    gridlines.ylabel_style = {"size": 9, "color": "#444444"}
    for spine in ax.spines.values():
        spine.set_edgecolor("#999999")
    fig.text(0.065, 0.94, "GLOENS | Ensemble Eddy Detections",
             fontsize=19, fontweight="bold", color="#222222")
    fig.text(0.065, 0.90,
             f"{len(dates)} forecast days | {last_member - first_member + 1} members",
             fontsize=11, color="#555555")
    scatters = {
        polarity: ax.scatter(
            [], [], s=17, alpha=0.55, facecolors="none",
            edgecolors=color, linewidths=0.75, label=polarity,
            transform=projection, zorder=7,
        )
        for polarity, color in POLARITIES
    }
    ax.legend(loc="lower left", facecolor="white",
              edgecolor="#cccccc", framealpha=0.95, fontsize=10)
    title = ax.text(
        0.985, 0.975, "", transform=ax.transAxes,
        ha="right", va="top", fontsize=11, color="#222222",
        bbox=dict(boxstyle="round,pad=0.45", facecolor="white",
                  edgecolor="#cccccc", alpha=0.96),
        zorder=12,
    )

    def update(i):
        centers = frames[i]
        for polarity, _ in POLARITIES:
            scatters[polarity].set_offsets(centers[polarity])
        title.set_text(
            f"GLOENS ensemble detections | {dates[i]} | "
            f"members {first_member:03d}–{last_member:03d}\n"
            + "  ".join(
                f"{polarity}: {len(centers[polarity])}"
                for polarity, _ in POLARITIES
            )
        )
        return (*scatters.values(), title)

    animation = FuncAnimation(fig, update, frames=len(dates),
                              interval=1000 / fps, blit=False, repeat=True)
    if output is None:
        output = Path(data_dir) / "GLOENS" / f"gloens_detection_ensemble.{fmt}"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        writer = PillowWriter(fps=fps) if fmt == "gif" else FFMpegWriter(fps=fps)
        animation.save(str(output), writer=writer, dpi=dpi)
    finally:
        plt.close(fig)
    print(f"Saved {len(dates)}-frame animation to {output}")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", help="Root containing GLOENS/MEMBERS")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--first-member", type=int, default=1)
    parser.add_argument("--last-member", type=int, default=50)
    parser.add_argument("--lon-min", type=float, default=-80)
    parser.add_argument("--lon-max", type=float, default=0)
    parser.add_argument("--lat-min", type=float, default=20)
    parser.add_argument("--lat-max", type=float, default=65)
    parser.add_argument("--fps", type=float, default=2)
    parser.add_argument("--dpi", type=int, default=130)
    parser.add_argument("--format", choices=("gif", "mp4"), default="gif")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args(argv)
    animate_detections(
        args.data_dir, output=args.output, first_member=args.first_member,
        last_member=args.last_member, lon_min=args.lon_min, lon_max=args.lon_max,
        lat_min=args.lat_min, lat_max=args.lat_max, fps=args.fps, dpi=args.dpi,
        fmt=args.format, strict=not args.allow_incomplete,
    )


if __name__ == "__main__":
    main()
