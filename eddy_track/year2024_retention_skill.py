"""Compare pooled 2024 tracking retention against independent daily detection skill.

Reads existing seven-system contingency and retention CSVs. No tracking or
matching is recomputed. All skill metrics are pooled over common days 1-9;
retention is measured at day 9 for initially matched fixed track IDs.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

METRICS = {
    "pod": ("Probability of detection (POD)", True),
    "far": ("False-alarm ratio (FAR)", False),
    "csi": ("Critical success index (CSI)", True),
    "frequency_bias": ("Frequency bias", None),
}
GLO12 = ("GLO12_025", "GLO12_CONS", "GLO12_LP15_CONS", "GLO12_NATIVE")
COLORS = {
    "GLONET": "#2CA02C", "GLONET3": "#D62728",
    "GLOENS_MEAN": "#1F77B4", "GLO12_025": "#E68613",
    "GLO12_NATIVE": "#4B176B", "GLO12_LP15_CONS": "#B85CBB",
    "GLO12_CONS": "#008C95",
    "GLO12_NATIVE45_LP15": "#FF7F0E",
}

def run(root: Path):
    figdir = root / "COMPARISON_FULL" / "FIGURES"
    skill_path = figdir / "year2024_sixway_contingency_summary.csv"
    retention_path = figdir / "year2024_sixway_tracking_retention_day9.csv"
    for path in (skill_path, retention_path):
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path}. Run --stage contingency and --stage retention.")
    skill = pd.read_csv(skill_path)
    retention = pd.read_csv(retention_path)
    required_skill = {"model", *METRICS}
    required_retention = {"configuration", "retention_percent", "initial_pairs", "retained_pairs"}
    if not required_skill.issubset(skill):
        raise ValueError(f"{skill_path}: missing {sorted(required_skill - set(skill))}")
    if not required_retention.issubset(retention):
        raise ValueError(f"{retention_path}: missing {sorted(required_retention - set(retention))}")
    if skill.model.duplicated().any() or retention.configuration.duplicated().any():
        raise ValueError("Duplicate configuration in input summaries")
    merged = retention.merge(skill, left_on="configuration", right_on="model",
                             how="outer", validate="one_to_one", indicator=True)
    if not (merged["_merge"] == "both").all():
        raise ValueError("Skill and retention configurations differ: " +
                         str(merged.loc[merged["_merge"] != "both",
                                        ["configuration", "model", "_merge"]].to_dict("records")))
    merged = merged.drop(columns=["model", "_merge"])
    merged.to_csv(figdir / "year2024_retention_vs_skill_summary.csv", index=False)

    fig, axes = plt.subplots(2, 2, figsize=(15, 11), constrained_layout=True)
    for ax, (metric, (name, higher_is_better)) in zip(axes.flat, METRICS.items()):
        for r in merged.itertuples(index=False):
            x = float(r.retention_percent)
            y = float(getattr(r, metric))
            ax.scatter(x, y, s=90, color=COLORS.get(r.configuration, "gray"), zorder=3)
            ax.annotate(r.configuration, (x, y), xytext=(5, 5),
                        textcoords="offset points", fontsize=8)
        ax.set_xlabel("Day 9 tracking retention (%)")
        ax.set_ylabel(name)
        ax.set_title(f"Day 9 retention vs. 9-day pooled {metric.upper()}")
        ax.grid(alpha=0.25)
        if metric == "frequency_bias":
            ax.axhline(1, linestyle="--", color="gray", alpha=0.6)
        ax.margins(x=0.16, y=0.17)
    fig.suptitle("2024: tracking continuity versus independent detection skill (52 cycles)",
                 fontsize=15)
    fig.savefig(figdir / "year2024_retention_vs_skill.png", dpi=220)
    plt.close(fig)

    available = merged.set_index("configuration")
    if all(x in available.index for x in GLO12):
        base = available.loc["GLO12_025"]
        rows = []
        for name in GLO12:
            r = available.loc[name]
            rows.append({
                "configuration": name,
                "retention_day9_percent": r.retention_percent,
                "retention_delta_vs_linear_pp": r.retention_percent - base.retention_percent,
                **{m: r[m] for m in METRICS},
                **{m + "_delta_vs_linear": r[m] - base[m] for m in METRICS},
            })
        pd.DataFrame(rows).to_csv(figdir / "year2024_glo12_regridding_effects.csv", index=False)
    print("\nTracking retention versus pooled detection skill:")
    print(merged[["configuration", "retention_percent", *METRICS]].sort_values(
        "retention_percent", ascending=False).to_string(index=False))
    print(f"\nSaved plots and CSV tables to {figdir}")
    print("Note: retention uses fixed initial pairs; POD/FAR/CSI use independent daily rematching.")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-root", type=Path, default=Path("data_2024_sevenway"))
    args = p.parse_args()
    run(args.output_root)

if __name__ == "__main__":
    main()
