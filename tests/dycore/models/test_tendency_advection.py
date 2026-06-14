import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.tendency_advection import (
    TendencyAdvectionDycoreModel,
    split_history_state,
)


def test_split_history_state_returns_current_and_previous_channels():
    current = jnp.ones((2, 3, 4, 5), dtype=jnp.float32)
    previous = jnp.zeros((2, 3, 4, 5), dtype=jnp.float32)
    state = jnp.concatenate([current, previous], axis=1)

    split_current, split_previous = split_history_state(state, current_count=3)

    np.testing.assert_allclose(split_current, current)
    np.testing.assert_allclose(split_previous, previous)


def test_tendency_advection_adds_recent_tendency_without_wind():
    model = TendencyAdvectionDycoreModel(
        current_count=10,
        wind_scale=0.0,
        diffusion_per_step=0.0,
        damping_days=1.0e9,
        tendency_scale=1.0,
        tendency_decay_days=1.0e9,
        jit_forecast=False,
    )
    previous = jnp.zeros((1, 10, 4, 3), dtype=jnp.float32)
    current = jnp.ones((1, 10, 4, 3), dtype=jnp.float32)
    initial_state = jnp.concatenate([current, previous], axis=1)

    forecast = model.forecast(initial_state, (0, 1, 2), 21_600.0)

    assert forecast.shape == (3, 1, 20, 4, 3)
    np.testing.assert_allclose(forecast[0], initial_state)
    np.testing.assert_allclose(forecast[1, :, :10], 2.0, atol=1e-5)
    np.testing.assert_allclose(forecast[1, :, 10:], 1.0, atol=1e-5)
    np.testing.assert_allclose(forecast[2, :, :10], 3.0, atol=1e-5)
    np.testing.assert_allclose(forecast[2, :, 10:], 2.0, atol=1e-5)


def test_tendency_advection_forecast_works_inside_jit():
    model = TendencyAdvectionDycoreModel()
    initial_state = jnp.arange(2 * 20 * 6 * 5, dtype=jnp.float32).reshape(
        (2, 20, 6, 5)
    )

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 21_600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 20, 6, 5)
    assert jnp.isfinite(forecast).all()


def test_tendency_advection_reuses_forecast_callable():
    model = TendencyAdvectionDycoreModel()

    assert model.forecast_function is model.forecast_function
