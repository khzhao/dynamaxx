# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

from dynamaxx.dycore.models.wind_advection import wind_advection_step

SECONDS_PER_DAY = 86_400.0
REFERENCE_STEP_SECONDS = 21_600.0


def split_history_state(
    state: jax.Array,
    *,
    current_count: int,
) -> tuple[jax.Array, jax.Array]:
    """Split packed current and previous-history state channels."""
    state = jnp.asarray(state)
    assert state.ndim == 4
    assert state.shape[1] >= 2 * current_count
    current = state[:, :current_count]
    previous = state[:, current_count : 2 * current_count]
    return current, previous


def tendency_advection_step(
    current_state: jax.Array,
    previous_state: jax.Array,
    initial_tendency: jax.Array,
    step_index: jax.Array,
    step_seconds: jax.Array,
    *,
    surface_indices: tuple[int, ...],
    lower_indices: tuple[int, ...],
    upper_indices: tuple[int, ...],
    surface_u_indices: tuple[int, ...],
    surface_v_indices: tuple[int, ...],
    surface_weights: tuple[float, ...],
    lower_u_index: int,
    lower_v_index: int,
    upper_u_index: int,
    upper_v_index: int,
    wind_scale: float,
    max_wind_speed: float,
    diffusion_per_step: float,
    damping_days: float,
    corrected_advection: bool,
    tendency_scale: float,
    tendency_decay_days: float,
) -> tuple[jax.Array, jax.Array]:
    """Advance current state with transport plus decaying recent tendency."""
    transported = wind_advection_step(
        current_state,
        step_seconds,
        surface_indices=surface_indices,
        lower_indices=lower_indices,
        upper_indices=upper_indices,
        surface_u_indices=surface_u_indices,
        surface_v_indices=surface_v_indices,
        surface_weights=surface_weights,
        lower_u_index=lower_u_index,
        lower_v_index=lower_v_index,
        upper_u_index=upper_u_index,
        upper_v_index=upper_v_index,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
        diffusion_per_step=diffusion_per_step,
        damping_days=damping_days,
        corrected_advection=corrected_advection,
    )
    lead_days = (step_index + 1) * step_seconds / SECONDS_PER_DAY
    tendency_decay = jnp.exp(-lead_days / tendency_decay_days)
    tendency_increment = tendency_scale * tendency_decay * initial_tendency
    next_state = transported + tendency_increment
    return next_state, current_state


def tendency_advection_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    surface_indices: tuple[int, ...],
    lower_indices: tuple[int, ...],
    upper_indices: tuple[int, ...],
    surface_u_indices: tuple[int, ...],
    surface_v_indices: tuple[int, ...],
    surface_weights: tuple[float, ...],
    lower_u_index: int,
    lower_v_index: int,
    upper_u_index: int,
    upper_v_index: int,
    wind_scale: float,
    max_wind_speed: float,
    diffusion_per_step: float,
    damping_days: float,
    corrected_advection: bool,
    tendency_scale: float,
    tendency_decay_days: float,
) -> jax.Array:
    """Roll out a history-informed wind and tendency forecast."""
    initial_state = jnp.asarray(initial_state)
    current, previous = split_history_state(initial_state, current_count=current_count)
    initial_tendency = current - previous
    step_seconds_array = jnp.asarray(step_seconds, dtype=initial_state.dtype)

    def scan_step(carry, step_index):
        current_state, previous_state = carry
        next_state, next_previous = tendency_advection_step(
            current_state,
            previous_state,
            initial_tendency,
            step_index,
            step_seconds_array,
            surface_indices=surface_indices,
            lower_indices=lower_indices,
            upper_indices=upper_indices,
            surface_u_indices=surface_u_indices,
            surface_v_indices=surface_v_indices,
            surface_weights=surface_weights,
            lower_u_index=lower_u_index,
            lower_v_index=lower_v_index,
            upper_u_index=upper_u_index,
            upper_v_index=upper_v_index,
            wind_scale=wind_scale,
            max_wind_speed=max_wind_speed,
            diffusion_per_step=diffusion_per_step,
            damping_days=damping_days,
            corrected_advection=corrected_advection,
            tendency_scale=tendency_scale,
            tendency_decay_days=tendency_decay_days,
        )
        packed_state = jnp.concatenate([next_state, next_previous], axis=1)
        return (next_state, next_previous), packed_state

    _, trajectory = jax.lax.scan(
        scan_step,
        (current, previous),
        jnp.arange(max(lead_steps), dtype=initial_state.dtype),
    )
    trajectory = jnp.concatenate([initial_state[jnp.newaxis], trajectory], axis=0)
    return jnp.take(
        trajectory,
        jnp.asarray(lead_steps, dtype=jnp.int32),
        axis=0,
    )


@dataclass(frozen=True)
class TendencyAdvectionDycoreModel:
    """Wind transport plus a decaying tendency estimated from the previous state."""

    name: str = "tendency_advection"
    current_count: int = 10
    surface_indices: tuple[int, ...] = (0, 1, 3, 4)
    lower_indices: tuple[int, ...] = (5, 8, 9)
    upper_indices: tuple[int, ...] = (2, 6, 7)
    surface_u_indices: tuple[int, ...] = (8, 3)
    surface_v_indices: tuple[int, ...] = (9, 4)
    surface_weights: tuple[float, ...] = (0.6, 0.4)
    lower_u_index: int = 8
    lower_v_index: int = 9
    upper_u_index: int = 6
    upper_v_index: int = 7
    wind_scale: float = 0.02
    max_wind_speed: float = 55.0
    diffusion_per_step: float = 0.10
    damping_days: float = 60.0
    corrected_advection: bool = True
    tendency_scale: float = 0.12
    tendency_decay_days: float = 0.25
    jit_forecast: bool = True

    @cached_property
    def forecast_function(self):
        """Return the reusable forecast callable."""
        if not self.jit_forecast:
            return self._forecast
        return jax.jit(self._forecast, static_argnames=("lead_steps",))

    def _forecast(
        self,
        initial_state: jax.Array,
        *,
        lead_steps: tuple[int, ...],
        step_seconds: float,
    ) -> jax.Array:
        return tendency_advection_forecast(
            initial_state,
            lead_steps,
            step_seconds,
            current_count=self.current_count,
            surface_indices=self.surface_indices,
            lower_indices=self.lower_indices,
            upper_indices=self.upper_indices,
            surface_u_indices=self.surface_u_indices,
            surface_v_indices=self.surface_v_indices,
            surface_weights=self.surface_weights,
            lower_u_index=self.lower_u_index,
            lower_v_index=self.lower_v_index,
            upper_u_index=self.upper_u_index,
            upper_v_index=self.upper_v_index,
            wind_scale=self.wind_scale,
            max_wind_speed=self.max_wind_speed,
            diffusion_per_step=self.diffusion_per_step,
            damping_days=self.damping_days,
            corrected_advection=self.corrected_advection,
            tendency_scale=self.tendency_scale,
            tendency_decay_days=self.tendency_decay_days,
        )

    def forecast(
        self,
        initial_state: jax.Array,
        lead_steps: Sequence[int],
        step_seconds: float,
    ) -> jax.Array:
        """Return forecast values shaped as (lead, init, variable, lon, lat)."""
        lead_steps = tuple(int(lead_step) for lead_step in lead_steps)
        assert lead_steps
        assert all(lead_step >= 0 for lead_step in lead_steps)
        assert self.current_count > 0
        assert self.wind_scale >= 0
        assert self.max_wind_speed > 0
        assert self.diffusion_per_step >= 0
        assert self.damping_days > 0
        assert self.tendency_decay_days > 0

        return self.forecast_function(
            jnp.asarray(initial_state),
            lead_steps=lead_steps,
            step_seconds=step_seconds,
        )


def default_tendency_advection_dycore_model() -> TendencyAdvectionDycoreModel:
    """Return the default tendency advection dycore model."""
    return TendencyAdvectionDycoreModel()
