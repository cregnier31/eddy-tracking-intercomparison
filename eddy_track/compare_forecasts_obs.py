"""Compare four forecast track products with Copernicus ADT tracked eddies.

One-to-one initial center matching, fixed track IDs, and daily position errors.
Virtual tracker observations are excluded. The four-system window is based on
valid dates, not identical forecast lead times.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from eddy_track.match_obs_gloens import (
    POLARITIES, initial_matches, read_tracks,
)
from eddy_track.gloens_displacement import haversine_km

MODELS = {
    "GLONET": ("GLONET/20240717/TRACK", "2024-07-17"),
    "GLOW": ("GLOW/20240717/TRACK", "2024-07-17"),
    "GLO12": ("GLO12/20240717/TRACK", "2024-07-17"),
    "GLOENS_MEAN": ("GLOENS/TRACK", "2024-07-18"),
}


def compare(data_dir: Path, start: str, days: int, max_distance_km: float,
            output_dir: Path, models: tuple[str, ...], init_dates=None, track_subdir="TRACK"):
    if days < 1 or max_distance_km <= 0:
        raise ValueError("days must be positive and max-distance-km > 0")
    output_dir.mkdir(parents=True, exist_ok=True)
    start_day = np.datetime64(start, "D")
    obs_dir = data_dir / "GLOENS/OBS/TRACK"
    observations = {
        pol: read_tracks(obs_dir / f"{pol}.nc", start, days)
        for pol in POLARITIES
    }
    matches_rows, daily_rows, summary_rows = [], [], []
    for model in models:
        relative_dir, init_date = MODELS[model]
        if init_dates is not None:
            init_date = init_dates[model]
            relative_dir = ("GLOENS/TRACK" if model == "GLOENS_MEAN"
                            else f"{model}/{init_date.replace('-', '')}/TRACK")
        model_dir = data_dir / relative_dir
        if track_subdir != "TRACK":
            model_dir = model_dir.parent / track_subdir
        init_day = np.datetime64(init_date, "D")
        for polarity in POLARITIES:
            obs = observations[polarity]
            predicted = read_tracks(model_dir / f"{polarity}.nc", start, days)
            matches = initial_matches(obs, predicted, max_distance_km)
            nobs = sum(0 in track for track in obs.values())
            nmodel = sum(0 in track for track in predicted.values())
            summary_rows.append({
                "model": model, "polarity": polarity, "start_date": start,
                "days": days, "observed_initial_tracks": nobs,
                "model_initial_tracks": nmodel, "matched_initial_tracks": len(matches),
                "obs_initial_match_percent": 100 * len(matches) / nobs if nobs else np.nan,
                "model_initial_match_percent": 100 * len(matches) / nmodel if nmodel else np.nan,
            })
            for obs_id, model_id, initial_error in matches:
                obs_positions = obs[obs_id]
                model_positions = predicted[model_id]
                matches_rows.append({
                    "model": model, "polarity": polarity,
                    "obs_track": obs_id, "model_track": model_id,
                    "initial_error_km": initial_error,
                })
                for day in range(days):
                    date = start_day + np.timedelta64(day, "D")
                    observed = obs_positions.get(day)
                    modeled = model_positions.get(day)
                    error = (float(haversine_km(*observed, *modeled))
                             if observed is not None and modeled is not None else np.nan)
                    daily_rows.append({
                        "model": model, "polarity": polarity,
                        "obs_track": obs_id, "model_track": model_id,
                        "date": str(date), "comparison_day": day,
                        "forecast_lead_day": int((date - init_day) / np.timedelta64(1, "D")),
                        "position_error_km": error,
                        "obs_lon": observed[0] if observed else np.nan,
                        "obs_lat": observed[1] if observed else np.nan,
                        "model_lon": modeled[0] if modeled else np.nan,
                        "model_lat": modeled[1] if modeled else np.nan,
                    })
            print(f"{model} {polarity}: {len(matches)} matches / "
                  f"{nobs} observed, {nmodel} modeled at window start", flush=True)

    daily = pd.DataFrame(daily_rows, columns=[
        "model", "polarity", "obs_track", "model_track", "date",
        "comparison_day", "forecast_lead_day", "position_error_km",
        "obs_lon", "obs_lat", "model_lon", "model_lat",
    ])
    matches_df = pd.DataFrame(matches_rows, columns=[
        "model", "polarity", "obs_track", "model_track", "initial_error_km",
    ])
    summary = pd.DataFrame(summary_rows)
    if not daily.empty:
        valid = daily.dropna(subset=["position_error_km"])
        errors = valid.groupby(["model", "polarity"]).position_error_km.agg(
            paired_positions="count", mean_error_km="mean",
            median_error_km="median",
        ).reset_index()
        summary = summary.merge(errors, on=["model", "polarity"], how="left")
        by_day = valid.groupby(
            ["model", "polarity", "date", "comparison_day", "forecast_lead_day"]
        ).position_error_km.agg(
            paired_positions="count", mean_error_km="mean",
            median_error_km="median",
        ).reset_index()
    else:
        by_day = pd.DataFrame(columns=[
            "model", "polarity", "date", "comparison_day", "forecast_lead_day",
            "paired_positions", "mean_error_km", "median_error_km",
        ])
    daily.to_csv(output_dir / "matched_positions.csv", index=False)
    matches_df.to_csv(output_dir / "initial_matches.csv", index=False)
    summary.to_csv(output_dir / "summary.csv", index=False)
    by_day.to_csv(output_dir / "daily_skill.csv", index=False)
    print(f"Saved comparison tables to {output_dir}", flush=True)
    print(summary.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--start", default="2024-07-18")
    parser.add_argument("--days", type=int, default=8)
    parser.add_argument("--max-distance-km", type=float, default=50)
    parser.add_argument("--models", nargs="+", choices=tuple(MODELS),
                        default=list(MODELS))
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--track-subdir", default="TRACK", choices=("TRACK", "TRACK_FULL"))
    parser.add_argument("--init-wednesday", help="Cycle Wednesday YYYY-MM-DD")
    args = parser.parse_args()
    output = args.output_dir or args.data_dir / "COMPARISON" / (
        args.start.replace("-", "") + f"_{args.days}d"
    )
    init_dates = None
    if args.init_wednesday:
        wed = np.datetime64(args.init_wednesday, "D")
        thu = wed + np.timedelta64(1, "D")
        init_dates = {model: str(thu if model == "GLOENS_MEAN" else wed)
                      for model in args.models}
    compare(args.data_dir, args.start, args.days, args.max_distance_km,
            output, tuple(args.models), init_dates=init_dates,
            track_subdir=args.track_subdir)


if __name__ == "__main__":
    main()
