# Copyright 2026 dynamaxx

"""Local estimation and storage of frozen training-set statistics."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.training.data import WeatherBench2TrajectorySampler
from dynamaxx.training.losses import (
    SpectralLossStatistics,
    estimate_spectral_loss_statistics,
)
from dynamaxx.weather import WeatherState


@dataclass(frozen=True)
class TrainingStatistics:
    """Frozen neural-input and forecast-loss normalizers."""

    input_mean: jax.Array
    input_standard_deviation: jax.Array
    spectral: SpectralLossStatistics
    input_variables: tuple[str, ...]
    target_variables: tuple[str, ...]


def estimate_training_statistics(
    core: Any,
    sampler: WeatherBench2TrajectorySampler,
    *,
    sample_count: int,
) -> TrainingStatistics:
    """Estimate all fixed statistics from random training-split truth starts."""
    if sample_count < 2:
        raise ValueError("sample_count must be at least two")
    sampled = sampler.sample(sample_count)
    feature_sum = np.zeros((core.input_feature_count,), dtype=np.float64)
    feature_square_sum = np.zeros_like(feature_sum)
    column_count = 0
    for sample_index, initial_time in enumerate(sampled.initial_times):
        weather_state = WeatherState(
            values=sampled.initial_state.values[sample_index],
            variables=sampled.initial_state.variables,
        )
        core_state = core.initialize(weather_state, initial_time)
        features = np.asarray(
            jax.device_get(core.corrector_inputs(core_state)),
            dtype=np.float64,
        )
        flat_features = features.reshape(-1, features.shape[-1])
        feature_sum += np.sum(flat_features, axis=0)
        feature_square_sum += np.sum(np.square(flat_features), axis=0)
        column_count += flat_features.shape[0]
    input_mean = feature_sum / column_count
    input_variance = np.maximum(
        feature_square_sum / column_count - np.square(input_mean),
        0.0,
    )
    input_standard_deviation = np.maximum(np.sqrt(input_variance), 1.0e-6)

    spectral = estimate_spectral_loss_statistics(
        jnp.asarray(sampled.targets.values[:, 0]),
        to_modal=core.coords.horizontal.to_modal,
        total_wavenumber=core.coords.horizontal.modal_mesh[1],
        modal_mask=core.coords.horizontal.mask,
    )
    return TrainingStatistics(
        input_mean=jnp.asarray(input_mean, dtype=jnp.float32),
        input_standard_deviation=jnp.asarray(
            input_standard_deviation,
            dtype=jnp.float32,
        ),
        spectral=spectral,
        input_variables=sampled.initial_state.variables,
        target_variables=sampled.targets.variables,
    )


def save_training_statistics(path: Path, statistics: TrainingStatistics) -> None:
    """Save statistics to a local NumPy archive."""
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "format_version": 1,
        "input_variables": list(statistics.input_variables),
        "target_variables": list(statistics.target_variables),
    }
    temporary_path = path.with_name(f".{path.name}.tmp.npz")
    np.savez_compressed(
        temporary_path,
        input_mean=np.asarray(jax.device_get(statistics.input_mean)),
        input_standard_deviation=np.asarray(
            jax.device_get(statistics.input_standard_deviation)
        ),
        coefficient_variance=np.asarray(
            jax.device_get(statistics.spectral.coefficient_variance)
        ),
        climatological_power=np.asarray(
            jax.device_get(statistics.spectral.climatological_power)
        ),
        channel_weights=np.asarray(jax.device_get(statistics.spectral.channel_weights)),
        metadata=np.asarray(json.dumps(metadata, sort_keys=True)),
    )
    temporary_path.replace(path)


def load_training_statistics(path: Path) -> TrainingStatistics:
    """Load and validate a local statistics archive."""
    path = Path(path).expanduser().resolve()
    with np.load(path, allow_pickle=False) as archive:
        metadata = json.loads(str(archive["metadata"]))
        if metadata.get("format_version") != 1:
            raise ValueError("unsupported training-statistics format version")
        return TrainingStatistics(
            input_mean=jnp.asarray(archive["input_mean"], dtype=jnp.float32),
            input_standard_deviation=jnp.asarray(
                archive["input_standard_deviation"],
                dtype=jnp.float32,
            ),
            spectral=SpectralLossStatistics(
                coefficient_variance=archive["coefficient_variance"],
                climatological_power=archive["climatological_power"],
                channel_weights=archive["channel_weights"],
            ),
            input_variables=tuple(metadata["input_variables"]),
            target_variables=tuple(metadata["target_variables"]),
        )
