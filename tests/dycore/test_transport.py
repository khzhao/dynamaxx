# Copyright 2026 dynamaxx

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.transport import (
    scale_selective_horizontal_cross_filter,
    scale_selective_latitude_filter,
    scale_selective_longitude_filter,
    semi_lagrangian_advect,
    semi_lagrangian_advect_corrected,
    spectral_longitude_shift,
)


def test_corrected_advection_preserves_state_without_wind():
    """Corrected semi-Lagrangian advection is identity with zero wind."""
    state = jnp.arange(2 * 3 * 8 * 5, dtype=jnp.float32).reshape((2, 3, 8, 5))
    u_wind = jnp.zeros((2, 8, 5), dtype=jnp.float32)
    v_wind = jnp.zeros((2, 8, 5), dtype=jnp.float32)

    advected = semi_lagrangian_advect_corrected(
        state,
        u_wind,
        v_wind,
        jnp.asarray(21_600.0, dtype=jnp.float32),
    )

    np.testing.assert_allclose(advected, state)


def test_corrected_advection_reduces_bilinear_diffusion_for_fractional_shift():
    """The reversible corrector sharpens a fractional shift without overshoot."""
    state = jnp.zeros((1, 1, 16, 7), dtype=jnp.float32)
    state = state.at[:, :, 7:9, 3].set(1.0)
    u_wind = jnp.full((1, 16, 7), 7.73, dtype=jnp.float32)
    v_wind = jnp.zeros((1, 16, 7), dtype=jnp.float32)
    step_seconds = jnp.asarray(21_600.0, dtype=jnp.float32)

    plain = semi_lagrangian_advect(state, u_wind, v_wind, step_seconds)
    corrected = semi_lagrangian_advect_corrected(state, u_wind, v_wind, step_seconds)

    assert jnp.max(corrected) >= jnp.max(plain)
    assert jnp.min(corrected) >= jnp.min(state)
    assert jnp.max(corrected) <= jnp.max(state)


def test_corrected_advection_works_inside_jit():
    """Corrected advection is compatible with JAX compilation."""
    state = jnp.arange(1 * 2 * 6 * 5, dtype=jnp.float32).reshape((1, 2, 6, 5))
    u_wind = jnp.ones((1, 6, 5), dtype=jnp.float32)
    v_wind = jnp.zeros((1, 6, 5), dtype=jnp.float32)

    advected = jax.jit(
        lambda values: semi_lagrangian_advect_corrected(
            values,
            u_wind,
            v_wind,
            jnp.asarray(21_600.0, dtype=jnp.float32),
        )
    )(state)

    assert advected.shape == state.shape
    assert jnp.isfinite(advected).all()


def test_spectral_longitude_shift_matches_integer_roll():
    """A one-cell spectral longitude shift matches a periodic roll."""
    state = jnp.arange(2 * 3 * 16 * 5, dtype=jnp.float32).reshape((2, 3, 16, 5))
    displacement = jnp.ones((2, 5), dtype=jnp.float32)

    shifted = spectral_longitude_shift(state, displacement)

    np.testing.assert_allclose(shifted, jnp.roll(state, shift=1, axis=-2), atol=1e-4)


def test_scale_selective_longitude_filter_damps_shorter_waves_first():
    """Scale-selective filtering preserves long waves more than short waves."""
    longitude = jnp.arange(16, dtype=jnp.float32)
    long_wave = jnp.sin(2.0 * jnp.pi * longitude / 16.0)
    short_wave = jnp.sin(2.0 * jnp.pi * 4.0 * longitude / 16.0)
    values = (long_wave + short_wave).reshape((1, 1, 16, 1))
    values = jnp.broadcast_to(values, (2, 1, 16, 1))

    filtered = scale_selective_longitude_filter(
        values,
        (0, 4),
        21_600.0,
        reference_wave_number=4.0,
        damping_power=4.0,
    )

    initial_spectrum = jnp.abs(jnp.fft.rfft(filtered[0, 0, :, 0]))
    filtered_spectrum = jnp.abs(jnp.fft.rfft(filtered[1, 0, :, 0]))
    np.testing.assert_allclose(filtered[0], values[0], atol=1e-6)
    assert filtered_spectrum[1] > 0.99 * initial_spectrum[1]
    assert filtered_spectrum[4] < 0.40 * initial_spectrum[4]


def test_scale_selective_longitude_filter_can_use_physical_wavelength():
    """Latitude-aware filtering damps a zonal wave fastest near the poles."""
    longitude = jnp.arange(16, dtype=jnp.float32)
    short_wave = jnp.sin(2.0 * jnp.pi * 4.0 * longitude / 16.0)
    values = short_wave[:, jnp.newaxis] * jnp.ones((1, 9), dtype=jnp.float32)
    values = values.reshape((1, 1, 16, 9))
    values = jnp.broadcast_to(values, (2, 1, 16, 9))

    filtered = scale_selective_longitude_filter(
        values,
        (0, 4),
        21_600.0,
        reference_wave_number=4.0,
        damping_power=4.0,
        latitude_aware=True,
    )

    initial_spectrum = jnp.abs(jnp.fft.rfft(filtered[0, 0], axis=0))
    filtered_spectrum = jnp.abs(jnp.fft.rfft(filtered[1, 0], axis=0))
    np.testing.assert_allclose(filtered[0], values[0], atol=1e-6)
    assert filtered_spectrum[4, 4] > 0.30 * initial_spectrum[4, 4]
    assert filtered_spectrum[4, 0] < 1.0e-3 * initial_spectrum[4, 0]


def test_scale_selective_latitude_filter_damps_shorter_waves_first():
    """Reflecting latitude filter preserves long waves more than short waves."""
    latitude = jnp.arange(17, dtype=jnp.float32)
    long_wave = jnp.cos(jnp.pi * latitude / 16.0)
    short_wave = jnp.cos(4.0 * jnp.pi * latitude / 16.0)
    values = (long_wave + short_wave).reshape((1, 1, 1, 17))
    values = jnp.broadcast_to(values, (2, 1, 1, 17))

    filtered = scale_selective_latitude_filter(
        values,
        (0, 4),
        21_600.0,
        reference_wave_number=4.0,
        damping_power=4.0,
    )

    initial_spectrum = jnp.abs(
        jnp.fft.rfft(
            jnp.concatenate([filtered[0, 0, 0], filtered[0, 0, 0, 1:-1][::-1]])
        )
    )
    filtered_spectrum = jnp.abs(
        jnp.fft.rfft(
            jnp.concatenate([filtered[1, 0, 0], filtered[1, 0, 0, 1:-1][::-1]])
        )
    )
    np.testing.assert_allclose(filtered[0], values[0], atol=1e-6)
    assert filtered_spectrum[1] > 0.99 * initial_spectrum[1]
    assert filtered_spectrum[4] < 0.40 * initial_spectrum[4]


def test_scale_selective_horizontal_cross_filter_damps_diagonal_waves():
    """Cross filtering damps waves that vary in both horizontal directions."""
    longitude = jnp.arange(16, dtype=jnp.float32)
    latitude = jnp.arange(17, dtype=jnp.float32)
    zonal_wave = jnp.sin(2.0 * jnp.pi * 4.0 * longitude / 16.0)[:, jnp.newaxis]
    meridional_wave = jnp.cos(4.0 * jnp.pi * latitude / 16.0)[jnp.newaxis, :]
    diagonal_wave = zonal_wave * meridional_wave
    values = (zonal_wave + meridional_wave + diagonal_wave).reshape((1, 1, 16, 17))
    values = jnp.broadcast_to(values, (2, 1, 16, 17))

    filtered = scale_selective_horizontal_cross_filter(
        values,
        (0, 4),
        21_600.0,
        reference_wave_number=4.0,
    )

    reflected_initial = jnp.concatenate(
        [filtered[0, 0], filtered[0, 0, :, 1:-1][:, ::-1]],
        axis=-1,
    )
    reflected_filtered = jnp.concatenate(
        [filtered[1, 0], filtered[1, 0, :, 1:-1][:, ::-1]],
        axis=-1,
    )
    initial_spectrum = jnp.abs(jnp.fft.fftn(reflected_initial))
    filtered_spectrum = jnp.abs(jnp.fft.fftn(reflected_filtered))
    np.testing.assert_allclose(filtered[0], values[0], atol=1e-6)
    assert filtered_spectrum[4, 0] > 0.99 * initial_spectrum[4, 0]
    assert filtered_spectrum[0, 4] > 0.99 * initial_spectrum[0, 4]
    assert filtered_spectrum[4, 4] < 0.20 * initial_spectrum[4, 4]


def test_scale_selective_horizontal_cross_filter_can_use_physical_wavelength():
    """Latitude-aware cross filtering damps diagonal coefficients more strongly."""
    longitude = jnp.arange(16, dtype=jnp.float32)
    latitude = jnp.arange(17, dtype=jnp.float32)
    diagonal_wave = (
        jnp.sin(2.0 * jnp.pi * 4.0 * longitude / 16.0)[:, jnp.newaxis]
        * jnp.cos(4.0 * jnp.pi * latitude / 16.0)[jnp.newaxis, :]
    )
    values = diagonal_wave.reshape((1, 1, 16, 17))
    values = jnp.broadcast_to(values, (2, 1, 16, 17))

    filtered = scale_selective_horizontal_cross_filter(
        values,
        (0, 4),
        21_600.0,
        reference_wave_number=4.0,
    )
    latitude_aware_filtered = scale_selective_horizontal_cross_filter(
        values,
        (0, 4),
        21_600.0,
        reference_wave_number=4.0,
        latitude_aware=True,
    )

    reflected_filtered = jnp.concatenate(
        [filtered[1, 0], filtered[1, 0, :, 1:-1][:, ::-1]],
        axis=-1,
    )
    reflected_latitude_aware = jnp.concatenate(
        [
            latitude_aware_filtered[1, 0],
            latitude_aware_filtered[1, 0, :, 1:-1][:, ::-1],
        ],
        axis=-1,
    )
    filtered_spectrum = jnp.abs(jnp.fft.fftn(reflected_filtered))
    latitude_aware_spectrum = jnp.abs(jnp.fft.fftn(reflected_latitude_aware))
    np.testing.assert_allclose(latitude_aware_filtered[0], values[0], atol=1e-6)
    assert latitude_aware_spectrum[4, 4] < 0.5 * filtered_spectrum[4, 4]
