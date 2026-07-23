# Copyright 2026 dynamaxx

"""Tests for safe training command-line configuration transitions."""

import pytest

from dynamaxx.training.cli import _validate_continuation_config
from dynamaxx.training.config import TrainingConfig


def test_continuation_allows_only_batch_output_and_run_name_changes():
    """A throughput continuation retains the scientific training recipe."""
    source = TrainingConfig(
        output_directory="checkpoints/original",
        per_device_batch_size=1,
        gradient_accumulation_steps=2,
        wandb_run_name="original",
    )
    destination = TrainingConfig(
        output_directory="checkpoints/optimized",
        per_device_batch_size=4,
        gradient_accumulation_steps=1,
        wandb_run_name="optimized",
    )

    _validate_continuation_config({"config": source.asdict()}, destination)


def test_continuation_rejects_changed_model_or_training_schedule():
    """A continuation cannot silently change the scientific stage."""
    source = TrainingConfig()
    destination = TrainingConfig(horizon_hours=12)

    with pytest.raises(ValueError, match="horizon_hours"):
        _validate_continuation_config({"config": source.asdict()}, destination)


def test_old_short_horizon_checkpoint_has_equivalent_bptt_semantics():
    """Before the BPTT option existed, short stages used their full horizon."""
    source_config = TrainingConfig().asdict()
    source_config.pop("bptt_window_hours")

    _validate_continuation_config(
        {"config": source_config},
        TrainingConfig(bptt_window_hours=24),
    )


def test_old_long_horizon_checkpoint_cannot_silently_enable_stopped_bptt():
    """Legacy long stages used full BPTT and therefore are not equivalent."""
    source_config = TrainingConfig(horizon_hours=48).asdict()
    source_config.pop("bptt_window_hours")

    with pytest.raises(ValueError, match="bptt_window_hours"):
        _validate_continuation_config(
            {"config": source_config},
            TrainingConfig(horizon_hours=48),
        )
