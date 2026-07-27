# Copyright 2026 dynamaxx

"""Short-range interface and forecast diagnostics for trained hybrid models."""

import argparse
import json
import logging
from dataclasses import replace
from pathlib import Path
from typing import Any

import jax
import numpy as np

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.dycore.registry import create_dycore_model
from dynamaxx.eval.batch import build_weatherbench2_batch
from dynamaxx.eval.core import EvalCase
from dynamaxx.eval.protocols import WEATHERBENCH2_HEADLINE_VARIABLES
from dynamaxx.eval.runner import (
    EvaluationResult,
    evaluate_batch,
    write_metric_csv,
    write_metric_json,
)
from dynamaxx.hybrid.checkpoint import HybridCheckpointModel, load_hybrid_checkpoint
from dynamaxx.hybrid.dinosaur import DinosaurHybridCore
from dynamaxx.training.checkpoints import restore_checkpoint

logger = logging.getLogger("dynamaxx.training.hybrid_diagnostics")
DEFAULT_OUTPUT_DIRECTORY = Path(
    "/mnt/data/dynamaxx-training-cache/eval/short-range-diagnostic-2019"
)
SHORT_RANGE_LEAD_HOURS = (0, 6, 12, 24)


def stratified_initial_times(
    available_times: np.ndarray,
    *,
    start: Any,
    end: Any,
    count: int,
    maximum_lead_hours: int,
) -> np.ndarray:
    """Select deterministic year-spanning starts with truth inside the split."""
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("count must be a positive integer")
    if maximum_lead_hours < 0:
        raise ValueError("maximum_lead_hours must be nonnegative")
    times = np.asarray(available_times, dtype="datetime64[ns]")
    start_time = np.datetime64(start, "ns")
    end_time = np.datetime64(end, "ns")
    latest_initial_time = end_time - np.timedelta64(maximum_lead_hours, "h")
    candidates = times[(times >= start_time) & (times <= latest_initial_time)]
    if candidates.size < count:
        raise ValueError(
            f"requested {count} starts but only {candidates.size} are available"
        )
    indices = np.rint(np.linspace(0, candidates.size - 1, count)).astype(np.int64)
    return candidates[indices]


def short_range_case(initial_times: np.ndarray) -> EvalCase:
    """Build the non-promotional 0/6/12/24-hour diagnostic case."""
    return EvalCase(
        name="short-range-diagnostic-2019",
        initial_times=initial_times,
        lead_steps=tuple(hours // 6 for hours in SHORT_RANGE_LEAD_HOURS),
        step_hours=6,
        target_variables=WEATHERBENCH2_HEADLINE_VARIABLES,
    )


def comparison_rows(
    hybrid_result: EvaluationResult,
    dycore_result: EvaluationResult,
) -> list[dict[str, Any]]:
    """Align hybrid and dycore RMSE records for direct attribution."""
    dycore_records = {
        (record.channel_name, record.lead_hours): record
        for record in dycore_result.records
        if record.model_name == dycore_result.model_name
    }
    rows = []
    for hybrid_record in hybrid_result.records:
        if hybrid_record.model_name != hybrid_result.model_name:
            continue
        key = (hybrid_record.channel_name, hybrid_record.lead_hours)
        dycore_record = dycore_records[key]
        ratio = (
            None
            if dycore_record.rmse == 0.0
            else hybrid_record.rmse / dycore_record.rmse
        )
        rows.append(
            {
                "channel_name": hybrid_record.channel_name,
                "lead_hours": hybrid_record.lead_hours,
                "hybrid_rmse": hybrid_record.rmse,
                "dycore_rmse": dycore_record.rmse,
                "hybrid_to_dycore_rmse_ratio": ratio,
                "hybrid_bias": hybrid_record.bias,
                "dycore_bias": dycore_record.bias,
            }
        )
    return rows


def interface_rows(
    initialized_result: EvaluationResult,
    no_dfi_result: EvaluationResult,
) -> list[dict[str, Any]]:
    """Attribute lead-zero interface error to digital-filter initialization."""
    no_dfi_records = {
        record.channel_name: record
        for record in no_dfi_result.records
        if record.model_name == no_dfi_result.model_name
    }
    rows = []
    for initialized_record in initialized_result.records:
        if (
            initialized_record.model_name != initialized_result.model_name
            or initialized_record.lead_hours != 0
        ):
            continue
        no_dfi_record = no_dfi_records[initialized_record.channel_name]
        rows.append(
            {
                "channel_name": initialized_record.channel_name,
                "with_dfi_rmse": initialized_record.rmse,
                "without_dfi_rmse": no_dfi_record.rmse,
                "dfi_rmse_change": initialized_record.rmse - no_dfi_record.rmse,
                "with_dfi_bias": initialized_record.bias,
                "without_dfi_bias": no_dfi_record.bias,
            }
        )
    return rows


def _write_summary(
    path: Path,
    *,
    checkpoint: Path,
    initial_times: np.ndarray,
    hybrid_result: EvaluationResult,
    dycore_result: EvaluationResult,
    no_dfi_result: EvaluationResult,
) -> None:
    values = {
        "schema_version": 1,
        "checkpoint": str(checkpoint),
        "initial_times": [str(value) for value in initial_times],
        "lead_hours": list(SHORT_RANGE_LEAD_HOURS),
        "hybrid_model_name": hybrid_result.model_name,
        "dycore_model_name": dycore_result.model_name,
        "comparison": comparison_rows(hybrid_result, dycore_result),
        "interface_dfi_attribution": interface_rows(
            hybrid_result,
            no_dfi_result,
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as output_file:
        json.dump(values, output_file, indent=2, sort_keys=True)
        output_file.write("\n")
    temporary_path.replace(path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Decompose lead-zero interface error and 6/12/24-hour hybrid skill."
        )
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--initial-count", type=int, default=16)
    parser.add_argument("--start", default="2019-01-01T00:00:00")
    parser.add_argument("--end", default="2019-12-31T18:00:00")
    parser.add_argument("--raw-hybrid-parameters", action="store_true")
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=DEFAULT_OUTPUT_DIRECTORY,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a deterministic short-range diagnostic on the 2019 split."""
    arguments = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    compilation_cache_directory = (
        arguments.output_directory.expanduser().resolve().parents[2]
        / "jax-compilation-cache"
    )
    compilation_cache_directory.mkdir(parents=True, exist_ok=True)
    jax.config.update(
        "jax_compilation_cache_dir",
        str(compilation_cache_directory),
    )
    checkpoint = arguments.checkpoint.expanduser().resolve()
    restored = restore_checkpoint(checkpoint)
    config = restored.metadata.get("config")
    if not isinstance(config, dict):
        raise ValueError("hybrid checkpoint is missing its training configuration")
    dataset_path = str(config["dataset_path"])
    dycore_name = str(config["dycore_name"])
    source = WeatherBench2Source(path=dataset_path)
    available_times = source.available_times(arguments.start, arguments.end)
    initial_times = stratified_initial_times(
        available_times,
        start=arguments.start,
        end=arguments.end,
        count=arguments.initial_count,
        maximum_lead_hours=max(SHORT_RANGE_LEAD_HOURS),
    )
    case = short_range_case(initial_times)
    logger.info(
        "loading %d starts spanning %s through %s",
        initial_times.size,
        initial_times[0],
        initial_times[-1],
    )
    batch = build_weatherbench2_batch(source, case)

    dycore_model = create_dycore_model(dycore_name)
    logger.info("evaluating frozen dycore %s", dycore_name)
    dycore_result = evaluate_batch(dycore_model, batch)

    hybrid_model = load_hybrid_checkpoint(
        checkpoint,
        use_ema=not arguments.raw_hybrid_parameters,
    )
    logger.info("evaluating hybrid %s", hybrid_model.name)
    hybrid_result = evaluate_batch(hybrid_model, batch)

    source_longitude, source_latitude = source.spatial_coordinates(
        time=initial_times[0]
    )
    initialized_core = hybrid_model.model.core
    no_dfi_core = DinosaurHybridCore(
        model=replace(
            initialized_core.model,
            apply_digital_filter_initialization=False,
        ),
        longitude=source_longitude,
        latitude=source_latitude,
        input_variables=initialized_core.input_variables,
        data_path=dataset_path,
        fallback_to_centered_sil3_on_nonfinite=False,
    )
    no_dfi_model = HybridCheckpointModel(
        model=replace(hybrid_model.model, core=no_dfi_core),
        parameters=hybrid_model.parameters,
        name=f"{hybrid_model.name}-no-dfi-interface",
    )
    lead_zero_case = EvalCase(
        name="lead-zero-interface-diagnostic-2019",
        initial_times=initial_times,
        lead_steps=(0,),
        step_hours=6,
        target_variables=WEATHERBENCH2_HEADLINE_VARIABLES,
    )
    logger.info("evaluating lead-zero interface without digital filtering")
    no_dfi_result = evaluate_batch(
        no_dfi_model,
        build_weatherbench2_batch(source, lead_zero_case),
    )

    output_directory = arguments.output_directory.expanduser().resolve()
    named_results = (
        (case.name, dycore_result),
        (case.name, hybrid_result),
        (lead_zero_case.name, no_dfi_result),
    )
    for case_name, result in named_results:
        stem = f"{case_name}_{result.model_name}"
        write_metric_json(result, output_directory / f"{stem}.json")
        write_metric_csv(result, output_directory / f"{stem}.csv")
    summary_path = output_directory / "summary.json"
    _write_summary(
        summary_path,
        checkpoint=checkpoint,
        initial_times=initial_times,
        hybrid_result=hybrid_result,
        dycore_result=dycore_result,
        no_dfi_result=no_dfi_result,
    )
    logger.info("diagnostic summary written to %s", summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
