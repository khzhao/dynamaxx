# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp

from dynamaxx.dycore.grid import SphericalGrid
from dynamaxx.dycore.simulation import SpectralDycore
from dynamaxx.utils.consts import EARTH_ANGULAR_VELOCITY


@dataclass(frozen=True)
class SpectralDycoreForecastModel:
    """Forecast named nodal weather states with a modal-space SpectralDycore."""

    dycore: SpectralDycore
    name: str = "spectral_dycore"
    method: str = "rk4"
    jit_forecast: bool = True

    @cached_property
    def simulate_forecast(self):
        """Return the reusable simulation callable for forecast rollouts."""
        if not self.jit_forecast:
            return self.dycore.simulate
        return jax.jit(
            self.dycore.simulate,
            static_argnames=("steps", "method", "include_initial"),
        )

    def forecast(
        self,
        initial_state: jax.Array,
        lead_steps: Sequence[int],
        step_seconds: float,
    ) -> jax.Array:
        """Return weather states at requested lead steps.

        Args:
            initial_state: Current weather state with shape
                (init, variable, longitude, latitude).
            lead_steps: Positive or zero integer lead steps to return.
            step_seconds: Time step in seconds for one dycore transition.

        Returns:
            Forecast values with shape
            (lead, init, variable, longitude, latitude).
        """
        grid = self.dycore.grid
        lead_steps = tuple(int(lead_step) for lead_step in lead_steps)
        assert lead_steps
        assert all(lead_step >= 0 for lead_step in lead_steps)
        initial_state = jnp.asarray(initial_state)
        assert initial_state.shape[-2:] == grid.nodal_shape

        initial_modal_state = grid.nodal_to_modal(initial_state)
        modal_trajectory = self.simulate_forecast(
            initial_modal_state,
            steps=max(lead_steps),
            step_seconds=step_seconds,
            method=self.method,
            include_initial=True,
        )
        modal_trajectory = jnp.take(
            modal_trajectory,
            jnp.asarray(lead_steps, dtype=jnp.int32),
            axis=0,
        )
        return grid.modal_to_nodal(modal_trajectory)


def default_spectral_dycore_forecast_model() -> SpectralDycoreForecastModel:
    """Return the default spectral dycore forecast model for WeatherBench2 evals."""
    grid = SphericalGrid(
        total_wavenumbers=32,
        longitude_nodes=240,
        latitude_nodes=121,
        latitude_spacing="equiangular_with_poles",
    )
    return SpectralDycoreForecastModel(
        dycore=SpectralDycore(
            grid=grid,
            zonal_angular_velocity=EARTH_ANGULAR_VELOCITY,
        ),
        name="spectral_dycore",
        method="rk4",
        jit_forecast=True,
    )
