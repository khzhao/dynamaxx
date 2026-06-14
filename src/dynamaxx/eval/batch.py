# Copyright 2026 dynamaxx

from typing import Any

import jax
import jax.numpy as jnp

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.eval.core import EvalBatch, EvalCase, ForecastInput, WeatherState


def build_weatherbench2_batch(
    source: WeatherBench2Source,
    case: EvalCase,
    *,
    dtype: Any = jnp.float32,
) -> EvalBatch:
    """Load one model-agnostic evaluation batch from WeatherBench2."""
    initial_channel_names = source.state_channel_names(time=case.initial_times[0])
    initial_values = source.read_state_times(
        case.initial_times,
        channels=initial_channel_names,
        dtype=dtype,
    )
    truth_values = _read_valid_times(
        source,
        case,
        channels=case.target_channel_names,
        dtype=dtype,
    )
    longitude, latitude = source.spatial_coordinates(time=case.initial_times[0])

    forecast_input = ForecastInput(
        initial_times=case.initial_times,
        valid_times=case.valid_times,
        lead_steps=case.lead_steps,
        lead_hours=case.lead_hours,
        step_seconds=case.step_seconds,
        longitude=longitude,
        latitude=latitude,
        initial_state=WeatherState(
            values=initial_values,
            variables=initial_channel_names,
        ),
    )
    return EvalBatch(
        case=case,
        forecast_input=forecast_input,
        truth=WeatherState(
            values=truth_values,
            variables=case.target_channel_names,
        ),
        area_weights=jnp.asarray(
            source.area_weights(time=case.initial_times[0]),
            dtype=dtype,
        ),
    )


def _read_valid_times(
    source: WeatherBench2Source,
    case: EvalCase,
    *,
    channels: tuple[str, ...],
    dtype: Any,
) -> jax.Array:
    values = source.read_state_times(
        case.valid_times.reshape(-1),
        channels=channels,
        dtype=dtype,
    )
    shape = (
        case.initial_times.size,
        len(case.lead_steps),
        len(channels),
        *values.shape[-2:],
    )
    values = jnp.reshape(values, shape)
    return jnp.swapaxes(values, 0, 1)
