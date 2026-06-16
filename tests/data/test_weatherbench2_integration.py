import os

import numpy as np
import pytest

from dynamaxx.data.weatherbench2 import WeatherBench2Source

pytestmark = [
    pytest.mark.integration,
    pytest.mark.weatherbench2,
    pytest.mark.skipif(
        os.environ.get("DYNAMAXX_RUN_WEATHERBENCH2_TESTS") != "1",
        reason=(
            "set DYNAMAXX_RUN_WEATHERBENCH2_TESTS=1 to run real WeatherBench2 "
            "tests"
        ),
    ),
]


def test_weatherbench2_real_data_smoke_read():
    source = WeatherBench2Source()

    state = source.read_state(
        np.datetime64("2016-01-01T00:00:00"),
        channels=["2m_temperature"],
    )
    constants = source.read_constants(["land_sea_mask"])

    assert state.shape == (1, 240, 121)
    assert constants.shape == (1, 240, 121)
    assert np.isfinite(np.asarray(state)).all()
    assert np.isfinite(np.asarray(constants)).all()
