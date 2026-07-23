# Copyright 2026 dynamaxx

"""Tests for the horizon-weighted production curriculum."""

from argparse import Namespace
from pathlib import Path

import pytest

from dynamaxx.training.config import (
    PRODUCTION_HIDDEN_SIZE,
    PRODUCTION_RESIDUAL_BLOCKS,
)
from dynamaxx.training.curriculum import (
    _fresh_stage_config,
    curriculum_stages,
    estimated_compute_hours,
)


def test_curriculum_equalizes_simulated_forecast_hours():
    """Every stage receives approximately 20k six-hour-equivalent updates."""
    stages = curriculum_stages(20_000)

    assert [stage.training_steps for stage in stages] == [
        20_000,
        10_000,
        5_000,
        2_500,
        1_250,
        625,
        334,
    ]
    assert all(20_000 <= stage.six_hour_equivalent_steps <= 20_040 for stage in stages)
    assert all(stage.warmup_steps < stage.training_steps for stage in stages)


def test_curriculum_projection_uses_measured_six_hour_rate():
    """The seven-stage ideal projection is comfortably below one week."""
    projected_hours = estimated_compute_hours(
        curriculum_stages(20_000),
        seconds_per_six_hour_update=2.06,
    )

    assert projected_hours == pytest.approx(80.13, abs=0.05)


def test_fresh_six_hour_stage_uses_measured_packed_batch16_configuration():
    """The production model packs two examples on each of eight GPUs."""
    stage = curriculum_stages(20_000)[0]
    arguments = Namespace(
        dataset="dataset",
        bptt_window_hours=24,
        validation_batches=8,
        wandb_project="dynamaxx",
        wandb_run_prefix="hybrid",
    )

    config = _fresh_stage_config(
        stage,
        arguments=arguments,
        stage_directory=Path("checkpoints/hybrid-optimized/6h"),
    )

    assert config["per_device_batch_size"] == 1
    assert config["gradient_accumulation_steps"] == 2
    assert config["hidden_size"] == PRODUCTION_HIDDEN_SIZE
    assert config["residual_blocks"] == PRODUCTION_RESIDUAL_BLOCKS
    assert config["bptt_window_hours"] == 24
