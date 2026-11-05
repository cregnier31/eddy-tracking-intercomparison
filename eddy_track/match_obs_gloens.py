"""Match observed eddy tracks to GLOENS member tracks at forecast initialization.

Match same-polarity centers one-to-one using Hungarian assignment and a
maximum initial separation. Track IDs are then fixed for the forecast period:
no daily rematching or substitution. Virtual observations are excluded.

Example:
  python -m eddy_track.match_obs_gloens ./data --model-dir ./data_sep2026 \\
    --start-date 2026-09-24 --days 28 --max-distance-km 50
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.optimize import linear_sum_assignment

from eddy_track.gloens_displacement import haversine_km

POLARITIES = ("Cyclonic", "Anticyclonic")
GS_BOX = (-75, -45, 35, 45)


def read_tracks(path, start_date, days):
    """Return observed daily positions, grouped by track ID."""
    if not path.is_file():
        raise FileNotFoundError(path)
    with xr.open_dataset(path) as ds:
        required = ("track", "time", "longitude", "latitude", "observation_flag")
        missing = [key for key in required if key not in ds]
        if missing:
            raise KeyError(f"{path}: missing variables {missing}")
        ids = np.asarray(ds.track.values)
        times = np.asarray(ds.time.values).astype("datetime64[D]")
        lon = np.asarray(ds.longitude.values, dtype=float)
        lat = np.asarray(ds.latitude.values, dtype=float)
        flags = np.asarray(ds.observation_flag.values)
    first = np.datetime64(start_date, "D")
    valid = ((flags == 0) & np.isfinite(lon) & np.isfinite(lat)
             & (times >= first) & (times < first + np.timedelta64(days, "D")))
    result = {}
    for track_id in np.unique(ids[valid]):
        idx = np.flatnonzero(valid & (ids == track_id))
        by_day = {}
        for i in idx:
            day = int((times[i] - first) / np.timedelta64(1, "D"))
            if day in by_day:
                raise ValueError(f"{path}: duplicate real observations for track {track_id}, day {day}")
            by_day[day] = (float(lon[i]), float(lat[i]))
        result[int(track_id)] = by_day
    return result


def initial_matches(observed, modeled, max_distance_km):
    """One-to-one, same-polarity nearest-center matching on day zero."""
    obs_ids = [k for k, positions in observed.items() if 0 in positions]
    mod_ids = [k for k, positions in modeled.items() if 0 in positions]
    if not obs_ids or not mod_ids:
        return []
    olon = np.array([observed[k][0][0] for k in obs_ids])
    olat = np.array([observed[k][0][1] for k in obs_ids])
    mlon = np.array([modeled[k][0][0] for k in mod_ids])
    mlat = np.array([modeled[k][0][1] for k in mod_ids])
    distances = haversine_km(olon[:, None], olat[:, None],
                             mlon[None, :], mlat[None, :])
    # Explicit dummy columns allow observations to remain unmatched.
    # Invalid pairs cost more than leaving an eddy unmatched.
    nobs = len(obs_ids)
    penalty = max_distance_km + 1.0
    costs = np.full((nobs, len(mod_ids) + nobs), penalty, dtype=float)
    costs[:, :len(mod_ids)] = np.where(
        distances <= max_distance_km, distances, penalty * 3
    )
    rows, cols = linear_sum_assignment(costs)
    return [
        (obs_ids[i], mod_ids[j], float(distances[i, j]))
        for i, j in zip(rows, cols)
        if j < len(mod_ids) and distances[i, j] <= max_distance_km
    ]


def compare(obs_root, model_root, start_date, days, first_member,
            last_member, max_distance_km, output_dir):
    if days < 2 or max_distance_km <= 0:
        raise ValueError("days must be >=2 and max-distance-km must be positive")
    obs = {
        polarity: read_tracks(obs_root / "TRACK" / f"{polarity}.nc", start_date, days)
        for polarity in POLARITIES
    }
    rows = []
    coverage = []
    for member in range(first_member, last_member + 1):
        member_root = model_root / "MEMBERS" / f"member_{member:03d}" / "TRACK"
        for polarity in POLARITIES:
            modeled = read_tracks(member_root / f"{polarity}.nc", start_date, days)
            matches = initial_matches(obs[polarity], modeled, max_distance_km)
            n_obs = sum(0 in positions for positions in obs[polarity].values())
            coverage.append({
                "member": member, "polarity": polarity,
                "observed_initial_eddies": n_obs,
                "matched_initial_eddies": len(matches),
                "initial_match_rate_percent": 100 * len(matches) / n_obs if n_obs else np.nan,
            })
            for obs_id, model_id, initial_error in matches:
                obs_track, model_track = obs[polarity][obs_id], modeled[model_id]
                first_lon, first_lat = obs_track[0]
                gs = (GS_BOX[0] <= first_lon <= GS_BOX[1]
                      and GS_BOX[2] <= first_lat <= GS_BOX[3])
                for day in range(days):
                    obs_pos = obs_track.get(day)
                    mod_pos = model_track.get(day)
                    # Retain missing days in output; no artificial interpolation.
                    error = (float(haversine_km(*obs_pos, *mod_pos))
                             if obs_pos is not None and mod_pos is not None else np.nan)
                    rows.append({
                        "member": member, "polarity": polarity,
                        "obs_track": obs_id, "model_track": model_id,
                        "lead_day": day, "date": str(np.datetime64(start_date, "D")
                                                     + np.timedelta64(day, "D")),
                        "initial_error_km": initial_error,
                        "position_error_km": error,
                        "obs_lon": obs_pos[0] if obs_pos else np.nan,
                        "obs_lat": obs_pos[1] if obs_pos else np.nan,
                        "model_lon": mod_pos[0] if mod_pos else np.nan,
                        "model_lat": mod_pos[1] if mod_pos else np.nan,
                        "gulf_stream_start": gs,
                    })
            print(f"member {member:03d} {polarity}: matched {len(matches)}/{n_obs} "
                  f"observed initial eddies", flush=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    daily = pd.DataFrame(rows, columns=[
        "member", "polarity", "obs_track", "model_track", "lead_day", "date",
        "initial_error_km", "position_error_km",
        "obs_lon", "obs_lat", "model_lon", "model_lat", "gulf_stream_start",
    ])
    match_rates = pd.DataFrame(coverage)
    daily_path = output_dir / "matched_trajectory_daily.csv"
    coverage_path = output_dir / "initial_match_rates.csv"
    daily.to_csv(daily_path, index=False)
    match_rates.to_csv(coverage_path, index=False)
    if daily.empty:
        print("No initial matches found. Try a larger search radius.", flush=True)
        return
    for region, subset in (
        ("North Atlantic", daily),
        ("Gulf Stream", daily[daily.gulf_stream_start]),
    ):
        print(f"\n{region}: {subset[['member', 'polarity', 'obs_track', 'model_track']].drop_duplicates().shape[0]} matched member–eddy pairs")
        for lead in (0, 6, 13, 20, 27):
            if lead >= days:
                continue
            current = subset[subset.lead_day == lead]
            good = current.position_error_km.dropna()
            print(f"  day {lead+1:2d}: {len(good)}/{len(current)} pairs observed "
                  f"in both; median error={good.median():.1f} km, "
                  f"mean error={good.mean():.1f} km")
    print(f"\nSaved: {daily_path}\nSaved: {coverage_path}", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", help="Root with GLOENS/OBS/TRACK")
    parser.add_argument("--model-dir", type=Path,
                        help="Root with GLOENS/MEMBERS; defaults to data_dir")
    parser.add_argument("--start-date", default="2026-09-24")
    parser.add_argument("--days", type=int, default=28)
    parser.add_argument("--first-member", type=int, default=1)
    parser.add_argument("--last-member", type=int, default=50)
    parser.add_argument("--max-distance-km", type=float, default=50)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    if not 1 <= args.first_member <= args.last_member <= 50:
        parser.error("Member range must be 1..50")
    model_dir = args.model_dir or Path(args.data_dir)
    obs_root = Path(args.data_dir) / "GLOENS" / "OBS"
    model_root = model_dir / "GLOENS"
    output_dir = args.output_dir or obs_root / "MATCHING"
    compare(obs_root, model_root, args.start_date, args.days,
            args.first_member, args.last_member, args.max_distance_km, output_dir)


if __name__ == "__main__":
    main()
