# Copyright 2026 dynamaxx

"""Run the logarithmic hybrid curriculum under a fixed compute budget."""

import argparse
import json
import math
import os
import shlex
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dynamaxx.training.config import (
    CURRICULUM_HORIZONS_HOURS,
    DEFAULT_TRAINING_OUTPUT_DIRECTORY,
    PRODUCTION_HIDDEN_SIZE,
    PRODUCTION_RESIDUAL_BLOCKS,
)
from dynamaxx.utils.consts import WEATHERBENCH2_ERA5_1P5DEG_6H_PATH

_MEMORY_FAILURE_MARKERS = (
    "CUDA_ERROR_OUT_OF_MEMORY",
    "RESOURCE_EXHAUSTED",
    "out of memory",
)


@dataclass(frozen=True)
class CurriculumStage:
    """One horizon with an equalized simulated-forecast-hour budget."""

    horizon_hours: int
    training_steps: int
    warmup_steps: int
    validation_interval_steps: int

    @property
    def six_hour_equivalent_steps(self) -> float:
        """Compute proxy relative to one six-hour rollout update."""
        return self.training_steps * self.horizon_hours / 6.0


def curriculum_stages(reference_six_hour_steps: int) -> tuple[CurriculumStage, ...]:
    """Construct stage maxima with approximately equal rollout-hour exposure."""
    if reference_six_hour_steps < 1:
        raise ValueError("reference_six_hour_steps must be positive")
    stages = []
    for horizon_hours in CURRICULUM_HORIZONS_HOURS:
        training_steps = max(
            1,
            math.ceil(reference_six_hour_steps * 6 / horizon_hours),
        )
        warmup_steps = (
            0
            if training_steps == 1
            else min(training_steps - 1, max(1, math.ceil(training_steps * 0.1)))
        )
        validation_interval_steps = max(1, math.ceil(training_steps / 20))
        stages.append(
            CurriculumStage(
                horizon_hours=horizon_hours,
                training_steps=training_steps,
                warmup_steps=warmup_steps,
                validation_interval_steps=validation_interval_steps,
            )
        )
    return tuple(stages)


def estimated_compute_hours(
    stages: tuple[CurriculumStage, ...],
    *,
    seconds_per_six_hour_update: float,
) -> float:
    """Estimate idealized curriculum compute time from the measured 6h rate."""
    if seconds_per_six_hour_update <= 0.0:
        raise ValueError("seconds_per_six_hour_update must be positive")
    equivalent_steps = sum(stage.six_hour_equivalent_steps for stage in stages)
    return equivalent_steps * seconds_per_six_hour_update / 3600.0


def _parser() -> argparse.ArgumentParser:
    """Build the full-curriculum command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Run 6h through 360h hybrid stages with equal simulated-time budgets."
        )
    )
    parser.add_argument("--dataset", default=WEATHERBENCH2_ERA5_1P5DEG_6H_PATH)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(DEFAULT_TRAINING_OUTPUT_DIRECTORY),
    )
    parser.add_argument("--reference-6h-steps", type=int, default=20_000)
    parser.add_argument("--bptt-window-hours", type=int, default=24)
    parser.add_argument("--validation-batches", type=int, default=4)
    parser.add_argument("--data-loader-workers", type=int, default=8)
    parser.add_argument("--state-cache-workers", type=int, default=8)
    parser.add_argument("--wandb-project", default="dynamaxx")
    parser.add_argument("--wandb-run-prefix", default="hybrid-production-20p69m")
    parser.add_argument(
        "--start-horizon-hours",
        type=int,
        choices=CURRICULUM_HORIZONS_HOURS,
        default=6,
    )
    parser.add_argument(
        "--initialize-from",
        type=Path,
        default=None,
        help="EMA checkpoint used only when the first selected stage is new.",
    )
    parser.add_argument(
        "--seconds-per-6h-update",
        type=float,
        default=2.06,
        help="Measured packed-update time used only for the printed projection.",
    )
    parser.add_argument("--no-wandb", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _read_json(path: Path) -> dict[str, Any]:
    """Read one local manifest or configuration mapping."""
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _latest_step(stage_directory: Path) -> int | None:
    """Return the durable latest step for one stage, if present."""
    manifest_path = stage_directory / "latest.json"
    if not manifest_path.is_file():
        return None
    return int(_read_json(manifest_path)["step"])


def _selected_checkpoint(stage_directory: Path) -> Path:
    """Prefer the best validation checkpoint, falling back to the latest."""
    for manifest_name in ("best.json", "latest.json"):
        manifest_path = stage_directory / manifest_name
        if manifest_path.is_file():
            checkpoint_path = stage_directory / str(
                _read_json(manifest_path)["checkpoint"]
            )
            if checkpoint_path.is_file():
                return checkpoint_path.resolve()
    raise FileNotFoundError(f"no checkpoint found in {stage_directory}")


def _fresh_stage_config(
    stage: CurriculumStage,
    *,
    arguments: argparse.Namespace,
    stage_directory: Path,
) -> dict[str, Any]:
    """Return CLI-relevant configuration for a newly promoted stage."""
    per_device_batch_size = 1
    gradient_accumulation_steps = 2
    return {
        "dataset_path": arguments.dataset,
        "output_directory": str(stage_directory),
        "horizon_hours": stage.horizon_hours,
        "bptt_window_hours": arguments.bptt_window_hours,
        "training_steps": stage.training_steps,
        "warmup_steps": stage.warmup_steps,
        "seed": 0,
        "hidden_size": PRODUCTION_HIDDEN_SIZE,
        "residual_blocks": PRODUCTION_RESIDUAL_BLOCKS,
        "correction_interval_seconds": 1800.0,
        "statistics_samples": 32,
        "per_device_batch_size": per_device_batch_size,
        "gradient_accumulation_steps": gradient_accumulation_steps,
        "checkpoint_every_steps": stage.validation_interval_steps,
        "validate_every_steps": stage.validation_interval_steps,
        "log_every_steps": 10,
        "validation_batches": arguments.validation_batches,
        "wandb_project": arguments.wandb_project,
        "wandb_run_name": (
            f"{arguments.wandb_run_prefix}-{stage.horizon_hours}h-2014-2018"
        ),
    }


def _stage_config(
    stage: CurriculumStage,
    *,
    arguments: argparse.Namespace,
    stage_directory: Path,
) -> tuple[dict[str, Any], bool]:
    """Use checkpoint-compatible settings when resuming an existing stage."""
    latest_step = _latest_step(stage_directory)
    config_path = stage_directory / "run_config.json"
    if latest_step is not None:
        if not config_path.is_file():
            raise FileNotFoundError(
                f"existing stage is missing its run configuration: {config_path}"
            )
        config = _read_json(config_path)
        if int(config["horizon_hours"]) != stage.horizon_hours:
            raise ValueError(f"horizon mismatch in {config_path}")
        return config, True
    return (
        _fresh_stage_config(
            stage,
            arguments=arguments,
            stage_directory=stage_directory,
        ),
        False,
    )


def _training_command(
    config: dict[str, Any],
    *,
    stop_at_step: int,
    arguments: argparse.Namespace,
    resume: bool,
    initialize_from: Path | None,
    pack_accumulation: bool,
) -> list[str]:
    """Translate one stage configuration into an exact trainer invocation."""
    command = [
        sys.executable,
        "-m",
        "dynamaxx.training.cli",
        "--dataset",
        str(config["dataset_path"]),
        "--output",
        str(config["output_directory"]),
        "--horizon-hours",
        str(config["horizon_hours"]),
        "--bptt-window-hours",
        str(config.get("bptt_window_hours", config["horizon_hours"])),
        "--steps",
        str(config["training_steps"]),
        "--warmup-steps",
        str(config["warmup_steps"]),
        "--seed",
        str(config["seed"]),
        "--hidden-size",
        str(config["hidden_size"]),
        "--residual-blocks",
        str(config["residual_blocks"]),
        "--correction-interval-seconds",
        str(config["correction_interval_seconds"]),
        "--statistics-samples",
        str(config["statistics_samples"]),
        "--per-device-batch-size",
        str(config["per_device_batch_size"]),
        "--gradient-accumulation-steps",
        str(config["gradient_accumulation_steps"]),
        "--checkpoint-every",
        str(config["checkpoint_every_steps"]),
        "--validate-every",
        str(config["validate_every_steps"]),
        "--log-every",
        str(config["log_every_steps"]),
        "--validation-batches",
        str(config["validation_batches"]),
        "--stop-at-step",
        str(stop_at_step),
        "--data-loader-workers",
        str(arguments.data_loader_workers),
        "--state-cache-workers",
        str(arguments.state_cache_workers),
        "--mmap-caches",
    ]
    if config.get("wandb_project") is not None:
        command.extend(("--wandb-project", str(config["wandb_project"])))
    if config.get("wandb_run_name") is not None:
        command.extend(("--wandb-run-name", str(config["wandb_run_name"])))
    if pack_accumulation:
        command.append("--pack-gradient-accumulation")
    if arguments.no_wandb:
        command.append("--no-wandb")
    if resume:
        command.append("--resume")
    elif initialize_from is not None:
        command.extend(("--initialize-from", str(initialize_from)))
    return command


def _run_and_tee(command: list[str], *, log_path: Path) -> tuple[int, str]:
    """Run one isolated JAX stage while retaining a local combined log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment["NCCL_NET"] = "Socket"
    environment.setdefault(
        "JAX_COMPILATION_CACHE_DIR",
        str((log_path.parents[2] / "jax-compilation-cache").resolve()),
    )
    recent_lines: deque[str] = deque(maxlen=200)
    with log_path.open("a", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=environment,
        )
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            log_file.write(line)
            log_file.flush()
            recent_lines.append(line)
        return_code = process.wait()
    return return_code, "".join(recent_lines)


def _format_command(command: list[str]) -> str:
    """Format an argv vector for readable dry-run output."""
    return shlex.join(command)


def main(argv: list[str] | None = None) -> int:
    """Execute every requested curriculum stage in its own JAX process."""
    arguments = _parser().parse_args(argv)
    if arguments.validation_batches < 1:
        raise ValueError("validation_batches must be positive")
    stages = tuple(
        stage
        for stage in curriculum_stages(arguments.reference_6h_steps)
        if stage.horizon_hours >= arguments.start_horizon_hours
    )
    projected_hours = estimated_compute_hours(
        stages,
        seconds_per_six_hour_update=arguments.seconds_per_6h_update,
    )
    print(
        f"curriculum projection: {projected_hours:.1f} ideal compute-hours "
        f"across {len(stages)} stages"
    )
    pipeline_start = time.monotonic()
    previous_checkpoint = arguments.initialize_from
    if previous_checkpoint is None and arguments.start_horizon_hours != 6:
        start_index = CURRICULUM_HORIZONS_HOURS.index(arguments.start_horizon_hours)
        preceding_horizon = CURRICULUM_HORIZONS_HOURS[start_index - 1]
        preceding_directory = (
            arguments.output_root.expanduser().resolve() / f"{preceding_horizon}h"
        )
        if _latest_step(preceding_directory) is not None:
            previous_checkpoint = _selected_checkpoint(preceding_directory)
    for stage in stages:
        stage_directory = (
            arguments.output_root.expanduser().resolve() / f"{stage.horizon_hours}h"
        )
        latest_step = _latest_step(stage_directory)
        if latest_step is not None and latest_step >= stage.training_steps:
            print(
                f"stage {stage.horizon_hours}h already complete at step "
                f"{latest_step}; skipping"
            )
            previous_checkpoint = _selected_checkpoint(stage_directory)
            continue
        config, resume = _stage_config(
            stage,
            arguments=arguments,
            stage_directory=stage_directory,
        )
        if not resume and previous_checkpoint is None and stage.horizon_hours != 6:
            raise ValueError(
                f"new {stage.horizon_hours}h stage requires --initialize-from "
                "or a completed preceding stage"
            )
        command = _training_command(
            config,
            stop_at_step=stage.training_steps,
            arguments=arguments,
            resume=resume,
            initialize_from=None if resume else previous_checkpoint,
            pack_accumulation=True,
        )
        print(
            f"stage {stage.horizon_hours}h: steps={stage.training_steps} "
            f"equivalent_6h_steps={stage.six_hour_equivalent_steps:.0f}"
        )
        print(_format_command(command))
        if arguments.dry_run:
            previous_checkpoint = stage_directory / "DRY_RUN_CHECKPOINT.pkl"
            continue
        return_code, recent_output = _run_and_tee(
            command,
            log_path=stage_directory / "train.log",
        )
        memory_failure = return_code == -9 or any(
            marker in recent_output for marker in _MEMORY_FAILURE_MARKERS
        )
        if return_code != 0 and memory_failure:
            print(
                f"packed {stage.horizon_hours}h stage exceeded memory; "
                "retrying the same global batch with sequential accumulation"
            )
            resume_after_failure = _latest_step(stage_directory) is not None
            command = _training_command(
                config,
                stop_at_step=stage.training_steps,
                arguments=arguments,
                resume=resume_after_failure,
                initialize_from=(None if resume_after_failure else previous_checkpoint),
                pack_accumulation=False,
            )
            return_code, recent_output = _run_and_tee(
                command,
                log_path=stage_directory / "train.log",
            )
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command, recent_output)
        durable_step = _latest_step(stage_directory)
        if durable_step is None or durable_step < stage.training_steps:
            raise RuntimeError(
                f"stage {stage.horizon_hours}h stopped at {durable_step}; "
                f"expected {stage.training_steps}"
            )
        previous_checkpoint = _selected_checkpoint(stage_directory)
    elapsed_hours = (time.monotonic() - pipeline_start) / 3600.0
    print(f"curriculum complete in {elapsed_hours:.2f} hours")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
