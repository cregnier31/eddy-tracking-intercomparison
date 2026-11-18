"""2D eddy diagnostics inspired by eddy_diags.my_classes.Plots.

Plots 2D radius-amplitude histograms and geographic eddy density from REAL
tracked positions for each 2024 forecast configuration and OBS. All model
samples use the common 9-day horizon across 52 cycles. The same observed
dates are repeated across cycles, intentionally matching forecast exposure.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from eddy_track.ond2024_contingency import load_daily
from eddy_track.match_obs_gloens import POLARITIES
from eddy_track.year2024_sixway import SOURCES, LABELS, PALETTE, cycle_dates, track_path

def collect(roots, obs_dir):
    rows = []
    cache = {}
    for cycle, wed, thu in cycle_dates():
        for label, (key, model, _) in SOURCES.items():
            init = thu if model == "GLOENS_MEAN" else wed
            for polarity in POLARITIES:
                source = track_path(roots[key], cycle, model, polarity)
                data = load_daily(source, init.isoformat(), 9)
                for day, positions in data.items():
                    for track_id, (lon, lat, radius, amplitude) in positions.items():
                        rows.append((cycle, label, polarity, day+1, lon, lat, radius, amplitude))
        # OBS for both initialization calendars: Wednesday and Thursday.
        for init, label in ((wed, "OBS_WED"), (thu, "OBS_THU")):
            for polarity in POLARITIES:
                key = (init.isoformat(), polarity)
                if key not in cache:
                    cache[key] = load_daily(obs_dir / f"{polarity}.nc", init.isoformat(), 9)
                for day, positions in cache[key].items():
                    for track_id, (lon, lat, radius, amplitude) in positions.items():
                        rows.append((cycle, label, polarity, day+1, lon, lat, radius, amplitude))
        print(f"Loaded 2D diagnostic positions: {cycle}", flush=True)
    return pd.DataFrame(rows, columns=["cycle", "configuration", "polarity",
                                        "forecast_day", "longitude", "latitude",
                                        "radius_km", "amplitude_cm"])

def save_maps(data, output, cell_deg):
    xedges = np.arange(-80, 0 + cell_deg*0.5, cell_deg)
    yedges = np.arange(20, 65 + cell_deg*0.5, cell_deg)
    if xedges[-1] < 0: xedges = np.r_[xedges, 0]
    if yedges[-1] < 65: yedges = np.r_[yedges, 65]
    names = list(SOURCES) + ["OBS_WED", "OBS_THU"]
    density = {}
    for label in names:
        sub = data[data.configuration == label]
        count, _, _ = np.histogram2d(sub.latitude, sub.longitude, bins=[yedges, xedges])
        density[label] = count / (52 * 9)
    vmax = max(np.nanmax(a) for a in density.values())
    fig, axes = plt.subplots(3, 3, figsize=(17, 15), sharex=True, sharey=True)
    for ax, label in zip(axes.flat, names):
        im = ax.pcolormesh(xedges, yedges, density[label], cmap="viridis",
                           vmin=0, vmax=max(vmax, 1e-9), shading="auto")
        ax.set_title(LABELS.get(label, label))
        ax.set_aspect("auto")
    for ax in list(axes.flat)[len(names):]: ax.axis("off")
    for ax in axes[-1]: ax.set_xlabel("Longitude (°)")
    for ax in axes[:, 0]: ax.set_ylabel("Latitude (°)")
    fig.colorbar(im, ax=axes.ravel().tolist(), label="Mean tracked eddy-day instances per grid cell per forecast day", shrink=.7)
    fig.suptitle("2024 eddy geographic density — 52 cycles, common 9 days", fontsize=16)
    fig.savefig(output / "year2024_2d_geographic_density.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    for label, arr in density.items():
        pd.DataFrame(arr, index=(yedges[:-1]+yedges[1:])/2,
                     columns=(xedges[:-1]+xedges[1:])/2).to_csv(
            output / f"year2024_2d_density_{label}.csv")

def save_histograms(data, output):
    names = list(SOURCES) + ["OBS_WED", "OBS_THU"]
    r_edges = np.arange(0, 205, 5)
    a_edges = np.arange(0, 40.5, .5)
    counts = {}
    for label in names:
        sub = data[data.configuration == label]
        r = sub.radius_km.to_numpy(dtype=float)
        a = sub.amplitude_cm.to_numpy(dtype=float)
        valid = np.isfinite(r) & np.isfinite(a) & (r >= 0) & (a >= 0)
        if valid.sum() == 0:
            print(f"WARNING: {label} has no valid radius/amplitude pairs; 2D histogram unavailable")
            continue
        counts[label] = np.histogram2d(r[valid], a[valid], bins=[r_edges, a_edges])[0]
    if not counts:
        print("WARNING: no radius/amplitude variables available in tracked files; skipping 2D histograms")
        return
    vmax = max(np.max(c) for c in counts.values())
    fig, axes = plt.subplots(3, 3, figsize=(17, 14), sharex=True, sharey=True)
    for ax, label in zip(axes.flat, names):
        if label not in counts:
            ax.text(.5,.5,"Radius/amplitude unavailable",ha="center",va="center",transform=ax.transAxes)
        else:
            im = ax.pcolormesh(r_edges, a_edges, counts[label].T, cmap="magma",
                               norm=LogNorm(vmin=1, vmax=max(2,vmax)), shading="auto")
        ax.set_title(LABELS.get(label, label))
    for ax in list(axes.flat)[len(names):]: ax.axis("off")
    for ax in axes[-1]: ax.set_xlabel("Effective radius (km)")
    for ax in axes[:,0]: ax.set_ylabel("Amplitude (cm)")
    fig.colorbar(im, ax=axes.ravel().tolist(), label="Eddy-day instances (log scale)", shrink=.7)
    fig.suptitle("2024 radius–amplitude 2D histograms — common 9 days", fontsize=16)
    fig.savefig(output / "year2024_2d_radius_amplitude.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    for label, arr in counts.items():
        pd.DataFrame(arr, index=(r_edges[:-1]+r_edges[1:])/2,
                     columns=(a_edges[:-1]+a_edges[1:])/2).to_csv(
            output / f"year2024_2d_radius_amplitude_{label}.csv")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-root",type=Path,default=Path("data_2024"))
    p.add_argument("--native-root",type=Path,default=Path("data_2024_glo12_native"))
    p.add_argument("--filtered-root",type=Path,default=Path("data_2024_lp15_cons"))
    p.add_argument("--conservative-root",type=Path)
    p.add_argument("--obs-root",type=Path)
    p.add_argument("--output-root",type=Path,default=Path("data_2024_sixway"))
    p.add_argument("--cell-deg",type=float,default=2.0)
    args=p.parse_args()
    if args.cell_deg <= 0: p.error("--cell-deg must be positive")
    roots={"base":args.base_root,"native":args.native_root,"filtered":args.filtered_root}
    if args.conservative_root is not None:
        roots["conservative"]=args.conservative_root
        SOURCES["GLO12_CONS"]=("conservative","GLO12",10)
        LABELS["GLO12_CONS"]="GLO12 conservative 0.25° (no Gaussian)"
        PALETTE["GLO12_CONS"]="#008C95"
    obs_dir=(args.obs_root or args.base_root/"OBS_FULL")/"GLOENS/OBS/TRACK"
    out=args.output_root/"COMPARISON_FULL/FIGURES"
    out.mkdir(parents=True,exist_ok=True)
    data=collect(roots,obs_dir)
    save_maps(data,out,args.cell_deg)
    save_histograms(data,out)
    print("Saved 2D diagnostics in",out)

if __name__=="__main__": main()
