# Copyright 2026 dynamaxx

from typing import Any

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.eval.core import EvalBatch, EvalCase, ForecastInput, WeatherState
from dynamaxx.utils.consts import EARTH_ANGULAR_VELOCITY


def build_weatherbench2_batch(
    source: WeatherBench2Source,
    case: EvalCase,
    *,
    dtype: Any = jnp.float32,
) -> EvalBatch:
    """Load one model-agnostic evaluation batch from WeatherBench2."""
    initial_values = _read_initial_state(source, case, dtype=dtype)
    truth_values = _read_valid_times(
        source,
        case,
        channels=case.target_source_channel_names,
        dtype=dtype,
    )
    forcing = None
    if case.forcing_variables:
        forcing = WeatherState(
            values=_read_valid_times(
                source,
                case,
                channels=case.forcing_channel_names,
                dtype=dtype,
            ),
            variables=case.forcing_state_names,
        )

    forecast_input = ForecastInput(
        initial_times=case.initial_times,
        valid_times=case.valid_times,
        lead_steps=case.lead_steps,
        lead_hours=case.lead_hours,
        step_seconds=case.step_seconds,
        initial_state=WeatherState(
            values=initial_values,
            variables=case.prognostic_state_names,
        ),
        forcing=forcing,
        static=_read_static_variables(source, case, dtype=dtype),
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


def _read_initial_state(
    source: WeatherBench2Source,
    case: EvalCase,
    *,
    dtype: Any,
) -> jax.Array:
    arrays_by_position: list[jax.Array | None] = [None] * len(case.prognostic_variables)
    history_hours = tuple(
        dict.fromkeys(variable.history_hours for variable in case.prognostic_variables)
    )
    for hours in history_hours:
        positions = [
            index
            for index, variable in enumerate(case.prognostic_variables)
            if variable.history_hours == hours
        ]
        channels = tuple(
            case.prognostic_variables[position].channel_name for position in positions
        )
        times = case.initial_times - np.timedelta64(int(hours), "h")
        values = source.read_state_times(times, channels=channels, dtype=dtype)
        for group_index, position in enumerate(positions):
            arrays_by_position[position] = values[:, group_index : group_index + 1]

    arrays = tuple(array for array in arrays_by_position if array is not None)
    assert len(arrays) == len(arrays_by_position)
    return jnp.concatenate(arrays, axis=1)


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


def _read_static_variables(
    source: WeatherBench2Source,
    case: EvalCase,
    *,
    dtype: Any,
) -> dict[str, jax.Array]:
    static = {}
    longitude, latitude = source.spatial_coordinates(time=case.initial_times[0])
    latitude_radians = np.deg2rad(latitude)
    for variable in case.static_variables:
        match variable:
            case "longitude":
                static[variable] = jnp.asarray(np.deg2rad(longitude), dtype=dtype)
            case "latitude":
                static[variable] = jnp.asarray(latitude_radians, dtype=dtype)
            case "sin_latitude":
                static[variable] = jnp.asarray(np.sin(latitude_radians), dtype=dtype)
            case "area_weights":
                static[variable] = jnp.asarray(
                    source.area_weights(time=case.initial_times[0]),
                    dtype=dtype,
                )
            case "coriolis":
                static[variable] = jnp.asarray(
                    2 * EARTH_ANGULAR_VELOCITY * np.sin(latitude_radians),
                    dtype=dtype,
                )
            case _:
                static[variable] = source.read_constants(
                    [variable],
                    dtype=dtype,
                )[0]
    return static
