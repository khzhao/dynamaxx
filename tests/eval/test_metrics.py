import jax.numpy as jnp
import numpy as np

from dynamaxx.eval.core import WeatherVariable
from dynamaxx.eval.metrics import (
    area_weighted_mean,
    merge_totals,
    score_totals,
    totals_to_records,
)


def test_area_weighted_mean_averages_last_two_axes():
    values = jnp.asarray([[[1.0, 3.0], [5.0, 7.0]]])
    weights = jnp.asarray([[1.0, 1.0], [1.0, 3.0]])

    mean = area_weighted_mean(values, weights)

    np.testing.assert_allclose(mean, np.array([5.0]))


def test_metric_totals_merge_squared_errors_before_rmse():
    truth = jnp.zeros((1, 1, 1, 1, 1))
    variables = (WeatherVariable("2m_temperature"),)
    first = score_totals(
        jnp.ones_like(truth) * 2.0,
        truth,
        jnp.ones((1, 1)),
        model_name="candidate",
        variables=variables,
        lead_hours=(6,),
    )
    second = score_totals(
        jnp.ones_like(truth) * 4.0,
        truth,
        jnp.ones((1, 1)),
        model_name="candidate",
        variables=variables,
        lead_hours=(6,),
    )

    merged = merge_totals(first + second)
    records = totals_to_records(merged, merged)

    assert len(records) == 1
    np.testing.assert_allclose(records[0].rmse, np.sqrt((4.0 + 16.0) / 2.0))
    assert records[0].skill_vs_persistence is not None
    np.testing.assert_allclose(records[0].skill_vs_persistence, 0.0)
