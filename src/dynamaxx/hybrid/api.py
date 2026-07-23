# Copyright 2026 dynamaxx

"""Public contracts for additive neural-tendency hybrid models."""

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

import jax
import numpy as np

from dynamaxx.weather import WeatherState

Parameters = TypeVar("Parameters")
CoreState = TypeVar("CoreState")
CorrectorInputs = TypeVar("CorrectorInputs")
NodalTendency = TypeVar("NodalTendency")
NativeTendency = TypeVar("NativeTendency")


@jax.tree_util.register_pytree_node_class
@dataclass(frozen=True)
class HybridState(Generic[CoreState]):
    """Complete recurrent carry for one prepared hybrid model.

    ``core`` must contain every value needed to resume a forecast at a public
    coupling boundary. For Dinosaur this includes the native prognostic state,
    auxiliary surface state, and simulation clock.
    """

    core: CoreState

    def tree_flatten(self):
        """Return dynamic children for JAX transformations."""
        return (self.core,), None

    @classmethod
    def tree_unflatten(cls, auxiliary_data, children):
        """Reconstruct a hybrid state from JAX PyTree children."""
        del auxiliary_data
        (core,) = children
        return cls(core=core)


@jax.tree_util.register_pytree_node_class
@dataclass(frozen=True)
class HybridStepDiagnostics(Generic[NodalTendency]):
    """Values produced while advancing one public coupling step.

    The nodal tendency is returned so training code can compute correction
    regularizers or reduced diagnostics without evaluating the neural model a
    second time. Rollout code may discard it when it is not needed.
    """

    nodal_tendency: NodalTendency

    def tree_flatten(self):
        """Return dynamic children for JAX transformations."""
        return (self.nodal_tendency,), None

    @classmethod
    def tree_unflatten(cls, auxiliary_data, children):
        """Reconstruct diagnostics from JAX PyTree children."""
        del auxiliary_data
        (nodal_tendency,) = children
        return cls(nodal_tendency=nodal_tendency)


class NeuralTendency(Protocol[Parameters, CorrectorInputs, NodalTendency]):
    """Pure neural correction evaluated once per coupling interval."""

    def __call__(
        self,
        parameters: Parameters,
        inputs: CorrectorInputs,
    ) -> NodalTendency:
        """Predict additive prognostic tendencies in nodal coordinates."""


class PreparedHybridCore(
    Protocol[CoreState, CorrectorInputs, NodalTendency, NativeTendency]
):
    """Grid-specific physical operations required by a hybrid model.

    This contract supports additive tendency correction only. The core owns
    feature construction, conversion to Dinosaur's native modal tendency, and
    insertion of that tendency into one completed inner integration step.
    """

    @property
    def inner_step_seconds(self) -> float:
        """Duration of one completed inner dycore step."""

    def initialize(
        self,
        weather_state: WeatherState,
        initial_time: np.datetime64,
    ) -> CoreState:
        """Encode one weather state into the complete recurrent core carry."""

    def corrector_inputs(self, state: CoreState) -> CorrectorInputs:
        """Build causal nodal features for one neural evaluation."""

    def to_native_tendency(
        self,
        state: CoreState,
        nodal_tendency: NodalTendency,
    ) -> NativeTendency:
        """Scale and transform a nodal tendency into native coordinates."""

    def advance_one_inner_step(
        self,
        state: CoreState,
        additive_tendency: NativeTendency,
    ) -> CoreState:
        """Advance one inner step with a fixed additive explicit tendency."""

    def decode(self, state: CoreState) -> WeatherState:
        """Decode a recurrent core state into forecast observables."""


class HybridStepper(Protocol[Parameters, CoreState, NodalTendency]):
    """Minimal functional interface consumed by scan-based rollouts."""

    @property
    def step_seconds(self) -> float:
        """Duration of one public neural-coupling step."""

    def step(
        self,
        parameters: Parameters,
        state: HybridState[CoreState],
    ) -> tuple[HybridState[CoreState], HybridStepDiagnostics[NodalTendency]]:
        """Advance exactly one public neural-coupling step."""

    def decode(self, state: HybridState[CoreState]) -> WeatherState:
        """Decode the current state without changing its recurrent carry."""
