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
    spatial_anomaly_correlation: float | None = None
    spatial_variance_ratio: float | None = None
    structure_score: float | None = None
    structure_skill_vs_persistence: float | None = None
    zonal_eddy_correlation: float | None = None
    zonal_eddy_variance_ratio: float | None = None
    zonal_eddy_score: float | None = None
    zonal_eddy_skill_vs_persistence: float | None = None

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
            "spatial_anomaly_correlation": self.spatial_anomaly_correlation,
            "spatial_variance_ratio": self.spatial_variance_ratio,
            "structure_score": self.structure_score,
            "structure_skill_vs_persistence": self.structure_skill_vs_persistence,
            "zonal_eddy_correlation": self.zonal_eddy_correlation,
            "zonal_eddy_variance_ratio": self.zonal_eddy_variance_ratio,
            "zonal_eddy_score": self.zonal_eddy_score,
            "zonal_eddy_skill_vs_persistence": self.zonal_eddy_skill_vs_persistence,
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
    anomaly_covariance_sum: float
    forecast_anomaly_variance_sum: float
    truth_anomaly_variance_sum: float
    zonal_eddy_covariance_sum: float
    forecast_zonal_eddy_variance_sum: float
    truth_zonal_eddy_variance_sum: float

    @property
    def key(self) -> tuple[str, str, int]:
        """Return the identity used to combine chunked totals."""
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
            anomaly_covariance_sum=(
                self.anomaly_covariance_sum + other.anomaly_covariance_sum
            ),
            forecast_anomaly_variance_sum=(
                self.forecast_anomaly_variance_sum + other.forecast_anomaly_variance_sum
            ),
            truth_anomaly_variance_sum=(
                self.truth_anomaly_variance_sum + other.truth_anomaly_variance_sum
            ),
            zonal_eddy_covariance_sum=(
                self.zonal_eddy_covariance_sum + other.zonal_eddy_covariance_sum
            ),
            forecast_zonal_eddy_variance_sum=(
                self.forecast_zonal_eddy_variance_sum
                + other.forecast_zonal_eddy_variance_sum
            ),
            truth_zonal_eddy_variance_sum=(
                self.truth_zonal_eddy_variance_sum + other.truth_zonal_eddy_variance_sum
            ),
        )

    @property
    def spatial_anomaly_correlation(self) -> float | None:
        """Return accumulated spatial anomaly correlation."""
        if self.truth_anomaly_variance_sum <= 0:
            return None
        if self.forecast_anomaly_variance_sum <= 0:
            return 0.0
        variance_product = (
            self.forecast_anomaly_variance_sum * self.truth_anomaly_variance_sum
        )
        correlation = self.anomaly_covariance_sum / sqrt(variance_product)
        return max(-1.0, min(1.0, correlation))

    @property
    def spatial_variance_ratio(self) -> float | None:
        """Return forecast-to-truth spatial anomaly standard-deviation ratio."""
        if self.truth_anomaly_variance_sum <= 0:
            return None
        if self.forecast_anomaly_variance_sum <= 0:
            return 0.0
        return sqrt(
            self.forecast_anomaly_variance_sum / self.truth_anomaly_variance_sum
        )

    @property
    def structure_score(self) -> float | None:
        """Return phase-and-amplitude spatial structure score."""
        correlation = self.spatial_anomaly_correlation
        variance_ratio = self.spatial_variance_ratio
        if correlation is None or variance_ratio is None:
            return None
        if variance_ratio <= 0:
            return 0.0
        amplitude_score = min(variance_ratio, 1.0 / variance_ratio)
        return correlation * amplitude_score

    @property
    def zonal_eddy_correlation(self) -> float | None:
        """Return correlation of longitude-varying anomalies."""
        if self.truth_zonal_eddy_variance_sum <= 0:
            return None
        if self.forecast_zonal_eddy_variance_sum <= 0:
            return 0.0
        variance_product = (
            self.forecast_zonal_eddy_variance_sum * self.truth_zonal_eddy_variance_sum
        )
        correlation = self.zonal_eddy_covariance_sum / sqrt(variance_product)
        return max(-1.0, min(1.0, correlation))

    @property
    def zonal_eddy_variance_ratio(self) -> float | None:
        """Return forecast-to-truth zonal-eddy standard-deviation ratio."""
        if self.truth_zonal_eddy_variance_sum <= 0:
            return None
        if self.forecast_zonal_eddy_variance_sum <= 0:
            return 0.0
        return sqrt(
            self.forecast_zonal_eddy_variance_sum / self.truth_zonal_eddy_variance_sum
        )

    @property
    def zonal_eddy_score(self) -> float | None:
        """Return phase-and-amplitude score for longitude-varying eddies."""
        correlation = self.zonal_eddy_correlation
        variance_ratio = self.zonal_eddy_variance_ratio
        if correlation is None or variance_ratio is None:
            return None
        if variance_ratio <= 0:
            return 0.0
        amplitude_score = min(variance_ratio, 1.0 / variance_ratio)
        return correlation * amplitude_score

    def to_record(
        self,
        persistence_rmse: float | None,
        persistence_structure_score: float | None,
        persistence_zonal_eddy_score: float | None,
    ) -> MetricRecord:
        """Convert accumulated sums to one public metric row."""
        assert self.count >= 1
        rmse = sqrt(self.mse_sum / self.count)
        skill = None
        if persistence_rmse is not None and persistence_rmse > 0:
            skill = 1 - rmse / persistence_rmse
        structure_score = self.structure_score
        structure_skill = None
        if structure_score is not None and persistence_structure_score is not None:
            structure_skill = structure_score - persistence_structure_score
        zonal_eddy_score = self.zonal_eddy_score
        zonal_eddy_skill = None
        if zonal_eddy_score is not None and persistence_zonal_eddy_score is not None:
            zonal_eddy_skill = zonal_eddy_score - persistence_zonal_eddy_score
        return MetricRecord(
            model_name=self.model_name,
            variable=self.variable,
            channel_name=self.channel_name,
            lead_hours=self.lead_hours,
            rmse=rmse,
            mae=self.mae_sum / self.count,
            bias=self.bias_sum / self.count,
            skill_vs_persistence=skill,
            spatial_anomaly_correlation=self.spatial_anomaly_correlation,
            spatial_variance_ratio=self.spatial_variance_ratio,
            structure_score=structure_score,
            structure_skill_vs_persistence=structure_skill,
            zonal_eddy_correlation=self.zonal_eddy_correlation,
            zonal_eddy_variance_ratio=self.zonal_eddy_variance_ratio,
            zonal_eddy_score=zonal_eddy_score,
            zonal_eddy_skill_vs_persistence=zonal_eddy_skill,
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
    forecast = jnp.asarray(forecast)
    truth = jnp.asarray(truth)
    error = forecast - truth
    forecast_anomaly = forecast - jnp.reshape(
        area_weighted_mean(forecast, area_weights),
        forecast.shape[:-2] + (1, 1),
    )
    truth_anomaly = truth - jnp.reshape(
        area_weighted_mean(truth, area_weights),
        truth.shape[:-2] + (1, 1),
    )
    forecast_zonal_eddy = forecast - jnp.mean(forecast, axis=-2, keepdims=True)
    truth_zonal_eddy = truth - jnp.mean(truth, axis=-2, keepdims=True)
    return {
        "bias": area_weighted_mean(error, area_weights),
        "mae": area_weighted_mean(jnp.abs(error), area_weights),
        "mse": area_weighted_mean(error * error, area_weights),
        "anomaly_covariance": area_weighted_mean(
            forecast_anomaly * truth_anomaly,
            area_weights,
        ),
        "forecast_anomaly_variance": area_weighted_mean(
            forecast_anomaly * forecast_anomaly,
            area_weights,
        ),
        "truth_anomaly_variance": area_weighted_mean(
            truth_anomaly * truth_anomaly,
            area_weights,
        ),
        "zonal_eddy_covariance": area_weighted_mean(
            forecast_zonal_eddy * truth_zonal_eddy,
            area_weights,
        ),
        "forecast_zonal_eddy_variance": area_weighted_mean(
            forecast_zonal_eddy * forecast_zonal_eddy,
            area_weights,
        ),
        "truth_zonal_eddy_variance": area_weighted_mean(
            truth_zonal_eddy * truth_zonal_eddy,
            area_weights,
        ),
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
    anomaly_covariance_sum = np.asarray(
        jnp.sum(components["anomaly_covariance"], axis=1),
    )
    forecast_anomaly_variance_sum = np.asarray(
        jnp.sum(components["forecast_anomaly_variance"], axis=1),
    )
    truth_anomaly_variance_sum = np.asarray(
        jnp.sum(components["truth_anomaly_variance"], axis=1),
    )
    zonal_eddy_covariance_sum = np.asarray(
        jnp.sum(components["zonal_eddy_covariance"], axis=1),
    )
    forecast_zonal_eddy_variance_sum = np.asarray(
        jnp.sum(components["forecast_zonal_eddy_variance"], axis=1),
    )
    truth_zonal_eddy_variance_sum = np.asarray(
        jnp.sum(components["truth_zonal_eddy_variance"], axis=1),
    )
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
                    anomaly_covariance_sum=float(
                        anomaly_covariance_sum[lead_index, variable_index],
                    ),
                    forecast_anomaly_variance_sum=float(
                        forecast_anomaly_variance_sum[lead_index, variable_index],
                    ),
                    truth_anomaly_variance_sum=float(
                        truth_anomaly_variance_sum[lead_index, variable_index],
                    ),
                    zonal_eddy_covariance_sum=float(
                        zonal_eddy_covariance_sum[lead_index, variable_index],
                    ),
                    forecast_zonal_eddy_variance_sum=float(
                        forecast_zonal_eddy_variance_sum[
                            lead_index,
                            variable_index,
                        ],
                    ),
                    truth_zonal_eddy_variance_sum=float(
                        truth_zonal_eddy_variance_sum[lead_index, variable_index],
                    ),
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
    persistence_structure_by_key = {
        (total.channel_name, total.lead_hours): total.structure_score
        for total in persistence_totals
    }
    persistence_zonal_eddy_by_key = {
        (total.channel_name, total.lead_hours): total.zonal_eddy_score
        for total in persistence_totals
    }
    return tuple(
        total.to_record(
            persistence_rmse_by_key.get((total.channel_name, total.lead_hours)),
            persistence_structure_by_key.get((total.channel_name, total.lead_hours)),
            persistence_zonal_eddy_by_key.get((total.channel_name, total.lead_hours)),
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
