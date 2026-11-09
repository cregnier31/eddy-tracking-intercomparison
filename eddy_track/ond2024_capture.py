"""Plot OND 2024 observed-eddy capture rate from per-cycle comparison summaries.

Metric: 100 * initially matched observed tracks / observed tracks at the
common verification start. Matching is same-polarity, one-to-one, within 50 km.
Cycles are separate samples; a track observed in multiple cycles is counted
once per cycle, not interpreted as an independent unique physical eddy.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eddy_track.plot_comparison_skill import MODELS, LABELS, COLORS

REQUIRED = {"model", "polarity", "observed_initial_tracks", "model_initial_tracks",
            "matched_initial_tracks"}


def plot_capture(root: Path):
    comparison = root / "COMPARISON"
    files = sorted(comparison.glob("20??????/summary.csv"))
    if len(files) != 13:
        raise ValueError(f"Expected 13 cycle summary.csv files; found {len(files)}")
    frames = []
    for path in files:
        frame = pd.read_csv(path)
        missing = REQUIRED - set(frame.columns)
        if missing:
            raise ValueError(f"{path}: missing columns {sorted(missing)}")
        if frame.duplicated(["model", "polarity"]).any():
            raise ValueError(f"{path}: duplicate model/polarity entries")
        if set(frame.model) != set(MODELS):
            raise ValueError(f"{path}: incomplete four-model comparison")
        if (frame["matched_initial_tracks"] > frame["observed_initial_tracks"]).any():
            raise ValueError(f"{path}: matched count exceeds observed count")
        frame["cycle"] = path.parent.name
        frames.append(frame)
    all_rows = pd.concat(frames, ignore_index=True)
    by_cycle = all_rows.groupby(["cycle", "model"], as_index=False).agg(
        observed=("observed_initial_tracks", "sum"),
        modeled=("model_initial_tracks", "sum"),
        matched=("matched_initial_tracks", "sum"),
    )
    by_cycle["obs_capture_percent"] = np.where(
        by_cycle.observed > 0, 100 * by_cycle.matched / by_cycle.observed, np.nan)
    by_cycle["model_precision_percent"] = np.where(
        by_cycle.modeled > 0, 100 * by_cycle.matched / by_cycle.modeled, np.nan)
    if by_cycle["obs_capture_percent"].isna().any():
        raise ValueError("At least one model-cycle has zero observed initial tracks")
    summary = by_cycle.groupby("model", as_index=False).agg(
        cycles=("cycle", "nunique"), observed_cycle_total=("observed", "sum"),
        model_cycle_total=("modeled", "sum"), matched_cycle_total=("matched", "sum"),
        mean_cycle_capture_percent=("obs_capture_percent", "mean"),
        std_cycle_capture_percent=("obs_capture_percent", "std"),
    )
    summary["pooled_obs_capture_percent"] = (
        100 * summary.matched_cycle_total / summary.observed_cycle_total)
    summary["pooled_model_precision_percent"] = (
        100 * summary.matched_cycle_total / summary.model_cycle_total)
    output = comparison / "FIGURES"
    output.mkdir(parents=True, exist_ok=True)
    by_cycle.to_csv(output / "ond2024_eddy_capture_by_cycle.csv", index=False)
    summary.to_csv(output / "ond2024_eddy_capture_summary.csv", index=False)

    fig, ax = plt.subplots(figsize=(12, 7.2))
    fig.subplots_adjust(left=.13, right=.97, top=.88, bottom=.25)
    x = np.arange(len(MODELS))
    values = [float(summary.loc[summary.model == model,
                                "pooled_obs_capture_percent"].iloc[0])
              for model in MODELS]
    bars = ax.bar(x, values, width=.65, color=[COLORS[m] for m in MODELS])
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, value + 1.2,
                f"{value:.1f}%", ha="center", va="bottom", fontsize=17)
    ax.set_xticks(x, [LABELS[m] for m in MODELS], fontsize=15)
    ax.set_ylabel("Observed eddies initially matched (%)", fontsize=19)
    ax.set_title("OND 2024 — Observed eddy capture rate", fontsize=22, pad=14)
    ax.set_ylim(0, max(100, max(values) + 10))
    ax.tick_params(axis="y", labelsize=18)
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    fig.text(.5, .025,
             "Pooled matched / observed initial tracks across 13 weekly cycles; "
             "50 km same-polarity matching.\n"
             "Repeated eddies across cycles count separately; this is not daily recall.",
             ha="center", fontsize=12, color="#555555")
    fig.savefig(output / "ond2024_eddy_capture_rate.png", dpi=250,
                bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {output / 'ond2024_eddy_capture_rate.png'}", flush=True)
    print(summary[["model", "cycles", "pooled_obs_capture_percent",
                   "pooled_model_precision_percent"]].to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root", type=Path)
    args = parser.parse_args()
    plot_capture(args.output_root)


if __name__ == "__main__":
    main()
