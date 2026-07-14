# Copyright 2026 dynamaxx

"""Data plumbing: grid construction, ERA5 windows, and state encoding.

THE SPLIT LAW (non-negotiable, see tutorial/04): the fixed evaluation
protocols initialize from 2014-2018 (iteration), 2019 (validation), and
2020 (golden). Training may touch 1959-2013 ONLY. `sample_training_window`
enforces this with an assertion rather than a comment.
"""

from __future__ import annotations

import dataclasses

import jax
import numpy as np

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.dycore.models.dinosaur import adapter, units
from dynamaxx.dycore.models.dinosaur.channels import infer_dinosaur_pressure_levels
from dynamaxx.dycore.models.dinosaur.coordinates import grid_metadata
from dynamaxx.weather import WeatherState

LAST_TRAINING_YEAR = 2013
DEFAULT_STEP_HOURS = 6


@dataclasses.dataclass(frozen=True)
class GridBundle:
    """Static geometry and metadata shared by encoding, rollout, features."""

    coords: object
    latitude_reversed: bool
    longitude: np.ndarray
    latitude: np.ndarray
    pressure_levels_hpa: tuple[int, ...]
    reference_temperature: np.ndarray
    physics_specs: object
    state_channels: tuple[str, ...]

    @property
    def layer_count(self) -> int:
        return len(self.pressure_levels_hpa)


def build_grid_bundle(
    source: WeatherBench2Source | None = None,
    *,
    spectral_wavenumbers: int = 80,
    reference_temperature_kelvin: float = 250.0,
    metadata_year: int = 2000,
) -> GridBundle:
    """Build the production T80/L13 bundle from the dataset's own metadata."""
    source = source or WeatherBench2Source()
    longitude, latitude = source.spatial_coordinates(year=metadata_year)
    channels = source.state_channel_names(year=metadata_year)
    pressure_levels = infer_dinosaur_pressure_levels(channels)
    grid = grid_metadata(
        longitude=longitude,
        latitude=latitude,
        layer_count=len(pressure_levels),
        spectral_wavenumbers=spectral_wavenumbers,
    )
    return GridBundle(
        coords=grid.coords,
        latitude_reversed=grid.latitude_reversed,
        longitude=np.asarray(longitude),
        latitude=np.asarray(latitude),
        pressure_levels_hpa=pressure_levels,
        reference_temperature=adapter._reference_temperature(
            layer_count=len(pressure_levels),
            temperature_kelvin=reference_temperature_kelvin,
        ),
        physics_specs=units.SimUnits.from_si(),
        state_channels=channels,
    )


def encode_analysis(
    bundle: GridBundle,
    packed_values: jax.Array,
    *,
    initialize_sim_time: bool = True,
):
    """Encode one packed analysis `[channel, lon, lat]` into a dinosaur State.

    Uses the SAME deterministic encode the incumbent lineage uses
    (log-pressure vertical interpolation + layer-mean hydrostatic
    temperature), so "corrector off" reproduces the plain dycore family
    exactly. Humidity is NOT passed into the model here: the free core is
    dry, and a tracer placed in `State.tracers` would be advected — see the
    no-advection warnings all over the optimization loop's history.
    """
    state = WeatherState(values=packed_values, variables=bundle.state_channels)
    return adapter.weather_state_to_dinosaur_state(
        state,
        coords=bundle.coords,
        pressure_levels_hpa=bundle.pressure_levels_hpa,
        latitude_reversed=bundle.latitude_reversed,
        physics_specs=bundle.physics_specs,
        reference_temperature=bundle.reference_temperature,
        include_humidity=False,
        use_log_pressure_initialization=True,
        use_hydrostatic_temperature_initialization=True,
        use_layer_mean_hydrostatic_temperature_initialization=True,
        initialize_sim_time=initialize_sim_time,
    )


def sample_training_window(
    source: WeatherBench2Source,
    rng: np.random.Generator,
    *,
    first_year: int = 1980,
    last_year: int = LAST_TRAINING_YEAR,
    target_count: int = 4,
    step_hours: int = DEFAULT_STEP_HOURS,
) -> tuple[np.ndarray, jax.Array]:
    """Sample one (t0, targets...) window of packed states from ERA5.

    Returns `(times[K + 1], values[K + 1, channel, lon, lat])` where
    times[0] is the initialization analysis and times[1:] are targets at
    `step_hours` spacing. Draws init times at 00Z on uniformly sampled days.

    The default `first_year=1980` skips the sparse pre-satellite era; widen
    it once the pipeline works and measure whether it helps — that is a real
    research question, not a settled default.
    """
    assert last_year <= LAST_TRAINING_YEAR, (
        f"training years must end by {LAST_TRAINING_YEAR}; the evaluation "
        f"protocols own 2014+ (iteration 2014-2018, validation 2019, golden "
        f"2020)"
    )
    year = int(rng.integers(first_year, last_year + 1))
    horizon_hours = target_count * step_hours
    last_start = np.datetime64(f"{year}-12-31T00") - np.timedelta64(
        horizon_hours, "h"
    )
    first_start = np.datetime64(f"{year}-01-01T00")
    day_span = int((last_start - first_start) / np.timedelta64(1, "D"))
    start = first_start + np.timedelta64(int(rng.integers(0, day_span + 1)), "D")
    times = start + np.arange(target_count + 1) * np.timedelta64(step_hours, "h")
    values = source.read_state_times(times)
    return times, values
