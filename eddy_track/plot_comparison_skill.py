"""Plot eddy position-error evolution from existing comparison CSV files.

Produces a common-valid-date comparison and a full-forecast lead-time figure.
Shaded bands are interquartile ranges of matched-pair errors, not confidence
intervals. No detection, tracking or matching is performed.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

MODELS = ("GLONET", "GLOW", "GLO12", "GLOENS_MEAN")
LABELS = {"GLONET": "GLONET", "GLOW": "GLOW", "GLO12": "GLO12",
          "GLOENS_MEAN": "GLOENS ensemble mean"}
COLORS = {"GLONET": "#377eb8", "GLOW": "#4daf4a", "GLO12": "#984ea3",
          "GLOENS_MEAN": "#e41a1c"}
FULL = {"GLONET": "GLONET_20240717", "GLOW": "GLOW_20240717",
        "GLO12": "GLO12_20240717", "GLOENS_MEAN": "20240718_28d"}


def read_csv(folder: Path):
    path = folder / "matched_positions.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}; run compare_forecasts_obs first")
    df = pd.read_csv(path)
    needed = {"model", "polarity", "date", "forecast_lead_day",
              "position_error_km"}
    if not needed.issubset(df.columns):
        raise ValueError(f"{path}: missing columns {sorted(needed - set(df))}")
    return df


def plot(root: Path, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    common = read_csv(root / "20240718_8d")
    full = {model: read_csv(root / folder) for model, folder in FULL.items()}
    for kind, datasets in (
        ("common_valid_dates", {model: common[common.model == model] for model in MODELS}),
        ("full_forecast", full),
    ):
        fig, ax = plt.subplots(figsize=(10.5, 6.2), constrained_layout=True)
        stats_rows = []
        for model in MODELS:
            data = datasets[model].copy()
            data = data[np.isfinite(data.position_error_km)]
            if data.empty:
                print(f"WARNING: no valid positions for {model} in {kind}")
                continue
            group_col = "date" if kind == "common_valid_dates" else "forecast_lead_day"
            agg = data.groupby(group_col, sort=True).position_error_km.agg(
                n="size", median="median", mean="mean",
                q25=lambda x: x.quantile(.25), q75=lambda x: x.quantile(.75),
            ).reset_index()
            if kind == "common_valid_dates":
                x = np.arange(len(agg), dtype=float)
                agg["x"] = x
            else:
                x = agg.forecast_lead_day.to_numpy(dtype=float)
                agg["x"] = x
            agg["model"] = model
            stats_rows.append(agg)
            ax.plot(x, agg["median"].to_numpy(), color=COLORS[model],
                    linewidth=2.4, marker="o", markersize=3.7,
                    label=LABELS[model])
            ax.fill_between(x, agg["q25"].to_numpy(), agg["q75"].to_numpy(),
                            color=COLORS[model], alpha=.12, linewidth=0)
        if kind == "common_valid_dates":
            dates = sorted(common.date.dropna().unique())
            ax.set_xticks(np.arange(len(dates)))
            ax.set_xticklabels([str(date)[5:] for date in dates])
            ax.set_xlabel("Valid date (2024, MM-DD)")
            ax.set_title("Eddy position error — common valid dates (18–25 July 2024)")
            ax.text(.01, .01,
                    "GLOENS initialized 18 July; other forecasts initialized 17 July",
                    transform=ax.transAxes, fontsize=8, color="#555555")
        else:
            ax.set_xlabel("Forecast lead time (days since model initialization)")
            ax.set_title("Eddy position error — full forecast horizons")
            ax.set_xlim(left=0, right=27)
            ax.set_xticks([0, 3, 6, 9, 13, 17, 20, 24, 27])
        ax.set_ylabel("Eddy-center position error (km)")
        ax.set_ylim(bottom=0)
        ax.grid(alpha=.22)
        ax.legend(loc="upper left", frameon=False, ncol=2, fontsize=9)
        fig.text(.5, .008,
                 "Lines: median across valid matched pairs. Bands: 25th–75th percentiles. "
                 "Initial matching threshold: 50 km.",
                 ha="center", fontsize=8, color="#555555")
        stem = output / f"eddy_error_{kind}"
        fig.savefig(stem.with_suffix(".png"), dpi=250, bbox_inches="tight")
        plt.close(fig)
        pd.concat(stats_rows, ignore_index=True).to_csv(
            output / f"eddy_error_{kind}.csv", index=False)
        print(f"Saved {stem}.png")
    print("Note: bands are IQR, not uncertainty in the estimated median.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("comparison_dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    plot(args.comparison_dir,
         args.output_dir or args.comparison_dir / "FIGURES")


if __name__ == "__main__":
    main()
