"""Synthetic interpolation, vector rotation and geostrophic velocity tests."""
import numpy as np
from eddy_detect.gloens_grid import (
    CurvilinearToRegular, geostrophic_velocity, rotate_grid_vectors, regularize_ssh,
)


def test_curvilinear_interpolation_preserves_linear_ssh():
    lon2, lat2 = np.meshgrid(np.linspace(-4, 4, 9), np.linspace(40, 46, 7))
    lon2 = lon2 + 0.1 * np.sin(np.deg2rad(lat2))
    ssh = 2 * lon2 + 3 * lat2
    lon = np.linspace(-3, 3, 7)
    lat = np.linspace(41, 45, 5)
    result = CurvilinearToRegular(lon2, lat2, lon, lat).scalar(ssh)
    expected_lon, expected_lat = np.meshgrid(lon, lat)
    np.testing.assert_allclose(result, 2 * expected_lon + 3 * expected_lat, atol=1e-8)


def test_rotation_of_native_vectors():
    east, north = rotate_grid_vectors(np.array([1.0]), np.array([0.0]), np.pi / 2)
    np.testing.assert_allclose(east, 0, atol=1e-12)
    np.testing.assert_allclose(north, 1, atol=1e-12)


def test_constant_ssh_produces_zero_geostrophic_current():
    lon = np.arange(-4, 5, 1.)
    lat = np.arange(40, 47, 1.)
    u, v = geostrophic_velocity(np.ones((lat.size, lon.size)), lon, lat)
    np.testing.assert_allclose(u, 0, atol=1e-12)
    np.testing.assert_allclose(v, 0, atol=1e-12)


def test_equatorial_velocity_is_masked():
    lon = np.arange(-4, 5, 1.)
    lat = np.arange(-6, 7, 1.)
    u, v = geostrophic_velocity(np.ones((lat.size, lon.size)), lon, lat)
    assert np.isnan(u[np.abs(lat) < 5]).all()
    assert np.isnan(v[np.abs(lat) < 5]).all()
