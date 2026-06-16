# Copyright 2026 dynamaxx

import csv
import json
import logging
import multiprocessing
import os
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Protocol

import jax.numpy as jnp
import numpy as np

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.eval.batch import build_weatherbench2_batch
from dynamaxx.eval.core import EvalBatch, EvalCase, WeatherState
from dynamaxx.eval.device_dispatch import (
    EvalDeviceDispatch,
    initialize_eval_worker,
    plan_eval_worker_devices,
)
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
from dynamaxx.weather import ForecastInput

logger = logging.getLogger("dynamaxx.eval.runner")


class ForecastModel(Protocol):
    """Forecast model interface required by evaluation."""

    @property
    def name(self) -> str:
        """Stable model name used in metric outputs."""

    def forecast(
        self,
        forecast_input: ForecastInput,
    ) -> WeatherState:
        """Return a named forecast shaped as (lead, init, variable, lon, lat)."""


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


@dataclass(frozen=True)
class EvaluationTotals:
    """Accumulated model and persistence metrics before record formatting."""

    model_name: str
    model_totals: tuple[MetricTotals, ...]
    persistence_totals: tuple[MetricTotals, ...]
    diagnostics: ForecastDiagnostics


def evaluate_batch(model: ForecastModel, batch: EvalBatch) -> EvaluationResult:
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
    model: ForecastModel,
    batch: EvalBatch,
) -> EvaluationTotals:
    """Evaluate one batch and return chunk-combinable metric totals."""
    forecast = model.forecast(batch.forecast_input)
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
    model: ForecastModel,
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
    chunks = case_chunks(case, chunk_initial_count)

    for chunk_index, chunk_case in enumerate(chunks):
        logger.info(
            "Eval chunk %d/%d: starts=%d first=%s last=%s",
            chunk_index + 1,
            len(chunks),
            chunk_case.initial_times.size,
            _format_time(chunk_case.initial_times[0]),
            _format_time(chunk_case.initial_times[-1]),
        )
        batch = build_weatherbench2_batch(source, chunk_case)
        chunk_totals = evaluate_batch_totals(model, batch)
        model_totals.extend(chunk_totals.model_totals)
        persistence_totals.extend(chunk_totals.persistence_totals)
        diagnostic_issues.extend(chunk_totals.diagnostics.issues)
        logger.info(
            "Eval chunk %d/%d complete: issues=%d",
            chunk_index + 1,
            len(chunks),
            len(chunk_totals.diagnostics.issues),
        )

    return _evaluation_result_from_totals(
        case=case,
        model_name=model.name,
        model_totals=tuple(model_totals),
        persistence_totals=tuple(persistence_totals),
        diagnostic_issues=tuple(diagnostic_issues),
    )


def evaluate_case_parallel(
    model_factory: Callable[[], ForecastModel],
    model_name: str,
    source_path: str,
    case: EvalCase,
    *,
    chunk_initial_count: int,
    worker_count: int,
    run_dir: str | Path,
    resume: bool = True,
) -> EvaluationResult:
    """Evaluate a case across initialization-time chunks in worker processes."""
    assert chunk_initial_count >= 1
    assert worker_count >= 1
    run_path = Path(run_dir)
    chunk_path = run_path / "chunks"
    chunk_path.mkdir(parents=True, exist_ok=True)
    chunks = case_chunks(case, chunk_initial_count)
    manifest_values = _parallel_manifest_values(
        model_name=model_name,
        source_path=source_path,
        case=case,
        chunk_initial_count=chunk_initial_count,
        chunk_count=len(chunks),
    )
    device_dispatch = plan_eval_worker_devices(worker_count)
    effective_worker_count = device_dispatch.effective_worker_count
    _prepare_parallel_run(
        run_path,
        manifest_values=manifest_values,
        worker_count=worker_count,
        device_dispatch=device_dispatch,
        resume=resume,
    )
    cached_count = sum(
        1
        for index in range(len(chunks))
        if _chunk_result_path(chunk_path, index).exists()
    )
    logger.info(
        "Parallel eval: chunks=%d cached=%d pending=%d run_dir=%s",
        len(chunks),
        cached_count,
        len(chunks) - cached_count,
        run_path,
    )
    logger.info(
        "Parallel eval device dispatch: mode=%s requested_workers=%d effective_workers=%d gpu_count=%d worker_devices=%s",
        device_dispatch.mode,
        worker_count,
        effective_worker_count,
        device_dispatch.available_gpu_count,
        _format_worker_devices(device_dispatch),
    )

    chunk_results: dict[int, EvaluationTotals] = {}
    jobs = []
    for chunk_index, chunk_case in enumerate(chunks):
        result_path = _chunk_result_path(chunk_path, chunk_index)
        if resume and result_path.exists():
            chunk_results[chunk_index] = _read_chunk_result(
                result_path,
                expected_chunk_index=chunk_index,
            )
            logger.info(
                "Parallel eval chunk %d/%d cached",
                chunk_index + 1,
                len(chunks),
            )
            continue
        jobs.append(
            _ChunkJob(
                model_factory=model_factory,
                source_path=source_path,
                chunk_index=chunk_index,
                chunk_case=chunk_case,
                result_path=result_path,
            )
        )

    if worker_count == 1 and effective_worker_count == 1:
        for job in jobs:
            logger.info(
                "Parallel eval chunk %d/%d started: first=%s last=%s",
                job.chunk_index + 1,
                len(chunks),
                _format_time(job.chunk_case.initial_times[0]),
                _format_time(job.chunk_case.initial_times[-1]),
            )
            chunk_results[job.chunk_index] = _evaluate_chunk_job(job)
            logger.info(
                "Parallel eval chunk %d/%d complete",
                job.chunk_index + 1,
                len(chunks),
            )
    else:
        spawn_context = multiprocessing.get_context("spawn")
        worker_slot_queue = spawn_context.Queue()
        for worker_slot in range(effective_worker_count):
            worker_slot_queue.put(worker_slot)
        with ProcessPoolExecutor(
            max_workers=effective_worker_count,
            mp_context=spawn_context,
            initializer=initialize_eval_worker,
            initargs=(
                worker_slot_queue,
                device_dispatch.worker_cuda_devices,
                device_dispatch.force_cpu,
            ),
        ) as executor:
            futures = {
                executor.submit(_evaluate_chunk_job, job): job.chunk_index
                for job in jobs
            }
            for future in as_completed(futures):
                chunk_index = futures[future]
                chunk_results[chunk_index] = future.result()
                logger.info(
                    "Parallel eval chunk %d/%d complete: done=%d pending=%d",
                    chunk_index + 1,
                    len(chunks),
                    len(chunk_results),
                    len(chunks) - len(chunk_results),
                )

    ordered_results = tuple(chunk_results[index] for index in range(len(chunks)))
    logger.info("Parallel eval: merging %d chunks", len(ordered_results))
    return _evaluation_result_from_chunk_totals(case, ordered_results)


def _evaluation_result_from_totals(
    *,
    case: EvalCase,
    model_name: str,
    model_totals: tuple[MetricTotals, ...],
    persistence_totals: tuple[MetricTotals, ...],
    diagnostic_issues: tuple[Any, ...],
) -> EvaluationResult:
    """Return the final public result from chunk-combinable metric totals."""
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
        model_name=model_name,
        records=records,
        diagnostics=diagnostics,
    )


def _evaluation_result_from_chunk_totals(
    case: EvalCase,
    chunk_totals: tuple[EvaluationTotals, ...],
) -> EvaluationResult:
    assert chunk_totals
    model_totals = []
    persistence_totals = []
    diagnostic_issues = []
    for totals in chunk_totals:
        model_totals.extend(totals.model_totals)
        persistence_totals.extend(totals.persistence_totals)
        diagnostic_issues.extend(totals.diagnostics.issues)
    return _evaluation_result_from_totals(
        case=case,
        model_name=chunk_totals[0].model_name,
        model_totals=tuple(model_totals),
        persistence_totals=tuple(persistence_totals),
        diagnostic_issues=tuple(diagnostic_issues),
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


def _format_time(time_value: Any) -> str:
    return str(np.datetime64(time_value, "s"))


@dataclass(frozen=True)
class _ChunkJob:
    """One chunk evaluation unit sent to a worker process."""

    model_factory: Callable[[], ForecastModel]
    source_path: str
    chunk_index: int
    chunk_case: EvalCase
    result_path: Path


def _evaluate_chunk_job(job: _ChunkJob) -> EvaluationTotals:
    source = WeatherBench2Source(path=job.source_path)
    model = job.model_factory()
    batch = build_weatherbench2_batch(source, job.chunk_case)
    totals = evaluate_batch_totals(model, batch)
    _write_chunk_result(job.result_path, chunk_index=job.chunk_index, totals=totals)
    return totals


def _chunk_result_path(chunk_dir: Path, chunk_index: int) -> Path:
    return chunk_dir / f"{chunk_index:06d}.json"


def _parallel_manifest_values(
    *,
    model_name: str,
    source_path: str,
    case: EvalCase,
    chunk_initial_count: int,
    chunk_count: int,
) -> dict[str, Any]:
    return {
        "model_name": model_name,
        "source_path": source_path,
        "case": case.asdict(),
        "chunk_initial_count": chunk_initial_count,
        "chunk_count": chunk_count,
    }


def _prepare_parallel_run(
    run_path: Path,
    *,
    manifest_values: dict[str, Any],
    worker_count: int,
    device_dispatch: EvalDeviceDispatch,
    resume: bool,
) -> None:
    manifest_path = run_path / "manifest.json"
    chunk_path = run_path / "chunks"
    if resume and manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as input_file:
            previous_manifest = json.load(input_file)
        previous_compatible_values = {
            key: previous_manifest[key] for key in manifest_values
        }
        assert previous_compatible_values == manifest_values, (
            f"parallel eval run_dir {run_path} contains incompatible chunks"
        )
    if not resume:
        for existing_path in chunk_path.glob("*.json"):
            existing_path.unlink()

    _write_json_atomic(
        manifest_path,
        {
            **manifest_values,
            "requested_worker_count": worker_count,
            "worker_count": device_dispatch.effective_worker_count,
            "device_dispatch": device_dispatch.asdict(),
            "pid": os.getpid(),
        },
    )


def _format_worker_devices(device_dispatch: EvalDeviceDispatch) -> str:
    if device_dispatch.mode == "cpu":
        return "cpu"
    return ",".join(
        f"{worker_index}:{cuda_device}"
        for worker_index, cuda_device in enumerate(device_dispatch.worker_cuda_devices)
    )


def _write_chunk_result(
    path: Path,
    *,
    chunk_index: int,
    totals: EvaluationTotals,
) -> None:
    values = {
        "chunk_index": chunk_index,
        "model_name": totals.model_name,
        "model_totals": [total.asdict() for total in totals.model_totals],
        "persistence_totals": [total.asdict() for total in totals.persistence_totals],
        "diagnostics": totals.diagnostics.asdict(),
    }
    _write_json_atomic(path, values)


def _read_chunk_result(
    path: Path,
    *,
    expected_chunk_index: int | None = None,
) -> EvaluationTotals:
    with path.open("r", encoding="utf-8") as input_file:
        values = json.load(input_file)
    if expected_chunk_index is not None:
        assert int(values["chunk_index"]) == expected_chunk_index
    return EvaluationTotals(
        model_name=str(values["model_name"]),
        model_totals=tuple(
            MetricTotals.fromdict(total_values)
            for total_values in values["model_totals"]
        ),
        persistence_totals=tuple(
            MetricTotals.fromdict(total_values)
            for total_values in values["persistence_totals"]
        ),
        diagnostics=ForecastDiagnostics.fromdict(values["diagnostics"]),
    )


def _write_json_atomic(path: Path, values: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as output_file:
        json.dump(values, output_file, indent=2, sort_keys=True)
        output_file.write("\n")
    temporary_path.replace(path)


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
