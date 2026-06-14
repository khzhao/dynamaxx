# Copyright 2026 dynamaxx

import csv
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import jax.numpy as jnp
import numpy as np

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.dycore.api import DycoreModel
from dynamaxx.eval.batch import build_weatherbench2_batch
from dynamaxx.eval.core import EvalBatch, EvalCase, WeatherState
from dynamaxx.eval.diagnostics import (
    ForecastDiagnostics,
    diagnose_forecast,
    diagnose_metric_records,
)
from dynamaxx.eval.metrics import (
    MetricRecord,
    MetricTotals,
    merge_totals,
    score_state_totals,
    totals_to_records,
)


@dataclass(frozen=True)
class EvaluationResult:
    """Compact result from one evaluation run."""

    case: EvalCase
    model_name: str
    records: tuple[MetricRecord, ...]
    diagnostics: ForecastDiagnostics

    @property
    def primary_score(self) -> float:
        """Return mean RMSE and spatial-structure skill against persistence."""
        if self.diagnostics.failed:
            return float("-inf")

        skill_values = []
        for record in self.records:
            if (
                record.model_name != self.model_name
                or record.skill_vs_persistence is None
            ):
                continue
            score = record.skill_vs_persistence
            if record.structure_skill_vs_persistence is not None:
                score += record.structure_skill_vs_persistence
            if record.zonal_eddy_skill_vs_persistence is not None:
                score += record.zonal_eddy_skill_vs_persistence
            skill_values.append(score)
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


@dataclass(frozen=True)
class EvaluationTotals:
    """Accumulated model and persistence metrics before record formatting."""

    model_name: str
    model_totals: tuple[MetricTotals, ...]
    persistence_totals: tuple[MetricTotals, ...]
    diagnostics: ForecastDiagnostics


def evaluate_batch(model: DycoreModel, batch: EvalBatch) -> EvaluationResult:
    """Evaluate a model on a preloaded batch."""
    totals = evaluate_batch_totals(model, batch)
    records = totals_to_records(
        totals.model_totals,
        totals.persistence_totals,
    ) + totals_to_records(
        totals.persistence_totals,
        totals.persistence_totals,
    )
    metric_diagnostics = diagnose_metric_records(records)
    diagnostics = ForecastDiagnostics(
        issues=totals.diagnostics.issues + metric_diagnostics.issues,
    )
    return EvaluationResult(
        case=batch.case,
        model_name=model.name,
        records=records,
        diagnostics=diagnostics,
    )


def evaluate_batch_totals(
    model: DycoreModel,
    batch: EvalBatch,
) -> EvaluationTotals:
    """Evaluate one batch and return chunk-combinable metric totals."""
    forecast = batch.forecast_input.initial_state.with_values(
        model.forecast(
            batch.forecast_input.initial_state.values,
            batch.forecast_input.lead_steps,
            batch.forecast_input.step_seconds,
        ),
    )
    forecast_diagnostics = diagnose_forecast(forecast.values)
    forecast_targets = forecast.select(batch.case.target_channel_names)
    truth_targets = batch.truth.select(batch.case.target_channel_names)
    initial_targets = batch.forecast_input.initial_state.select(
        batch.case.target_channel_names,
    )
    persistence = persistence_state(
        initial_targets,
        lead_count=len(batch.case.lead_steps),
    )
    model_totals = score_state_totals(
        forecast_targets,
        truth_targets,
        batch.area_weights,
        model_name=model.name,
        variables=batch.case.target_variables,
        lead_hours=batch.case.lead_hours,
    )
    persistence_totals = score_state_totals(
        persistence,
        truth_targets,
        batch.area_weights,
        model_name="persistence",
        variables=batch.case.target_variables,
        lead_hours=batch.case.lead_hours,
    )
    return EvaluationTotals(
        model_name=model.name,
        model_totals=model_totals,
        persistence_totals=persistence_totals,
        diagnostics=forecast_diagnostics,
    )


def evaluate_case(
    model: DycoreModel,
    source: WeatherBench2Source,
    case: EvalCase,
    *,
    chunk_initial_count: int,
) -> EvaluationResult:
    """Evaluate a case in initialization-time chunks and aggregate metrics."""
    assert chunk_initial_count >= 1
    model_totals = []
    persistence_totals = []
    diagnostic_issues = []

    for chunk_case in case_chunks(case, chunk_initial_count):
        batch = build_weatherbench2_batch(source, chunk_case)
        chunk_totals = evaluate_batch_totals(model, batch)
        model_totals.extend(chunk_totals.model_totals)
        persistence_totals.extend(chunk_totals.persistence_totals)
        diagnostic_issues.extend(chunk_totals.diagnostics.issues)

    merged_model_totals = merge_totals(tuple(model_totals))
    merged_persistence_totals = merge_totals(tuple(persistence_totals))
    records = totals_to_records(
        merged_model_totals,
        merged_persistence_totals,
    ) + totals_to_records(
        merged_persistence_totals,
        merged_persistence_totals,
    )
    metric_diagnostics = diagnose_metric_records(records)
    diagnostics = ForecastDiagnostics(
        issues=tuple(diagnostic_issues) + metric_diagnostics.issues,
    )
    return EvaluationResult(
        case=case,
        model_name=model.name,
        records=records,
        diagnostics=diagnostics,
    )


def case_chunks(case: EvalCase, chunk_initial_count: int) -> tuple[EvalCase, ...]:
    """Split a case into chunks along the initialization-time axis."""
    assert chunk_initial_count >= 1
    return tuple(
        replace(
            case,
            initial_times=case.initial_times[
                start_index : start_index + chunk_initial_count
            ],
        )
        for start_index in range(0, case.initial_times.size, chunk_initial_count)
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
