# Copyright 2026 dynamaxx

"""Scan-based advancement and selectively observed hybrid rollouts."""

from collections.abc import Callable
from typing import TypeVar

import jax
import jax.numpy as jnp

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
) -> HybridState[CoreState]:
    """Advance a model without retaining intermediate states or diagnostics."""
    steps = _positive_integer(steps, name="steps")

    def scan_step(state, _):
        next_state, _ = model.step(parameters, state)
        return next_state, None

    final_state, _ = jax.lax.scan(
        scan_step,
        initial_state,
        xs=None,
        length=steps,
    )
    return final_state


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
