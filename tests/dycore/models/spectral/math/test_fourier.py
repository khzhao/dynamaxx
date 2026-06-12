import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.spectral.math.fourier import (
    quadrature_nodes,
    real_basis,
    real_basis_derivative,
    real_basis_derivative_with_zero_imag,
    real_basis_with_zero_imag,
)


def test_real_basis_matches_closed_form_columns():
    nodes = 8
    x, _ = quadrature_nodes(nodes)
    basis = real_basis(wavenumbers=3, nodes=nodes)

    expected = np.column_stack(
        [
            np.full(nodes, 1 / np.sqrt(2 * np.pi)),
            np.cos(x) / np.sqrt(np.pi),
            np.sin(x) / np.sqrt(np.pi),
            np.cos(2 * x) / np.sqrt(np.pi),
            np.sin(2 * x) / np.sqrt(np.pi),
        ]
    )

    np.testing.assert_allclose(basis, expected, atol=1e-14)


def test_real_basis_is_orthonormal_under_trapezoidal_quadrature():
    nodes = 32
    _, weights = quadrature_nodes(nodes)
    basis = real_basis(wavenumbers=6, nodes=nodes)
    gram_matrix = basis.T @ (weights[:, np.newaxis] * basis)

    np.testing.assert_allclose(
        gram_matrix,
        np.eye(gram_matrix.shape[0]),
        atol=1e-13,
    )


def test_real_basis_derivative_maps_coefficients():
    coefficients = jnp.array([7.0, 2.0, 3.0, 5.0, 11.0])
    derivative = real_basis_derivative(coefficients)

    np.testing.assert_allclose(
        derivative,
        jnp.array([0.0, 3.0, -2.0, 22.0, -10.0]),
    )


def test_real_basis_derivative_handles_nonfinal_axis():
    coefficients = jnp.array(
        [
            [7.0, 13.0],
            [2.0, 17.0],
            [3.0, 19.0],
            [5.0, 23.0],
            [11.0, 29.0],
        ]
    )
    derivative = real_basis_derivative(coefficients, axis=-2)

    np.testing.assert_allclose(
        derivative,
        jnp.array(
            [
                [0.0, 0.0],
                [3.0, 19.0],
                [-2.0, -17.0],
                [22.0, 58.0],
                [-10.0, -46.0],
            ]
        ),
    )


def test_real_basis_with_zero_imag_matches_closed_form_columns():
    nodes = 8
    x, _ = quadrature_nodes(nodes)
    basis = real_basis_with_zero_imag(wavenumbers=3, nodes=nodes)

    expected = np.column_stack(
        [
            np.full(nodes, 1 / np.sqrt(2 * np.pi)),
            np.zeros(nodes),
            np.cos(x) / np.sqrt(np.pi),
            np.sin(x) / np.sqrt(np.pi),
            np.cos(2 * x) / np.sqrt(np.pi),
            np.sin(2 * x) / np.sqrt(np.pi),
        ]
    )

    np.testing.assert_allclose(basis, expected, atol=1e-14)


def test_real_basis_derivative_with_zero_imag_maps_coefficients():
    coefficients = jnp.array([7.0, 0.0, 2.0, 3.0, 5.0, 11.0])
    derivative = real_basis_derivative_with_zero_imag(coefficients)

    np.testing.assert_allclose(
        derivative,
        jnp.array([0.0, 0.0, 3.0, -2.0, 22.0, -10.0]),
    )


def test_real_basis_derivative_with_zero_imag_supports_frequency_offset():
    coefficients = jnp.array([2.0, 3.0, 5.0, 11.0])
    derivative = real_basis_derivative_with_zero_imag(
        coefficients,
        frequency_offset=3,
    )

    np.testing.assert_allclose(
        derivative,
        jnp.array([9.0, -6.0, 44.0, -20.0]),
    )


def test_fourier_derivative_functions_work_inside_jit():
    coefficients = jnp.array([7.0, 2.0, 3.0, 5.0, 11.0])
    jitted_derivative = jax.jit(real_basis_derivative)(coefficients)

    np.testing.assert_allclose(
        jitted_derivative,
        real_basis_derivative(coefficients),
    )


def test_quadrature_nodes_integrate_low_frequency_modes():
    nodes, weights = quadrature_nodes(16)

    np.testing.assert_allclose(weights.sum(), 2 * np.pi)
    np.testing.assert_allclose(weights @ np.sin(nodes), 0.0, atol=1e-14)
    np.testing.assert_allclose(weights @ np.cos(nodes), 0.0, atol=1e-14)
