import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.wind_advection import (
    WindAdvectionDycoreModel,
    weighted_wind,
)


def test_weighted_wind_uses_requested_channels():
    state = jnp.zeros((1, 6, 4, 3), dtype=jnp.float32)
    state = state.at[:, 1].set(2.0)
    state = state.at[:, 3].set(4.0)
    state = state.at[:, 2].set(-1.0)
    state = state.at[:, 4].set(3.0)

    u_wind, v_wind = weighted_wind(
        state,
        u_indices=(1, 3),
        v_indices=(2, 4),
        weights=(0.25, 0.75),
        wind_scale=2.0,
        max_wind_speed=100.0,
    )

    np.testing.assert_allclose(u_wind, jnp.full((1, 4, 3), 7.0))
    np.testing.assert_allclose(v_wind, jnp.full((1, 4, 3), 4.0))


def test_weighted_wind_clips_speed():
    state = jnp.zeros((1, 2, 4, 3), dtype=jnp.float32)
    state = state.at[:, 0].set(30.0)
    state = state.at[:, 1].set(40.0)

    u_wind, v_wind = weighted_wind(
        state,
        u_indices=(0,),
        v_indices=(1,),
        weights=(1.0,),
        wind_scale=1.0,
        max_wind_speed=10.0,
    )

    speed = jnp.sqrt(u_wind * u_wind + v_wind * v_wind)
    np.testing.assert_allclose(speed, jnp.full((1, 4, 3), 10.0), atol=1e-5)


def test_wind_advection_preserves_state_without_wind_diffusion_or_damping():
    model = WindAdvectionDycoreModel(
        wind_scale=1.0,
        diffusion_per_step=0.0,
        damping_days=1.0e9,
        jit_forecast=False,
    )
    initial_state = jnp.arange(1 * 10 * 4 * 3, dtype=jnp.float32).reshape((1, 10, 4, 3))
    for wind_index in (3, 4, 6, 7, 8, 9):
        initial_state = initial_state.at[:, wind_index].set(0.0)

    forecast = model.forecast(initial_state, (0, 1, 3), 21_600.0)

    assert forecast.shape == (3, 1, 10, 4, 3)
    np.testing.assert_allclose(
        forecast, jnp.broadcast_to(initial_state, forecast.shape)
    )


def test_wind_advection_forecast_works_inside_jit():
    model = WindAdvectionDycoreModel()
    initial_state = jnp.arange(2 * 10 * 6 * 5, dtype=jnp.float32).reshape((2, 10, 6, 5))

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 21_600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 10, 6, 5)
    assert jnp.isfinite(forecast).all()


def test_wind_advection_reuses_forecast_callable():
    model = WindAdvectionDycoreModel()

    assert model.forecast_function is model.forecast_function
