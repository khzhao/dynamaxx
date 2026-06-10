# Copyright 2026 dynamaxx

from dataclasses import dataclass
from typing import Any

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.eval.core import WeatherState, WeatherVariable


@dataclass(frozen=True)
class MetricRecord:
    """One aggregated metric row for a model, variable, and lead time."""

    model_name: str
    variable: str
    channel_name: str
    lead_hours: int
    rmse: float
    mae: float
    bias: float
    skill_vs_persistence: float | None = None

    def asdict(self) -> dict[str, Any]:
        """Return a JSON-serializable metric row."""
        return {
            "model_name": self.model_name,
            "variable": self.variable,
            "channel_name": self.channel_name,
            "lead_hours": self.lead_hours,
            "rmse": self.rmse,
            "mae": self.mae,
            "bias": self.bias,
            "skill_vs_persistence": self.skill_vs_persistence,
        }


def area_weighted_mean(values: jax.Array, area_weights: jax.Array) -> jax.Array:
    """Average values over longitude-latitude axes with physical area weights."""
    values = jnp.asarray(values)
    area_weights = jnp.asarray(area_weights, dtype=values.dtype)
    return jnp.sum(values * area_weights, axis=(-2, -1)) / jnp.sum(area_weights)


def score_components(
    forecast: jax.Array,
    truth: jax.Array,
    area_weights: jax.Array,
) -> dict[str, jax.Array]:
    """Compute area-weighted metric arrays with shape (lead, variable)."""
    error = jnp.asarray(forecast) - jnp.asarray(truth)
    spatial_bias = area_weighted_mean(error, area_weights)
    spatial_mae = area_weighted_mean(jnp.abs(error), area_weights)
    spatial_mse = area_weighted_mean(error * error, area_weights)
    return {
        "bias": jnp.mean(spatial_bias, axis=1),
        "mae": jnp.mean(spatial_mae, axis=1),
        "rmse": jnp.sqrt(jnp.mean(spatial_mse, axis=1)),
    }


def score_forecast(
    forecast: jax.Array,
    truth: jax.Array,
    area_weights: jax.Array,
    *,
    model_name: str,
    variables: tuple[WeatherVariable, ...],
    lead_hours: tuple[int, ...],
    persistence_rmse: jax.Array | None = None,
) -> tuple[MetricRecord, ...]:
    """Return metric records for forecast arrays shaped (lead, init, var, lon, lat)."""
    scores = score_components(forecast, truth, area_weights)
    rmse = np.asarray(scores["rmse"])
    mae = np.asarray(scores["mae"])
    bias = np.asarray(scores["bias"])
    if persistence_rmse is not None:
        persistence_rmse_values = np.asarray(persistence_rmse)
        skill = np.where(
            persistence_rmse_values > 0,
            1 - rmse / persistence_rmse_values,
            np.nan,
        )
    else:
        skill = np.full_like(rmse, np.nan)

    records = []
    for lead_index, lead_hour in enumerate(lead_hours):
        for variable_index, variable in enumerate(variables):
            skill_value = float(skill[lead_index, variable_index])
            records.append(
                MetricRecord(
                    model_name=model_name,
                    variable=variable.label,
                    channel_name=variable.channel_name,
                    lead_hours=int(lead_hour),
                    rmse=float(rmse[lead_index, variable_index]),
                    mae=float(mae[lead_index, variable_index]),
                    bias=float(bias[lead_index, variable_index]),
                    skill_vs_persistence=(
                        None if np.isnan(skill_value) else skill_value
                    ),
                )
            )
    return tuple(records)


def score_states(
    forecast: WeatherState,
    truth: WeatherState,
    area_weights: jax.Array,
    *,
    model_name: str,
    variables: tuple[WeatherVariable, ...],
    lead_hours: tuple[int, ...],
    persistence_rmse: jax.Array | None = None,
) -> tuple[MetricRecord, ...]:
    """Score named forecast and truth states with matching variable order."""
    channel_names = tuple(variable.channel_name for variable in variables)
    forecast = forecast.select(channel_names)
    truth = truth.select(channel_names)
    return score_forecast(
        forecast.values,
        truth.values,
        area_weights,
        model_name=model_name,
        variables=variables,
        lead_hours=lead_hours,
        persistence_rmse=persistence_rmse,
    )
