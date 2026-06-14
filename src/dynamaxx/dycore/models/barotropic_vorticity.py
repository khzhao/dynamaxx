# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

from dynamaxx.dycore.models.geostrophic_advection import (
    geostrophic_wind,
    latitude_gradient,
    longitude_gradient,
)
from dynamaxx.dycore.transport import latitude_radians, semi_lagrangian_advect_corrected
from dynamaxx.utils.consts import EARTH_ANGULAR_VELOCITY, EARTH_RADIUS

SECONDS_PER_DAY = 86_400.0
REFERENCE_LATITUDE_RADIANS = 0.75


def coriolis_parameter(latitude_count: int, dtype) -> jax.Array:
    """Return latitude-dependent Coriolis parameter."""
    latitudes = latitude_radians(latitude_count, dtype)
    return 2.0 * EARTH_ANGULAR_VELOCITY * jnp.sin(latitudes)


def relative_vorticity(
    u_wind: jax.Array,
    v_wind: jax.Array,
) -> jax.Array:
    """Return vertical relative vorticity from horizontal wind components."""
    return longitude_gradient(v_wind) - latitude_gradient(u_wind)


def reflect_latitude(values: jax.Array) -> jax.Array:
    """Reflect values across the latitude boundaries for spectral inversion."""
    values = jnp.asarray(values)
    return jnp.concatenate([values, values[..., 1:-1][..., ::-1]], axis=-1)


def invert_vorticity_to_geopotential(
    vorticity: jax.Array,
    *,
    coriolis_scale: float,
    reference_latitude_radians: float,
) -> jax.Array:
    """Invert quasi-geostrophic vorticity into a geopotential anomaly."""
    vorticity = jnp.asarray(vorticity)
    longitude_count, latitude_count = vorticity.shape[-2:]
    reflected = reflect_latitude(vorticity)
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


def barotropic_vorticity_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    current_count: int,
    geopotential_index: int,
    flow_scale: float,
    max_wind_speed: float,
    vorticity_decay_days: float,
    anomaly_weight: float,
    coriolis_scale: float,
    reference_latitude_radians: float,
) -> jax.Array:
    """Roll out a barotropic-vorticity Z500 forecast over persisted channels."""
    initial_state = jnp.asarray(initial_state)
    assert initial_state.ndim == 4
    assert initial_state.shape[1] >= current_count
    current_state = initial_state[:, :current_count]
    step_seconds_array = jnp.asarray(step_seconds, dtype=initial_state.dtype)
    u_wind, v_wind = geostrophic_wind(
        current_state,
        geopotential_index=geopotential_index,
        flow_scale=flow_scale,
        max_wind_speed=max_wind_speed,
    )
    current_geopotential = current_state[:, geopotential_index]
    coriolis = coriolis_parameter(
        current_geopotential.shape[-1],
        current_geopotential.dtype,
    )
    absolute_vorticity = (
        relative_vorticity(u_wind, v_wind) + coriolis[jnp.newaxis, jnp.newaxis, :]
    )

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
    relative_vorticity_forecast = (
        selected_vorticity - coriolis[jnp.newaxis, jnp.newaxis, jnp.newaxis, :]
    )
    initial_relative_vorticity = (
        absolute_vorticity - coriolis[jnp.newaxis, jnp.newaxis, :]
    )
    relative_vorticity_change = (
        relative_vorticity_forecast - initial_relative_vorticity[jnp.newaxis]
    )

    def invert_one_lead(vorticity):
        return invert_vorticity_to_geopotential(
            vorticity,
            coriolis_scale=coriolis_scale,
            reference_latitude_radians=reference_latitude_radians,
        )

    geopotential_increment = jax.vmap(invert_one_lead)(relative_vorticity_change)
    lead_days = (
        jnp.asarray(lead_steps, dtype=initial_state.dtype)
        * step_seconds_array
        / SECONDS_PER_DAY
    )
    anomaly_decay = jnp.exp(-lead_days / vorticity_decay_days)
    geopotential_forecast = current_geopotential[jnp.newaxis] + (
        anomaly_weight
        * anomaly_decay[:, jnp.newaxis, jnp.newaxis, jnp.newaxis]
        * geopotential_increment
    )
    forecast = jnp.broadcast_to(
        initial_state[jnp.newaxis],
        (len(lead_steps),) + initial_state.shape,
    )
    return forecast.at[:, :, geopotential_index].set(geopotential_forecast)


@dataclass(frozen=True)
class BarotropicVorticityDycoreModel:
    """Barotropic-vorticity Z500 evolution with persistence elsewhere."""

    name: str = "barotropic_vorticity"
    current_count: int = 10
    geopotential_index: int = 2
    flow_scale: float = 0.02
    max_wind_speed: float = 60.0
    vorticity_decay_days: float = 30.0
    anomaly_weight: float = 1.0
    coriolis_scale: float = 1.0e-4
    reference_latitude_radians: float = REFERENCE_LATITUDE_RADIANS
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
        return barotropic_vorticity_forecast(
            initial_state,
            lead_steps,
            step_seconds,
            current_count=self.current_count,
            geopotential_index=self.geopotential_index,
            flow_scale=self.flow_scale,
            max_wind_speed=self.max_wind_speed,
            vorticity_decay_days=self.vorticity_decay_days,
            anomaly_weight=self.anomaly_weight,
            coriolis_scale=self.coriolis_scale,
            reference_latitude_radians=self.reference_latitude_radians,
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
        assert 0 <= self.geopotential_index < self.current_count
        assert self.flow_scale >= 0
        assert self.max_wind_speed > 0
        assert self.vorticity_decay_days > 0
        assert self.anomaly_weight >= 0
        assert self.coriolis_scale > 0

        return self.forecast_function(
            jnp.asarray(initial_state),
            lead_steps=lead_steps,
            step_seconds=step_seconds,
        )


def default_barotropic_vorticity_dycore_model() -> BarotropicVorticityDycoreModel:
    """Return the default barotropic-vorticity dycore model."""
    return BarotropicVorticityDycoreModel()
