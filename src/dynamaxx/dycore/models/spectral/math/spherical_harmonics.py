# Copyright 2026 dynamaxx
# Adapted from: https://github.com/neuralgcm/dinosaur/blob/main/dinosaur/spherical_harmonic.py

from dataclasses import dataclass, field
from functools import cached_property, partial

import jax
import jax.numpy as jnp
import numpy as np

from . import associated_legendre, fourier

einsum = partial(jnp.einsum, precision=jax.lax.Precision.HIGHEST)


LATITUDE_SPACINGS = {
    "gauss": associated_legendre.gauss_legendre_nodes,
    "equiangular": associated_legendre.equiangular_nodes,
    "equiangular_with_poles": associated_legendre.equiangular_nodes_with_poles,
}


def get_latitude_nodes(n: int, spacing: str = "gauss") -> tuple[np.ndarray, np.ndarray]:
    """Return sin(latitude) nodes and quadrature weights."""
    assert spacing in LATITUDE_SPACINGS, f"unknown latitude spacing {spacing}"
    return LATITUDE_SPACINGS[spacing](n)


@dataclass(frozen=True)
class SphericalHarmonicBasis:
    """Basis matrices and quadrature weights for real spherical harmonics.

    The Fourier basis has shape (longitude_nodes, modal_m). The Legendre
    basis has shape (modal_m, latitude_nodes, total_wavenumbers). The weights
    have shape (longitude_nodes, latitude_nodes).
    """

    fourier: np.ndarray
    legendre: np.ndarray
    weights: np.ndarray


@dataclass(frozen=True)
class RealSphericalHarmonics:
    """Readable real spherical harmonic transform with triangular truncation."""

    total_wavenumbers: int
    longitude_nodes: int
    latitude_nodes: int
    latitude_spacing: str = "gauss"
    basis: SphericalHarmonicBasis = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self):
        assert self.total_wavenumbers >= 1
        assert 2 * self.total_wavenumbers - 1 <= self.longitude_nodes
        assert self.total_wavenumbers <= self.latitude_nodes

        fourier_basis = fourier.real_basis(
            wavenumbers=self.total_wavenumbers,
            nodes=self.longitude_nodes,
        )
        longitude_weights = fourier.quadrature_nodes(self.longitude_nodes)[1]

        sin_latitude, latitude_weights = get_latitude_nodes(
            self.latitude_nodes,
            self.latitude_spacing,
        )
        legendre_basis = np.asarray(
            associated_legendre.evaluate(
                n_m=self.total_wavenumbers,
                n_l=self.total_wavenumbers,
                x=sin_latitude,
            )
        )

        legendre_basis = np.repeat(legendre_basis, 2, axis=0)[1:]
        weights = longitude_weights[:, np.newaxis] * latitude_weights[np.newaxis, :]
        object.__setattr__(
            self,
            "basis",
            SphericalHarmonicBasis(
                fourier=fourier_basis,
                legendre=legendre_basis,
                weights=weights,
            ),
        )

    @cached_property
    def nodal_axes(self) -> tuple[np.ndarray, np.ndarray]:
        """Longitude and sin(latitude) coordinates for nodal fields."""
        longitude, _ = fourier.quadrature_nodes(self.longitude_nodes)
        sin_latitude, _ = get_latitude_nodes(self.latitude_nodes, self.latitude_spacing)
        return longitude, sin_latitude

    @cached_property
    def nodal_shape(self) -> tuple[int, int]:
        """Shape of a scalar field in nodal space."""
        return self.longitude_nodes, self.latitude_nodes

    @cached_property
    def modal_axes(self) -> tuple[np.ndarray, np.ndarray]:
        """Longitude wavenumber labels and total wavenumber labels."""
        positive_m = np.arange(1, self.total_wavenumbers)
        signed_m = np.stack([positive_m, -positive_m], axis=1).ravel()
        longitude_orders = np.concatenate([[0], signed_m])
        total_wavenumbers = np.arange(self.total_wavenumbers)
        return longitude_orders, total_wavenumbers

    @cached_property
    def modal_shape(self) -> tuple[int, int]:
        """Shape of a scalar field in modal space."""
        return 2 * self.total_wavenumbers - 1, self.total_wavenumbers

    @cached_property
    def mask(self) -> np.ndarray:
        """Boolean mask for structurally valid modal coefficients."""
        m, l = np.meshgrid(*self.modal_axes, indexing="ij")
        return np.abs(m) <= l

    def modal_to_nodal(self, modal_values: jax.Array) -> jax.Array:
        """Map modal coefficients to nodal values.

        The expected input shape is (*batch, modal_m, total_wavenumbers), where
        modal_m = 2 * total_wavenumbers - 1. The returned array has shape
        (*batch, longitude_nodes, latitude_nodes). This sums over modal
        wavenumber axes m and l.
        """
        degree_summed_values = einsum(
            "mjl,...ml->...mj",
            self.basis.legendre,
            modal_values,
        )
        nodal_values = einsum(
            "im,...mj->...ij",
            self.basis.fourier,
            degree_summed_values,
        )
        return nodal_values

    def nodal_to_modal(self, nodal_values: jax.Array) -> jax.Array:
        """Map nodal values to modal coefficients.

        The expected input shape is (*batch, longitude_nodes, latitude_nodes).
        The returned array has shape (*batch, modal_m, total_wavenumbers),
        where modal_m = 2 * total_wavenumbers - 1. This sums over nodal
        longitude and latitude axes.
        """
        weighted_nodal_values = self.basis.weights * nodal_values
        longitude_summed_values = einsum(
            "im,...ij->...mj",
            self.basis.fourier,
            weighted_nodal_values,
        )
        modal_values = einsum(
            "mjl,...mj->...ml",
            self.basis.legendre,
            longitude_summed_values,
        )
        return modal_values

    def longitudinal_derivative(self, modal_values: jax.Array) -> jax.Array:
        """Differentiate modal coefficients with respect to longitude.

        The expected input shape is (*batch, modal_m, total_wavenumbers). The
        returned array has the same shape.
        """
        return fourier.real_basis_derivative(modal_values, axis=-2)
