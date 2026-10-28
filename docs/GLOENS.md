# GLOENS ensemble-mean SSH preprocessing

This is a **preprocessing stage**, adapted from the lazy xarray/Dask ensemble-mean approach in
[class1-comparisons](https://github.com/cregnier31/class1-comparisons/blob/main/stats_fcst_processing.py).
Unlike the 3D temperature/current fields in that code, GLOENS `zos` is already surface SSH,
so it has **no depth coordinate** to select.

For the forecast initialized **2026-10-22** (28 daily leads, 50 members):

```bash
python -m pip install "xarray" "dask[array]" "s3fs" "zarr" "netCDF4" pytest
python -m eddy_load.gloens_mean \
  s3://MOISICEEF/glo4-ens50_ng_1d-m_20261022-20261118_2DT-oce_fcst_R20261022.zarr \
  ./data --endpoint https://s3.waw3-1.cloudferro.com --first-day 0 --last-day 1
```

The first command exports **one forecast day** for inspection; omit `--last-day 1`
to process all 28. Outputs are cached under `data/GLOENS/<forecast-store-name>_<source-hash>/GLOENS_YYYYMMDD.nc` (one per lead), so different forecast runs cannot overwrite each other. Existing valid daily files are opened and reused without recomputing the mean. Missing or invalid files are recreated. Add `--force` to regenerate the cache.
The code opens the Zarr lazily, loads only `zos`, reduces over `ens`, and
writes one daily NetCDF file at a time; missing member values are ignored
by the mean.

Anonymous CloudFerro S3 access is attempted by default, as in your example.
If the bucket needs credentials, export suitable AWS environment variables
and append `--authenticated`; **never commit keys to Git**.

**Original cached mean files alone are not directly consumable by eddy_detect.** GLOENS carries
2D `latitude(y,x)` and `longitude(y,x)` coordinates. The current detector
uses py-eddy-tracker's `RegularGridDataset`, which expects a regular grid
with suitable 1D longitude/latitude dimensions, and its eddy-identification
call also needs `uo` and `vo`. The 2DT-oce store listed here contains
`zos` but **not** velocities. A subsequent stage must regrid to a regular
longitude/latitude grid and derive *geostrophic* currents from SSH (or load
matching currents from the U/V stores), then validate units and behavior
before running full detection.

```bash
python -m pytest -q tests/test_gloens_mean.py
```


## Inline eddy detection (no separate preprocessing command)

```bash
python -m eddy_detect.gloens_grid \
  s3://MOISICEEF/glo4-ens50_ng_1d-m_20261022-20261118_2DT-oce_fcst_R20261022.zarr \
  ./data --lon-min -19 --lon-max 5 --lat-min 26 --lat-max 56 --resolution 0.25
```

This command processes each lead in one workflow: load or compute/cache its 50-member
`zos` mean, interpolate SSH from the native 2D curvilinear grid to a regional
regular lon/lat grid, derive eastward/northward **geostrophic** currents from
SSH gradients, and run the existing eddy detector. Temporary regular-grid
files are deleted after detection. Daily detections are written to
`data/GLOENS/DETECT/`.

**Vector rotation:** `zos` is a scalar and is never rotated. Since this
2DT-oce store contains no U/V fields, geostrophic currents are calculated
*after* interpolation in geographic east/north coordinates; no grid-vector
rotation is needed. `rotate_grid_vectors` is available if future companion
native-grid U/V data are added, but requires a scientifically verified
grid-orientation angle and must not be applied to already east/north velocities.

**Scientific limitations:** Linear triangulation is regional and does not
currently handle dateline-crossing bounds. NaN/land boundaries can create
invalid interpolation triangles; inspect coastlines and masks. Geostrophic
velocities are masked within 5 degrees of the equator and are not equivalent
to model total surface currents. Verify whether SSH needs a geoid/MDT
correction for the intended detection algorithm and compare against a
known benchmark before production use. The default 0.25 degree grid is an
example, not a validated optimal detection resolution.

```bash
python -m pytest -q tests/test_gloens_mean.py tests/test_gloens_grid.py
```
