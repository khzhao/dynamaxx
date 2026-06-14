# Copyright 2026 dynamaxx

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.barotropic_vorticity import (
    BarotropicVorticityDycoreModel,
    barotropic_vorticity_forecast,
    invert_vorticity_to_geopotential,
    relative_vorticity,
)


def test_relative_vorticity_is_zero_for_uniform_wind():
    """Uniform wind should have no resolved relative vorticity."""
    u_wind = jnp.ones((2, 8, 5), dtype=jnp.float32)
    v_wind = -jnp.ones((2, 8, 5), dtype=jnp.float32)

    vorticity = relative_vorticity(u_wind, v_wind)

    np.testing.assert_allclose(vorticity, 0.0, atol=1.0e-7)


def test_vorticity_inversion_returns_zero_mean_geopotential_anomaly():
    """Poisson inversion should return a finite zero-zonal-mean anomaly."""
    longitude_count = 16
    latitude_count = 5
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    vorticity = 1.0e-6 * jnp.sin(longitude)[jnp.newaxis, :, jnp.newaxis]
    vorticity = jnp.broadcast_to(vorticity, (1, longitude_count, latitude_count))

    geopotential = invert_vorticity_to_geopotential(
        vorticity,
        coriolis_scale=1.0e-4,
        reference_latitude_radians=0.75,
    )

    assert geopotential.shape == vorticity.shape
    assert jnp.isfinite(geopotential).all()
    np.testing.assert_allclose(jnp.mean(geopotential, axis=-2), 0.0, atol=1.0e-4)


def test_barotropic_vorticity_forecast_preserves_constant_geopotential():
    """A constant Z500 field should persist because it has no anomaly vorticity."""
    initial_state = jnp.zeros((1, 10, 8, 5), dtype=jnp.float32)
    initial_state = initial_state.at[:, 2].set(50_000.0)

    forecast = barotropic_vorticity_forecast(
        initial_state,
        (0, 1, 2),
        21_600.0,
        current_count=10,
        geopotential_index=2,
        flow_scale=0.02,
        max_wind_speed=60.0,
        vorticity_decay_days=30.0,
        anomaly_weight=1.0,
        coriolis_scale=1.0e-4,
        reference_latitude_radians=0.75,
    )

    np.testing.assert_allclose(forecast[:, :, 2], 50_000.0, atol=1.0e-4)
    np.testing.assert_allclose(forecast[:, :, 0], 0.0, atol=1.0e-6)


def test_barotropic_vorticity_model_has_expected_shape_and_finite_values():
    """Model forecast should preserve full-state shape and finite values."""
    model = BarotropicVorticityDycoreModel(jit_forecast=False)
    initial_state = jnp.zeros((2, 20, 16, 5), dtype=jnp.float32)
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, 16, endpoint=False)
    wave = 50_000.0 + 500.0 * jnp.sin(longitude)[:, jnp.newaxis]
    initial_state = initial_state.at[:, 2].set(wave)

    forecast = model.forecast(initial_state, (0, 1, 3), 21_600.0)

    assert forecast.shape == (3, 2, 20, 16, 5)
    assert jnp.isfinite(forecast).all()


def test_barotropic_vorticity_model_works_inside_jit():
    """Barotropic-vorticity model should remain valid inside JAX jit."""
    model = BarotropicVorticityDycoreModel()
    initial_state = jnp.zeros((2, 20, 16, 5), dtype=jnp.float32)
    initial_state = initial_state.at[:, 2].set(50_000.0)

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 21_600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 20, 16, 5)
    assert jnp.isfinite(forecast).all()


def test_barotropic_vorticity_model_reuses_forecast_callable():
    """Forecast callable should be cached per model instance."""
    model = BarotropicVorticityDycoreModel()

    assert model.forecast_function is model.forecast_function
