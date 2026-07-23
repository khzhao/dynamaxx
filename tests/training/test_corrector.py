# Copyright 2026 dynamaxx

"""Tests for the shared vertical-column neural corrector."""

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.training.config import (
    PRODUCTION_HIDDEN_SIZE,
    PRODUCTION_RESIDUAL_BLOCKS,
)
from dynamaxx.training.corrector import (
    ColumnResidualMLP,
    hidden_weight_decay_mask,
)


def test_production_corrector_has_twenty_million_parameter_scale():
    """The production preset is a roughly twenty-million-parameter corrector."""
    network = ColumnResidualMLP(
        input_mean=jnp.zeros((172,)),
        input_standard_deviation=jnp.ones((172,)),
        output_scale=jnp.ones((53,)),
        hidden_size=PRODUCTION_HIDDEN_SIZE,
        residual_blocks=PRODUCTION_RESIDUAL_BLOCKS,
    )

    parameters = network.initialize(jax.random.key(0))
    parameter_count = sum(
        parameter.size for parameter in jax.tree_util.tree_leaves(parameters)
    )

    assert parameter_count == 20_692_853


def _network():
    return ColumnResidualMLP(
        input_mean=jnp.asarray([1.0, -2.0, 0.5]),
        input_standard_deviation=jnp.asarray([2.0, 4.0, 1.0]),
        output_scale=jnp.asarray([0.1, 2.0]),
        hidden_size=8,
        residual_blocks=2,
        matrix_dtype=jnp.float32,
    )


def test_zero_output_projection_starts_with_exact_zero_correction():
    """The initialized corrector exactly preserves the frozen backbone."""
    network = _network()
    parameters = network.initialize(jax.random.key(0))
    inputs = jax.random.normal(jax.random.key(1), (4, 5, 3))

    outputs = network(parameters, inputs)

    np.testing.assert_array_equal(outputs, jnp.zeros((4, 5, 2)))


def test_zero_output_projection_receives_a_nonzero_gradient():
    """Zero initialization does not prevent the output kernel from learning."""
    network = _network()
    parameters = network.initialize(jax.random.key(0))
    inputs = jax.random.normal(jax.random.key(1), (4, 5, 3))

    gradients = jax.grad(lambda values: jnp.sum(network(values, inputs)))(parameters)

    assert float(jnp.linalg.norm(gradients["output"]["kernel"])) > 0.0


def test_weight_decay_mask_excludes_output_and_normalization_parameters():
    """Weight decay applies only to hidden dense kernels."""
    parameters = _network().initialize(jax.random.key(0))

    mask = hidden_weight_decay_mask(parameters)

    assert mask["input"]["kernel"]
    assert not mask["input"]["bias"]
    assert mask["blocks"][0]["expansion"]["kernel"]
    assert not mask["blocks"][0]["norm_scale"]
    assert not mask["output"]["kernel"]
