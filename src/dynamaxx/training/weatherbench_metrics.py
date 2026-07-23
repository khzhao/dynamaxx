# Copyright 2026 dynamaxx

"""WeatherBench2-compatible physical validation metrics during training."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import jax
import jax.numpy as jnp
import numpy as np

WEATHERBENCH2_HEADLINE_CHANNELS = (
    "2m_temperature",
    "mean_sea_level_pressure",
    "geopotential_500",
    "temperature_850",
    "specific_humidity_700",
    "u_component_of_wind_850",
    "v_component_of_wind_850",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
)


def weatherbench2_error_components(
    forecast: jax.Array,
    truth: jax.Array,
    area_weights: jax.Array,
    *,
    channel_names: tuple[str, ...],
    reported_channels: tuple[str, ...],
    lead_hours: tuple[int, ...],
) -> dict[str, jax.Array]:
    """Return WB2 global MSE and bias averaged over examples and grid cells.

    Forecast and truth use ``(example, lead, channel, longitude, latitude)``.
    The returned MSE is deliberately not square-rooted until all validation
    batches have been combined, matching WeatherBench2's recommended ordering.
    """
    forecast = jnp.asarray(forecast)
    truth = jnp.asarray(truth)
    area_weights = jnp.asarray(area_weights, dtype=forecast.dtype)
    if forecast.shape != truth.shape:
        raise ValueError("forecast and truth must have identical shapes")
    if forecast.ndim != 5:
        raise ValueError("forecast and truth must have five dimensions")
    if forecast.shape[1] != len(lead_hours):
        raise ValueError("lead_hours do not match the forecast lead axis")
    if forecast.shape[2] != len(channel_names):
        raise ValueError("channel_names do not match the forecast channel axis")
    if area_weights.shape != forecast.shape[-2:]:
        raise ValueError("area_weights do not match the forecast spatial axes")

    channel_to_index = {
        channel_name: channel_index
        for channel_index, channel_name in enumerate(channel_names)
    }
    missing_channels = tuple(
        channel_name
        for channel_name in reported_channels
        if channel_name not in channel_to_index
    )
    if missing_channels:
        raise ValueError(f"reported channels are unavailable: {missing_channels}")
    channel_indices = np.asarray(
        [channel_to_index[channel_name] for channel_name in reported_channels],
        dtype=np.int32,
    )
    error = forecast[:, :, channel_indices] - truth[:, :, channel_indices]
    normalized_weights = area_weights / jnp.sum(area_weights)
    spatial_bias = jnp.sum(
        error * normalized_weights,
        axis=(-2, -1),
    )
    spatial_mse = jnp.sum(
        jnp.square(error) * normalized_weights,
        axis=(-2, -1),
    )
    mean_bias = jnp.mean(spatial_bias, axis=0)
    mean_mse = jnp.mean(spatial_mse, axis=0)

    metrics: dict[str, jax.Array] = {}
    for lead_index, lead_hour in enumerate(lead_hours):
        for channel_index, channel_name in enumerate(reported_channels):
            suffix = f"{channel_name}/{int(lead_hour)}h"
            metrics[f"weatherbench2/bias/{suffix}"] = mean_bias[
                lead_index,
                channel_index,
            ]
            metrics[f"weatherbench2/mse/{suffix}"] = mean_mse[
                lead_index,
                channel_index,
            ]
    return metrics


@dataclass(frozen=True)
class WeatherBenchValidationMetrics:
    """Convert cached truth if needed and compute comparable WB2 components."""

    to_nodal: Callable[[jax.Array], jax.Array]
    area_weights: Any
    channel_names: tuple[str, ...]
    reported_channels: tuple[str, ...] = WEATHERBENCH2_HEADLINE_CHANNELS

    def __post_init__(self):
        channel_names = tuple(map(str, self.channel_names))
        reported_channels = tuple(map(str, self.reported_channels))
        if not channel_names or not reported_channels:
            raise ValueError("metric channel lists must not be empty")
        missing_channels = set(reported_channels).difference(channel_names)
        if missing_channels:
            raise ValueError(
                f"reported channels are unavailable: {sorted(missing_channels)}"
            )
        object.__setattr__(self, "channel_names", channel_names)
        object.__setattr__(self, "reported_channels", reported_channels)

    def score(
        self,
        forecast: jax.Array,
        truth: jax.Array,
        *,
        targets_are_modal: bool,
        lead_hours: tuple[int, ...],
    ) -> dict[str, jax.Array]:
        """Return WB2 components for one device-local validation batch."""
        nodal_truth = self.to_nodal(truth) if targets_are_modal else truth
        return weatherbench2_error_components(
            forecast,
            nodal_truth,
            self.area_weights,
            channel_names=self.channel_names,
            reported_channels=self.reported_channels,
            lead_hours=lead_hours,
        )
