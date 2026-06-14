import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.advected_persistence import (
    AdvectedPersistenceDycoreModel,
    shift_longitude,
)


def test_shift_longitude_moves_values_eastward():
    values = jnp.arange(4, dtype=jnp.float32).reshape((1, 1, 4, 1))

    shifted_values = shift_longitude(values, 1.0)

    expected_values = jnp.asarray([3.0, 0.0, 1.0, 2.0]).reshape((1, 1, 4, 1))
    np.testing.assert_allclose(shifted_values, expected_values)


def test_shift_longitude_interpolates_fractional_cells():
    values = jnp.asarray([0.0, 2.0, 4.0, 6.0]).reshape((1, 1, 4, 1))

    shifted_values = shift_longitude(values, 0.5)

    expected_values = jnp.asarray([3.0, 1.0, 3.0, 5.0]).reshape((1, 1, 4, 1))
    np.testing.assert_allclose(shifted_values, expected_values)


def test_advected_persistence_preserves_zonally_constant_state():
    model = AdvectedPersistenceDycoreModel(jit_forecast=False)
    latitude_profile = jnp.asarray([1.0, 2.0, 3.0], dtype=jnp.float32)
    initial_state = jnp.broadcast_to(latitude_profile, (2, 1, 4, 3))

    forecast = model.forecast(initial_state, (1, 3), 21_600.0)

    assert forecast.shape == (2, 2, 1, 4, 3)
    np.testing.assert_allclose(forecast, jnp.broadcast_to(initial_state, forecast.shape))


def test_advected_persistence_forecast_works_inside_jit():
    model = AdvectedPersistenceDycoreModel()
    initial_state = jnp.arange(2 * 1 * 4 * 3, dtype=jnp.float32).reshape((2, 1, 4, 3))

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 21_600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 1, 4, 3)
    assert jnp.isfinite(forecast).all()


def test_advected_persistence_reuses_forecast_callable():
    model = AdvectedPersistenceDycoreModel()

    assert model.forecast_function is model.forecast_function
