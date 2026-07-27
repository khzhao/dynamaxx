# Copyright 2026 dynamaxx

"""Tests for scan-based hybrid-model rollout helpers."""

from dataclasses import dataclass

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from dynamaxx.hybrid.model import PreparedHybridModel
from dynamaxx.hybrid.rollout import (
    advance,
    advance_duration,
    rollout,
    rollout_at_durations,
    rollout_at_durations_with_tendency_statistics,
)
from dynamaxx.weather import WeatherState


@dataclass(frozen=True)
class _IncrementCore:
    inner_step_seconds: float = 900.0

    def initialize(self, weather_state, initial_time):
        del initial_time
        return weather_state.values[0, 0, 0]

    def corrector_inputs(self, state):
        return state

    def to_native_tendency(self, state, nodal_tendency):
        del state
        return nodal_tendency

    def advance_one_inner_step(self, state, additive_tendency):
        return state + 1.0 + additive_tendency

    def decode(self, state):
        return WeatherState(
            values=jnp.reshape(state, (1, 1, 1)),
            variables=("x",),
        )


def _constant_corrector(parameters, inputs):
    del inputs
    return parameters["correction"]


def _model_and_state():
    model = PreparedHybridModel(
        core=_IncrementCore(),
        corrector=_constant_corrector,
    )
    weather_state = WeatherState(
        values=jnp.asarray([[[1.0]]]),
        variables=("x",),
    )
    state = model.initialize(weather_state, np.datetime64("2020-01-01"))
    return model, state


def test_advance_returns_only_the_final_recurrent_state():
    """Advance discards intermediate states and returns the last carry."""
    model, state = _model_and_state()

    final_state = advance(
        model,
        {"correction": jnp.asarray(0.0)},
        state,
        steps=3,
    )

    np.testing.assert_allclose(final_state.core, 7.0)


def test_rollout_observes_only_requested_coupling_boundaries():
    """Rollout decodes only the requested public coupling boundaries."""
    model, state = _model_and_state()

    final_state, trajectory = rollout(
        model,
        {"correction": jnp.asarray(0.0)},
        state,
        steps=6,
        save_every=2,
        observe=model.decode,
        include_initial=True,
    )

    np.testing.assert_allclose(final_state.core, 13.0)
    np.testing.assert_allclose(
        trajectory.values[:, 0, 0, 0],
        jnp.asarray([1.0, 5.0, 9.0, 13.0]),
    )
    assert trajectory.variables == ("x",)


def test_rollout_supports_bptt_through_public_steps():
    """The ordinary advance path preserves exact temporal gradients."""
    model, state = _model_and_state()

    def terminal_value(correction):
        final_state = advance(
            model,
            {"correction": correction},
            state,
            steps=4,
        )
        return final_state.core

    derivative = jax.jit(jax.grad(terminal_value))(jnp.asarray(0.0))

    np.testing.assert_allclose(derivative, 8.0)


def test_physical_duration_advance_and_irregular_observation_schedule():
    """Duration rollouts support increasing, irregular observation times."""
    model, state = _model_and_state()
    parameters = {"correction": jnp.asarray(0.0)}

    intermediate = advance_duration(
        model,
        parameters,
        state,
        duration_seconds=3600.0,
    )
    final_state, observations = rollout_at_durations(
        model,
        parameters,
        state,
        durations_seconds=(1800.0, 3600.0, 7200.0),
    )

    np.testing.assert_allclose(intermediate.core, 5.0)
    np.testing.assert_allclose(final_state.core, 9.0)
    np.testing.assert_allclose(
        observations.values[:, 0, 0, 0],
        jnp.asarray([3.0, 5.0, 9.0]),
    )


def test_stopped_gradient_rollout_preserves_forecast_and_bounds_bptt():
    """Detaching recurrent state changes credit assignment, not the forecast."""
    model, state = _model_and_state()

    def terminal_value(correction, maximum_gradient_duration_seconds):
        _, observations, _ = rollout_at_durations_with_tendency_statistics(
            model,
            {"correction": correction},
            state,
            durations_seconds=(7200.0,),
            rematerialize=False,
            collect_tendency_statistics=False,
            maximum_gradient_duration_seconds=maximum_gradient_duration_seconds,
        )
        return observations.values[-1, 0, 0, 0]

    correction = jnp.asarray(0.0)
    full_bptt_value, full_bptt_gradient = jax.value_and_grad(
        lambda value: terminal_value(value, None)
    )(correction)
    stopped_value, stopped_gradient = jax.value_and_grad(
        lambda value: terminal_value(value, 1800.0)
    )(correction)

    np.testing.assert_allclose(full_bptt_value, 9.0)
    np.testing.assert_allclose(stopped_value, full_bptt_value)
    np.testing.assert_allclose(full_bptt_gradient, 8.0)
    np.testing.assert_allclose(stopped_gradient, 2.0)


def test_uniform_truncated_suffix_preserves_requested_leads_and_gradients():
    """A reusable truncated window scan preserves log-spaced lead semantics."""
    model, state = _model_and_state()
    durations_seconds = (1800.0, 3600.0, 7200.0, 14_400.0)

    def forecast_sum(correction):
        final_state, observations, statistics = (
            rollout_at_durations_with_tendency_statistics(
                model,
                {"correction": correction},
                state,
                durations_seconds=durations_seconds,
                rematerialize=False,
                collect_tendency_statistics=True,
                maximum_gradient_duration_seconds=3600.0,
            )
        )
        return (
            jnp.sum(observations.values),
            (final_state, observations, statistics),
        )

    (forecast_total, auxiliary), gradient = jax.value_and_grad(
        forecast_sum,
        has_aux=True,
    )(jnp.asarray(0.0))
    final_state, observations, statistics = auxiliary

    np.testing.assert_allclose(final_state.core, 17.0)
    np.testing.assert_allclose(
        observations.values[:, 0, 0, 0],
        jnp.asarray([3.0, 5.0, 9.0, 17.0]),
    )
    np.testing.assert_allclose(forecast_total, 34.0)
    # Each lead receives credit through at most its local two-step window.
    np.testing.assert_allclose(gradient, 14.0)
    np.testing.assert_allclose(statistics["correction/rms"], 0.0)
    np.testing.assert_allclose(statistics["correction/max_abs"], 0.0)


def test_unaligned_truncated_lead_uses_general_segmented_path():
    """Irregular requested leads retain the general stop-gradient behavior."""
    model, state = _model_and_state()

    def forecast_sum(correction):
        _, observations, _ = rollout_at_durations_with_tendency_statistics(
            model,
            {"correction": correction},
            state,
            durations_seconds=(3600.0, 5400.0, 7200.0),
            rematerialize=False,
            collect_tendency_statistics=False,
            maximum_gradient_duration_seconds=3600.0,
        )
        return jnp.sum(observations.values)

    forecast_total, gradient = jax.value_and_grad(forecast_sum)(jnp.asarray(0.0))

    np.testing.assert_allclose(forecast_total, 21.0)
    np.testing.assert_allclose(gradient, 10.0)


def test_stopped_gradient_window_must_end_on_correction_boundary():
    """A detach event cannot split one public neural-correction step."""
    model, state = _model_and_state()

    with pytest.raises(ValueError, match="neural-correction boundary"):
        rollout_at_durations_with_tendency_statistics(
            model,
            {"correction": jnp.asarray(0.0)},
            state,
            durations_seconds=(7200.0,),
            maximum_gradient_duration_seconds=2700.0,
        )


def test_physical_duration_rejects_partial_correction_interval():
    """Physical durations must contain a whole number of public steps."""
    model, state = _model_and_state()

    with pytest.raises(ValueError, match="integer multiple"):
        advance_duration(
            model,
            {"correction": jnp.asarray(0.0)},
            state,
            duration_seconds=2700.0,
        )


@pytest.mark.parametrize(
    ("steps", "save_every", "error_type", "message"),
    [
        (0, 1, ValueError, "at least one"),
        (1.5, 1, TypeError, "integer"),
        (3, 2, ValueError, "divisible"),
    ],
)
def test_rollout_rejects_invalid_static_lengths(
    steps,
    save_every,
    error_type,
    message,
):
    """Static scan lengths must be positive integers with exact grouping."""
    model, state = _model_and_state()

    with pytest.raises(error_type, match=message):
        rollout(
            model,
            {"correction": jnp.asarray(0.0)},
            state,
            steps=steps,
            save_every=save_every,
            observe=model.decode,
        )
