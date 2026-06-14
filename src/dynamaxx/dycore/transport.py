# Copyright 2026 dynamaxx

import jax
import jax.numpy as jnp

from dynamaxx.utils.consts import EARTH_RADIUS

MIN_COS_LATITUDE = 0.08


def latitude_radians(latitude_count: int, dtype) -> jax.Array:
    """Return latitude coordinates from north to south in radians."""
    assert latitude_count >= 2
    return jnp.linspace(0.5 * jnp.pi, -0.5 * jnp.pi, latitude_count, dtype=dtype)


def cell_laplacian(values: jax.Array) -> jax.Array:
    """Return a bounded grid-cell Laplacian for mild numerical diffusion."""
    values = jnp.asarray(values)
    west = jnp.roll(values, shift=1, axis=-2)
    east = jnp.roll(values, shift=-1, axis=-2)
    north = jnp.concatenate([values[..., :1], values[..., :-1]], axis=-1)
    south = jnp.concatenate([values[..., 1:], values[..., -1:]], axis=-1)
    return west + east + north + south - 4.0 * values


def bilinear_sample_periodic_longitude(
    values: jax.Array,
    source_longitude: jax.Array,
    source_latitude: jax.Array,
) -> jax.Array:
    """Sample one longitude-latitude field at fractional grid coordinates."""
    longitude_count, latitude_count = values.shape
    source_longitude = source_longitude % longitude_count
    source_latitude = jnp.clip(source_latitude, 0.0, latitude_count - 1.0)

    lon0 = jnp.floor(source_longitude).astype(jnp.int32)
    lat0 = jnp.floor(source_latitude).astype(jnp.int32)
    lon1 = (lon0 + 1) % longitude_count
    lat1 = jnp.minimum(lat0 + 1, latitude_count - 1)
    lon_weight = source_longitude - jnp.floor(source_longitude)
    lat_weight = source_latitude - jnp.floor(source_latitude)

    value00 = values[lon0, lat0]
    value10 = values[lon1, lat0]
    value01 = values[lon0, lat1]
    value11 = values[lon1, lat1]
    lower = value00 * (1.0 - lon_weight) + value10 * lon_weight
    upper = value01 * (1.0 - lon_weight) + value11 * lon_weight
    return lower * (1.0 - lat_weight) + upper * lat_weight


def semi_lagrangian_advect_single(
    state: jax.Array,
    u_wind: jax.Array,
    v_wind: jax.Array,
    step_seconds: jax.Array,
) -> jax.Array:
    """Advect one batched state member by tracing departure points backward."""
    longitude_count, latitude_count = state.shape[-2:]
    latitudes = latitude_radians(latitude_count, state.dtype)
    dlon = 2.0 * jnp.pi / longitude_count
    dlat = jnp.pi / (latitude_count - 1)
    dx = (
        EARTH_RADIUS * jnp.maximum(jnp.abs(jnp.cos(latitudes)), MIN_COS_LATITUDE) * dlon
    )
    dy = EARTH_RADIUS * dlat

    longitude_index = jnp.arange(longitude_count, dtype=state.dtype)[:, jnp.newaxis]
    latitude_index = jnp.arange(latitude_count, dtype=state.dtype)[jnp.newaxis, :]
    source_longitude = longitude_index - u_wind * step_seconds / dx[jnp.newaxis, :]
    source_latitude = latitude_index + v_wind * step_seconds / dy

    return jax.vmap(
        lambda variable: bilinear_sample_periodic_longitude(
            variable,
            source_longitude,
            source_latitude,
        )
    )(state)


def semi_lagrangian_advect(
    state: jax.Array,
    u_wind: jax.Array,
    v_wind: jax.Array,
    step_seconds: jax.Array,
) -> jax.Array:
    """Advect state shaped as (init, variable, longitude, latitude)."""
    return jax.vmap(semi_lagrangian_advect_single, in_axes=(0, 0, 0, None))(
        state,
        u_wind,
        v_wind,
        step_seconds,
    )


def semi_lagrangian_advect_corrected(
    state: jax.Array,
    u_wind: jax.Array,
    v_wind: jax.Array,
    step_seconds: jax.Array,
) -> jax.Array:
    """Advect with a reversible corrector that reduces interpolation diffusion."""
    state = jnp.asarray(state)
    forward = semi_lagrangian_advect(state, u_wind, v_wind, step_seconds)
    backward = semi_lagrangian_advect(forward, u_wind, v_wind, -step_seconds)
    corrected = forward + 0.5 * (state - backward)
    state_min = jnp.min(state, axis=(-2, -1), keepdims=True)
    state_max = jnp.max(state, axis=(-2, -1), keepdims=True)
    return jnp.clip(corrected, state_min, state_max)


def spectral_longitude_shift(
    state: jax.Array,
    displacement_cells: jax.Array,
) -> jax.Array:
    """Shift fields along periodic longitude with an exact Fourier phase factor."""
    state = jnp.asarray(state)
    displacement_cells = jnp.asarray(displacement_cells, dtype=state.dtype)
    assert state.ndim == 4
    assert displacement_cells.shape == (state.shape[0], state.shape[-1])

    longitude_count = state.shape[-2]
    wave_numbers = jnp.fft.rfftfreq(longitude_count) * longitude_count
    phase_angle = (
        -2.0
        * jnp.pi
        * wave_numbers[jnp.newaxis, jnp.newaxis, :, jnp.newaxis]
        * displacement_cells[:, jnp.newaxis, jnp.newaxis, :]
        / longitude_count
    )
    phase = jnp.cos(phase_angle) + 1j * jnp.sin(phase_angle)
    coefficients = jnp.fft.rfft(state, axis=-2)
    shifted = jnp.fft.irfft(
        coefficients * phase,
        n=longitude_count,
        axis=-2,
    )
    return shifted.astype(state.dtype)


def scale_selective_longitude_filter(
    values: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    reference_wave_number: float,
    damping_power: float,
    latitude_aware: bool = False,
) -> jax.Array:
    """Damp short zonal waves faster than planetary-scale waves."""
    values = jnp.asarray(values)
    assert values.ndim >= 3
    assert values.shape[0] == len(lead_steps)
    assert reference_wave_number > 0
    assert damping_power > 0

    coefficients = jnp.fft.rfft(values, axis=-2)
    wave_numbers = jnp.arange(coefficients.shape[-2], dtype=values.dtype)
    if latitude_aware:
        latitudes = latitude_radians(values.shape[-1], values.dtype)
        cos_latitudes = jnp.maximum(jnp.abs(jnp.cos(latitudes)), MIN_COS_LATITUDE)
        effective_wave_numbers = wave_numbers[:, jnp.newaxis] / cos_latitudes
        damping_rate = (effective_wave_numbers / reference_wave_number) ** damping_power
    else:
        damping_rate = (wave_numbers / reference_wave_number) ** damping_power
    lead_days = (
        jnp.asarray(lead_steps, dtype=values.dtype)
        * jnp.asarray(step_seconds, dtype=values.dtype)
        / 86_400.0
    )
    lead_shape = (lead_days.shape[0],) + (1,) * (coefficients.ndim - 1)
    if damping_rate.ndim == 1:
        damping_rate_shape = (1,) * (coefficients.ndim - 2) + (
            coefficients.shape[-2],
            1,
        )
    else:
        damping_rate_shape = (1,) * (coefficients.ndim - 2) + tuple(damping_rate.shape)
    damping = jnp.exp(
        -jnp.reshape(lead_days, lead_shape)
        * jnp.reshape(damping_rate, damping_rate_shape)
    )
    filtered = jnp.fft.irfft(
        coefficients * damping,
        n=values.shape[-2],
        axis=-2,
    )
    return filtered.astype(values.dtype)


def scale_selective_latitude_filter(
    values: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    reference_wave_number: float,
    damping_power: float,
) -> jax.Array:
    """Damp short meridional waves using a reflecting-boundary spectrum."""
    values = jnp.asarray(values)
    assert values.ndim >= 3
    assert values.shape[0] == len(lead_steps)
    assert reference_wave_number > 0
    assert damping_power > 0

    latitude_count = values.shape[-1]
    reflected_interior = values[..., 1:-1][..., ::-1]
    reflected_values = jnp.concatenate([values, reflected_interior], axis=-1)
    coefficients = jnp.fft.rfft(reflected_values, axis=-1)
    wave_numbers = jnp.arange(coefficients.shape[-1], dtype=values.dtype)
    damping_rate = (wave_numbers / reference_wave_number) ** damping_power
    lead_days = (
        jnp.asarray(lead_steps, dtype=values.dtype)
        * jnp.asarray(step_seconds, dtype=values.dtype)
        / 86_400.0
    )
    lead_shape = (lead_days.shape[0],) + (1,) * (coefficients.ndim - 1)
    wave_shape = (1,) * (coefficients.ndim - 1) + (coefficients.shape[-1],)
    damping = jnp.exp(
        -jnp.reshape(lead_days, lead_shape) * jnp.reshape(damping_rate, wave_shape)
    )
    filtered = jnp.fft.irfft(
        coefficients * damping,
        n=reflected_values.shape[-1],
        axis=-1,
    )
    return filtered[..., :latitude_count].astype(values.dtype)


def scale_selective_horizontal_cross_filter(
    values: jax.Array,
    lead_steps: tuple[int, ...],
    step_seconds: float,
    *,
    reference_wave_number: float,
    latitude_aware: bool = False,
) -> jax.Array:
    """Damp diagonal small scales from the biharmonic cross term."""
    values = jnp.asarray(values)
    assert values.ndim >= 3
    assert values.shape[0] == len(lead_steps)
    assert reference_wave_number > 0

    latitude_count = values.shape[-1]
    reflected_interior = values[..., 1:-1][..., ::-1]
    reflected_values = jnp.concatenate([values, reflected_interior], axis=-1)
    coefficients = jnp.fft.fftn(reflected_values, axes=(-2, -1))
    longitude_waves = (
        jnp.fft.fftfreq(reflected_values.shape[-2]) * (reflected_values.shape[-2])
    )
    latitude_waves = (
        jnp.fft.fftfreq(reflected_values.shape[-1]) * (reflected_values.shape[-1])
    )
    if latitude_aware:
        latitudes = latitude_radians(latitude_count, values.dtype)
        reflected_latitudes = jnp.concatenate([latitudes, latitudes[1:-1][::-1]])
        cos_latitudes = jnp.maximum(
            jnp.abs(jnp.cos(reflected_latitudes)), MIN_COS_LATITUDE
        )
        longitude_squared = (longitude_waves[:, jnp.newaxis] / cos_latitudes) ** 2
    else:
        longitude_squared = (
            longitude_waves[:, jnp.newaxis] * longitude_waves[:, jnp.newaxis]
        )
    latitude_squared = latitude_waves[jnp.newaxis, :] * latitude_waves[jnp.newaxis, :]
    damping_rate = (
        2.0
        * longitude_squared
        * latitude_squared
        / (reference_wave_number * reference_wave_number) ** 2
    )
    lead_days = (
        jnp.asarray(lead_steps, dtype=values.dtype)
        * jnp.asarray(step_seconds, dtype=values.dtype)
        / 86_400.0
    )
    lead_shape = (lead_days.shape[0],) + (1,) * (coefficients.ndim - 1)
    rate_shape = (1,) * (coefficients.ndim - 2) + tuple(damping_rate.shape)
    damping = jnp.exp(
        -jnp.reshape(lead_days, lead_shape) * jnp.reshape(damping_rate, rate_shape)
    )
    filtered = jnp.fft.ifftn(coefficients * damping, axes=(-2, -1)).real
    return filtered[..., :latitude_count].astype(values.dtype)
