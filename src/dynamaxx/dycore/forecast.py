# Copyright 2026 dynamaxx

from dataclasses import dataclass

import jax
import jax.numpy as jnp

from dynamaxx.dycore.grid import SphericalGrid
from dynamaxx.dycore.simulation import SpectralDycore
from dynamaxx.eval.core import ForecastInput, WeatherState
from dynamaxx.utils.consts import EARTH_ANGULAR_VELOCITY


@dataclass(frozen=True)
class SpectralDycoreForecastModel:
    """ForecastModel adapter for the modal-space SpectralDycore."""

    dycore: SpectralDycore
    name: str = "spectral_dycore"
    method: str = "rk4"
    jit_forecast: bool = True

    def forecast(self, forecast_input: ForecastInput) -> WeatherState:
        """Run the spectral dycore and return lead times in nodal space."""
        grid = self.dycore.grid
        assert forecast_input.initial_state.spatial_shape == grid.nodal_shape

        initial_modal_state = grid.nodal_to_modal(forecast_input.initial_state.values)
        simulate = self.dycore.simulate
        if self.jit_forecast:
            simulate = jax.jit(
                simulate,
                static_argnames=("steps", "method", "include_initial"),
            )
        modal_trajectory = simulate(
            initial_modal_state,
            steps=max(forecast_input.lead_steps),
            step_seconds=forecast_input.step_seconds,
            method=self.method,
            include_initial=True,
        )
        modal_trajectory = jnp.take(
            modal_trajectory,
            jnp.asarray(forecast_input.lead_steps, dtype=jnp.int32),
            axis=0,
        )
        return WeatherState(
            values=grid.modal_to_nodal(modal_trajectory),
            variables=forecast_input.initial_state.variables,
        )


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
