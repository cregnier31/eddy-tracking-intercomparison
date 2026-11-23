"""Full-horizon calendar-year 2024 forecast detection, tracking, and matching.

Separate output tree avoids corrupting the existing common 8-day experiment.
OBS tracks must cover 2024-01-03 through 2025-01-22 for all forecast days.
"""
from __future__ import annotations
import argparse
from datetime import date,timedelta
from pathlib import Path
import subprocess,sys
from eddy_run.ond2024 import gloens_store,FORECAST_DAYS
from eddy_track.gloens_members import DEFAULT_TEMPLATE, tracking_config
import shutil,tempfile

def track_gloens_full(cycle, days, execute):
    detect_dir=cycle/"GLOENS/DETECT"
    track_dir=cycle/"GLOENS/TRACK_FULL"
    for pol in ("Cyclonic","Anticyclonic"):
        files=sorted(detect_dir.glob(f"{pol}_GLOENS_*.nc"))
        if len(files)!=days: raise ValueError(f"{detect_dir}: {len(files)} {pol} files, expected {days}")
        exe=shutil.which("EddyTracking")
        if not exe: raise FileNotFoundError("EddyTracking")
        track_dir.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="full-gloens-") as tmp:
            yaml=Path(tmp)/f"{pol}.yaml"
            yaml.write_text(tracking_config(DEFAULT_TEMPLATE,detect_dir,track_dir,pol))
            subprocess.run([exe,str(yaml)],check=True)

MODELS=("GLONET","GLOW","GLO12","GLOENS_MEAN")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output_root",type=Path,help="Separate output directory, e.g. data_2024")
    p.add_argument("--stage",choices=("detect","track","compare"),required=True)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--lon-min",type=float,default=-80)
    p.add_argument("--lon-max",type=float,default=0)
    p.add_argument("--lat-min",type=float,default=20)
    p.add_argument("--lat-max",type=float,default=65)
    p.add_argument("--resolution",type=float,default=0.25)
    p.add_argument("--obs-root",type=Path,required=True,help="Directory containing GLOENS/OBS/TRACK with full observation period")
    p.add_argument("--models",nargs="+",choices=MODELS,default=list(MODELS))
    p.add_argument("--glo12-pixel-min",type=int,default=None,
                   help="GLO12 detection minimum pixel count; e.g. 45 for native area sensitivity")
    p.add_argument("--glo12-native-grid",action="store_true",
                   help="Detect unfiltered GLO12 on its native 1/12-degree grid")
    p.add_argument("--glo12-regrid-method",choices=("linear","conservative"),default="linear",
                   help="GLO12 detect stage: choose SSH interpolation method")
    p.add_argument("--glo12-gaussian-sigma-km",type=float,default=None,
                   help="GLO12 detect stage: native-grid Gaussian SSH low-pass before 0.25-degree interpolation")
    a=p.parse_args()
    root=a.output_root
    if not (-180 <= a.lon_min < a.lon_max <= 180 and
            -90 <= a.lat_min < a.lat_max <= 90 and a.resolution > 0):
        p.error("Invalid geographic bounds or resolution")
    bounds=["--lon-min",str(a.lon_min),"--lon-max",str(a.lon_max),
            "--lat-min",str(a.lat_min),"--lat-max",str(a.lat_max),
            "--resolution",str(a.resolution)]
    if a.glo12_pixel_min is not None and (a.glo12_pixel_min < 1 or a.stage != "detect" or a.models != ["GLO12"]):
        p.error("--glo12-pixel-min requires --stage detect --models GLO12 and a positive integer")
    if a.glo12_native_grid and (a.stage != "detect" or a.models != ["GLO12"] or
                                 a.glo12_regrid_method != "linear"):
        p.error("--glo12-native-grid requires GLO12-only detection without regridding")
    if a.glo12_regrid_method != "linear" and (a.stage != "detect" or a.models != ["GLO12"]):
        p.error("--glo12-regrid-method conservative requires --stage detect --models GLO12")
    if a.glo12_gaussian_sigma_km is not None:
        if a.glo12_gaussian_sigma_km <= 0 or a.stage != "detect" or a.models != ["GLO12"]:
            p.error("--glo12-gaussian-sigma-km requires --stage detect --models GLO12 and positive sigma")
    if a.stage=="compare" and set(a.models)!=set(MODELS):
        p.error("Compare requires all four models")
    if a.execute and a.stage=="compare":
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
                         gloens_store(init),str(cycle),*bounds,"--last-day",str(days)]
                else:
                    cmd=[sys.executable,"-m","eddy_detect.zarr_forecasts",model,
                         init.strftime("%Y%m%d"),str(cycle),*BOUNDS,
                         "--last-day",str(days),"--assume-ssh-metres"]
                    if model=="GLO12":
                        if a.glo12_native_grid:
                            cmd.append("--native-grid")
                        if a.glo12_pixel_min is not None:
                            cmd.extend(["--pixel-min",str(a.glo12_pixel_min)])
                        cmd.extend(["--regrid-method",a.glo12_regrid_method])
                        if a.glo12_gaussian_sigma_km is not None:
                            cmd.extend(["--gaussian-sigma-km",str(a.glo12_gaussian_sigma_km)])
            elif a.stage=="track":
                if model=="GLOENS_MEAN":
                    print(f"+ Track {model} {init}",flush=True)
                    if a.execute: track_gloens_full(cycle,days,True)
                    continue
                cmd=[sys.executable,"-m","eddy_track.zarr_forecasts",model,
                     init.strftime("%Y%m%d"),str(cycle),"--expected-days",str(days),"--track-subdir","TRACK_FULL"]
            else:
                continue
            print("+ "+" ".join(cmd),flush=True)
            if a.execute: subprocess.run(cmd,check=True)
        if a.stage=="compare":
            for model in a.models:
                init=thu if model=="GLOENS_MEAN" else wed
                days=FORECAST_DAYS[model]
                # Match on each system's actual initialization day.
                out=root/"COMPARISON_FULL"/wed.strftime("%Y%m%d")/model
                cmd=[sys.executable,"-m","eddy_track.compare_forecasts_obs",
                     str(cycle),"--start",init.isoformat(),"--days",str(days),
                     "--init-wednesday",wed.isoformat(),"--track-subdir","TRACK_FULL",
                     "--obs-track-dir",str(a.obs_root.resolve()/"GLOENS/OBS/TRACK"),"--models",model,
                     "--output-dir",str(out)]
                print("+ "+" ".join(cmd),flush=True)
                if a.execute: subprocess.run(cmd,check=True)

if __name__=="__main__":
    main()
