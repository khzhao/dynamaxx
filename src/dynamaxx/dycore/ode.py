# Copyright 2026 dynamaxx

from collections.abc import Callable

import jax
import jax.numpy as jnp

TimeValue = jax.Array | float
Tendency = Callable[[jax.Array, TimeValue], jax.Array]


def euler_step(
    tendency: Tendency,
    state: jax.Array,
    time: TimeValue,
    step_seconds: TimeValue,
) -> jax.Array:
    """Advance one explicit Euler step for dy/dt = tendency(y, t)."""
    return state + step_seconds * tendency(state, time)


def rk4_step(
    tendency: Tendency,
    state: jax.Array,
    time: TimeValue,
    step_seconds: TimeValue,
) -> jax.Array:
    """Advance one fourth-order Runge-Kutta step for dy/dt = tendency(y, t)."""
    half_step = 0.5 * step_seconds
    k1 = tendency(state, time)
    k2 = tendency(state + half_step * k1, time + half_step)
    k3 = tendency(state + half_step * k2, time + half_step)
    k4 = tendency(state + step_seconds * k3, time + step_seconds)
    return state + step_seconds * (k1 + 2 * k2 + 2 * k3 + k4) / 6


def integrate(
    tendency: Tendency,
    initial_state: jax.Array,
    *,
    steps: int,
    step_seconds: TimeValue,
    start_time: TimeValue = 0.0,
    method: str = "rk4",
    include_initial: bool = True,
) -> jax.Array:
    """Roll out an ODE trajectory with a leading time axis.

    Args:
        tendency: Callable with signature tendency(state, time).
        initial_state: Initial state with arbitrary shape.
        steps: Number of time steps to take.
        step_seconds: Step size in seconds.
        start_time: Initial simulation time in seconds.
        method: Either "euler" or "rk4".
        include_initial: Include the initial state as trajectory[0].

    Returns:
        Array with shape (steps + 1, *initial_state.shape) when
        include_initial is True, otherwise (steps, *initial_state.shape).
    """
    assert steps >= 0
    assert method in STEP_METHODS

    initial_state = jnp.asarray(initial_state)
    time_dtype = jnp.result_type(initial_state, jnp.float32)
    step_seconds = jnp.asarray(step_seconds, dtype=time_dtype)
    start_time = jnp.asarray(start_time, dtype=time_dtype)
    step = STEP_METHODS[method]

    def scan_step(carry, _):
        time, state = carry
        next_state = step(tendency, state, time, step_seconds)
        return (time + step_seconds, next_state), next_state

    _, trajectory = jax.lax.scan(
        scan_step,
        (start_time, initial_state),
        None,
        length=steps,
    )
    if include_initial:
        return jnp.concatenate([initial_state[jnp.newaxis], trajectory], axis=0)
    return trajectory


STEP_METHODS = {
    "euler": euler_step,
    "rk4": rk4_step,
}
