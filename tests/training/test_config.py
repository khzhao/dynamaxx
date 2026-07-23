# Copyright 2026 dynamaxx

"""Tests for hybrid-training configuration and supervised lead schedules."""

import pytest

from dynamaxx.training.config import (
    PRODUCTION_HIDDEN_SIZE,
    PRODUCTION_RESIDUAL_BLOCKS,
    TrainingConfig,
    supervised_lead_hours,
)


@pytest.mark.parametrize(
    ("horizon_hours", "expected_leads"),
    [
        (6, (6,)),
        (12, (6, 12)),
        (24, (6, 12, 24)),
        (48, (6, 12, 24, 48)),
        (96, (6, 12, 24, 48, 96)),
        (192, (6, 12, 24, 48, 96, 192)),
        (360, (6, 12, 24, 48, 96, 192, 360)),
    ],
)
def test_curriculum_retains_previous_leads_and_adds_one(
    horizon_hours,
    expected_leads,
):
    """Each promotion retains prior logarithmic lead losses."""
    assert supervised_lead_hours(horizon_hours) == expected_leads


def test_training_config_defaults_to_iteration_period_pilot():
    """Defaults select the intended pilot period and production model size."""
    config = TrainingConfig()

    assert config.train_start.startswith("2014-")
    assert config.train_end.startswith("2018-")
    assert config.statistics_start.startswith("1979-")
    assert config.statistics_end.startswith("2018-")
    assert config.lead_hours == (6,)
    assert config.hidden_size == PRODUCTION_HIDDEN_SIZE
    assert config.residual_blocks == PRODUCTION_RESIDUAL_BLOCKS
    assert config.bptt_window_hours == 24
    assert config.effective_bptt_window_hours == 6


def test_long_rollouts_use_bounded_bptt_by_default():
    """Multi-day stages cap their temporal gradient history at 24 hours."""
    config = TrainingConfig(horizon_hours=96)

    assert config.effective_bptt_window_hours == 24


def test_bptt_window_must_align_with_neural_correction_interval():
    """Stopped-gradient events must fall on public model-step boundaries."""
    with pytest.raises(ValueError, match="effective BPTT window"):
        TrainingConfig(
            horizon_hours=48,
            correction_interval_seconds=1000.0,
        )


def test_unknown_curriculum_horizon_is_rejected():
    """Only the fixed logarithmic curriculum stages are accepted."""
    with pytest.raises(ValueError, match="horizon_hours"):
        TrainingConfig(horizon_hours=36)
