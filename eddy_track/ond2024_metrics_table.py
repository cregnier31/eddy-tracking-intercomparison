"""Create a publication-ready OND 2024 metric table as PNG and CSV.

Reads existing summary figures' statistics and initial eddy capture counts.
No detection or tracking is performed.
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


def build(root: Path):
    folder = root / "COMPARISON" / "FIGURES"
    pos = pd.read_csv(folder / "ond2024_position_error.csv")
    amp = pd.read_csv(folder / "ond2024_amplitude_error.csv")
    capture = pd.read_csv(folder / "ond2024_eddy_capture_summary.csv")
    rows = []
    for model in MODELS:
        p = pos[pos.model == model]
        a = amp[amp.model == model]
        c = capture[capture.model == model]
        if p.empty or a.empty or len(c) != 1:
            raise ValueError(f"Missing statistics for {model}")
        # Weighting by valid matched pairs, not by number of forecast days.
        # Daily aggregated medians cannot reconstruct the pooled sample median.
        p_median = float(np.average(p["median"], weights=p["n"]))
        a_median = float(np.average(a["median"], weights=a["n"])) * 100
        rows.append({
            "model": LABELS[model],
            "position_error_weighted_daily_median_km": p_median,
            "amplitude_error_weighted_daily_median_cm": a_median,
            "initial_obs_capture_percent": float(c.pooled_obs_capture_percent.iloc[0]),
            "matched_position_samples": int(p["n"].sum()),
            "matched_amplitude_samples": int(a["n"].sum()),
            "initial_matched_eddies_cycle_total": int(c.matched_cycle_total.iloc[0]),
            "initial_observed_eddies_cycle_total": int(c.observed_cycle_total.iloc[0]),
        })
    result = pd.DataFrame(rows)
    folder.mkdir(parents=True, exist_ok=True)
    result.to_csv(folder / "ond2024_metrics_table.csv", index=False)
    columns = ["System", "Position error\n(km)", "Amplitude error\n(cm)",
               "Initial eddy\ncapture (%)", "Position\nsamples"]
    cells = [[r["model"], f'{r["position_error_weighted_daily_median_km"]:.2f}',
              f'{r["amplitude_error_weighted_daily_median_cm"]:.2f}',
              f'{r["initial_obs_capture_percent"]:.1f}',
              f'{r["matched_position_samples"]:,}'] for r in rows]
    fig, ax = plt.subplots(figsize=(13, 4.9))
    ax.axis("off")
    ax.set_title("OND 2024 — Eddy forecast skill summary", fontsize=21, pad=22)
    table = ax.table(cellText=cells, colLabels=columns, cellLoc="center",
                     colLoc="center", loc="center",
                     colWidths=[.28, .19, .20, .20, .13])
    table.auto_set_font_size(False)
    table.set_fontsize(12.5)
    table.scale(1, 2.5)
    for j in range(len(columns)):
        cell = table[(0, j)]
        cell.set_facecolor("#e9edf2")
        cell.set_text_props(weight="bold")
    for i, model in enumerate(MODELS, start=1):
        table[(i, 0)].set_text_props(weight="bold", color=COLORS[model])
        if i % 2 == 0:
            for j in range(len(columns)):
                table[(i, j)].set_facecolor("#f7f8fa")
    fig.text(.5, .06,
             "Common 8-day verification window; 13 weekly cycles; 50 km initial matching.\n"
             "Errors are sample-count-weighted averages of daily medians, not pooled medians.\n"
             "Capture = initially matched / observed eddies, pooled across cycles.",
             ha="center", va="center", fontsize=10.5, color="#555555")
    fig.savefig(folder / "ond2024_metrics_table.png", dpi=240,
                bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {folder / 'ond2024_metrics_table.png'}")
    print(result.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root", type=Path)
    args = parser.parse_args()
    build(args.output_root)


if __name__ == "__main__":
    main()
