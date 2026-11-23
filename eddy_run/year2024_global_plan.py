"""Plan (but do not launch) the 2024 global four-system eddy experiment.

Tiles are computational partitions, NOT independent verification domains.
Eddies and tracks crossing tile edges must be deduplicated and stitched before
global scores can be computed. The current detectors/trackers do not do this.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path

MODELS = ("GLONET", "GLONET3", "GLOENS_MEAN", "GLO12_NATIVE45_LP15")
COLORS = {
    "GLONET": "#2CA02C",
    "GLONET3": "#D62728",
    "GLOENS_MEAN": "#1F77B4",
    "GLO12_NATIVE45_LP15": "#FF7F0E",
}
LONGITUDE_EDGES = (-180, -120, -60, 0, 60, 120, 180)
LATITUDE_EDGES = (-70, -35, 0, 35, 70)
# The native geostrophic calculation masks |latitude| < 5 degrees.
EQUATORIAL_MASK_DEGREES = 5.0
OVERLAP_DEGREES = 2.0


def tiles():
    """Yield core and padded bounds, wrapping longitude beyond +/-180 at the seam."""
    for iy, (south, north) in enumerate(zip(LATITUDE_EDGES, LATITUDE_EDGES[1:])):
        for ix, (west, east) in enumerate(zip(LONGITUDE_EDGES, LONGITUDE_EDGES[1:])):
            yield {
                "tile": f"lat{iy:02d}_lon{ix:02d}",
                "core_lon_min": west, "core_lon_max": east,
                "core_lat_min": south, "core_lat_max": north,
                "read_lon_min": west - OVERLAP_DEGREES,
                "read_lon_max": east + OVERLAP_DEGREES,
                "read_lat_min": max(-70, south - OVERLAP_DEGREES),
                "read_lat_max": min(70, north + OVERLAP_DEGREES),
                "crosses_equatorial_mask": south < EQUATORIAL_MASK_DEGREES and north > -EQUATORIAL_MASK_DEGREES,
                "touches_dateline": west == -180 or east == 180,
            }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-root", type=Path, default=Path("data_2024_global_fourway"))
    p.add_argument("--pilot-cycle", default="20240103", help="Wednesday cycle YYYYMMDD")
    p.add_argument("--obs-source", type=Path, default=Path("/data/rd_exchange/cregnier/Rappat/SEALEVEL_GLO_PHY_L4_MY_008_047/cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D_202411"), help="Local delayed-time AVISO source (file or directory); availability is not assumed")
    a = p.parse_args()
    try:
        pilot = date.fromisoformat(f"{a.pilot_cycle[:4]}-{a.pilot_cycle[4:6]}-{a.pilot_cycle[6:]}")
    except ValueError as exc:
        p.error(f"Invalid --pilot-cycle: {exc}")
    valid = {date(2024, 1, 3) + timedelta(days=7 * i) for i in range(52)}
    if pilot not in valid:
        p.error("--pilot-cycle must be one of the 52 Wednesday cycles in 2024")
    a.output_root.mkdir(parents=True, exist_ok=True)
    rows = list(tiles())
    with (a.output_root / "global_tiles.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with (a.output_root / "global_cycle_model_plan.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=("cycle", "model", "source_model", "initialization", "common_days", "color"))
        writer.writeheader()
        for i in range(52):
            wed = date(2024, 1, 3) + timedelta(days=7 * i)
            for model in MODELS:
                writer.writerow({
                    "cycle": wed.strftime("%Y%m%d"), "model": model,
                    "source_model": "GLOW" if model == "GLONET3" else "GLO12" if model.startswith("GLO12") else model,
                    "initialization": (wed + timedelta(days=(model == "GLOENS_MEAN"))).isoformat(),
                    "common_days": 9, "color": COLORS[model],
                })
    print(f"Saved {len(rows)} tiles and {52 * len(MODELS)} cycle/model entries to {a.output_root}")
    print(f"Pilot cycle: {pilot}; 50 km one-to-one same-polarity matching")
    print(f"AVISO source: {a.obs_source}")
    if not a.obs_source.exists():
        print("WARNING: AVISO source is not accessible on this machine")
    elif a.obs_source.is_dir():
        print("AVISO source is a directory: multi-file reader and time coverage checks required")
    else:
        print("AVISO source is a file: verify ADT variable and date coverage before processing")
    print("NOT PRODUCTION READY: tiles require seam-aware SSH padding, duplicate removal,")
    print("cross-tile eddy and track stitching, and a common valid-observation mask.")
    print("The global AVISO record must extend into January 2025.")
    print("Do not run 52-cycle global detection until these safeguards are implemented.")


if __name__ == "__main__":
    main()
