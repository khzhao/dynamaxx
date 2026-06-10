import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.grid import SphericalGrid
from dynamaxx.dycore.operators import SpectralOperators
from dynamaxx.dycore.simulation import SpectralDycore


def _test_grid() -> SphericalGrid:
    return SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )


def test_spectral_dycore_zero_tendency_is_persistence():
    grid = _test_grid()
    dycore = SpectralDycore(grid)
    modal_state = jnp.zeros(grid.modal_shape).at[1, 2].set(3.0)

    trajectory = dycore.simulate(
        modal_state,
        steps=3,
        step_seconds=600.0,
    )

    assert trajectory.shape == (4, *grid.modal_shape)
    np.testing.assert_allclose(
        trajectory, jnp.broadcast_to(modal_state, trajectory.shape)
    )


def test_spectral_dycore_masks_invalid_initial_modes():
    grid = _test_grid()
    dycore = SpectralDycore(grid)
    modal_state = jnp.zeros(grid.modal_shape).at[5, 2].set(99.0)

    trajectory = dycore.simulate(
        modal_state,
        steps=1,
        step_seconds=1.0,
    )

    np.testing.assert_allclose(trajectory, jnp.zeros_like(trajectory))


def test_spectral_dycore_diffusion_matches_laplacian_for_first_order_diffusion():
    grid = _test_grid()
    operators = SpectralOperators(grid)
    dycore = SpectralDycore(grid, diffusivity=0.25)
    modal_state = jnp.zeros(grid.modal_shape).at[1, 2].set(4.0)

    expected = 0.25 * operators.laplacian(modal_state)

    np.testing.assert_allclose(dycore.tendency(modal_state), expected)


def test_spectral_dycore_even_order_diffusion_has_stable_sign():
    grid = _test_grid()
    dycore = SpectralDycore(grid, diffusivity=0.5, diffusion_order=2)
    modal_state = jnp.zeros(grid.modal_shape).at[1, 2].set(4.0)

    tendency = dycore.tendency(modal_state)

    np.testing.assert_allclose(tendency[1, 2], -72.0)


def test_spectral_dycore_zonal_advection_matches_longitudinal_derivative():
    grid = _test_grid()
    operators = SpectralOperators(grid)
    angular_velocity = 0.1
    dycore = SpectralDycore(grid, zonal_angular_velocity=angular_velocity)
    modal_state = jnp.zeros(grid.modal_shape).at[3, 3].set(2.0)

    expected = -angular_velocity * operators.longitudinal_derivative(modal_state)

    np.testing.assert_allclose(dycore.tendency(modal_state), expected)


def test_spectral_dycore_step_uses_requested_ode_method():
    grid = _test_grid()
    operators = SpectralOperators(grid)
    diffusivity = 0.25
    dycore = SpectralDycore(grid, diffusivity=diffusivity)
    modal_state = jnp.zeros(grid.modal_shape).at[1, 2].set(4.0)

    next_state = dycore.step(
        modal_state,
        step_seconds=2.0,
        method="euler",
    )
    expected = modal_state + 2.0 * diffusivity * operators.laplacian(modal_state)

    np.testing.assert_allclose(next_state, expected)


def test_spectral_dycore_simulates_batches():
    grid = _test_grid()
    dycore = SpectralDycore(grid, diffusivity=0.01)
    modal_state = jnp.zeros((2, *grid.modal_shape)).at[:, 1, 2].set(1.0)

    trajectory = dycore.simulate(
        modal_state,
        steps=2,
        step_seconds=10.0,
    )

    assert trajectory.shape == (3, 2, *grid.modal_shape)


def test_spectral_dycore_simulate_nodal_returns_nodal_trajectory():
    grid = _test_grid()
    dycore = SpectralDycore(grid)
    modal_state = jnp.zeros(grid.modal_shape).at[1, 2].set(1.0)
    nodal_state = grid.modal_to_nodal(modal_state)

    nodal_trajectory = dycore.simulate_nodal(
        nodal_state,
        steps=2,
        step_seconds=1.0,
    )

    expected = jnp.broadcast_to(nodal_state, nodal_trajectory.shape)
    assert nodal_trajectory.shape == (3, *grid.nodal_shape)
    np.testing.assert_allclose(nodal_trajectory, expected, atol=2e-5)


def test_spectral_dycore_works_inside_jit():
    grid = _test_grid()
    dycore = SpectralDycore(grid, diffusivity=0.01)
    modal_state = jnp.zeros(grid.modal_shape).at[1, 2].set(1.0)

    trajectory = jax.jit(
        dycore.simulate,
        static_argnames=("steps", "method", "include_initial"),
    )(
        modal_state,
        steps=2,
        step_seconds=10.0,
        method="rk4",
        include_initial=True,
    )

    assert trajectory.shape == (3, *grid.modal_shape)
