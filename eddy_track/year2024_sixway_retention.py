"""Tracking retention for the six-configuration 2024 eddy comparison.

A pair is retained when BOTH initially matched fixed track IDs have real
positions at a forecast day. A finite position error in matched_positions.csv
indicates both positions exist. No rematching or subsequent 50-km cutoff.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from eddy_track.year2024_sixway import SOURCES, LABELS, PALETTE, cycle_dates

KEYS = ["polarity", "obs_track", "model_track"]

def compute(output_root):
    base = Path(output_root) / "COMPARISON_FULL"
    rows = []
    for cycle, _, _ in cycle_dates():
        for label, (_, _, horizon) in SOURCES.items():
            folder = base / cycle / label
            initial_path = folder / "initial_matches.csv"
            daily_path = folder / "matched_positions.csv"
            summary_path = folder / "summary.csv"
            for path in (initial_path, daily_path, summary_path):
                if not path.is_file():
                    raise FileNotFoundError(f"{path}; run year2024_sixway --stage compare first")
            initial = pd.read_csv(initial_path)
            daily = pd.read_csv(daily_path)
            summary = pd.read_csv(summary_path)
            if not set(KEYS).issubset(initial.columns):
                raise ValueError(f"{initial_path}: missing pair IDs")
            if not set(KEYS + ["forecast_lead_day", "position_error_km"]).issubset(daily.columns):
                raise ValueError(f"{daily_path}: missing required columns")
            if initial.duplicated(KEYS).any():
                raise ValueError(f"{initial_path}: duplicate initial pair")
            n = len(initial)
            if n != int(summary.matched_initial_tracks.sum()):
                raise ValueError(f"{folder}: initial match count disagrees with summary")
            if n == 0:
                # No initial pairs: retention is undefined for this cycle.
                for day in range(horizon):
                    rows.append(dict(cycle=cycle, configuration=label, forecast_day=day+1,
                                     initial_pairs=0, retained_pairs=0,
                                     retention_percent=np.nan))
                continue
            if len(daily) != n * horizon:
                raise ValueError(f"{daily_path}: expected {n*horizon} rows; got {len(daily)}")
            if daily.duplicated(KEYS + ["forecast_lead_day"]).any():
                raise ValueError(f"{daily_path}: duplicate pair/day")
            if set(daily.forecast_lead_day.astype(int)) != set(range(horizon)):
                raise ValueError(f"{daily_path}: incomplete forecast lead days")
            for day, frame in daily.groupby("forecast_lead_day"):
                if len(frame) != n:
                    raise ValueError(f"{daily_path}: incomplete pairs on day {day}")
                retained = int(np.isfinite(frame.position_error_km).sum())
                rows.append(dict(cycle=cycle, configuration=label, forecast_day=int(day)+1,
                                 initial_pairs=n, retained_pairs=retained,
                                 retention_percent=100*retained/n))
    per_cycle = pd.DataFrame(rows)
    pooled = per_cycle.groupby(["configuration", "forecast_day"], as_index=False).agg(
        cycles=("cycle", "nunique"), initial_pairs=("initial_pairs", "sum"),
        retained_pairs=("retained_pairs", "sum"))
    pooled["retention_percent"] = np.where(
        pooled.initial_pairs > 0,
        100 * pooled.retained_pairs / pooled.initial_pairs, np.nan)
    return per_cycle, pooled

def plot(pooled, output, common):
    fig, ax = plt.subplots(figsize=(12, 7))
    for label in SOURCES:
        sub = pooled[pooled.configuration == label].sort_values("forecast_day")
        if common:
            sub = sub[sub.forecast_day <= 9]
        ax.plot(sub.forecast_day, sub.retention_percent, color=PALETTE[label],
                linewidth=2.5, marker="o", markersize=3.5, label=LABELS[label])
    ax.set_xlabel("Forecast day (day 1 = initialization)")
    ax.set_ylabel("Initially matched pairs still tracked (%)")
    ax.set_title("Full year 2024 — Six-configuration tracking retention " +
                 ("(common 9 days)" if common else "(full horizons)"))
    ax.set_xlim(1, 9 if common else 28)
    ax.set_ylim(0, 105)
    ax.set_xticks(range(1, 10) if common else [1, 4, 7, 10, 14, 18, 21, 25, 28])
    ax.grid(alpha=.2)
    ax.legend(ncol=2, frameon=False, fontsize=9)
    fig.text(.5, .02,
             "Original matched track IDs only; both must have real positions; no rematching. "
             "52 weekly cycles, pooled by initial pair count.",
             ha="center", fontsize=9)
    fig.subplots_adjust(bottom=.18)
    filename = ("year2024_sixway_tracking_retention_9d.png" if common else
                "year2024_sixway_tracking_retention_full.png")
    fig.savefig(output / filename, dpi=250, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {output / filename}", flush=True)

def run(output_root):
    out = Path(output_root) / "COMPARISON_FULL/FIGURES"
    per_cycle, pooled = compute(output_root)
    out.mkdir(parents=True, exist_ok=True)
    per_cycle.to_csv(out / "year2024_sixway_tracking_retention_by_cycle.csv", index=False)
    pooled.to_csv(out / "year2024_sixway_tracking_retention_by_day.csv", index=False)
    summary = pooled.loc[pooled.groupby("configuration").forecast_day.idxmax()].copy()
    summary.rename(columns={"forecast_day": "horizon_days"}, inplace=True)
    summary.to_csv(out / "year2024_sixway_tracking_retention_summary.csv", index=False)
    common = pooled[pooled.forecast_day == 9].copy()
    common.to_csv(out / "year2024_sixway_tracking_retention_day9.csv", index=False)
    plot(pooled, out, common=True)
    plot(pooled, out, common=False)
    print("\nDay 9 retention:")
    print(common[["configuration", "initial_pairs", "retained_pairs", "retention_percent"]].to_string(index=False))
    return per_cycle, pooled

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("data_2024_sixway"))
    args = parser.parse_args()
    run(args.output_root)

if __name__ == "__main__":
    main()
