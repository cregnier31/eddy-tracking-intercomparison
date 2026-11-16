"""Daily object-based eddy contingency verification for OND 2024 full horizons.

Each forecast day is matched independently, by polarity, with one-to-one
Hungarian nearest-center matching within a maximum distance (default 50 km).
Only real tracked positions (observation_flag == 0) are used. This measures
daily eddy presence, NOT persistence of the original track IDs.

Run: python -m eddy_track.ond2024_contingency ./data_ond2024
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from eddy_track.match_obs_gloens import POLARITIES, initial_matches
from eddy_track.plot_comparison_skill import COLORS, LABELS

HORIZONS = {"GLONET": 10, "GLOW": 9, "GLO12": 10, "GLOENS_MEAN": 28}
COLUMNS = ["cycle", "model", "polarity", "date", "forecast_day",
           "observed", "forecast", "hits", "misses", "false_alarms",
           "pod", "far", "success_ratio", "csi", "f1", "frequency_bias"]
SIZE_BINS = [(0, 25, "<25 km"), (25, 50, "25–50 km"),
             (50, 100, "50–100 km"), (100, np.inf, ">=100 km")]


def safe_ratio(numerator, denominator):
    return float(numerator / denominator) if denominator else np.nan


def scores(hits, misses, false_alarms):
    h, m, f = int(hits), int(misses), int(false_alarms)
    return {
        "pod": safe_ratio(h, h + m),
        "far": safe_ratio(f, h + f),
        "success_ratio": safe_ratio(h, h + f),
        "csi": safe_ratio(h, h + m + f),
        "f1": safe_ratio(2 * h, 2 * h + m + f),
        "frequency_bias": safe_ratio(h + f, h + m),
    }


def load_daily(path, start, days):
    """Read real observations by date; preserve radius/amplitude when available."""
    if not path.is_file():
        raise FileNotFoundError(path)
    start_day = np.datetime64(start, "D")
    with xr.open_dataset(path) as ds:
        required = ("track", "time", "longitude", "latitude", "observation_flag")
        missing = [v for v in required if v not in ds]
        if missing:
            raise ValueError(f"{path}: missing {missing}")
        ids = np.asarray(ds["track"].values)
        times = np.asarray(ds["time"].values).astype("datetime64[D]")
        lon = np.asarray(ds["longitude"].values, dtype=float)
        lat = np.asarray(ds["latitude"].values, dtype=float)
        flag = np.asarray(ds["observation_flag"].values)
        radius = np.asarray(ds["radius_e"].values, dtype=float) / 1000 if "radius_e" in ds else np.full(len(ids), np.nan)
        amp = np.asarray(ds["amplitude"].values, dtype=float) * 100 if "amplitude" in ds else np.full(len(ids), np.nan)
    valid = ((flag == 0) & np.isfinite(lon) & np.isfinite(lat)
             & (times >= start_day) & (times < start_day + np.timedelta64(days, "D")))
    result = {i: {} for i in range(days)}
    for idx in np.flatnonzero(valid):
        day = int((times[idx] - start_day) / np.timedelta64(1, "D"))
        track_id = int(ids[idx])
        if track_id in result[day]:
            raise ValueError(f"{path}: duplicate track {track_id} on day {day}")
        result[day][track_id] = (float(lon[idx]), float(lat[idx]),
                                  float(radius[idx]), float(amp[idx]))
    return result


def match_day(obs, model, threshold):
    # Reuse the established 50-km Hungarian matching, with today's detections
    # mapped to day zero. Do not preserve yesterday's track associations.
    obs0 = {k: {0: v[:2]} for k, v in obs.items()}
    mod0 = {k: {0: v[:2]} for k, v in model.items()}
    return initial_matches(obs0, mod0, threshold)


def classify_radius(value):
    if not np.isfinite(value) or value < 0:
        return None
    for lower, upper, label in SIZE_BINS:
        if lower <= value < upper:
            return label
    return None


def verify(root, max_distance_km=50, max_days=9, year2024=False, obs_root=None):
    if max_distance_km <= 0:
        raise ValueError("max_distance_km must be positive")
    if not 1 <= max_days <= min(HORIZONS.values()):
        raise ValueError("max_days must be between 1 and 9 for a common four-model horizon")
    obs_dir = (Path(obs_root) if obs_root is not None else root / "OBS_FULL") / "GLOENS/OBS/TRACK"
    obs_cache = {}
    rows, event_rows = [], []
    for week in range(52 if year2024 else 13):
        wed = date(2024, 1, 3) + timedelta(days=7 * week) if year2024 else date(2024, 10, 2) + timedelta(days=7 * week)
        thu = wed + timedelta(days=1)
        cycle = wed.strftime("%Y%m%d")
        for model, horizon in HORIZONS.items():
            days = min(horizon, max_days)
            init = thu if model == "GLOENS_MEAN" else wed
            start = init.isoformat()
            model_dir = (root / "CYCLES" / cycle / "GLOENS/TRACK_FULL"
                         if model == "GLOENS_MEAN" else
                         root / "CYCLES" / cycle / model / cycle / "TRACK_FULL")
            for polarity in POLARITIES:
                key = (start, days, polarity)
                if key not in obs_cache:
                    obs_cache[key] = load_daily(obs_dir / f"{polarity}.nc", start, days)
                observed = obs_cache[key]
                predicted = load_daily(model_dir / f"{polarity}.nc", start, days)
                for day in range(days):
                    obs, mod = observed[day], predicted[day]
                    matched = match_day(obs, mod, max_distance_km)
                    obs_matched = {o for o, _, _ in matched}
                    mod_matched = {m for _, m, _ in matched}
                    h = len(matched)
                    m = len(obs) - h
                    f = len(mod) - h
                    date_str = str(np.datetime64(start, "D") + np.timedelta64(day, "D"))
                    base = dict(cycle=cycle, model=model, polarity=polarity,
                                date=date_str, forecast_day=day + 1)
                    rows.append({**base, "observed": len(obs), "forecast": len(mod),
                                 "hits": h, "misses": m, "false_alarms": f,
                                 **scores(h, m, f)})
                    for kind, members, source in (
                        ("hit", obs_matched, obs),
                        ("miss", set(obs) - obs_matched, obs),
                        ("false_alarm", set(mod) - mod_matched, mod),
                    ):
                        for track_id in members:
                            lon, lat, radius, amp = source[track_id]
                            event_rows.append({**base, "event": kind,
                                               "track_id": track_id,
                                               "longitude": lon, "latitude": lat,
                                               "radius_km": radius,
                                               "amplitude_cm": amp,
                                               "radius_class": classify_radius(radius)})
            print(f"{cycle} {model}: {days} days verified", flush=True)
    return pd.DataFrame(rows, columns=COLUMNS), pd.DataFrame(event_rows)


def aggregate(frame, keys):
    sums = frame.groupby(keys, as_index=False)[
        ["observed", "forecast", "hits", "misses", "false_alarms"]].sum()
    for name in ("pod", "far", "success_ratio", "csi", "f1", "frequency_bias"):
        sums[name] = [scores(r.hits, r.misses, r.false_alarms)[name]
                      for r in sums.itertuples()]
    return sums


def size_statistics(events):
    """Object counts by size; hits/misses use observed radius, false alarms model radius."""
    if events.empty:
        return pd.DataFrame()
    valid = events.dropna(subset=["radius_class"])
    if valid.empty:
        return pd.DataFrame()
    grouped = valid.groupby(["model", "polarity", "radius_class", "event"]).size()
    table = grouped.unstack("event", fill_value=0).reset_index()
    for kind in ("hit", "miss", "false_alarm"):
        if kind not in table:
            table[kind] = 0
    table["pod"] = [safe_ratio(h, h + m) for h, m in zip(table.hit, table.miss)]
    # FAR by size is not meaningful here because hit radius comes from OBS,
    # while false-alarm radius comes from the model; report raw counts only.
    return table


def plot_scores(by_day, output, max_days=9):
    for metric, ylabel in (
        ("pod", "Probability of detection (POD)"),
        ("far", "False alarm ratio (FAR)"),
        ("csi", "Critical success index (CSI)"),
        ("frequency_bias", "Frequency bias"),
    ):
        fig, ax = plt.subplots(figsize=(11, 6.5))
        for model in HORIZONS:
            sub = by_day[by_day.model == model].sort_values("forecast_day")
            ax.plot(sub.forecast_day, sub[metric], marker="o", markersize=3,
                    linewidth=2, label=LABELS.get(model, model),
                    color=COLORS.get(model))
        ax.set_xlabel("Forecast day (day 1 = initialization)")
        ax.set_ylabel(ylabel)
        ax.set_title("OND 2024 — Daily eddy contingency: " + metric.upper())
        ax.set_xlim(1, max_days)
        ax.set_xticks(range(1, max_days + 1))
        if metric != "frequency_bias":
            ax.set_ylim(0, 1.02)
        else:
            ax.axhline(1, color="gray", linestyle="--", linewidth=1)
            ax.set_ylim(bottom=0)
        ax.grid(alpha=.2)
        ax.legend(ncol=2, frameon=False)
        fig.text(.5, .015,
                 "13 OND 2024 cycles; independent daily Hungarian matching (50 km); "
                 "cyclonic + anticyclonic pooled; no virtual positions.",
                 ha="center", fontsize=9)
        fig.tight_layout(rect=(0, .045, 1, 1))
        path = output / f"ond2024_full_contingency_{metric}.png"
        fig.savefig(path, dpi=220)
        plt.close(fig)
        print(f"Saved {path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--max-distance-km", type=float, default=50)
    parser.add_argument("--year2024", action="store_true", help="Verify all 52 weekly cycles of 2024")
    parser.add_argument("--obs-root", type=Path, help="Root containing GLOENS/OBS/TRACK; defaults to output_root/OBS_FULL")
    parser.add_argument("--max-days", type=int, default=9,
                        help="Common forecast horizon, 1–9 days (default: 9)")
    args = parser.parse_args(argv)
    root = args.output_root
    out = root / "COMPARISON_FULL/FIGURES"
    # Verify all inputs before writing any results.
    daily, events = verify(root, args.max_distance_km, args.max_days, args.year2024, args.obs_root)
    out.mkdir(parents=True, exist_ok=True)
    daily.to_csv(out / "ond2024_full_contingency_daily.csv", index=False)
    aggregate(daily, ["model", "polarity", "forecast_day"]).to_csv(
        out / "ond2024_full_contingency_by_polarity_day.csv", index=False)
    by_day = aggregate(daily, ["model", "forecast_day"])
    by_day.to_csv(out / "ond2024_full_contingency_by_day.csv", index=False)
    aggregate(daily, ["model", "polarity"]).to_csv(
        out / "ond2024_full_contingency_by_polarity.csv", index=False)
    overall = aggregate(daily, ["model"])
    overall.to_csv(out / "ond2024_full_contingency_summary.csv", index=False)
    events.to_csv(out / "ond2024_full_contingency_events.csv", index=False)
    size_statistics(events).to_csv(out / "ond2024_full_contingency_by_radius.csv", index=False)
    plot_scores(by_day, out, args.max_days)
    print(f"\nPooled contingency scores for {52 if args.year2024 else 13} cycles, common {args.max_days}-day horizon:")
    print(overall.to_string(index=False))
    print(f"\nSaved contingency outputs to {out}")


if __name__ == "__main__":
    main()
