# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property
from math import log

import jax
import jax.numpy as jnp

from dynamaxx.dycore.models.barotropic_vorticity import barotropic_vorticity_forecast
from dynamaxx.dycore.models.geostrophic_advection import (
    latitude_gradient,
    longitude_gradient,
)
from dynamaxx.dycore.models.layered_balanced_zonal_advection import (
    layered_balanced_zonal_advection_forecast,
)
from dynamaxx.dycore.models.optical_flow_advection import (
    advect_with_cell_displacement,
    estimate_optical_flow_cells,
)
from dynamaxx.dycore.models.transported_inertia_layered_balanced_zonal_advection import (
    add_transported_upper_tendency,
)
from dynamaxx.dycore.models.wind_advection import weighted_wind
from dynamaxx.dycore.models.zonal_advection import (
    shift_variable_group,
    zonal_cell_displacement,
    zonal_phase_displacement,
)
from dynamaxx.dycore.transport import (
    latitude_radians,
    scale_selective_horizontal_cross_filter,
    scale_selective_latitude_filter,
    scale_selective_longitude_filter,
    semi_lagrangian_advect_corrected,
)
from dynamaxx.utils.consts import EARTH_ANGULAR_VELOCITY, EARTH_RADIUS

SECONDS_PER_DAY = 86_400.0
SECONDS_PER_HOUR = 3_600.0


LOWER_TEMPERATURE_INDEX = 5
REFERENCE_LATITUDE_RADIANS = 0.75
DRY_AIR_GAS_CONSTANT = 287.05
MIN_HYDROSTATIC_TEMPERATURE = 180.0
MIN_SURFACE_AIR_DENSITY = 0.1
LOWER_MIDLEVEL_LOG_PRESSURE_RATIO = log(850.0 / 500.0)
BAROCLINIC_LAYER_DEPTH = 5_500.0
BRUNT_VAISALA_FREQUENCY = 0.012
EADY_GROWTH_COEFFICIENT = 0.31


def surface_pressure_tendency_correction(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    pressure_index: int,
    surface_u_indices: tuple[int, ...],
    surface_v_indices: tuple[int, ...],
    surface_weights: tuple[float, ...],
    wind_scale: float,
    max_wind_speed: float,
    decay_days: float,
) -> jax.Array:
    """Return transported short-memory pressure tendency corrections."""
    initial_state = jnp.asarray(initial_state)
    assert initial_state.ndim == 4
    assert initial_state.shape[1] >= 2 * current_count

    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    tendency = current_state - previous_state
    u_wind, _ = weighted_wind(
        current_state,
        u_indices=surface_u_indices,
        v_indices=surface_v_indices,
        weights=surface_weights,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    displacement = zonal_cell_displacement(
        u_wind,
        jnp.asarray(step_seconds, dtype=initial_state.dtype),
    )

    def scan_step(state, _):
        shifted = shift_variable_group(
            state,
            variable_indices=(pressure_index,),
            displacement_cells=displacement,
        )
        return shifted, shifted

    _, trajectory = jax.lax.scan(
        scan_step,
        tendency,
        None,
        length=max(lead_steps),
    )
    trajectory = jnp.concatenate([tendency[jnp.newaxis], trajectory], axis=0)
    correction = jnp.take(
        trajectory,
        jnp.asarray(lead_steps, dtype=jnp.int32),
        axis=0,
    )
    lead_days = (
        jnp.asarray(lead_steps, dtype=initial_state.dtype)
        * jnp.asarray(step_seconds, dtype=initial_state.dtype)
        / SECONDS_PER_DAY
    )
    decay = jnp.exp(-lead_days / decay_days)
    return decay[:, jnp.newaxis, jnp.newaxis, jnp.newaxis, jnp.newaxis] * correction


def upper_pressure_tendency_correction(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    pressure_index: int,
    upper_u_index: int,
    upper_v_index: int,
    wind_scale: float,
    max_wind_speed: float,
    decay_days: float,
) -> jax.Array:
    """Return pressure tendency corrections steered by upper-level flow."""
    return surface_pressure_tendency_correction(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        pressure_index=pressure_index,
        surface_u_indices=(upper_u_index,),
        surface_v_indices=(upper_v_index,),
        surface_weights=(1.0,),
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
        decay_days=decay_days,
    )


def transported_boundary_layer_offset_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    temperature_index: int,
    lower_temperature_index: int,
    lower_u_index: int,
    lower_v_index: int,
    wind_scale: float,
    max_wind_speed: float,
    zonal_damping_days: float,
) -> jax.Array:
    """Return transported 2 m minus lower-tropospheric temperature offset."""
    initial_state = jnp.asarray(initial_state)
    assert initial_state.ndim == 4
    assert initial_state.shape[1] >= current_count

    current_state = initial_state[:, :current_count]
    u_wind, v_wind = weighted_wind(
        current_state,
        u_indices=(lower_u_index,),
        v_indices=(lower_v_index,),
        weights=(1.0,),
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    offset_state = (
        current_state[:, temperature_index : temperature_index + 1]
        - current_state[:, lower_temperature_index : lower_temperature_index + 1]
    )
    step_seconds_array = jnp.asarray(step_seconds, dtype=initial_state.dtype)
    step_damping = jnp.exp(-step_seconds_array / (zonal_damping_days * SECONDS_PER_DAY))

    def scan_step(state, _):
        transported = semi_lagrangian_advect_corrected(
            state,
            u_wind,
            v_wind,
            step_seconds_array,
        )
        zonal_mean = jnp.mean(transported, axis=-2, keepdims=True)
        transported = zonal_mean + step_damping * (transported - zonal_mean)
        return transported, transported

    _, trajectory = jax.lax.scan(
        scan_step,
        offset_state,
        None,
        length=max(lead_steps),
    )
    trajectory = jnp.concatenate([offset_state[jnp.newaxis], trajectory], axis=0)
    return jnp.take(
        trajectory,
        jnp.asarray(lead_steps, dtype=jnp.int32),
        axis=0,
    )[:, :, 0]


def surface_temperature_memory_forecast(
    initial_state: jax.Array,
    lower_temperature_forecast: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    temperature_index: int,
    lower_temperature_index: int,
    lower_u_index: int,
    lower_v_index: int,
    wind_scale: float,
    max_wind_speed: float,
    zonal_damping_days: float,
    memory_decay_days: float,
) -> jax.Array:
    """Return short-memory thermal forecast using lower-air offset transport."""
    initial_state = jnp.asarray(initial_state)
    lower_temperature_forecast = jnp.asarray(lower_temperature_forecast)
    assert initial_state.ndim == 4
    assert initial_state.shape[1] >= current_count

    current_state = initial_state[:, :current_count]
    offset_forecast = transported_boundary_layer_offset_forecast(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        temperature_index=temperature_index,
        lower_temperature_index=lower_temperature_index,
        lower_u_index=lower_u_index,
        lower_v_index=lower_v_index,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
        zonal_damping_days=zonal_damping_days,
    )
    persisted = current_state[jnp.newaxis, :, temperature_index]
    dynamic_temperature = lower_temperature_forecast + offset_forecast
    lead_days = (
        jnp.asarray(lead_steps, dtype=initial_state.dtype)
        * jnp.asarray(step_seconds, dtype=initial_state.dtype)
        / SECONDS_PER_DAY
    )
    memory = jnp.exp(-lead_days / memory_decay_days)
    return persisted + memory[:, jnp.newaxis, jnp.newaxis, jnp.newaxis] * (
        dynamic_temperature - persisted
    )


def add_lower_air_surface_temperature_anchor(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    temperature_index: int,
    lower_temperature_index: int,
    anchor_weight: float,
    ramp_days: float,
    decay_days: float,
) -> jax.Array:
    """Anchor T2m to lower-air evolution plus the initialized surface offset."""
    if anchor_weight <= 0.0:
        return forecast

    forecast = jnp.asarray(forecast)
    initial_state = jnp.asarray(initial_state, dtype=forecast.dtype)
    current_offset = (
        initial_state[:, temperature_index] - initial_state[:, lower_temperature_index]
    )
    target_temperature = (
        forecast[:, :, lower_temperature_index] + current_offset[jnp.newaxis]
    )
    lead_days = (
        jnp.asarray(lead_steps, dtype=forecast.dtype)
        * jnp.asarray(step_seconds, dtype=forecast.dtype)
        / SECONDS_PER_DAY
    )
    anchor_blend = anchor_weight * (1.0 - jnp.exp(-lead_days / ramp_days))
    anchor_blend = anchor_blend * jnp.exp(-lead_days / decay_days)
    anchored_temperature = forecast[:, :, temperature_index] + anchor_blend[
        :, jnp.newaxis, jnp.newaxis, jnp.newaxis
    ] * (target_temperature - forecast[:, :, temperature_index])
    return forecast.at[:, :, temperature_index].set(anchored_temperature)


def surface_temperature_tendency_correction(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    temperature_index: int,
    decay_days: float,
) -> jax.Array:
    """Return short boundary-layer memory from recent surface-temperature tendency."""
    initial_state = jnp.asarray(initial_state)
    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    tendency = (
        current_state[:, temperature_index] - previous_state[:, temperature_index]
    )
    lead_steps_array = jnp.asarray(lead_steps, dtype=initial_state.dtype)
    lead_days = (
        lead_steps_array
        * jnp.asarray(step_seconds, dtype=initial_state.dtype)
        / SECONDS_PER_DAY
    )
    decay = jnp.where(
        lead_steps_array > 0.0,
        jnp.exp(-lead_days / decay_days),
        0.0,
    )
    return decay[:, jnp.newaxis, jnp.newaxis, jnp.newaxis] * tendency[jnp.newaxis]


def add_surface_temperature_tendency(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    temperature_index: int,
    decay_days: float,
    tendency_weight: float,
) -> jax.Array:
    """Add short-memory recent tendency to the surface-temperature channel."""
    correction = surface_temperature_tendency_correction(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        temperature_index=temperature_index,
        decay_days=decay_days,
    )
    return forecast.at[:, :, temperature_index].set(
        forecast[:, :, temperature_index] + tendency_weight * correction
    )


def add_surface_pressure_tendency(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    pressure_index: int,
    surface_u_indices: tuple[int, ...],
    surface_v_indices: tuple[int, ...],
    surface_weights: tuple[float, ...],
    wind_scale: float,
    max_wind_speed: float,
    decay_days: float,
) -> jax.Array:
    """Add transported pressure tendency to one surface-pressure channel."""
    forecast = jnp.asarray(forecast)
    correction = surface_pressure_tendency_correction(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        pressure_index=pressure_index,
        surface_u_indices=surface_u_indices,
        surface_v_indices=surface_v_indices,
        surface_weights=surface_weights,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
        decay_days=decay_days,
    )
    return forecast.at[:, :, pressure_index].set(
        forecast[:, :, pressure_index] + correction[:, :, pressure_index]
    )


def surface_wind_tendency_correction(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    wind_indices: tuple[int, ...],
    surface_u_indices: tuple[int, ...],
    surface_v_indices: tuple[int, ...],
    surface_weights: tuple[float, ...],
    wind_scale: float,
    max_wind_speed: float,
    decay_days: float,
) -> jax.Array:
    """Return transported short-memory surface-wind tendency corrections."""
    initial_state = jnp.asarray(initial_state)
    assert initial_state.ndim == 4
    assert initial_state.shape[1] >= 2 * current_count

    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    tendency = current_state - previous_state
    u_wind, _ = weighted_wind(
        current_state,
        u_indices=surface_u_indices,
        v_indices=surface_v_indices,
        weights=surface_weights,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    displacement = zonal_cell_displacement(
        u_wind,
        jnp.asarray(step_seconds, dtype=initial_state.dtype),
    )

    def scan_step(state, _):
        shifted = shift_variable_group(
            state,
            variable_indices=wind_indices,
            displacement_cells=displacement,
        )
        return shifted, shifted

    _, trajectory = jax.lax.scan(
        scan_step,
        tendency,
        None,
        length=max(lead_steps),
    )
    trajectory = jnp.concatenate([tendency[jnp.newaxis], trajectory], axis=0)
    correction = jnp.take(
        trajectory,
        jnp.asarray(lead_steps, dtype=jnp.int32),
        axis=0,
    )
    lead_days = (
        jnp.asarray(lead_steps, dtype=initial_state.dtype)
        * jnp.asarray(step_seconds, dtype=initial_state.dtype)
        / SECONDS_PER_DAY
    )
    decay = jnp.exp(-lead_days / decay_days)
    return decay[:, jnp.newaxis, jnp.newaxis, jnp.newaxis, jnp.newaxis] * correction


def add_surface_wind_tendency(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    wind_indices: tuple[int, ...],
    surface_u_indices: tuple[int, ...],
    surface_v_indices: tuple[int, ...],
    surface_weights: tuple[float, ...],
    wind_scale: float,
    max_wind_speed: float,
    decay_days: float,
) -> jax.Array:
    """Add transported short-memory tendency to selected surface winds."""
    forecast = jnp.asarray(forecast)
    correction = surface_wind_tendency_correction(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        wind_indices=wind_indices,
        surface_u_indices=surface_u_indices,
        surface_v_indices=surface_v_indices,
        surface_weights=surface_weights,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
        decay_days=decay_days,
    )
    indices = jnp.asarray(wind_indices, dtype=jnp.int32)
    return forecast.at[:, :, indices].set(
        jnp.take(forecast, indices, axis=2) + jnp.take(correction, indices, axis=2)
    )


def add_upper_steered_pressure_tendency(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    pressure_index: int,
    upper_u_index: int,
    upper_v_index: int,
    wind_scale: float,
    max_wind_speed: float,
    decay_days: float,
) -> jax.Array:
    """Add upper-steered pressure tendency to one surface-pressure channel."""
    forecast = jnp.asarray(forecast)
    correction = upper_pressure_tendency_correction(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        pressure_index=pressure_index,
        upper_u_index=upper_u_index,
        upper_v_index=upper_v_index,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
        decay_days=decay_days,
    )
    return forecast.at[:, :, pressure_index].set(
        forecast[:, :, pressure_index] + correction[:, :, pressure_index]
    )


def add_lower_temperature_tendency(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    lower_temperature_index: int,
    lower_u_index: int,
    lower_v_index: int,
    wind_scale: float,
    max_wind_speed: float,
    decay_days: float,
) -> jax.Array:
    """Add transported short-memory tendency to lower-tropospheric temperature."""
    forecast = jnp.asarray(forecast)
    correction = phase_steered_lower_temperature_tendency_correction(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        lower_temperature_index=lower_temperature_index,
        lower_u_index=lower_u_index,
        lower_v_index=lower_v_index,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
        decay_days=decay_days,
    )
    return forecast.at[:, :, lower_temperature_index].set(
        forecast[:, :, lower_temperature_index] + correction
    )


def phase_steered_lower_temperature_tendency_correction(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    lower_temperature_index: int,
    lower_u_index: int,
    lower_v_index: int,
    wind_scale: float,
    max_wind_speed: float,
    decay_days: float,
) -> jax.Array:
    """Return lower-air tendency shifted by observed lower-temperature phase."""
    initial_state = jnp.asarray(initial_state)
    assert initial_state.ndim == 4
    assert initial_state.shape[1] >= 2 * current_count

    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    tendency = current_state - previous_state
    lower_u_wind, _ = weighted_wind(
        current_state,
        u_indices=(lower_u_index,),
        v_indices=(lower_v_index,),
        weights=(1.0,),
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    wind_displacement = zonal_cell_displacement(
        lower_u_wind,
        jnp.asarray(step_seconds, dtype=initial_state.dtype),
    )
    phase_displacement = zonal_phase_displacement(
        current_state[:, lower_temperature_index],
        previous_state[:, lower_temperature_index],
        wind_displacement,
    )

    def scan_step(state, _):
        shifted = shift_variable_group(
            state,
            variable_indices=(lower_temperature_index,),
            displacement_cells=phase_displacement,
        )
        return shifted, shifted

    _, trajectory = jax.lax.scan(
        scan_step,
        tendency,
        None,
        length=max(lead_steps),
    )
    trajectory = jnp.concatenate([tendency[jnp.newaxis], trajectory], axis=0)
    correction = jnp.take(
        trajectory,
        jnp.asarray(lead_steps, dtype=jnp.int32),
        axis=0,
    )[:, :, lower_temperature_index]
    lead_days = (
        jnp.asarray(lead_steps, dtype=initial_state.dtype)
        * jnp.asarray(step_seconds, dtype=initial_state.dtype)
        / SECONDS_PER_DAY
    )
    decay = jnp.exp(-lead_days / decay_days)
    return decay[:, jnp.newaxis, jnp.newaxis, jnp.newaxis] * correction


def partially_restore_initialized_anomaly_rms(
    forecast: jax.Array,
    initial_state: jax.Array,
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
) -> jax.Array:
    """Partially restore initialized zonal-anomaly RMS for selected channels."""
    forecast = jnp.asarray(forecast)
    initial_state = jnp.asarray(initial_state, dtype=forecast.dtype)
    assert forecast.ndim == 5
    assert initial_state.ndim == 4
    assert initial_state.shape[1] >= current_count
    assert forecast.shape[1:] == initial_state.shape

    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    forecast_values = jnp.take(forecast, indices, axis=2)
    forecast_zonal_mean = jnp.mean(forecast_values, axis=-2, keepdims=True)
    forecast_anomalies = forecast_values - forecast_zonal_mean
    current_values = jnp.take(initial_state[:, :current_count], indices, axis=1)
    current_zonal_mean = jnp.mean(current_values, axis=-2, keepdims=True)
    current_anomalies = current_values - current_zonal_mean
    current_rms = jnp.sqrt(
        jnp.mean(current_anomalies * current_anomalies, axis=(-2, -1))
    )
    forecast_rms = jnp.sqrt(
        jnp.mean(forecast_anomalies * forecast_anomalies, axis=(-2, -1)),
    )
    rms_ratio = current_rms[jnp.newaxis] / jnp.maximum(forecast_rms, 1.0e-6)
    anomaly_scale = jnp.sqrt(jnp.maximum(1.0, rms_ratio))
    restored = (
        forecast_zonal_mean
        + anomaly_scale[:, :, :, jnp.newaxis, jnp.newaxis] * forecast_anomalies
    )
    return forecast.at[:, :, indices].set(restored)


def restore_initialized_anomaly_rms(
    forecast: jax.Array,
    initial_state: jax.Array,
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
) -> jax.Array:
    """Restore initialized zonal-anomaly RMS for selected channels."""
    forecast = jnp.asarray(forecast)
    initial_state = jnp.asarray(initial_state, dtype=forecast.dtype)
    assert forecast.ndim == 5
    assert initial_state.ndim == 4
    assert initial_state.shape[1] >= current_count
    assert forecast.shape[1:] == initial_state.shape

    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    forecast_values = jnp.take(forecast, indices, axis=2)
    forecast_zonal_mean = jnp.mean(forecast_values, axis=-2, keepdims=True)
    forecast_anomalies = forecast_values - forecast_zonal_mean
    current_values = jnp.take(initial_state[:, :current_count], indices, axis=1)
    current_zonal_mean = jnp.mean(current_values, axis=-2, keepdims=True)
    current_anomalies = current_values - current_zonal_mean
    current_rms = jnp.sqrt(
        jnp.mean(current_anomalies * current_anomalies, axis=(-2, -1))
    )
    forecast_rms = jnp.sqrt(
        jnp.mean(forecast_anomalies * forecast_anomalies, axis=(-2, -1)),
    )
    rms_ratio = current_rms[jnp.newaxis] / jnp.maximum(forecast_rms, 1.0e-6)
    anomaly_scale = jnp.maximum(1.0, rms_ratio)
    restored = (
        forecast_zonal_mean
        + anomaly_scale[:, :, :, jnp.newaxis, jnp.newaxis] * forecast_anomalies
    )
    return forecast.at[:, :, indices].set(restored)


def apply_history_eddy_growth_memory(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
    growth_weight: float,
    memory_decay_days: float,
    max_scale: float,
    max_log_growth_per_step: float,
) -> jax.Array:
    """Scale selected zonal eddies by bounded recent anomaly-growth memory."""
    if not variable_indices or growth_weight <= 0.0:
        return forecast

    forecast = jnp.asarray(forecast)
    initial_state = jnp.asarray(initial_state, dtype=forecast.dtype)
    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    current_values = jnp.take(current_state, indices, axis=1)
    previous_values = jnp.take(previous_state, indices, axis=1)
    current_eddy = current_values - jnp.mean(
        current_values,
        axis=-2,
        keepdims=True,
    )
    previous_eddy = previous_values - jnp.mean(
        previous_values,
        axis=-2,
        keepdims=True,
    )
    current_rms = jnp.sqrt(jnp.mean(current_eddy * current_eddy, axis=(-2, -1)))
    previous_rms = jnp.sqrt(jnp.mean(previous_eddy * previous_eddy, axis=(-2, -1)))
    log_growth = jnp.log(
        jnp.maximum(current_rms, 1.0e-6) / jnp.maximum(previous_rms, 1.0e-6)
    )
    log_growth = jnp.clip(
        log_growth,
        -max_log_growth_per_step,
        max_log_growth_per_step,
    )
    lead_steps_array = jnp.asarray(lead_steps, dtype=forecast.dtype)
    step_decay = jnp.exp(
        -jnp.asarray(step_seconds, dtype=forecast.dtype)
        / (memory_decay_days * SECONDS_PER_DAY),
    )
    memory_steps = (1.0 - step_decay**lead_steps_array) / jnp.maximum(
        1.0 - step_decay,
        1.0e-6,
    )
    scale = jnp.exp(
        growth_weight * memory_steps[:, jnp.newaxis, jnp.newaxis] * log_growth
    )
    scale = jnp.clip(scale, 1.0 / max_scale, max_scale)
    forecast_values = jnp.take(forecast, indices, axis=2)
    forecast_mean = jnp.mean(forecast_values, axis=-2, keepdims=True)
    forecast_eddy = forecast_values - forecast_mean
    updated = forecast_mean + scale[:, :, :, jnp.newaxis, jnp.newaxis] * forecast_eddy
    return forecast.at[:, :, indices].set(updated)


def scale_selective_filter(
    values: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    longitude_reference_wave_number: float,
    longitude_damping_power: float,
    longitude_latitude_aware: bool,
    latitude_reference_wave_number: float,
    latitude_damping_power: float,
    cross_reference_wave_number: float,
    cross_latitude_aware: bool,
) -> jax.Array:
    """Apply the model's horizontal scale-selective filter sequence."""
    filtered = scale_selective_longitude_filter(
        values,
        lead_steps,
        step_seconds,
        reference_wave_number=longitude_reference_wave_number,
        damping_power=longitude_damping_power,
        latitude_aware=longitude_latitude_aware,
    )
    filtered = scale_selective_latitude_filter(
        filtered,
        lead_steps,
        step_seconds,
        reference_wave_number=latitude_reference_wave_number,
        damping_power=latitude_damping_power,
    )
    return scale_selective_horizontal_cross_filter(
        filtered,
        lead_steps,
        step_seconds,
        reference_wave_number=cross_reference_wave_number,
        latitude_aware=cross_latitude_aware,
    )


def one_day_scale_selective_filter(
    values: jax.Array,
    *,
    reference_wave_number: float,
    damping_power: float,
) -> jax.Array:
    """Return a fixed one-day low-pass split independent of forecast lead."""
    values = jnp.asarray(values)
    lead_steps = tuple(1 for _ in range(values.shape[0]))
    return scale_selective_filter(
        values,
        lead_steps,
        SECONDS_PER_DAY,
        longitude_reference_wave_number=reference_wave_number,
        longitude_damping_power=damping_power,
        longitude_latitude_aware=True,
        latitude_reference_wave_number=reference_wave_number,
        latitude_damping_power=damping_power,
        cross_reference_wave_number=reference_wave_number,
        cross_latitude_aware=True,
    )


def phase_blended_zonal_displacement(
    current_state: jax.Array,
    previous_state: jax.Array,
    wind_displacement: jax.Array,
    *,
    phase_reference_index: int | None,
    phase_blend: float,
    phase_bound: float,
) -> jax.Array:
    """Blend steering-wind displacement with recent observed zonal phase motion."""
    if phase_reference_index is None or phase_blend <= 0.0:
        return wind_displacement

    phase_displacement = zonal_phase_displacement(
        current_state[:, phase_reference_index],
        previous_state[:, phase_reference_index],
        wind_displacement * phase_bound,
    )
    return (1.0 - phase_blend) * wind_displacement + phase_blend * phase_displacement


def scale_split_residual_correction(
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
    reference_wave_number: float,
    damping_power: float,
    decay_days: float,
    residual_weight: float,
    surface_phase_reference_index: int | None = None,
    lower_phase_reference_index: int | None = None,
    upper_phase_reference_index: int | None = None,
    phase_blend: float = 0.0,
    phase_bound: float = 1.0,
) -> jax.Array:
    """Return phase-preserved weather-scale residuals from the initial state."""
    initial_state = jnp.asarray(initial_state)
    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    current_low_pass = one_day_scale_selective_filter(
        current_state[jnp.newaxis],
        reference_wave_number=reference_wave_number,
        damping_power=damping_power,
    )[0]
    current_residual = current_state - current_low_pass
    step_seconds_array = jnp.asarray(step_seconds, dtype=initial_state.dtype)

    surface_u_wind, _ = weighted_wind(
        current_state,
        u_indices=surface_u_indices,
        v_indices=surface_v_indices,
        weights=surface_weights,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    lower_u_wind, _ = weighted_wind(
        current_state,
        u_indices=(lower_u_index,),
        v_indices=(lower_v_index,),
        weights=(1.0,),
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    upper_u_wind, _ = weighted_wind(
        current_state,
        u_indices=(upper_u_index,),
        v_indices=(upper_v_index,),
        weights=(1.0,),
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    surface_displacement = zonal_cell_displacement(surface_u_wind, step_seconds_array)
    lower_displacement = zonal_cell_displacement(lower_u_wind, step_seconds_array)
    upper_displacement = zonal_cell_displacement(upper_u_wind, step_seconds_array)
    surface_displacement = phase_blended_zonal_displacement(
        current_state,
        previous_state,
        surface_displacement,
        phase_reference_index=surface_phase_reference_index,
        phase_blend=phase_blend,
        phase_bound=phase_bound,
    )
    lower_displacement = phase_blended_zonal_displacement(
        current_state,
        previous_state,
        lower_displacement,
        phase_reference_index=lower_phase_reference_index,
        phase_blend=phase_blend,
        phase_bound=phase_bound,
    )
    upper_displacement = phase_blended_zonal_displacement(
        current_state,
        previous_state,
        upper_displacement,
        phase_reference_index=upper_phase_reference_index,
        phase_blend=phase_blend,
        phase_bound=phase_bound,
    )

    def forecast_one_lead(lead_step):
        lead_step = lead_step.astype(initial_state.dtype)
        shifted = shift_variable_group(
            current_residual,
            variable_indices=surface_indices,
            displacement_cells=surface_displacement * lead_step,
        )
        shifted = shift_variable_group(
            shifted,
            variable_indices=lower_indices,
            displacement_cells=lower_displacement * lead_step,
        )
        shifted = shift_variable_group(
            shifted,
            variable_indices=upper_indices,
            displacement_cells=upper_displacement * lead_step,
        )
        return shifted

    shifted_residual = jax.vmap(forecast_one_lead)(
        jnp.asarray(lead_steps, dtype=jnp.int32)
    )
    lead_days = (
        jnp.asarray(lead_steps, dtype=initial_state.dtype)
        * jnp.asarray(step_seconds, dtype=initial_state.dtype)
        / SECONDS_PER_DAY
    )
    decay = jnp.exp(-lead_days / decay_days)
    return (
        residual_weight
        * decay[:, jnp.newaxis, jnp.newaxis, jnp.newaxis, jnp.newaxis]
        * shifted_residual
    )


def add_scale_split_residual(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
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
    reference_wave_number: float,
    damping_power: float,
    decay_days: float,
    residual_weight: float,
    surface_phase_reference_index: int | None = None,
    lower_phase_reference_index: int | None = None,
    upper_phase_reference_index: int | None = None,
    phase_blend: float = 0.0,
    phase_bound: float = 1.0,
) -> jax.Array:
    """Replace selected channels with low-pass forecast plus advected residual."""
    forecast = jnp.asarray(forecast)
    forecast_low_pass = one_day_scale_selective_filter(
        forecast,
        reference_wave_number=reference_wave_number,
        damping_power=damping_power,
    )
    residual = scale_split_residual_correction(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
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
        reference_wave_number=reference_wave_number,
        damping_power=damping_power,
        decay_days=decay_days,
        residual_weight=residual_weight,
        surface_phase_reference_index=surface_phase_reference_index,
        lower_phase_reference_index=lower_phase_reference_index,
        upper_phase_reference_index=upper_phase_reference_index,
        phase_blend=phase_blend,
        phase_bound=phase_bound,
    )
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    selected = jnp.take(forecast_low_pass, indices, axis=2) + jnp.take(
        residual, indices, axis=2
    )
    return forecast.at[:, :, indices].set(selected)


def cumulative_decayed_displacement(
    lead_steps: tuple[int, ...],
    dtype,
    *,
    displacement_decay_steps: float,
) -> jax.Array:
    """Return integrated step counts for exponentially fading feature motion."""
    lead_array = jnp.asarray(lead_steps, dtype=dtype)
    step_decay = jnp.exp(-1.0 / displacement_decay_steps)
    return (1.0 - step_decay**lead_array) / (1.0 - step_decay)


def optical_flow_residual_correction(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    flow_channel_indices: tuple[int, ...],
    regularization: float,
    smoothing_passes: int,
    max_displacement_cells: float,
    flow_scale: float,
    displacement_decay_steps: float,
    reference_wave_number: float,
    damping_power: float,
    decay_days: float,
    residual_weight: float,
) -> jax.Array:
    """Return weather-scale residuals transported by recent 2-D feature motion."""
    initial_state = jnp.asarray(initial_state)
    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    current_low_pass = one_day_scale_selective_filter(
        current_state[jnp.newaxis],
        reference_wave_number=reference_wave_number,
        damping_power=damping_power,
    )[0]
    current_residual = current_state - current_low_pass
    displacement_x, displacement_y = estimate_optical_flow_cells(
        current_state,
        previous_state,
        channel_indices=flow_channel_indices,
        regularization=regularization,
        smoothing_passes=smoothing_passes,
        max_displacement_cells=max_displacement_cells,
        flow_scale=flow_scale,
    )
    cumulative_displacement = cumulative_decayed_displacement(
        lead_steps,
        initial_state.dtype,
        displacement_decay_steps=displacement_decay_steps,
    )

    def forecast_one_lead(displacement_scale):
        return advect_with_cell_displacement(
            current_residual,
            displacement_x * displacement_scale,
            displacement_y * displacement_scale,
        )

    shifted_residual = jax.vmap(forecast_one_lead)(cumulative_displacement)
    lead_days = (
        jnp.asarray(lead_steps, dtype=initial_state.dtype)
        * jnp.asarray(step_seconds, dtype=initial_state.dtype)
        / SECONDS_PER_DAY
    )
    decay = jnp.exp(-lead_days / decay_days)
    return (
        residual_weight
        * decay[:, jnp.newaxis, jnp.newaxis, jnp.newaxis, jnp.newaxis]
        * shifted_residual
    )


def spectral_phase_residual_correction(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    reference_wave_number: float,
    damping_power: float,
    decay_days: float,
    residual_weight: float,
) -> jax.Array:
    """Return weather-scale residuals propagated by recent zonal wave phase."""
    initial_state = jnp.asarray(initial_state)
    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    current_low_pass = one_day_scale_selective_filter(
        current_state[jnp.newaxis],
        reference_wave_number=reference_wave_number,
        damping_power=damping_power,
    )[0]
    previous_low_pass = one_day_scale_selective_filter(
        previous_state[jnp.newaxis],
        reference_wave_number=reference_wave_number,
        damping_power=damping_power,
    )[0]
    current_residual = current_state - current_low_pass
    previous_residual = previous_state - previous_low_pass
    current_coefficients = jnp.fft.rfft(current_residual, axis=-2)
    previous_coefficients = jnp.fft.rfft(previous_residual, axis=-2)
    cross_spectrum = current_coefficients * jnp.conj(previous_coefficients)
    raw_phase = cross_spectrum / jnp.maximum(jnp.abs(cross_spectrum), 1.0e-6)
    coherent_phase = (jnp.abs(current_coefficients) > 1.0e-4) & (
        jnp.abs(previous_coefficients) > 1.0e-4
    )
    phase_step = jnp.where(coherent_phase, raw_phase, 1.0 + 0.0j)
    phase_step = phase_step.at[:, :, 0].set(1.0 + 0.0j)
    lead_array = jnp.asarray(lead_steps, dtype=initial_state.dtype)

    def forecast_one_lead(lead_step):
        propagated = current_coefficients * phase_step**lead_step
        return jnp.fft.irfft(
            propagated,
            n=current_state.shape[-2],
            axis=-2,
        ).astype(initial_state.dtype)

    shifted_residual = jax.vmap(forecast_one_lead)(lead_array)
    lead_days = lead_array * jnp.asarray(step_seconds, dtype=initial_state.dtype)
    lead_days = lead_days / SECONDS_PER_DAY
    decay = jnp.exp(-lead_days / decay_days)
    return (
        residual_weight
        * decay[:, jnp.newaxis, jnp.newaxis, jnp.newaxis, jnp.newaxis]
        * shifted_residual
    )


def zonal_phase_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
) -> jax.Array:
    """Return selected fields propagated by recent zonal wave phase speed."""
    initial_state = jnp.asarray(initial_state)
    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    current_values = jnp.take(current_state, indices, axis=1)
    previous_values = jnp.take(previous_state, indices, axis=1)
    current_zonal_mean = jnp.mean(current_values, axis=-2, keepdims=True)
    previous_zonal_mean = jnp.mean(previous_values, axis=-2, keepdims=True)
    current_anomaly = current_values - current_zonal_mean
    previous_anomaly = previous_values - previous_zonal_mean
    current_coefficients = jnp.fft.rfft(current_anomaly, axis=-2)
    previous_coefficients = jnp.fft.rfft(previous_anomaly, axis=-2)
    cross_spectrum = current_coefficients * jnp.conj(previous_coefficients)
    raw_phase = cross_spectrum / jnp.maximum(jnp.abs(cross_spectrum), 1.0e-6)
    coherent_phase = (jnp.abs(current_coefficients) > 1.0e-4) & (
        jnp.abs(previous_coefficients) > 1.0e-4
    )
    phase_step = jnp.where(coherent_phase, raw_phase, 1.0 + 0.0j)
    phase_step = phase_step.at[:, :, 0].set(1.0 + 0.0j)
    lead_array = jnp.asarray(lead_steps, dtype=initial_state.dtype)

    def forecast_one_lead(lead_step):
        propagated = current_coefficients * phase_step**lead_step
        anomaly = jnp.fft.irfft(
            propagated,
            n=current_state.shape[-2],
            axis=-2,
        )
        return current_zonal_mean + anomaly.astype(initial_state.dtype)

    return jax.vmap(forecast_one_lead)(lead_array)


def add_zonal_phase_forecast(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
    phase_weight: float,
) -> jax.Array:
    """Blend selected channels with full-field recent zonal phase propagation."""
    if not variable_indices or phase_weight <= 0.0:
        return forecast

    phase_forecast = zonal_phase_forecast(
        initial_state,
        lead_steps,
        current_count=current_count,
        variable_indices=variable_indices,
    )
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    blended = (1.0 - phase_weight) * jnp.take(forecast, indices, axis=2)
    blended = blended + phase_weight * phase_forecast
    return forecast.at[:, :, indices].set(blended)


def reflect_phase_latitude(values: jax.Array) -> jax.Array:
    """Return a pole-reflected latitude axis for 2-D spectral phase operations."""
    values = jnp.asarray(values)
    return jnp.concatenate([values, values[..., 1:-1][..., ::-1]], axis=-1)


def phase_nudged_values(
    forecast_values: jax.Array,
    target_values: jax.Array,
    *,
    phase_weight: float,
) -> jax.Array:
    """Rotate forecast spectral phase toward a target while retaining amplitudes."""
    forecast_values = jnp.asarray(forecast_values)
    target_values = jnp.asarray(target_values, dtype=forecast_values.dtype)
    forecast_mean = jnp.mean(forecast_values, axis=(-2, -1), keepdims=True)
    target_mean = jnp.mean(target_values, axis=(-2, -1), keepdims=True)
    forecast_coefficients = jnp.fft.fftn(
        reflect_phase_latitude(forecast_values - forecast_mean),
        axes=(-2, -1),
    )
    target_coefficients = jnp.fft.fftn(
        reflect_phase_latitude(target_values - target_mean),
        axes=(-2, -1),
    )
    cross_spectrum = target_coefficients * jnp.conj(forecast_coefficients)
    phase_delta = cross_spectrum / jnp.maximum(jnp.abs(cross_spectrum), 1.0e-6)
    coherent = (jnp.abs(forecast_coefficients) > 1.0e-4) & (
        jnp.abs(target_coefficients) > 1.0e-4
    )
    phase_delta = jnp.where(coherent, phase_delta, 1.0 + 0.0j)
    phase_delta = phase_delta.at[:, :, :, 0, 0].set(1.0 + 0.0j)
    nudged_coefficients = forecast_coefficients * phase_delta**phase_weight
    reflected = jnp.fft.ifftn(nudged_coefficients, axes=(-2, -1)).real
    return forecast_mean + reflected[..., : forecast_values.shape[-1]].astype(
        forecast_values.dtype,
    )


def add_zonal_phase_nudge(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
    phase_weight: float,
    decay_days: float,
) -> jax.Array:
    """Nudge selected channels toward recent zonal phase without damping amplitude."""
    if not variable_indices or phase_weight <= 0.0:
        return forecast

    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    phase_target = zonal_phase_forecast(
        initial_state,
        lead_steps,
        current_count=current_count,
        variable_indices=variable_indices,
    )
    lead_days = (
        jnp.asarray(lead_steps, dtype=forecast.dtype)
        * jnp.asarray(step_seconds, dtype=forecast.dtype)
        / SECONDS_PER_DAY
    )
    lead_weights = phase_weight * jnp.exp(-lead_days / decay_days)

    def nudge_one_lead(forecast_values, target_values, lead_weight):
        return phase_nudged_values(
            forecast_values[jnp.newaxis],
            target_values[jnp.newaxis],
            phase_weight=lead_weight,
        )[0]

    nudged = jax.vmap(nudge_one_lead)(
        jnp.take(forecast, indices, axis=2),
        phase_target,
        lead_weights,
    )
    return forecast.at[:, :, indices].set(nudged)


def two_dimensional_phase_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
    max_zonal_wave_number: float,
    max_meridional_wave_number: float,
) -> jax.Array:
    """Return selected fields propagated by coherent 2-D spectral phase motion."""
    initial_state = jnp.asarray(initial_state)
    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    current_values = jnp.take(current_state, indices, axis=1)
    previous_values = jnp.take(previous_state, indices, axis=1)
    current_mean = jnp.mean(current_values, axis=(-2, -1), keepdims=True)
    previous_mean = jnp.mean(previous_values, axis=(-2, -1), keepdims=True)
    current_anomaly = current_values - current_mean
    previous_anomaly = previous_values - previous_mean
    current_coefficients = jnp.fft.fftn(
        reflect_phase_latitude(current_anomaly),
        axes=(-2, -1),
    )
    previous_coefficients = jnp.fft.fftn(
        reflect_phase_latitude(previous_anomaly),
        axes=(-2, -1),
    )
    cross_spectrum = current_coefficients * jnp.conj(previous_coefficients)
    phase_step = cross_spectrum / jnp.maximum(jnp.abs(cross_spectrum), 1.0e-6)
    longitude_count = current_coefficients.shape[-2]
    reflected_latitude_count = current_coefficients.shape[-1]
    zonal_wave_numbers = jnp.abs(jnp.fft.fftfreq(longitude_count) * longitude_count)
    meridional_wave_numbers = jnp.abs(
        jnp.fft.fftfreq(reflected_latitude_count) * reflected_latitude_count,
    )
    wave_mask = (zonal_wave_numbers[:, jnp.newaxis] <= max_zonal_wave_number) & (
        meridional_wave_numbers[jnp.newaxis, :] <= max_meridional_wave_number
    )
    wave_mask = wave_mask.at[0, 0].set(False)
    coherent = (jnp.abs(current_coefficients) > 1.0e-4) & (
        jnp.abs(previous_coefficients) > 1.0e-4
    )
    phase_step = jnp.where(
        wave_mask[jnp.newaxis, jnp.newaxis] & coherent,
        phase_step,
        1.0 + 0.0j,
    )
    lead_steps_array = jnp.asarray(lead_steps, dtype=initial_state.dtype)

    def forecast_one_lead(lead_step):
        propagated = current_coefficients * phase_step**lead_step
        reflected = jnp.fft.ifftn(propagated, axes=(-2, -1)).real
        return current_mean + reflected[..., : current_values.shape[-1]].astype(
            initial_state.dtype,
        )

    return jax.vmap(forecast_one_lead)(lead_steps_array)


def add_two_dimensional_phase_nudge(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
    phase_weight: float,
    decay_days: float,
    max_zonal_wave_number: float,
    max_meridional_wave_number: float,
) -> jax.Array:
    """Nudge selected channels toward recent 2-D phase motion."""
    if not variable_indices or phase_weight <= 0.0:
        return forecast

    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    phase_target = two_dimensional_phase_forecast(
        initial_state,
        lead_steps,
        current_count=current_count,
        variable_indices=variable_indices,
        max_zonal_wave_number=max_zonal_wave_number,
        max_meridional_wave_number=max_meridional_wave_number,
    )
    lead_days = (
        jnp.asarray(lead_steps, dtype=forecast.dtype)
        * jnp.asarray(step_seconds, dtype=forecast.dtype)
        / SECONDS_PER_DAY
    )
    lead_weights = phase_weight * jnp.exp(-lead_days / decay_days)

    def nudge_one_lead(forecast_values, target_values, lead_weight):
        return phase_nudged_values(
            forecast_values[jnp.newaxis],
            target_values[jnp.newaxis],
            phase_weight=lead_weight,
        )[0]

    nudged = jax.vmap(nudge_one_lead)(
        jnp.take(forecast, indices, axis=2),
        phase_target,
        lead_weights,
    )
    return forecast.at[:, :, indices].set(nudged)


def coriolis_parameter(latitude_count: int, dtype) -> jax.Array:
    """Return latitude-dependent Coriolis parameter."""
    latitudes = latitude_radians(latitude_count, dtype)
    return 2.0 * EARTH_ANGULAR_VELOCITY * jnp.sin(latitudes)


def upper_absolute_vorticity_geopotential_increment(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    upper_u_index: int,
    upper_v_index: int,
    wind_scale: float,
    max_wind_speed: float,
    coriolis_scale: float,
    reference_latitude_radians: float,
) -> jax.Array:
    """Return Z500 increments from advected upper absolute vorticity."""
    initial_state = jnp.asarray(initial_state)
    current_state = initial_state[:, :current_count]
    u_wind = wind_scale * current_state[:, upper_u_index]
    v_wind = wind_scale * current_state[:, upper_v_index]
    speed = jnp.sqrt(u_wind * u_wind + v_wind * v_wind)
    speed_scale = jnp.minimum(1.0, max_wind_speed / jnp.maximum(speed, 1.0e-6))
    u_wind = u_wind * speed_scale
    v_wind = v_wind * speed_scale

    coriolis = coriolis_parameter(current_state.shape[-1], current_state.dtype)
    absolute_vorticity = (
        longitude_gradient(v_wind)
        - latitude_gradient(u_wind)
        + coriolis[jnp.newaxis, jnp.newaxis, :]
    )
    step_seconds_array = jnp.asarray(step_seconds, dtype=initial_state.dtype)

    def scan_step(vorticity, _):
        advected = semi_lagrangian_advect_corrected(
            vorticity[:, jnp.newaxis],
            u_wind,
            v_wind,
            step_seconds_array,
        )[:, 0]
        return advected, advected

    _, trajectory = jax.lax.scan(
        scan_step,
        absolute_vorticity,
        None,
        length=max(lead_steps),
    )
    trajectory = jnp.concatenate([absolute_vorticity[jnp.newaxis], trajectory], axis=0)
    selected_vorticity = jnp.take(
        trajectory,
        jnp.asarray(lead_steps, dtype=jnp.int32),
        axis=0,
    )
    vorticity_change = selected_vorticity - absolute_vorticity[jnp.newaxis]

    def invert_one_lead(vorticity):
        return invert_vorticity_to_geopotential(
            vorticity,
            coriolis_scale=coriolis_scale,
            reference_latitude_radians=reference_latitude_radians,
        )

    return jax.vmap(invert_one_lead)(vorticity_change)


def invert_vorticity_to_geopotential(
    vorticity: jax.Array,
    *,
    coriolis_scale: float,
    reference_latitude_radians: float,
) -> jax.Array:
    """Invert a barotropic vorticity tendency into a geopotential anomaly."""
    vorticity = jnp.asarray(vorticity)
    longitude_count, latitude_count = vorticity.shape[-2:]
    reflected = reflect_phase_latitude(vorticity)
    reflected_latitude_count = reflected.shape[-1]
    dx = (
        EARTH_RADIUS
        * jnp.cos(jnp.asarray(reference_latitude_radians, dtype=vorticity.dtype))
        * 2.0
        * jnp.pi
        / longitude_count
    )
    dy = EARTH_RADIUS * jnp.pi / (latitude_count - 1)
    zonal_waves = 2.0 * jnp.pi * jnp.fft.fftfreq(longitude_count, d=dx)
    meridional_waves = (
        2.0
        * jnp.pi
        * jnp.fft.fftfreq(
            reflected_latitude_count,
            d=dy,
        )
    )
    laplacian_eigenvalue = -(
        zonal_waves[:, jnp.newaxis] * zonal_waves[:, jnp.newaxis]
        + meridional_waves[jnp.newaxis, :] * meridional_waves[jnp.newaxis, :]
    )
    source_coefficients = jnp.fft.fftn(
        coriolis_scale * reflected,
        axes=(-2, -1),
    )
    solution_coefficients = jnp.where(
        laplacian_eigenvalue[jnp.newaxis] == 0.0,
        0.0 + 0.0j,
        source_coefficients / laplacian_eigenvalue[jnp.newaxis],
    )
    reflected_geopotential = jnp.fft.ifftn(
        solution_coefficients,
        axes=(-2, -1),
    ).real
    geopotential = reflected_geopotential[..., :latitude_count]
    return geopotential - jnp.mean(geopotential, axis=-2, keepdims=True)


def cap_increment_to_current_eddy_rms(
    increment: jax.Array,
    current_values: jax.Array,
    *,
    max_fraction: float,
) -> jax.Array:
    """Bound a geopotential increment by initialized zonal-eddy RMS."""
    increment = jnp.asarray(increment)
    current_values = jnp.asarray(current_values, dtype=increment.dtype)
    increment_eddy = increment - jnp.mean(increment, axis=-2, keepdims=True)
    current_eddy = current_values - jnp.mean(current_values, axis=-2, keepdims=True)
    increment_rms = jnp.sqrt(jnp.mean(increment_eddy * increment_eddy, axis=(-2, -1)))
    current_rms = jnp.sqrt(jnp.mean(current_eddy * current_eddy, axis=(-2, -1)))
    increment_scale = (
        max_fraction
        * current_rms[jnp.newaxis]
        / jnp.maximum(
            increment_rms,
            1.0e-6,
        )
    )
    increment_scale = jnp.minimum(1.0, increment_scale)
    return increment_scale[:, :, jnp.newaxis, jnp.newaxis] * increment


def add_upper_vorticity_phase_nudge(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    geopotential_index: int,
    upper_u_index: int,
    upper_v_index: int,
    wind_scale: float,
    max_wind_speed: float,
    coriolis_scale: float,
    reference_latitude_radians: float,
    max_increment_fraction: float,
    phase_weight: float,
    decay_days: float,
) -> jax.Array:
    """Nudge Z500 phase toward an upper absolute-vorticity forecast target."""
    if phase_weight <= 0.0 or max_increment_fraction <= 0.0:
        return forecast

    forecast = jnp.asarray(forecast)
    initial_state = jnp.asarray(initial_state, dtype=forecast.dtype)
    current_geopotential = initial_state[:, geopotential_index]
    increment = upper_absolute_vorticity_geopotential_increment(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        upper_u_index=upper_u_index,
        upper_v_index=upper_v_index,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
        coriolis_scale=coriolis_scale,
        reference_latitude_radians=reference_latitude_radians,
    )
    increment = cap_increment_to_current_eddy_rms(
        increment,
        current_geopotential,
        max_fraction=max_increment_fraction,
    )
    lead_days = (
        jnp.asarray(lead_steps, dtype=forecast.dtype)
        * jnp.asarray(step_seconds, dtype=forecast.dtype)
        / SECONDS_PER_DAY
    )
    decay = jnp.exp(-lead_days / decay_days)
    target = current_geopotential[jnp.newaxis] + (
        decay[:, jnp.newaxis, jnp.newaxis, jnp.newaxis] * increment
    )
    lead_weights = phase_weight * decay

    def nudge_one_lead(forecast_values, target_values, lead_weight):
        return phase_nudged_values(
            forecast_values[jnp.newaxis],
            target_values[jnp.newaxis],
            phase_weight=lead_weight,
        )[0]

    nudged = jax.vmap(nudge_one_lead)(
        forecast[:, :, geopotential_index : geopotential_index + 1],
        target[:, :, jnp.newaxis],
        lead_weights,
    )[:, :, 0]
    return forecast.at[:, :, geopotential_index].set(nudged)


def add_barotropic_vorticity_phase_nudge(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    geopotential_index: int,
    pressure_index: int,
    surface_temperature_index: int,
    surface_u_index: int,
    lower_temperature_index: int,
    flow_scale: float,
    max_wind_speed: float,
    vorticity_decay_days: float,
    target_anomaly_weight: float,
    coriolis_scale: float,
    reference_latitude_radians: float,
    phase_weight: float,
    amplitude_weight: float,
    pressure_response_weight: float,
    wind_response_weight: float,
    wind_response_hours: float,
    wind_response_max_increment: float,
    wind_response_ramp_days: float,
    wind_response_decay_days: float,
    ramp_days: float,
    decay_days: float,
) -> jax.Array:
    """Nudge Z500 phase toward a barotropic-vorticity evolution target."""
    if target_anomaly_weight <= 0.0 or (
        phase_weight <= 0.0
        and amplitude_weight <= 0.0
        and pressure_response_weight <= 0.0
        and wind_response_weight <= 0.0
    ):
        return forecast

    forecast = jnp.asarray(forecast)
    target_forecast = barotropic_vorticity_forecast(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        geopotential_index=geopotential_index,
        flow_scale=flow_scale,
        max_wind_speed=max_wind_speed,
        vorticity_decay_days=vorticity_decay_days,
        anomaly_weight=target_anomaly_weight,
        coriolis_scale=coriolis_scale,
        reference_latitude_radians=reference_latitude_radians,
    )
    target = target_forecast[:, :, geopotential_index]
    lead_days = (
        jnp.asarray(lead_steps, dtype=forecast.dtype)
        * jnp.asarray(step_seconds, dtype=forecast.dtype)
        / SECONDS_PER_DAY
    )
    ramp = 1.0 - jnp.exp(-lead_days / ramp_days)
    lead_decay = ramp * jnp.exp(-lead_days / decay_days)
    lead_weights = phase_weight * lead_decay

    def nudge_one_lead(forecast_values, target_values, lead_weight):
        return phase_nudged_values(
            forecast_values[jnp.newaxis],
            target_values[jnp.newaxis],
            phase_weight=lead_weight,
        )[0]

    nudged = jax.vmap(nudge_one_lead)(
        forecast[:, :, geopotential_index : geopotential_index + 1],
        target[:, :, jnp.newaxis],
        lead_weights,
    )[:, :, 0]
    if amplitude_weight > 0.0:
        blend = amplitude_weight * lead_decay
        nudged = nudged + blend[:, jnp.newaxis, jnp.newaxis, jnp.newaxis] * (
            target - nudged
        )
    forecast = forecast.at[:, :, geopotential_index].set(nudged)

    current_pressure = initial_state[:, pressure_index]
    current_temperature = jnp.maximum(
        initial_state[:, lower_temperature_index],
        MIN_HYDROSTATIC_TEMPERATURE,
    )
    current_height = initial_state[:, geopotential_index]
    height_increment = target - current_height[jnp.newaxis]
    pressure_sensitivity = current_pressure / (
        DRY_AIR_GAS_CONSTANT * current_temperature
    )
    target_pressure = current_pressure[jnp.newaxis] + (
        pressure_sensitivity[jnp.newaxis] * height_increment
    )
    if pressure_response_weight > 0.0:
        pressure_blend = pressure_response_weight * lead_decay
        forecast_pressure = forecast[:, :, pressure_index]
        updated_pressure = forecast_pressure + pressure_blend[
            :, jnp.newaxis, jnp.newaxis, jnp.newaxis
        ] * (target_pressure - forecast_pressure)
        forecast = forecast.at[:, :, pressure_index].set(updated_pressure)
    if wind_response_weight > 0.0:
        surface_temperature = jnp.maximum(
            initial_state[:, surface_temperature_index],
            MIN_HYDROSTATIC_TEMPERATURE,
        )
        density = jnp.maximum(
            current_pressure / (DRY_AIR_GAS_CONSTANT * surface_temperature),
            MIN_SURFACE_AIR_DENSITY,
        )
        pressure_increment = target_pressure - current_pressure[jnp.newaxis]
        acceleration = -longitude_gradient(pressure_increment) / density[jnp.newaxis]
        wind_increment = jnp.clip(
            wind_response_hours * SECONDS_PER_HOUR * acceleration,
            -wind_response_max_increment,
            wind_response_max_increment,
        )
        wind_lead_decay = (
            1.0 - jnp.exp(-lead_days / wind_response_ramp_days)
        ) * jnp.exp(-lead_days / wind_response_decay_days)
        wind_blend = wind_response_weight * wind_lead_decay
        forecast_wind = forecast[:, :, surface_u_index]
        updated_wind = (
            forecast_wind
            + wind_blend[:, jnp.newaxis, jnp.newaxis, jnp.newaxis] * wind_increment
        )
        forecast = forecast.at[:, :, surface_u_index].set(updated_wind)
    return forecast


def add_ramped_thermal_thickness_phase_nudge(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    temperature_index: int,
    height_index: int,
    phase_weight: float,
    ramp_days: float,
    decay_days: float,
    max_increment_fraction: float,
    max_zonal_wave_number: float,
    max_meridional_wave_number: float,
) -> jax.Array:
    """Nudge Z500 phase using a ramped hypsometric lower-temperature target."""
    if phase_weight <= 0.0 or max_increment_fraction <= 0.0:
        return forecast

    forecast = jnp.asarray(forecast)
    initial_state = jnp.asarray(initial_state, dtype=forecast.dtype)
    current_temperature = initial_state[:, temperature_index]
    current_height = initial_state[:, height_index]
    temperature_phase = two_dimensional_phase_forecast(
        initial_state,
        lead_steps,
        current_count=current_count,
        variable_indices=(temperature_index,),
        max_zonal_wave_number=max_zonal_wave_number,
        max_meridional_wave_number=max_meridional_wave_number,
    )[:, :, 0]
    raw_increment = (
        DRY_AIR_GAS_CONSTANT
        * LOWER_MIDLEVEL_LOG_PRESSURE_RATIO
        * (temperature_phase - current_temperature[jnp.newaxis])
    )
    increment = cap_increment_to_current_eddy_rms(
        raw_increment,
        current_height,
        max_fraction=max_increment_fraction,
    )
    lead_days = (
        jnp.asarray(lead_steps, dtype=forecast.dtype)
        * jnp.asarray(step_seconds, dtype=forecast.dtype)
        / SECONDS_PER_DAY
    )
    ramp = 1.0 - jnp.exp(-lead_days / ramp_days)
    lead_weights = phase_weight * ramp * jnp.exp(-lead_days / decay_days)
    target = current_height[jnp.newaxis] + increment

    def nudge_one_lead(forecast_values, target_values, lead_weight):
        return phase_nudged_values(
            forecast_values[jnp.newaxis],
            target_values[jnp.newaxis],
            phase_weight=lead_weight,
        )[0]

    nudged = jax.vmap(nudge_one_lead)(
        forecast[:, :, height_index : height_index + 1],
        target[:, :, jnp.newaxis],
        lead_weights,
    )[:, :, 0]
    return forecast.at[:, :, height_index].set(nudged)


def phase_propagated_tendency_correction(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
    memory_decay_days: float,
    max_cumulative_steps: float,
    max_zonal_wave_number: float,
    max_meridional_wave_number: float,
) -> jax.Array:
    """Return recent tendency integrated along coherent 2-D spectral phase motion."""
    initial_state = jnp.asarray(initial_state)
    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    current_values = jnp.take(current_state, indices, axis=1)
    previous_values = jnp.take(previous_state, indices, axis=1)
    tendency = current_values - previous_values
    current_anomaly = current_values - jnp.mean(
        current_values,
        axis=(-2, -1),
        keepdims=True,
    )
    previous_anomaly = previous_values - jnp.mean(
        previous_values,
        axis=(-2, -1),
        keepdims=True,
    )
    tendency_coefficients = jnp.fft.fftn(
        reflect_phase_latitude(tendency),
        axes=(-2, -1),
    )
    current_coefficients = jnp.fft.fftn(
        reflect_phase_latitude(current_anomaly),
        axes=(-2, -1),
    )
    previous_coefficients = jnp.fft.fftn(
        reflect_phase_latitude(previous_anomaly),
        axes=(-2, -1),
    )
    cross_spectrum = current_coefficients * jnp.conj(previous_coefficients)
    phase_step = cross_spectrum / jnp.maximum(jnp.abs(cross_spectrum), 1.0e-6)
    longitude_count = tendency_coefficients.shape[-2]
    reflected_latitude_count = tendency_coefficients.shape[-1]
    zonal_wave_numbers = jnp.abs(jnp.fft.fftfreq(longitude_count) * longitude_count)
    meridional_wave_numbers = jnp.abs(
        jnp.fft.fftfreq(reflected_latitude_count) * reflected_latitude_count,
    )
    wave_mask = (zonal_wave_numbers[:, jnp.newaxis] <= max_zonal_wave_number) & (
        meridional_wave_numbers[jnp.newaxis, :] <= max_meridional_wave_number
    )
    wave_mask = wave_mask.at[0, 0].set(False)
    coherent = (jnp.abs(current_coefficients) > 1.0e-4) & (
        jnp.abs(previous_coefficients) > 1.0e-4
    )
    phase_step = jnp.where(
        wave_mask[jnp.newaxis, jnp.newaxis] & coherent,
        phase_step,
        1.0 + 0.0j,
    )
    lead_steps_array = jnp.asarray(lead_steps, dtype=initial_state.dtype)
    step_decay = jnp.exp(
        -jnp.asarray(step_seconds, dtype=initial_state.dtype)
        / (memory_decay_days * SECONDS_PER_DAY),
    )
    cumulative_steps = (1.0 - step_decay**lead_steps_array) / jnp.maximum(
        1.0 - step_decay,
        1.0e-6,
    )
    cumulative_steps = jnp.minimum(cumulative_steps, max_cumulative_steps)

    def correction_one_lead(lead_step, cumulative_step_count):
        propagated = tendency_coefficients * phase_step**lead_step
        tendency_field = jnp.fft.ifftn(propagated, axes=(-2, -1)).real
        tendency_field = tendency_field[..., : current_values.shape[-1]]
        return cumulative_step_count * tendency_field.astype(initial_state.dtype)

    return jax.vmap(correction_one_lead)(lead_steps_array, cumulative_steps)


def add_phase_propagated_tendency(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
    tendency_weight: float,
    memory_decay_days: float,
    max_cumulative_steps: float,
    max_zonal_wave_number: float,
    max_meridional_wave_number: float,
) -> jax.Array:
    """Add a small coherent recent-tendency memory to selected channels."""
    if not variable_indices or tendency_weight <= 0.0:
        return forecast

    correction = phase_propagated_tendency_correction(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        variable_indices=variable_indices,
        memory_decay_days=memory_decay_days,
        max_cumulative_steps=max_cumulative_steps,
        max_zonal_wave_number=max_zonal_wave_number,
        max_meridional_wave_number=max_meridional_wave_number,
    )
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    updated = jnp.take(forecast, indices, axis=2) + tendency_weight * correction
    return forecast.at[:, :, indices].set(updated)


def baroclinic_eddy_activity(
    initial_state: jax.Array,
    *,
    current_count: int,
    lower_u_index: int,
    lower_v_index: int,
    upper_u_index: int,
    upper_v_index: int,
) -> jax.Array:
    """Return bounded Eady-growth activity from lower-upper wind shear."""
    initial_state = jnp.asarray(initial_state)
    current_state = initial_state[:, :current_count]
    latitudes = latitude_radians(current_state.shape[-1], current_state.dtype)
    coriolis = jnp.abs(2.0 * EARTH_ANGULAR_VELOCITY * jnp.sin(latitudes))
    shear = jnp.sqrt(
        (current_state[:, upper_u_index] - current_state[:, lower_u_index]) ** 2
        + (current_state[:, upper_v_index] - current_state[:, lower_v_index]) ** 2
    )
    vertical_shear = shear / BAROCLINIC_LAYER_DEPTH
    eady_growth_per_day = (
        EADY_GROWTH_COEFFICIENT
        * coriolis[jnp.newaxis, jnp.newaxis, :]
        * vertical_shear
        * SECONDS_PER_DAY
        / BRUNT_VAISALA_FREQUENCY
    )
    return eady_growth_per_day / (eady_growth_per_day + 1.0)


def baroclinic_residual_memory_factor(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    lower_u_index: int,
    lower_v_index: int,
    upper_u_index: int,
    upper_v_index: int,
    decay_days: float,
    memory_strength: float,
) -> jax.Array:
    """Return a bounded factor that slows eddy decay in baroclinic zones."""
    initial_state = jnp.asarray(initial_state)
    activity = baroclinic_eddy_activity(
        initial_state,
        current_count=current_count,
        lower_u_index=lower_u_index,
        lower_v_index=lower_v_index,
        upper_u_index=upper_u_index,
        upper_v_index=upper_v_index,
    )
    lead_days = (
        jnp.asarray(lead_steps, dtype=initial_state.dtype)
        * jnp.asarray(step_seconds, dtype=initial_state.dtype)
        / SECONDS_PER_DAY
    )
    effective_decay_days = decay_days * (1.0 + memory_strength * activity)
    return jnp.exp(
        lead_days[:, jnp.newaxis, jnp.newaxis, jnp.newaxis] / decay_days
        - lead_days[:, jnp.newaxis, jnp.newaxis, jnp.newaxis]
        / effective_decay_days[jnp.newaxis],
    )


def add_optical_flow_residual(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
    flow_channel_indices: tuple[int, ...],
    regularization: float,
    smoothing_passes: int,
    max_displacement_cells: float,
    flow_scale: float,
    displacement_decay_steps: float,
    reference_wave_number: float,
    damping_power: float,
    decay_days: float,
    residual_weight: float,
    phase_channel_indices: tuple[int, ...] = (),
    phase_blend: float = 0.0,
    baroclinic_memory_indices: tuple[int, ...] = (),
    baroclinic_memory_strength: float = 0.0,
    lower_u_index: int = 8,
    lower_v_index: int = 9,
    upper_u_index: int = 6,
    upper_v_index: int = 7,
) -> jax.Array:
    """Replace selected channels with low-pass forecast plus 2-D residual motion."""
    forecast = jnp.asarray(forecast)
    forecast_low_pass = one_day_scale_selective_filter(
        forecast,
        reference_wave_number=reference_wave_number,
        damping_power=damping_power,
    )
    residual = optical_flow_residual_correction(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        flow_channel_indices=flow_channel_indices,
        regularization=regularization,
        smoothing_passes=smoothing_passes,
        max_displacement_cells=max_displacement_cells,
        flow_scale=flow_scale,
        displacement_decay_steps=displacement_decay_steps,
        reference_wave_number=reference_wave_number,
        damping_power=damping_power,
        decay_days=decay_days,
        residual_weight=residual_weight,
    )
    if phase_channel_indices and phase_blend > 0.0:
        phase_residual = spectral_phase_residual_correction(
            initial_state,
            lead_steps,
            step_seconds,
            current_count=current_count,
            reference_wave_number=reference_wave_number,
            damping_power=damping_power,
            decay_days=decay_days,
            residual_weight=residual_weight,
        )
        phase_indices = jnp.asarray(phase_channel_indices, dtype=jnp.int32)
        blended_residual = (1.0 - phase_blend) * jnp.take(
            residual,
            phase_indices,
            axis=2,
        ) + phase_blend * jnp.take(phase_residual, phase_indices, axis=2)
        residual = residual.at[:, :, phase_indices].set(blended_residual)
    if baroclinic_memory_indices and baroclinic_memory_strength > 0.0:
        memory_factor = baroclinic_residual_memory_factor(
            initial_state,
            lead_steps,
            step_seconds,
            current_count=current_count,
            lower_u_index=lower_u_index,
            lower_v_index=lower_v_index,
            upper_u_index=upper_u_index,
            upper_v_index=upper_v_index,
            decay_days=decay_days,
            memory_strength=baroclinic_memory_strength,
        )
        memory_indices = jnp.asarray(baroclinic_memory_indices, dtype=jnp.int32)
        memory_residual = jnp.take(residual, memory_indices, axis=2)
        residual = residual.at[:, :, memory_indices].set(
            memory_residual * memory_factor[:, :, jnp.newaxis],
        )
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    selected = jnp.take(forecast_low_pass, indices, axis=2) + jnp.take(
        residual,
        indices,
        axis=2,
    )
    return forecast.at[:, :, indices].set(selected)


def thermal_height_tendency_correction(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    temperature_index: int,
    u_index: int,
    v_index: int,
    reference_wave_number: float,
    damping_power: float,
    decay_days: float,
) -> jax.Array:
    """Return a short-memory Z500 tendency from lower-tropospheric warm advection."""
    initial_state = jnp.asarray(initial_state)
    current_state = initial_state[:, :current_count]
    lower_temperature = current_state[:, temperature_index]
    u_wind = current_state[:, u_index]
    v_wind = current_state[:, v_index]
    temperature_tendency = -(
        u_wind * longitude_gradient(lower_temperature)
        + v_wind * latitude_gradient(lower_temperature)
    )
    step_temperature_tendency = temperature_tendency * jnp.asarray(
        step_seconds, dtype=initial_state.dtype
    )
    hypsometric_factor = jnp.asarray(
        DRY_AIR_GAS_CONSTANT * LOWER_MIDLEVEL_LOG_PRESSURE_RATIO,
        dtype=initial_state.dtype,
    )
    height_tendency = hypsometric_factor * step_temperature_tendency
    height_tendency = height_tendency - jnp.mean(
        height_tendency,
        axis=-2,
        keepdims=True,
    )
    filtered_tendency = one_day_scale_selective_filter(
        height_tendency[jnp.newaxis, :, jnp.newaxis],
        reference_wave_number=reference_wave_number,
        damping_power=damping_power,
    )[0, :, 0]
    lead_steps_array = jnp.asarray(lead_steps, dtype=initial_state.dtype)
    lead_days = (
        lead_steps_array
        * jnp.asarray(step_seconds, dtype=initial_state.dtype)
        / SECONDS_PER_DAY
    )
    lead_decay = jnp.where(
        lead_steps_array > 0.0,
        jnp.exp(-lead_days / decay_days),
        0.0,
    )
    return lead_decay[:, jnp.newaxis, jnp.newaxis, jnp.newaxis] * filtered_tendency


def add_thermal_height_tendency(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    height_index: int,
    temperature_index: int,
    u_index: int,
    v_index: int,
    reference_wave_number: float,
    damping_power: float,
    decay_days: float,
    tendency_weight: float,
) -> jax.Array:
    """Add lower-tropospheric warm-advection height tendency to one channel."""
    correction = thermal_height_tendency_correction(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        temperature_index=temperature_index,
        u_index=u_index,
        v_index=v_index,
        reference_wave_number=reference_wave_number,
        damping_power=damping_power,
        decay_days=decay_days,
    )
    return forecast.at[:, :, height_index].set(
        forecast[:, :, height_index] + tendency_weight * correction
    )


def advect_grouped_zonal_residual(
    residual: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_state: jax.Array,
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
) -> jax.Array:
    """Shift one residual field with the model's layer-wise zonal steering."""
    residual = jnp.asarray(residual)
    step_seconds_array = jnp.asarray(step_seconds, dtype=residual.dtype)
    surface_u_wind, _ = weighted_wind(
        current_state,
        u_indices=surface_u_indices,
        v_indices=surface_v_indices,
        weights=surface_weights,
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    lower_u_wind, _ = weighted_wind(
        current_state,
        u_indices=(lower_u_index,),
        v_indices=(lower_v_index,),
        weights=(1.0,),
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    upper_u_wind, _ = weighted_wind(
        current_state,
        u_indices=(upper_u_index,),
        v_indices=(upper_v_index,),
        weights=(1.0,),
        wind_scale=wind_scale,
        max_wind_speed=max_wind_speed,
    )
    surface_displacement = zonal_cell_displacement(surface_u_wind, step_seconds_array)
    lower_displacement = zonal_cell_displacement(lower_u_wind, step_seconds_array)
    upper_displacement = zonal_cell_displacement(upper_u_wind, step_seconds_array)

    def forecast_one_lead(lead_step):
        lead_step = lead_step.astype(residual.dtype)
        shifted = shift_variable_group(
            residual,
            variable_indices=surface_indices,
            displacement_cells=surface_displacement * lead_step,
        )
        shifted = shift_variable_group(
            shifted,
            variable_indices=lower_indices,
            displacement_cells=lower_displacement * lead_step,
        )
        shifted = shift_variable_group(
            shifted,
            variable_indices=upper_indices,
            displacement_cells=upper_displacement * lead_step,
        )
        return shifted

    return jax.vmap(forecast_one_lead)(jnp.asarray(lead_steps, dtype=jnp.int32))


def highpass_tendency_residual_correction(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
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
    reference_wave_number: float,
    damping_power: float,
    decay_days: float,
    residual_weight: float,
) -> jax.Array:
    """Return transported short-memory weather-scale tendency corrections."""
    initial_state = jnp.asarray(initial_state)
    current_state = initial_state[:, :current_count]
    previous_state = initial_state[:, current_count : 2 * current_count]
    tendency = current_state - previous_state
    tendency_low_pass = one_day_scale_selective_filter(
        tendency[jnp.newaxis],
        reference_wave_number=reference_wave_number,
        damping_power=damping_power,
    )[0]
    highpass_tendency = tendency - tendency_low_pass
    shifted_tendency = advect_grouped_zonal_residual(
        highpass_tendency,
        lead_steps,
        step_seconds,
        current_state=current_state,
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
    )
    lead_days = (
        jnp.asarray(lead_steps, dtype=initial_state.dtype)
        * jnp.asarray(step_seconds, dtype=initial_state.dtype)
        / SECONDS_PER_DAY
    )
    decay = jnp.exp(-lead_days / decay_days)
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    return (
        residual_weight
        * decay[:, jnp.newaxis, jnp.newaxis, jnp.newaxis, jnp.newaxis]
        * jnp.take(shifted_tendency, indices, axis=2)
    )


def add_highpass_tendency_residual(
    forecast: jax.Array,
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    variable_indices: tuple[int, ...],
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
    reference_wave_number: float,
    damping_power: float,
    decay_days: float,
    residual_weight: float,
) -> jax.Array:
    """Add transported high-pass recent tendency to selected channels."""
    forecast = jnp.asarray(forecast)
    correction = highpass_tendency_residual_correction(
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        variable_indices=variable_indices,
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
        reference_wave_number=reference_wave_number,
        damping_power=damping_power,
        decay_days=decay_days,
        residual_weight=residual_weight,
    )
    indices = jnp.asarray(variable_indices, dtype=jnp.int32)
    return forecast.at[:, :, indices].set(
        jnp.take(forecast, indices, axis=2) + correction
    )


def pressure_inertia_layered_balanced_zonal_advection_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    tendency_indices: tuple[int, ...],
    tendency_decay_days: float,
    pressure_index: int,
    pressure_decay_days: float,
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
    temperature_memory_decay_days: float,
    surface_temperature_tendency_decay_days: float,
    surface_temperature_tendency_weight: float,
    surface_temperature_lower_air_anchor_weight: float,
    surface_temperature_lower_air_anchor_ramp_days: float,
    surface_temperature_lower_air_anchor_decay_days: float,
    scale_selective_indices: tuple[int, ...],
    scale_selective_reference_wave_number: float,
    scale_selective_damping_power: float,
    scale_selective_latitude_aware: bool,
    meridional_scale_selective_reference_wave_number: float,
    meridional_scale_selective_damping_power: float,
    horizontal_cross_scale_selective_reference_wave_number: float,
    horizontal_cross_scale_selective_latitude_aware: bool,
    surface_anomaly_rms_indices: tuple[int, ...],
    anomaly_rms_indices: tuple[int, ...],
    surface_wind_tendency_indices: tuple[int, ...],
    scale_split_residual_indices: tuple[int, ...],
    scale_split_reference_wave_number: float,
    scale_split_damping_power: float,
    scale_split_decay_days: float,
    scale_split_residual_weight: float,
    scale_split_flow_channel_indices: tuple[int, ...],
    scale_split_flow_regularization: float,
    scale_split_flow_smoothing_passes: int,
    scale_split_flow_max_displacement_cells: float,
    scale_split_flow_scale: float,
    scale_split_flow_displacement_decay_steps: float,
    scale_split_phase_residual_indices: tuple[int, ...],
    scale_split_phase_blend: float,
    scale_split_baroclinic_memory_indices: tuple[int, ...],
    scale_split_baroclinic_memory_strength: float,
    thermal_height_reference_wave_number: float,
    thermal_height_damping_power: float,
    thermal_height_decay_days: float,
    thermal_height_weight: float,
    zonal_phase_forecast_indices: tuple[int, ...],
    zonal_phase_forecast_weight: float,
    zonal_phase_nudge_indices: tuple[int, ...],
    zonal_phase_nudge_weight: float,
    zonal_phase_nudge_decay_days: float,
    phase_tendency_indices: tuple[int, ...],
    phase_tendency_weight: float,
    phase_tendency_memory_decay_days: float,
    phase_tendency_max_cumulative_steps: float,
    phase_tendency_max_zonal_wave_number: float,
    phase_tendency_max_meridional_wave_number: float,
    history_eddy_growth_indices: tuple[int, ...],
    history_eddy_growth_weight: float,
    history_eddy_growth_memory_decay_days: float,
    history_eddy_growth_max_scale: float,
    history_eddy_growth_max_log_growth_per_step: float,
    two_dimensional_phase_nudge_indices: tuple[int, ...],
    two_dimensional_phase_nudge_weight: float,
    two_dimensional_phase_nudge_decay_days: float,
    two_dimensional_phase_nudge_max_zonal_wave_number: float,
    two_dimensional_phase_nudge_max_meridional_wave_number: float,
    upper_vorticity_phase_nudge_weight: float,
    upper_vorticity_phase_nudge_decay_days: float,
    upper_vorticity_max_increment_fraction: float,
    upper_vorticity_wind_scale: float,
    upper_vorticity_max_wind_speed: float,
    upper_vorticity_coriolis_scale: float,
    upper_vorticity_reference_latitude_radians: float,
    barotropic_vorticity_phase_nudge_weight: float,
    barotropic_vorticity_amplitude_weight: float,
    barotropic_vorticity_pressure_response_weight: float,
    barotropic_vorticity_wind_response_weight: float,
    barotropic_vorticity_wind_response_hours: float,
    barotropic_vorticity_wind_response_max_increment: float,
    barotropic_vorticity_wind_response_ramp_days: float,
    barotropic_vorticity_wind_response_decay_days: float,
    barotropic_vorticity_phase_ramp_days: float,
    barotropic_vorticity_phase_decay_days: float,
    barotropic_vorticity_target_anomaly_weight: float,
    barotropic_vorticity_flow_scale: float,
    barotropic_vorticity_max_wind_speed: float,
    barotropic_vorticity_decay_days: float,
    barotropic_vorticity_coriolis_scale: float,
    barotropic_vorticity_reference_latitude_radians: float,
    thermal_thickness_phase_nudge_weight: float,
    thermal_thickness_phase_ramp_days: float,
    thermal_thickness_phase_decay_days: float,
    thermal_thickness_phase_max_increment_fraction: float,
    thermal_thickness_phase_max_zonal_wave_number: float,
    thermal_thickness_phase_max_meridional_wave_number: float,
    highpass_tendency_residual_indices: tuple[int, ...],
    highpass_tendency_reference_wave_number: float,
    highpass_tendency_damping_power: float,
    highpass_tendency_decay_days: float,
    highpass_tendency_residual_weight: float,
) -> jax.Array:
    """Roll out pressure-inertia transport with scale-selective damping."""
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
        lower_phase_reference_index=LOWER_TEMPERATURE_INDEX,
        upper_phase_reference_index=balanced_geopotential_index,
        phase_history_offset=current_count,
    )
    indices = jnp.asarray(scale_selective_indices, dtype=jnp.int32)
    filtered = scale_selective_filter(
        jnp.take(forecast, indices, axis=2),
        lead_steps,
        step_seconds,
        longitude_reference_wave_number=scale_selective_reference_wave_number,
        longitude_damping_power=scale_selective_damping_power,
        longitude_latitude_aware=scale_selective_latitude_aware,
        latitude_reference_wave_number=meridional_scale_selective_reference_wave_number,
        latitude_damping_power=meridional_scale_selective_damping_power,
        cross_reference_wave_number=horizontal_cross_scale_selective_reference_wave_number,
        cross_latitude_aware=horizontal_cross_scale_selective_latitude_aware,
    )
    forecast = forecast.at[:, :, indices].set(filtered)
    forecast = add_transported_upper_tendency(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        tendency_indices=tendency_indices,
        upper_u_index=upper_u_index,
        upper_v_index=upper_v_index,
        wind_scale=zonal_wind_scale,
        max_wind_speed=zonal_max_wind_speed,
        decay_days=tendency_decay_days,
    )
    forecast = add_lower_temperature_tendency(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        lower_temperature_index=LOWER_TEMPERATURE_INDEX,
        lower_u_index=lower_u_index,
        lower_v_index=lower_v_index,
        wind_scale=zonal_wind_scale,
        max_wind_speed=zonal_max_wind_speed,
        decay_days=tendency_decay_days,
    )
    forecast = add_upper_steered_pressure_tendency(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        pressure_index=pressure_index,
        upper_u_index=upper_u_index,
        upper_v_index=upper_v_index,
        wind_scale=zonal_wind_scale,
        max_wind_speed=zonal_max_wind_speed,
        decay_days=pressure_decay_days,
    )
    temperature_forecast = surface_temperature_memory_forecast(
        initial_state,
        forecast[:, :, LOWER_TEMPERATURE_INDEX],
        lead_steps,
        step_seconds,
        current_count=current_count,
        temperature_index=temperature_index,
        lower_temperature_index=LOWER_TEMPERATURE_INDEX,
        lower_u_index=lower_u_index,
        lower_v_index=lower_v_index,
        wind_scale=zonal_wind_scale,
        max_wind_speed=zonal_max_wind_speed,
        zonal_damping_days=zonal_damping_days,
        memory_decay_days=temperature_memory_decay_days,
    )
    forecast = forecast.at[:, :, temperature_index].set(temperature_forecast)
    forecast = add_surface_temperature_tendency(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        temperature_index=temperature_index,
        decay_days=surface_temperature_tendency_decay_days,
        tendency_weight=surface_temperature_tendency_weight,
    )
    forecast = partially_restore_initialized_anomaly_rms(
        forecast,
        initial_state,
        current_count=current_count,
        variable_indices=surface_anomaly_rms_indices,
    )
    forecast = add_surface_pressure_tendency(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        pressure_index=pressure_index,
        surface_u_indices=surface_u_indices,
        surface_v_indices=surface_v_indices,
        surface_weights=surface_weights,
        wind_scale=zonal_wind_scale,
        max_wind_speed=zonal_max_wind_speed,
        decay_days=pressure_decay_days,
    )
    forecast = add_surface_wind_tendency(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        wind_indices=surface_wind_tendency_indices,
        surface_u_indices=surface_u_indices,
        surface_v_indices=surface_v_indices,
        surface_weights=surface_weights,
        wind_scale=zonal_wind_scale,
        max_wind_speed=zonal_max_wind_speed,
        decay_days=tendency_decay_days,
    )
    forecast = restore_initialized_anomaly_rms(
        forecast,
        initial_state,
        current_count=current_count,
        variable_indices=anomaly_rms_indices,
    )
    forecast = add_highpass_tendency_residual(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        variable_indices=highpass_tendency_residual_indices,
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
        reference_wave_number=highpass_tendency_reference_wave_number,
        damping_power=highpass_tendency_damping_power,
        decay_days=highpass_tendency_decay_days,
        residual_weight=highpass_tendency_residual_weight,
    )
    forecast = add_optical_flow_residual(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        variable_indices=scale_split_residual_indices,
        flow_channel_indices=scale_split_flow_channel_indices,
        regularization=scale_split_flow_regularization,
        smoothing_passes=scale_split_flow_smoothing_passes,
        max_displacement_cells=scale_split_flow_max_displacement_cells,
        flow_scale=scale_split_flow_scale,
        displacement_decay_steps=scale_split_flow_displacement_decay_steps,
        reference_wave_number=scale_split_reference_wave_number,
        damping_power=scale_split_damping_power,
        decay_days=scale_split_decay_days,
        residual_weight=scale_split_residual_weight,
        phase_channel_indices=scale_split_phase_residual_indices,
        phase_blend=scale_split_phase_blend,
        baroclinic_memory_indices=scale_split_baroclinic_memory_indices,
        baroclinic_memory_strength=scale_split_baroclinic_memory_strength,
        lower_u_index=lower_u_index,
        lower_v_index=lower_v_index,
        upper_u_index=upper_u_index,
        upper_v_index=upper_v_index,
    )
    forecast = add_thermal_height_tendency(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        height_index=balanced_geopotential_index,
        temperature_index=LOWER_TEMPERATURE_INDEX,
        u_index=lower_u_index,
        v_index=lower_v_index,
        reference_wave_number=thermal_height_reference_wave_number,
        damping_power=thermal_height_damping_power,
        decay_days=thermal_height_decay_days,
        tendency_weight=thermal_height_weight,
    )
    forecast = add_zonal_phase_forecast(
        forecast,
        initial_state,
        lead_steps,
        current_count=current_count,
        variable_indices=zonal_phase_forecast_indices,
        phase_weight=zonal_phase_forecast_weight,
    )
    forecast = add_zonal_phase_nudge(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        variable_indices=zonal_phase_nudge_indices,
        phase_weight=zonal_phase_nudge_weight,
        decay_days=zonal_phase_nudge_decay_days,
    )
    forecast = add_phase_propagated_tendency(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        variable_indices=phase_tendency_indices,
        tendency_weight=phase_tendency_weight,
        memory_decay_days=phase_tendency_memory_decay_days,
        max_cumulative_steps=phase_tendency_max_cumulative_steps,
        max_zonal_wave_number=phase_tendency_max_zonal_wave_number,
        max_meridional_wave_number=phase_tendency_max_meridional_wave_number,
    )
    forecast = apply_history_eddy_growth_memory(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        variable_indices=history_eddy_growth_indices,
        growth_weight=history_eddy_growth_weight,
        memory_decay_days=history_eddy_growth_memory_decay_days,
        max_scale=history_eddy_growth_max_scale,
        max_log_growth_per_step=history_eddy_growth_max_log_growth_per_step,
    )
    forecast = add_two_dimensional_phase_nudge(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        variable_indices=two_dimensional_phase_nudge_indices,
        phase_weight=two_dimensional_phase_nudge_weight,
        decay_days=two_dimensional_phase_nudge_decay_days,
        max_zonal_wave_number=two_dimensional_phase_nudge_max_zonal_wave_number,
        max_meridional_wave_number=(
            two_dimensional_phase_nudge_max_meridional_wave_number
        ),
    )
    forecast = add_upper_vorticity_phase_nudge(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        geopotential_index=balanced_geopotential_index,
        upper_u_index=upper_u_index,
        upper_v_index=upper_v_index,
        wind_scale=upper_vorticity_wind_scale,
        max_wind_speed=upper_vorticity_max_wind_speed,
        coriolis_scale=upper_vorticity_coriolis_scale,
        reference_latitude_radians=upper_vorticity_reference_latitude_radians,
        max_increment_fraction=upper_vorticity_max_increment_fraction,
        phase_weight=upper_vorticity_phase_nudge_weight,
        decay_days=upper_vorticity_phase_nudge_decay_days,
    )
    forecast = add_ramped_thermal_thickness_phase_nudge(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        temperature_index=LOWER_TEMPERATURE_INDEX,
        height_index=balanced_geopotential_index,
        phase_weight=thermal_thickness_phase_nudge_weight,
        ramp_days=thermal_thickness_phase_ramp_days,
        decay_days=thermal_thickness_phase_decay_days,
        max_increment_fraction=thermal_thickness_phase_max_increment_fraction,
        max_zonal_wave_number=thermal_thickness_phase_max_zonal_wave_number,
        max_meridional_wave_number=(thermal_thickness_phase_max_meridional_wave_number),
    )
    forecast = add_barotropic_vorticity_phase_nudge(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        current_count=current_count,
        geopotential_index=balanced_geopotential_index,
        pressure_index=pressure_index,
        surface_temperature_index=temperature_index,
        surface_u_index=surface_u_indices[-1],
        lower_temperature_index=LOWER_TEMPERATURE_INDEX,
        flow_scale=barotropic_vorticity_flow_scale,
        max_wind_speed=barotropic_vorticity_max_wind_speed,
        vorticity_decay_days=barotropic_vorticity_decay_days,
        target_anomaly_weight=barotropic_vorticity_target_anomaly_weight,
        coriolis_scale=barotropic_vorticity_coriolis_scale,
        reference_latitude_radians=barotropic_vorticity_reference_latitude_radians,
        phase_weight=barotropic_vorticity_phase_nudge_weight,
        amplitude_weight=barotropic_vorticity_amplitude_weight,
        pressure_response_weight=barotropic_vorticity_pressure_response_weight,
        wind_response_weight=barotropic_vorticity_wind_response_weight,
        wind_response_hours=barotropic_vorticity_wind_response_hours,
        wind_response_max_increment=(barotropic_vorticity_wind_response_max_increment),
        wind_response_ramp_days=barotropic_vorticity_wind_response_ramp_days,
        wind_response_decay_days=barotropic_vorticity_wind_response_decay_days,
        ramp_days=barotropic_vorticity_phase_ramp_days,
        decay_days=barotropic_vorticity_phase_decay_days,
    )
    return add_lower_air_surface_temperature_anchor(
        forecast,
        initial_state,
        lead_steps,
        step_seconds,
        temperature_index=temperature_index,
        lower_temperature_index=LOWER_TEMPERATURE_INDEX,
        anchor_weight=surface_temperature_lower_air_anchor_weight,
        ramp_days=surface_temperature_lower_air_anchor_ramp_days,
        decay_days=surface_temperature_lower_air_anchor_decay_days,
    )


@dataclass(frozen=True)
class PressureInertiaLayeredBalancedZonalAdvectionDycoreModel:
    """Transported upper inertia with upper-steered pressure tendency."""

    name: str = "pressure_inertia_layered_balanced_zonal_advection"
    current_count: int = 10
    tendency_indices: tuple[int, ...] = (2, 6, 7)
    tendency_decay_days: float = 1.0
    pressure_index: int = 1
    pressure_decay_days: float = 1.0
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
    zonal_damping_days: float = 60.0
    balanced_flow_scale: float = 0.02
    balanced_max_wind_speed: float = 60.0
    balanced_diffusion_per_step: float = 0.0
    balanced_damping_days: float = 60.0
    temperature_memory_decay_days: float = 2.0
    surface_temperature_tendency_decay_days: float = 0.25
    surface_temperature_tendency_weight: float = 1.0
    surface_temperature_lower_air_anchor_weight: float = 0.20
    surface_temperature_lower_air_anchor_ramp_days: float = 3.0
    surface_temperature_lower_air_anchor_decay_days: float = 20.0
    scale_selective_indices: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9)
    scale_selective_reference_wave_number: float = 24.0
    scale_selective_damping_power: float = 4.0
    scale_selective_latitude_aware: bool = True
    meridional_scale_selective_reference_wave_number: float = 24.0
    meridional_scale_selective_damping_power: float = 4.0
    horizontal_cross_scale_selective_reference_wave_number: float = 24.0
    horizontal_cross_scale_selective_latitude_aware: bool = True
    surface_anomaly_rms_indices: tuple[int, ...] = (1, 3, 4)
    anomaly_rms_indices: tuple[int, ...] = (1, 2, 3, 4)
    surface_wind_tendency_indices: tuple[int, ...] = (3, 4)
    scale_split_residual_indices: tuple[int, ...] = (1, 2, 3, 4)
    scale_split_reference_wave_number: float = 20.0
    scale_split_damping_power: float = 4.0
    scale_split_decay_days: float = 12.0
    scale_split_residual_weight: float = 0.8
    scale_split_flow_channel_indices: tuple[int, ...] = (1, 2, 3, 4, 5)
    scale_split_flow_regularization: float = 0.05
    scale_split_flow_smoothing_passes: int = 6
    scale_split_flow_max_displacement_cells: float = 1.5
    scale_split_flow_scale: float = 1.0
    scale_split_flow_displacement_decay_steps: float = 8.0
    scale_split_phase_residual_indices: tuple[int, ...] = (2,)
    scale_split_phase_blend: float = 0.5
    scale_split_baroclinic_memory_indices: tuple[int, ...] = (1,)
    scale_split_baroclinic_memory_strength: float = 1.0
    thermal_height_reference_wave_number: float = 18.0
    thermal_height_damping_power: float = 4.0
    thermal_height_decay_days: float = 3.0
    thermal_height_weight: float = 1.0
    zonal_phase_forecast_indices: tuple[int, ...] = (2,)
    zonal_phase_forecast_weight: float = 0.15
    zonal_phase_nudge_indices: tuple[int, ...] = (1, 2, 3)
    zonal_phase_nudge_weight: float = 0.15
    zonal_phase_nudge_decay_days: float = 5.0
    phase_tendency_indices: tuple[int, ...] = (1, 2)
    phase_tendency_weight: float = 0.02
    phase_tendency_memory_decay_days: float = 2.0
    phase_tendency_max_cumulative_steps: float = 4.0
    phase_tendency_max_zonal_wave_number: float = 12.0
    phase_tendency_max_meridional_wave_number: float = 12.0
    history_eddy_growth_indices: tuple[int, ...] = (2,)
    history_eddy_growth_weight: float = 0.2
    history_eddy_growth_memory_decay_days: float = 2.0
    history_eddy_growth_max_scale: float = 1.15
    history_eddy_growth_max_log_growth_per_step: float = 0.05
    two_dimensional_phase_nudge_indices: tuple[int, ...] = (2,)
    two_dimensional_phase_nudge_weight: float = 0.10
    two_dimensional_phase_nudge_decay_days: float = 10.0
    two_dimensional_phase_nudge_max_zonal_wave_number: float = 12.0
    two_dimensional_phase_nudge_max_meridional_wave_number: float = 12.0
    upper_vorticity_phase_nudge_weight: float = 0.10
    upper_vorticity_phase_nudge_decay_days: float = 20.0
    upper_vorticity_max_increment_fraction: float = 0.10
    upper_vorticity_wind_scale: float = 1.0
    upper_vorticity_max_wind_speed: float = 70.0
    upper_vorticity_coriolis_scale: float = 1.0e-4
    upper_vorticity_reference_latitude_radians: float = REFERENCE_LATITUDE_RADIANS
    barotropic_vorticity_phase_nudge_weight: float = 0.05
    barotropic_vorticity_amplitude_weight: float = 0.10
    barotropic_vorticity_pressure_response_weight: float = 0.05
    barotropic_vorticity_wind_response_weight: float = 0.50
    barotropic_vorticity_wind_response_hours: float = 2.0
    barotropic_vorticity_wind_response_max_increment: float = 4.0
    barotropic_vorticity_wind_response_ramp_days: float = 2.0
    barotropic_vorticity_wind_response_decay_days: float = 10.0
    barotropic_vorticity_phase_ramp_days: float = 3.0
    barotropic_vorticity_phase_decay_days: float = 20.0
    barotropic_vorticity_target_anomaly_weight: float = 0.5
    barotropic_vorticity_flow_scale: float = 0.02
    barotropic_vorticity_max_wind_speed: float = 60.0
    barotropic_vorticity_decay_days: float = 30.0
    barotropic_vorticity_coriolis_scale: float = 1.0e-4
    barotropic_vorticity_reference_latitude_radians: float = REFERENCE_LATITUDE_RADIANS
    thermal_thickness_phase_nudge_weight: float = 0.25
    thermal_thickness_phase_ramp_days: float = 5.0
    thermal_thickness_phase_decay_days: float = 20.0
    thermal_thickness_phase_max_increment_fraction: float = 0.10
    thermal_thickness_phase_max_zonal_wave_number: float = 12.0
    thermal_thickness_phase_max_meridional_wave_number: float = 12.0
    highpass_tendency_residual_indices: tuple[int, ...] = (1, 2)
    highpass_tendency_reference_wave_number: float = 18.0
    highpass_tendency_damping_power: float = 4.0
    highpass_tendency_decay_days: float = 2.0
    highpass_tendency_residual_weight: float = 1.0
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
        return pressure_inertia_layered_balanced_zonal_advection_forecast(
            initial_state,
            lead_steps,
            step_seconds,
            current_count=self.current_count,
            tendency_indices=self.tendency_indices,
            tendency_decay_days=self.tendency_decay_days,
            pressure_index=self.pressure_index,
            pressure_decay_days=self.pressure_decay_days,
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
            temperature_memory_decay_days=self.temperature_memory_decay_days,
            surface_temperature_tendency_decay_days=(
                self.surface_temperature_tendency_decay_days
            ),
            surface_temperature_tendency_weight=(
                self.surface_temperature_tendency_weight
            ),
            surface_temperature_lower_air_anchor_weight=(
                self.surface_temperature_lower_air_anchor_weight
            ),
            surface_temperature_lower_air_anchor_ramp_days=(
                self.surface_temperature_lower_air_anchor_ramp_days
            ),
            surface_temperature_lower_air_anchor_decay_days=(
                self.surface_temperature_lower_air_anchor_decay_days
            ),
            scale_selective_indices=self.scale_selective_indices,
            scale_selective_reference_wave_number=(
                self.scale_selective_reference_wave_number
            ),
            scale_selective_damping_power=self.scale_selective_damping_power,
            scale_selective_latitude_aware=self.scale_selective_latitude_aware,
            meridional_scale_selective_reference_wave_number=(
                self.meridional_scale_selective_reference_wave_number
            ),
            meridional_scale_selective_damping_power=(
                self.meridional_scale_selective_damping_power
            ),
            horizontal_cross_scale_selective_reference_wave_number=(
                self.horizontal_cross_scale_selective_reference_wave_number
            ),
            horizontal_cross_scale_selective_latitude_aware=(
                self.horizontal_cross_scale_selective_latitude_aware
            ),
            surface_anomaly_rms_indices=self.surface_anomaly_rms_indices,
            anomaly_rms_indices=self.anomaly_rms_indices,
            surface_wind_tendency_indices=self.surface_wind_tendency_indices,
            scale_split_residual_indices=self.scale_split_residual_indices,
            scale_split_reference_wave_number=self.scale_split_reference_wave_number,
            scale_split_damping_power=self.scale_split_damping_power,
            scale_split_decay_days=self.scale_split_decay_days,
            scale_split_residual_weight=self.scale_split_residual_weight,
            scale_split_flow_channel_indices=self.scale_split_flow_channel_indices,
            scale_split_flow_regularization=self.scale_split_flow_regularization,
            scale_split_flow_smoothing_passes=self.scale_split_flow_smoothing_passes,
            scale_split_flow_max_displacement_cells=(
                self.scale_split_flow_max_displacement_cells
            ),
            scale_split_flow_scale=self.scale_split_flow_scale,
            scale_split_flow_displacement_decay_steps=(
                self.scale_split_flow_displacement_decay_steps
            ),
            scale_split_phase_residual_indices=(
                self.scale_split_phase_residual_indices
            ),
            scale_split_phase_blend=self.scale_split_phase_blend,
            scale_split_baroclinic_memory_indices=(
                self.scale_split_baroclinic_memory_indices
            ),
            scale_split_baroclinic_memory_strength=(
                self.scale_split_baroclinic_memory_strength
            ),
            thermal_height_reference_wave_number=(
                self.thermal_height_reference_wave_number
            ),
            thermal_height_damping_power=self.thermal_height_damping_power,
            thermal_height_decay_days=self.thermal_height_decay_days,
            thermal_height_weight=self.thermal_height_weight,
            zonal_phase_forecast_indices=self.zonal_phase_forecast_indices,
            zonal_phase_forecast_weight=self.zonal_phase_forecast_weight,
            zonal_phase_nudge_indices=self.zonal_phase_nudge_indices,
            zonal_phase_nudge_weight=self.zonal_phase_nudge_weight,
            zonal_phase_nudge_decay_days=self.zonal_phase_nudge_decay_days,
            phase_tendency_indices=self.phase_tendency_indices,
            phase_tendency_weight=self.phase_tendency_weight,
            phase_tendency_memory_decay_days=self.phase_tendency_memory_decay_days,
            phase_tendency_max_cumulative_steps=(
                self.phase_tendency_max_cumulative_steps
            ),
            phase_tendency_max_zonal_wave_number=(
                self.phase_tendency_max_zonal_wave_number
            ),
            phase_tendency_max_meridional_wave_number=(
                self.phase_tendency_max_meridional_wave_number
            ),
            history_eddy_growth_indices=self.history_eddy_growth_indices,
            history_eddy_growth_weight=self.history_eddy_growth_weight,
            history_eddy_growth_memory_decay_days=(
                self.history_eddy_growth_memory_decay_days
            ),
            history_eddy_growth_max_scale=self.history_eddy_growth_max_scale,
            history_eddy_growth_max_log_growth_per_step=(
                self.history_eddy_growth_max_log_growth_per_step
            ),
            two_dimensional_phase_nudge_indices=(
                self.two_dimensional_phase_nudge_indices
            ),
            two_dimensional_phase_nudge_weight=(
                self.two_dimensional_phase_nudge_weight
            ),
            two_dimensional_phase_nudge_decay_days=(
                self.two_dimensional_phase_nudge_decay_days
            ),
            two_dimensional_phase_nudge_max_zonal_wave_number=(
                self.two_dimensional_phase_nudge_max_zonal_wave_number
            ),
            two_dimensional_phase_nudge_max_meridional_wave_number=(
                self.two_dimensional_phase_nudge_max_meridional_wave_number
            ),
            upper_vorticity_phase_nudge_weight=(
                self.upper_vorticity_phase_nudge_weight
            ),
            upper_vorticity_phase_nudge_decay_days=(
                self.upper_vorticity_phase_nudge_decay_days
            ),
            upper_vorticity_max_increment_fraction=(
                self.upper_vorticity_max_increment_fraction
            ),
            upper_vorticity_wind_scale=self.upper_vorticity_wind_scale,
            upper_vorticity_max_wind_speed=self.upper_vorticity_max_wind_speed,
            upper_vorticity_coriolis_scale=self.upper_vorticity_coriolis_scale,
            upper_vorticity_reference_latitude_radians=(
                self.upper_vorticity_reference_latitude_radians
            ),
            barotropic_vorticity_phase_nudge_weight=(
                self.barotropic_vorticity_phase_nudge_weight
            ),
            barotropic_vorticity_amplitude_weight=(
                self.barotropic_vorticity_amplitude_weight
            ),
            barotropic_vorticity_pressure_response_weight=(
                self.barotropic_vorticity_pressure_response_weight
            ),
            barotropic_vorticity_wind_response_weight=(
                self.barotropic_vorticity_wind_response_weight
            ),
            barotropic_vorticity_wind_response_hours=(
                self.barotropic_vorticity_wind_response_hours
            ),
            barotropic_vorticity_wind_response_max_increment=(
                self.barotropic_vorticity_wind_response_max_increment
            ),
            barotropic_vorticity_wind_response_ramp_days=(
                self.barotropic_vorticity_wind_response_ramp_days
            ),
            barotropic_vorticity_wind_response_decay_days=(
                self.barotropic_vorticity_wind_response_decay_days
            ),
            barotropic_vorticity_phase_ramp_days=(
                self.barotropic_vorticity_phase_ramp_days
            ),
            barotropic_vorticity_phase_decay_days=(
                self.barotropic_vorticity_phase_decay_days
            ),
            barotropic_vorticity_target_anomaly_weight=(
                self.barotropic_vorticity_target_anomaly_weight
            ),
            barotropic_vorticity_flow_scale=self.barotropic_vorticity_flow_scale,
            barotropic_vorticity_max_wind_speed=(
                self.barotropic_vorticity_max_wind_speed
            ),
            barotropic_vorticity_decay_days=self.barotropic_vorticity_decay_days,
            barotropic_vorticity_coriolis_scale=(
                self.barotropic_vorticity_coriolis_scale
            ),
            barotropic_vorticity_reference_latitude_radians=(
                self.barotropic_vorticity_reference_latitude_radians
            ),
            thermal_thickness_phase_nudge_weight=(
                self.thermal_thickness_phase_nudge_weight
            ),
            thermal_thickness_phase_ramp_days=(self.thermal_thickness_phase_ramp_days),
            thermal_thickness_phase_decay_days=(
                self.thermal_thickness_phase_decay_days
            ),
            thermal_thickness_phase_max_increment_fraction=(
                self.thermal_thickness_phase_max_increment_fraction
            ),
            thermal_thickness_phase_max_zonal_wave_number=(
                self.thermal_thickness_phase_max_zonal_wave_number
            ),
            thermal_thickness_phase_max_meridional_wave_number=(
                self.thermal_thickness_phase_max_meridional_wave_number
            ),
            highpass_tendency_residual_indices=(
                self.highpass_tendency_residual_indices
            ),
            highpass_tendency_reference_wave_number=(
                self.highpass_tendency_reference_wave_number
            ),
            highpass_tendency_damping_power=self.highpass_tendency_damping_power,
            highpass_tendency_decay_days=self.highpass_tendency_decay_days,
            highpass_tendency_residual_weight=(self.highpass_tendency_residual_weight),
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
        assert self.pressure_decay_days > 0
        assert all(0 <= index < self.current_count for index in self.tendency_indices)
        assert 0 <= self.pressure_index < self.current_count
        assert self.temperature_index not in self.tendency_indices
        assert self.temperature_index != self.pressure_index
        assert self.pressure_index not in self.tendency_indices
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
        assert self.temperature_memory_decay_days > 0
        assert self.surface_temperature_tendency_decay_days > 0
        assert self.surface_temperature_tendency_weight >= 0
        assert self.surface_temperature_lower_air_anchor_weight >= 0
        assert self.surface_temperature_lower_air_anchor_weight <= 1
        assert self.surface_temperature_lower_air_anchor_ramp_days > 0
        assert self.surface_temperature_lower_air_anchor_decay_days > 0
        assert all(
            0 <= index < self.current_count for index in self.scale_selective_indices
        )
        assert self.temperature_index not in self.scale_selective_indices
        assert self.scale_selective_reference_wave_number > 0
        assert self.scale_selective_damping_power > 0
        assert self.meridional_scale_selective_reference_wave_number > 0
        assert self.meridional_scale_selective_damping_power > 0
        assert self.horizontal_cross_scale_selective_reference_wave_number > 0
        assert all(
            0 <= index < self.current_count
            for index in self.surface_anomaly_rms_indices
        )
        assert self.temperature_index not in self.surface_anomaly_rms_indices
        assert all(
            0 <= index < self.current_count for index in self.anomaly_rms_indices
        )
        assert self.temperature_index not in self.anomaly_rms_indices
        assert all(
            0 <= index < self.current_count
            for index in self.surface_wind_tendency_indices
        )
        assert self.temperature_index not in self.surface_wind_tendency_indices
        assert self.pressure_index not in self.surface_wind_tendency_indices
        assert all(
            0 <= index < self.current_count
            for index in self.scale_split_residual_indices
        )
        assert self.temperature_index not in self.scale_split_residual_indices
        assert self.scale_split_reference_wave_number > 0
        assert self.scale_split_damping_power > 0
        assert self.scale_split_decay_days > 0
        assert self.scale_split_residual_weight >= 0
        assert all(
            0 <= index < self.current_count
            for index in self.scale_split_flow_channel_indices
        )
        assert self.scale_split_flow_regularization > 0
        assert self.scale_split_flow_smoothing_passes >= 0
        assert self.scale_split_flow_max_displacement_cells > 0
        assert self.scale_split_flow_scale >= 0
        assert self.scale_split_flow_displacement_decay_steps > 0
        assert all(
            0 <= index < self.current_count
            for index in self.scale_split_phase_residual_indices
        )
        assert set(self.scale_split_phase_residual_indices).issubset(
            set(self.scale_split_residual_indices)
        )
        assert self.scale_split_phase_blend >= 0
        assert self.scale_split_phase_blend <= 1
        assert all(
            0 <= index < self.current_count
            for index in self.scale_split_baroclinic_memory_indices
        )
        assert set(self.scale_split_baroclinic_memory_indices).issubset(
            set(self.scale_split_residual_indices)
        )
        assert self.scale_split_baroclinic_memory_strength >= 0
        assert self.thermal_height_reference_wave_number > 0
        assert self.thermal_height_damping_power > 0
        assert self.thermal_height_decay_days > 0
        assert self.thermal_height_weight >= 0
        assert all(
            0 <= index < self.current_count
            for index in self.zonal_phase_forecast_indices
        )
        assert self.temperature_index not in self.zonal_phase_forecast_indices
        assert self.zonal_phase_forecast_weight >= 0
        assert self.zonal_phase_forecast_weight <= 1
        assert all(
            0 <= index < self.current_count for index in self.zonal_phase_nudge_indices
        )
        assert self.temperature_index not in self.zonal_phase_nudge_indices
        assert self.zonal_phase_nudge_weight >= 0
        assert self.zonal_phase_nudge_weight <= 1
        assert self.zonal_phase_nudge_decay_days > 0
        assert all(
            0 <= index < self.current_count for index in self.phase_tendency_indices
        )
        assert self.temperature_index not in self.phase_tendency_indices
        assert self.phase_tendency_weight >= 0
        assert self.phase_tendency_memory_decay_days > 0
        assert self.phase_tendency_max_cumulative_steps > 0
        assert self.phase_tendency_max_zonal_wave_number >= 0
        assert self.phase_tendency_max_meridional_wave_number >= 0
        assert all(
            0 <= index < self.current_count
            for index in self.history_eddy_growth_indices
        )
        assert self.temperature_index not in self.history_eddy_growth_indices
        assert self.history_eddy_growth_weight >= 0
        assert self.history_eddy_growth_memory_decay_days > 0
        assert self.history_eddy_growth_max_scale >= 1
        assert self.history_eddy_growth_max_log_growth_per_step >= 0
        assert all(
            0 <= index < self.current_count
            for index in self.two_dimensional_phase_nudge_indices
        )
        assert self.temperature_index not in self.two_dimensional_phase_nudge_indices
        assert self.two_dimensional_phase_nudge_weight >= 0
        assert self.two_dimensional_phase_nudge_weight <= 1
        assert self.two_dimensional_phase_nudge_decay_days > 0
        assert self.two_dimensional_phase_nudge_max_zonal_wave_number >= 0
        assert self.two_dimensional_phase_nudge_max_meridional_wave_number >= 0
        assert self.upper_vorticity_phase_nudge_weight >= 0
        assert self.upper_vorticity_phase_nudge_weight <= 1
        assert self.upper_vorticity_phase_nudge_decay_days > 0
        assert self.upper_vorticity_max_increment_fraction >= 0
        assert self.upper_vorticity_wind_scale >= 0
        assert self.upper_vorticity_max_wind_speed > 0
        assert self.upper_vorticity_coriolis_scale > 0
        assert self.barotropic_vorticity_phase_nudge_weight >= 0
        assert self.barotropic_vorticity_phase_nudge_weight <= 1
        assert self.barotropic_vorticity_amplitude_weight >= 0
        assert self.barotropic_vorticity_amplitude_weight <= 1
        assert self.barotropic_vorticity_pressure_response_weight >= 0
        assert self.barotropic_vorticity_pressure_response_weight <= 1
        assert self.barotropic_vorticity_wind_response_weight >= 0
        assert self.barotropic_vorticity_wind_response_weight <= 1
        assert self.barotropic_vorticity_wind_response_hours >= 0
        assert self.barotropic_vorticity_wind_response_max_increment > 0
        assert self.barotropic_vorticity_wind_response_ramp_days > 0
        assert self.barotropic_vorticity_wind_response_decay_days > 0
        assert self.barotropic_vorticity_phase_ramp_days > 0
        assert self.barotropic_vorticity_phase_decay_days > 0
        assert self.barotropic_vorticity_target_anomaly_weight >= 0
        assert self.barotropic_vorticity_flow_scale >= 0
        assert self.barotropic_vorticity_max_wind_speed > 0
        assert self.barotropic_vorticity_decay_days > 0
        assert self.barotropic_vorticity_coriolis_scale > 0
        assert self.thermal_thickness_phase_nudge_weight >= 0
        assert self.thermal_thickness_phase_nudge_weight <= 1
        assert self.thermal_thickness_phase_ramp_days > 0
        assert self.thermal_thickness_phase_decay_days > 0
        assert self.thermal_thickness_phase_max_increment_fraction >= 0
        assert self.thermal_thickness_phase_max_zonal_wave_number >= 0
        assert self.thermal_thickness_phase_max_meridional_wave_number >= 0
        assert all(
            0 <= index < self.current_count
            for index in self.highpass_tendency_residual_indices
        )
        assert self.temperature_index not in self.highpass_tendency_residual_indices
        assert self.highpass_tendency_reference_wave_number > 0
        assert self.highpass_tendency_damping_power > 0
        assert self.highpass_tendency_decay_days > 0
        assert self.highpass_tendency_residual_weight >= 0

        return self.forecast_function(
            jnp.asarray(initial_state),
            lead_steps=lead_steps,
            step_seconds=step_seconds,
        )


def default_pressure_inertia_layered_balanced_zonal_advection_dycore_model() -> (
    PressureInertiaLayeredBalancedZonalAdvectionDycoreModel
):
    """Return the default pressure-inertia layered balanced-zonal dycore."""
    return PressureInertiaLayeredBalancedZonalAdvectionDycoreModel()
