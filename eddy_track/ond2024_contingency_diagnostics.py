"""Plot lead-day, polarity, and eddy-size contingency skill from existing CSVs.

No detection, tracking, or matching is rerun.

Example:
  python -m eddy_track.ond2024_contingency_diagnostics ./data_ond2024
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eddy_track.plot_comparison_skill import COLORS, LABELS

MODELS = ("GLONET", "GLOW", "GLO12", "GLOENS_MEAN")
METRICS = {"pod": "Probability of detection", "far": "False alarm ratio",
           "csi": "Critical success index"}
BINS = ("<25 km", "25–50 km", "50–100 km", ">=100 km")


def ratio(a, b):
    return a / b if b else np.nan


def grouped_scores(daily, keys):
    counts = daily.groupby(keys, as_index=False)[["hits", "misses", "false_alarms"]].sum()
    h, m, f = (counts[k].to_numpy(dtype=float) for k in ("hits", "misses", "false_alarms"))
    with np.errstate(divide="ignore", invalid="ignore"):
        counts["pod"] = np.divide(h, h + m, out=np.full_like(h, np.nan), where=(h + m) > 0)
        counts["far"] = np.divide(f, h + f, out=np.full_like(h, np.nan), where=(h + f) > 0)
        counts["csi"] = np.divide(h, h + m + f, out=np.full_like(h, np.nan), where=(h + m + f) > 0)
    return counts


def plot_leads(daily, out, max_days):
    pooled = grouped_scores(daily, ["model", "forecast_day"])
    polarity = grouped_scores(daily, ["model", "polarity", "forecast_day"])
    pooled.to_csv(out / "ond2024_contingency_9d_lead_scores.csv", index=False)
    polarity.to_csv(out / "ond2024_contingency_9d_polarity_lead_scores.csv", index=False)
    for metric, label in METRICS.items():
        fig, axes = plt.subplots(1, 3, figsize=(17, 5.2), sharex=True, sharey=True)
        for ax, (name, data) in zip(axes, [
            ("Both polarities", pooled),
            ("Cyclonic", polarity[polarity.polarity == "Cyclonic"]),
            ("Anticyclonic", polarity[polarity.polarity == "Anticyclonic"]),
        ]):
            for model in MODELS:
                d = data[data.model == model].sort_values("forecast_day")
                ax.plot(d.forecast_day, d[metric], marker="o", markersize=3.5,
                        linewidth=2, color=COLORS.get(model),
                        label=LABELS.get(model, model))
            ax.set_title(name)
            ax.set_xlim(1, max_days)
            ax.set_xticks(range(1, max_days + 1))
            ax.set_ylim(0, 1)
            ax.set_xlabel("Forecast day")
            ax.grid(alpha=.2)
        axes[0].set_ylabel(label)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
        fig.suptitle(f"OND 2024 — {label} by lead day and polarity", fontsize=15)
        fig.tight_layout(rect=(0, .11, 1, .94))
        path = out / f"ond2024_contingency_9d_{metric}_polarity.png"
        fig.savefig(path, dpi=220)
        plt.close(fig)
        print(f"Saved {path}")


def plot_radius(events, out):
    needed = {"model", "polarity", "radius_km", "event"}
    if not needed.issubset(events.columns):
        raise ValueError(f"Event CSV missing columns: {needed - set(events.columns)}")
    # Observed hit and miss radii are comparable; false alarms use model radius
    # and are intentionally excluded from radius-stratified POD.
    obs = events[events.event.isin(("hit", "miss"))].copy()
    obs["radius_km"] = pd.to_numeric(obs.radius_km, errors="coerce")
    obs = obs[np.isfinite(obs.radius_km) & (obs.radius_km >= 0)]
    if obs.empty:
        print("No valid observed radii; skipping radius-dependent POD")
        return
    obs["radius_bin"] = pd.cut(
        obs.radius_km, bins=[0, 25, 50, 100, np.inf],
        labels=BINS, right=False, include_lowest=True)
    counts = (obs.groupby(["model", "polarity", "radius_bin", "event"],
                          observed=True).size().unstack("event", fill_value=0))
    for col in ("hit", "miss"):
        if col not in counts:
            counts[col] = 0
    table = counts.reset_index()
    table["observed"] = table.hit + table.miss
    table["pod"] = [ratio(h, n) for h, n in zip(table.hit, table.observed)]
    table.to_csv(out / "ond2024_contingency_9d_radius_pod.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.3), sharey=True)
    x = np.arange(len(BINS))
    width = .19
    for ax, polarity in zip(axes, ("Cyclonic", "Anticyclonic")):
        for j, model in enumerate(MODELS):
            sub = table[(table.model == model) & (table.polarity == polarity)]
            values = sub.set_index("radius_bin").reindex(BINS).pod.to_numpy()
            ax.bar(x + (j - 1.5) * width, values, width,
                   color=COLORS.get(model), label=LABELS.get(model, model))
        ax.set_xticks(x, BINS)
        ax.set_ylim(0, 1)
        ax.set_title(polarity)
        ax.set_xlabel("Observed effective radius")
        ax.grid(axis="y", alpha=.2)
    axes[0].set_ylabel("Probability of detection")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
    fig.suptitle("OND 2024 — POD by observed eddy radius (days 1–9)", fontsize=15)
    fig.tight_layout(rect=(0, .11, 1, .94))
    path = out / "ond2024_contingency_9d_radius_pod.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    print(f"Saved {path}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output_root", type=Path)
    args = p.parse_args(argv)
    out = args.output_root / "COMPARISON_FULL/FIGURES"
    daily_path = out / "ond2024_full_contingency_daily.csv"
    event_path = out / "ond2024_full_contingency_events.csv"
    daily = pd.read_csv(daily_path)
    if daily.empty:
        raise ValueError(f"No contingency data in {daily_path}")
    days = sorted(daily.forecast_day.unique())
    if days != list(range(1, 10)):
        raise ValueError(f"Expected exactly days 1–9, got {days}")
    if set(daily.model.unique()) != set(MODELS):
        raise ValueError("Expected all four models in daily contingency CSV")
    plot_leads(daily, out, 9)
    events = pd.read_csv(event_path)
    plot_radius(events, out)
    print(f"Diagnostics saved in {out}")


if __name__ == "__main__":
    main()
