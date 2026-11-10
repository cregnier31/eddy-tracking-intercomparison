"""Assemble daily local DUACS NetCDF files into a regional ADT time series."""
from __future__ import annotations
import argparse
from datetime import date, timedelta
from pathlib import Path
import xarray as xr
import numpy as np

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive",type=Path,help="Root containing YYYY/MM/dt_global_allsat_phy_l4_YYYYMMDD_*.nc")
    p.add_argument("output",type=Path)
    p.add_argument("--start",default="2025-01-01")
    p.add_argument("--end",default="2025-01-22")
    a=p.parse_args()
    start=date.fromisoformat(a.start);end=date.fromisoformat(a.end)
    if end<start:p.error("end precedes start")
    if a.output.exists():p.error(f"Output already exists: {a.output}")
    pieces=[]
    for i in range((end-start).days+1):
        day=start+timedelta(days=i)
        files=sorted((a.archive/f"{day:%Y}"/f"{day:%m}").glob(f"dt_global_allsat_phy_l4_{day:%Y%m%d}_*.nc"))
        if len(files)!=1:raise ValueError(f"{day}: expected one daily NetCDF, found {len(files)}: {files}")
        with xr.open_dataset(files[0]) as ds:
            if "adt" not in ds:raise KeyError(f"{files[0]}: no adt")
            da=ds["adt"]
            if "longitude" not in da.coords or "latitude" not in da.coords:
                raise ValueError(f"{files[0]}: expected latitude/longitude coordinates")
            da=da.sel(longitude=slice(-80,0),latitude=slice(20,65))
            if da.sizes.get("longitude",0)==0 or da.sizes.get("latitude",0)==0:
                raise ValueError(f"{files[0]}: empty regional subset")
            if "time" in da.dims:
                if da.sizes["time"]!=1:raise ValueError(f"{files[0]}: expected one time sample")
                da=da.isel(time=0,drop=True)
            pieces.append(da.load().expand_dims(time=[np.datetime64(day.isoformat())]))
        print(f"Loaded {day}: {files[0].name}",flush=True)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    xr.concat(pieces,dim="time").to_dataset(name="adt").to_netcdf(a.output)
    print(f"Saved {a.output}",flush=True)

if __name__=="__main__":main()
