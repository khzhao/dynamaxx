# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

from dynamaxx.dycore.transport import (
    MIN_COS_LATITUDE,
    cell_laplacian,
    latitude_radians,
    semi_lagrangian_advect,
)
from dynamaxx.utils.consts import EARTH_ANGULAR_VELOCITY, EARTH_RADIUS

SECONDS_PER_DAY = 86_400.0
REFERENCE_STEP_SECONDS = 21_600.0
MIN_CORIOLIS = 2.0e-5


def longitude_gradient(values: jax.Array) -> jax.Array:
    """Return d(values)/dx on an inferred global longitude-latitude grid."""
    values = jnp.asarray(values)
    longitude_count, latitude_count = values.shape[-2:]
    latitudes = latitude_radians(latitude_count, values.dtype)
    dlon = 2.0 * jnp.pi / longitude_count
    dx = (
        EARTH_RADIUS * jnp.maximum(jnp.abs(jnp.cos(latitudes)), MIN_COS_LATITUDE) * dlon
    )
    dx_shape = (1,) * (values.ndim - 1) + (latitude_count,)
    dx = jnp.reshape(dx, dx_shape)
    return (
        jnp.roll(values, shift=-1, axis=-2) - jnp.roll(values, shift=1, axis=-2)
    ) / (2.0 * dx)


def latitude_gradient(values: jax.Array) -> jax.Array:
    """Return d(values)/dy on an inferred north-to-south latitude axis."""
    values = jnp.asarray(values)
    latitude_count = values.shape[-1]
    assert latitude_count >= 2
    dlat = -jnp.pi / (latitude_count - 1)
    dy = EARTH_RADIUS * dlat
    first = (values[..., 1:2] - values[..., :1]) / dy
    interior = (values[..., 2:] - values[..., :-2]) / (2.0 * dy)
    last = (values[..., -1:] - values[..., -2:-1]) / dy
    return jnp.concatenate([first, interior, last], axis=-1)


def geostrophic_wind(
    state: jax.Array,
    *,
    geopotential_index: int,
    flow_scale: float,
    max_wind_speed: float,
) -> tuple[jax.Array, jax.Array]:
    """Infer a clipped geostrophic steering flow from one geopotential channel."""
    state = jnp.asarray(state)
    geopotential = state[:, geopotential_index]
    latitude_count = state.shape[-1]
    latitudes = latitude_radians(latitude_count, state.dtype)
    coriolis = 2.0 * EARTH_ANGULAR_VELOCITY * jnp.sin(latitudes)
    coriolis_sign = jnp.where(coriolis >= 0.0, 1.0, -1.0)
    coriolis_safe = coriolis_sign * jnp.maximum(jnp.abs(coriolis), MIN_CORIOLIS)
    equator_taper = jnp.abs(coriolis) / (jnp.abs(coriolis) + MIN_CORIOLIS)
    coriolis_safe = jnp.reshape(coriolis_safe, (1, 1, latitude_count))
    equator_taper = jnp.reshape(equator_taper, (1, 1, latitude_count))

    u_wind = -latitude_gradient(geopotential) / coriolis_safe
    v_wind = longitude_gradient(geopotential) / coriolis_safe
    u_wind = flow_scale * equator_taper * u_wind
    v_wind = flow_scale * equator_taper * v_wind

    speed = jnp.sqrt(u_wind * u_wind + v_wind * v_wind)
    speed_scale = jnp.minimum(1.0, max_wind_speed / jnp.maximum(speed, 1.0e-6))
    return u_wind * speed_scale, v_wind * speed_scale


def geostrophic_step(
    state: jax.Array,
    step_seconds: jax.Array,
    *,
    geopotential_index: int,
    flow_scale: float,
    max_wind_speed: float,
    diffusion_per_step: float,
    damping_days: float,
) -> jax.Array:
    """Advance one semi-Lagrangian geostrophic advection step."""
    u_wind, v_wind = geostrophic_wind(
        state,
        geopotential_index=geopotential_index,
        flow_scale=flow_scale,
        max_wind_speed=max_wind_speed,
    )
    advected = semi_lagrangian_advect(state, u_wind, v_wind, step_seconds)
    diffusion_amount = diffusion_per_step * step_seconds / REFERENCE_STEP_SECONDS
    diffused = advected + diffusion_amount * cell_laplacian(advected)
    zonal_mean = jnp.mean(diffused, axis=-2, keepdims=True)
    damping = jnp.exp(-step_seconds / (damping_days * SECONDS_PER_DAY))
    return zonal_mean + damping * (diffused - zonal_mean)


def geostrophic_advection_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    geopotential_index: int,
    flow_scale: float,
    max_wind_speed: float,
    diffusion_per_step: float,
    damping_days: float,
) -> jax.Array:
    """Roll out a geostrophic semi-Lagrangian forecast."""
    initial_state = jnp.asarray(initial_state)
    assert initial_state.ndim == 4
    assert 0 <= geopotential_index < initial_state.shape[1]
    step_seconds_array = jnp.asarray(step_seconds, dtype=initial_state.dtype)

    def scan_step(state, _):
        next_state = geostrophic_step(
            state,
            step_seconds_array,
            geopotential_index=geopotential_index,
            flow_scale=flow_scale,
            max_wind_speed=max_wind_speed,
            diffusion_per_step=diffusion_per_step,
            damping_days=damping_days,
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
class GeostrophicAdvectionDycoreModel:
    """Semi-Lagrangian model using 500 hPa geopotential as steering flow."""

    name: str = "geostrophic_advection"
    geopotential_index: int = 2
    flow_scale: float = 0.02
    max_wind_speed: float = 60.0
    diffusion_per_step: float = 0.05
    damping_days: float = 40.0
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
        return geostrophic_advection_forecast(
            initial_state,
            lead_steps,
            step_seconds,
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
        assert self.max_wind_speed > 0
        assert self.diffusion_per_step >= 0
        assert self.damping_days > 0

        return self.forecast_function(
            jnp.asarray(initial_state),
            lead_steps=lead_steps,
            step_seconds=step_seconds,
        )


def default_geostrophic_advection_dycore_model() -> GeostrophicAdvectionDycoreModel:
    """Return the default geostrophic advection dycore model."""
    return GeostrophicAdvectionDycoreModel()
