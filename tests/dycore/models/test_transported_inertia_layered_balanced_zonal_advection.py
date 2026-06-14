import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.transported_inertia_layered_balanced_zonal_advection import (
    TransportedInertiaLayeredBalancedZonalAdvectionDycoreModel,
    upper_zonal_tendency_correction,
)


def test_upper_zonal_tendency_correction_decays_selected_tendency():
    initial_state = jnp.zeros((1, 8, 4, 3), dtype=jnp.float32)
    initial_state = initial_state.at[:, 2].set(4.0)
    initial_state = initial_state.at[:, 6].set(1.0)

    correction = upper_zonal_tendency_correction(
        initial_state,
        (0, 4),
        21_600.0,
        current_count=4,
        tendency_indices=(2,),
        upper_u_index=0,
        upper_v_index=1,
        wind_scale=0.0,
        max_wind_speed=55.0,
        decay_days=1.0,
    )

    np.testing.assert_allclose(correction[0, :, 2], 3.0)
    np.testing.assert_allclose(correction[1, :, 2], 3.0 * np.exp(-1.0))
    np.testing.assert_allclose(correction[:, :, 0], 0.0)
    np.testing.assert_allclose(correction[:, :, 1], 0.0)
    np.testing.assert_allclose(correction[:, :, 3], 0.0)


def test_transported_inertia_layered_balanced_zonal_advection_keeps_temperature_fixed():
    model = TransportedInertiaLayeredBalancedZonalAdvectionDycoreModel(
        jit_forecast=False
    )
    initial_state = jnp.arange(1 * 20 * 8 * 5, dtype=jnp.float32).reshape((1, 20, 8, 5))

    forecast = model.forecast(initial_state, (0, 1, 2), 21_600.0)

    assert forecast.shape == (3, 1, 20, 8, 5)
    expected_temperature = jnp.broadcast_to(
        initial_state[jnp.newaxis, :, 0],
        forecast[:, :, 0].shape,
    )
    np.testing.assert_allclose(forecast[:, :, 0], expected_temperature)


def test_transported_inertia_layered_balanced_zonal_advection_works_inside_jit():
    model = TransportedInertiaLayeredBalancedZonalAdvectionDycoreModel()
    initial_state = jnp.arange(2 * 20 * 6 * 5, dtype=jnp.float32).reshape((2, 20, 6, 5))

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 21_600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 20, 6, 5)
    assert jnp.isfinite(forecast).all()


def test_transported_inertia_layered_balanced_zonal_advection_reuses_callable():
    model = TransportedInertiaLayeredBalancedZonalAdvectionDycoreModel()

    assert model.forecast_function is model.forecast_function
