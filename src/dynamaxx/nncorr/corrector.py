# Copyright 2026 dynamaxx

"""The neural corrector as a dinosaur step filter.

Hook-point decision (chapter 3 discusses the alternatives): the corrector is
a POST-STEP STATE FILTER with signature `(u_prev, u_next) -> u_next`,
appended after the dycore's own filters — exactly the mechanism every
accepted hand-crafted feature in `adapter.py` uses (`step_with_filters`).
The NN sees the state after a full SIL3 step and adds a bounded increment.
The NeuralGCM-faithful alternative — composing an extra explicit tendency
into the ODE via `time_integration.compose_equations` so the network's
output is integrated by the Runge-Kutta stages — is the chapter-6 extension.

Differentiability: params enter through a closure. In JAX a closure over a
traced value is just another input to the traced function, so
`jax.grad(lambda p: loss(build_filter(p), ...))` works with no ceremony.
This is the functional replacement for "the module owns its parameters".
"""

from __future__ import annotations

import dataclasses
from typing import Any, Callable

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.dinosaur import primitive_equations, spherical_harmonic
from dynamaxx.dycore.models.dinosaur.adapter import _unit_factor
from dynamaxx.nncorr import mlp as mlp_lib
from dynamaxx.nncorr.features import FeatureSpec

# Fixed output tendency scales, in SI, applied to the raw O(1) network
# outputs. 5 K/day and 5 (m/s)/day are the size of large physics tendencies
# (radiation, boundary-layer drag); the network can express weaker
# corrections easily and stronger ones only by saturating its output. Fixed
# here, not learned: keeping the output scale out of the optimizer is one of
# the quiet stability tricks of hybrid models.
TEMPERATURE_TENDENCY_SCALE_SI = 5.0 / 86400.0  # K / s
WIND_TENDENCY_SCALE_SI = 5.0 / 86400.0  # (m/s) / s


@dataclasses.dataclass(frozen=True)
class CorrectorContext:
    """Everything the correction needs besides params and the state."""

    coords: Any
    physics_specs: Any
    reference_temperature: np.ndarray  # [L], Kelvin
    feature_spec: FeatureSpec
    static_stack: jax.Array  # [S, lon, lat]
    state_mean: jax.Array  # [3L + 1]
    state_std: jax.Array  # [3L + 1]
    step_seconds_si: float
    mlp_apply_fn: Callable[[Any, jax.Array], jax.Array] = mlp_lib.mlp_apply


def decode_nodal_si(
    state: Any,
    *,
    coords: Any,
    physics_specs: Any,
    reference_temperature: np.ndarray,
) -> dict[str, jax.Array]:
    """Decode a modal dinosaur State into nodal SI fields.

    Provided in full because it concentrates the three ideas you need
    before writing any corrector code:

      1. The prognostic state is SPECTRAL (modal coefficients), and
         temperature is stored as a VARIATION about a per-layer reference.
      2. Winds are not state variables at all — vorticity and divergence
         are; `vor_div_to_uv_nodal` solves for the velocity potential /
         streamfunction under the hood.
      3. Everything is NONDIMENSIONAL inside the model. `_unit_factor(
         physics_specs, "kelvin")` is the SI -> nondimensional multiplier,
         so DIVIDING by it converts model values back to SI.

    Returns nodal fields on the dinosaur grid:
      {"temperature": [L, lon, lat] K, "u"/"v": [L, lon, lat] m/s,
       "surface_pressure": [lon, lat] Pa}
    """
    grid = coords.horizontal
    kelvin = _unit_factor(physics_specs, "kelvin")
    meters_per_second = _unit_factor(physics_specs, "meter / second")
    pascal = _unit_factor(physics_specs, "pascal")

    temperature_nodal = grid.to_nodal(state.temperature_variation) + jnp.asarray(
        reference_temperature, dtype=jnp.float32
    )[:, jnp.newaxis, jnp.newaxis]
    u_nodal, v_nodal = spherical_harmonic.vor_div_to_uv_nodal(
        grid, state.vorticity, state.divergence
    )
    surface_pressure_nodal = jnp.exp(grid.to_nodal(state.log_surface_pressure))[0]
    return {
        "temperature": temperature_nodal / kelvin,
        "u": u_nodal / meters_per_second,
        "v": v_nodal / meters_per_second,
        "surface_pressure": surface_pressure_nodal / pascal,
    }


def si_increments_to_modal(
    delta_temperature_si: jax.Array,
    delta_u_si: jax.Array,
    delta_v_si: jax.Array,
    *,
    coords: Any,
    physics_specs: Any,
) -> tuple[jax.Array, jax.Array, jax.Array]:
    """Convert SI nodal state increments to modal (dzeta, ddiv, dT).

    Increments (already multiplied by the step length) come in as
    `[L, lon, lat]` nodal arrays in K and m/s. They leave as modal
    increments to vorticity, divergence, and temperature_variation, in
    model units, wavenumber-clipped the same way the encode path clips.
    """
    grid = coords.horizontal
    kelvin = _unit_factor(physics_specs, "kelvin")
    meters_per_second = _unit_factor(physics_specs, "meter / second")
    delta_vorticity, delta_divergence = spherical_harmonic.uv_nodal_to_vor_div_modal(
        grid,
        delta_u_si * meters_per_second,
        delta_v_si * meters_per_second,
    )
    delta_temperature = grid.to_modal(delta_temperature_si * kelvin)
    return grid.clip_wavenumbers(
        (delta_vorticity, delta_divergence, delta_temperature)
    )


def corrector_increments(
    params: Any,
    state: Any,
    ctx: CorrectorContext,
) -> tuple[jax.Array, jax.Array, jax.Array]:
    """EXERCISE 3 — the full state -> modal-increment pipeline.

    Chain, in order (every piece already exists):
      1. `decode_nodal_si(state, ...)` using fields from `ctx`.
      2. `features.assemble_features(...)` -> `[lon, lat, F]`.
      3. `ctx.mlp_apply_fn(params, features)` -> `[lon, lat, 3L]`.
      4. Split the last axis into dT, du, dv blocks of L; `jnp.moveaxis`
         each to `[L, lon, lat]`.
      5. Scale: dT * TEMPERATURE_TENDENCY_SCALE_SI * ctx.step_seconds_si,
         winds with WIND_TENDENCY_SCALE_SI — outputs become per-STEP
         increments in K and m/s.
      6. `si_increments_to_modal(...)` -> modal (dzeta, ddiv, dT).

    Sanity anchors you should be able to state before running anything:
    with |NN output| <= O(1), the per-step temperature increment is about
    5 K/day * 900 s ~ 0.05 K — the same magnitude as the hand-tuned caps on
    the accepted features (`_OCEAN_BULK_SHF_MAX_STEP_TEMPERATURE_INCREMENT_
    KELVIN` etc.). That is not a coincidence; it is the size of increment
    this dycore is known to absorb stably.

    Acceptance test (identity at zero init, bit-exact):
      uv run pytest tests/nncorr/test_exercises.py -k identity -m exercise
    """
    raise NotImplementedError("EXERCISE 3: see tutorial/03-corrector-design.md")


def make_nn_correction_filter(params: Any, ctx: CorrectorContext):
    """Wrap `corrector_increments` as a `(u, u_next) -> u_next` step filter.

    Provided in full: the interesting physics/ML is in the increments; this
    wrapper encodes two repository disciplines you should copy rather than
    reinvent —

      * construct the WHOLE candidate state explicitly (all six State
        fields; tracers and sim_time pass through untouched), and
      * guard with a single all-finite predicate that falls back to the
        UNCORRECTED state, the exact-fallback idiom every accepted feature
        uses (`jnp.where` on a scalar bool is free under jit).
    """

    def _filter(u_prev: Any, u_next: Any) -> Any:
        del u_prev
        delta_vorticity, delta_divergence, delta_temperature = corrector_increments(
            params, u_next, ctx
        )
        candidate = primitive_equations.State(
            vorticity=u_next.vorticity + delta_vorticity,
            divergence=u_next.divergence + delta_divergence,
            temperature_variation=u_next.temperature_variation + delta_temperature,
            log_surface_pressure=u_next.log_surface_pressure,
            tracers=u_next.tracers,
            sim_time=u_next.sim_time,
        )
        finite = (
            jnp.all(jnp.isfinite(delta_vorticity))
            & jnp.all(jnp.isfinite(delta_divergence))
            & jnp.all(jnp.isfinite(delta_temperature))
        )
        return jax.tree_util.tree_map(
            lambda corrected, fallback: jnp.where(finite, corrected, fallback),
            candidate,
            u_next,
        )

    return _filter
