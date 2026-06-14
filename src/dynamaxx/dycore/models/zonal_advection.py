# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

from dynamaxx.dycore.models.wind_advection import weighted_wind
from dynamaxx.dycore.transport import (
    MIN_COS_LATITUDE,
    latitude_radians,
    spectral_longitude_shift,
)
from dynamaxx.utils.consts import EARTH_RADIUS

SECONDS_PER_DAY = 86_400.0


def zonal_cell_displacement(
    u_wind: jax.Array,
    step_seconds: jax.Array,
) -> jax.Array:
    """Return latitude-dependent longitude displacement in grid cells."""
    u_wind = jnp.asarray(u_wind)
    longitude_count, latitude_count = u_wind.shape[-2:]
    latitudes = latitude_radians(latitude_count, u_wind.dtype)
    dlon = 2.0 * jnp.pi / longitude_count
    dx = (
        EARTH_RADIUS * jnp.maximum(jnp.abs(jnp.cos(latitudes)), MIN_COS_LATITUDE) * dlon
    )
    return jnp.mean(u_wind, axis=-2) * step_seconds / dx[jnp.newaxis, :]


def zonal_phase_displacement(
    current_field: jax.Array,
    previous_field: jax.Array,
    wind_displacement: jax.Array,
) -> jax.Array:
    """Estimate zonal phase motion from input history within wind bounds."""
    current_field = jnp.asarray(current_field)
    previous_field = jnp.asarray(previous_field)
    current_anomaly = current_field - jnp.mean(current_field, axis=-2, keepdims=True)
    previous_anomaly = previous_field - jnp.mean(
        previous_field,
        axis=-2,
        keepdims=True,
    )
    longitude_gradient = 0.5 * (
        jnp.roll(current_anomaly, shift=-1, axis=-2)
        - jnp.roll(current_anomaly, shift=1, axis=-2)
    )
    anomaly_change = current_anomaly - previous_anomaly
    numerator = -jnp.sum(anomaly_change * longitude_gradient, axis=-2)
    denominator = (
        jnp.sum(longitude_gradient * longitude_gradient, axis=-2)
        + jnp.finfo(current_field.dtype).eps
    )
    displacement = numerator / denominator
    displacement_bound = jnp.abs(wind_displacement)
    return jnp.clip(displacement, -displacement_bound, displacement_bound)


def shift_variable_group(
    state: jax.Array,
    *,
    variable_indices: tuple[int, ...],
    displacement_cells: jax.Array,
) -> jax.Array:
    """Return state with one variable group shifted in longitude."""
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    group_state = jnp.take(state, indices, axis=1)
    shifted_group = spectral_longitude_shift(group_state, displacement_cells)
    return state.at[:, indices].set(shifted_group)


def zonal_advection_forecast(
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
    damping_days: float,
    lower_phase_reference_index: int | None = None,
    upper_phase_reference_index: int | None = None,
    phase_history_offset: int | None = None,
) -> jax.Array:
    """Roll out exact zonal wave transport from fixed initial steering winds."""
    initial_state = jnp.asarray(initial_state)
    assert initial_state.ndim == 4
    all_indices = (
        surface_indices
        + lower_indices
        + upper_indices
        + surface_u_indices
        + surface_v_indices
        + (lower_u_index, lower_v_index, upper_u_index, upper_v_index)
    )
    assert all(0 <= index < initial_state.shape[1] for index in all_indices)
    if (
        lower_phase_reference_index is not None
        or upper_phase_reference_index is not None
    ):
        assert phase_history_offset is not None
    history_offset = phase_history_offset
    if lower_phase_reference_index is not None:
        assert history_offset is not None
        assert 0 <= lower_phase_reference_index < initial_state.shape[1]
        assert (
            0 <= history_offset + lower_phase_reference_index < initial_state.shape[1]
        )
    if upper_phase_reference_index is not None:
        assert history_offset is not None
        assert 0 <= upper_phase_reference_index < initial_state.shape[1]
        assert (
            0 <= history_offset + upper_phase_reference_index < initial_state.shape[1]
        )

    step_seconds_array = jnp.asarray(step_seconds, dtype=initial_state.dtype)
    surface_u_wind, _ = weighted_wind(
        initial_state,
        u_indices=surface_u_indices,
        v_indices=surface_v_indices,
        weights=surface_weights,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    lower_u_wind, _ = weighted_wind(
        initial_state,
        u_indices=(lower_u_index,),
        v_indices=(lower_v_index,),
        weights=(1.0,),
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    upper_u_wind, _ = weighted_wind(
        initial_state,
        u_indices=(upper_u_index,),
        v_indices=(upper_v_index,),
        weights=(1.0,),
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    surface_displacement = zonal_cell_displacement(surface_u_wind, step_seconds_array)
    lower_displacement = zonal_cell_displacement(lower_u_wind, step_seconds_array)
    upper_displacement = zonal_cell_displacement(upper_u_wind, step_seconds_array)
    if lower_phase_reference_index is not None:
        assert history_offset is not None
        lower_displacement = zonal_phase_displacement(
            initial_state[:, lower_phase_reference_index],
            initial_state[:, history_offset + lower_phase_reference_index],
            lower_displacement,
        )
    if upper_phase_reference_index is not None:
        assert history_offset is not None
        upper_displacement = zonal_phase_displacement(
            initial_state[:, upper_phase_reference_index],
            initial_state[:, history_offset + upper_phase_reference_index],
            upper_displacement,
        )
    damping = jnp.exp(-step_seconds_array / (damping_days * SECONDS_PER_DAY))

    def scan_step(state, _):
        next_state = shift_variable_group(
            state,
            variable_indices=surface_indices,
            displacement_cells=surface_displacement,
        )
        next_state = shift_variable_group(
            next_state,
            variable_indices=lower_indices,
            displacement_cells=lower_displacement,
        )
        next_state = shift_variable_group(
            next_state,
            variable_indices=upper_indices,
            displacement_cells=upper_displacement,
        )
        zonal_mean = jnp.mean(next_state, axis=-2, keepdims=True)
        next_state = zonal_mean + damping * (next_state - zonal_mean)
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
class ZonalAdvectionDycoreModel:
    """Exact longitude-wave transport using fixed initial zonal steering winds."""

    name: str = "zonal_advection"
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
    wind_scale: float = 0.20
    max_wind_speed: float = 55.0
    damping_days: float = 30.0
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
        return zonal_advection_forecast(
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
            damping_days=self.damping_days,
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
        assert self.wind_scale >= 0
        assert self.max_wind_speed > 0
        assert self.damping_days > 0
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


def default_zonal_advection_dycore_model() -> ZonalAdvectionDycoreModel:
    """Return the default zonal advection dycore model."""
    return ZonalAdvectionDycoreModel()
