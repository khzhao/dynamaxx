# Copyright 2026 dynamaxx

from dataclasses import dataclass
from functools import cached_property

import jax
import jax.numpy as jnp
import numpy as np

from .grid import SphericalGrid


@dataclass(frozen=True)
class SpectralOperators:
    """Differential operators for scalar fields in spherical harmonic space."""

    grid: SphericalGrid

    @cached_property
    def laplacian_eigenvalues(self) -> np.ndarray:
        """Eigenvalues of the spherical Laplacian for each modal coefficient."""
        _, total_wavenumbers = self.grid.modal_axes
        eigenvalues_by_degree = (
            -total_wavenumbers * (total_wavenumbers + 1) / self.grid.radius**2
        )
        eigenvalues = np.broadcast_to(
            eigenvalues_by_degree[np.newaxis, :],
            self.grid.modal_shape,
        )
        return np.where(self.grid.modal_mask, eigenvalues, 0.0)

    def apply_modal_mask(self, modal_values: jax.Array) -> jax.Array:
        """Zero structurally invalid modal coefficients."""
        modal_values = jnp.asarray(modal_values)
        modal_mask = jnp.asarray(self.grid.modal_mask)
        return jnp.where(modal_mask, modal_values, jnp.zeros_like(modal_values))

    def laplacian(self, modal_values: jax.Array) -> jax.Array:
        """Apply the spherical Laplacian to modal coefficients."""
        modal_values = jnp.asarray(modal_values)
        eigenvalues = jnp.asarray(
            self.laplacian_eigenvalues,
            dtype=modal_values.dtype,
        )
        return self.apply_modal_mask(eigenvalues * modal_values)

    def inverse_laplacian(self, modal_values: jax.Array) -> jax.Array:
        """Invert the spherical Laplacian, with the constant mode set to zero."""
        modal_values = self.apply_modal_mask(modal_values)
        eigenvalues = jnp.asarray(
            self.laplacian_eigenvalues,
            dtype=modal_values.dtype,
        )
        zero_eigenvalue = eigenvalues == 0
        safe_eigenvalues = jnp.where(
            zero_eigenvalue,
            jnp.ones_like(eigenvalues),
            eigenvalues,
        )
        inverse_values = modal_values / safe_eigenvalues
        return jnp.where(
            zero_eigenvalue, jnp.zeros_like(inverse_values), inverse_values
        )

    def longitudinal_derivative(self, modal_values: jax.Array) -> jax.Array:
        """Differentiate modal coefficients with respect to longitude."""
        derivative = self.grid.spherical_harmonics.longitudinal_derivative(
            modal_values,
        )
        return self.apply_modal_mask(derivative)
