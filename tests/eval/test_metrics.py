import jax.numpy as jnp
import numpy as np

from dynamaxx.eval.core import WeatherVariable
from dynamaxx.eval.metrics import area_weighted_mean, score_forecast


def test_area_weighted_mean_averages_last_two_axes():
    values = jnp.asarray([[[1.0, 3.0], [5.0, 7.0]]])
    weights = jnp.asarray([[1.0, 1.0], [1.0, 3.0]])

    mean = area_weighted_mean(values, weights)

    np.testing.assert_allclose(mean, np.array([5.0]))


def test_score_forecast_returns_area_weighted_records():
    truth = jnp.zeros((1, 2, 1, 2, 2))
    forecast = jnp.ones_like(truth) * 2.0
    weights = jnp.ones((2, 2))

    records = score_forecast(
        forecast,
        truth,
        weights,
        model_name="candidate",
        variables=(WeatherVariable("2m_temperature"),),
        lead_hours=(6,),
        persistence_rmse=jnp.asarray([[4.0]]),
    )

    assert len(records) == 1
    assert records[0].model_name == "candidate"
    assert records[0].channel_name == "2m_temperature"
    np.testing.assert_allclose(records[0].rmse, 2.0)
    np.testing.assert_allclose(records[0].mae, 2.0)
    np.testing.assert_allclose(records[0].bias, 2.0)
    np.testing.assert_allclose(records[0].skill_vs_persistence, 0.5)
