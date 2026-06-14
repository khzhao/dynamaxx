# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

from dynamaxx.dycore.models.layered_balanced_zonal_advection import (
    layered_balanced_zonal_advection_forecast,
)

SECONDS_PER_DAY = 86_400.0


def add_decaying_tendency(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
    decay_days: float,
) -> jax.Array:
    """Add a short-memory current-minus-previous tendency to selected channels."""
    forecast = jnp.asarray(forecast)
    initial_state = jnp.asarray(initial_state, dtype=forecast.dtype)
    assert forecast.ndim == 5
    assert initial_state.ndim == 4
    assert initial_state.shape[1] >= 2 * current_count
    assert forecast.shape[1:] == initial_state.shape

    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    tendency = current_state - previous_state
    lead_days = (
        jnp.asarray(lead_steps, dtype=forecast.dtype)
        * jnp.asarray(step_seconds, dtype=forecast.dtype)
        / SECONDS_PER_DAY
    )
    decay = jnp.exp(-lead_days / decay_days)
    correction = (
        decay[:, jnp.newaxis, jnp.newaxis, jnp.newaxis, jnp.newaxis]
        * tendency[jnp.newaxis]
    )
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    return forecast.at[:, :, indices].set(
        jnp.take(forecast, indices, axis=2) + jnp.take(correction, indices, axis=2)
    )


def inertial_layered_balanced_zonal_advection_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    tendency_indices: tuple[int, ...],
    tendency_decay_days: float,
    temperature_index: int,
    surface_indices: tuple[int, ...],
    lower_indices: tuple[int, ...],
    upper_indices: tuple[int, ...],
    balanced_surface_indices: tuple[int, ...],
    balanced_geopotential_index: int,
    surface_u_indices: tuple[int, ...],
    surface_v_indices: tuple[int, ...],
    surface_weights: tuple[float, ...],
    lower_u_index: int,
    lower_v_index: int,
    upper_u_index: int,
    upper_v_index: int,
    zonal_wind_scale: float,
    zonal_max_wind_speed: float,
    zonal_damping_days: float,
    balanced_flow_scale: float,
    balanced_max_wind_speed: float,
    balanced_diffusion_per_step: float,
    balanced_damping_days: float,
) -> jax.Array:
    """Roll out layered transport plus a short-memory upper-level inertia."""
    forecast = layered_balanced_zonal_advection_forecast(
        initial_state,
        lead_steps,
        step_seconds,
        temperature_index=temperature_index,
        surface_indices=surface_indices,
        lower_indices=lower_indices,
        upper_indices=upper_indices,
        balanced_surface_indices=balanced_surface_indices,
        balanced_geopotential_index=balanced_geopotential_index,
        surface_u_indices=surface_u_indices,
        surface_v_indices=surface_v_indices,
        surface_weights=surface_weights,
        lower_u_index=lower_u_index,
        lower_v_index=lower_v_index,
        upper_u_index=upper_u_index,
        upper_v_index=upper_v_index,
        zonal_wind_scale=zonal_wind_scale,
        zonal_max_wind_speed=zonal_max_wind_speed,
        zonal_damping_days=zonal_damping_days,
        balanced_flow_scale=balanced_flow_scale,
        balanced_max_wind_speed=balanced_max_wind_speed,
        balanced_diffusion_per_step=balanced_diffusion_per_step,
        balanced_damping_days=balanced_damping_days,
    )
    return add_decaying_tendency(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        variable_indices=tendency_indices,
        decay_days=tendency_decay_days,
    )


@dataclass(frozen=True)
class InertialLayeredBalancedZonalAdvectionDycoreModel:
    """Layered balanced-zonal transport with short-memory upper-level inertia."""

    name: str = "inertial_layered_balanced_zonal_advection"
    current_count: int = 10
    tendency_indices: tuple[int, ...] = (2, 6, 7)
    tendency_decay_days: float = 1.0
    temperature_index: int = 0
    surface_indices: tuple[int, ...] = (1, 3, 4)
    lower_indices: tuple[int, ...] = (5, 8, 9)
    upper_indices: tuple[int, ...] = (2, 6, 7)
    balanced_surface_indices: tuple[int, ...] = (1, 3, 4)
    balanced_geopotential_index: int = 2
    surface_u_indices: tuple[int, ...] = (8, 3)
    surface_v_indices: tuple[int, ...] = (9, 4)
    surface_weights: tuple[float, ...] = (0.6, 0.4)
    lower_u_index: int = 8
    lower_v_index: int = 9
    upper_u_index: int = 6
    upper_v_index: int = 7
    zonal_wind_scale: float = 0.10
    zonal_max_wind_speed: float = 55.0
    zonal_damping_days: float = 10.0
    balanced_flow_scale: float = 0.02
    balanced_max_wind_speed: float = 60.0
    balanced_diffusion_per_step: float = 0.0
    balanced_damping_days: float = 10.0
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
        return inertial_layered_balanced_zonal_advection_forecast(
            initial_state,
            lead_steps,
            step_seconds,
            current_count=self.current_count,
            tendency_indices=self.tendency_indices,
            tendency_decay_days=self.tendency_decay_days,
            temperature_index=self.temperature_index,
            surface_indices=self.surface_indices,
            lower_indices=self.lower_indices,
            upper_indices=self.upper_indices,
            balanced_surface_indices=self.balanced_surface_indices,
            balanced_geopotential_index=self.balanced_geopotential_index,
            surface_u_indices=self.surface_u_indices,
            surface_v_indices=self.surface_v_indices,
            surface_weights=self.surface_weights,
            lower_u_index=self.lower_u_index,
            lower_v_index=self.lower_v_index,
            upper_u_index=self.upper_u_index,
            upper_v_index=self.upper_v_index,
            zonal_wind_scale=self.zonal_wind_scale,
            zonal_max_wind_speed=self.zonal_max_wind_speed,
            zonal_damping_days=self.zonal_damping_days,
            balanced_flow_scale=self.balanced_flow_scale,
            balanced_max_wind_speed=self.balanced_max_wind_speed,
            balanced_diffusion_per_step=self.balanced_diffusion_per_step,
            balanced_damping_days=self.balanced_damping_days,
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
        assert self.tendency_decay_days > 0
        assert all(0 <= index < self.current_count for index in self.tendency_indices)
        assert self.temperature_index not in self.tendency_indices
        assert (
            len(self.surface_u_indices)
            == len(self.surface_v_indices)
            == len(self.surface_weights)
        )
        assert self.temperature_index not in self.surface_indices
        assert self.temperature_index not in self.lower_indices
        assert self.temperature_index not in self.upper_indices
        assert self.temperature_index not in self.balanced_surface_indices
        assert self.balanced_geopotential_index not in self.balanced_surface_indices
        assert self.zonal_wind_scale >= 0
        assert self.zonal_max_wind_speed > 0
        assert self.zonal_damping_days > 0
        assert self.balanced_flow_scale >= 0
        assert self.balanced_max_wind_speed > 0
        assert self.balanced_diffusion_per_step >= 0
        assert self.balanced_damping_days > 0

        return self.forecast_function(
            jnp.asarray(initial_state),
            lead_steps=lead_steps,
            step_seconds=step_seconds,
        )


def default_inertial_layered_balanced_zonal_advection_dycore_model() -> (
    InertialLayeredBalancedZonalAdvectionDycoreModel
):
    """Return the default inertial layered balanced-zonal advection dycore."""
    return InertialLayeredBalancedZonalAdvectionDycoreModel()
