# Copyright 2026 dynamaxx

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jax.numpy as jnp
import numpy as np

from dynamaxx.eval.core import EvalBatch, EvalCase, ForecastModel, WeatherState
from dynamaxx.eval.diagnostics import (
    ForecastDiagnostics,
    diagnose_forecast,
    diagnose_metric_records,
)
from dynamaxx.eval.metrics import MetricRecord, score_components, score_states


@dataclass(frozen=True)
class EvaluationResult:
    """Compact result from one evaluation run."""

    case: EvalCase
    model_name: str
    records: tuple[MetricRecord, ...]
    diagnostics: ForecastDiagnostics

    @property
    def primary_score(self) -> float:
        """Return mean candidate skill against persistence across all records."""
        if self.diagnostics.failed:
            return float("-inf")

        skill_values = [
            record.skill_vs_persistence
            for record in self.records
            if record.model_name == self.model_name
            and record.skill_vs_persistence is not None
        ]
        if not skill_values:
            return float("nan")
        return float(np.mean(skill_values))

    def asdict(self) -> dict[str, Any]:
        """Return a JSON-serializable evaluation result."""
        return {
            "case": self.case.asdict(),
            "diagnostics": self.diagnostics.asdict(),
            "model_name": self.model_name,
            "primary_score": self.primary_score,
            "records": [record.asdict() for record in self.records],
        }


def evaluate_batch(model: ForecastModel, batch: EvalBatch) -> EvaluationResult:
    """Evaluate a model on a preloaded batch."""
    case = batch.case
    forecast = model.forecast(batch.forecast_input)
    forecast_diagnostics = diagnose_forecast(forecast.values)
    forecast_targets = forecast.select(case.target_channel_names)
    truth_targets = batch.truth.select(case.target_channel_names)
    initial_targets = batch.forecast_input.initial_state.select(
        case.target_channel_names,
    )
    persistence = persistence_state(
        initial_targets,
        lead_count=len(case.lead_steps),
    )
    persistence_scores = score_components(
        persistence.values,
        truth_targets.values,
        batch.area_weights,
    )
    persistence_rmse = persistence_scores["rmse"]

    records = score_states(
        forecast_targets,
        truth_targets,
        batch.area_weights,
        model_name=model.name,
        variables=case.target_variables,
        lead_hours=case.lead_hours,
        persistence_rmse=persistence_rmse,
    ) + score_states(
        persistence,
        truth_targets,
        batch.area_weights,
        model_name="persistence",
        variables=case.target_variables,
        lead_hours=case.lead_hours,
        persistence_rmse=persistence_rmse,
    )
    metric_diagnostics = diagnose_metric_records(records)
    diagnostics = ForecastDiagnostics(
        issues=forecast_diagnostics.issues + metric_diagnostics.issues,
    )
    return EvaluationResult(
        case=case,
        model_name=model.name,
        records=records,
        diagnostics=diagnostics,
    )


def persistence_state(
    initial_state: WeatherState,
    *,
    lead_count: int,
) -> WeatherState:
    """Return a named persistence trajectory."""
    initial_values = jnp.asarray(initial_state.values)
    target_shape = (lead_count, *initial_values.shape)
    return WeatherState(
        values=jnp.broadcast_to(initial_values[jnp.newaxis], target_shape),
        variables=initial_state.variables,
    )


def write_metric_json(result: EvaluationResult, path: str | Path) -> None:
    """Write an evaluation result as JSON."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(result.asdict(), output_file, indent=2, sort_keys=True)
        output_file.write("\n")


def write_metric_csv(result: EvaluationResult, path: str | Path) -> None:
    """Write metric records as CSV."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [record.asdict() for record in result.records]
    fieldnames = list(rows[0]) if rows else []
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
