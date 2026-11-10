"""Track daily GLONET/GLOW/GLO12 detections using the existing AreaTracker."""
from __future__ import annotations
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from eddy_track.gloens_members import DEFAULT_TEMPLATE, tracking_config, POLARITIES

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=("GLONET", "GLOW", "GLO12"))
    parser.add_argument("init_date")
    parser.add_argument("data_dir")
    parser.add_argument("--expected-days", type=int, default=None, help="Default: GLONET/GLO12 10, GLOW 9")
    parser.add_argument("--track-subdir", default="TRACK", choices=("TRACK", "TRACK_FULL"))
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    args = parser.parse_args()
    expected_days = args.expected_days if args.expected_days is not None else (9 if args.model == "GLOW" else 10)
    if expected_days < 1:
        parser.error("--expected-days must be positive")
    executable = shutil.which("EddyTracking")
    if not executable:
        raise FileNotFoundError("EddyTracking not found in PATH")
    root = Path(args.data_dir) / args.model / args.init_date
    detect_dir, track_dir = root / "DETECT", root / args.track_subdir
    for polarity in POLARITIES:
        files = sorted(detect_dir.glob(f"{polarity}_{args.model}_*.nc"))
        if len(files) != expected_days:
            raise ValueError(f"{polarity}: found {len(files)} daily files in {detect_dir}; expected {expected_days}")
        track_dir.mkdir(parents=True, exist_ok=True)
        config = tracking_config(args.template, detect_dir, track_dir, polarity)
        with tempfile.TemporaryDirectory(prefix="zarr-track-") as tmp:
            yaml_path = Path(tmp) / f"{polarity}.yaml"
            yaml_path.write_text(config, encoding="utf-8")
            print(f"Tracking {args.model} {args.init_date} {polarity}", flush=True)
            subprocess.run([executable, str(yaml_path)], check=True)
    print(f"Tracking complete: {track_dir}", flush=True)

if __name__ == "__main__":
    main()
