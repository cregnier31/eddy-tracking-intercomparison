"""Batch calendar-year 2024 model/observation eddy intercomparison.

Run with --stage plan first. Execution is explicit via --stage detect|track|compare.
Each cycle has isolated model outputs; one shared continuous ADT track archive.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path
import shutil
import subprocess
import tempfile

from eddy_track.gloens_members import DEFAULT_TEMPLATE, tracking_config

ENDPOINT = "https://s3.waw3-1.cloudferro.com"
MODELS = ("GLONET", "GLOW", "GLO12", "GLOENS_MEAN")
START = date(2024, 1, 3)
END = date(2024, 12, 31)
FORECAST_DAYS = {"GLONET": 10, "GLOW": 9, "GLO12": 10, "GLOENS_MEAN": 28}


def cycles():
    for week in range(53):
        wed = START + timedelta(days=7 * week)
        thu = wed + timedelta(days=1)
        if thu > END:
            break
        verify_days = min(8, (END - thu).days + 1)
        yield wed, thu, verify_days


def gloens_store(init):
    finish = init + timedelta(days=27)
    a, b = init.strftime("%Y%m%d"), finish.strftime("%Y%m%d")
    return f"s3://MOISICEEF/glo4-ens50_ng_1d-m_{a}-{b}_2DT-oce_fcst_R{a}.zarr"


def run(command, dry_run):
    print("+ " + " ".join(str(arg) for arg in command), flush=True)
    if not dry_run:
        subprocess.run([str(arg) for arg in command], check=True)


def track_gloens(cycle_root, expected_days, dry_run):
    detect_dir = cycle_root / "GLOENS/DETECT"
    track_dir = cycle_root / "GLOENS/TRACK"
    for polarity in ("Cyclonic", "Anticyclonic"):
        files = sorted(detect_dir.glob(f"{polarity}_GLOENS_*.nc"))
        if not dry_run and len(files) != expected_days:
            raise ValueError(f"{detect_dir}: {len(files)} {polarity} files; expected {expected_days}")
        executable = shutil.which("EddyTracking")
        if not dry_run and executable is None:
            raise FileNotFoundError("EddyTracking executable not in PATH")
        if dry_run:
            print(f"+ EddyTracking {polarity} {detect_dir} -> {track_dir}")
            continue
        track_dir.mkdir(parents=True, exist_ok=True)
        config = tracking_config(DEFAULT_TEMPLATE, detect_dir, track_dir, polarity)
        with tempfile.TemporaryDirectory(prefix="ond-gloens-track-") as tmp:
            path = Path(tmp) / f"{polarity}.yaml"
            path.write_text(config)
            subprocess.run([executable, str(path)], check=True)


def link(source, target, dry_run):
    if dry_run:
        print(f"+ link {target} -> {source}")
        return
    if not source.exists():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        if target.resolve() != source.resolve():
            raise ValueError(f"Conflicting link: {target}")
    elif target.exists():
        raise FileExistsError(f"Expected link, found existing path: {target}")
    else:
        target.symlink_to(source.resolve(), target_is_directory=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root", type=Path, help="e.g. ./data_ond2024")
    parser.add_argument("--stage", choices=("plan", "check", "detect", "track", "compare"),
                        default="plan")
    parser.add_argument("--execute", action="store_true",
                        help="Required for detect/track/compare; otherwise print commands")
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--lon-min", type=float, default=-80)
    parser.add_argument("--lon-max", type=float, default=0)
    parser.add_argument("--lat-min", type=float, default=20)
    parser.add_argument("--lat-max", type=float, default=65)
    parser.add_argument("--resolution", type=float, default=0.25)
    parser.add_argument("--obs-dataset-id", help="Override Copernicus ADT dataset ID")
    parser.add_argument("--skip-obs", action="store_true",
                        help="Observation detection/tracking already completed")
    args = parser.parse_args()
    root = args.output_root
    dry = not args.execute or args.stage in ("plan", "check")
    python = __import__("sys").executable
    bounds = ["--lon-min", str(args.lon_min), "--lon-max", str(args.lon_max),
              "--lat-min", str(args.lat_min), "--lat-max", str(args.lat_max),
              "--resolution", str(args.resolution)]
    rows = []
    for wed, thu, days in cycles():
        for model in args.models:
            init = thu if model == "GLOENS_MEAN" else wed
            rows.append({"cycle": wed.isoformat(), "model": model,
                         "init_date": init.isoformat(), "verify_start": thu.isoformat(),
                         "verify_end": (thu + timedelta(days=days-1)).isoformat(),
                         "verify_days": days,
                         "source": gloens_store(thu) if model == "GLOENS_MEAN"
                         else f"oceanbench-bucket/{'dev/ml-forecast-outputs/glowcascade_v5_ring' if model == 'GLOW' else 'public/GLO12' if model == 'GLO12' else 'public/ml-forecast-outputs/glonet'}/{wed:%Y%m%d}.zarr"})
    if args.stage in ("plan", "check"):
        root.mkdir(parents=True, exist_ok=True)
        path = root / "year2024_plan.csv"
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Saved {len(rows)} model-cycle entries: {path}")
        print("NOTE: paths are inferred from the provided inventory; Zarr contents are not yet verified.")
        print("NOTE: model and OBS SSH units, available lead days and ADT dataset coverage must be checked.")
        if args.stage == "check":
            import s3fs
            fs = s3fs.S3FileSystem(anon=True, client_kwargs={"endpoint_url": ENDPOINT})
            missing = []
            for row in rows:
                store = row["source"].removeprefix("s3://")
                exists = fs.exists(store)
                print(f"{'OK' if exists else 'MISSING'} {row['model']} {row['init_date']} {store}", flush=True)
                if not exists:
                    missing.append(store)
            if missing:
                raise SystemExit(f"{len(missing)} forecast stores missing; do not launch the full experiment.")
            print("All forecast store paths found; variables, lead lengths and ADT still need verification.")
        return
    if args.stage in ("detect", "track") and not args.skip_obs:
        obs_root = root / "OBS_SHARED"
        command = [python, "-m", "eddy_detect.observations", args.stage,
                   str(obs_root), "--start", "2024-01-01", "--end", "2024-12-31"]
        if args.stage == "detect":
            command += bounds
            if args.obs_dataset_id:
                command += ["--dataset-id", args.obs_dataset_id]
        run(command, dry)
    for wed, thu, days in cycles():
        cycle_root = root / "CYCLES" / wed.strftime("%Y%m%d")
        for model in args.models:
            init = thu if model == "GLOENS_MEAN" else wed
            if args.stage == "detect":
                if model == "GLOENS_MEAN":
                    command = [python, "-m", "eddy_detect.gloens_grid",
                               gloens_store(thu), str(cycle_root),
                               *bounds, "--last-day", str(days)]
                else:
                    command = [python, "-m", "eddy_detect.zarr_forecasts",
                               model, init.strftime("%Y%m%d"), str(cycle_root),
                               *bounds, "--last-day", str(days + 1),
                               "--assume-ssh-metres"]
                run(command, dry)
            elif args.stage == "track":
                if model == "GLOENS_MEAN":
                    track_gloens(cycle_root, days, dry)
                else:
                    run([python, "-m", "eddy_track.zarr_forecasts", model,
                         init.strftime("%Y%m%d"), str(cycle_root),
                         "--expected-days", str(days + 1)], dry)
            elif args.stage == "compare":
                if set(args.models) != set(MODELS):
                    raise ValueError("Comparison requires all four models; omit --models")
                # The comparison reader uses the actual cycle initialization date.
        if args.stage == "compare":
            link(root / "OBS_SHARED/GLOENS/OBS", cycle_root / "GLOENS/OBS", dry)
            out = root / "COMPARISON" / wed.strftime("%Y%m%d")
            run([python, "-m", "eddy_track.compare_forecasts_obs",
                 str(cycle_root), "--start", thu.isoformat(),
                 "--days", str(days), "--init-wednesday", wed.isoformat(),
                 "--output-dir", str(out)], dry)
    print(f"Stage {args.stage} finished (dry_run={dry})", flush=True)


if __name__ == "__main__":
    main()
