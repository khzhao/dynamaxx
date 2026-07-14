# Copyright 2026 dynamaxx

"""Differentiable hybrid rollout: free dycore + neural corrector.

Design decision (argued in tutorial/03): we train the corrector on the
PLAIN spectral core (primitive equations + hyperdiffusion + SIL3, no
accepted hand-crafted features). The scientific question this sets up is
sharp: the optimization loop spent ~25 accepted/rejected experiments
hand-discovering surface memory, drag, and flux correctors — can one
column MLP learn the lot from data? Chapter 6 evaluates you against the
incumbent `dino_rskin_apv` on the same fixed protocols to answer it.
"""

from __future__ import annotations

from typing import Any, Callable

import jax.numpy as jnp

from dynamaxx.dycore.models.dinosaur import time_integration
from dynamaxx.dycore.models.dinosaur.adapter import (
    _horizontal_diffusion_step_filter,
    _nondimensionalize_seconds,
    _primitive_equation,
)
from dynamaxx.nncorr.data import GridBundle

DEFAULT_STEP_SECONDS = 900.0
DEFAULT_IMPLICIT_OFFCENTERING = 0.05


def build_step_fn(
    bundle: GridBundle,
    *,
    step_seconds_si: float = DEFAULT_STEP_SECONDS,
    implicit_offcentering: float = DEFAULT_IMPLICIT_OFFCENTERING,
    diffusion_order: int = 2,
    nn_filter: Callable[[Any, Any], Any] | None = None,
) -> Callable[[Any], Any]:
    """One 900 s hybrid step: SIL3 dycore step, hyperdiffusion, then NN.

    Mirrors the incumbent lineage's numerical choices (900 s step, SIL3
    with 0.05 implicit off-centering, order-2 hyperdiffusion with the
    resolution-scaled default tau) minus all hand-crafted physics filters.
    The NN filter runs LAST, seeing exactly the state the next step would
    otherwise consume.
    """
    orography = jnp.zeros(bundle.coords.horizontal.modal_shape, dtype=jnp.float32)
    equation = _primitive_equation(
        reference_temperature=bundle.reference_temperature,
        orography=orography,
        coords=bundle.coords,
        physics_specs=bundle.physics_specs,
        include_vertical_advection=True,
        humidity_key=None,
    )
    step_nondim = _nondimensionalize_seconds(bundle.physics_specs, step_seconds_si)
    step_fn = time_integration.imex_rk_sil3(
        equation,
        step_nondim,
        implicit_offcentering=implicit_offcentering,
    )
    filters = [
        _horizontal_diffusion_step_filter(
            coords=bundle.coords,
            physics_specs=bundle.physics_specs,
            step_seconds=step_nondim,
            tau_seconds=None,
            order=diffusion_order,
        )
    ]
    if nn_filter is not None:
        filters.append(nn_filter)
    return time_integration.step_with_filters(step_fn, filters)


def rollout_loss(
    params: Any,
    initial_state: Any,
    target_fields_si: list[dict[str, Any]],
    *,
    bundle: GridBundle,
    make_filter: Callable[[Any], Callable[[Any, Any], Any]],
    inner_steps: int = 24,
    remat_lengths: tuple[int, ...] = (6, 4),
    area_weights: Any = None,
    field_weights: dict[str, float] | None = None,
):
    """EXERCISE 5 — the differentiable multi-window rollout loss.

    Contract:
      * `make_filter(params)` builds the NN step filter (closure over
        params, so this whole function is differentiable in params via
        `jax.value_and_grad(rollout_loss)`).
      * Advance `initial_state` by `inner_steps` (default 24 x 900 s = 6 h)
        per target, for `len(target_fields_si)` targets; after each block,
        decode with `corrector.decode_nodal_si` and accumulate loss against
        the matching entry of `target_fields_si` (same dict layout).
      * Loss per field: area-weighted MSE, standardized by the field's
        climatological std (pass per-field scalars via `field_weights` as
        1/std^2 factors, or bake standardization into the targets — your
        call, document it), summed over fields, averaged over targets.
      * Memory is the whole point of this exercise. A naive
        `lax.scan` over 24 steps stores every intermediate for the backward
        pass; at T80/L13 you will hold ~24 full states per 6 h block.
        Use `time_integration.nested_checkpoint_scan` with
        `nested_lengths=remat_lengths` (6 * 4 = 24) so the backward pass
        stores O(max(remat_lengths)) states per block at the price of one
        extra forward evaluation per level. Derive the numbers first
        (exercise 5a in tutorial/05): state bytes, naive scan memory,
        checkpointed memory, and check them against `jax.live_arrays()`
        or the profiler.
      * A Python loop over the (few) targets is fine — it unrolls; the
        per-step scan must NOT unroll.
      * Return a scalar float32.

    Structure hint, nothing more:

        step = build_step_fn(bundle, nn_filter=make_filter(params))
        def one(carry, _):
            return step(carry), None
        for target in target_fields_si:
            state, _ = nested_checkpoint_scan(one, state, None,
                length=inner_steps, nested_lengths=remat_lengths)
            ... accumulate ...

    Acceptance test (tiny grid, gradients finite and nonzero):
      uv run pytest tests/nncorr/test_exercises.py -k rollout -m exercise
    """
    raise NotImplementedError("EXERCISE 5: see tutorial/05-training.md")
