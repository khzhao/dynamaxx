# Copyright 2026 dynamaxx

"""Shared fixtures for the nncorr tutorial tests.

Everything runs on a tiny synthetic T21 grid (64 x 33 nodes, 4 sigma
layers) so the whole suite is CPU-friendly and needs no data on disk.
"""

import os

# Pin JAX to CPU BEFORE jax is imported anywhere: the optimization loop
# owns this machine's GPUs, and unit tests must never touch them.
os.environ.setdefault("JAX_PLATFORMS", "cpu")

import dataclasses  # noqa: E402

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

from dynamaxx.dycore.models.dinosaur import primitive_equations, units  # noqa: E402
from dynamaxx.dycore.models.dinosaur.adapter import (  # noqa: E402
    _reference_temperature,
    _unit_factor,
)
from dynamaxx.dycore.models.dinosaur.coordinates import grid_metadata  # noqa: E402
from dynamaxx.nncorr.data import GridBundle  # noqa: E402


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "exercise: acceptance tests that fail until the reader implements "
        "the corresponding tutorial exercise",
    )


TINY_LAYER_COUNT = 4
TINY_PRESSURE_LEVELS = (300, 500, 700, 900)


@pytest.fixture(scope="session")
def tiny_bundle() -> GridBundle:
    longitude = np.arange(64) * (360.0 / 64.0)
    latitude = np.linspace(-90.0, 90.0, 33)
    grid = grid_metadata(
        longitude=longitude,
        latitude=latitude,
        layer_count=TINY_LAYER_COUNT,
        spectral_wavenumbers=21,
    )
    return GridBundle(
        coords=grid.coords,
        latitude_reversed=grid.latitude_reversed,
        longitude=longitude,
        latitude=latitude,
        pressure_levels_hpa=TINY_PRESSURE_LEVELS,
        reference_temperature=_reference_temperature(
            layer_count=TINY_LAYER_COUNT,
            temperature_kelvin=250.0,
        ),
        physics_specs=units.SimUnits.from_si(),
        state_channels=(),
    )


@dataclasses.dataclass(frozen=True)
class _TinyShapes:
    nodal: tuple[int, int]
    modal: tuple[int, ...]


@pytest.fixture(scope="session")
def tiny_shapes(tiny_bundle) -> _TinyShapes:
    grid = tiny_bundle.coords.horizontal
    return _TinyShapes(nodal=grid.nodal_shape, modal=grid.modal_shape)


def make_rest_state(
    bundle: GridBundle,
    key: jax.Array,
    noise_kelvin: float = 0.1,
    noise_wind: float = 0.5,
) -> primitive_equations.State:
    """A near-rest, isothermal, hydrostatically trivial state plus noise.

    Built in NODAL space and transformed, so the spectral content is valid
    by construction (random modal coefficients are NOT a valid state — the
    transform pair enforces the truncation and symmetries).
    """
    grid = bundle.coords.horizontal
    layer_count = len(bundle.reference_temperature)
    key_t, key_u, key_v, key_p = jax.random.split(key, 4)
    nodal_shape = (layer_count, *grid.nodal_shape)

    kelvin = _unit_factor(bundle.physics_specs, "kelvin")
    mps = _unit_factor(bundle.physics_specs, "meter / second")
    pascal = _unit_factor(bundle.physics_specs, "pascal")

    from dynamaxx.dycore.models.dinosaur import spherical_harmonic

    temperature_variation = grid.to_modal(
        jax.random.normal(key_t, nodal_shape) * (noise_kelvin * kelvin)
    )
    u_nodal = jax.random.normal(key_u, nodal_shape) * (noise_wind * mps)
    v_nodal = jax.random.normal(key_v, nodal_shape) * (noise_wind * mps)
    vorticity, divergence = spherical_harmonic.uv_nodal_to_vor_div_modal(
        grid, u_nodal, v_nodal
    )
    log_surface_pressure = grid.to_modal(
        jnp.full((1, *grid.nodal_shape), jnp.log(1.0e5 * pascal))
        + jax.random.normal(key_p, (1, *grid.nodal_shape)) * 1.0e-4
    )
    return primitive_equations.State(
        vorticity=vorticity,
        divergence=divergence,
        temperature_variation=temperature_variation,
        log_surface_pressure=log_surface_pressure,
        tracers={},
        sim_time=None,
    )


@pytest.fixture
def tiny_state(tiny_bundle) -> primitive_equations.State:
    return make_rest_state(tiny_bundle, jax.random.PRNGKey(0))
