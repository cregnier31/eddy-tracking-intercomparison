"""Full-horizon year 2024 forecast detection, tracking, and matching.

Separate output tree avoids corrupting the existing common 8-day experiment.
OBS tracks must cover 2024-01-03 through 2025-01-22 for all forecast days.
"""
from __future__ import annotations
import argparse
from datetime import date,timedelta
from pathlib import Path
import subprocess,sys
from eddy_run.ond2024 import gloens_store,track_gloens,link,FORECAST_DAYS

MODELS=("GLONET","GLOW","GLO12","GLOENS_MEAN")
BOUNDS=["--lon-min","-80","--lon-max","0","--lat-min","20","--lat-max","65","--resolution","0.25"]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output_root",type=Path,help="Separate output directory, e.g. data_2024")
    p.add_argument("--stage",choices=("detect","track","compare"),required=True)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--obs-root",type=Path,required=True,help="Directory containing GLOENS/OBS/TRACK with full observation period")
    p.add_argument("--models",nargs="+",choices=MODELS,default=list(MODELS))
    a=p.parse_args()
    root=a.output_root
    if a.stage=="compare" and set(a.models)!=set(MODELS):
        p.error("Compare requires all four models")
    if a.execute and a.stage in ("track","compare"):
        for pol in ("Cyclonic","Anticyclonic"):
            f=a.obs_root/"GLOENS/OBS/TRACK"/f"{pol}.nc"
            if not f.is_file():
                p.error(f"Missing observed track file: {f}")
    for week in range(52):
        wed=date(2024,1,3)+timedelta(days=7*week)
        thu=wed+timedelta(days=1)
        cycle=root/"CYCLES"/wed.strftime("%Y%m%d")
        for model in a.models:
            init=thu if model=="GLOENS_MEAN" else wed
            days=FORECAST_DAYS[model]
            if a.stage=="detect":
                if model=="GLOENS_MEAN":
                    cmd=[sys.executable,"-m","eddy_detect.gloens_grid",
                         gloens_store(init),str(cycle),*BOUNDS,"--last-day",str(days)]
                else:
                    cmd=[sys.executable,"-m","eddy_detect.zarr_forecasts",model,
                         init.strftime("%Y%m%d"),str(cycle),*BOUNDS,
                         "--last-day",str(days),"--assume-ssh-metres"]
            elif a.stage=="track":
                if model=="GLOENS_MEAN":
                    print(f"+ Track {model} {init}",flush=True)
                    if a.execute: track_gloens(cycle,days,False)
                    continue
                cmd=[sys.executable,"-m","eddy_track.zarr_forecasts",model,
                     init.strftime("%Y%m%d"),str(cycle),"--expected-days",str(days)]
            else:
                continue
            print("+ "+" ".join(cmd),flush=True)
            if a.execute: subprocess.run(cmd,check=True)
        if a.stage=="compare":
            link(a.obs_root/"GLOENS/OBS",cycle/"GLOENS/OBS",not a.execute)
            for model in a.models:
                init=thu if model=="GLOENS_MEAN" else wed
                days=FORECAST_DAYS[model]
                # Match on each system's actual initialization day.
                out=root/"COMPARISON"/wed.strftime("%Y%m%d")/model
                cmd=[sys.executable,"-m","eddy_track.compare_forecasts_obs",
                     str(cycle),"--start",init.isoformat(),"--days",str(days),
                     "--init-wednesday",wed.isoformat(),"--models",model,
                     "--output-dir",str(out)]
                print("+ "+" ".join(cmd),flush=True)
                if a.execute: subprocess.run(cmd,check=True)

if __name__=="__main__":
    main()
