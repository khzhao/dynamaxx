# Copyright 2026 dynamaxx

from dataclasses import dataclass
from typing import Any

import jax
import numpy as np

from dynamaxx.utils.consts import SECONDS_PER_HOUR
from dynamaxx.weather import WeatherState


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
    target_variables: tuple[WeatherVariable, ...]

    def __post_init__(self):
        initial_times = np.asarray(self.initial_times, dtype="datetime64[ns]")
        assert initial_times.ndim == 1
        assert initial_times.size >= 1
        assert self.step_hours >= 1
        assert self.lead_steps
        assert all(lead_step >= 0 for lead_step in self.lead_steps)
        assert self.target_variables

        target_variables = tuple(self.target_variables)

        object.__setattr__(self, "initial_times", initial_times)
        object.__setattr__(
            self,
            "lead_steps",
            tuple(int(lead_step) for lead_step in self.lead_steps),
        )
        object.__setattr__(self, "target_variables", target_variables)

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
    def target_channel_names(self) -> tuple[str, ...]:
        """Return target channel names in scoring order."""
        return tuple(variable.channel_name for variable in self.target_variables)

    def asdict(self) -> dict[str, Any]:
        """Return a JSON-serializable case description."""
        return {
            "name": self.name,
            "initial_times": [str(time) for time in self.initial_times],
            "lead_steps": list(self.lead_steps),
            "lead_hours": list(self.lead_hours),
            "step_hours": self.step_hours,
            "target_variables": [
                variable.asdict() for variable in self.target_variables
            ],
        }


@dataclass(frozen=True)
class ForecastInput:
    """Dynamic initial conditions and lead metadata for one forecast."""

    lead_steps: tuple[int, ...]
    step_seconds: float
    initial_state: WeatherState

    def __post_init__(self):
        assert self.lead_steps
        object.__setattr__(
            self,
            "lead_steps",
            tuple(int(lead_step) for lead_step in self.lead_steps),
        )


@dataclass(frozen=True)
class EvalBatch:
    """Model input plus held-out target truth for scoring."""

    case: EvalCase
    forecast_input: ForecastInput
    truth: WeatherState
    area_weights: jax.Array
