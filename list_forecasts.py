#!/usr/bin/env python3
"""Inventory local or CloudFerro S3 forecast files/Zarr stores without downloading data."""
import argparse
import csv
import re
from pathlib import Path
from urllib.parse import urlparse

DATE_RE = re.compile(r"(?<!\d)(20\d{6})(?!\d)")
SYSTEM_RE = re.compile(r"(?<![A-Z0-9])(GLONET3|GLONET|GLOW|GLO12|GLOENS)(?![A-Z0-9])", re.I)
EXTENSIONS = (".nc", ".nc4", ".grib", ".grb", ".grib2", ".zarr")


def identify(path):
    match = SYSTEM_RE.search(path.upper())
    system = match.group(1).upper() if match else "UNKNOWN"
    if system == "GLOW":
        system = "GLONET3"
    dates = DATE_RE.findall(path)
    return system, dates[0] if dates else ""


def local_items(root, recursive):
    root = Path(root).expanduser()
    if not root.exists():
        raise FileNotFoundError(root)
    if root.is_file() or root.name.lower().endswith(".zarr"):
        yield str(root), "file" if root.is_file() else "zarr"
        return
    for p in (root.rglob("*") if recursive else root.iterdir()):
        if any(parent.name.lower().endswith(".zarr") for parent in p.parents):
            continue
        if p.is_dir() and p.name.lower().endswith(".zarr"):
            yield str(p), "zarr"
        elif p.is_file() and p.name.lower().endswith(EXTENSIONS[:-1]):
            yield str(p), "file"


def s3_items(uri, endpoint_url, anonymous):
    try:
        import s3fs
    except ImportError as exc:
        raise SystemExit("Install s3fs: pip install s3fs") from exc
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise ValueError("Expected s3://bucket/prefix")
    fs = s3fs.S3FileSystem(anon=anonymous, client_kwargs={"endpoint_url": endpoint_url})
    prefix = parsed.netloc + parsed.path
    for item in fs.find(prefix):
        name = item.rstrip("/")
        if ".zarr/" in name.lower():
            zarr = name[:name.lower().index(".zarr/") + 5]
            yield "s3://" + zarr, "zarr"
        elif name.lower().endswith(EXTENSIONS):
            yield "s3://" + name, "file"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", help="Local paths or S3 prefixes")
    parser.add_argument("-o", "--output", default="forecast_inventory.csv")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--s3", action="store_true")
    parser.add_argument("--endpoint-url", default="https://s3.waw3-1.cloudferro.com")
    parser.add_argument("--anon", action="store_true", help="Anonymous S3 access")
    args = parser.parse_args()
    rows, seen = [], set()
    for root in args.roots:
        items = (s3_items(root, args.endpoint_url, args.anon)
                 if args.s3 or root.startswith("s3://")
                 else local_items(root, args.recursive))
        for path, kind in items:
            if path in seen:
                continue
            seen.add(path)
            system, init = identify(path)
            rows.append({"system": system, "initialization_date_yyyymmdd": init,
                         "format": kind, "path": path})
    rows.sort(key=lambda r: (r["system"], r["initialization_date_yyyymmdd"], r["path"]))
    with open(args.output, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["system", "initialization_date_yyyymmdd", "format", "path"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} entries to {args.output}")
    print("Note: forecast horizons and data coverage are not verified.")


if __name__ == "__main__":
    main()
