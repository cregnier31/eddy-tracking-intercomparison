"""Batch local AVISO observation detection over all 24 periodic-halo tiles.

Outputs are tile-local, not globally deduplicated or stitched.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from eddy_run.year2024_global_plan import tiles

DEFAULT_SOURCE = Path("/data/rd_exchange/cregnier/Rappat/SEALEVEL_GLO_PHY_L4_MY_008_047/cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D_202411")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", type=date.fromisoformat, default=date(2024, 1, 3))
    p.add_argument("--end", type=date.fromisoformat, default=date(2025, 1, 22))
    p.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    p.add_argument("--output-root", type=Path, default=Path("data_2024_global_pilot"))
    p.add_argument("--execute", action="store_true", help="Default is dry run")
    p.add_argument("--tile", action="append", help="Optional tile ID, repeat to select multiple")
    args = p.parse_args(argv)
    if args.end < args.start:
        p.error("--end must not precede --start")
    selected = list(tiles())
    if args.tile:
        unknown = set(args.tile) - {t["tile"] for t in selected}
        if unknown:
            p.error(f"Unknown tile(s): {sorted(unknown)}")
        selected = [t for t in selected if t["tile"] in args.tile]
    if not selected:
        p.error("No tiles selected")
    days = (args.end - args.start).days + 1
    print(f"Observation batch: {len(selected)} tiles x {days} days = {len(selected)*days} tile-days", flush=True)
    print("Includes date-line tiles with periodic longitude halos; does not deduplicate or stitch eddies", flush=True)
    if args.execute:
        from eddy_detect.observations import daily_aviso_path
        for n in range(days):
            day = args.start + timedelta(days=n)
            daily_aviso_path(args.source_root, day)
        print("All daily AVISO inputs exist", flush=True)
    for tile in selected:
        root = args.output_root / "TILES" / tile["tile"] / "OBS_FULL"
        cmd = [
            sys.executable, "-m", "eddy_detect.observations", "detect", str(root),
            "--start", args.start.isoformat(), "--end", args.end.isoformat(),
            "--lon-min", str(tile["read_lon_min"]),
            "--lon-max", str(tile["read_lon_max"]),
            "--lat-min", str(tile["read_lat_min"]),
            "--lat-max", str(tile["read_lat_max"]),
            "--resolution", "0.125", "--source-root", str(args.source_root),
        ]
        print(f"{tile['tile']}: {' '.join(cmd)}", flush=True)
        if args.execute:
            subprocess.run(cmd, check=True)
    print("Finished tile detections; global deduplication and track stitching remain required", flush=True)


if __name__ == "__main__":
    main()
