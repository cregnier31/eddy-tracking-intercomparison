"""Plot OND 2024 full forecast horizons for position and amplitude error."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from eddy_track.plot_comparison_skill import MODELS,LABELS,COLORS
from eddy_track.plot_comparison_amplitude import amplitudes

HORIZONS={"GLONET":10,"GLOW":9,"GLO12":10,"GLOENS_MEAN":28}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output_root",type=Path)
    a=p.parse_args()
    root=a.output_root
    out=root/"COMPARISON_FULL/FIGURES"
    out.mkdir(parents=True,exist_ok=True)
    position=[]
    amplitude=[]
    for csv in sorted(root.glob("COMPARISON_FULL/20??????/*/matched_positions.csv")):
        model=csv.parent.name
        cycle=csv.parent.parent.name
        if model not in MODELS: continue
        df=pd.read_csv(csv)
        if df.empty: continue
        df["cycle"]=cycle
        df["forecast_day"]=df.forecast_lead_day.astype(int)+1
        if not df.forecast_day.between(1,HORIZONS[model]).all():
            raise ValueError(f"Invalid lead days in {csv}")
        position.append(df)
        cycle_root=root/"CYCLES"/cycle
        init=cycle
        for pol in ("Cyclonic","Anticyclonic"):
            sub=df[(df.polarity==pol)&df.position_error_km.notna()].copy()
            if sub.empty: continue
            obs_path=root/"OBS_FULL/GLOENS/OBS/TRACK"/f"{pol}.nc"
            model_path=(cycle_root/"GLOENS/TRACK_FULL"/f"{pol}.nc" if model=="GLOENS_MEAN"
                        else cycle_root/model/init/"TRACK_FULL"/f"{pol}.nc")
            obs=amplitudes(obs_path,"obs")
            mod=amplitudes(model_path,"model")
            sub=sub.merge(obs,on=["obs_track","date"],how="left",validate="many_to_one")
            sub=sub.merge(mod,on=["model_track","date"],how="left",validate="many_to_one")
            sub["amplitude_abs_error_m"]=(sub.model_amplitude_m-sub.obs_amplitude_m).abs()
            amplitude.append(sub)
    if len(position)!=52: raise ValueError(f"Expected 52 full-horizon model-cycle CSVs (13 x 4); found {len(position)}")
    pos=pd.concat(position,ignore_index=True)
    amp=pd.concat(amplitude,ignore_index=True) if amplitude else pd.DataFrame()
    for metric,frame,stem,ylabel,scale in (
        ("position_error_km",pos,"ond2024_full_position_error",
         "Eddy-center position error (km)",1),
        ("amplitude_abs_error_m",amp,"ond2024_full_amplitude_error",
         "Absolute eddy amplitude error (cm)",100),
    ):
        if frame.empty: raise ValueError(f"No data for {metric}")
        fig,ax=plt.subplots(figsize=(12,7))
        fig.subplots_adjust(left=.13,right=.97,top=.89,bottom=.24)
        rows=[]
        for model in MODELS:
            sub=frame[(frame.model==model)&np.isfinite(frame[metric])]
            if sub.empty:
                raise ValueError(f"No finite {metric} for {model}")
            agg=sub.groupby("forecast_day")[metric].agg(
                n="size",median="median",mean="mean",
                q25=lambda x:x.quantile(.25),q75=lambda x:x.quantile(.75)).reset_index()
            agg["model"]=model
            rows.append(agg)
            x=agg.forecast_day.to_numpy()
            ax.plot(x,agg["median"].to_numpy()*scale,color=COLORS[model],
                    linewidth=2.4,marker="o",markersize=3.5,label=LABELS[model])
            ax.fill_between(x,agg.q25.to_numpy()*scale,agg.q75.to_numpy()*scale,
                            color=COLORS[model],alpha=.12)
        ax.set_title("OND 2024 — Full-horizon "+("position" if scale==1 else "amplitude")+" error",
                     fontsize=20)
        ax.set_xlabel("Forecast day (day 1 = model initialization)",fontsize=16)
        ax.set_ylabel(ylabel,fontsize=16)
        ax.set_xlim(1,28)
        ax.set_xticks([1,4,7,10,14,18,21,25,28])
        ax.set_ylim(bottom=0)
        ax.grid(alpha=.2)
        ax.legend(ncol=2,frameon=False)
        fig.text(.5,.025,"Median and interquartile range; weekly OND cycles; 50 km initial matching.\n"
                 "Model-specific initialization dates; observations must extend into January 2025.",
                 ha="center",fontsize=11,color="#555555")
        fig.savefig(out/f"{stem}.png",dpi=250,bbox_inches="tight")
        plt.close(fig)
        pd.concat(rows,ignore_index=True).to_csv(out/f"{stem}.csv",index=False)
        print(f"Saved {out / (stem+'.png')}",flush=True)

if __name__=="__main__":
    main()
