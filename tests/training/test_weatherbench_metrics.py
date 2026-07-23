# Copyright 2026 dynamaxx

"""Tests for WeatherBench2-compatible training validation metrics."""

import jax.numpy as jnp
import numpy as np

from dynamaxx.training.weatherbench_metrics import weatherbench2_error_components


def test_weatherbench2_components_average_space_then_examples():
    truth = jnp.zeros((2, 1, 1, 2, 2))
    forecast = jnp.asarray(
        [
            [[[[1.0, 1.0], [1.0, 1.0]]]],
            [[[[3.0, 3.0], [3.0, 3.0]]]],
        ]
    )
    metrics = weatherbench2_error_components(
        forecast,
        truth,
        jnp.asarray([[1.0, 1.0], [1.0, 3.0]]),
        channel_names=("temperature_850",),
        reported_channels=("temperature_850",),
        lead_hours=(24,),
    )

    np.testing.assert_allclose(
        metrics["weatherbench2/bias/temperature_850/24h"],
        2.0,
    )
    np.testing.assert_allclose(
        metrics["weatherbench2/mse/temperature_850/24h"],
        5.0,
    )


def test_weatherbench2_components_respect_physical_area_weights():
    truth = jnp.zeros((1, 1, 1, 1, 2))
    forecast = jnp.asarray([[[[[2.0, 4.0]]]]])
    metrics = weatherbench2_error_components(
        forecast,
        truth,
        jnp.asarray([[3.0, 1.0]]),
        channel_names=("geopotential_500",),
        reported_channels=("geopotential_500",),
        lead_hours=(120,),
    )

    np.testing.assert_allclose(
        metrics["weatherbench2/bias/geopotential_500/120h"],
        2.5,
    )
    np.testing.assert_allclose(
        metrics["weatherbench2/mse/geopotential_500/120h"],
        7.0,
    )
