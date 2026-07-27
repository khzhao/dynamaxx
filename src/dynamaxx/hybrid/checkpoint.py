# Copyright 2026 dynamaxx

"""Inference-only loading and forecasting for local hybrid checkpoints."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.hybrid.dinosaur import (
    DinosaurNeuralCorrector,
    DinosaurNeuralDecoder,
    make_dinosaur_hybrid_core,
)
from dynamaxx.hybrid.model import PreparedHybridModel
from dynamaxx.hybrid.rollout import rollout_at_durations_with_tendency_statistics
from dynamaxx.training.checkpoints import restore_checkpoint
from dynamaxx.training.corrector import ColumnResidualMLP
from dynamaxx.training.statistics import TrainingStatistics
from dynamaxx.weather import ForecastInput, WeatherState


def hybrid_checkpoint_model_name(
    checkpoint_path: str | Path,
    *,
    use_ema: bool = True,
) -> str:
    """Return a stable filesystem-derived name without loading checkpoint data."""
    checkpoint = Path(checkpoint_path).expanduser().resolve()
    parameter_label = "ema" if use_ema else "raw"
    stage_label = checkpoint.parent.name.replace("_", "-")
    checkpoint_label = checkpoint.stem.replace("_", "-")
    return f"hybrid-{stage_label}-{checkpoint_label}-{parameter_label}"


@dataclass
class HybridCheckpointModel:
    """A frozen trained hybrid model implementing the forecast evaluation API."""

    model: PreparedHybridModel[Any, Any, Any, Any, Any]
    parameters: Any
    name: str
    maximum_scan_window_hours: int = 24
    _compiled_forecasts: dict[tuple[int, ...], Callable[..., jax.Array]] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _compiled_initial_decoder: Callable[..., jax.Array] | None = field(
        default=None,
        init=False,
        repr=False,
    )

    def _compiled_decode_initial(self) -> Callable[..., jax.Array]:
        """Return a reusable batched decoder for initialized recurrent states."""
        if self._compiled_initial_decoder is None:

            def decode_one(initial_state: Any) -> jax.Array:
                return self.model.observe(self.parameters, initial_state).values

            self._compiled_initial_decoder = jax.jit(jax.vmap(decode_one))
        return self._compiled_initial_decoder

    def _compiled_forecast(self, lead_hours: tuple[int, ...]) -> Callable[..., Any]:
        """Return a reusable batched forecast executable for one lead schedule."""
        compiled = self._compiled_forecasts.get(lead_hours)
        if compiled is not None:
            return compiled

        durations_seconds = tuple(float(hours * 3600) for hours in lead_hours)
        scan_window_seconds = float(self.maximum_scan_window_hours * 3600)

        def forecast_one(parameters: Any, initial_state: Any) -> jax.Array:
            _, observations, _ = rollout_at_durations_with_tendency_statistics(
                self.model,
                parameters,
                initial_state,
                durations_seconds=durations_seconds,
                rematerialize=False,
                collect_tendency_statistics=False,
                maximum_gradient_duration_seconds=scan_window_seconds,
            )
            return observations.values

        compiled = jax.jit(jax.vmap(forecast_one, in_axes=(None, 0)))
        self._compiled_forecasts[lead_hours] = compiled
        return compiled

    def forecast(self, forecast_input: ForecastInput) -> WeatherState:
        """Forecast every initialization continuously at requested lead times."""
        lead_hours = tuple(int(hours) for hours in forecast_input.lead_hours)
        if not lead_hours or any(hours < 0 for hours in lead_hours):
            raise ValueError("lead_hours must contain nonnegative values")
        if tuple(sorted(set(lead_hours))) != lead_hours:
            raise ValueError("lead_hours must be unique and increasing")

        initialized_states = []
        for initial_index, initial_time in enumerate(forecast_input.initial_times):
            initial_state = WeatherState(
                values=forecast_input.initial_state.values[initial_index],
                variables=forecast_input.initial_state.variables,
            )
            initialized_states.append(
                self.model.initialize(initial_state, initial_time)
            )
        stacked_states = jax.tree_util.tree_map(
            lambda *leaves: jnp.stack(leaves),
            *initialized_states,
        )
        forecast_parts = []
        if lead_hours[0] == 0:
            initial_values = self._compiled_decode_initial()(stacked_states)
            forecast_parts.append(initial_values[jnp.newaxis])

        positive_lead_hours = tuple(hours for hours in lead_hours if hours > 0)
        if positive_lead_hours:
            positive_values = self._compiled_forecast(positive_lead_hours)(
                self.parameters,
                stacked_states,
            )
            forecast_parts.append(jnp.swapaxes(positive_values, 0, 1))

        forecast_values = (
            forecast_parts[0]
            if len(forecast_parts) == 1
            else jnp.concatenate(forecast_parts, axis=0)
        )
        return WeatherState(
            values=forecast_values,
            variables=self.model.core.output_variables,
        )


def load_hybrid_checkpoint(
    checkpoint_path: str | Path,
    *,
    use_ema: bool = True,
) -> HybridCheckpointModel:
    """Load one trusted local training checkpoint as a forecast model."""
    checkpoint = Path(checkpoint_path).expanduser().resolve()
    restored = restore_checkpoint(checkpoint)
    config = restored.metadata.get("config")
    statistics = restored.metadata.get("statistics")
    if not isinstance(config, dict):
        raise ValueError("hybrid checkpoint is missing its training configuration")
    if not isinstance(statistics, TrainingStatistics):
        raise ValueError("hybrid checkpoint is missing its training statistics")

    dataset_path = str(config["dataset_path"])
    source = WeatherBench2Source(path=dataset_path)
    reference_time = np.datetime64(config["train_end"], "ns")
    longitude, latitude = source.spatial_coordinates(time=reference_time)
    core = make_dinosaur_hybrid_core(
        dycore_name=str(config["dycore_name"]),
        longitude=longitude,
        latitude=latitude,
        input_variables=statistics.input_variables,
        data_path=dataset_path,
        fallback_to_centered_sil3_on_nonfinite=False,
    )
    if core.output_variables != statistics.target_variables:
        raise ValueError("checkpoint statistics do not match hybrid core outputs")

    network = ColumnResidualMLP(
        input_mean=statistics.input_mean,
        input_standard_deviation=statistics.input_standard_deviation,
        output_scale=core.conservative_output_scale,
        hidden_size=int(config["hidden_size"]),
        residual_blocks=int(config["residual_blocks"]),
        normalized_tendency_limit=float(config["normalized_tendency_limit"]),
    )
    decoder = None
    if int(config.get("decoder_hidden_size", 0)) > 0:
        if statistics.decoder_output_scale is None:
            raise ValueError("hybrid checkpoint is missing interface decoder scales")
        decoder_use_raw_observation = bool(
            config.get("decoder_use_raw_observation", False)
        )
        decoder_input_mean = (
            statistics.decoder_input_mean
            if decoder_use_raw_observation
            else statistics.input_mean
        )
        decoder_input_standard_deviation = (
            statistics.decoder_input_standard_deviation
            if decoder_use_raw_observation
            else statistics.input_standard_deviation
        )
        if decoder_input_mean is None or decoder_input_standard_deviation is None:
            raise ValueError(
                "hybrid checkpoint is missing raw-observation decoder statistics"
            )
        decoder_network = ColumnResidualMLP(
            input_mean=decoder_input_mean,
            input_standard_deviation=decoder_input_standard_deviation,
            output_scale=statistics.decoder_output_scale,
            hidden_size=int(config["decoder_hidden_size"]),
            residual_blocks=int(config["decoder_residual_blocks"]),
            normalized_tendency_limit=float(config["normalized_tendency_limit"]),
        )
        decoder = DinosaurNeuralDecoder(
            decoder_network,
            output_variables=core.output_variables,
            include_raw_observation=decoder_use_raw_observation,
        )
    model = PreparedHybridModel(
        core=core,
        corrector=DinosaurNeuralCorrector(network, layer_count=core.layer_count),
        decoder=decoder,
        correction_interval_seconds=float(config["correction_interval_seconds"]),
    )
    host_parameters = (
        restored.training_state.ema_parameters
        if use_ema
        else restored.training_state.parameters
    )
    parameters = jax.tree_util.tree_map(jnp.asarray, host_parameters)
    return HybridCheckpointModel(
        model=model,
        parameters=parameters,
        name=hybrid_checkpoint_model_name(checkpoint, use_ema=use_ema),
    )
