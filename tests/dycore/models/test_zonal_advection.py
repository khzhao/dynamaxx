# Copyright 2026 dynamaxx

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.zonal_advection import (
    ZonalAdvectionDycoreModel,
    shift_variable_group,
    zonal_cell_displacement,
    zonal_phase_displacement,
)


def test_zonal_cell_displacement_uses_zonal_mean_wind():
    """Zonal displacement should use the longitude-mean wind at each latitude."""
    u_wind = jnp.ones((2, 8, 5), dtype=jnp.float32)
    displacement = zonal_cell_displacement(
        u_wind,
        jnp.asarray(21_600.0, dtype=jnp.float32),
    )

    assert displacement.shape == (2, 5)
    assert jnp.all(displacement > 0)
    np.testing.assert_allclose(displacement[0], displacement[1])


def test_shift_variable_group_only_updates_requested_channels():
    """Variable-group shifting should leave unrelated channels unchanged."""
    state = jnp.arange(1 * 4 * 8 * 3, dtype=jnp.float32).reshape((1, 4, 8, 3))
    displacement = jnp.ones((1, 3), dtype=jnp.float32)

    shifted = shift_variable_group(
        state,
        variable_indices=(1, 3),
        displacement_cells=displacement,
    )

    np.testing.assert_allclose(shifted[:, 0], state[:, 0])
    np.testing.assert_allclose(shifted[:, 2], state[:, 2])
    np.testing.assert_allclose(shifted[:, 1], jnp.roll(state[:, 1], 1, axis=-2))
    np.testing.assert_allclose(shifted[:, 3], jnp.roll(state[:, 3], 1, axis=-2))


def test_zonal_phase_displacement_tracks_history_shift_within_wind_bound():
    """Phase displacement should recover a clean one-cell history shift."""
    longitude_count = 32
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    previous = jnp.sin(longitude)[jnp.newaxis, :, jnp.newaxis]
    current = jnp.roll(previous, shift=1, axis=-2)
    wind_displacement = jnp.full((1, 1), 2.0, dtype=jnp.float32)

    displacement = zonal_phase_displacement(
        current,
        previous,
        wind_displacement,
    )

    np.testing.assert_allclose(displacement, 1.0, atol=1.0e-5)


def test_zonal_phase_displacement_respects_wind_bound():
    """Phase displacement should stay inside the physical wind displacement."""
    longitude_count = 32
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    previous = jnp.sin(longitude)[jnp.newaxis, :, jnp.newaxis]
    current = jnp.roll(previous, shift=2, axis=-2)
    wind_displacement = jnp.full((1, 1), 0.5, dtype=jnp.float32)

    displacement = zonal_phase_displacement(
        current,
        previous,
        wind_displacement,
    )

    np.testing.assert_allclose(displacement, 0.5, atol=1.0e-6)


def test_zonal_advection_forecast_works_inside_jit():
    """Zonal advection should remain valid inside JAX jit."""
    model = ZonalAdvectionDycoreModel()
    initial_state = jnp.arange(2 * 20 * 6 * 5, dtype=jnp.float32).reshape((2, 20, 6, 5))

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 21_600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 20, 6, 5)
    assert jnp.isfinite(forecast).all()


def test_zonal_advection_reuses_forecast_callable():
    """Forecast callable should be cached per model instance."""
    model = ZonalAdvectionDycoreModel()

    assert model.forecast_function is model.forecast_function
