# Copyright 2026 dynamaxx

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.utils.consts import SECONDS_PER_HOUR


@dataclass(frozen=True)
class WeatherState:
    """Named weather variables with longitude-latitude spatial axes.

    Values are shaped as (*leading, variable, longitude, latitude). The leading
    axes may contain lead time, initialization time, ensemble member, or any
    other model-specific batch axes.
    """

    values: jax.Array
    variables: tuple[str, ...]

    def __post_init__(self):
        values = jnp.asarray(self.values)
        variables = tuple(str(variable) for variable in self.variables)
        assert values.ndim >= 3
        assert values.shape[-3] == len(variables)
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "variables", variables)

    @property
    def leading_shape(self) -> tuple[int, ...]:
        """Return axes before variable, longitude, and latitude."""
        return tuple(self.values.shape[:-3])

    @property
    def spatial_shape(self) -> tuple[int, int]:
        """Return longitude-latitude shape."""
        longitude_count, latitude_count = self.values.shape[-2:]
        return int(longitude_count), int(latitude_count)

    def variable_indices(self, variables: Sequence[str]) -> np.ndarray:
        """Return integer indices for variables in the current state."""
        variable_to_index = {
            variable: variable_index
            for variable_index, variable in enumerate(self.variables)
        }
        missing_variables = [
            variable for variable in variables if variable not in variable_to_index
        ]
        assert not missing_variables, f"unknown variables {missing_variables}"
        return np.asarray(
            [variable_to_index[variable] for variable in variables],
            dtype=np.int64,
        )

    def select(self, variables: Sequence[str]) -> "WeatherState":
        """Return a state containing variables in the requested order."""
        variables = tuple(str(variable) for variable in variables)
        indices = jnp.asarray(self.variable_indices(variables), dtype=jnp.int32)
        values = jnp.take(self.values, indices, axis=-3)
        return WeatherState(values=values, variables=variables)

    def with_values(self, values: jax.Array) -> "WeatherState":
        """Return a new state with the same variable names and new values."""
        return WeatherState(values=values, variables=self.variables)


@dataclass(frozen=True)
class WeatherVariable:
    """A semantic weather variable stored as a packed WeatherBench2 channel."""

    variable: str
    level: int | None = None
    title: str | None = None
    unit: str | None = None
    history_hours: int = 0

    def __post_init__(self):
        assert self.history_hours >= 0

    @property
    def channel_name(self) -> str:
        """Return the WeatherBench2 source channel name."""
        if self.level is None:
            return self.variable
        return f"{self.variable}_{int(self.level)}"

    @property
    def state_name(self) -> str:
        """Return the packed model-state variable name."""
        if self.history_hours == 0:
            return self.channel_name
        return f"{self.channel_name}__minus_{self.history_hours}h"

    @property
    def label(self) -> str:
        """Return a readable stable label for metric tables."""
        return self.title or self.channel_name

    def with_history(self, history_hours: int) -> "WeatherVariable":
        """Return this source variable shifted into the past."""
        return WeatherVariable(
            variable=self.variable,
            level=self.level,
            title=self.title,
            unit=self.unit,
            history_hours=history_hours,
        )

    def asdict(self) -> dict[str, Any]:
        """Return a JSON-serializable variable description."""
        return {
            "variable": self.variable,
            "level": self.level,
            "channel_name": self.channel_name,
            "state_name": self.state_name,
            "title": self.title,
            "unit": self.unit,
            "history_hours": self.history_hours,
        }


@dataclass(frozen=True)
class EvalCase:
    """A fixed benchmark definition independent of model implementation."""

    name: str
    initial_times: np.ndarray
    lead_steps: tuple[int, ...]
    step_hours: int
    prognostic_variables: tuple[WeatherVariable, ...]
    target_variables: tuple[WeatherVariable, ...]
    forcing_variables: tuple[WeatherVariable, ...] = ()
    static_variables: tuple[str, ...] = ()

    def __post_init__(self):
        initial_times = np.asarray(self.initial_times, dtype="datetime64[ns]")
        assert initial_times.ndim == 1
        assert initial_times.size >= 1
        assert self.step_hours >= 1
        assert self.lead_steps
        assert all(lead_step >= 0 for lead_step in self.lead_steps)
        assert self.prognostic_variables
        assert self.target_variables

        prognostic_variables = tuple(self.prognostic_variables)
        target_variables = tuple(self.target_variables)
        prognostic_channels = {variable.state_name for variable in prognostic_variables}
        missing_targets = [
            variable.state_name
            for variable in target_variables
            if variable.state_name not in prognostic_channels
        ]
        assert not missing_targets, (
            f"target variables missing from prognostic variables {missing_targets}"
        )

        object.__setattr__(self, "initial_times", initial_times)
        object.__setattr__(
            self,
            "lead_steps",
            tuple(int(lead_step) for lead_step in self.lead_steps),
        )
        object.__setattr__(self, "prognostic_variables", prognostic_variables)
        object.__setattr__(self, "target_variables", target_variables)
        object.__setattr__(self, "forcing_variables", tuple(self.forcing_variables))
        object.__setattr__(
            self,
            "static_variables",
            tuple(str(variable) for variable in self.static_variables),
        )

    @property
    def step_seconds(self) -> float:
        """Return the model step size in seconds."""
        return float(self.step_hours * SECONDS_PER_HOUR)

    @property
    def lead_hours(self) -> tuple[int, ...]:
        """Return lead times in hours."""
        return tuple(lead_step * self.step_hours for lead_step in self.lead_steps)

    @property
    def valid_times(self) -> np.ndarray:
        """Return verification times with shape (initial_time, lead)."""
        lead_offsets = np.asarray(self.lead_hours, dtype="timedelta64[h]")
        return self.initial_times[:, np.newaxis] + lead_offsets[np.newaxis, :]

    @property
    def prognostic_channel_names(self) -> tuple[str, ...]:
        """Return prognostic source channel names in model input order."""
        return tuple(variable.channel_name for variable in self.prognostic_variables)

    @property
    def prognostic_state_names(self) -> tuple[str, ...]:
        """Return prognostic packed-state names in model input order."""
        return tuple(variable.state_name for variable in self.prognostic_variables)

    @property
    def target_channel_names(self) -> tuple[str, ...]:
        """Return target packed-state names in scoring order."""
        return tuple(variable.state_name for variable in self.target_variables)

    @property
    def target_source_channel_names(self) -> tuple[str, ...]:
        """Return target source channel names in scoring order."""
        return tuple(variable.channel_name for variable in self.target_variables)

    @property
    def forcing_channel_names(self) -> tuple[str, ...]:
        """Return prescribed forcing source channel names in input order."""
        return tuple(variable.channel_name for variable in self.forcing_variables)

    @property
    def forcing_state_names(self) -> tuple[str, ...]:
        """Return prescribed forcing packed-state names in input order."""
        return tuple(variable.state_name for variable in self.forcing_variables)

    def asdict(self) -> dict[str, Any]:
        """Return a JSON-serializable case description."""
        return {
            "name": self.name,
            "initial_times": [str(time) for time in self.initial_times],
            "lead_steps": list(self.lead_steps),
            "lead_hours": list(self.lead_hours),
            "step_hours": self.step_hours,
            "prognostic_variables": [
                variable.asdict() for variable in self.prognostic_variables
            ],
            "target_variables": [
                variable.asdict() for variable in self.target_variables
            ],
            "forcing_variables": [
                variable.asdict() for variable in self.forcing_variables
            ],
            "static_variables": list(self.static_variables),
        }


@dataclass(frozen=True)
class ForecastInput:
    """All data a model may use to produce a forecast."""

    initial_times: np.ndarray
    valid_times: np.ndarray
    lead_steps: tuple[int, ...]
    lead_hours: tuple[int, ...]
    step_seconds: float
    initial_state: WeatherState
    forcing: WeatherState | None = None
    static: Mapping[str, jax.Array] = field(default_factory=dict)

    def __post_init__(self):
        initial_times = np.asarray(self.initial_times, dtype="datetime64[ns]")
        valid_times = np.asarray(self.valid_times, dtype="datetime64[ns]")
        assert initial_times.ndim == 1
        assert valid_times.shape == (initial_times.size, len(self.lead_steps))
        object.__setattr__(self, "initial_times", initial_times)
        object.__setattr__(self, "valid_times", valid_times)
        object.__setattr__(self, "static", dict(self.static))


@dataclass(frozen=True)
class EvalBatch:
    """Model input plus held-out target truth for scoring."""

    case: EvalCase
    forecast_input: ForecastInput
    truth: WeatherState
    area_weights: jax.Array
