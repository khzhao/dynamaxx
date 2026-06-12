import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.persistence import PersistenceDycoreModel, tendency


def test_persistence_tendency_is_zero():
    state = jnp.arange(2 * 3 * 4, dtype=jnp.float32).reshape((2, 3, 4))

    state_tendency = tendency(state, 0.0)

    np.testing.assert_allclose(state_tendency, jnp.zeros_like(state))


def test_persistence_forecast_returns_requested_leads_as_persistence():
    model = PersistenceDycoreModel(jit_forecast=False)
    initial_state = jnp.arange(2 * 1 * 4 * 3, dtype=jnp.float32).reshape((2, 1, 4, 3))

    forecast = model.forecast(
        initial_state,
        (0, 1, 3),
        600.0,
    )

    assert forecast.shape == (3, 2, 1, 4, 3)
    np.testing.assert_allclose(forecast[0], initial_state)
    np.testing.assert_allclose(forecast[1], initial_state)
    np.testing.assert_allclose(forecast[2], initial_state)


def test_persistence_forecast_works_inside_jit():
    model = PersistenceDycoreModel()
    initial_state = jnp.ones((2, 1, 4, 3), dtype=jnp.float32)

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 1, 4, 3)
    np.testing.assert_allclose(forecast, jnp.ones_like(forecast))


def test_persistence_reuses_simulate_callable():
    model = PersistenceDycoreModel()

    assert model.simulate is model.simulate
