# Copyright 2026 dynamaxx

"""Hybrid neural-corrector training components."""

from dynamaxx.training.config import (
    CURRICULUM_HORIZONS_HOURS,
    TrainingConfig,
    supervised_lead_hours,
)
from dynamaxx.training.corrector import ColumnResidualMLP
from dynamaxx.training.data import (
    SampledTrajectory,
    WeatherBench2TrajectorySampler,
)
from dynamaxx.training.losses import (
    HybridForecastLoss,
    SpectralLossStatistics,
    estimate_spectral_loss_statistics,
)

__all__ = [
    "CURRICULUM_HORIZONS_HOURS",
    "ColumnResidualMLP",
    "HybridForecastLoss",
    "SampledTrajectory",
    "SpectralLossStatistics",
    "TrainingConfig",
    "WeatherBench2TrajectorySampler",
    "estimate_spectral_loss_statistics",
    "supervised_lead_hours",
]
