import jax
import jax.numpy as jnp
import numpy as np
import pytest

from dynamaxx.utils.math.associated_legendre import (
    equiangular_nodes,
    equiangular_nodes_with_poles,
    evaluate,
    gauss_legendre_nodes,
)


def test_evaluate_matches_low_degree_normalized_closed_forms():
    x = jnp.array([-0.5, 0.0, 0.5])
    values = evaluate(n_m=3, n_l=3, x=x)

    np.testing.assert_allclose(values[0, :, 0], 1 / np.sqrt(2), rtol=1e-6)
    np.testing.assert_allclose(values[0, :, 1], np.sqrt(3 / 2) * x, rtol=1e-6)
    np.testing.assert_allclose(
        values[0, :, 2],
        np.sqrt(5 / 2) * 0.5 * (3 * x * x - 1),
        rtol=1e-6,
    )
    np.testing.assert_allclose(
        values[1, :, 1],
        -np.sqrt(3 / 4) * jnp.sqrt(1 - x * x),
        rtol=1e-6,
    )
    np.testing.assert_allclose(
        values[2, :, 2],
        np.sqrt(15 / 16) * (1 - x * x),
        rtol=1e-6,
    )


def test_evaluate_zero_pads_invalid_degree_order_pairs():
    x = jnp.array([-0.25, 0.25])
    values = evaluate(n_m=4, n_l=4, x=x)

    assert values.shape == (4, 2, 4)
    for m in range(4):
        for l in range(m):
            np.testing.assert_allclose(values[m, :, l], jnp.zeros_like(x))


def test_evaluate_is_orthonormal_under_gauss_legendre_quadrature():
    nodes, weights = gauss_legendre_nodes(12)
    values = np.asarray(evaluate(n_m=4, n_l=6, x=jnp.asarray(nodes)))

    for m in range(values.shape[0]):
        valid_values = values[m, :, m:]
        gram_matrix = valid_values.T @ (weights[:, np.newaxis] * valid_values)

        np.testing.assert_allclose(
            gram_matrix,
            np.eye(gram_matrix.shape[0]),
            atol=2e-6,
        )


def test_evaluate_supports_multidimensional_x_and_jit():
    x = jnp.array([[-0.75, -0.25], [0.25, 0.75]])

    values = evaluate(n_m=3, n_l=5, x=x)
    jitted_values = jax.jit(lambda y: evaluate(n_m=3, n_l=5, x=y))(x)

    assert values.shape == (3, 2, 2, 5)
    np.testing.assert_allclose(jitted_values, values, rtol=1e-6)


def test_gauss_legendre_nodes_match_numpy_leggauss():
    nodes, weights = gauss_legendre_nodes(5)
    expected_nodes, expected_weights = np.polynomial.legendre.leggauss(5)

    np.testing.assert_allclose(nodes, expected_nodes)
    np.testing.assert_allclose(weights, expected_weights)


@pytest.mark.parametrize(
    "node_function",
    [equiangular_nodes, equiangular_nodes_with_poles],
)
def test_equiangular_weights_integrate_low_degree_polynomials(node_function):
    nodes, weights = node_function(6)

    np.testing.assert_allclose(np.sum(weights), 2.0, rtol=1e-10)
    np.testing.assert_allclose(weights @ nodes, 0.0, atol=1e-12)
    np.testing.assert_allclose(weights @ (nodes * nodes), 2 / 3, rtol=1e-10)


def test_evaluate_rejects_too_many_order_modes():
    with pytest.raises(AssertionError, match="expected n_m <= n_l"):
        evaluate(n_m=4, n_l=3, x=jnp.array([0.0]))
