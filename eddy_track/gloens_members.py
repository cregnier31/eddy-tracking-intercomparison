"""Run the existing overlap-based EddyTracking CLI for GLOENS members.

Each member and polarity is tracked independently. Tracking configuration is
written to a temporary file, never to the shared eddy_track/overlap.yaml.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from eddy_detect.gloens_members import member_indices

DEFAULT_TEMPLATE = Path(__file__).with_name("overlap_template.yaml")
POLARITIES = ("Cyclonic", "Anticyclonic")


def tracking_directories(data_dir, member_number):
    root = Path(data_dir) / "GLOENS" / "MEMBERS" / f"member_{member_number:03d}"
    return root / "DETECT", root / "TRACK"


def tracking_config(template, input_dir, output_dir, polarity):
    """Render the repository's AreaTracker configuration for one polarity."""
    if polarity not in POLARITIES:
        raise ValueError(f"Unknown polarity: {polarity}")
    content = Path(template).read_text(encoding="utf-8")
    for key, value in (
        ("DIR_IN", str(Path(input_dir).resolve())),
        ("DIR_OUT", str(Path(output_dir).resolve())),
        ("EDDY_TYPE", polarity),
    ):
        content = content.replace(key, value)
    return content


def track_members(
    data_dir, first_member=1, last_member=1, expected_days=28,
    template=DEFAULT_TEMPLATE, executable="EddyTracking",
):
    """Track complete daily detection series using the existing AreaTracker."""
    command = shutil.which(executable)
    if command is None:
        raise FileNotFoundError(
            f"{executable!r} was not found in PATH. Activate the py-eddy-tracker environment."
        )
    if expected_days < 1:
        raise ValueError("expected_days must be positive")

    for index in member_indices(50, first_member, last_member):
        number = index + 1
        input_dir, output_dir = tracking_directories(data_dir, number)
        for polarity in POLARITIES:
            files = sorted(input_dir.glob(f"{polarity}_GLOENS_*.nc"))
            if len(files) != expected_days:
                raise ValueError(
                    f"Member {number:03d}: found {len(files)} {polarity} detection files, "
                    f"expected {expected_days}. Complete detection before tracking."
                )
            output_dir.mkdir(parents=True, exist_ok=True)
            config = tracking_config(template, input_dir, output_dir, polarity)
            with tempfile.TemporaryDirectory(prefix="gloens-track-") as temporary:
                config_file = Path(temporary) / f"{polarity}.yaml"
                config_file.write_text(config, encoding="utf-8")
                print(f"Tracking member {number:03d}, {polarity}", flush=True)
                subprocess.run([command, str(config_file)], check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", help="Root containing GLOENS/MEMBERS")
    parser.add_argument("--first-member", type=int, default=1)
    parser.add_argument("--last-member", type=int, default=1)
    parser.add_argument("--expected-days", type=int, default=28)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--executable", default="EddyTracking")
    args = parser.parse_args(argv)
    track_members(
        args.data_dir, first_member=args.first_member,
        last_member=args.last_member, expected_days=args.expected_days,
        template=args.template, executable=args.executable,
    )


if __name__ == "__main__":
    main()
