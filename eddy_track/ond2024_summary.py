"""Aggregate OND 2024 matched eddy position and amplitude skill across weekly cycles."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eddy_track.plot_comparison_skill import MODELS, LABELS, COLORS
from eddy_track.plot_comparison_amplitude import enrich


def summarize(root: Path):
    comparison = root / "COMPARISON"
    output = comparison / "FIGURES"
    output.mkdir(parents=True, exist_ok=True)
    files = sorted(comparison.glob("20??????/matched_positions.csv"))
    if len(files) != 13:
        raise ValueError(f"Expected 13 weekly comparison CSVs, found {len(files)} in {comparison}")
    positions, amplitudes = [], []
    for file in files:
        cycle = file.parent.name
        data = pd.read_csv(file)
        if set(data.model.unique()) != set(MODELS):
            raise ValueError(f"{file}: missing one or more models")
        data["cycle"] = cycle
        positions.append(data)
        cycle_root = root / "CYCLES" / cycle
        for model in MODELS:
            amp = enrich(data, model, cycle_root)
            if not amp.empty:
                amplitudes.append(amp)
    pos = pd.concat(positions, ignore_index=True)
    amp = pd.concat(amplitudes, ignore_index=True) if amplitudes else pd.DataFrame()
    if amp.empty:
        raise ValueError("No matched amplitude data; verify TRACK amplitude variables")
    for metric, frame, title, ylabel, stem in (
        ("position_error_km", pos, "OND 2024 — Eddy position error",
         "Eddy-center position error (km)", "ond2024_position_error"),
        ("amplitude_abs_error_m", amp, "OND 2024 — Eddy amplitude absolute error",
         "Absolute amplitude error (cm)", "ond2024_amplitude_error"),
    ):
        frame = frame[np.isfinite(frame[metric])].copy()
        # Day 1 is initialization. GLOENS initializes on Thursday, others Wednesday.
        frame["forecast_day"] = frame["forecast_lead_day"].astype(int) + 1
        rows = []
        fig, ax = plt.subplots(figsize=(12, 7.2))
        fig.subplots_adjust(left=.13, right=.97, top=.88, bottom=.24)
        for model in MODELS:
            sub = frame[frame.model == model]
            if sub.empty:
                continue
            agg = sub.groupby("forecast_day")[metric].agg(
                n="size", median="median", mean="mean",
                q25=lambda x: x.quantile(.25),
                q75=lambda x: x.quantile(.75)).reset_index()
            agg["model"] = model
            rows.append(agg)
            scale = 100 if metric == "amplitude_abs_error_m" else 1
            x = agg.forecast_day.to_numpy()
            ax.plot(x, agg["median"].to_numpy() * scale, linewidth=2.4,
                    marker="o", markersize=4, label=LABELS[model],
                    color=COLORS[model])
            ax.fill_between(x, agg["q25"].to_numpy() * scale,
                            agg["q75"].to_numpy() * scale,
                            color=COLORS[model], alpha=.12, linewidth=0)
        if not rows:
            raise ValueError(f"No valid data for {metric}")
        ax.set_title(title, fontsize=22, pad=14)
        ax.set_xlabel("Forecast day (day 1 = initialization)", fontsize=20, labelpad=12)
        ax.set_ylabel(ylabel, fontsize=20)
        ax.tick_params(axis="both", labelsize=20)
        ax.set_ylim(bottom=0)
        ax.set_xlim(1, 9)
        ax.set_xticks(range(1, 10))
        ax.grid(alpha=.22)
        ax.legend(loc="upper left", frameon=False, ncol=2, fontsize=16)
        fig.text(.5, .025, "Lines: median. Bands: 25th–75th percentiles. "
                 "13 weekly cycles; initial matching radius 50 km.",
                 ha="center", fontsize=13, color="#555555")
        fig.savefig(output / f"{stem}.png", dpi=250, bbox_inches="tight")
        plt.close(fig)
        pd.concat(rows, ignore_index=True).to_csv(output / f"{stem}.csv", index=False)
        print(f"Saved {output / (stem + '.png')}", flush=True)
    pos.to_csv(output / "ond2024_matched_positions.csv", index=False)
    amp.to_csv(output / "ond2024_matched_amplitudes.csv", index=False)
    from eddy_track.ond2024_capture import plot_capture
    plot_capture(root)
    print("Note: pooled matched observations are not statistically independent across cycles.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root", type=Path)
    args = parser.parse_args()
    summarize(args.output_root)


if __name__ == "__main__":
    main()
