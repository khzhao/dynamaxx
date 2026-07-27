# Copyright 2026 dynamaxx

"""Preparation and stepping for additive neural-tendency hybrid models."""

from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, TypeVar

import jax
import numpy as np

from dynamaxx.hybrid.api import (
    HybridState,
    HybridStepDiagnostics,
    NeuralDecoder,
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
    decoder: NeuralDecoder[Parameters, CorrectorInputs, WeatherState] | None = None
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
        """Duration of one public neural-coupling step."""
        return self.correction_interval_seconds

    @property
    def inner_step_seconds(self) -> float:
        """Duration of one completed dycore step."""
        return float(self.core.inner_step_seconds)

    @property
    def inner_steps_per_step(self) -> int:
        """Number of inner dycore steps in one public step."""
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
        corrector_parameters = (
            parameters if self.decoder is None else parameters["corrector"]
        )
        nodal_tendency = self.corrector(corrector_parameters, corrector_inputs)
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

    def observe(
        self,
        parameters: Parameters,
        state: HybridState[CoreState],
    ) -> WeatherState:
        """Decode a state and apply the learned observation residual if present."""
        raw_observation = self.decode(state)
        if self.decoder is None:
            return raw_observation
        decoder_inputs = self.core.corrector_inputs(state.core)
        return self.decoder(
            parameters["decoder"],
            decoder_inputs,
            raw_observation,
        )

    def advance(
        self,
        parameters: Parameters,
        state: HybridState[CoreState],
        *,
        duration_seconds: float,
    ) -> HybridState[CoreState]:
        """Advance an exact physical duration without retaining intermediates."""
        from dynamaxx.hybrid.rollout import advance_duration

        return advance_duration(
            self,
            parameters,
            state,
            duration_seconds=duration_seconds,
        )


@dataclass
class HybridModel:
    """Simple public hybrid model that prepares its named core on first use."""

    neural_model: Any
    dycore_name: str = "dino_rskin_apv"
    correction_interval_seconds: float = 1800.0
    _prepared: PreparedHybridModel[Any, Any, Any, Any, Any] | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _input_variables: tuple[str, ...] | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _spatial_shape: tuple[int, int] | None = field(
        default=None,
        init=False,
        repr=False,
    )

    def __post_init__(self):
        if not callable(self.neural_model):
            raise TypeError("neural_model must be callable")
        if not self.dycore_name.strip():
            raise ValueError("dycore_name must not be empty")
        correction_interval_seconds = _positive_finite_seconds(
            self.correction_interval_seconds,
            name="correction_interval_seconds",
        )
        self.dycore_name = self.dycore_name.strip()
        self.correction_interval_seconds = correction_interval_seconds

    @property
    def name(self) -> str:
        """Stable forecast-model name."""
        return f"hybrid_{self.dycore_name}"

    @property
    def step_seconds(self) -> float:
        """Duration of one neural-correction interval."""
        return self.correction_interval_seconds

    def _prepare(self, weather_state: WeatherState) -> None:
        """Infer the regular input grid and construct hidden core machinery."""
        if self._prepared is not None:
            if weather_state.variables != self._input_variables:
                raise ValueError("weather_state variables changed after initialization")
            if weather_state.spatial_shape != self._spatial_shape:
                raise ValueError("weather_state grid changed after initialization")
            return
        from dynamaxx.hybrid.dinosaur import DinosaurHybridCoreFactory

        longitude_count, latitude_count = weather_state.spatial_shape
        longitude = np.linspace(
            0.0,
            360.0,
            longitude_count,
            endpoint=False,
            dtype=np.float64,
        )
        latitude = np.linspace(
            -90.0,
            90.0,
            latitude_count,
            dtype=np.float64,
        )
        core = DinosaurHybridCoreFactory(self.dycore_name)(
            longitude=longitude,
            latitude=latitude,
            input_variables=weather_state.variables,
        )
        self._prepared = PreparedHybridModel(
            core=core,
            corrector=self.neural_model,
            correction_interval_seconds=self.correction_interval_seconds,
        )
        self._input_variables = weather_state.variables
        self._spatial_shape = weather_state.spatial_shape

    def initialize(
        self,
        weather_state: WeatherState,
        initial_time: np.datetime64,
    ) -> HybridState[Any]:
        """Initialize the recurrent state from one weather analysis."""
        self._prepare(weather_state)
        assert self._prepared is not None
        return self._prepared.initialize(weather_state, initial_time)

    def step(
        self,
        parameters: Any,
        state: HybridState[Any],
    ) -> HybridState[Any]:
        """Advance one configured neural-correction interval."""
        if self._prepared is None:
            raise RuntimeError("initialize must be called before step")
        next_state, _ = self._prepared.step(parameters, state)
        return next_state

    def advance(
        self,
        parameters: Any,
        state: HybridState[Any],
        *,
        duration_seconds: float,
    ) -> HybridState[Any]:
        """Advance an exact physical duration."""
        if self._prepared is None:
            raise RuntimeError("initialize must be called before advance")
        return self._prepared.advance(
            parameters,
            state,
            duration_seconds=duration_seconds,
        )

    def decode(self, state: HybridState[Any]) -> WeatherState:
        """Decode forecast observables from the current recurrent state."""
        if self._prepared is None:
            raise RuntimeError("initialize must be called before decode")
        return self._prepared.decode(state)
