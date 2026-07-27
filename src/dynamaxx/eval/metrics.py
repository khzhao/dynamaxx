# Copyright 2026 dynamaxx

from dataclasses import dataclass
from math import sqrt
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


@dataclass(frozen=True)
class MetricTotals:
    """Accumulated metric sums before converting to reported records."""

    model_name: str
    variable: str
    channel_name: str
    lead_hours: int
    count: int
    bias_sum: float
    mae_sum: float
    mse_sum: float

    @property
    def key(self) -> tuple[str, str, int]:
        """The identity used to combine chunked totals."""
        return self.model_name, self.channel_name, self.lead_hours

    def combine(self, other: "MetricTotals") -> "MetricTotals":
        """Return totals accumulated across two disjoint batches."""
        assert self.key == other.key
        assert self.variable == other.variable
        return MetricTotals(
            model_name=self.model_name,
            variable=self.variable,
            channel_name=self.channel_name,
            lead_hours=self.lead_hours,
            count=self.count + other.count,
            bias_sum=self.bias_sum + other.bias_sum,
            mae_sum=self.mae_sum + other.mae_sum,
            mse_sum=self.mse_sum + other.mse_sum,
        )

    def to_record(self, persistence_rmse: float | None) -> MetricRecord:
        """Convert accumulated sums to one public metric row."""
        assert self.count >= 1
        rmse = sqrt(self.mse_sum / self.count)
        skill = None
        if persistence_rmse is not None and persistence_rmse > 0:
            skill = 1 - rmse / persistence_rmse
        return MetricRecord(
            model_name=self.model_name,
            variable=self.variable,
            channel_name=self.channel_name,
            lead_hours=self.lead_hours,
            rmse=rmse,
            mae=self.mae_sum / self.count,
            bias=self.bias_sum / self.count,
            skill_vs_persistence=skill,
        )

    def asdict(self) -> dict[str, Any]:
        """Return a JSON-serializable metric total."""
        return {
            "model_name": self.model_name,
            "variable": self.variable,
            "channel_name": self.channel_name,
            "lead_hours": self.lead_hours,
            "count": self.count,
            "bias_sum": self.bias_sum,
            "mae_sum": self.mae_sum,
            "mse_sum": self.mse_sum,
        }

    @classmethod
    def fromdict(cls, values: dict[str, Any]) -> "MetricTotals":
        """Return metric totals from serialized values."""
        return cls(
            model_name=str(values["model_name"]),
            variable=str(values["variable"]),
            channel_name=str(values["channel_name"]),
            lead_hours=int(values["lead_hours"]),
            count=int(values["count"]),
            bias_sum=float(values["bias_sum"]),
            mae_sum=float(values["mae_sum"]),
            mse_sum=float(values["mse_sum"]),
        )


def area_weighted_mean(values: jax.Array, area_weights: jax.Array) -> jax.Array:
    """Average values over longitude-latitude axes with physical area weights."""
    values = jnp.asarray(values)
    area_weights = jnp.asarray(area_weights, dtype=values.dtype)
    return jnp.sum(values * area_weights, axis=(-2, -1)) / jnp.sum(area_weights)


def score_components_by_initial_time(
    forecast: jax.Array,
    truth: jax.Array,
    area_weights: jax.Array,
) -> dict[str, jax.Array]:
    """Compute area-weighted metrics with shape (lead, init, variable)."""
    error = jnp.asarray(forecast) - jnp.asarray(truth)
    return {
        "bias": area_weighted_mean(error, area_weights),
        "mae": area_weighted_mean(jnp.abs(error), area_weights),
        "mse": area_weighted_mean(error * error, area_weights),
    }


def score_totals(
    forecast: jax.Array,
    truth: jax.Array,
    area_weights: jax.Array,
    *,
    model_name: str,
    variables: tuple[WeatherVariable, ...],
    lead_hours: tuple[int, ...],
) -> tuple[MetricTotals, ...]:
    """Return accumulated metrics for arrays shaped (lead, init, var, lon, lat)."""
    components = score_components_by_initial_time(forecast, truth, area_weights)
    bias_sum = np.asarray(jnp.sum(components["bias"], axis=1))
    mae_sum = np.asarray(jnp.sum(components["mae"], axis=1))
    mse_sum = np.asarray(jnp.sum(components["mse"], axis=1))
    count = int(jnp.asarray(forecast).shape[1])

    totals = []
    for lead_index, lead_hour in enumerate(lead_hours):
        for variable_index, variable in enumerate(variables):
            totals.append(
                MetricTotals(
                    model_name=model_name,
                    variable=variable.label,
                    channel_name=variable.channel_name,
                    lead_hours=int(lead_hour),
                    count=count,
                    bias_sum=float(bias_sum[lead_index, variable_index]),
                    mae_sum=float(mae_sum[lead_index, variable_index]),
                    mse_sum=float(mse_sum[lead_index, variable_index]),
                )
            )
    return tuple(totals)


def merge_totals(metric_totals: tuple[MetricTotals, ...]) -> tuple[MetricTotals, ...]:
    """Merge totals with the same model, channel, and lead."""
    merged: dict[tuple[str, str, int], MetricTotals] = {}
    for total in metric_totals:
        previous = merged.get(total.key)
        merged[total.key] = total if previous is None else previous.combine(total)
    return tuple(merged.values())


def totals_to_records(
    model_totals: tuple[MetricTotals, ...],
    persistence_totals: tuple[MetricTotals, ...],
) -> tuple[MetricRecord, ...]:
    """Convert accumulated model totals to public records with persistence skill."""
    persistence_rmse_by_key = {
        (total.channel_name, total.lead_hours): sqrt(total.mse_sum / total.count)
        for total in persistence_totals
    }
    return tuple(
        total.to_record(
            persistence_rmse_by_key.get((total.channel_name, total.lead_hours)),
        )
        for total in model_totals
    )


def score_state_totals(
    forecast: WeatherState,
    truth: WeatherState,
    area_weights: jax.Array,
    *,
    model_name: str,
    variables: tuple[WeatherVariable, ...],
    lead_hours: tuple[int, ...],
) -> tuple[MetricTotals, ...]:
    """Accumulate named-state metrics for chunked evaluation."""
    channel_names = tuple(variable.channel_name for variable in variables)
    forecast = forecast.select(channel_names)
    truth = truth.select(channel_names)
    return score_totals(
        forecast.values,
        truth.values,
        area_weights,
        model_name=model_name,
        variables=variables,
        lead_hours=lead_hours,
    )
