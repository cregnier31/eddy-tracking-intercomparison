"""Synthetic tests for GLOENS surface ensemble mean (no S3 access needed)."""
import numpy as np
import pytest
import xarray as xr

from eddy_load.gloens_mean import ensemble_mean_ssh


def test_ensemble_mean_uses_all_50_members():
    data = np.broadcast_to(np.arange(1, 51, dtype=np.float32)[None, :, None, None], (2, 50, 2, 3)).copy()
    ds = xr.Dataset({"zos": (("time", "ens", "y", "x"), data)})
    out = ensemble_mean_ssh(ds)
    assert out.dims == ("time", "y", "x")
    np.testing.assert_allclose(out, 25.5)


def test_ensemble_mean_ignores_missing_members():
    data = np.ones((1, 50, 1, 1), dtype="float32")
    data[:, 0] = np.nan
    data[:, 1:] = 2.0
    ds = xr.Dataset({"zos": (("time", "ens", "y", "x"), data)})
    np.testing.assert_allclose(ensemble_mean_ssh(ds), 2.0)


def test_member_count_is_validated():
    ds = xr.Dataset({"zos": (("time", "ens", "y", "x"), np.ones((1, 2, 1, 1)))})
    with pytest.raises(ValueError, match="50"):
        ensemble_mean_ssh(ds)


def test_cache_directory_is_stable_and_run_specific(tmp_path):
    from eddy_load.gloens_mean import cache_directory, cached_mean_path

    run_a = "s3://MOISICEEF/glo4-ens50_2DT-oce_fcst_R20261022.zarr"
    run_b = "s3://MOISICEEF/glo4-ens50_2DT-oce_fcst_R20261029.zarr"
    folder_a = cache_directory(run_a, str(tmp_path))
    assert folder_a == cache_directory(run_a, str(tmp_path))
    assert folder_a != cache_directory(run_b, str(tmp_path))
    assert cached_mean_path(run_a, str(tmp_path), "20261022").parent == folder_a


def test_cached_file_is_loaded_instead_of_recomputed(tmp_path, monkeypatch):
    import eddy_load.gloens_mean as module

    store = "s3://MOISICEEF/test-run.zarr"
    times = np.array(["2026-10-22"], dtype="datetime64[ns]")
    values = np.arange(1, 51, dtype="float32")[None, :, None, None]
    data = xr.Dataset(
        {"zos": (("time", "ens", "y", "x"), values)},
        coords={
            "time": times,
            "latitude": (("y", "x"), np.array([[10.]], dtype="float32")),
            "longitude": (("y", "x"), np.array([[20.]], dtype="float32")),
        },
    )

    class DatasetContext:
        def __enter__(self):
            return data
        def __exit__(self, *_):
            return False

    monkeypatch.setattr(module, "open_gloens_store", lambda *a, **kw: DatasetContext())
    output = module.export_daily_mean(store, str(tmp_path))
    produced = list(output.glob("GLOENS_*.nc"))
    assert len(produced) == 1
    with module.load_cached_mean(produced[0]) as cached:
        np.testing.assert_allclose(cached["zos"].values, 25.5)
    original_modification = produced[0].stat().st_mtime_ns
    def unexpected_write(*_args, **_kwargs):
        raise AssertionError("A cache hit must not write NetCDF")
    monkeypatch.setattr(xr.Dataset, "to_netcdf", unexpected_write)
    module.export_daily_mean(store, str(tmp_path))
    assert produced[0].stat().st_mtime_ns == original_modification
