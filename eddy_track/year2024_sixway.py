"""Annual six-configuration eddy intercomparison, including two GLO12 experiments.

Use the original four-system root for GLONET/GLOW/GLO12/GLOENS, plus two
separate GLO12-only roots. Outputs never overwrite the original comparisons.
"""
from __future__ import annotations
import argparse
from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from eddy_track.compare_forecasts_obs import compare
from eddy_track.ond2024_contingency import load_daily, match_day, scores
from eddy_track.match_obs_gloens import POLARITIES
from eddy_track.plot_comparison_skill import COLORS

SOURCES = {
    "GLONET": ("base", "GLONET", 10),
    "GLONET3": ("base", "GLOW", 9),
    "GLOENS_MEAN": ("base", "GLOENS_MEAN", 28),
    "GLO12_025": ("base", "GLO12", 10),
    "GLO12_NATIVE": ("native", "GLO12", 10),
    "GLO12_LP15_CONS": ("filtered", "GLO12", 10),
}
LABELS = {
    "GLONET": "GLONET", "GLONET3": "GLONET3",
    "GLOENS_MEAN": "GLOENS mean", "GLO12_025": "GLO12 linear 0.25°",
    "GLO12_NATIVE": "GLO12 native 1/12°",
    "GLO12_LP15_CONS": "GLO12 Gaussian 15 km + conservative 0.25°",
}
PALETTE = {
    **{k: COLORS.get(k, "gray") for k in ("GLONET", "GLOENS_MEAN")},
    "GLONET3": COLORS.get("GLOW", "tab:orange"),
    "GLO12_025": "#E68613", "GLO12_NATIVE": "#4B176B",
    "GLO12_LP15_CONS": "#B85CBB",
}

def cycle_dates():
    for i in range(52):
        wed = date(2024, 1, 3) + timedelta(days=7 * i)
        yield wed.strftime("%Y%m%d"), wed, wed + timedelta(days=1)

def track_path(root, cycle, model, polarity):
    base = root / "CYCLES" / cycle
    if model == "GLOENS_MEAN":
        return base / "GLOENS" / "TRACK_FULL" / f"{polarity}.nc"
    return base / model / cycle / "TRACK_FULL" / f"{polarity}.nc"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-root", type=Path, default=Path("data_2024"))
    p.add_argument("--native-root", type=Path, default=Path("data_2024_glo12_native"))
    p.add_argument("--filtered-root", type=Path, default=Path("data_2024_lp15_cons"))
    p.add_argument("--conservative-root", type=Path, default=None,
                   help="Include seventh configuration: GLO12 conservative 0.25-degree without Gaussian filtering")
    p.add_argument("--obs-root", type=Path, default=None)
    p.add_argument("--output-root", type=Path, default=Path("data_2024_sixway"))
    p.add_argument("--max-distance-km", type=float, default=50)
    p.add_argument("--stage", choices=("all", "compare", "contingency", "plots", "retention"), default="all")
    args = p.parse_args()
    if args.max_distance_km <= 0:
        p.error("--max-distance-km must be positive")
    roots = {"base": args.base_root, "native": args.native_root, "filtered": args.filtered_root}
    if args.conservative_root is not None:
        roots["conservative"] = args.conservative_root
        SOURCES["GLO12_CONS"] = ("conservative", "GLO12", 10)
        LABELS["GLO12_CONS"] = "GLO12 conservative 0.25° (no Gaussian)"
        PALETTE["GLO12_CONS"] = "#008C95"
    obs_root = args.obs_root or args.base_root / "OBS_FULL"
    obs_dir = obs_root / "GLOENS/OBS/TRACK"
    out = args.output_root / "COMPARISON_FULL"
    figdir = out / "FIGURES"
    figdir.mkdir(parents=True, exist_ok=True)
    for pol in POLARITIES:
        if not (obs_dir / f"{pol}.nc").is_file():
            raise FileNotFoundError(obs_dir / f"{pol}.nc")

    if args.stage in ("all", "compare"):
        for cycle, wed, thu in cycle_dates():
            for label, (root_key, model, horizon) in SOURCES.items():
                root = roots[root_key]
                init = thu if model == "GLOENS_MEAN" else wed
                for pol in POLARITIES:
                    path = track_path(root, cycle, model, pol)
                    if not path.is_file():
                        raise FileNotFoundError(path)
                cycle_root = root / "CYCLES" / cycle
                target = out / cycle / label
                print(f"Compare {cycle} {label} ({horizon} days)", flush=True)
                compare(cycle_root, init.isoformat(), horizon, args.max_distance_km,
                        target, (model,),
                        init_dates={model: init.isoformat()},
                        track_subdir="TRACK_FULL", obs_track_dir=obs_dir)
    if args.stage in ("all", "contingency"):
        rows = []
        obs_cache = {}
        for cycle, wed, thu in cycle_dates():
            for label, (root_key, model, _) in SOURCES.items():
                init = thu if model == "GLOENS_MEAN" else wed
                for pol in POLARITIES:
                    key = (init.isoformat(), pol)
                    if key not in obs_cache:
                        obs_cache[key] = load_daily(obs_dir / f"{pol}.nc", init.isoformat(), 9)
                    obs = obs_cache[key]
                    predicted = load_daily(track_path(roots[root_key], cycle, model, pol),
                                           init.isoformat(), 9)
                    for day in range(9):
                        hits = len(match_day(obs[day], predicted[day], args.max_distance_km))
                        misses = len(obs[day]) - hits
                        false = len(predicted[day]) - hits
                        rows.append(dict(cycle=cycle, model=label, polarity=pol,
                                         forecast_day=day+1, observed=len(obs[day]),
                                         forecast=len(predicted[day]), hits=hits,
                                         misses=misses, false_alarms=false,
                                         **scores(hits, misses, false)))
            print(f"Contingency {cycle} complete", flush=True)
        daily = pd.DataFrame(rows)
        daily.to_csv(figdir / "year2024_sixway_contingency_daily.csv", index=False)
        def aggregate(keys):
            frame = daily.groupby(keys, as_index=False)[
                ["observed", "forecast", "hits", "misses", "false_alarms"]].sum()
            for metric in ("pod", "far", "success_ratio", "csi", "f1", "frequency_bias"):
                frame[metric] = [scores(r.hits, r.misses, r.false_alarms)[metric]
                                 for r in frame.itertuples()]
            return frame
        aggregate(["model", "polarity", "forecast_day"]).to_csv(
            figdir / "year2024_sixway_contingency_polarity_day.csv", index=False)
        aggregate(["model", "forecast_day"]).to_csv(
            figdir / "year2024_sixway_contingency_by_day.csv", index=False)
        summary = aggregate(["model"])
        summary.to_csv(figdir / "year2024_sixway_contingency_summary.csv", index=False)
        print(summary.to_string(index=False))
    if args.stage in ("all", "plots"):
        summary_rows = []
        positions = []
        for cycle, _, _ in cycle_dates():
            for label, (_, _, horizon) in SOURCES.items():
                folder = out / cycle / label
                summary = pd.read_csv(folder / "summary.csv")
                summary["configuration"] = label
                summary["cycle"] = cycle
                summary_rows.append(summary)
                pos = pd.read_csv(folder / "matched_positions.csv")
                pos["configuration"] = label
                pos["cycle"] = cycle
                pos["forecast_day"] = pos["forecast_lead_day"].astype(int) + 1
                if not pos["forecast_day"].between(1, horizon).all():
                    raise ValueError(f"Invalid forecast days: {folder}")
                positions.append(pos)
        captures = pd.concat(summary_rows, ignore_index=True)
        captures.to_csv(figdir / "year2024_sixway_initial_capture_by_cycle.csv", index=False)
        capture = captures.groupby("configuration", as_index=False)[
            ["observed_initial_tracks", "model_initial_tracks", "matched_initial_tracks"]].sum()
        capture["capture_percent"] = (100 * capture.matched_initial_tracks /
                                       capture.observed_initial_tracks)
        capture.to_csv(figdir / "year2024_sixway_initial_capture_summary.csv", index=False)
        print(capture.to_string(index=False))
        allpos = pd.concat(positions, ignore_index=True)
        allpos.to_csv(figdir / "year2024_sixway_matched_positions.csv", index=False)
        valid = allpos.dropna(subset=["position_error_km"])
        agg = valid.groupby(["configuration", "forecast_day"], as_index=False).position_error_km.agg(
            count="count", median="median", mean="mean",
            q25=lambda x: x.quantile(.25), q75=lambda x: x.quantile(.75))
        agg.to_csv(figdir / "year2024_sixway_position_by_day.csv", index=False)
        for common in (True, False):
            fig, ax = plt.subplots(figsize=(12, 7))
            for label in SOURCES:
                sub = agg[agg.configuration == label].sort_values("forecast_day")
                if common:
                    sub = sub[sub.forecast_day <= 9]
                ax.plot(sub.forecast_day, sub["median"], label=LABELS[label],
                        color=PALETTE[label], linewidth=2, marker="o", markersize=3)
                ax.fill_between(sub.forecast_day, sub.q25, sub.q75,
                                color=PALETTE[label], alpha=.10)
            ax.set_xlabel("Forecast day (day 1 = initialization)")
            ax.set_ylabel("Eddy-center position error (km)")
            ax.set_title("2024: configuration position error " +
                         ("(common 9 days)" if common else "(full horizons)"))
            ax.set_xlim(1, 9 if common else 28)
            ax.set_ylim(bottom=0)
            ax.grid(alpha=.2)
            ax.legend(fontsize=9, ncol=2)
            fig.tight_layout()
            fig.savefig(figdir / ("year2024_sixway_position_9d.png" if common else
                                  "year2024_sixway_position_full.png"), dpi=220)
            plt.close(fig)
        contingency_path = figdir / "year2024_sixway_contingency_by_day.csv"
        if contingency_path.is_file():
            byday = pd.read_csv(contingency_path)
            for metric in ("pod", "far", "csi", "frequency_bias"):
                fig, ax = plt.subplots(figsize=(11, 6))
                for label in SOURCES:
                    sub = byday[byday.model == label].sort_values("forecast_day")
                    ax.plot(sub.forecast_day, sub[metric], marker="o",
                            label=LABELS[label], color=PALETTE[label])
                ax.set_xlabel("Forecast day")
                ax.set_ylabel(metric.upper())
                ax.set_title("2024 configuration contingency: " + metric.upper())
                ax.set_xlim(1, 9)
                ax.set_xticks(range(1, 10))
                ax.grid(alpha=.2)
                ax.legend(fontsize=9, ncol=2)
                fig.tight_layout()
                fig.savefig(figdir / f"year2024_sixway_{metric}.png", dpi=220)
                plt.close(fig)
        print(f"Saved six-way diagnostics to {figdir}", flush=True)
    if args.stage in ("all", "retention"):
        # When launched with python -m, this file runs as __main__, while the
        # retention module imports eddy_track.year2024_sixway by its canonical
        # name. Synchronize optional configurations across those module objects.
        import eddy_track.year2024_sixway as canonical
        canonical.SOURCES.update(SOURCES)
        canonical.LABELS.update(LABELS)
        canonical.PALETTE.update(PALETTE)
        from eddy_track.year2024_sixway_retention import run as run_retention
        run_retention(args.output_root)

if __name__ == "__main__":
    main()
