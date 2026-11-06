"""Plot matched model-versus-observed eddy amplitude errors as PNG figures.

Reads the existing comparison matched_positions.csv files and original TRACK
NetCDFs. Matches are NOT recomputed. Virtual observations are excluded.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from eddy_track.plot_comparison_skill import MODELS, LABELS, COLORS, FULL

TRACK_DIRS = {
    "GLONET": "GLONET/20240717/TRACK",
    "GLOW": "GLOW/20240717/TRACK",
    "GLO12": "GLO12/20240717/TRACK",
    "GLOENS_MEAN": "GLOENS/TRACK",
}


def amplitudes(path, prefix):
    if not path.is_file():
        raise FileNotFoundError(path)
    with xr.open_dataset(path) as ds:
        needed = ("track", "time", "observation_flag", "amplitude")
        missing = [v for v in needed if v not in ds]
        if missing:
            raise KeyError(f"{path}: missing {missing}; available: {list(ds.variables)}")
        ids = np.asarray(ds["track"].values)
        dates = np.asarray(ds["time"].values).astype("datetime64[D]").astype(str)
        flags = np.asarray(ds["observation_flag"].values)
        amps = np.asarray(ds["amplitude"].values, dtype=float)
    valid = (flags == 0) & np.isfinite(amps)
    result = pd.DataFrame({
        prefix + "_track": ids[valid].astype(np.int64),
        "date": dates[valid],
        prefix + "_amplitude_m": amps[valid],
    })
    keys = [prefix + "_track", "date"]
    if result.duplicated(keys).any():
        raise ValueError(f"{path}: duplicate real track/date amplitude observations")
    return result


def enrich(df, model, data_dir):
    chunks = []
    for polarity in ("Cyclonic", "Anticyclonic"):
        subset = df[(df.model == model) & (df.polarity == polarity)].copy()
        if subset.empty:
            continue
        obs = amplitudes(data_dir / "GLOENS/OBS/TRACK" / f"{polarity}.nc", "obs")
        mod = amplitudes(data_dir / TRACK_DIRS[model] / f"{polarity}.nc", "model")
        subset["date"] = pd.to_datetime(subset["date"]).dt.strftime("%Y-%m-%d")
        subset = subset.merge(obs, on=["obs_track", "date"], how="left",
                              validate="many_to_one")
        subset = subset.merge(mod, on=["model_track", "date"], how="left",
                              validate="many_to_one")
        # Require a valid matched pair on the date, as in the position-error plot.
        subset = subset[np.isfinite(subset["position_error_km"])].copy()
        subset["amplitude_bias_m"] = (subset["model_amplitude_m"]
                                      - subset["obs_amplitude_m"])
        subset["amplitude_abs_error_m"] = subset["amplitude_bias_m"].abs()
        chunks.append(subset)
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()


def plot(data_dir, comparison_dir, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    sources = {
        "common_valid_dates": comparison_dir / "20240718_8d",
        "full_forecast": None,
    }
    for kind in sources:
        fig, ax = plt.subplots(figsize=(12, 7.2))
        fig.subplots_adjust(left=.09, right=.97, top=.92, bottom=.17)
        stats = []
        paired = []
        for model in MODELS:
            folder = (sources[kind] if kind == "common_valid_dates"
                      else comparison_dir / FULL[model])
            csv_path = folder / "matched_positions.csv"
            if not csv_path.is_file():
                raise FileNotFoundError(csv_path)
            df = pd.read_csv(csv_path)
            needed = {"model", "polarity", "date", "forecast_lead_day",
                      "obs_track", "model_track", "position_error_km"}
            if not needed.issubset(df):
                raise ValueError(f"{csv_path}: missing {sorted(needed - set(df))}")
            df = enrich(df, model, data_dir)
            if df.empty:
                print(f"WARNING: no matched pairs for {model} ({kind})")
                continue
            paired.append(df)
            valid = df[np.isfinite(df["amplitude_abs_error_m"])]
            if valid.empty:
                print(f"WARNING: no paired amplitudes for {model} ({kind})")
                continue
            key = "date" if kind == "common_valid_dates" else "forecast_lead_day"
            agg = valid.groupby(key, sort=True).agg(
                n=("amplitude_abs_error_m", "size"),
                median=("amplitude_abs_error_m", "median"),
                mean=("amplitude_abs_error_m", "mean"),
                q25=("amplitude_abs_error_m", lambda s: s.quantile(.25)),
                q75=("amplitude_abs_error_m", lambda s: s.quantile(.75)),
                mean_bias_m=("amplitude_bias_m", "mean"),
                median_bias_m=("amplitude_bias_m", "median"),
            ).reset_index()
            x = (np.arange(len(agg), dtype=float) if kind == "common_valid_dates"
                 else agg["forecast_lead_day"].to_numpy(dtype=float))
            agg["model"] = model
            stats.append(agg)
            ax.plot(x, 100 * agg["median"].to_numpy(), color=COLORS[model],
                    linewidth=2.4, marker="o", markersize=3.7, label=LABELS[model])
            ax.fill_between(x, 100 * agg["q25"].to_numpy(),
                            100 * agg["q75"].to_numpy(),
                            color=COLORS[model], alpha=.12, linewidth=0)
        if kind == "common_valid_dates":
            dates = sorted(pd.read_csv(sources[kind] / "matched_positions.csv")
                           .date.dropna().unique())
            ax.set_xticks(np.arange(len(dates)))
            ax.set_xticklabels([str(d)[5:] for d in dates])
            ax.set_xlabel("Valid date (2024, MM-DD)", labelpad=12, fontsize=15)
            ax.set_title("Eddy amplitude absolute error — common valid dates (18–25 July 2024)", pad=14)
        else:
            ax.set_xlabel("Forecast lead time (days since model initialization)", labelpad=12, fontsize=15)
            ax.set_title("Eddy amplitude absolute error — full forecast horizons", pad=14)
            ax.set_xlim(left=0, right=27)
            ax.set_xticks([0, 3, 6, 9, 13, 17, 20, 24, 27])
        ax.set_ylabel("Absolute amplitude error (cm)", fontsize=15)
        ax.tick_params(axis="both", which="major", labelsize=13)
        ax.set_ylim(bottom=0)
        ax.grid(alpha=.22)
        ax.legend(loc="upper left", frameon=False, ncol=2, fontsize=12)
        fig.text(.5, .025, "Lines: median absolute error. Bands: 25th–75th percentiles. "
                 "Same initially matched eddy pairs (50 km threshold).",
                 ha="center", fontsize=9, color="#555555")
        stem = output_dir / f"eddy_amplitude_error_{kind}"
        fig.savefig(stem.with_suffix(".png"), dpi=250, bbox_inches="tight")
        plt.close(fig)
        if not stats:
            raise ValueError(f"No valid amplitude data for {kind}; check matching CSVs and TRACK NetCDFs")
        if stats:
            pd.concat(stats, ignore_index=True).to_csv(
                output_dir / f"eddy_amplitude_error_{kind}.csv", index=False)
        if paired:
            pd.concat(paired, ignore_index=True).to_csv(
                output_dir / f"eddy_amplitude_pairs_{kind}.csv", index=False)
        print(f"Saved {stem}.png", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path,
                        help="Root containing GLONET, GLOW, GLO12 and GLOENS")
    parser.add_argument("--comparison-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    comparison = args.comparison_dir or args.data_dir / "COMPARISON"
    plot(args.data_dir, comparison, args.output_dir or comparison / "FIGURES")


if __name__ == "__main__":
    main()
