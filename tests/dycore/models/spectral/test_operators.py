import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.spectral import SpectralOperators, SphericalGrid


def test_laplacian_eigenvalues_match_spherical_harmonic_degrees():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
        radius=2.0,
    )
    operators = SpectralOperators(grid)

    assert operators.laplacian_eigenvalues.shape == grid.modal_shape
    np.testing.assert_allclose(operators.laplacian_eigenvalues[0, 0], 0.0)
    np.testing.assert_allclose(operators.laplacian_eigenvalues[0, 2], -6 / 4)
    np.testing.assert_allclose(operators.laplacian_eigenvalues[5, 2], 0.0)
    np.testing.assert_allclose(operators.laplacian_eigenvalues[5, 3], -12 / 4)


def test_apply_modal_mask_zeros_invalid_coefficients():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    operators = SpectralOperators(grid)
    modal_values = jnp.ones(grid.modal_shape)
    masked_values = operators.apply_modal_mask(modal_values)

    np.testing.assert_allclose(masked_values, grid.modal_mask.astype(np.float32))


def test_invalid_modal_values_do_not_leak_through_operators():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    operators = SpectralOperators(grid)
    modal_values = jnp.zeros(grid.modal_shape).at[5, 2].set(99.0)
    expected = jnp.zeros(grid.modal_shape)

    np.testing.assert_allclose(operators.apply_modal_mask(modal_values), expected)
    np.testing.assert_allclose(operators.laplacian(modal_values), expected)
    np.testing.assert_allclose(operators.inverse_laplacian(modal_values), expected)
    np.testing.assert_allclose(
        operators.longitudinal_derivative(modal_values), expected
    )


def test_laplacian_multiplies_each_valid_mode_by_its_eigenvalue():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
        radius=3.0,
    )
    operators = SpectralOperators(grid)
    modal_values = jnp.zeros(grid.modal_shape).at[3, 3].set(2.5)
    laplacian_values = operators.laplacian(modal_values)
    expected = jnp.zeros(grid.modal_shape).at[3, 3].set(-12 / 9 * 2.5)

    np.testing.assert_allclose(laplacian_values, expected, rtol=1e-6)


def test_laplacian_is_consistent_after_transforming_to_nodal_space():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
        radius=2.0,
    )
    operators = SpectralOperators(grid)
    modal_values = jnp.zeros(grid.modal_shape).at[1, 2].set(1.25)

    nodal_laplacian = grid.modal_to_nodal(operators.laplacian(modal_values))
    expected = (-6 / 4) * grid.modal_to_nodal(modal_values)

    np.testing.assert_allclose(nodal_laplacian, expected, rtol=1e-6, atol=1e-6)


def test_inverse_laplacian_recovers_nonconstant_valid_modes():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    operators = SpectralOperators(grid)
    modal_values = jnp.arange(np.prod(grid.modal_shape), dtype=jnp.float32).reshape(
        grid.modal_shape,
    )
    recovered_values = operators.inverse_laplacian(operators.laplacian(modal_values))
    expected = operators.apply_modal_mask(modal_values).at[:, 0].set(0.0)

    np.testing.assert_allclose(recovered_values, expected, rtol=1e-6)


def test_inverse_laplacian_sends_constant_mode_to_zero():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    operators = SpectralOperators(grid)
    modal_values = jnp.zeros(grid.modal_shape).at[0, 0].set(7.0)

    np.testing.assert_allclose(
        operators.inverse_laplacian(modal_values),
        jnp.zeros(grid.modal_shape),
    )


def test_operators_broadcast_over_leading_dimensions():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    operators = SpectralOperators(grid)
    modal_values = jnp.arange(
        2 * np.prod(grid.modal_shape),
        dtype=jnp.float32,
    ).reshape((2, *grid.modal_shape))

    laplacian_values = operators.laplacian(modal_values)
    eigenvalues = jnp.asarray(operators.laplacian_eigenvalues)
    expected_laplacian = eigenvalues * modal_values
    recovered_values = operators.inverse_laplacian(laplacian_values)
    expected_recovered = operators.apply_modal_mask(modal_values).at[..., :, 0].set(0)

    np.testing.assert_allclose(laplacian_values, expected_laplacian, rtol=1e-6)
    np.testing.assert_allclose(recovered_values, expected_recovered, rtol=1e-6)


def test_operators_preserve_float32_dtype():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    operators = SpectralOperators(grid)
    modal_values = jnp.zeros(grid.modal_shape, dtype=jnp.float32).at[1, 2].set(1.0)

    assert operators.apply_modal_mask(modal_values).dtype == jnp.float32
    assert operators.laplacian(modal_values).dtype == jnp.float32
    assert operators.inverse_laplacian(modal_values).dtype == jnp.float32
    assert operators.longitudinal_derivative(modal_values).dtype == jnp.float32


def test_longitudinal_derivative_maps_real_fourier_pairs():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    operators = SpectralOperators(grid)
    modal_values = jnp.zeros(grid.modal_shape).at[3, 3].set(1.0)
    derivative = operators.longitudinal_derivative(modal_values)
    expected = jnp.zeros(grid.modal_shape).at[4, 3].set(-2.0)

    np.testing.assert_allclose(derivative, expected)


def test_second_longitudinal_derivative_multiplies_by_negative_wavenumber_squared():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    operators = SpectralOperators(grid)
    modal_values = jnp.zeros(grid.modal_shape).at[3, 3].set(1.0)

    second_derivative = operators.longitudinal_derivative(
        operators.longitudinal_derivative(modal_values),
    )
    expected = jnp.zeros(grid.modal_shape).at[3, 3].set(-4.0)

    np.testing.assert_allclose(second_derivative, expected)


def test_spectral_operators_work_inside_jit():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    operators = SpectralOperators(grid)
    modal_values = jnp.zeros(grid.modal_shape).at[1, 2].set(1.0)

    laplacian_values = jax.jit(operators.laplacian)(modal_values)
    recovered_values = jax.jit(operators.inverse_laplacian)(laplacian_values)

    np.testing.assert_allclose(recovered_values, modal_values, rtol=1e-6)
