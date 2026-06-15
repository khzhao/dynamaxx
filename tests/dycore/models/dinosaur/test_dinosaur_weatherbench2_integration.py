# Copyright 2026 dynamaxx

import os

import jax.numpy as jnp
import numpy as np
import pytest

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.dycore.models.dinosaur import DinosaurPrimitiveEquationsDycoreModel
from dynamaxx.utils.consts import SECONDS_PER_HOUR
from dynamaxx.weather import ForecastInput, WeatherState

pytestmark = [
    pytest.mark.integration,
    pytest.mark.s3,
    pytest.mark.skipif(
        os.environ.get("DYNAMAXX_RUN_S3_TESTS") != "1",
        reason="set DYNAMAXX_RUN_S3_TESTS=1 to run real S3 tests",
    ),
]


def test_dinosaur_real_weatherbench2_rollout_smoke():
    """The vendored Dinosaur dycore runs on one real WeatherBench2 rollout."""
    initial_time = np.datetime64("2016-01-01T00:00:00", "ns")
    input_channels = (
        "temperature_250",
        "temperature_850",
        "u_component_of_wind_250",
        "u_component_of_wind_850",
        "v_component_of_wind_250",
        "v_component_of_wind_850",
        "mean_sea_level_pressure",
    )
    output_channels = (
        "temperature_250",
        "temperature_850",
        "u_component_of_wind_250",
        "v_component_of_wind_850",
        "mean_sea_level_pressure",
    )
    source = WeatherBench2Source()
    longitude, latitude = source.spatial_coordinates(time=initial_time)
    initial_values = source.read_state(initial_time, channels=input_channels)
    forecast_input = ForecastInput(
        initial_times=np.asarray([initial_time], dtype="datetime64[ns]"),
        valid_times=np.asarray(
            [[initial_time, initial_time + np.timedelta64(6, "h")]],
            dtype="datetime64[ns]",
        ),
        lead_steps=(0, 1),
        lead_hours=(0, 6),
        step_seconds=6 * SECONDS_PER_HOUR,
        longitude=longitude,
        latitude=latitude,
        initial_state=WeatherState(
            values=initial_values[jnp.newaxis, ...],
            variables=input_channels,
        ),
    )

    forecast = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=SECONDS_PER_HOUR,
        output_variables=output_channels,
        include_vertical_advection=False,
        jit_forecast=False,
    ).forecast(forecast_input)

    assert forecast.variables == output_channels
    assert forecast.values.shape == (2, 1, len(output_channels), 240, 121)
    assert bool(jnp.isfinite(forecast.values).all())
