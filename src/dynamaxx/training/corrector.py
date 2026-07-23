# Copyright 2026 dynamaxx

"""Pure-JAX vertical-column residual MLP used by the first hybrid model."""

from dataclasses import dataclass
from typing import Any

import jax
import jax.numpy as jnp

ParameterTree = dict[str, Any]


def _glorot_normal(
    key: jax.Array,
    input_size: int,
    output_size: int,
) -> jax.Array:
    """Initialize one dense kernel with fan-average variance."""
    standard_deviation = jnp.sqrt(2.0 / float(input_size + output_size))
    return standard_deviation * jax.random.normal(
        key,
        (input_size, output_size),
        dtype=jnp.float32,
    )


def _dense(
    inputs: jax.Array,
    parameters: ParameterTree,
    *,
    matrix_dtype: jnp.dtype,
) -> jax.Array:
    """Apply a dense layer with low-precision matrix multiplication."""
    inputs_for_matrix = inputs.astype(matrix_dtype)
    kernel = parameters["kernel"].astype(matrix_dtype)
    output = jnp.einsum(
        "...f,fh->...h",
        inputs_for_matrix,
        kernel,
        precision=jax.lax.Precision.HIGH,
    )
    return output.astype(jnp.float32) + parameters["bias"]


def _layer_norm(
    inputs: jax.Array,
    scale: jax.Array,
    bias: jax.Array,
    epsilon: float,
) -> jax.Array:
    """Normalize the last axis in FP32."""
    inputs = inputs.astype(jnp.float32)
    mean = jnp.mean(inputs, axis=-1, keepdims=True)
    variance = jnp.mean(jnp.square(inputs - mean), axis=-1, keepdims=True)
    normalized = (inputs - mean) * jax.lax.rsqrt(variance + epsilon)
    return normalized * scale + bias


@dataclass(frozen=True)
class ColumnResidualMLP:
    """Shared residual MLP evaluated independently at every grid column.

    Inputs and outputs use a final feature axis. Training-set normalization and
    physical output scaling are fixed model buffers, not trainable parameters.
    The zero output projection makes the initialized hybrid exactly reproduce
    its frozen backbone.
    """

    input_mean: jax.Array
    input_standard_deviation: jax.Array
    output_scale: jax.Array
    hidden_size: int = 256
    residual_blocks: int = 4
    matrix_dtype: jnp.dtype = jnp.bfloat16
    layer_norm_epsilon: float = 1.0e-5

    def __post_init__(self):
        input_mean = jnp.asarray(self.input_mean, dtype=jnp.float32)
        input_standard_deviation = jnp.asarray(
            self.input_standard_deviation,
            dtype=jnp.float32,
        )
        output_scale = jnp.asarray(self.output_scale, dtype=jnp.float32)
        if input_mean.ndim != 1:
            raise ValueError("input_mean must be one-dimensional")
        if input_standard_deviation.shape != input_mean.shape:
            raise ValueError(
                "input_standard_deviation must have the same shape as input_mean"
            )
        if output_scale.ndim != 1 or output_scale.size == 0:
            raise ValueError("output_scale must be a non-empty one-dimensional array")
        if not bool(jnp.all(jnp.isfinite(input_mean))):
            raise ValueError("input_mean must be finite")
        if not bool(
            jnp.all(
                jnp.isfinite(input_standard_deviation)
                & (input_standard_deviation > 0.0)
            )
        ):
            raise ValueError("input_standard_deviation must be positive and finite")
        if not bool(jnp.all(jnp.isfinite(output_scale) & (output_scale >= 0.0))):
            raise ValueError("output_scale must be nonnegative and finite")
        if self.hidden_size < 1 or self.residual_blocks < 1:
            raise ValueError("hidden_size and residual_blocks must be positive")
        object.__setattr__(self, "input_mean", input_mean)
        object.__setattr__(
            self,
            "input_standard_deviation",
            input_standard_deviation,
        )
        object.__setattr__(self, "output_scale", output_scale)

    @property
    def input_size(self) -> int:
        """Number of features per column."""
        return int(self.input_mean.size)

    @property
    def output_size(self) -> int:
        """Number of predicted tendency channels per column."""
        return int(self.output_scale.size)

    def initialize(self, key: jax.Array) -> ParameterTree:
        """Initialize trainable parameters with a zero final projection."""
        key_count = 1 + 2 * self.residual_blocks
        keys = iter(jax.random.split(key, key_count))
        parameters: ParameterTree = {
            "input": {
                "kernel": _glorot_normal(
                    next(keys),
                    self.input_size,
                    self.hidden_size,
                ),
                "bias": jnp.zeros((self.hidden_size,), dtype=jnp.float32),
            },
            "blocks": [],
        }
        blocks = []
        for _ in range(self.residual_blocks):
            blocks.append(
                {
                    "norm_scale": jnp.ones(
                        (self.hidden_size,),
                        dtype=jnp.float32,
                    ),
                    "norm_bias": jnp.zeros(
                        (self.hidden_size,),
                        dtype=jnp.float32,
                    ),
                    "expansion": {
                        "kernel": _glorot_normal(
                            next(keys),
                            self.hidden_size,
                            2 * self.hidden_size,
                        ),
                        "bias": jnp.zeros(
                            (2 * self.hidden_size,),
                            dtype=jnp.float32,
                        ),
                    },
                    "projection": {
                        "kernel": _glorot_normal(
                            next(keys),
                            2 * self.hidden_size,
                            self.hidden_size,
                        ),
                        "bias": jnp.zeros(
                            (self.hidden_size,),
                            dtype=jnp.float32,
                        ),
                    },
                }
            )
        parameters["blocks"] = tuple(blocks)
        parameters["output"] = {
            "kernel": jnp.zeros(
                (self.hidden_size, self.output_size),
                dtype=jnp.float32,
            ),
            "bias": jnp.zeros((self.output_size,), dtype=jnp.float32),
        }
        return parameters

    def __call__(
        self,
        parameters: ParameterTree,
        inputs: jax.Array,
    ) -> jax.Array:
        """Predict scaled physical tendencies for a set of columns."""
        inputs = jnp.asarray(inputs, dtype=jnp.float32)
        if inputs.shape[-1] != self.input_size:
            raise ValueError(
                f"expected {self.input_size} input features; "
                f"received {inputs.shape[-1]}"
            )
        normalized_inputs = (inputs - self.input_mean) / self.input_standard_deviation
        hidden = _dense(
            normalized_inputs,
            parameters["input"],
            matrix_dtype=self.matrix_dtype,
        )
        for block in parameters["blocks"]:
            residual_input = hidden
            hidden = _layer_norm(
                hidden,
                block["norm_scale"],
                block["norm_bias"],
                self.layer_norm_epsilon,
            )
            hidden = jax.nn.silu(
                _dense(
                    hidden,
                    block["expansion"],
                    matrix_dtype=self.matrix_dtype,
                )
            )
            hidden = _dense(
                hidden,
                block["projection"],
                matrix_dtype=self.matrix_dtype,
            )
            hidden = residual_input + hidden
        output = _dense(
            hidden,
            parameters["output"],
            matrix_dtype=self.matrix_dtype,
        )
        return output * self.output_scale


def hidden_weight_decay_mask(parameters: ParameterTree) -> ParameterTree:
    """Return an Optax mask that decays hidden dense kernels only."""

    def build_mask(node: Any, path: tuple[str, ...] = ()) -> Any:
        if isinstance(node, dict):
            return {
                key: build_mask(value, (*path, str(key))) for key, value in node.items()
            }
        if isinstance(node, tuple):
            return tuple(
                build_mask(value, (*path, str(index)))
                for index, value in enumerate(node)
            )
        return bool(path and path[-1] == "kernel" and "output" not in path)

    return build_mask(parameters)
