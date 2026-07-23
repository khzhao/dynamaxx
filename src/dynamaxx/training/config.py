# Copyright 2026 dynamaxx

"""Configuration and curriculum definitions for hybrid-model training."""

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from dynamaxx.utils.consts import WEATHERBENCH2_ERA5_1P5DEG_6H_PATH

CURRICULUM_HORIZONS_HOURS = (6, 12, 24, 48, 96, 192, 360)
DEFAULT_TRAINING_OUTPUT_DIRECTORY = (
    "/mnt/data/dynamaxx-training-cache/checkpoints/hybrid-production-20m"
)
PRODUCTION_HIDDEN_SIZE = 800
PRODUCTION_RESIDUAL_BLOCKS = 8
PILOT_HIDDEN_SIZE = 256
PILOT_RESIDUAL_BLOCKS = 4


def supervised_lead_hours(horizon_hours: int) -> tuple[int, ...]:
    """Return all logarithmic lead losses active at one curriculum horizon."""
    horizon_hours = int(horizon_hours)
    if horizon_hours not in CURRICULUM_HORIZONS_HOURS:
        raise ValueError(
            f"horizon_hours must be one of {CURRICULUM_HORIZONS_HOURS}; "
            f"received {horizon_hours}"
        )
    return tuple(
        lead_hours
        for lead_hours in CURRICULUM_HORIZONS_HOURS
        if lead_hours <= horizon_hours
    )


@dataclass(frozen=True)
class TrainingConfig:
    """Complete reproducible configuration for one curriculum-stage run."""

    dataset_path: str = WEATHERBENCH2_ERA5_1P5DEG_6H_PATH
    output_directory: str = DEFAULT_TRAINING_OUTPUT_DIRECTORY
    dycore_name: str = "dino_rskin_apv"
    horizon_hours: int = 6
    bptt_window_hours: int = 24
    correction_interval_seconds: float = 1800.0
    train_start: str = "2014-01-01T00:00:00"
    train_end: str = "2018-12-31T18:00:00"
    validation_start: str = "2019-01-01T00:00:00"
    validation_end: str = "2019-12-31T18:00:00"
    statistics_start: str = "1979-01-01T00:00:00"
    statistics_end: str = "2018-12-31T18:00:00"
    statistics_samples: int = 32
    seed: int = 0
    training_steps: int = 100_000
    warmup_steps: int = 2_000
    per_device_batch_size: int = 1
    gradient_accumulation_steps: int = 2
    learning_rate: float = 2.0e-4
    minimum_learning_rate_ratio: float = 0.05
    weight_decay: float = 1.0e-5
    gradient_clip_norm: float = 1.0
    ema_decay: float = 0.999
    spectral_loss_weight: float = 0.1
    bias_loss_weight: float = 0.1
    full_resolution_loss_hours: int = 24
    final_retained_wavenumber_fraction: float = 0.25
    spectral_taper_width_fraction: float = 0.15
    hidden_size: int = PRODUCTION_HIDDEN_SIZE
    residual_blocks: int = PRODUCTION_RESIDUAL_BLOCKS
    log_every_steps: int = 10
    validate_every_steps: int = 500
    checkpoint_every_steps: int = 500
    validation_batches: int = 8
    wandb_project: str | None = None
    wandb_run_name: str | None = None

    def __post_init__(self):
        if self.horizon_hours not in CURRICULUM_HORIZONS_HOURS:
            raise ValueError(
                f"horizon_hours must be one of {CURRICULUM_HORIZONS_HOURS}"
            )
        positive_integers = {
            "training_steps": self.training_steps,
            "per_device_batch_size": self.per_device_batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "log_every_steps": self.log_every_steps,
            "validate_every_steps": self.validate_every_steps,
            "checkpoint_every_steps": self.checkpoint_every_steps,
            "validation_batches": self.validation_batches,
            "statistics_samples": self.statistics_samples,
            "hidden_size": self.hidden_size,
            "residual_blocks": self.residual_blocks,
            "full_resolution_loss_hours": self.full_resolution_loss_hours,
            "bptt_window_hours": self.bptt_window_hours,
        }
        for name, value in positive_integers.items():
            if isinstance(value, bool) or int(value) != value or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.warmup_steps < 0 or self.warmup_steps >= self.training_steps:
            raise ValueError("warmup_steps must be in [0, training_steps)")
        positive_values = {
            "correction_interval_seconds": self.correction_interval_seconds,
            "learning_rate": self.learning_rate,
            "gradient_clip_norm": self.gradient_clip_norm,
        }
        for name, value in positive_values.items():
            if value <= 0.0:
                raise ValueError(f"{name} must be positive")
        bptt_correction_steps = (
            self.effective_bptt_window_hours * 3600.0 / self.correction_interval_seconds
        )
        if not math.isclose(
            bptt_correction_steps,
            round(bptt_correction_steps),
            rel_tol=0.0,
            abs_tol=1.0e-9,
        ):
            raise ValueError(
                "the effective BPTT window must be an integer multiple of "
                "correction_interval_seconds"
            )
        if not 0.0 <= self.minimum_learning_rate_ratio <= 1.0:
            raise ValueError("minimum_learning_rate_ratio must be in [0, 1]")
        if not 0.0 <= self.ema_decay < 1.0:
            raise ValueError("ema_decay must be in [0, 1)")
        if self.weight_decay < 0.0:
            raise ValueError("weight_decay must be nonnegative")
        if self.spectral_loss_weight < 0.0 or self.bias_loss_weight < 0.0:
            raise ValueError("loss weights must be nonnegative")
        if not 0.0 < self.final_retained_wavenumber_fraction <= 1.0:
            raise ValueError("final_retained_wavenumber_fraction must be in (0, 1]")
        if not 0.0 < self.spectral_taper_width_fraction <= 1.0:
            raise ValueError("spectral_taper_width_fraction must be in (0, 1]")
        if not self.dycore_name.strip():
            raise ValueError("dycore_name must not be empty")

    @property
    def lead_hours(self) -> tuple[int, ...]:
        """Active supervised leads for this stage."""
        return supervised_lead_hours(self.horizon_hours)

    @property
    def effective_bptt_window_hours(self) -> int:
        """Temporal gradient window after accounting for the rollout horizon."""
        return min(self.horizon_hours, self.bptt_window_hours)

    @property
    def checkpoint_directory(self) -> Path:
        """Local-only checkpoint directory."""
        return Path(self.output_directory).expanduser().resolve()

    def asdict(self) -> dict[str, Any]:
        """Return a JSON-compatible configuration mapping."""
        values = asdict(self)
        values["lead_hours"] = list(self.lead_hours)
        return values
