"""Daily persistence of initially matched observed/forecast eddy track pairs.

A pair is retained at forecast day d when both original fixed track IDs have
real (nonvirtual) positions on that date. No rematching or distance threshold
is applied after initialization. Denominator includes every initial pair.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from eddy_track.plot_comparison_skill import MODELS,LABELS,COLORS

HORIZONS={"GLONET":10,"GLOW":9,"GLO12":10,"GLOENS_MEAN":28}
KEYS=["polarity","obs_track","model_track"]

def compute(root:Path):
    base=root/"COMPARISON_FULL"
    records=[]
    cycles=sorted(p.name for p in base.glob("20??????") if p.is_dir())
    if len(cycles)!=13:raise ValueError(f"Expected 13 OND cycles, found {len(cycles)}")
    for cycle in cycles:
        for model in MODELS:
            folder=base/cycle/model
            initial_path=folder/"initial_matches.csv"
            daily_path=folder/"matched_positions.csv"
            summary_path=folder/"summary.csv"
            for path in (initial_path,daily_path,summary_path):
                if not path.is_file():raise FileNotFoundError(path)
            initial=pd.read_csv(initial_path)
            daily=pd.read_csv(daily_path)
            summary=pd.read_csv(summary_path)
            if not set(KEYS).issubset(initial):raise ValueError(f"{initial_path}: missing pair IDs")
            if not set(KEYS+["forecast_lead_day","position_error_km"]).issubset(daily):
                raise ValueError(f"{daily_path}: missing required columns")
            if initial.duplicated(KEYS).any():raise ValueError(f"{initial_path}: duplicate initial pairs")
            n=len(initial)
            if n!=int(summary.matched_initial_tracks.sum()):
                raise ValueError(f"{folder}: initial match count disagrees with summary")
            if n==0:raise ValueError(f"{folder}: no initially matched pairs")
            if len(daily)!=n*HORIZONS[model]:
                raise ValueError(f"{daily_path}: expected {n*HORIZONS[model]} daily pair rows, got {len(daily)}")
            if daily.duplicated(KEYS+["forecast_lead_day"]).any():
                raise ValueError(f"{daily_path}: duplicate pair/day")
            if set(daily.forecast_lead_day.astype(int))!=set(range(HORIZONS[model])):
                raise ValueError(f"{daily_path}: incomplete forecast lead days")
            # A finite position error is produced only when BOTH fixed tracks
            # have positions; NaN means at least one is absent on this day.
            for day,group in daily.groupby("forecast_lead_day"):
                if len(group)!=n:raise ValueError(f"{daily_path}: incomplete pairs at day {day}")
                retained=int(np.isfinite(group.position_error_km).sum())
                records.append({"cycle":cycle,"model":model,"forecast_day":int(day)+1,
                                "initial_pairs":n,"retained_pairs":retained,
                                "retention_percent":100*retained/n})
    per_cycle=pd.DataFrame(records)
    pooled=per_cycle.groupby(["model","forecast_day"],as_index=False).agg(
        cycles=("cycle","nunique"),initial_pairs=("initial_pairs","sum"),
        retained_pairs=("retained_pairs","sum"))
    pooled["retention_percent"]=100*pooled.retained_pairs/pooled.initial_pairs
    return per_cycle,pooled

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root",type=Path)
    args=parser.parse_args()
    out=args.output_root/"COMPARISON_FULL/FIGURES"
    out.mkdir(parents=True,exist_ok=True)
    per_cycle,pooled=compute(args.output_root)
    per_cycle.to_csv(out/"ond2024_full_tracking_retention_by_cycle.csv",index=False)
    pooled.to_csv(out/"ond2024_full_tracking_retention.csv",index=False)
    fig,ax=plt.subplots(figsize=(12,7))
    for model in MODELS:
        d=pooled[pooled.model==model].sort_values("forecast_day")
        ax.plot(d.forecast_day,d.retention_percent,label=LABELS[model],
                color=COLORS[model],linewidth=2.5,marker="o",markersize=3.5)
    ax.set(xlim=(1,28),ylim=(0,105),xlabel="Forecast day (day 1 = initialization)",
           ylabel="Initially matched pairs still tracked (%)",
           title="OND 2024 — Full-horizon eddy tracking retention")
    ax.set_xticks([1,4,7,10,14,18,21,25,28])
    ax.grid(alpha=.2)
    ax.legend(frameon=False,ncol=2)
    fig.text(.5,.025,"Both original track IDs must have valid positions; no rematching.\n"
             "Pooled across 13 weekly cycles; model horizons: 10 / 9 / 10 / 28 days.",
             ha="center",fontsize=10,color="#555555")
    fig.subplots_adjust(bottom=.20)
    fig.savefig(out/"ond2024_full_tracking_retention.png",dpi=250,bbox_inches="tight")
    plt.close(fig)
    last=pooled.loc[pooled.groupby("model").forecast_day.idxmax()].copy()
    last["horizon_days"]=last.forecast_day
    last[["model","horizon_days","initial_pairs","retained_pairs","retention_percent"]].to_csv(
        out/"ond2024_full_tracking_retention_summary.csv",index=False)
    print("Saved",out/"ond2024_full_tracking_retention.png")
    print(last[["model","horizon_days","retention_percent"]].to_string(index=False))

if __name__=="__main__":main()
