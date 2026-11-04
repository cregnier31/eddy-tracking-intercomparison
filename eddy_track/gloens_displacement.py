"""Compute 28-day eddy center displacement from GLOENS member tracks.

Example:
  python -m eddy_track.gloens_displacement ./data --days 28
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr


def haversine_km(lon1, lat1, lon2, lat2):
    """Great-circle distance in kilometers, with longitude wrapping."""
    lon1, lat1, lon2, lat2 = np.broadcast_arrays(
        *[np.asarray(v, dtype=float) for v in (lon1, lat1, lon2, lat2)]
    )
    dlambda = np.deg2rad((lon2 - lon1 + 180) % 360 - 180)
    dphi = np.deg2rad(lat2 - lat1)
    a = np.sin(dphi / 2) ** 2 + (
        np.cos(np.deg2rad(lat1)) * np.cos(np.deg2rad(lat2))
        * np.sin(dlambda / 2) ** 2
    )
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def track_statistics(path, member, polarity, days, start_date, gulf_stream):
    with xr.open_dataset(path) as ds:
        required = ("track", "time", "longitude", "latitude", "observation_flag")
        missing = [name for name in required if name not in ds]
        if missing:
            raise KeyError(f"{path}: missing {missing}")
        tracks = np.asarray(ds.track.values)
        times = np.asarray(ds.time.values).astype("datetime64[D]")
        lon = np.asarray(ds.longitude.values, dtype=float)
        lat = np.asarray(ds.latitude.values, dtype=float)
        flags = np.asarray(ds.observation_flag.values)
    first_day = np.datetime64(start_date, "D")
    target = first_day + np.arange(days).astype("timedelta64[D]")
    valid = ((flags == 0) & np.isfinite(lon) & np.isfinite(lat)
             & np.isin(times, target))
    rows = []
    for track_id in np.unique(tracks[valid]):
        idx = np.flatnonzero(valid & (tracks == track_id))
        order = np.argsort(times[idx])
        idx = idx[order]
        # Exactly one real observation on each requested day.
        if len(idx) != days or not np.array_equal(times[idx], target):
            continue
        path_km = float(np.sum(haversine_km(
            lon[idx[:-1]], lat[idx[:-1]], lon[idx[1:]], lat[idx[1:]]
        )))
        net_km = float(haversine_km(lon[idx[0]], lat[idx[0]],
                                    lon[idx[-1]], lat[idx[-1]]))
        gs_lon_min, gs_lon_max, gs_lat_min, gs_lat_max = gulf_stream
        in_gulf_stream = (
            gs_lon_min <= lon[idx[0]] <= gs_lon_max
            and gs_lat_min <= lat[idx[0]] <= gs_lat_max
        )
        rows.append(dict(
            member=member, polarity=polarity, track=int(track_id),
            start_date=str(times[idx[0]]), end_date=str(times[idx[-1]]),
            start_lon=float(lon[idx[0]]), start_lat=float(lat[idx[0]]),
            end_lon=float(lon[idx[-1]]), end_lat=float(lat[idx[-1]]),
            net_displacement_km=net_km, path_length_km=path_km,
            mean_path_speed_cm_s=path_km * 100000 / ((days - 1) * 86400),
            gulf_stream_start=in_gulf_stream,
        ))
    return rows


def summarize(df, label):
    print(f"\n{label} — {len(df)} qualifying tracks")
    if df.empty:
        return
    for column in ("net_displacement_km", "path_length_km", "mean_path_speed_cm_s"):
        print(f"  {column}: mean={df[column].mean():.2f}, "
              f"median={df[column].median():.2f}, "
              f"std={df[column].std():.2f}, "
              f"min={df[column].min():.2f}, max={df[column].max():.2f}")
    for polarity, group in df.groupby("polarity"):
        print(f"  {polarity}: n={len(group)}, "
              f"mean net displacement={group.net_displacement_km.mean():.2f} km")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir")
    parser.add_argument("--first-member", type=int, default=1)
    parser.add_argument("--last-member", type=int, default=50)
    parser.add_argument("--days", type=int, default=28)
    parser.add_argument("--start-date", default="2026-10-22")
    parser.add_argument("--gulf-stream", nargs=4, type=float,
                        metavar=("LON_MIN", "LON_MAX", "LAT_MIN", "LAT_MAX"),
                        default=(-75, -45, 35, 45),
                        help="Gulf Stream box; membership determined by first-day center")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.days < 2 or not 1 <= args.first_member <= args.last_member <= 50:
        parser.error("Need at least two days and member range within 1..50")
    rows = []
    for member in range(args.first_member, args.last_member + 1):
        for polarity in ("Cyclonic", "Anticyclonic"):
            path = (Path(args.data_dir) / "GLOENS" / "MEMBERS"
                    / f"member_{member:03d}" / "TRACK" / f"{polarity}.nc")
            if not path.exists():
                raise FileNotFoundError(f"Missing tracking file: {path}")
            rows.extend(track_statistics(
                path, member, polarity, args.days,
                args.start_date, args.gulf_stream,
            ))
    df = pd.DataFrame(rows, columns=[
        "member", "polarity", "track", "start_date", "end_date",
        "start_lon", "start_lat", "end_lon", "end_lat",
        "net_displacement_km", "path_length_km",
        "mean_path_speed_cm_s", "gulf_stream_start",
    ])
    summarize(df, "All selected members and regions")
    summarize(df[df.gulf_stream_start], "Gulf Stream box (initial center)")
    output = args.output or (Path(args.data_dir) / "GLOENS" / "eddy_displacement_28d.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"\nSaved individual track statistics: {output}")


if __name__ == "__main__":
    main()
