"""Run an isolated one-day AVISO tile pilot; never treat tile tracks as global.

Uses the same detector and local delayed-time AVISO files as the regional run.
Each tile has a separate output root so duplicate filenames cannot overwrite.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

from eddy_run.year2024_global_plan import tiles

DEFAULT_AVISO = Path(
    "/data/rd_exchange/cregnier/Rappat/SEALEVEL_GLO_PHY_L4_MY_008_047/"
    "cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D_202411"
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=date.fromisoformat, default=date(2024, 1, 3))
    parser.add_argument("--source-root", type=Path, default=DEFAULT_AVISO)
    parser.add_argument("--output-root", type=Path, default=Path("data_2024_global_pilot"))
    parser.add_argument("--tile", required=True, help="One tile identifier, e.g. lat03_lon03")
    parser.add_argument("--execute", action="store_true", help="Actually run detection (default dry run)")
    args = parser.parse_args(argv)
    matching = [t for t in tiles() if t["tile"] == args.tile]
    if not matching:
        parser.error("Unknown tile; expected lat00_lon00 through lat03_lon05")
    tile = matching[0]
    # Current regional detector interpolates without periodic longitude wrapping.
    # Seam tiles must not be accepted as seam-safe until periodic halos exist.
    if tile["touches_dateline"]:
        parser.error("Date-line tile is not seam-safe in the current detector; periodic halo implementation required")
    from eddy_detect.observations import daily_aviso_path
    source = daily_aviso_path(args.source_root, args.date)
    out = args.output_root / "TILES" / args.tile / "OBS_FULL"
    command = [
        sys.executable, "-m", "eddy_detect.observations", "detect", str(out),
        "--start", args.date.isoformat(), "--end", args.date.isoformat(),
        "--lon-min", str(tile["read_lon_min"]), "--lon-max", str(tile["read_lon_max"]),
        "--lat-min", str(tile["read_lat_min"]), "--lat-max", str(tile["read_lat_max"]),
        "--resolution", "0.125", "--source-root", str(args.source_root),
    ]
    print(f"AVISO input: {source}", flush=True)
    print(f"Tile core: {tile['core_lon_min']}..{tile['core_lon_max']} lon, "
          f"{tile['core_lat_min']}..{tile['core_lat_max']} lat", flush=True)
    print("Tile read area includes 2-degree overlap; detections are NOT stitched", flush=True)
    print("+ " + " ".join(command), flush=True)
    if args.execute:
        subprocess.run(command, check=True)
        print(f"Tile detection complete: {out / 'GLOENS/OBS/DETECT'}", flush=True)


if __name__ == "__main__":
    main()
