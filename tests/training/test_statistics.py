from types import SimpleNamespace

import jax.numpy as jnp
import numpy as np

from dynamaxx.training.data import SampledTrajectory
from dynamaxx.training.statistics import (
    estimate_training_statistics,
    load_training_statistics,
    save_training_statistics,
)
from dynamaxx.weather import WeatherState


class _StatisticsCore:
    input_feature_count = 2
    coords = SimpleNamespace(
        horizontal=SimpleNamespace(
            to_modal=lambda values: values,
            modal_mesh=(jnp.zeros((2, 2)), jnp.asarray([[0, 1], [1, 1]])),
            mask=jnp.ones((2, 2)),
        )
    )

    def initialize(self, weather_state, initial_time):
        del initial_time
        return weather_state.values

    def corrector_inputs(self, state):
        field = state[0]
        return jnp.stack((field, 2.0 * field), axis=-1)


class _StatisticsSampler:
    def sample(self, sample_count):
        assert sample_count == 2
        initial_values = jnp.asarray(
            [
                [[[1.0, 2.0], [3.0, 4.0]]],
                [[[2.0, 4.0], [6.0, 8.0]]],
            ]
        )
        return SampledTrajectory(
            initial_times=np.asarray(
                ["2018-01-01", "2018-01-02"],
                dtype="datetime64[ns]",
            ),
            initial_state=WeatherState(values=initial_values, variables=("x",)),
            targets=WeatherState(
                values=initial_values[:, jnp.newaxis],
                variables=("x",),
            ),
            lead_hours=(6,),
        )


def test_training_statistics_estimation_and_local_archive_round_trip(tmp_path):
    statistics = estimate_training_statistics(
        _StatisticsCore(),
        _StatisticsSampler(),
        sample_count=2,
    )
    path = tmp_path / "statistics.npz"

    save_training_statistics(path, statistics)
    restored = load_training_statistics(path)

    np.testing.assert_allclose(statistics.input_mean, [3.75, 7.5])
    assert bool(jnp.all(statistics.input_standard_deviation > 0.0))
    np.testing.assert_allclose(restored.input_mean, statistics.input_mean)
    np.testing.assert_allclose(
        restored.spectral.coefficient_variance,
        statistics.spectral.coefficient_variance,
    )
    assert restored.input_variables == ("x",)
    assert restored.target_variables == ("x",)
