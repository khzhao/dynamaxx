# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

from dynamaxx.dycore.models.geostrophic_advection import geostrophic_advection_forecast
from dynamaxx.dycore.models.thermal_inertia_zonal_advection import persist_channel
from dynamaxx.dycore.models.zonal_advection import zonal_advection_forecast


def unique_indices(indices: tuple[int, ...]) -> tuple[int, ...]:
    """Return indices in first-seen order without duplicates."""
    return tuple(dict.fromkeys(indices))


def layered_balanced_zonal_advection_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
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
    lower_phase_reference_index: int | None = None,
    upper_phase_reference_index: int | None = None,
    phase_history_offset: int | None = None,
) -> jax.Array:
    """Roll out layer-split zonal-wave and balanced-flow transport."""
    zonal_forecast = zonal_advection_forecast(
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
        wind_scale=zonal_wind_scale,
        max_wind_speed=zonal_max_wind_speed,
        damping_days=zonal_damping_days,
        lower_phase_reference_index=lower_phase_reference_index,
        upper_phase_reference_index=upper_phase_reference_index,
        phase_history_offset=phase_history_offset,
    )
    balanced_indices = unique_indices(
        (balanced_geopotential_index,) + balanced_surface_indices
    )
    balanced_initial_state = jnp.take(
        initial_state,
        jnp.asarray(balanced_indices, dtype=jnp.int32),
        axis=1,
    )
    balanced_forecast = geostrophic_advection_forecast(
        balanced_initial_state,
        lead_steps,
        step_seconds,
        geopotential_index=balanced_indices.index(balanced_geopotential_index),
        flow_scale=balanced_flow_scale,
        max_wind_speed=balanced_max_wind_speed,
        diffusion_per_step=balanced_diffusion_per_step,
        damping_days=balanced_damping_days,
    )
    balanced_surface_positions = tuple(
        balanced_indices.index(index) for index in balanced_surface_indices
    )
    balanced_surface_forecast = jnp.take(
        balanced_forecast,
        jnp.asarray(balanced_surface_positions, dtype=jnp.int32),
        axis=2,
    )
    forecast = zonal_forecast.at[
        :, :, jnp.asarray(balanced_surface_indices, dtype=jnp.int32)
    ].set(balanced_surface_forecast)
    return persist_channel(
        forecast,
        initial_state,
        channel_index=temperature_index,
    )


@dataclass(frozen=True)
class LayeredBalancedZonalAdvectionDycoreModel:
    """Zonal upper-layer waves with balanced-flow surface transport."""

    name: str = "layered_balanced_zonal_advection"
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
    lower_phase_reference_index: int | None = None
    upper_phase_reference_index: int | None = None
    phase_history_offset: int | None = None
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
        return layered_balanced_zonal_advection_forecast(
            initial_state,
            lead_steps,
            step_seconds,
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
            lower_phase_reference_index=self.lower_phase_reference_index,
            upper_phase_reference_index=self.upper_phase_reference_index,
            phase_history_offset=self.phase_history_offset,
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
        assert self.temperature_index not in self.balanced_surface_indices
        assert self.balanced_geopotential_index not in self.balanced_surface_indices
        assert self.zonal_wind_scale >= 0
        assert self.zonal_max_wind_speed > 0
        assert self.zonal_damping_days > 0
        assert self.balanced_flow_scale >= 0
        assert self.balanced_max_wind_speed > 0
        assert self.balanced_diffusion_per_step >= 0
        assert self.balanced_damping_days > 0
        if (
            self.lower_phase_reference_index is not None
            or self.upper_phase_reference_index is not None
        ):
            assert self.phase_history_offset is not None

        return self.forecast_function(
            jnp.asarray(initial_state),
            lead_steps=lead_steps,
            step_seconds=step_seconds,
        )


def default_layered_balanced_zonal_advection_dycore_model() -> (
    LayeredBalancedZonalAdvectionDycoreModel
):
    """Return the default layered balanced-zonal advection dycore model."""
    return LayeredBalancedZonalAdvectionDycoreModel()
