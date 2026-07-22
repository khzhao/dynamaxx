from dataclasses import dataclass

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from dynamaxx.hybrid.model import PreparedHybridModel
from dynamaxx.hybrid.rollout import advance, rollout
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
    model, state = _model_and_state()

    final_state = advance(
        model,
        {"correction": jnp.asarray(0.0)},
        state,
        steps=3,
    )

    np.testing.assert_allclose(final_state.core, 7.0)


def test_rollout_observes_only_requested_coupling_boundaries():
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
