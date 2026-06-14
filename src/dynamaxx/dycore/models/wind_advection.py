# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

from dynamaxx.dycore.transport import (
    cell_laplacian,
    semi_lagrangian_advect,
    semi_lagrangian_advect_corrected,
)

SECONDS_PER_DAY = 86_400.0
REFERENCE_STEP_SECONDS = 21_600.0


def weighted_wind(
    state: jax.Array,
    *,
    u_indices: tuple[int, ...],
    v_indices: tuple[int, ...],
    weights: tuple[float, ...],
    wind_scale: float,
    max_wind_speed: float,
) -> tuple[jax.Array, jax.Array]:
    """Return clipped steering winds from prognostic u/v channels."""
    state = jnp.asarray(state)
    assert len(u_indices) == len(v_indices) == len(weights)

    weight_array = jnp.asarray(weights, dtype=state.dtype)
    weight_array = weight_array / jnp.sum(weight_array)
    u_stack = jnp.stack([state[:, channel_index] for channel_index in u_indices])
    v_stack = jnp.stack([state[:, channel_index] for channel_index in v_indices])
    u_wind = wind_scale * jnp.tensordot(weight_array, u_stack, axes=1)
    v_wind = wind_scale * jnp.tensordot(weight_array, v_stack, axes=1)

    speed = jnp.sqrt(u_wind * u_wind + v_wind * v_wind)
    speed_scale = jnp.minimum(1.0, max_wind_speed / jnp.maximum(speed, 1.0e-6))
    return u_wind * speed_scale, v_wind * speed_scale


def steering_wind_groups(
    state: jax.Array,
    *,
    surface_u_indices: tuple[int, ...],
    surface_v_indices: tuple[int, ...],
    surface_weights: tuple[float, ...],
    lower_u_index: int,
    lower_v_index: int,
    upper_u_index: int,
    upper_v_index: int,
    wind_scale: float,
    max_wind_speed: float,
) -> tuple[
    tuple[jax.Array, jax.Array],
    tuple[jax.Array, jax.Array],
    tuple[jax.Array, jax.Array],
]:
    """Return surface, lower-level, and upper-level steering wind groups."""
    surface_wind = weighted_wind(
        state,
        u_indices=surface_u_indices,
        v_indices=surface_v_indices,
        weights=surface_weights,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    lower_wind = weighted_wind(
        state,
        u_indices=(lower_u_index,),
        v_indices=(lower_v_index,),
        weights=(1.0,),
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    upper_wind = weighted_wind(
        state,
        u_indices=(upper_u_index,),
        v_indices=(upper_v_index,),
        weights=(1.0,),
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    return surface_wind, lower_wind, upper_wind


def advect_variable_group(
    state: jax.Array,
    variable_indices: tuple[int, ...],
    u_wind: jax.Array,
    v_wind: jax.Array,
    step_seconds: jax.Array,
    *,
    corrected_advection: bool,
) -> jax.Array:
    """Semi-Lagrangian advect one variable group with a shared wind."""
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    group_state = jnp.take(state, indices, axis=1)
    if corrected_advection:
        return semi_lagrangian_advect_corrected(
            group_state,
            u_wind,
            v_wind,
            step_seconds,
        )
    return semi_lagrangian_advect(group_state, u_wind, v_wind, step_seconds)


def set_variable_group(
    state: jax.Array,
    variable_indices: tuple[int, ...],
    group_state: jax.Array,
) -> jax.Array:
    """Return state with one variable group replaced."""
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    return state.at[:, indices].set(group_state)


def wind_advection_step_with_steering(
    state: jax.Array,
    step_seconds: jax.Array,
    *,
    surface_indices: tuple[int, ...],
    lower_indices: tuple[int, ...],
    upper_indices: tuple[int, ...],
    surface_wind: tuple[jax.Array, jax.Array],
    lower_wind: tuple[jax.Array, jax.Array],
    upper_wind: tuple[jax.Array, jax.Array],
    diffusion_per_step: float,
    damping_days: float,
    corrected_advection: bool,
) -> jax.Array:
    """Advance one transport step with supplied steering wind groups."""
    surface_state = advect_variable_group(
        state,
        surface_indices,
        surface_wind[0],
        surface_wind[1],
        step_seconds,
        corrected_advection=corrected_advection,
    )
    lower_state = advect_variable_group(
        state,
        lower_indices,
        lower_wind[0],
        lower_wind[1],
        step_seconds,
        corrected_advection=corrected_advection,
    )
    upper_state = advect_variable_group(
        state,
        upper_indices,
        upper_wind[0],
        upper_wind[1],
        step_seconds,
        corrected_advection=corrected_advection,
    )
    advected = set_variable_group(state, surface_indices, surface_state)
    advected = set_variable_group(advected, lower_indices, lower_state)
    advected = set_variable_group(advected, upper_indices, upper_state)
    diffusion_amount = diffusion_per_step * step_seconds / REFERENCE_STEP_SECONDS
    diffused = advected + diffusion_amount * cell_laplacian(advected)
    zonal_mean = jnp.mean(diffused, axis=-2, keepdims=True)
    damping = jnp.exp(-step_seconds / (damping_days * SECONDS_PER_DAY))
    return zonal_mean + damping * (diffused - zonal_mean)


def wind_advection_step(
    state: jax.Array,
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
) -> jax.Array:
    """Advance one wind-driven semi-Lagrangian transport step."""
    surface_wind, lower_wind, upper_wind = steering_wind_groups(
        state,
        surface_u_indices=surface_u_indices,
        surface_v_indices=surface_v_indices,
        surface_weights=surface_weights,
        lower_u_index=lower_u_index,
        lower_v_index=lower_v_index,
        upper_u_index=upper_u_index,
        upper_v_index=upper_v_index,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    return wind_advection_step_with_steering(
        state,
        step_seconds,
        surface_indices=surface_indices,
        lower_indices=lower_indices,
        upper_indices=upper_indices,
        surface_wind=surface_wind,
        lower_wind=lower_wind,
        upper_wind=upper_wind,
        diffusion_per_step=diffusion_per_step,
        damping_days=damping_days,
        corrected_advection=corrected_advection,
    )


def wind_advection_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
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
    fixed_steering_wind: bool,
) -> jax.Array:
    """Roll out a wind-driven semi-Lagrangian forecast."""
    initial_state = jnp.asarray(initial_state)
    assert initial_state.ndim == 4
    assert len(surface_u_indices) == len(surface_v_indices) == len(surface_weights)
    all_indices = (
        surface_indices
        + lower_indices
        + upper_indices
        + surface_u_indices
        + surface_v_indices
        + (lower_u_index, lower_v_index, upper_u_index, upper_v_index)
    )
    assert all(0 <= index < initial_state.shape[1] for index in all_indices)
    step_seconds_array = jnp.asarray(step_seconds, dtype=initial_state.dtype)
    if fixed_steering_wind:
        fixed_surface_wind, fixed_lower_wind, fixed_upper_wind = steering_wind_groups(
            initial_state,
            surface_u_indices=surface_u_indices,
            surface_v_indices=surface_v_indices,
            surface_weights=surface_weights,
            lower_u_index=lower_u_index,
            lower_v_index=lower_v_index,
            upper_u_index=upper_u_index,
            upper_v_index=upper_v_index,
            wind_scale=wind_scale,
            max_wind_speed=max_wind_speed,
        )

    def scan_step(state, _):
        if fixed_steering_wind:
            next_state = wind_advection_step_with_steering(
                state,
                step_seconds_array,
                surface_indices=surface_indices,
                lower_indices=lower_indices,
                upper_indices=upper_indices,
                surface_wind=fixed_surface_wind,
                lower_wind=fixed_lower_wind,
                upper_wind=fixed_upper_wind,
                diffusion_per_step=diffusion_per_step,
                damping_days=damping_days,
                corrected_advection=corrected_advection,
            )
        else:
            next_state = wind_advection_step(
                state,
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
            )
        return next_state, next_state

    _, trajectory = jax.lax.scan(
        scan_step,
        initial_state,
        None,
        length=max(lead_steps),
    )
    trajectory = jnp.concatenate([initial_state[jnp.newaxis], trajectory], axis=0)
    return jnp.take(
        trajectory,
        jnp.asarray(lead_steps, dtype=jnp.int32),
        axis=0,
    )


@dataclass(frozen=True)
class WindAdvectionDycoreModel:
    """Semi-Lagrangian transport using prognostic wind channels."""

    name: str = "wind_advection"
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
    wind_scale: float = 0.10
    max_wind_speed: float = 55.0
    diffusion_per_step: float = 0.03
    damping_days: float = 60.0
    corrected_advection: bool = False
    fixed_steering_wind: bool = True
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
        return wind_advection_forecast(
            initial_state,
            lead_steps,
            step_seconds,
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
            fixed_steering_wind=self.fixed_steering_wind,
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
        assert (
            len(self.surface_u_indices)
            == len(self.surface_v_indices)
            == len(self.surface_weights)
        )
        assert self.wind_scale >= 0
        assert self.max_wind_speed > 0
        assert self.diffusion_per_step >= 0
        assert self.damping_days > 0

        return self.forecast_function(
            jnp.asarray(initial_state),
            lead_steps=lead_steps,
            step_seconds=step_seconds,
        )


def default_wind_advection_dycore_model() -> WindAdvectionDycoreModel:
    """Return the default wind advection dycore model."""
    return WindAdvectionDycoreModel()
