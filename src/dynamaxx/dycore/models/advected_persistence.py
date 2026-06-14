# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

SECONDS_PER_DAY = 86_400.0


def shift_longitude(values: jax.Array, shift_cells: jax.Array | float) -> jax.Array:
    """Periodically shift values eastward along the longitude axis.

    Values are shaped as (..., longitude, latitude). Fractional shifts use
    linear interpolation between neighboring longitudes.
    """
    values = jnp.asarray(values)
    longitude_count = values.shape[-2]
    source_positions = (
        jnp.arange(longitude_count, dtype=values.dtype) - shift_cells
    ) % longitude_count
    lower_indices = jnp.floor(source_positions).astype(jnp.int32)
    upper_indices = (lower_indices + 1) % longitude_count
    interpolation_weight = source_positions - jnp.floor(source_positions)

    lower_values = jnp.take(values, lower_indices, axis=-2)
    upper_values = jnp.take(values, upper_indices, axis=-2)
    weight_shape = (1,) * (values.ndim - 2) + (longitude_count, 1)
    interpolation_weight = jnp.reshape(interpolation_weight, weight_shape)
    return lower_values * (1 - interpolation_weight) + upper_values * (
        interpolation_weight
    )


def advected_persistence_forecast(
    initial_state: jax.Array,
    lead_steps: Sequence[int],
    step_seconds: float,
    *,
    zonal_cells_per_day: float,
    damping_days: float,
) -> jax.Array:
    """Forecast by advecting and damping zonal anomalies."""
    initial_state = jnp.asarray(initial_state)
    lead_step_array = jnp.asarray(tuple(lead_steps), dtype=initial_state.dtype)
    step_days = jnp.asarray(step_seconds / SECONDS_PER_DAY, dtype=initial_state.dtype)
    zonal_mean = jnp.mean(initial_state, axis=-2, keepdims=True)
    anomaly = initial_state - zonal_mean
    damping_day_array = jnp.asarray(damping_days, dtype=initial_state.dtype)
    zonal_cell_array = jnp.asarray(zonal_cells_per_day, dtype=initial_state.dtype)

    def forecast_one_lead(lead_step):
        lead_days = lead_step * step_days
        shifted_anomaly = shift_longitude(
            anomaly,
            shift_cells=zonal_cell_array * lead_days,
        )
        damping = jnp.exp(-lead_days / damping_day_array)
        return zonal_mean + damping * shifted_anomaly

    return jax.vmap(forecast_one_lead)(lead_step_array)


@dataclass(frozen=True)
class AdvectedPersistenceDycoreModel:
    """Persistence model with optional eastward advection and anomaly damping."""

    name: str = "advected_persistence"
    zonal_cells_per_day: float = 0.0
    damping_days: float = 24.0
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
        return advected_persistence_forecast(
            initial_state,
            lead_steps,
            step_seconds,
            zonal_cells_per_day=self.zonal_cells_per_day,
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
        assert self.damping_days > 0

        return self.forecast_function(
            jnp.asarray(initial_state),
            lead_steps=lead_steps,
            step_seconds=step_seconds,
        )


def default_advected_persistence_dycore_model() -> AdvectedPersistenceDycoreModel:
    """Return the default advected persistence dycore model."""
    return AdvectedPersistenceDycoreModel()
