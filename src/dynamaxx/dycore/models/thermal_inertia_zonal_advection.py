# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

from dynamaxx.dycore.models.zonal_advection import zonal_advection_forecast


def persist_channel(
    forecast: jax.Array,
    initial_state: jax.Array,
    *,
    channel_index: int,
) -> jax.Array:
    """Return forecast with one channel held fixed at initialization."""
    forecast = jnp.asarray(forecast)
    initial_state = jnp.asarray(initial_state, dtype=forecast.dtype)
    assert forecast.ndim == 5
    assert initial_state.ndim == 4
    assert forecast.shape[1:] == initial_state.shape
    assert 0 <= channel_index < forecast.shape[2]

    initial_channel = initial_state[:, channel_index : channel_index + 1]
    return forecast.at[:, :, channel_index : channel_index + 1].set(
        initial_channel[jnp.newaxis],
    )


def thermal_inertia_zonal_advection_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    temperature_index: int,
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
    damping_days: float,
) -> jax.Array:
    """Roll out zonal circulation while holding 2m temperature inertial."""
    forecast = zonal_advection_forecast(
        initial_state,
        lead_steps,
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
        damping_days=damping_days,
    )
    return persist_channel(
        forecast,
        initial_state,
        channel_index=temperature_index,
    )


@dataclass(frozen=True)
class ThermalInertiaZonalAdvectionDycoreModel:
    """Zonal wave transport with inertial near-surface temperature."""

    name: str = "thermal_inertia_zonal_advection"
    temperature_index: int = 0
    surface_indices: tuple[int, ...] = (1, 3, 4)
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
    damping_days: float = 10.0
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
        return thermal_inertia_zonal_advection_forecast(
            initial_state,
            lead_steps,
            step_seconds,
            temperature_index=self.temperature_index,
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
            damping_days=self.damping_days,
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
        assert self.temperature_index not in self.surface_indices
        assert self.temperature_index not in self.lower_indices
        assert self.temperature_index not in self.upper_indices
        assert self.wind_scale >= 0
        assert self.max_wind_speed > 0
        assert self.damping_days > 0

        return self.forecast_function(
            jnp.asarray(initial_state),
            lead_steps=lead_steps,
            step_seconds=step_seconds,
        )


def default_thermal_inertia_zonal_advection_dycore_model() -> (
    ThermalInertiaZonalAdvectionDycoreModel
):
    """Return the default thermal-inertia zonal advection dycore model."""
    return ThermalInertiaZonalAdvectionDycoreModel()
