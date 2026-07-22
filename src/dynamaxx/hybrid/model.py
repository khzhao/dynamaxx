# Copyright 2026 dynamaxx

"""Preparation and stepping for additive neural-tendency hybrid models."""

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

import jax
import numpy as np

from dynamaxx.hybrid.api import (
    HybridState,
    HybridStepDiagnostics,
    NeuralTendency,
    PreparedHybridCore,
)
from dynamaxx.weather import WeatherState

Parameters = TypeVar("Parameters")
CoreState = TypeVar("CoreState")
CorrectorInputs = TypeVar("CorrectorInputs")
NodalTendency = TypeVar("NodalTendency")
NativeTendency = TypeVar("NativeTendency")


class HybridCoreFactory(
    Protocol[CoreState, CorrectorInputs, NodalTendency, NativeTendency]
):
    """Construct a grid-specific physical core for a hybrid model."""

    def __call__(
        self,
        *,
        longitude: np.ndarray,
        latitude: np.ndarray,
        input_variables: tuple[str, ...],
    ) -> PreparedHybridCore[
        CoreState,
        CorrectorInputs,
        NodalTendency,
        NativeTendency,
    ]:
        """Prepare coordinates, transforms, forcings, and the inner solver."""


def _positive_finite_seconds(value: float, *, name: str) -> float:
    """Validate and normalize one physical time interval."""
    seconds = float(value)
    if not np.isfinite(seconds) or seconds <= 0.0:
        raise ValueError(f"{name} must be positive and finite")
    return seconds


@dataclass(frozen=True)
class PreparedHybridModel(
    Generic[
        Parameters,
        CoreState,
        CorrectorInputs,
        NodalTendency,
        NativeTendency,
    ]
):
    """Pure prepared model whose public step is one correction interval.

    The neural corrector is evaluated once at the beginning of ``step``. Its
    additive tendency is transformed once and held fixed while the core takes
    the configured number of inner steps.
    """

    core: PreparedHybridCore[
        CoreState,
        CorrectorInputs,
        NodalTendency,
        NativeTendency,
    ]
    corrector: NeuralTendency[Parameters, CorrectorInputs, NodalTendency]
    correction_interval_seconds: float = 1800.0

    def __post_init__(self):
        correction_interval_seconds = _positive_finite_seconds(
            self.correction_interval_seconds,
            name="correction_interval_seconds",
        )
        inner_step_seconds = _positive_finite_seconds(
            self.core.inner_step_seconds,
            name="core.inner_step_seconds",
        )
        interval_ratio = correction_interval_seconds / inner_step_seconds
        inner_steps_per_step = int(round(interval_ratio))
        tolerance = max(1e-9, correction_interval_seconds * 1e-12)
        if inner_steps_per_step < 1 or not np.isclose(
            correction_interval_seconds,
            inner_steps_per_step * inner_step_seconds,
            rtol=0.0,
            atol=tolerance,
        ):
            raise ValueError(
                "correction_interval_seconds must be an integer multiple of "
                "core.inner_step_seconds"
            )
        object.__setattr__(
            self,
            "correction_interval_seconds",
            correction_interval_seconds,
        )

    @property
    def step_seconds(self) -> float:
        """Return the duration of one public neural-coupling step."""
        return self.correction_interval_seconds

    @property
    def inner_step_seconds(self) -> float:
        """Return the duration of one completed dycore step."""
        return float(self.core.inner_step_seconds)

    @property
    def inner_steps_per_step(self) -> int:
        """Return the number of inner dycore steps in one public step."""
        return int(round(self.step_seconds / self.inner_step_seconds))

    def initialize(
        self,
        weather_state: WeatherState,
        initial_time: np.datetime64,
    ) -> HybridState[CoreState]:
        """Encode observations into the complete recurrent hybrid state."""
        return HybridState(
            core=self.core.initialize(weather_state, initial_time),
        )

    def step(
        self,
        parameters: Parameters,
        state: HybridState[CoreState],
    ) -> tuple[HybridState[CoreState], HybridStepDiagnostics[NodalTendency]]:
        """Evaluate one correction and advance one complete coupling block."""
        corrector_inputs = self.core.corrector_inputs(state.core)
        nodal_tendency = self.corrector(parameters, corrector_inputs)
        native_tendency = self.core.to_native_tendency(
            state.core,
            nodal_tendency,
        )

        def advance_inner_step(core_state, _):
            next_core_state = self.core.advance_one_inner_step(
                core_state,
                native_tendency,
            )
            return next_core_state, None

        next_core_state, _ = jax.lax.scan(
            advance_inner_step,
            state.core,
            xs=None,
            length=self.inner_steps_per_step,
        )
        return (
            HybridState(core=next_core_state),
            HybridStepDiagnostics(nodal_tendency=nodal_tendency),
        )

    def decode(self, state: HybridState[CoreState]) -> WeatherState:
        """Decode a hybrid state without changing its recurrent carry."""
        return self.core.decode(state.core)


@dataclass(frozen=True)
class HybridModel(
    Generic[
        Parameters,
        CoreState,
        CorrectorInputs,
        NodalTendency,
        NativeTendency,
    ]
):
    """Unprepared hybrid model that binds a core factory and corrector."""

    name: str
    core_factory: HybridCoreFactory[
        CoreState,
        CorrectorInputs,
        NodalTendency,
        NativeTendency,
    ]
    corrector: NeuralTendency[Parameters, CorrectorInputs, NodalTendency]
    correction_interval_seconds: float = 1800.0

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("name must not be empty")
        correction_interval_seconds = _positive_finite_seconds(
            self.correction_interval_seconds,
            name="correction_interval_seconds",
        )
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(
            self,
            "correction_interval_seconds",
            correction_interval_seconds,
        )

    def prepare(
        self,
        *,
        longitude: np.ndarray,
        latitude: np.ndarray,
        input_variables: tuple[str, ...],
    ) -> PreparedHybridModel[
        Parameters,
        CoreState,
        CorrectorInputs,
        NodalTendency,
        NativeTendency,
    ]:
        """Build the static grid-specific machinery used by training and inference."""
        longitude = np.asarray(longitude, dtype=np.float64)
        latitude = np.asarray(latitude, dtype=np.float64)
        input_variables = tuple(str(variable) for variable in input_variables)
        if longitude.ndim != 1 or longitude.size == 0:
            raise ValueError("longitude must be a non-empty one-dimensional array")
        if latitude.ndim != 1 or latitude.size == 0:
            raise ValueError("latitude must be a non-empty one-dimensional array")
        if not input_variables:
            raise ValueError("input_variables must not be empty")

        core = self.core_factory(
            longitude=longitude,
            latitude=latitude,
            input_variables=input_variables,
        )
        return PreparedHybridModel(
            core=core,
            corrector=self.corrector,
            correction_interval_seconds=self.correction_interval_seconds,
        )
