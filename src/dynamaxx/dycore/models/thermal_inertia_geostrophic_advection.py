# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

from dynamaxx.dycore.models.geostrophic_advection import geostrophic_advection_forecast
from dynamaxx.dycore.models.thermal_inertia_zonal_advection import persist_channel


def thermal_inertia_geostrophic_advection_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    temperature_index: int,
    geopotential_index: int,
    flow_scale: float,
    max_wind_speed: float,
    diffusion_per_step: float,
    damping_days: float,
) -> jax.Array:
    """Roll out balanced-flow transport while holding near-surface temperature."""
    forecast = geostrophic_advection_forecast(
        initial_state,
        lead_steps,
        step_seconds,
        geopotential_index=geopotential_index,
        flow_scale=flow_scale,
        max_wind_speed=max_wind_speed,
        diffusion_per_step=diffusion_per_step,
        damping_days=damping_days,
    )
    return persist_channel(
        forecast,
        initial_state,
        channel_index=temperature_index,
    )


@dataclass(frozen=True)
class ThermalInertiaGeostrophicAdvectionDycoreModel:
    """Geostrophic transport with inertial near-surface temperature."""

    name: str = "thermal_inertia_geostrophic_advection"
    temperature_index: int = 0
    geopotential_index: int = 2
    flow_scale: float = 0.02
    max_wind_speed: float = 60.0
    diffusion_per_step: float = 0.0
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
        return thermal_inertia_geostrophic_advection_forecast(
            initial_state,
            lead_steps,
            step_seconds,
            temperature_index=self.temperature_index,
            geopotential_index=self.geopotential_index,
            flow_scale=self.flow_scale,
            max_wind_speed=self.max_wind_speed,
            diffusion_per_step=self.diffusion_per_step,
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
        assert self.temperature_index != self.geopotential_index
        assert self.flow_scale >= 0
        assert self.max_wind_speed > 0
        assert self.diffusion_per_step >= 0
        assert self.damping_days > 0

        return self.forecast_function(
            jnp.asarray(initial_state),
            lead_steps=lead_steps,
            step_seconds=step_seconds,
        )


def default_thermal_inertia_geostrophic_advection_dycore_model() -> (
    ThermalInertiaGeostrophicAdvectionDycoreModel
):
    """Return the default thermal-inertia geostrophic advection dycore model."""
    return ThermalInertiaGeostrophicAdvectionDycoreModel()
