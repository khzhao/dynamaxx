# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

from dynamaxx.dycore.transport import bilinear_sample_periodic_longitude


def split_history_state(
    state: jax.Array,
    *,
    current_count: int,
) -> tuple[jax.Array, jax.Array]:
    """Split packed current and previous-history state channels."""
    state = jnp.asarray(state)
    assert state.ndim == 4
    assert state.shape[1] >= 2 * current_count
    return state[:, :current_count], state[:, current_count : 2 * current_count]


def cell_gradient_x(values: jax.Array) -> jax.Array:
    """Return centered longitude gradient in grid-cell units."""
    return 0.5 * (
        jnp.roll(values, shift=-1, axis=-2) - jnp.roll(values, shift=1, axis=-2)
    )


def cell_gradient_y(values: jax.Array) -> jax.Array:
    """Return centered latitude gradient in grid-cell units."""
    first = values[..., 1:2] - values[..., :1]
    interior = 0.5 * (values[..., 2:] - values[..., :-2])
    last = values[..., -1:] - values[..., -2:-1]
    return jnp.concatenate([first, interior, last], axis=-1)


def smooth_grid(values: jax.Array, passes: int) -> jax.Array:
    """Smooth grid values with a compact conservative stencil."""
    values = jnp.asarray(values)
    for _ in range(passes):
        west = jnp.roll(values, shift=1, axis=-2)
        east = jnp.roll(values, shift=-1, axis=-2)
        north = jnp.concatenate([values[..., :1], values[..., :-1]], axis=-1)
        south = jnp.concatenate([values[..., 1:], values[..., -1:]], axis=-1)
        values = 0.5 * values + 0.125 * (west + east + north + south)
    return values


def normalized_features(
    state: jax.Array,
    *,
    channel_indices: tuple[int, ...],
) -> jax.Array:
    """Return selected channels normalized over longitude-latitude axes."""
    indices = jnp.asarray(channel_indices, dtype=jnp.int32)
    features = jnp.take(state, indices, axis=1)
    mean = jnp.mean(features, axis=(-2, -1), keepdims=True)
    variance = jnp.mean((features - mean) ** 2, axis=(-2, -1), keepdims=True)
    return (features - mean) / jnp.sqrt(variance + 1.0e-6)


def estimate_optical_flow_cells(
    current_state: jax.Array,
    previous_state: jax.Array,
    *,
    channel_indices: tuple[int, ...],
    regularization: float,
    smoothing_passes: int,
    max_displacement_cells: float,
    flow_scale: float,
) -> tuple[jax.Array, jax.Array]:
    """Estimate previous-to-current displacement in grid cells per step."""
    current_features = normalized_features(
        current_state,
        channel_indices=channel_indices,
    )
    previous_features = normalized_features(
        previous_state,
        channel_indices=channel_indices,
    )
    reference_features = 0.5 * (current_features + previous_features)
    gradient_x = cell_gradient_x(reference_features)
    gradient_y = cell_gradient_y(reference_features)
    tendency = current_features - previous_features

    a00 = jnp.sum(gradient_x * gradient_x, axis=1)
    a01 = jnp.sum(gradient_x * gradient_y, axis=1)
    a11 = jnp.sum(gradient_y * gradient_y, axis=1)
    b0 = -jnp.sum(gradient_x * tendency, axis=1)
    b1 = -jnp.sum(gradient_y * tendency, axis=1)

    a00 = smooth_grid(a00, smoothing_passes)
    a01 = smooth_grid(a01, smoothing_passes)
    a11 = smooth_grid(a11, smoothing_passes)
    b0 = smooth_grid(b0, smoothing_passes)
    b1 = smooth_grid(b1, smoothing_passes)

    a00_regularized = a00 + regularization
    a11_regularized = a11 + regularization
    determinant = a00_regularized * a11_regularized - a01 * a01
    displacement_x = (b0 * a11_regularized - b1 * a01) / determinant
    displacement_y = (a00_regularized * b1 - a01 * b0) / determinant
    displacement_x = flow_scale * smooth_grid(displacement_x, smoothing_passes)
    displacement_y = flow_scale * smooth_grid(displacement_y, smoothing_passes)

    speed = jnp.sqrt(displacement_x * displacement_x + displacement_y * displacement_y)
    speed_scale = jnp.minimum(
        1.0,
        max_displacement_cells / jnp.maximum(speed, 1.0e-6),
    )
    return displacement_x * speed_scale, displacement_y * speed_scale


def advect_with_cell_displacement(
    state: jax.Array,
    displacement_x: jax.Array,
    displacement_y: jax.Array,
) -> jax.Array:
    """Advect state by a displacement field measured in grid cells per step."""
    state = jnp.asarray(state)
    longitude_count, latitude_count = state.shape[-2:]
    longitude_index = jnp.arange(longitude_count, dtype=state.dtype)[:, jnp.newaxis]
    latitude_index = jnp.arange(latitude_count, dtype=state.dtype)[jnp.newaxis, :]
    source_longitude = longitude_index - displacement_x
    source_latitude = latitude_index - displacement_y

    def advect_member(member_state, member_source_lon, member_source_lat):
        return jax.vmap(
            lambda variable: bilinear_sample_periodic_longitude(
                variable,
                member_source_lon,
                member_source_lat,
            )
        )(member_state)

    return jax.vmap(advect_member)(state, source_longitude, source_latitude)


def optical_flow_advection_forecast(
    initial_state: jax.Array,
    lead_steps: tuple[int, ...],
    *,
    current_count: int,
    flow_channel_indices: tuple[int, ...],
    regularization: float,
    smoothing_passes: int,
    max_displacement_cells: float,
    flow_scale: float,
    displacement_decay_steps: float,
) -> jax.Array:
    """Roll out an optical-flow feature-tracking forecast."""
    current, previous = split_history_state(initial_state, current_count=current_count)
    displacement_x, displacement_y = estimate_optical_flow_cells(
        current,
        previous,
        channel_indices=flow_channel_indices,
        regularization=regularization,
        smoothing_passes=smoothing_passes,
        max_displacement_cells=max_displacement_cells,
        flow_scale=flow_scale,
    )
    decay = jnp.exp(-1.0 / displacement_decay_steps)

    def scan_step(carry, _):
        current_state, step_displacement_x, step_displacement_y = carry
        next_current = advect_with_cell_displacement(
            current_state,
            step_displacement_x,
            step_displacement_y,
        )
        packed_state = jnp.concatenate([next_current, current_state], axis=1)
        next_carry = (
            next_current,
            step_displacement_x * decay,
            step_displacement_y * decay,
        )
        return next_carry, packed_state

    _, trajectory = jax.lax.scan(
        scan_step,
        (current, displacement_x, displacement_y),
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
class OpticalFlowAdvectionDycoreModel:
    """Feature-tracking model that extrapolates the observed 6h displacement."""

    name: str = "optical_flow_advection"
    current_count: int = 10
    flow_channel_indices: tuple[int, ...] = (0, 1, 2, 3, 5)
    regularization: float = 0.05
    smoothing_passes: int = 4
    max_displacement_cells: float = 2.0
    flow_scale: float = 1.0
    displacement_decay_steps: float = 12.0
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
        del step_seconds
        return optical_flow_advection_forecast(
            jnp.asarray(initial_state),
            lead_steps,
            current_count=self.current_count,
            flow_channel_indices=self.flow_channel_indices,
            regularization=self.regularization,
            smoothing_passes=self.smoothing_passes,
            max_displacement_cells=self.max_displacement_cells,
            flow_scale=self.flow_scale,
            displacement_decay_steps=self.displacement_decay_steps,
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
        assert self.regularization > 0
        assert self.smoothing_passes >= 0
        assert self.max_displacement_cells > 0
        assert self.displacement_decay_steps > 0

        return self.forecast_function(
            jnp.asarray(initial_state),
            lead_steps=lead_steps,
            step_seconds=step_seconds,
        )


def default_optical_flow_advection_dycore_model() -> OpticalFlowAdvectionDycoreModel:
    """Return the default optical-flow advection dycore model."""
    return OpticalFlowAdvectionDycoreModel()
