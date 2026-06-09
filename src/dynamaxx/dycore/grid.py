# Copyright 2026 dynamaxx

from dataclasses import dataclass, field
from functools import cached_property

import jax
import numpy as np

from dynamaxx.utils.math.spherical_harmonics import RealSphericalHarmonics


@dataclass(frozen=True)
class SphericalGrid:
    """Spectral and nodal grid metadata for a spherical dycore."""

    total_wavenumbers: int
    longitude_nodes: int
    latitude_nodes: int
    latitude_spacing: str = "gauss"
    radius: float = 1.0
    spherical_harmonics: RealSphericalHarmonics = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self):
        assert self.radius > 0

        spherical_harmonics = RealSphericalHarmonics(
            total_wavenumbers=self.total_wavenumbers,
            longitude_nodes=self.longitude_nodes,
            latitude_nodes=self.latitude_nodes,
            latitude_spacing=self.latitude_spacing,
        )
        object.__setattr__(self, "spherical_harmonics", spherical_harmonics)

    @cached_property
    def longitude(self) -> np.ndarray:
        """Longitude nodes in radians."""
        longitude, _ = self.spherical_harmonics.nodal_axes
        return longitude

    @cached_property
    def sin_latitude(self) -> np.ndarray:
        """Sine of latitude at each latitude node."""
        _, sin_latitude = self.spherical_harmonics.nodal_axes
        return sin_latitude

    @cached_property
    def latitude(self) -> np.ndarray:
        """Latitude nodes in radians."""
        return np.arcsin(self.sin_latitude)

    @cached_property
    def nodal_shape(self) -> tuple[int, int]:
        """Shape of scalar nodal fields."""
        return self.spherical_harmonics.nodal_shape

    @cached_property
    def modal_shape(self) -> tuple[int, int]:
        """Shape of scalar modal fields."""
        return self.spherical_harmonics.modal_shape

    @cached_property
    def modal_axes(self) -> tuple[np.ndarray, np.ndarray]:
        """Longitude and total wavenumber labels for modal fields."""
        return self.spherical_harmonics.modal_axes

    @cached_property
    def modal_mask(self) -> np.ndarray:
        """Boolean mask for structurally valid modal coefficients."""
        return self.spherical_harmonics.mask

    @cached_property
    def quadrature_weights(self) -> np.ndarray:
        """Unit-sphere quadrature weights with nodal field shape."""
        return self.spherical_harmonics.basis.weights

    @cached_property
    def area_weights(self) -> np.ndarray:
        """Physical area weights with nodal field shape."""
        return self.radius**2 * self.quadrature_weights

    def modal_to_nodal(self, modal_values: jax.Array) -> jax.Array:
        """Map modal coefficients to nodal values."""
        return self.spherical_harmonics.modal_to_nodal(modal_values)

    def nodal_to_modal(self, nodal_values: jax.Array) -> jax.Array:
        """Map nodal values to modal coefficients."""
        return self.spherical_harmonics.nodal_to_modal(nodal_values)
