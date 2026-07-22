from dataclasses import dataclass

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from dynamaxx.hybrid.model import HybridModel, PreparedHybridModel
from dynamaxx.weather import WeatherState


@dataclass(frozen=True)
class _LinearCore:
    inner_step_seconds: float = 900.0

    def initialize(self, weather_state, initial_time):
        del initial_time
        return {
            "value": weather_state.values[0, 0, 0],
            "elapsed_seconds": jnp.asarray(0.0),
        }

    def corrector_inputs(self, state):
        return state["value"]

    def to_native_tendency(self, state, nodal_tendency):
        del state
        return nodal_tendency

    def advance_one_inner_step(self, state, additive_tendency):
        return {
            "value": state["value"] + 1.0 + additive_tendency,
            "elapsed_seconds": (
                state["elapsed_seconds"] + self.inner_step_seconds
            ),
        }

    def decode(self, state):
        return WeatherState(
            values=jnp.reshape(state["value"], (1, 1, 1)),
            variables=("x",),
        )


@dataclass(frozen=True)
class _LinearCoreFactory:
    def __call__(self, *, longitude, latitude, input_variables):
        assert longitude.shape == (1,)
        assert latitude.shape == (1,)
        assert input_variables == ("x",)
        return _LinearCore()


def _state(value=2.0):
    return WeatherState(
        values=jnp.asarray([[[value]]]),
        variables=("x",),
    )


def _corrector(parameters, inputs):
    return parameters["scale"] * inputs


def test_step_evaluates_one_correction_and_holds_it_for_two_inner_steps():
    model = PreparedHybridModel(
        core=_LinearCore(),
        corrector=_corrector,
        correction_interval_seconds=1800.0,
    )
    state = model.initialize(_state(), np.datetime64("2020-01-01"))

    next_state, diagnostics = jax.jit(model.step)(
        {"scale": jnp.asarray(0.5)},
        state,
    )

    np.testing.assert_allclose(diagnostics.nodal_tendency, 1.0)
    np.testing.assert_allclose(next_state.core["value"], 6.0)
    np.testing.assert_allclose(next_state.core["elapsed_seconds"], 1800.0)
    assert model.step_seconds == 1800.0
    assert model.inner_step_seconds == 900.0
    assert model.inner_steps_per_step == 2


def test_step_is_differentiable_through_both_inner_steps():
    model = PreparedHybridModel(
        core=_LinearCore(),
        corrector=_corrector,
    )
    state = model.initialize(_state(), np.datetime64("2020-01-01"))

    def terminal_value(scale):
        next_state, _ = model.step({"scale": scale}, state)
        return next_state.core["value"]

    derivative = jax.jit(jax.grad(terminal_value))(jnp.asarray(0.5))

    np.testing.assert_allclose(derivative, 4.0)


def test_zero_correction_recovers_two_uncorrected_inner_steps():
    model = PreparedHybridModel(
        core=_LinearCore(),
        corrector=_corrector,
    )
    state = model.initialize(_state(), np.datetime64("2020-01-01"))

    next_state, _ = model.step({"scale": jnp.asarray(0.0)}, state)

    np.testing.assert_allclose(next_state.core["value"], 4.0)


def test_decode_delegates_to_the_prepared_core():
    model = PreparedHybridModel(core=_LinearCore(), corrector=_corrector)
    state = model.initialize(_state(3.0), np.datetime64("2020-01-01"))

    decoded = model.decode(state)

    assert decoded.variables == ("x",)
    np.testing.assert_allclose(decoded.values, jnp.asarray([[[3.0]]]))


def test_prepare_builds_a_grid_specific_model():
    model = HybridModel(
        name="linear_hybrid",
        core_factory=_LinearCoreFactory(),
        corrector=_corrector,
    )

    prepared = model.prepare(
        longitude=np.asarray([0.0]),
        latitude=np.asarray([45.0]),
        input_variables=("x",),
    )

    assert isinstance(prepared, PreparedHybridModel)
    assert prepared.step_seconds == 1800.0


@pytest.mark.parametrize("correction_interval_seconds", [0.0, np.inf, np.nan])
def test_model_rejects_nonpositive_or_nonfinite_correction_intervals(
    correction_interval_seconds,
):
    with pytest.raises(ValueError, match="positive and finite"):
        PreparedHybridModel(
            core=_LinearCore(),
            corrector=_corrector,
            correction_interval_seconds=correction_interval_seconds,
        )


def test_model_rejects_correction_interval_not_divisible_by_inner_step():
    with pytest.raises(ValueError, match="integer multiple"):
        PreparedHybridModel(
            core=_LinearCore(),
            corrector=_corrector,
            correction_interval_seconds=1350.0,
        )

