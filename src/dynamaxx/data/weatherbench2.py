# Copyright 2026 dynamaxx

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

import jax
import jax.numpy as jnp
import numpy as np
import pandas as pd
import xarray as xr

from dynamaxx.dycore.grid import SphericalGrid
from dynamaxx.utils.consts import WEATHERBENCH2_ERA5_1P5DEG_6H_PATH

PROCESSED_ERA5_1P5DEG_6H_PATH = WEATHERBENCH2_ERA5_1P5DEG_6H_PATH

STATE_VARIABLE = "state"
CONSTANTS_VARIABLE = "constants"
CHANNEL_COORDINATE = "channel"
CONSTANT_CHANNEL_COORDINATE = "constant_channel"
TIME_COORDINATE = "time"
LONGITUDE_COORDINATE = "longitude"
LATITUDE_COORDINATE = "latitude"


@dataclass(frozen=True)
class WeatherBench2Source:
    """Access a processed WeatherBench2 Zarr dataset and project fields to a grid.

    The default path is the processed ERA5 1.5-degree, 6-hourly subset used by
    this project. A broader raw WeatherBench2 processing pipeline can use the
    same source interface later with a different path.
    """

    path: str = PROCESSED_ERA5_1P5DEG_6H_PATH
    storage_options: Mapping[str, Any] = field(default_factory=dict)
    chunks: Mapping[str, int] | None = None
    consolidated: bool | None = None
    year_datasets: dict[int, xr.Dataset] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )
    year_time_axes: dict[int, np.ndarray] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    @cached_property
    def dataset(self) -> xr.Dataset:
        """Open the source path as a single Zarr dataset."""
        return self._open_zarr(self.path)

    @cached_property
    def time_axis(self) -> np.ndarray:
        """Time axis for a single Zarr source."""
        return self._time_axis(self.dataset)

    @cached_property
    def constants_dataset(self) -> xr.Dataset:
        """Open the constants Zarr store for a processed dataset collection."""
        return self._open_zarr(self.constants_path())

    @property
    def _is_collection(self) -> bool:
        return not self.path.rstrip("/").endswith(".zarr")

    def open_year(self, year: int) -> xr.Dataset:
        """Open one yearly Zarr store from the processed dataset collection."""
        dataset = self.year_datasets.get(year)
        if dataset is None:
            dataset = self._open_zarr(self.year_path(year))
            self.year_datasets[year] = dataset
        return dataset

    def year_time_axis(self, year: int) -> np.ndarray:
        """Return the cached time axis for one yearly store."""
        time_axis = self.year_time_axes.get(year)
        if time_axis is None:
            time_axis = self._time_axis(self.open_year(year))
            self.year_time_axes[year] = time_axis
        return time_axis

    def prefetch_years(self, years: list[int] | tuple[int, ...]) -> None:
        """Open yearly datasets and time axes before trajectory reads."""
        for year in years:
            self.year_time_axis(int(year))

    def year_path(self, year: int) -> str:
        """Return the yearly Zarr path for this processed dataset collection."""
        return f"{self.path.rstrip('/')}/years/{year}.zarr"

    def constants_path(self) -> str:
        """Return the constants Zarr path for this processed dataset collection."""
        return f"{self.path.rstrip('/')}/constants.zarr"

    def _open_zarr(self, path: str) -> xr.Dataset:
        options: dict[str, Any] = {
            "chunks": self.chunks,
        }
        if self.consolidated is not None:
            options["consolidated"] = self.consolidated
        if self.storage_options and "://" in path:
            options["storage_options"] = dict(self.storage_options)
        return xr.open_zarr(path, **options)

    def select_field(
        self,
        variable: str,
        *,
        time: Any | None = None,
        level: Any | None = None,
        year: int | None = None,
        selectors: Mapping[str, Any] | None = None,
    ) -> xr.DataArray:
        """Select one variable and optional coordinates from the dataset."""
        dataset = self._dataset_for_selection(time=time, year=year)
        assert STATE_VARIABLE in dataset.data_vars
        assert CHANNEL_COORDINATE in dataset.coords

        channel_name = self.channel_name(variable, level=level)
        field_values = dataset[STATE_VARIABLE].sel({CHANNEL_COORDINATE: channel_name})

        field_selectors = dict(selectors or {})
        if time is not None:
            field_selectors[TIME_COORDINATE] = time

        if field_selectors:
            field_values = field_values.sel(field_selectors)
        return field_values

    def select_state(
        self,
        *,
        time: Any | None = None,
        year: int | None = None,
        selectors: Mapping[str, Any] | None = None,
    ) -> xr.DataArray:
        """Select a packed weather state with dimensions ending in lon-lat."""
        dataset = self._dataset_for_selection(time=time, year=year)
        assert STATE_VARIABLE in dataset.data_vars

        state_values = dataset[STATE_VARIABLE]
        state_selectors = dict(selectors or {})
        if time is not None:
            state_selectors[TIME_COORDINATE] = time
        if state_selectors:
            state_values = state_values.sel(state_selectors)
        return self._transpose_state(state_values)

    def read_state(
        self,
        time: Any,
        *,
        channels: Sequence[str] | None = None,
        dtype: Any = jnp.float32,
    ) -> jax.Array:
        """Read one packed state as (channel, longitude, latitude)."""
        return self.read_state_times([time], channels=channels, dtype=dtype)[0]

    def read_state_times(
        self,
        times: Any,
        *,
        channels: Sequence[str] | None = None,
        dtype: Any = jnp.float32,
    ) -> jax.Array:
        """Read exact times as (time, channel, longitude, latitude)."""
        times = np.asarray(times, dtype="datetime64[ns]")
        assert times.ndim == 1
        assert times.size

        read_order = np.argsort(times, kind="stable")
        return_order = np.empty_like(read_order)
        return_order[read_order] = np.arange(read_order.size)
        sorted_times = times[read_order]

        if not self._is_collection:
            channel_indices = self.channel_indices(channels) if channels else None
            indices = self._time_indices(self.time_axis, sorted_times)
            state_values = self._read_state_indices(
                self.dataset,
                indices,
                channel_indices=channel_indices,
                dtype=dtype,
            )
            return state_values[return_order]

        years = np.asarray([pd.Timestamp(time).year for time in sorted_times])
        channel_indices = (
            self.channel_indices(channels, year=int(years[0])) if channels else None
        )
        arrays = []
        for year in dict.fromkeys(years.tolist()):
            year_times = sorted_times[years == year]
            indices = self._time_indices(self.year_time_axis(year), year_times)
            arrays.append(
                self._read_state_indices(
                    self.open_year(year),
                    indices,
                    channel_indices=channel_indices,
                    dtype=dtype,
                )
            )
        return jnp.concatenate(arrays, axis=0)[return_order]

    def read_state_range(
        self,
        *,
        start_time: Any,
        end_time: Any,
        dtype: Any = jnp.float32,
    ) -> jax.Array:
        """Read an inclusive time range as (time, channel, longitude, latitude)."""
        return self.read_state_times(
            self.times_between(start_time=start_time, end_time=end_time),
            dtype=dtype,
        )

    def times_between(self, *, start_time: Any, end_time: Any) -> np.ndarray:
        """Return available timestamps in an inclusive time range."""
        start_time = np.datetime64(start_time, "ns")
        end_time = np.datetime64(end_time, "ns")
        assert start_time <= end_time

        if not self._is_collection:
            return self._slice_time_axis(self.time_axis, start_time, end_time)

        start_year = pd.Timestamp(start_time).year
        end_year = pd.Timestamp(end_time).year
        time_arrays = []

        for year in range(start_year, end_year + 1):
            time_axis = self._slice_time_axis(
                self.year_time_axis(year),
                start_time,
                end_time,
            )
            if time_axis.size:
                time_arrays.append(time_axis)
        assert time_arrays
        return np.concatenate(time_arrays)

    def trajectory_times(
        self,
        start_time: Any,
        *,
        steps: int,
        step_hours: int = 6,
    ) -> np.ndarray:
        """Return equally spaced trajectory verification timestamps."""
        assert steps >= 1
        start_time = np.datetime64(start_time, "ns")
        step = np.timedelta64(step_hours, "h")
        return start_time + np.arange(steps) * step

    def read_state_trajectory(
        self,
        start_time: Any,
        *,
        steps: int,
        step_hours: int = 6,
        channels: Sequence[str] | None = None,
        dtype: Any = jnp.float32,
    ) -> jax.Array:
        """Read a trajectory block as (time, channel, longitude, latitude)."""
        return self.read_state_times(
            self.trajectory_times(start_time, steps=steps, step_hours=step_hours),
            channels=channels,
            dtype=dtype,
        )

    def read_modal_state(
        self,
        time: Any,
        grid: SphericalGrid,
        *,
        dtype: Any = jnp.float32,
    ) -> jax.Array:
        """Read one packed state and project every channel to modal space."""
        state_values = self.read_state(time, dtype=dtype)
        return grid.nodal_to_modal(state_values)

    def read_modal_state_range(
        self,
        *,
        start_time: Any,
        end_time: Any,
        grid: SphericalGrid,
        dtype: Any = jnp.float32,
    ) -> jax.Array:
        """Read a packed state range and project every channel to modal space."""
        state_values = self.read_state_range(
            start_time=start_time,
            end_time=end_time,
            dtype=dtype,
        )
        return grid.nodal_to_modal(state_values)

    def read_modal_state_trajectory(
        self,
        start_time: Any,
        *,
        steps: int,
        grid: SphericalGrid,
        step_hours: int = 6,
        dtype: Any = jnp.float32,
    ) -> jax.Array:
        """Read a trajectory block and project every channel to modal space."""
        state_values = self.read_state_trajectory(
            start_time,
            steps=steps,
            step_hours=step_hours,
            dtype=dtype,
        )
        return grid.nodal_to_modal(state_values)

    def channel_name(self, variable: str, *, level: Any | None = None) -> str:
        """Return the exact state channel name for this processed dataset."""
        if level is None:
            return variable
        return f"{variable}_{int(level)}"

    def spatial_coordinates(
        self,
        *,
        time: Any | None = None,
        year: int | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return longitude and latitude coordinates in degrees."""
        dataset = self._dataset_for_selection(time=time, year=year)
        assert LONGITUDE_COORDINATE in dataset.coords
        assert LATITUDE_COORDINATE in dataset.coords
        return (
            np.asarray(dataset[LONGITUDE_COORDINATE].values, dtype=np.float64),
            np.asarray(dataset[LATITUDE_COORDINATE].values, dtype=np.float64),
        )

    def area_weights(
        self,
        *,
        time: Any | None = None,
        year: int | None = None,
    ) -> np.ndarray:
        """Return spherical cell area weights with shape (longitude, latitude)."""
        longitude, latitude = self.spatial_coordinates(time=time, year=year)
        longitude_weight = 2 * np.pi / longitude.size
        sin_latitude = np.sin(np.deg2rad(latitude))
        latitude_edges = np.empty(latitude.size + 1, dtype=np.float64)
        latitude_edges[0] = sin_latitude[0]
        latitude_edges[-1] = sin_latitude[-1]
        latitude_edges[1:-1] = 0.5 * (sin_latitude[:-1] + sin_latitude[1:])
        latitude_weights = np.abs(np.diff(latitude_edges))
        return np.broadcast_to(
            longitude_weight * latitude_weights[np.newaxis, :],
            (longitude.size, latitude.size),
        )

    def channel_values(
        self,
        *,
        time: Any | None = None,
        year: int | None = None,
    ) -> np.ndarray:
        """Return packed state channel names for a single dataset or year."""
        dataset = self._dataset_for_selection(time=time, year=year)
        assert CHANNEL_COORDINATE in dataset.coords
        return np.asarray(dataset[CHANNEL_COORDINATE].values)

    def channel_indices(
        self,
        channels: Sequence[str],
        *,
        time: Any | None = None,
        year: int | None = None,
    ) -> np.ndarray:
        """Return integer indices for packed state channel names."""
        channel_values = self.channel_values(time=time, year=year)
        channel_to_index = {
            str(channel_name): channel_index
            for channel_index, channel_name in enumerate(channel_values)
        }
        missing_channels = [
            channel_name
            for channel_name in channels
            if str(channel_name) not in channel_to_index
        ]
        assert not missing_channels, f"unknown channels {missing_channels}"
        return np.asarray(
            [channel_to_index[str(channel_name)] for channel_name in channels],
            dtype=np.int64,
        )

    def constant_values(self) -> np.ndarray:
        """Return available constant channel names."""
        assert CONSTANT_CHANNEL_COORDINATE in self.constants_dataset.coords
        return np.asarray(self.constants_dataset[CONSTANT_CHANNEL_COORDINATE].values)

    def constant_indices(self, channels: Sequence[str]) -> np.ndarray:
        """Return integer indices for constant channel names."""
        constant_values = self.constant_values()
        constant_to_index = {
            str(channel_name): channel_index
            for channel_index, channel_name in enumerate(constant_values)
        }
        missing_channels = [
            channel_name
            for channel_name in channels
            if str(channel_name) not in constant_to_index
        ]
        assert not missing_channels, f"unknown constants {missing_channels}"
        return np.asarray(
            [constant_to_index[str(channel_name)] for channel_name in channels],
            dtype=np.int64,
        )

    def read_constants(
        self,
        channels: Sequence[str],
        *,
        dtype: Any = jnp.float32,
    ) -> jax.Array:
        """Read constants as (constant, longitude, latitude)."""
        indices = self.constant_indices(channels)
        values = self.constants_dataset[CONSTANTS_VARIABLE].isel(
            {CONSTANT_CHANNEL_COORDINATE: indices}
        )
        values = values.transpose(
            CONSTANT_CHANNEL_COORDINATE,
            LONGITUDE_COORDINATE,
            LATITUDE_COORDINATE,
        )
        return jnp.asarray(values.to_numpy(), dtype=dtype)

    def field_to_grid(
        self,
        field_values: xr.DataArray,
        grid: SphericalGrid,
        *,
        dtype: Any = jnp.float32,
    ) -> jax.Array:
        """Interpolate a field to grid nodes and return longitude-latitude arrays.

        Latitude and longitude dimensions are moved to the final two axes, so
        the returned shape is (*batch, longitude_nodes, latitude_nodes).
        """
        assert LONGITUDE_COORDINATE in field_values.coords
        assert LATITUDE_COORDINATE in field_values.coords

        field_values = self._normalize_longitude(field_values)
        field_values = field_values.sortby(LATITUDE_COORDINATE)

        target_coordinates = {
            LONGITUDE_COORDINATE: np.rad2deg(grid.longitude),
            LATITUDE_COORDINATE: np.rad2deg(grid.latitude),
        }
        field_values = field_values.interp(target_coordinates)

        leading_dimensions = [
            dimension
            for dimension in field_values.dims
            if dimension not in (LONGITUDE_COORDINATE, LATITUDE_COORDINATE)
        ]
        field_values = field_values.transpose(
            *leading_dimensions,
            LONGITUDE_COORDINATE,
            LATITUDE_COORDINATE,
        )
        return jnp.asarray(field_values.to_numpy(), dtype=dtype)

    def field_to_modal(
        self,
        field_values: xr.DataArray,
        grid: SphericalGrid,
        *,
        dtype: Any = jnp.float32,
    ) -> jax.Array:
        """Interpolate a field to a grid and project it to modal coefficients."""
        nodal_values = self.field_to_grid(field_values, grid, dtype=dtype)
        return grid.nodal_to_modal(nodal_values)

    def _transpose_state(self, state_values: xr.DataArray) -> xr.DataArray:
        leading_dimensions = [
            dimension
            for dimension in state_values.dims
            if dimension
            not in (
                CHANNEL_COORDINATE,
                LONGITUDE_COORDINATE,
                LATITUDE_COORDINATE,
            )
        ]
        return state_values.transpose(
            *leading_dimensions,
            CHANNEL_COORDINATE,
            LONGITUDE_COORDINATE,
            LATITUDE_COORDINATE,
        )

    def _read_state_indices(
        self,
        dataset: xr.Dataset,
        indices: np.ndarray,
        *,
        channel_indices: np.ndarray | None = None,
        dtype: Any,
    ) -> jax.Array:
        state_values = dataset[STATE_VARIABLE].isel({TIME_COORDINATE: indices})
        if channel_indices is not None:
            state_values = state_values.isel({CHANNEL_COORDINATE: channel_indices})
        state_values = self._transpose_state(state_values)
        return jnp.asarray(state_values.to_numpy(), dtype=dtype)

    def _dataset_for_selection(
        self,
        *,
        time: Any | None,
        year: int | None,
    ) -> xr.Dataset:
        if year is not None:
            return self.open_year(year)
        if time is not None and self._is_collection:
            return self.open_year(pd.Timestamp(time).year)
        return self.dataset

    def _time_indices(self, time_axis: np.ndarray, times: np.ndarray) -> np.ndarray:
        indices = np.searchsorted(time_axis, times)
        assert np.all(indices < time_axis.size)
        assert np.array_equal(time_axis[indices], times)
        return indices.astype(np.int64)

    def _slice_time_axis(
        self,
        time_axis: np.ndarray,
        start_time: np.datetime64,
        end_time: np.datetime64,
    ) -> np.ndarray:
        mask = (time_axis >= start_time) & (time_axis <= end_time)
        return time_axis[mask]

    def _time_axis(self, dataset: xr.Dataset) -> np.ndarray:
        return np.asarray(dataset[TIME_COORDINATE].values, dtype="datetime64[ns]")

    def _normalize_longitude(
        self,
        field_values: xr.DataArray,
    ) -> xr.DataArray:
        longitude_values = np.asarray(field_values[LONGITUDE_COORDINATE])
        if np.nanmin(longitude_values) < 0:
            field_values = field_values.assign_coords(
                {LONGITUDE_COORDINATE: field_values[LONGITUDE_COORDINATE] % 360}
            )
        return field_values.sortby(LONGITUDE_COORDINATE)
