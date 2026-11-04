"""Animate daily Copernicus observational eddy detections.

Examples:
  python -m eddy_plot.obs_detection_animation ./data_sep2026 --mode shape
  python -m eddy_plot.obs_detection_animation ./data_sep2026 --mode center
  python -m eddy_plot.obs_detection_animation ./data_sep2026 --min-consecutive-days 28
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
from matplotlib.collections import LineCollection

from eddy_detect.observations import date_strings
from eddy_plot.gloens_detection_animation import POLARITIES, read_centers, read_contours


def frames_from_tracks(root, dates, mode, min_days):
    frames = {date: {p: [] for p, _ in POLARITIES} for date in dates}
    requested = np.array([np.datetime64(f"{d[:4]}-{d[4:6]}-{d[6:]}") for d in dates])
    for polarity, _ in POLARITIES:
        file = root / "TRACK" / f"{polarity}.nc"
        if not file.exists():
            raise FileNotFoundError(file)
        with xr.open_dataset(file) as ds:
            ids = np.asarray(ds.track.values)
            times = np.asarray(ds.time.values).astype("datetime64[D]")
            flags = np.asarray(ds.observation_flag.values)
            real = (flags == 0) & np.isin(times, requested)
            keep = np.zeros(len(ids), dtype=bool)
            for track_id in np.unique(ids[real]):
                indices = np.flatnonzero(real & (ids == track_id))
                days = np.unique(times[indices]).astype("int64")
                run = longest = 1
                for delta in np.diff(days):
                    run = run + 1 if delta == 1 else 1
                    longest = max(longest, run)
                if longest >= min_days:
                    keep[indices] = True
            if mode == "center":
                lon = np.asarray(ds.longitude.values, dtype=float)
                lat = np.asarray(ds.latitude.values, dtype=float)
                for date in dates:
                    day = np.datetime64(f"{date[:4]}-{date[4:6]}-{date[6:]}")
                    mask = keep & (times == day) & np.isfinite(lon) & np.isfinite(lat)
                    frames[date][polarity].extend(
                        np.column_stack((((lon[mask] + 180) % 360) - 180, lat[mask]))
                    )
            else:
                pairs = (("effective_contour_longitude", "effective_contour_latitude"),
                         ("speed_contour_longitude", "speed_contour_latitude"))
                pair = next(((x, y) for x, y in pairs if x in ds and y in ds), None)
                if pair is None:
                    raise KeyError(f"No contour coordinates in {file}")
                lons = np.asarray(ds[pair[0]].values, dtype=float)
                lats = np.asarray(ds[pair[1]].values, dtype=float)
                for i in np.flatnonzero(keep):
                    valid = np.isfinite(lons[i]) & np.isfinite(lats[i])
                    if valid.sum() < 3:
                        continue
                    lon = ((lons[i, valid] + 180) % 360) - 180
                    if np.any(np.abs(np.diff(lon)) > 180):
                        continue
                    vertices = np.column_stack((lon, lats[i, valid]))
                    if not np.allclose(vertices[0], vertices[-1]):
                        vertices = np.vstack((vertices, vertices[0]))
                    date = np.datetime_as_string(times[i], unit="D").replace("-", "")
                    frames[date][polarity].append(vertices)
    return [
        {p: (np.asarray(frames[d][p]).reshape(-1, 2) if mode == "center"
             else frames[d][p]) for p, _ in POLARITIES}
        for d in dates
    ]


def animate(data_dir, start, end, mode="shape", output=None,
            min_consecutive_days=0, lon_min=-80, lon_max=0,
            lat_min=20, lat_max=65, fps=2, dpi=130, fmt="gif"):
    if fps <= 0 or min_consecutive_days < 0:
        raise ValueError("fps must be positive and min-consecutive-days nonnegative")
    root = Path(data_dir) / "GLOENS" / "OBS"
    dates = date_strings(start, end)
    if min_consecutive_days:
        frames = frames_from_tracks(root, dates, mode, min_consecutive_days)
    else:
        frames = []
        for date in dates:
            frame = {}
            for polarity, _ in POLARITIES:
                path = root / "DETECT" / f"{polarity}_OBS_{date}.nc"
                if not path.exists():
                    raise FileNotFoundError(path)
                frame[polarity] = read_contours(path) if mode == "shape" else read_centers(path)
            frames.append(frame)
    projection = ccrs.PlateCarree()
    fig = plt.figure(figsize=(13.5, 8), facecolor="white")
    ax = fig.add_axes((0.065, 0.12, 0.88, 0.75), projection=projection)
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=projection)
    ax.set_facecolor("white")
    ax.add_feature(cfeature.LAND.with_scale("10m"),
                   facecolor="#eeeeee", edgecolor="none", zorder=9)
    ax.coastlines(resolution="10m", linewidth=0.75, color="#777777", zorder=10)
    gl = ax.gridlines(crs=projection, draw_labels=True,
                      linewidth=0.5, alpha=0.35, color="#999999", linestyle="--")
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 9, "color": "#444444"}
    gl.ylabel_style = {"size": 9, "color": "#444444"}
    fig.text(0.065, 0.94, "Copernicus Marine | Observed Eddy Detections",
             fontsize=19, fontweight="bold", color="#222222")
    fig.text(0.065, 0.90, f"{start} to {end} | {len(dates)} days",
             fontsize=11, color="#555555")
    if mode == "shape":
        artists = {
            p: LineCollection([], colors=[color], linewidths=0.8, alpha=0.75,
                              transform=projection, zorder=7, label=p)
            for p, color in POLARITIES
        }
        for artist in artists.values():
            ax.add_collection(artist)
    else:
        artists = {
            p: ax.scatter([], [], s=9, alpha=0.8, c=color,
                          edgecolors="none", transform=projection, zorder=7, label=p)
            for p, color in POLARITIES
        }
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.065), ncol=2,
              facecolor="white", edgecolor="none", frameon=False, fontsize=11)
    label = ax.text(
        0.985, -0.065, "", transform=ax.transAxes, ha="right", va="top",
        fontsize=10, color="#222222",
        bbox=dict(boxstyle="round,pad=0.45", facecolor="white",
                  edgecolor="#cccccc", alpha=0.96), zorder=12,
    )

    def update(i):
        for polarity, _ in POLARITIES:
            if mode == "shape":
                artists[polarity].set_segments(frames[i][polarity])
            else:
                artists[polarity].set_offsets(frames[i][polarity])
        label.set_text(
            f"OBS | {dates[i]}\n" +
            "  ".join(f"{p}: {len(frames[i][p])}" for p, _ in POLARITIES)
        )
        return (*artists.values(), label)

    animation = FuncAnimation(fig, update, frames=len(dates),
                              interval=1000 / fps, blit=False, repeat=True)
    if output is None:
        suffix = f"_min{min_consecutive_days}d" if min_consecutive_days else ""
        output = root / f"obs_detection_{mode}{suffix}.{fmt}"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        writer = PillowWriter(fps=fps) if fmt == "gif" else FFMpegWriter(fps=fps)
        animation.save(str(output), writer=writer, dpi=dpi)
    finally:
        plt.close(fig)
    print(f"Saved {len(dates)} frames to {output}", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir")
    parser.add_argument("--start", default="2026-09-24")
    parser.add_argument("--end", default="2026-10-21")
    parser.add_argument("--mode", choices=("shape", "center"), default="shape")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-consecutive-days", type=int, default=0)
    parser.add_argument("--lon-min", type=float, default=-80)
    parser.add_argument("--lon-max", type=float, default=0)
    parser.add_argument("--lat-min", type=float, default=20)
    parser.add_argument("--lat-max", type=float, default=65)
    parser.add_argument("--fps", type=float, default=2)
    parser.add_argument("--dpi", type=int, default=130)
    parser.add_argument("--format", choices=("gif", "mp4"), default="gif")
    args = parser.parse_args(argv)
    animate(args.data_dir, args.start, args.end, args.mode, args.output,
            args.min_consecutive_days, args.lon_min, args.lon_max,
            args.lat_min, args.lat_max, args.fps, args.dpi, args.format)


if __name__ == "__main__":
    main()
