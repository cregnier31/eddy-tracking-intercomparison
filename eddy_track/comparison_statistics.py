"""Summarize existing eddy-to-observation comparison CSV files.

Reads COMPARISON subdirectories; never reruns detection, tracking, or matching.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def summarize(root: Path, output: Path):
    directories = sorted(p for p in root.iterdir() if p.is_dir() and
                         (p / "summary.csv").is_file() and
                         (p / "matched_positions.csv").is_file())
    if not directories:
        raise FileNotFoundError(f"No comparison CSV directories under {root}")
    coverage, errors, retention = [], [], []
    for folder in directories:
        summary = pd.read_csv(folder / "summary.csv")
        daily = pd.read_csv(folder / "matched_positions.csv")
        summary.insert(0, "comparison", folder.name)
        coverage.append(summary)
        if daily.empty:
            continue
        for (model, polarity, lead), group in daily.groupby(
            ["model", "polarity", "forecast_lead_day"], dropna=False
        ):
            valid = group.position_error_km.dropna()
            key = {"comparison": folder.name, "model": model,
                   "polarity": polarity, "forecast_lead_day": int(lead)}
            errors.append({**key, "n_matched_pairs": len(group),
                           "n_valid_pairs": len(valid),
                           "mean_error_km": valid.mean(),
                           "median_error_km": valid.median(),
                           "rmse_km": np.sqrt(np.mean(valid.to_numpy() ** 2))
                           if len(valid) else np.nan,
                           "p90_error_km": valid.quantile(.9)})
            retention.append({**key, "n_initial_pairs": len(group),
                              "n_both_present": len(valid),
                              "retention_percent": 100 * len(valid) / len(group)
                              if len(group) else np.nan})
    output.mkdir(parents=True, exist_ok=True)
    pd.concat(coverage, ignore_index=True).to_csv(
        output / "matching_summary.csv", index=False)
    pd.DataFrame(errors).to_csv(output / "position_error_by_lead.csv", index=False)
    pd.DataFrame(retention).to_csv(output / "trajectory_retention_by_lead.csv",
                                   index=False)
    print(f"Processed {len(directories)} comparison directories:")
    for folder in directories:
        print(f"  {folder.name}")
    print(f"Saved statistical summaries to {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("comparison_dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    summarize(args.comparison_dir,
              args.output_dir or args.comparison_dir / "STATISTICS")


if __name__ == "__main__":
    main()
