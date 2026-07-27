# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import jax
import jax.numpy as jnp
import numpy as np


@jax.tree_util.register_pytree_node_class
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
        """Axes before variable, longitude, and latitude."""
        return tuple(self.values.shape[:-3])

    @property
    def spatial_shape(self) -> tuple[int, int]:
        """The longitude-latitude shape."""
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

    def tree_flatten(self):
        """Return dynamic and static PyTree components for JAX transforms."""
        return (self.values,), self.variables

    @classmethod
    def tree_unflatten(cls, variables: tuple[str, ...], children):
        """Rebuild a state from JAX PyTree components."""
        (values,) = children
        return cls(values=values, variables=variables)


@dataclass(frozen=True)
class ForecastInput:
    """All shared forecast metadata and initial conditions for a model."""

    initial_times: np.ndarray
    valid_times: np.ndarray
    lead_steps: tuple[int, ...]
    lead_hours: tuple[int, ...]
    step_seconds: float
    longitude: np.ndarray
    latitude: np.ndarray
    initial_state: WeatherState

    def __post_init__(self):
        initial_times = np.asarray(self.initial_times, dtype="datetime64[ns]")
        valid_times = np.asarray(self.valid_times, dtype="datetime64[ns]")
        lead_steps = tuple(int(lead_step) for lead_step in self.lead_steps)
        lead_hours = tuple(int(lead_hour) for lead_hour in self.lead_hours)
        longitude = np.asarray(self.longitude, dtype=np.float64)
        latitude = np.asarray(self.latitude, dtype=np.float64)
        assert initial_times.ndim == 1
        assert initial_times.size >= 1
        assert self.initial_state.leading_shape == (initial_times.size,)
        assert longitude.ndim == 1
        assert latitude.ndim == 1
        assert self.initial_state.spatial_shape == (longitude.size, latitude.size)
        assert lead_steps
        assert len(lead_hours) == len(lead_steps)
        assert valid_times.shape == (initial_times.size, len(lead_steps))
        longitude.setflags(write=False)
        latitude.setflags(write=False)
        object.__setattr__(self, "initial_times", initial_times)
        object.__setattr__(self, "valid_times", valid_times)
        object.__setattr__(self, "lead_steps", lead_steps)
        object.__setattr__(self, "lead_hours", lead_hours)
        object.__setattr__(self, "longitude", longitude)
        object.__setattr__(self, "latitude", latitude)

    def with_initial_state(self, initial_state: WeatherState) -> "ForecastInput":
        """Return an equivalent forecast input with a different initial state."""
        return ForecastInput(
            initial_times=self.initial_times,
            valid_times=self.valid_times,
            lead_steps=self.lead_steps,
            lead_hours=self.lead_hours,
            step_seconds=self.step_seconds,
            longitude=self.longitude,
            latitude=self.latitude,
            initial_state=initial_state,
        )

    def slice_initial_time(self, initial_index: int) -> "ForecastInput":
        """Return a single-initialization forecast input."""
        initial_index = int(initial_index)
        return ForecastInput(
            initial_times=self.initial_times[initial_index : initial_index + 1],
            valid_times=self.valid_times[initial_index : initial_index + 1],
            lead_steps=self.lead_steps,
            lead_hours=self.lead_hours,
            step_seconds=self.step_seconds,
            longitude=self.longitude,
            latitude=self.latitude,
            initial_state=WeatherState(
                values=self.initial_state.values[initial_index : initial_index + 1],
                variables=self.initial_state.variables,
            ),
        )

    def asdict(self) -> dict[str, Any]:
        """Return JSON-compatible forecast timing metadata."""
        return {
            "initial_times": [str(time) for time in self.initial_times],
            "valid_times": [
                [str(time) for time in valid_time_row]
                for valid_time_row in self.valid_times
            ],
            "lead_steps": list(self.lead_steps),
            "lead_hours": list(self.lead_hours),
            "step_seconds": self.step_seconds,
        }
