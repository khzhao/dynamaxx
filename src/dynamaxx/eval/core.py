# Copyright 2026 dynamaxx

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.utils.consts import HOURS_PER_DAY, SECONDS_PER_HOUR


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
        return tuple(self.values.shape[-2:])

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

    @property
    def channel_name(self) -> str:
        """Return the packed state channel name."""
        if self.level is None:
            return self.variable
        return f"{self.variable}_{int(self.level)}"

    @property
    def label(self) -> str:
        """Return a readable stable label for metric tables."""
        return self.title or self.channel_name

    def asdict(self) -> dict[str, Any]:
        """Return a JSON-serializable variable description."""
        return {
            "variable": self.variable,
            "level": self.level,
            "channel_name": self.channel_name,
            "title": self.title,
            "unit": self.unit,
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
        prognostic_channels = {
            variable.channel_name for variable in prognostic_variables
        }
        missing_targets = [
            variable.channel_name
            for variable in target_variables
            if variable.channel_name not in prognostic_channels
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
        """Return prognostic channel names in model input order."""
        return tuple(variable.channel_name for variable in self.prognostic_variables)

    @property
    def target_channel_names(self) -> tuple[str, ...]:
        """Return target channel names in scoring order."""
        return tuple(variable.channel_name for variable in self.target_variables)

    @property
    def forcing_channel_names(self) -> tuple[str, ...]:
        """Return prescribed forcing channel names in input order."""
        return tuple(variable.channel_name for variable in self.forcing_variables)

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
    static: Mapping[str, jax.Array] | None = None

    def __post_init__(self):
        initial_times = np.asarray(self.initial_times, dtype="datetime64[ns]")
        valid_times = np.asarray(self.valid_times, dtype="datetime64[ns]")
        assert initial_times.ndim == 1
        assert valid_times.shape == (initial_times.size, len(self.lead_steps))
        object.__setattr__(self, "initial_times", initial_times)
        object.__setattr__(self, "valid_times", valid_times)
        object.__setattr__(self, "static", dict(self.static or {}))


@dataclass(frozen=True)
class EvalBatch:
    """Model input plus held-out target truth for scoring."""

    case: EvalCase
    forecast_input: ForecastInput
    truth: WeatherState
    area_weights: jax.Array


class ForecastModel(Protocol):
    """Protocol for models that can forecast named weather states."""

    name: str

    def forecast(self, forecast_input: ForecastInput) -> WeatherState:
        """Return a trajectory shaped as (lead, init, variable, lon, lat)."""


DEFAULT_VARIABLES = (
    WeatherVariable("2m_temperature", title="2 m temperature", unit="K"),
    WeatherVariable(
        "mean_sea_level_pressure",
        title="Mean sea level pressure",
        unit="Pa",
    ),
    WeatherVariable(
        "geopotential",
        level=500,
        title="500 hPa geopotential",
        unit="m2 s-2",
    ),
    WeatherVariable(
        "10m_u_component_of_wind",
        title="10 m zonal wind",
        unit="m s-1",
    ),
)

DEFAULT_LEAD_DAYS = tuple(range(1, 16))


def lead_days_to_steps(
    lead_days: tuple[int | float, ...],
    *,
    step_hours: int,
) -> tuple[int, ...]:
    """Convert lead times in days to integer model step indices."""
    steps_per_day = HOURS_PER_DAY / step_hours
    lead_steps = tuple(int(round(lead_day * steps_per_day)) for lead_day in lead_days)
    assert all(
        np.isclose(lead_step, lead_day * steps_per_day)
        for lead_step, lead_day in zip(lead_steps, lead_days, strict=True)
    )
    return lead_steps


def daily_initial_times(start_date: str, end_date: str) -> np.ndarray:
    """Return daily initialization times in an inclusive date range."""
    start = np.datetime64(start_date, "D")
    end = np.datetime64(end_date, "D")
    assert start <= end
    day_count = int((end - start) / np.timedelta64(1, "D")) + 1
    return start + np.arange(day_count).astype("timedelta64[D]")


def fixed_case(
    name: str,
    initial_times: np.ndarray | list[str] | tuple[str, ...],
    *,
    lead_days: tuple[int | float, ...] = DEFAULT_LEAD_DAYS,
    step_hours: int = 6,
    prognostic_variables: tuple[WeatherVariable, ...] = DEFAULT_VARIABLES,
    target_variables: tuple[WeatherVariable, ...] | None = None,
    forcing_variables: tuple[WeatherVariable, ...] = (),
    static_variables: tuple[str, ...] = (),
) -> EvalCase:
    """Create a fixed eval case from explicit initialization times."""
    return EvalCase(
        name=name,
        initial_times=np.asarray(initial_times, dtype="datetime64[ns]"),
        lead_steps=lead_days_to_steps(lead_days, step_hours=step_hours),
        step_hours=step_hours,
        prognostic_variables=prognostic_variables,
        target_variables=target_variables or prognostic_variables,
        forcing_variables=forcing_variables,
        static_variables=static_variables,
    )


def smoke_case(
    *,
    prognostic_variables: tuple[WeatherVariable, ...] = DEFAULT_VARIABLES,
    target_variables: tuple[WeatherVariable, ...] | None = None,
    forcing_variables: tuple[WeatherVariable, ...] = (),
    static_variables: tuple[str, ...] = (),
) -> EvalCase:
    """Return a tiny deterministic case for wiring and regression checks."""
    return fixed_case(
        "smoke",
        [
            "2020-01-01T00:00:00",
            "2020-04-01T00:00:00",
            "2020-07-01T00:00:00",
            "2020-10-01T00:00:00",
        ],
        lead_days=(1, 5),
        prognostic_variables=prognostic_variables,
        target_variables=target_variables,
        forcing_variables=forcing_variables,
        static_variables=static_variables,
    )


def fast_case(
    *,
    prognostic_variables: tuple[WeatherVariable, ...] = DEFAULT_VARIABLES,
    target_variables: tuple[WeatherVariable, ...] | None = None,
    forcing_variables: tuple[WeatherVariable, ...] = (),
    static_variables: tuple[str, ...] = (),
) -> EvalCase:
    """Return a seasonal sample intended for routine agent iteration."""
    return fixed_case(
        "fast",
        [
            "2019-01-01T00:00:00",
            "2019-01-15T00:00:00",
            "2019-02-01T00:00:00",
            "2019-03-01T00:00:00",
            "2019-04-01T00:00:00",
            "2019-05-01T00:00:00",
            "2019-06-01T00:00:00",
            "2019-07-01T00:00:00",
            "2019-08-01T00:00:00",
            "2019-09-01T00:00:00",
            "2019-10-01T00:00:00",
            "2019-11-01T00:00:00",
            "2019-12-01T00:00:00",
            "2019-12-15T00:00:00",
        ],
        prognostic_variables=prognostic_variables,
        target_variables=target_variables,
        forcing_variables=forcing_variables,
        static_variables=static_variables,
    )


def candidate_year_case(
    year: int,
    *,
    prognostic_variables: tuple[WeatherVariable, ...] = DEFAULT_VARIABLES,
    target_variables: tuple[WeatherVariable, ...] | None = None,
    forcing_variables: tuple[WeatherVariable, ...] = (),
    static_variables: tuple[str, ...] = (),
) -> EvalCase:
    """Return a daily-start benchmark case for one full year."""
    return fixed_case(
        f"candidate-{year}",
        daily_initial_times(f"{year}-01-01", f"{year}-12-31"),
        prognostic_variables=prognostic_variables,
        target_variables=target_variables,
        forcing_variables=forcing_variables,
        static_variables=static_variables,
    )
