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
    decoder_output_scale: jax.Array | None = None
    forecast_channel_scale: jax.Array | None = None
    decoder_input_mean: jax.Array | None = None
    decoder_input_standard_deviation: jax.Array | None = None


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
    decoder_feature_sum = None
    decoder_feature_square_sum = None
    target_sum = None
    target_square_sum = None
    reconstruction_square_sum = None
    temporal_difference_square_sum = None
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
        initial_target = weather_state.select(core.output_variables)
        decoded = core.decode(core_state)
        decoder_features = np.concatenate(
            (
                features,
                np.moveaxis(
                    np.asarray(decoded.values, dtype=np.float64),
                    0,
                    -1,
                ),
            ),
            axis=-1,
        )
        flat_decoder_features = decoder_features.reshape(
            -1,
            decoder_features.shape[-1],
        )
        if decoder_feature_sum is None:
            decoder_feature_sum = np.zeros(
                (flat_decoder_features.shape[-1],),
                dtype=np.float64,
            )
            decoder_feature_square_sum = np.zeros_like(decoder_feature_sum)
        decoder_feature_sum += np.sum(flat_decoder_features, axis=0)
        decoder_feature_square_sum += np.sum(
            np.square(flat_decoder_features),
            axis=0,
        )
        target_values = np.asarray(initial_target.values, dtype=np.float64)
        reconstruction_error = target_values - np.asarray(
            decoded.values,
            dtype=np.float64,
        )
        if target_sum is None:
            target_sum = np.zeros((target_values.shape[0],), dtype=np.float64)
            target_square_sum = np.zeros_like(target_sum)
            reconstruction_square_sum = np.zeros_like(target_sum)
            temporal_difference_square_sum = np.zeros_like(target_sum)
        target_sum += np.sum(target_values, axis=(-2, -1))
        target_square_sum += np.sum(np.square(target_values), axis=(-2, -1))
        reconstruction_square_sum += np.sum(
            np.square(reconstruction_error),
            axis=(-2, -1),
        )
        six_hour_target = np.asarray(
            sampled.targets.values[sample_index, 0],
            dtype=np.float64,
        )
        temporal_difference_square_sum += np.sum(
            np.square(six_hour_target - target_values),
            axis=(-2, -1),
        )
        column_count += flat_features.shape[0]
    input_mean = feature_sum / column_count
    input_variance = np.maximum(
        feature_square_sum / column_count - np.square(input_mean),
        0.0,
    )
    input_standard_deviation = np.maximum(np.sqrt(input_variance), 1.0e-6)
    assert decoder_feature_sum is not None
    assert decoder_feature_square_sum is not None
    decoder_input_mean = decoder_feature_sum / column_count
    decoder_input_variance = np.maximum(
        decoder_feature_square_sum / column_count - np.square(decoder_input_mean),
        0.0,
    )
    decoder_input_standard_deviation = np.maximum(
        np.sqrt(decoder_input_variance),
        1.0e-6,
    )
    assert target_sum is not None
    assert target_square_sum is not None
    assert reconstruction_square_sum is not None
    assert temporal_difference_square_sum is not None
    target_variance = np.maximum(
        target_square_sum / column_count - np.square(target_sum / column_count),
        0.0,
    )
    target_standard_deviation = np.sqrt(target_variance)
    reconstruction_rms = np.sqrt(reconstruction_square_sum / column_count)
    temporal_difference_rms = np.sqrt(temporal_difference_square_sum / column_count)
    decoder_output_scale = np.maximum.reduce(
        (
            reconstruction_rms,
            0.1 * target_standard_deviation,
            np.full_like(reconstruction_rms, 1.0e-8),
        )
    )
    forecast_channel_scale = np.maximum.reduce(
        (
            temporal_difference_rms,
            0.01 * target_standard_deviation,
            np.full_like(temporal_difference_rms, 1.0e-8),
        )
    )

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
        decoder_output_scale=jnp.asarray(
            decoder_output_scale,
            dtype=jnp.float32,
        ),
        forecast_channel_scale=jnp.asarray(
            forecast_channel_scale,
            dtype=jnp.float32,
        ),
        decoder_input_mean=jnp.asarray(
            decoder_input_mean,
            dtype=jnp.float32,
        ),
        decoder_input_standard_deviation=jnp.asarray(
            decoder_input_standard_deviation,
            dtype=jnp.float32,
        ),
    )


def save_training_statistics(path: Path, statistics: TrainingStatistics) -> None:
    """Save statistics to a local NumPy archive."""
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "format_version": 4,
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
        decoder_output_scale=(
            np.asarray([], dtype=np.float32)
            if statistics.decoder_output_scale is None
            else np.asarray(jax.device_get(statistics.decoder_output_scale))
        ),
        forecast_channel_scale=(
            np.asarray([], dtype=np.float32)
            if statistics.forecast_channel_scale is None
            else np.asarray(jax.device_get(statistics.forecast_channel_scale))
        ),
        decoder_input_mean=(
            np.asarray([], dtype=np.float32)
            if statistics.decoder_input_mean is None
            else np.asarray(jax.device_get(statistics.decoder_input_mean))
        ),
        decoder_input_standard_deviation=(
            np.asarray([], dtype=np.float32)
            if statistics.decoder_input_standard_deviation is None
            else np.asarray(jax.device_get(statistics.decoder_input_standard_deviation))
        ),
        metadata=np.asarray(json.dumps(metadata, sort_keys=True)),
    )
    temporary_path.replace(path)


def load_training_statistics(path: Path) -> TrainingStatistics:
    """Load and validate a local statistics archive."""
    path = Path(path).expanduser().resolve()
    with np.load(path, allow_pickle=False) as archive:
        metadata = json.loads(str(archive["metadata"]))
        if metadata.get("format_version") not in (1, 2, 3, 4):
            raise ValueError("unsupported training-statistics format version")
        decoder_output_scale = (
            jnp.asarray(archive["decoder_output_scale"], dtype=jnp.float32)
            if "decoder_output_scale" in archive
            and archive["decoder_output_scale"].size
            else None
        )
        forecast_channel_scale = (
            jnp.asarray(archive["forecast_channel_scale"], dtype=jnp.float32)
            if "forecast_channel_scale" in archive
            and archive["forecast_channel_scale"].size
            else None
        )
        decoder_input_mean = (
            jnp.asarray(archive["decoder_input_mean"], dtype=jnp.float32)
            if "decoder_input_mean" in archive and archive["decoder_input_mean"].size
            else None
        )
        decoder_input_standard_deviation = (
            jnp.asarray(
                archive["decoder_input_standard_deviation"],
                dtype=jnp.float32,
            )
            if "decoder_input_standard_deviation" in archive
            and archive["decoder_input_standard_deviation"].size
            else None
        )
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
            decoder_output_scale=decoder_output_scale,
            forecast_channel_scale=forecast_channel_scale,
            decoder_input_mean=decoder_input_mean,
            decoder_input_standard_deviation=(decoder_input_standard_deviation),
        )
