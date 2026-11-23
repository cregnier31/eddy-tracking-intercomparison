"""Inspect adjacent AVISO tile detections for duplicate eddies.

Diagnostic only: no eddies are merged and no track IDs are assigned.
Candidate pairs are matched one-to-one by center distance and polarity.
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
import numpy as np
import xarray as xr
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
from eddy_run.year2024_global_plan import tiles


def centers(path):
    with xr.open_dataset(path) as ds:
        for name in ("longitude", "latitude"):
            if name not in ds:
                raise ValueError(f"{path}: missing {name}; variables={list(ds.variables)}")
        lon = np.asarray(ds["longitude"].values, dtype=float).ravel()
        lat = np.asarray(ds["latitude"].values, dtype=float).ravel()
        if lon.shape != lat.shape:
            raise ValueError(f"{path}: center coordinate shapes differ")
    return lon, lat


def xyz(lon, lat):
    lon, lat = np.deg2rad(lon), np.deg2rad(lat)
    return np.column_stack((np.cos(lat) * np.cos(lon),
                            np.cos(lat) * np.sin(lon), np.sin(lat)))


def pairs(lon_a, lat_a, lon_b, lat_b, distance_km):
    good_a = np.flatnonzero(np.isfinite(lon_a) & np.isfinite(lat_a))
    good_b = np.flatnonzero(np.isfinite(lon_b) & np.isfinite(lat_b))
    if not len(good_a) or not len(good_b):
        return []
    aa, bb = xyz(lon_a[good_a], lat_a[good_a]), xyz(lon_b[good_b], lat_b[good_b])
    radius = 2 * np.sin(distance_km / (2 * 6371.0088))
    neighbor = cKDTree(bb)
    candidate = neighbor.query_ball_point(aa, radius)
    # Connected components avoid constructing a global dense assignment matrix.
    edges = [(i, j) for i, js in enumerate(candidate) for j in js]
    if not edges:
        return []
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(x, y):
        x, y = find(x), find(y)
        if x != y:
            parent[y] = x
    for i, j in edges:
        union(("a", i), ("b", j))
    groups = {}
    for i, j in edges:
        groups.setdefault(find(("a", i)), []).append((i, j))
    result = []
    for component in groups.values():
        ai = sorted({i for i, _ in component})
        bj = sorted({j for _, j in component})
        imap, jmap = {i: k for k, i in enumerate(ai)}, {j: k for k, j in enumerate(bj)}
        costs = np.full((len(ai), len(bj) + len(ai)), distance_km + 1.0)
        for i, j in component:
            chord = np.linalg.norm(aa[i] - bb[j])
            d = 2 * 6371.0088 * np.arcsin(min(1., chord / 2))
            costs[imap[i], jmap[j]] = d
        rows, cols = linear_sum_assignment(costs)
        for ri, cj in zip(rows, cols):
            if cj < len(bj) and costs[ri, cj] <= distance_km:
                i, j = ai[ri], bj[cj]
                result.append((int(good_a[i]), int(good_b[j]), float(costs[ri, cj])))
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path("data_2024_global_pilot"))
    p.add_argument("--date", default="20240103")
    p.add_argument("--tile-a", default="lat03_lon03")
    p.add_argument("--tile-b", default="lat03_lon04")
    p.add_argument("--distance-km", type=float, default=50)
    p.add_argument("--output", type=Path, default=None)
    args = p.parse_args(argv)
    if args.distance_km <= 0:
        p.error("--distance-km must be positive")
    tile_map = {t["tile"]: t for t in tiles()}
    if args.tile_a not in tile_map or args.tile_b not in tile_map:
        p.error("Unknown tile")
    a, b = tile_map[args.tile_a], tile_map[args.tile_b]
    if not (max(a["read_lon_min"], b["read_lon_min"]) < min(a["read_lon_max"], b["read_lon_max"])
            and max(a["read_lat_min"], b["read_lat_min"]) < min(a["read_lat_max"], b["read_lat_max"])):
        p.error("Tiles do not have overlapping read areas")
    output = args.output or args.root / "DIAGNOSTICS" / f"overlap_{args.tile_a}_{args.tile_b}_{args.date}.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for polarity in ("Cyclonic", "Anticyclonic"):
        path_a = args.root / "TILES" / args.tile_a / "OBS_FULL/GLOENS/OBS/DETECT" / f"{polarity}_OBS_{args.date}.nc"
        path_b = args.root / "TILES" / args.tile_b / "OBS_FULL/GLOENS/OBS/DETECT" / f"{polarity}_OBS_{args.date}.nc"
        if not path_a.is_file() or not path_b.is_file():
            raise FileNotFoundError(f"Both tiles must be detected: {path_a} / {path_b}")
        alon, alat = centers(path_a)
        blon, blat = centers(path_b)
        matches = pairs(alon, alat, blon, blat, args.distance_km)
        for i, j, distance in matches:
            rows.append(dict(polarity=polarity, tile_a=args.tile_a, index_a=i,
                             longitude_a=alon[i], latitude_a=alat[i],
                             tile_b=args.tile_b, index_b=j,
                             longitude_b=blon[j], latitude_b=blat[j],
                             distance_km=distance))
        print(f"{polarity}: tile A {len(alon)}, tile B {len(blon)}, "
              f"candidate duplicate pairs {len(matches)}")
    with output.open("w", newline="") as stream:
        columns = ("polarity", "tile_a", "index_a", "longitude_a", "latitude_a",
                   "tile_b", "index_b", "longitude_b", "latitude_b", "distance_km")
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved diagnostic: {output}")
    print("WARNING: center proximity is not sufficient to merge eddy contours; "
          "these are candidate duplicates only. No stitching performed.")


if __name__ == "__main__":
    main()
