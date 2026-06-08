# Copyright 2026 dynamaxx
# Adapted from: https://github.com/neuralgcm/dinosaur/blob/main/dinosaur/associated_legendre.py

import functools
from functools import partial

import jax
import jax.numpy as jnp
import numpy as np


@partial(jax.jit, static_argnames=("n_m", "n_l"))
def evaluate(n_m: int, n_l: int, x: jax.Array | float) -> jax.Array:
    """Evaluate normalized associated Legendre functions.

    The normalization gives each basis function unit L2 norm on [-1, 1].

    Args:
        n_m: Number of order modes. Must satisfy n_m <= n_l.
        n_l: Number of degree modes.
        x: Point or JAX array of points in [-1, 1].

    Returns:
        Array values with shape (n_m, *jnp.asarray(x).shape, n_l).
        values[m, ..., l] stores the normalized P_l^m(x), and entries with
        l < m are zero.
    """
    assert n_m <= n_l, "expected n_m <= n_l"

    x = jnp.asarray(x, dtype=jnp.result_type(x, jnp.float32))
    rhombus_values = _evaluate_rhombus(n_l, n_m, x, triangle=True)
    values = jnp.zeros((n_m, *x.shape, n_l), dtype=x.dtype)

    for m in range(n_m):
        target = (m, *[slice(None)] * x.ndim, slice(m, n_l))
        source = jnp.moveaxis(rhombus_values[: n_l - m, m], 0, -1)
        values = values.at[target].set(source)

    return values


def gauss_legendre_nodes(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Return Gauss-Legendre quadrature nodes and weights."""
    return np.polynomial.legendre.leggauss(n)


@functools.lru_cache(maxsize=128)
def equiangular_nodes(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Return equiangular quadrature nodes and weights without pole nodes."""
    spacing = np.pi / n
    theta = np.linspace(
        -np.pi / 2 + spacing / 2,
        np.pi / 2 - spacing / 2,
        n,
    )
    x = np.sin(theta)
    return x, _compute_weights(x)


@functools.lru_cache(maxsize=128)
def equiangular_nodes_with_poles(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Return equiangular quadrature nodes and weights including pole nodes."""
    theta = np.linspace(-np.pi / 2, np.pi / 2, n)
    x = np.sin(theta)
    return x, _compute_weights(x)


@partial(jax.jit, static_argnames=("n_l", "n_m", "triangle"))
def _evaluate_rhombus(
    n_l: int,
    n_m: int,
    x: jax.Array | float,
    *,
    triangle: bool,
) -> jax.Array:
    x = jnp.asarray(x, dtype=jnp.result_type(x, jnp.float32))
    values = jnp.zeros((n_l, n_m, *x.shape), dtype=x.dtype)

    root = jnp.sqrt(1 - x * x)
    values = values.at[0, 0].set(jnp.ones_like(x) / jnp.sqrt(jnp.asarray(2.0)))

    for m in range(1, n_m):
        scale = -jnp.sqrt(1 + 1 / (2 * m))
        values = values.at[0, m].set(scale * root * values[0, m - 1])

    for k in range(1, n_l):
        m_count = min(n_m, n_l - k) if triangle else n_m
        if m_count:
            m = jnp.arange(m_count).reshape((m_count, *[1] * x.ndim))
            m_squared = m * m
            l_squared = (m + k) * (m + k)
            previous_l_squared = (m + k - 1) * (m + k - 1)
            scale = jnp.sqrt((4 * l_squared - 1) / (l_squared - m_squared))
            previous_scale = jnp.sqrt(
                (previous_l_squared - m_squared) / (4 * previous_l_squared - 1)
            )
            next_values = scale * (
                x * values[k - 1, :m_count] - previous_scale * values[k - 2, :m_count]
            )
            values = values.at[k, :m_count].set(next_values)

    return values


def _compute_weights(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    degrees = np.arange(x.shape[0], dtype=np.float64)
    normalization = np.sqrt((2 * degrees + 1) / 2)
    legendre_values = np.polynomial.legendre.legvander(x, x.shape[0] - 1).T
    legendre_values = normalization[:, np.newaxis] * legendre_values

    integrals = np.zeros_like(x)
    integrals[0] = np.sqrt(2)
    weights = np.linalg.solve(legendre_values, integrals)
    return weights
