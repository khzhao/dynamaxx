# Copyright 2026 dynamaxx

"""Pure-JAX multilayer perceptron: parameters as pytrees, forward as function.

There is no Module class anywhere in this file. In JAX the idiomatic
decomposition is:

    params (a pytree of arrays)  +  apply(params, x) (a pure function)

which replaces PyTorch's `nn.Module` (which fuses both into one stateful
object). Everything else — jit, grad, vmap, optimizers — works on exactly
this decomposition.
"""

from __future__ import annotations

from collections.abc import Sequence

import jax
import jax.numpy as jnp

Params = list[dict[str, jax.Array]]


def init_mlp_params(
    key: jax.Array,
    feature_dim: int,
    hidden_dims: Sequence[int],
    output_dim: int,
    dtype: jnp.dtype = jnp.float32,
) -> Params:
    """Initialize MLP parameters.

    Hidden layers use He (Kaiming) normal initialization; the FINAL layer is
    zero-initialized (weights and bias). Zero-initializing the last layer
    makes the corrector's output exactly zero at initialization, so the
    hybrid model starts as a bit-exact copy of the free dycore — the same
    "exact incumbent fallback" discipline every accepted feature in this
    repository follows, and the same trick NeuralGCM-class hybrids use to
    make early training stable.

    Args:
      key: PRNG key. Note that randomness in JAX is explicit: you pass keys,
        you split keys, nothing is global. (PyTorch: implicit global RNG.)
      feature_dim: input feature dimension F.
      hidden_dims: widths of hidden layers.
      output_dim: output dimension O.
      dtype: parameter dtype.

    Returns:
      A list of {"w": [d_in, d_out], "b": [d_out]} dicts. This is a pytree:
      `jax.tree_util.tree_leaves(params)` yields all arrays, and jit/grad
      traverse it transparently.
    """
    dims = [int(feature_dim), *map(int, hidden_dims), int(output_dim)]
    keys = jax.random.split(key, len(dims) - 1)
    params: Params = []
    for i, (d_in, d_out) in enumerate(zip(dims[:-1], dims[1:], strict=True)):
        is_last = i == len(dims) - 2
        if is_last:
            w = jnp.zeros((d_in, d_out), dtype)
        else:
            w = jax.random.normal(keys[i], (d_in, d_out), dtype) * jnp.sqrt(
                2.0 / d_in
            )
        params.append({"w": w, "b": jnp.zeros((d_out,), dtype)})
    return params


def mlp_apply(params: Params, features: jax.Array) -> jax.Array:
    """EXERCISE 1 — implement the forward pass.

    Contract:
      * `features` has shape `[..., F]` for arbitrary leading batch axes
        (in the corrector it will be `[lon, lat, F]`). Return `[..., O]`.
      * Hidden layers: affine transform then `jax.nn.gelu`. Final layer:
        affine only.
      * Do NOT loop over batch elements or call vmap here — a matmul on the
        last axis already broadcasts over leading axes. (vmap is for when
        broadcasting genuinely cannot express the mapping; reaching for it
        reflexively is the most common PyTorch-refugee mistake.)
      * A Python `for` over `params` (layers) is fine: layer count is static,
        so the loop unrolls at trace time into a fixed graph.
      * Must be jit-safe: no shape-dependent Python branching on traced
        values, no in-place mutation (there is none in JAX anyway — `x.at[i]
        .set(v)` returns a new array).

    Acceptance test:
      uv run pytest tests/nncorr/test_exercises.py -k mlp -m exercise
    """
    raise NotImplementedError("EXERCISE 1: see tutorial/03-corrector-design.md")


def parameter_count(params: Params) -> int:
    """Total number of scalar parameters in the pytree."""
    return sum(int(leaf.size) for leaf in jax.tree_util.tree_leaves(params))
