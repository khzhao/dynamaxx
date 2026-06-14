import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.inertial_layered_balanced_zonal_advection import (
    InertialLayeredBalancedZonalAdvectionDycoreModel,
    add_decaying_tendency,
)


def test_add_decaying_tendency_updates_only_selected_channels():
    forecast = jnp.zeros((2, 1, 8, 3, 2), dtype=jnp.float32)
    initial_state = jnp.zeros((1, 8, 3, 2), dtype=jnp.float32)
    initial_state = initial_state.at[:, 2].set(4.0)
    initial_state = initial_state.at[:, 6].set(1.0)

    corrected = add_decaying_tendency(
        forecast,
        initial_state,
        (0, 4),
        21_600.0,
        current_count=4,
        variable_indices=(2,),
        decay_days=1.0,
    )

    np.testing.assert_allclose(corrected[0, :, 2], 3.0)
    np.testing.assert_allclose(corrected[1, :, 2], 3.0 * np.exp(-1.0))
    np.testing.assert_allclose(corrected[:, :, 0], 0.0)
    np.testing.assert_allclose(corrected[:, :, 1], 0.0)
    np.testing.assert_allclose(corrected[:, :, 3], 0.0)
    np.testing.assert_allclose(corrected[:, :, 4:], 0.0)


def test_inertial_layered_balanced_zonal_advection_keeps_temperature_fixed():
    model = InertialLayeredBalancedZonalAdvectionDycoreModel(jit_forecast=False)
    initial_state = jnp.arange(1 * 20 * 8 * 5, dtype=jnp.float32).reshape((1, 20, 8, 5))

    forecast = model.forecast(initial_state, (0, 1, 2), 21_600.0)

    assert forecast.shape == (3, 1, 20, 8, 5)
    expected_temperature = jnp.broadcast_to(
        initial_state[jnp.newaxis, :, 0],
        forecast[:, :, 0].shape,
    )
    np.testing.assert_allclose(forecast[:, :, 0], expected_temperature)


def test_inertial_layered_balanced_zonal_advection_works_inside_jit():
    model = InertialLayeredBalancedZonalAdvectionDycoreModel()
    initial_state = jnp.arange(2 * 20 * 6 * 5, dtype=jnp.float32).reshape((2, 20, 6, 5))

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 21_600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 20, 6, 5)
    assert jnp.isfinite(forecast).all()


def test_inertial_layered_balanced_zonal_advection_reuses_forecast_callable():
    model = InertialLayeredBalancedZonalAdvectionDycoreModel()

    assert model.forecast_function is model.forecast_function
