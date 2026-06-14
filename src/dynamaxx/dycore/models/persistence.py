# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

from dynamaxx.dycore.ode import TimeValue, integrate
from dynamaxx.weather import WeatherState


def tendency(state: jax.Array, time: TimeValue) -> jax.Array:
    """Return the persistence dX/dt.

    This is the intended minimal dynamics surface for agent experiments. The
    default zero tendency makes the model a persistence forecast.
    """
    del time
    return jnp.zeros_like(state)


@dataclass(frozen=True)
class PersistenceDycoreModel:
    """Simple physical-state dycore model using the shared ODE integrator."""

    name: str = "persistence"
    method: str = "euler"
    jit_forecast: bool = True

    @cached_property
    def simulate(self):
        """Return the reusable rollout callable."""
        if not self.jit_forecast:
            return self._simulate
        return jax.jit(
            self._simulate,
            static_argnames=("steps", "method", "include_initial"),
        )

    def _simulate(
        self,
        initial_state: jax.Array,
        *,
        steps: int,
        step_seconds: TimeValue,
        method: str,
        include_initial: bool,
    ) -> jax.Array:
        return integrate(
            tendency,
            initial_state,
            steps=steps,
            step_seconds=step_seconds,
            method=method,
            include_initial=include_initial,
        )

    def forecast(
        self,
        initial_state: WeatherState,
        lead_steps: Sequence[int],
        step_seconds: float,
    ) -> WeatherState:
        """Return a persistence forecast for the provided weather state."""
        lead_steps = tuple(int(lead_step) for lead_step in lead_steps)
        assert lead_steps
        assert all(lead_step >= 0 for lead_step in lead_steps)

        trajectory = self.simulate(
            jnp.asarray(initial_state.values),
            steps=max(lead_steps),
            step_seconds=step_seconds,
            method=self.method,
            include_initial=True,
        )
        forecast_values = jnp.take(
            trajectory,
            jnp.asarray(lead_steps, dtype=jnp.int32),
            axis=0,
        )
        return initial_state.with_values(forecast_values)


def default_persistence_dycore_model() -> PersistenceDycoreModel:
    """Return the default persistence dycore model."""
    return PersistenceDycoreModel()
