# Copyright 2026 dynamaxx

from dataclasses import dataclass

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from dynamaxx.hybrid.checkpoint import (
    HybridCheckpointModel,
    hybrid_checkpoint_model_name,
)
from dynamaxx.hybrid.model import HybridModel, PreparedHybridModel
from dynamaxx.weather import ForecastInput, WeatherState


def test_public_hybrid_api_is_minimal():
    """Only construction and local-checkpoint loading are package-level API."""
    import dynamaxx.hybrid as hybrid

    assert hybrid.__all__ == ["HybridModel", "load_hybrid_checkpoint"]


@dataclass(frozen=True)
class _LinearCore:
    inner_step_seconds: float = 900.0
    output_variables: tuple[str, ...] = ("x",)

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
            "elapsed_seconds": (state["elapsed_seconds"] + self.inner_step_seconds),
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


def _decoder(parameters, inputs, raw_observation):
    del inputs
    return raw_observation.with_values(raw_observation.values + parameters["offset"])


def test_step_evaluates_one_correction_and_holds_it_for_two_inner_steps():
    """One correction must remain fixed across the complete coupling block."""
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
    """Gradients must include every inner step in the coupling block."""
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
    """A zero tendency must reduce to the prepared core integration."""
    model = PreparedHybridModel(
        core=_LinearCore(),
        corrector=_corrector,
    )
    state = model.initialize(_state(), np.datetime64("2020-01-01"))

    next_state, _ = model.step({"scale": jnp.asarray(0.0)}, state)

    np.testing.assert_allclose(next_state.core["value"], 4.0)


def test_decode_delegates_to_the_prepared_core():
    """Prepared model decoding must preserve the core's named output."""
    model = PreparedHybridModel(core=_LinearCore(), corrector=_corrector)
    state = model.initialize(_state(3.0), np.datetime64("2020-01-01"))

    decoded = model.decode(state)

    assert decoded.variables == ("x",)
    np.testing.assert_allclose(decoded.values, jnp.asarray([[[3.0]]]))


def test_observe_applies_parameterized_decoder_without_changing_raw_decode():
    """Learned decoding must alter observations but not the recurrent state."""
    model = PreparedHybridModel(
        core=_LinearCore(),
        corrector=_corrector,
        decoder=_decoder,
    )
    state = model.initialize(_state(3.0), np.datetime64("2020-01-01"))
    parameters = {
        "corrector": {"scale": jnp.asarray(0.0)},
        "decoder": {"offset": jnp.asarray(2.0)},
    }

    raw = model.decode(state)
    observed = model.observe(parameters, state)

    np.testing.assert_allclose(raw.values, jnp.asarray([[[3.0]]]))
    np.testing.assert_allclose(observed.values, jnp.asarray([[[5.0]]]))


def test_public_model_initializes_and_advances_with_simple_api(monkeypatch):
    """The public wrapper must expose the minimal recurrent workflow."""
    from dynamaxx.hybrid import dinosaur as hybrid_dinosaur

    monkeypatch.setattr(
        hybrid_dinosaur,
        "DinosaurHybridCoreFactory",
        lambda dycore_name: _LinearCoreFactory(),
    )
    model = HybridModel(
        neural_model=_corrector,
        dycore_name="linear",
    )
    state = model.initialize(
        _state(),
        np.datetime64("2020-01-01"),
    )
    state = model.step({"scale": jnp.asarray(0.0)}, state)
    state = model.advance(
        {"scale": jnp.asarray(0.0)},
        state,
        duration_seconds=1800.0,
    )
    forecast = model.decode(state)

    assert model.name == "hybrid_linear"
    assert model.step_seconds == 1800.0
    np.testing.assert_allclose(forecast.values, jnp.asarray([[[6.0]]]))


def test_checkpoint_model_forecasts_batched_initializations_at_named_leads():
    """Checkpoint inference must support lead zero and positive named leads."""
    model = HybridCheckpointModel(
        model=PreparedHybridModel(core=_LinearCore(), corrector=_corrector),
        parameters={"scale": jnp.asarray(0.0)},
        name="hybrid-test",
        maximum_scan_window_hours=1,
    )
    forecast_input = ForecastInput(
        initial_times=np.asarray(
            ["2020-01-01T00:00:00", "2020-01-01T12:00:00"],
            dtype="datetime64[ns]",
        ),
        valid_times=np.asarray(
            [
                [
                    "2020-01-01T00:00:00",
                    "2020-01-01T01:00:00",
                    "2020-01-01T02:00:00",
                ],
                [
                    "2020-01-01T12:00:00",
                    "2020-01-01T13:00:00",
                    "2020-01-01T14:00:00",
                ],
            ],
            dtype="datetime64[ns]",
        ),
        lead_steps=(0, 1, 2),
        lead_hours=(0, 1, 2),
        step_seconds=3600.0,
        longitude=np.asarray([0.0]),
        latitude=np.asarray([0.0]),
        initial_state=WeatherState(
            values=jnp.asarray([[[[2.0]]], [[[3.0]]]]),
            variables=("x",),
        ),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.leading_shape == (3, 2)
    assert forecast.variables == ("x",)
    np.testing.assert_allclose(
        forecast.values[:, :, 0, 0, 0],
        jnp.asarray([[2.0, 3.0], [6.0, 7.0], [10.0, 11.0]]),
    )


def test_checkpoint_model_name_identifies_stage_step_and_parameter_set(tmp_path):
    """Checkpoint model names must identify the source and parameter choice."""
    checkpoint = tmp_path / "360h" / "step_000000323.pkl"

    assert hybrid_checkpoint_model_name(checkpoint) == (
        "hybrid-360h-step-000000323-ema"
    )
    assert hybrid_checkpoint_model_name(checkpoint, use_ema=False) == (
        "hybrid-360h-step-000000323-raw"
    )


@pytest.mark.parametrize("correction_interval_seconds", [0.0, np.inf, np.nan])
def test_model_rejects_nonpositive_or_nonfinite_correction_intervals(
    correction_interval_seconds,
):
    """Coupling intervals must be physically meaningful finite durations."""
    with pytest.raises(ValueError, match="positive and finite"):
        PreparedHybridModel(
            core=_LinearCore(),
            corrector=_corrector,
            correction_interval_seconds=correction_interval_seconds,
        )


def test_model_rejects_correction_interval_not_divisible_by_inner_step():
    """A coupling block must contain an integer number of core steps."""
    with pytest.raises(ValueError, match="integer multiple"):
        PreparedHybridModel(
            core=_LinearCore(),
            corrector=_corrector,
            correction_interval_seconds=1350.0,
        )
