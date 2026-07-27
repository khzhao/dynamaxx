# Copyright 2026 dynamaxx

"""Scan-based advancement and selectively observed hybrid rollouts."""

from collections.abc import Callable
from typing import TypeVar

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.hybrid._rollout_schedule import RolloutSchedule, normalize_durations
from dynamaxx.hybrid.api import HybridState, HybridStepper

Parameters = TypeVar("Parameters")
CoreState = TypeVar("CoreState")
NodalTendency = TypeVar("NodalTendency")
Observation = TypeVar("Observation")

TendencyStatistics = tuple[jax.Array, jax.Array, jax.Array]


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
    durations_seconds = normalize_durations(durations_seconds)

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
        observations.append(model.observe(parameters, state))
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
    schedule = RolloutSchedule.build(
        durations_seconds=durations_seconds,
        correction_step_seconds=float(model.step_seconds),
        gradient_window_seconds=maximum_gradient_duration_seconds,
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

    def advance_segment(scan_state, correction_steps):
        return jax.lax.scan(
            transformed_scan_step,
            scan_state,
            xs=None,
            length=correction_steps,
        )

    def add_statistics(
        accumulated: TendencyStatistics,
        segment: TendencyStatistics,
    ) -> TendencyStatistics:
        return (
            accumulated[0] + jnp.sum(segment[0]),
            accumulated[1] + jnp.sum(segment[1]),
            jnp.maximum(accumulated[2], jnp.max(segment[2])),
        )

    state = initial_state
    elapsed_seconds = 0.0
    observations = []
    accumulated_statistics = (
        jnp.asarray(0.0, dtype=jnp.float32),
        jnp.asarray(0.0, dtype=jnp.float32),
        jnp.asarray(0.0, dtype=jnp.float32),
    )

    for duration_seconds in schedule.prefix_events:
        correction_steps = schedule.segment_steps(
            elapsed_seconds,
            duration_seconds,
        )
        state, segment_statistics = advance_segment(state, correction_steps)
        accumulated_statistics = add_statistics(
            accumulated_statistics,
            segment_statistics,
        )
        if duration_seconds in schedule.observation_durations:
            observations.append(model.observe(parameters, state))
        if duration_seconds in schedule.gradient_boundaries:
            state = jax.tree_util.tree_map(jax.lax.stop_gradient, state)
        elapsed_seconds = duration_seconds

    if schedule.uniform_suffix_steps:
        window_steps = schedule.uniform_window_steps

        def advance_window(window_state, window_index):
            next_state, window_statistics = advance_segment(
                window_state,
                window_steps,
            )
            observation = model.observe(parameters, next_state)
            next_state = jax.tree_util.tree_map(
                lambda value: jax.lax.cond(
                    window_index + 1 < schedule.uniform_suffix_steps,
                    jax.lax.stop_gradient,
                    lambda item: item,
                    value,
                ),
                next_state,
            )
            return next_state, (observation, window_statistics)

        state, (suffix_observations, suffix_statistics) = jax.lax.scan(
            advance_window,
            state,
            jnp.arange(schedule.uniform_suffix_steps),
        )
        accumulated_statistics = add_statistics(
            accumulated_statistics,
            suffix_statistics,
        )
        selected_suffix_observations = jax.tree_util.tree_map(
            lambda value: jnp.take(
                value,
                schedule.requested_suffix_indices,
                axis=0,
            ),
            suffix_observations,
        )
        if observations:
            prefix_observations = jax.tree_util.tree_map(
                lambda *values: jnp.stack(values),
                *observations,
            )
            stacked_observations = jax.tree_util.tree_map(
                lambda prefix, suffix: jnp.concatenate((prefix, suffix), axis=0),
                prefix_observations,
                selected_suffix_observations,
            )
        else:
            stacked_observations = selected_suffix_observations
    else:
        for duration_seconds in schedule.remaining_events:
            correction_steps = schedule.segment_steps(
                elapsed_seconds,
                duration_seconds,
            )
            state, segment_statistics = advance_segment(state, correction_steps)
            accumulated_statistics = add_statistics(
                accumulated_statistics,
                segment_statistics,
            )
            if duration_seconds in schedule.observation_durations:
                observations.append(model.observe(parameters, state))
            if duration_seconds in schedule.gradient_boundaries:
                state = jax.tree_util.tree_map(jax.lax.stop_gradient, state)
            elapsed_seconds = duration_seconds
        stacked_observations = jax.tree_util.tree_map(
            lambda *values: jnp.stack(values),
            *observations,
        )

    total_squared_tendency = accumulated_statistics[0]
    total_tendency_elements = accumulated_statistics[1]
    maximum_absolute_tendency = accumulated_statistics[2]
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
