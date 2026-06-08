import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.utils.math.spherical_harmonics import (
    RealSphericalHarmonics,
    get_latitude_nodes,
)


def test_get_latitude_nodes_dispatches_supported_spacings():
    for spacing in ["gauss", "equiangular", "equiangular_with_poles"]:
        nodes, weights = get_latitude_nodes(6, spacing)

        assert nodes.shape == (6,)
        assert weights.shape == (6,)
        np.testing.assert_allclose(np.sum(weights), 2.0, rtol=1e-10)


def test_real_spherical_harmonics_shapes_and_mask():
    transform = RealSphericalHarmonics(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )

    assert transform.nodal_shape == (12, 6)
    assert transform.modal_shape == (7, 4)
    assert transform.basis.fourier.shape == (12, 7)
    assert transform.basis.legendre.shape == (7, 6, 4)
    assert transform.basis.weights.shape == (12, 6)
    assert transform.mask.shape == (7, 4)
    assert not transform.mask[3, 1]
    assert transform.mask[3, 2]


def test_inverse_transform_matches_basis_product_for_single_mode():
    transform = RealSphericalHarmonics(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    modal_values = jnp.zeros(transform.modal_shape)
    modal_values = modal_values.at[1, 2].set(1.0)

    nodal_values = transform.inverse_transform(modal_values)
    expected = (
        transform.basis.fourier[:, 1, np.newaxis]
        * transform.basis.legendre[1, :, 2][np.newaxis, :]
    )

    np.testing.assert_allclose(nodal_values, expected, rtol=1e-6)


def test_real_spherical_harmonic_basis_is_orthonormal_under_quadrature():
    transform = RealSphericalHarmonics(
        total_wavenumbers=5,
        longitude_nodes=16,
        latitude_nodes=8,
    )
    basis_values = np.einsum(
        "im,mjl->ijml",
        transform.basis.fourier,
        transform.basis.legendre,
    )
    basis_matrix = basis_values.reshape(-1, np.prod(transform.modal_shape))
    valid_basis_matrix = basis_matrix[:, transform.mask.ravel()]
    weights = transform.basis.weights.reshape(-1)
    gram_matrix = valid_basis_matrix.T @ (weights[:, np.newaxis] * valid_basis_matrix)

    np.testing.assert_allclose(
        gram_matrix,
        np.eye(gram_matrix.shape[0]),
        atol=4e-6,
    )


def test_transform_inverse_transform_roundtrip_for_valid_modes():
    transform = RealSphericalHarmonics(
        total_wavenumbers=4,
        longitude_nodes=16,
        latitude_nodes=8,
    )
    modal_values = np.zeros(transform.modal_shape, dtype=np.float32)
    modal_values[0, 0] = 1.5
    modal_values[1, 2] = -0.25
    modal_values[2, 3] = 0.75
    modal_values[3, 3] = -1.25
    modal_values = jnp.asarray(modal_values)

    nodal_values = transform.inverse_transform(modal_values)
    recovered_values = transform.transform(nodal_values)

    np.testing.assert_allclose(recovered_values, modal_values, atol=2e-5)


def test_transform_constant_field_has_only_constant_mode():
    transform = RealSphericalHarmonics(
        total_wavenumbers=4,
        longitude_nodes=16,
        latitude_nodes=8,
    )
    nodal_values = jnp.ones(transform.nodal_shape)
    modal_values = transform.transform(nodal_values)
    expected = jnp.zeros(transform.modal_shape)
    expected = expected.at[0, 0].set(2 * jnp.sqrt(jnp.pi))

    np.testing.assert_allclose(modal_values, expected, atol=2e-5)


def test_longitudinal_derivative_maps_modal_coefficients():
    transform = RealSphericalHarmonics(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    modal_values = jnp.zeros(transform.modal_shape)
    modal_values = modal_values.at[3, 3].set(1.0)

    derivative = transform.longitudinal_derivative(modal_values)
    expected = jnp.zeros(transform.modal_shape)
    expected = expected.at[4, 3].set(-2.0)

    np.testing.assert_allclose(derivative, expected)


def test_transform_methods_work_inside_jit():
    transform = RealSphericalHarmonics(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    modal_values = jnp.zeros(transform.modal_shape).at[1, 2].set(1.0)

    nodal_values = jax.jit(transform.inverse_transform)(modal_values)
    recovered_values = jax.jit(transform.transform)(nodal_values)

    np.testing.assert_allclose(recovered_values, modal_values, atol=2e-5)
