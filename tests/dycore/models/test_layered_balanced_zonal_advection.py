import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.layered_balanced_zonal_advection import (
    LayeredBalancedZonalAdvectionDycoreModel,
    unique_indices,
)


def test_unique_indices_preserves_first_seen_order():
    assert unique_indices((2, 1, 2, 3, 1)) == (2, 1, 3)


def test_layered_balanced_zonal_advection_keeps_temperature_channel_fixed():
    model = LayeredBalancedZonalAdvectionDycoreModel(jit_forecast=False)
    initial_state = jnp.arange(1 * 20 * 8 * 5, dtype=jnp.float32).reshape((1, 20, 8, 5))

    forecast = model.forecast(initial_state, (0, 1, 2), 21_600.0)

    assert forecast.shape == (3, 1, 20, 8, 5)
    expected_temperature = jnp.broadcast_to(
        initial_state[jnp.newaxis, :, 0],
        forecast[:, :, 0].shape,
    )
    np.testing.assert_allclose(forecast[:, :, 0], expected_temperature)


def test_layered_balanced_zonal_advection_forecast_works_inside_jit():
    model = LayeredBalancedZonalAdvectionDycoreModel()
    initial_state = jnp.arange(2 * 20 * 6 * 5, dtype=jnp.float32).reshape((2, 20, 6, 5))

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 21_600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 20, 6, 5)
    assert jnp.isfinite(forecast).all()


def test_layered_balanced_zonal_advection_reuses_forecast_callable():
    model = LayeredBalancedZonalAdvectionDycoreModel()

    assert model.forecast_function is model.forecast_function
