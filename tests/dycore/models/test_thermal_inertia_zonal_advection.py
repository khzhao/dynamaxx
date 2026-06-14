import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.thermal_inertia_zonal_advection import (
    ThermalInertiaZonalAdvectionDycoreModel,
    persist_channel,
)


def test_persist_channel_holds_requested_channel_fixed():
    initial_state = jnp.zeros((1, 3, 4, 5), dtype=jnp.float32)
    initial_state = initial_state.at[:, 1].set(2.0)
    forecast = jnp.ones((2, 1, 3, 4, 5), dtype=jnp.float32)

    persisted = persist_channel(forecast, initial_state, channel_index=1)

    np.testing.assert_allclose(persisted[:, :, 0], 1.0)
    np.testing.assert_allclose(persisted[:, :, 1], 2.0)
    np.testing.assert_allclose(persisted[:, :, 2], 1.0)


def test_thermal_inertia_zonal_advection_keeps_temperature_channel_fixed():
    model = ThermalInertiaZonalAdvectionDycoreModel(jit_forecast=False)
    initial_state = jnp.arange(1 * 20 * 8 * 5, dtype=jnp.float32).reshape((1, 20, 8, 5))

    forecast = model.forecast(initial_state, (0, 1, 2), 21_600.0)

    assert forecast.shape == (3, 1, 20, 8, 5)
    expected_temperature = jnp.broadcast_to(
        initial_state[jnp.newaxis, :, 0],
        forecast[:, :, 0].shape,
    )
    np.testing.assert_allclose(forecast[:, :, 0], expected_temperature)


def test_thermal_inertia_zonal_advection_forecast_works_inside_jit():
    model = ThermalInertiaZonalAdvectionDycoreModel()
    initial_state = jnp.arange(2 * 20 * 6 * 5, dtype=jnp.float32).reshape((2, 20, 6, 5))

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 21_600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 20, 6, 5)
    assert jnp.isfinite(forecast).all()


def test_thermal_inertia_zonal_advection_reuses_forecast_callable():
    model = ThermalInertiaZonalAdvectionDycoreModel()

    assert model.forecast_function is model.forecast_function
