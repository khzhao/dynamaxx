# Copyright 2026 dynamaxx
# Adapted from: https://github.com/neuralgcm/dinosaur/blob/main/dinosaur/fourier.py

from functools import partial

import jax
import jax.numpy as jnp
import numpy as np


def real_basis(wavenumbers: int, nodes: int) -> np.ndarray:
    """Return the normalized real Fourier basis on equally spaced nodes.

    Args:
        wavenumbers: Number of nonnegative Fourier wavenumbers.
        nodes: Number of longitude nodes in [0, 2 pi).

    Returns:
        Matrix with shape (nodes, 2 * wavenumbers - 1). The columns are
        1 / sqrt(2 pi), cos(j x) / sqrt(pi), and sin(j x) / sqrt(pi) for
        1 <= j < wavenumbers.
    """
    assert 1 <= wavenumbers <= nodes, "expected 1 <= wavenumbers <= nodes"

    x = np.linspace(0, 2 * np.pi, nodes, endpoint=False)
    frequencies = np.arange(1, wavenumbers)
    angles = x[:, np.newaxis] * frequencies[np.newaxis, :]

    basis = np.empty((nodes, 2 * wavenumbers - 1), dtype=np.float64)
    basis[:, 0] = 1 / np.sqrt(2 * np.pi)
    basis[:, 1::2] = np.cos(angles) / np.sqrt(np.pi)
    basis[:, 2::2] = np.sin(angles) / np.sqrt(np.pi)
    return basis


@partial(jax.jit, static_argnames=("axis",))
def real_basis_derivative(u: jax.Array, axis: int = -1) -> jax.Array:
    """Differentiate coefficients stored in the real Fourier basis.

    The coefficient order is constant, cos(1x), sin(1x), cos(2x), sin(2x),
    and so on. The derivative maps cos(jx) to -j sin(jx), and sin(jx) to
    j cos(jx).
    """
    assert axis < 0, "axis must be negative"
    assert u.shape[axis] % 2 == 1, "real Fourier coefficient axis must be odd"

    u = jnp.asarray(u)
    i = jnp.arange(u.shape[axis]).reshape((-1,) + (1,) * (-1 - axis))
    frequency = (i + 1) // 2
    next_coefficient = jnp.roll(u, shift=-1, axis=axis)
    previous_coefficient = jnp.roll(u, shift=1, axis=axis)
    return frequency * jnp.where(i % 2, next_coefficient, -previous_coefficient)


def real_basis_with_zero_imag(wavenumbers: int, nodes: int) -> np.ndarray:
    """Return the real Fourier basis with an explicit zero imaginary column."""
    assert 1 <= wavenumbers <= nodes, "expected 1 <= wavenumbers <= nodes"

    x = np.linspace(0, 2 * np.pi, nodes, endpoint=False)
    frequencies = np.arange(1, wavenumbers)
    angles = x[:, np.newaxis] * frequencies[np.newaxis, :]

    basis = np.empty((nodes, 2 * wavenumbers), dtype=np.float64)
    basis[:, 0] = 1 / np.sqrt(2 * np.pi)
    basis[:, 1] = 0.0
    basis[:, 2::2] = np.cos(angles) / np.sqrt(np.pi)
    basis[:, 3::2] = np.sin(angles) / np.sqrt(np.pi)
    return basis


@partial(jax.jit, static_argnames=("axis",))
def real_basis_derivative_with_zero_imag(
    u: jax.Array,
    axis: int = -1,
    frequency_offset: int | jax.Array = 0,
) -> jax.Array:
    """Differentiate real Fourier coefficients with a zero imaginary column."""
    assert axis < 0, "axis must be negative"
    assert u.shape[axis] % 2 == 0, "zero-imag Fourier coefficient axis must be even"

    u = jnp.asarray(u)
    i = jnp.arange(u.shape[axis]).reshape((-1,) + (1,) * (-1 - axis))
    frequency = frequency_offset + i // 2
    next_coefficient = jnp.roll(u, shift=-1, axis=axis)
    previous_coefficient = jnp.roll(u, shift=1, axis=axis)
    return frequency * jnp.where(
        (i + 1) % 2,
        next_coefficient,
        -previous_coefficient,
    )


def quadrature_nodes(nodes: int) -> tuple[np.ndarray, np.ndarray]:
    """Return trapezoidal-rule nodes and weights on [0, 2 pi)."""
    x = np.linspace(0, 2 * np.pi, nodes, endpoint=False)
    weights = np.full(nodes, 2 * np.pi / nodes, dtype=np.float64)
    return x, weights
