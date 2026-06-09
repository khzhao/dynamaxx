import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.grid import SphericalGrid


def test_spherical_grid_exposes_shapes_axes_and_weights():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
        radius=2.0,
    )

    assert grid.nodal_shape == (12, 6)
    assert grid.modal_shape == (7, 4)
    assert grid.longitude.shape == (12,)
    assert grid.latitude.shape == (6,)
    assert grid.sin_latitude.shape == (6,)
    assert grid.modal_mask.shape == (7, 4)
    assert grid.quadrature_weights.shape == grid.nodal_shape
    assert grid.area_weights.shape == grid.nodal_shape
    np.testing.assert_allclose(grid.area_weights, 4.0 * grid.quadrature_weights)
    np.testing.assert_allclose(np.sum(grid.quadrature_weights), 4 * np.pi)
    np.testing.assert_allclose(np.sum(grid.area_weights), 16 * np.pi)


def test_spherical_grid_transform_roundtrip_matches_math_transform():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=16,
        latitude_nodes=8,
    )
    modal_values = np.zeros(grid.modal_shape, dtype=np.float32)
    modal_values[0, 0] = 1.25
    modal_values[1, 2] = -0.5
    modal_values[2, 3] = 0.75
    modal_values = jnp.asarray(modal_values)

    nodal_values = grid.modal_to_nodal(modal_values)
    recovered_values = grid.nodal_to_modal(nodal_values)
    expected_nodal_values = grid.spherical_harmonics.modal_to_nodal(modal_values)

    np.testing.assert_allclose(nodal_values, expected_nodal_values, atol=2e-6)
    np.testing.assert_allclose(recovered_values, modal_values, atol=2e-5)


def test_spherical_grid_transform_methods_work_inside_jit():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    modal_values = jnp.zeros(grid.modal_shape).at[1, 2].set(1.0)

    nodal_values = jax.jit(grid.modal_to_nodal)(modal_values)
    recovered_values = jax.jit(grid.nodal_to_modal)(nodal_values)

    np.testing.assert_allclose(recovered_values, modal_values, atol=2e-5)
