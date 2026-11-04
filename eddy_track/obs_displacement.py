"""Compute observational 28-day eddy displacement with GLOENS-identical metrics.

Example:
  python -m eddy_track.obs_displacement ./data --start-date 2026-09-24 --days 28
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from eddy_track.gloens_displacement import track_statistics, summarize

COLUMNS = [
    "member", "polarity", "track", "start_date", "end_date",
    "start_lon", "start_lat", "end_lon", "end_lat",
    "net_displacement_km", "path_length_km",
    "mean_path_speed_cm_s", "gulf_stream_start",
]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir")
    parser.add_argument("--start-date", default="2026-09-24")
    parser.add_argument("--days", type=int, default=28)
    parser.add_argument("--gulf-stream", nargs=4, type=float,
                        metavar=("LON_MIN", "LON_MAX", "LAT_MIN", "LAT_MAX"),
                        default=(-75, -45, 35, 45))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.days < 2:
        parser.error("--days must be at least 2")
    root = Path(args.data_dir) / "GLOENS" / "OBS"
    rows = []
    for polarity in ("Cyclonic", "Anticyclonic"):
        path = root / "TRACK" / f"{polarity}.nc"
        if not path.exists():
            raise FileNotFoundError(f"Missing observation tracking file: {path}")
        rows.extend(track_statistics(
            path, "OBS", polarity, args.days, args.start_date,
            args.gulf_stream,
        ))
    df = pd.DataFrame(rows, columns=COLUMNS)
    summarize(df, "OBS — North Atlantic")
    summarize(df[df.gulf_stream_start], "OBS — Gulf Stream box (initial center)")
    output = args.output or root / f"obs_displacement_{args.days}d.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"Saved individual observed eddy statistics: {output}", flush=True)


if __name__ == "__main__":
    main()
