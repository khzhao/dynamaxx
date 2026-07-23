# Copyright 2026 dynamaxx

"""Gradient-safety tests for differentiable Dinosaur physical closures."""

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.dinosaur.adapter import (
    _sqrt_nonnegative_with_finite_gradient,
)


def test_nonnegative_square_root_has_finite_origin_gradient():
    """Calm and clipped points must not inject NaNs into BPTT."""
    values = jnp.asarray([-1.0, 0.0, 4.0], dtype=jnp.float32)

    results = _sqrt_nonnegative_with_finite_gradient(values)
    gradients = jax.grad(
        lambda inputs: jnp.sum(_sqrt_nonnegative_with_finite_gradient(inputs))
    )(values)

    np.testing.assert_allclose(results, [0.0, 0.0, 2.0])
    np.testing.assert_allclose(gradients, [0.0, 0.0, 0.25])
    assert bool(jnp.all(jnp.isfinite(gradients)))
