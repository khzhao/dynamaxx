# Copyright 2026 dynamaxx

from __future__ import annotations

from dataclasses import dataclass

import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.dinosaur import (
    coordinate_systems,
    sigma_coordinates,
    spherical_harmonic,
    units,
)


@dataclass(frozen=True)
class GridMetadata:
    """Dinosaur coordinate system plus latitude-axis adapter metadata."""

    coords: coordinate_systems.CoordinateSystem
    latitude_reversed: bool


def grid_metadata(
    *,
    longitude: np.ndarray,
    latitude: np.ndarray,
    layer_count: int,
    spectral_wavenumbers: int | None,
) -> GridMetadata:
    """Build Dinosaur coordinates compatible with the WeatherState grid."""
    physics_specs = units.SimUnits.from_si()
    longitude = np.asarray(longitude, dtype=np.float64)
    latitude = np.asarray(latitude, dtype=np.float64)
    max_longitude_wavenumbers = max(1, min((longitude.size + 1) // 2, latitude.size))
    max_total_wavenumbers = max(max_longitude_wavenumbers, latitude.size)
    if spectral_wavenumbers is None:
        longitude_wavenumbers = max_longitude_wavenumbers
        total_wavenumbers = max_total_wavenumbers
    else:
        assert spectral_wavenumbers >= 1
        longitude_wavenumbers = min(spectral_wavenumbers, max_longitude_wavenumbers)
        total_wavenumbers = min(
            max(longitude_wavenumbers, spectral_wavenumbers),
            max_total_wavenumbers,
        )
    for latitude_spacing in (
        "equiangular_with_poles",
        "equiangular",
        "gauss",
    ):
        horizontal_grid = spherical_harmonic.Grid(
            longitude_wavenumbers=longitude_wavenumbers,
            total_wavenumbers=total_wavenumbers,
            longitude_nodes=longitude.size,
            latitude_nodes=latitude.size,
            latitude_spacing=latitude_spacing,
            longitude_offset=np.deg2rad(float(longitude[0])),
            radius=physics_specs.radius,
        )
        if not np.allclose(
            np.rad2deg(horizontal_grid.longitudes), longitude, atol=1e-5
        ):
            continue
        grid_latitude = np.rad2deg(horizontal_grid.latitudes)
        if np.allclose(grid_latitude, latitude, atol=1e-5):
            return GridMetadata(
                coords=_coordinate_system(horizontal_grid, layer_count),
                latitude_reversed=False,
            )
        if np.allclose(grid_latitude, latitude[::-1], atol=1e-5):
            return GridMetadata(
                coords=_coordinate_system(horizontal_grid, layer_count),
                latitude_reversed=True,
            )
    raise AssertionError("Dinosaur requires a supported latitude-longitude grid")


def _coordinate_system(
    horizontal_grid: spherical_harmonic.Grid,
    layer_count: int,
) -> coordinate_systems.CoordinateSystem:
    coords = coordinate_systems.CoordinateSystem(
        horizontal_grid,
        sigma_coordinates.SigmaCoordinates.equidistant(layer_count),
    )
    object.__setattr__(coords, "horizontal", _with_safe_polar_cosine(coords.horizontal))
    return coords


def _with_safe_polar_cosine(
    horizontal_grid: spherical_harmonic.Grid,
) -> spherical_harmonic.Grid:
    """Return a grid whose pole cosine factors stay finite."""
    cos_latitude = jnp.asarray(horizontal_grid.cos_lat)
    smallest_interior_cosine = jnp.min(
        jnp.where(cos_latitude > 0.0, cos_latitude, jnp.inf)
    )
    safe_cos_latitude = jnp.maximum(cos_latitude, smallest_interior_cosine)
    object.__setattr__(horizontal_grid, "cos_lat", safe_cos_latitude)
    object.__setattr__(horizontal_grid, "sec2_lat", 1.0 / safe_cos_latitude**2)
    return horizontal_grid
