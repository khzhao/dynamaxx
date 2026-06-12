# Copyright 2026 dynamaxx

from dataclasses import dataclass, field

import jax
import jax.numpy as jnp

from dynamaxx.dycore.ode import integrate

from .grid import SphericalGrid
from .operators import SpectralOperators


@dataclass(frozen=True)
class SpectralDycore:
    """Minimal modal-space dycore for spherical ODE rollouts.

    The state shape is (*batch, modal_m, total_wavenumbers). The tendency is a
    linear combination of zonal advection and diffusion in spectral space.
    """

    grid: SphericalGrid
    diffusivity: float = 0.0
    diffusion_order: int = 1
    zonal_angular_velocity: float = 0.0
    operators: SpectralOperators = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        assert self.diffusion_order >= 1
        object.__setattr__(self, "operators", SpectralOperators(self.grid))

    def tendency(
        self,
        modal_state: jax.Array,
        time: jax.Array | float = 0.0,
    ) -> jax.Array:
        """Return d(state)/dt for modal coefficients.

        Args:
            modal_state: State with shape (*batch, modal_m, total_wavenumbers).
            time: Simulation time in seconds. Included for ODE solver
                compatibility; the current dynamics are time independent.
        """
        del time
        modal_state = self.operators.apply_modal_mask(modal_state)
        modal_tendency = jnp.zeros_like(modal_state)

        if self.zonal_angular_velocity:
            modal_tendency -= self.zonal_angular_velocity * (
                self.operators.longitudinal_derivative(modal_state)
            )
        if self.diffusivity:
            modal_tendency += self.diffusivity * self.diffusion(modal_state)

        return self.operators.apply_modal_mask(modal_tendency)

    def diffusion(self, modal_state: jax.Array) -> jax.Array:
        """Return the stable diffusion operator applied to modal coefficients."""
        diffused_state = self.operators.apply_modal_mask(modal_state)
        for _ in range(self.diffusion_order):
            diffused_state = self.operators.laplacian(diffused_state)

        if self.diffusion_order % 2 == 0:
            diffused_state = -diffused_state
        return diffused_state

    def step(
        self,
        modal_state: jax.Array,
        *,
        step_seconds: jax.Array | float,
        time: jax.Array | float = 0.0,
        method: str = "rk4",
    ) -> jax.Array:
        """Advance modal coefficients by one ODE step."""
        trajectory = integrate(
            self.tendency,
            modal_state,
            steps=1,
            step_seconds=step_seconds,
            start_time=time,
            method=method,
            include_initial=False,
        )
        return trajectory[0]

    def simulate(
        self,
        initial_modal_state: jax.Array,
        *,
        steps: int,
        step_seconds: jax.Array | float,
        start_time: jax.Array | float = 0.0,
        method: str = "rk4",
        include_initial: bool = True,
    ) -> jax.Array:
        """Roll out modal coefficients with a leading trajectory axis."""
        return integrate(
            self.tendency,
            self.operators.apply_modal_mask(initial_modal_state),
            steps=steps,
            step_seconds=step_seconds,
            start_time=start_time,
            method=method,
            include_initial=include_initial,
        )

    def simulate_nodal(
        self,
        initial_nodal_state: jax.Array,
        *,
        steps: int,
        step_seconds: jax.Array | float,
        start_time: jax.Array | float = 0.0,
        method: str = "rk4",
        include_initial: bool = True,
    ) -> jax.Array:
        """Project nodal values to modal space, simulate, and return nodal values."""
        initial_modal_state = self.grid.nodal_to_modal(initial_nodal_state)
        modal_trajectory = self.simulate(
            initial_modal_state,
            steps=steps,
            step_seconds=step_seconds,
            start_time=start_time,
            method=method,
            include_initial=include_initial,
        )
        return self.grid.modal_to_nodal(modal_trajectory)
