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
