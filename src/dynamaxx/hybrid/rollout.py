# Copyright 2026 dynamaxx

"""Scan-based advancement and selectively observed hybrid rollouts."""

from collections.abc import Callable
from typing import TypeVar

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.hybrid.api import HybridState, HybridStepper

Parameters = TypeVar("Parameters")
CoreState = TypeVar("CoreState")
NodalTendency = TypeVar("NodalTendency")
Observation = TypeVar("Observation")


def _positive_integer(value: int, *, name: str) -> int:
    """Validate one static scan length."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 1:
        raise ValueError(f"{name} must be at least one")
    return value


def advance(
    model: HybridStepper[Parameters, CoreState, NodalTendency],
    parameters: Parameters,
    initial_state: HybridState[CoreState],
    *,
    steps: int,
    rematerialize: bool = False,
) -> HybridState[CoreState]:
    """Advance a model without retaining intermediate states or diagnostics."""
    steps = _positive_integer(steps, name="steps")

    def scan_step(state, _):
        next_state, _ = model.step(parameters, state)
        return next_state, None

    transformed_scan_step = jax.checkpoint(scan_step) if rematerialize else scan_step

    final_state, _ = jax.lax.scan(
        transformed_scan_step,
        initial_state,
        xs=None,
        length=steps,
    )
    return final_state


def advance_duration(
    model: HybridStepper[Parameters, CoreState, NodalTendency],
    parameters: Parameters,
    initial_state: HybridState[CoreState],
    *,
    duration_seconds: float,
    rematerialize: bool = False,
) -> HybridState[CoreState]:
    """Advance a physical duration that exactly spans correction intervals."""
    duration_seconds = float(duration_seconds)
    if not np.isfinite(duration_seconds) or duration_seconds <= 0.0:
        raise ValueError("duration_seconds must be positive and finite")
    correction_steps_float = duration_seconds / float(model.step_seconds)
    correction_steps = int(round(correction_steps_float))
    tolerance = max(1.0e-9, duration_seconds * 1.0e-12)
    if correction_steps < 1 or not np.isclose(
        duration_seconds,
        correction_steps * float(model.step_seconds),
        rtol=0.0,
        atol=tolerance,
    ):
        raise ValueError(
            "duration_seconds must be an integer multiple of model.step_seconds"
        )
    return advance(
        model,
        parameters,
        initial_state,
        steps=correction_steps,
        rematerialize=rematerialize,
    )


def rollout_at_durations(
    model: HybridStepper[Parameters, CoreState, NodalTendency],
    parameters: Parameters,
    initial_state: HybridState[CoreState],
    *,
    durations_seconds: tuple[float, ...],
    rematerialize: bool = False,
) -> tuple[HybridState[CoreState], Observation]:
    """Decode a continuous rollout only at requested physical durations."""
    durations_seconds = tuple(float(value) for value in durations_seconds)
    if not durations_seconds:
        raise ValueError("durations_seconds must not be empty")
    if any(not np.isfinite(value) or value <= 0.0 for value in durations_seconds):
        raise ValueError("durations_seconds must be positive and finite")
    if tuple(sorted(set(durations_seconds))) != durations_seconds:
        raise ValueError("durations_seconds must be unique and increasing")

    state = initial_state
    elapsed_seconds = 0.0
    observations = []
    for duration_seconds in durations_seconds:
        state = advance_duration(
            model,
            parameters,
            state,
            duration_seconds=duration_seconds - elapsed_seconds,
            rematerialize=rematerialize,
        )
        observations.append(model.decode(state))
        elapsed_seconds = duration_seconds
    stacked_observations = jax.tree_util.tree_map(
        lambda *values: jnp.stack(values),
        *observations,
    )
    return state, stacked_observations


def rollout_at_durations_with_tendency_statistics(
    model: HybridStepper[Parameters, CoreState, NodalTendency],
    parameters: Parameters,
    initial_state: HybridState[CoreState],
    *,
    durations_seconds: tuple[float, ...],
    rematerialize: bool = True,
    rematerialization_policy: Callable[..., bool] | None = None,
    collect_tendency_statistics: bool | jax.Array = True,
    maximum_gradient_duration_seconds: float | None = None,
) -> tuple[HybridState[CoreState], Observation, dict[str, jax.Array]]:
    """Decode selected durations and reduce tendencies with bounded BPTT.

    When ``maximum_gradient_duration_seconds`` is set, the recurrent state is
    detached at fixed intervals of that duration. The numerical trajectory is
    unchanged, but losses can propagate through no more than one interval.
    """
    durations_seconds = tuple(float(value) for value in durations_seconds)
    if not durations_seconds:
        raise ValueError("durations_seconds must not be empty")
    if any(not np.isfinite(value) or value <= 0.0 for value in durations_seconds):
        raise ValueError("durations_seconds must be positive and finite")
    if tuple(sorted(set(durations_seconds))) != durations_seconds:
        raise ValueError("durations_seconds must be unique and increasing")

    maximum_duration_seconds = durations_seconds[-1]
    gradient_boundaries: tuple[float, ...] = ()
    if maximum_gradient_duration_seconds is not None:
        maximum_gradient_duration_seconds = float(maximum_gradient_duration_seconds)
        if (
            not np.isfinite(maximum_gradient_duration_seconds)
            or maximum_gradient_duration_seconds <= 0.0
        ):
            raise ValueError(
                "maximum_gradient_duration_seconds must be positive and finite"
            )
        gradient_steps_float = maximum_gradient_duration_seconds / float(
            model.step_seconds
        )
        gradient_steps = int(round(gradient_steps_float))
        if gradient_steps < 1 or not np.isclose(
            maximum_gradient_duration_seconds,
            gradient_steps * float(model.step_seconds),
        ):
            raise ValueError(
                "maximum_gradient_duration_seconds must fall on a "
                "neural-correction boundary"
            )
        gradient_boundaries = tuple(
            boundary_index * maximum_gradient_duration_seconds
            for boundary_index in range(
                1,
                int(
                    np.ceil(
                        maximum_duration_seconds / maximum_gradient_duration_seconds
                    )
                ),
            )
            if boundary_index * maximum_gradient_duration_seconds
            < maximum_duration_seconds
        )

    event_durations_seconds = tuple(
        sorted(set(durations_seconds).union(gradient_boundaries))
    )
    observation_durations = frozenset(durations_seconds)
    gradient_boundary_set = frozenset(gradient_boundaries)

    state = initial_state
    elapsed_seconds = 0.0
    observations = []
    total_squared_tendency = jnp.asarray(0.0, dtype=jnp.float32)
    total_tendency_elements = jnp.asarray(0.0, dtype=jnp.float32)
    maximum_absolute_tendency = jnp.asarray(0.0, dtype=jnp.float32)
    for duration_seconds in event_durations_seconds:
        segment_seconds = duration_seconds - elapsed_seconds
        correction_steps_float = segment_seconds / float(model.step_seconds)
        correction_steps = int(round(correction_steps_float))
        if correction_steps < 1 or not np.isclose(
            segment_seconds,
            correction_steps * float(model.step_seconds),
        ):
            raise ValueError(
                "durations_seconds must fall on neural-correction boundaries"
            )

        def scan_step(scan_state, _):
            next_state, diagnostics = model.step(parameters, scan_state)
            collect_statistics = jnp.asarray(collect_tendency_statistics)

            def summarize_tendency(_):
                leaves = jax.tree_util.tree_leaves(diagnostics.nodal_tendency)
                squared_sum = sum(
                    jnp.sum(jnp.square(leaf.astype(jnp.float32))) for leaf in leaves
                )
                element_count = sum(leaf.size for leaf in leaves)
                maximum = jnp.max(
                    jnp.stack(
                        [jnp.max(jnp.abs(leaf.astype(jnp.float32))) for leaf in leaves]
                    )
                )
                return (
                    squared_sum,
                    jnp.asarray(element_count, dtype=jnp.float32),
                    maximum,
                )

            tendency_statistics = jax.lax.cond(
                collect_statistics,
                summarize_tendency,
                lambda _: (
                    jnp.asarray(0.0, dtype=jnp.float32),
                    jnp.asarray(1.0, dtype=jnp.float32),
                    jnp.asarray(0.0, dtype=jnp.float32),
                ),
                operand=None,
            )
            return next_state, tendency_statistics

        transformed_scan_step = scan_step
        if rematerialize:
            transformed_scan_step = jax.checkpoint(
                scan_step,
                policy=rematerialization_policy,
            )
        state, segment_statistics = jax.lax.scan(
            transformed_scan_step,
            state,
            xs=None,
            length=correction_steps,
        )
        total_squared_tendency += jnp.sum(segment_statistics[0])
        total_tendency_elements += jnp.sum(segment_statistics[1])
        maximum_absolute_tendency = jnp.maximum(
            maximum_absolute_tendency,
            jnp.max(segment_statistics[2]),
        )
        if duration_seconds in observation_durations:
            observations.append(model.decode(state))
        if duration_seconds in gradient_boundary_set:
            state = jax.tree_util.tree_map(jax.lax.stop_gradient, state)
        elapsed_seconds = duration_seconds
    stacked_observations = jax.tree_util.tree_map(
        lambda *values: jnp.stack(values),
        *observations,
    )
    tendency_rms = jnp.sqrt(
        total_squared_tendency / jnp.maximum(total_tendency_elements, 1.0)
    )
    return (
        state,
        stacked_observations,
        {
            "correction/rms": tendency_rms,
            "correction/max_abs": maximum_absolute_tendency,
        },
    )


def rollout(
    model: HybridStepper[Parameters, CoreState, NodalTendency],
    parameters: Parameters,
    initial_state: HybridState[CoreState],
    *,
    steps: int,
    save_every: int,
    observe: Callable[[HybridState[CoreState]], Observation],
    include_initial: bool = True,
) -> tuple[HybridState[CoreState], Observation]:
    """Advance and observe only selected public coupling boundaries.

    Args:
        model: Prepared model whose public step is one correction interval.
        parameters: Neural-corrector parameters.
        initial_state: Complete recurrent state at a coupling boundary.
        steps: Total number of public coupling steps.
        save_every: Number of public steps between observations. ``steps`` must
            be divisible by this value.
        observe: Pure function mapping a state to an array PyTree. Passing
            ``model.decode`` produces weather outputs only at saved boundaries.
        include_initial: Whether to prepend the observation at the initial state.

    Returns:
        The final recurrent state and a stacked observation PyTree.
    """
    steps = _positive_integer(steps, name="steps")
    save_every = _positive_integer(save_every, name="save_every")
    if steps % save_every != 0:
        raise ValueError("steps must be divisible by save_every")
    output_count = steps // save_every

    def scan_output(state, _):
        next_state = advance(
            model,
            parameters,
            state,
            steps=save_every,
        )
        return next_state, observe(next_state)

    final_state, observations = jax.lax.scan(
        scan_output,
        initial_state,
        xs=None,
        length=output_count,
    )
    if include_initial:
        initial_observation = observe(initial_state)
        observations = jax.tree_util.tree_map(
            lambda initial, trajectory: jnp.concatenate(
                (jnp.expand_dims(initial, axis=0), trajectory),
                axis=0,
            ),
            initial_observation,
            observations,
        )
    return final_state, observations
