# Copyright 2026 dynamaxx

from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

import jax
import jax.numpy as jnp
import numpy as np
import xarray as xr

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
    """Access processed WeatherBench2 Zarr data for fixed evaluations.

    The default path is the processed ERA5 1.5-degree, 6-hourly subset used by
    this project. A broader raw WeatherBench2 processing pipeline can use the
    same source interface later with a different path.
    """

    path: str = PROCESSED_ERA5_1P5DEG_6H_PATH
    storage_options: Mapping[str, Any] = field(default_factory=dict)
    chunks: Mapping[str, int] | None = None
    consolidated: bool | None = None
    _year_datasets: dict[int, xr.Dataset] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )
    _year_time_axes: dict[int, np.ndarray] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )
    _channel_index_cache: dict[tuple[int | None, tuple[str, ...]], np.ndarray] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )
    _state_channel_cache: dict[int | None, tuple[str, ...]] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )
    _constant_index_cache: dict[tuple[str, ...], np.ndarray] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )
    _spatial_coordinate_cache: dict[int | None, tuple[np.ndarray, np.ndarray]] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )
    _area_weight_cache: dict[int | None, np.ndarray] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    @cached_property
    def _dataset(self) -> xr.Dataset:
        """Open the source path as a single Zarr dataset."""
        return self._open_zarr(self.path)

    @cached_property
    def _single_store_time_axis(self) -> np.ndarray:
        """Time axis for a single Zarr source."""
        return np.asarray(self._dataset[TIME_COORDINATE].values, dtype="datetime64[ns]")

    @cached_property
    def _constants_dataset(self) -> xr.Dataset:
        """Open the constants Zarr store for a processed dataset collection."""
        return self._open_zarr(f"{self.path.rstrip('/')}/constants.zarr")

    @property
    def _is_collection(self) -> bool:
        return not self.path.rstrip("/").endswith(".zarr")

    def _open_year(self, year: int) -> xr.Dataset:
        """Open one yearly Zarr store from the processed dataset collection."""
        dataset = self._year_datasets.get(year)
        if dataset is None:
            dataset = self._open_zarr(f"{self.path.rstrip('/')}/years/{year}.zarr")
            self._year_datasets[year] = dataset
        return dataset

    def _year_time_axis(self, year: int) -> np.ndarray:
        """Return the cached time axis for one yearly store."""
        time_axis = self._year_time_axes.get(year)
        if time_axis is None:
            time_axis = np.asarray(
                self._open_year(year)[TIME_COORDINATE].values,
                dtype="datetime64[ns]",
            )
            self._year_time_axes[year] = time_axis
        return time_axis

    def prefetch_years(self, years: list[int] | tuple[int, ...]) -> None:
        """Open yearly datasets and time axes before trajectory reads."""
        for year in years:
            self._year_time_axis(int(year))

    def available_times(self, start: Any, end: Any) -> np.ndarray:
        """Return all stored timestamps in the inclusive requested interval."""
        start = np.datetime64(start, "ns")
        end = np.datetime64(end, "ns")
        if end < start:
            raise ValueError("end must not precede start")
        if not self._is_collection:
            time_axis = self._single_store_time_axis
            return time_axis[(time_axis >= start) & (time_axis <= end)]

        first_year = int(start.astype("datetime64[Y]").astype(np.int64) + 1970)
        final_year = int(end.astype("datetime64[Y]").astype(np.int64) + 1970)
        time_axes = [
            self._year_time_axis(year) for year in range(first_year, final_year + 1)
        ]
        time_axis = time_axes[0] if len(time_axes) == 1 else np.concatenate(time_axes)
        return time_axis[(time_axis >= start) & (time_axis <= end)]

    def _open_zarr(self, path: str) -> xr.Dataset:
        options: dict[str, Any] = {
            "chunks": self.chunks,
        }
        if self.consolidated is not None:
            options["consolidated"] = self.consolidated
        if self.storage_options and "://" in path:
            options["storage_options"] = dict(self.storage_options)
        return xr.open_zarr(path, **options)

    def read_state(
        self,
        time: Any,
        *,
        channels: Sequence[str] | None = None,
        dtype: Any = jnp.float32,
    ) -> np.ndarray:
        """Read one packed state as (channel, longitude, latitude)."""
        return self.read_state_times([time], channels=channels, dtype=dtype)[0]

    def read_state_times(
        self,
        times: Any,
        *,
        channels: Sequence[str] | None = None,
        dtype: Any = jnp.float32,
        parallel_workers: int = 1,
    ) -> np.ndarray:
        """Read exact times as (time, channel, longitude, latitude)."""
        times = np.asarray(times, dtype="datetime64[ns]")
        assert times.ndim == 1
        assert times.size
        if isinstance(parallel_workers, bool) or not isinstance(parallel_workers, int):
            raise TypeError("parallel_workers must be an integer")
        if parallel_workers < 1:
            raise ValueError("parallel_workers must be positive")

        read_order = np.argsort(times, kind="stable")
        return_order = np.empty_like(read_order)
        return_order[read_order] = np.arange(read_order.size)
        sorted_times = times[read_order]
        already_sorted = np.array_equal(read_order, np.arange(read_order.size))

        if not self._is_collection:
            channel_indices = self._channel_indices(channels) if channels else None
            indices = self._time_indices(self._single_store_time_axis, sorted_times)
            state_values = self._read_state_indices(
                self._dataset,
                indices,
                channel_indices=channel_indices,
                dtype=dtype,
            )
            return state_values if already_sorted else state_values[return_order]

        years = sorted_times.astype("datetime64[Y]").astype(np.int64) + 1970
        requests = []
        for year in dict.fromkeys(years.tolist()):
            year_times = sorted_times[years == year]
            indices = self._time_indices(self._year_time_axis(year), year_times)
            channel_indices = (
                self._channel_indices(channels, year=int(year)) if channels else None
            )
            requests.append(
                (
                    self._open_year(int(year)),
                    indices,
                    channel_indices,
                )
            )

        def read_request(request):
            dataset, indices, channel_indices = request
            return self._read_state_indices(
                dataset,
                indices,
                channel_indices=channel_indices,
                dtype=dtype,
            )

        if parallel_workers == 1 or len(requests) == 1:
            arrays = [read_request(request) for request in requests]
        else:
            worker_count = min(parallel_workers, len(requests))
            with ThreadPoolExecutor(
                max_workers=worker_count,
                thread_name_prefix="weatherbench2-read",
            ) as executor:
                arrays = list(executor.map(read_request, requests))
        state_values = arrays[0] if len(arrays) == 1 else np.concatenate(arrays, axis=0)
        return state_values if already_sorted else state_values[return_order]

    def state_channel_names(
        self,
        *,
        time: Any | None = None,
        year: int | None = None,
    ) -> tuple[str, ...]:
        """Return packed state channel names in source order."""
        if year is not None:
            cache_key = int(year)
        elif time is not None and self._is_collection:
            cache_key = int(np.datetime64(time, "Y").astype(np.int64) + 1970)
        else:
            assert not self._is_collection, (
                "collection metadata reads require time or year"
            )
            cache_key = None

        channel_names = self._state_channel_cache.get(cache_key)
        if channel_names is not None:
            return channel_names

        dataset = self._dataset if cache_key is None else self._open_year(cache_key)
        assert CHANNEL_COORDINATE in dataset.coords
        channel_names = tuple(
            str(channel_name)
            for channel_name in np.asarray(dataset[CHANNEL_COORDINATE].values)
        )
        self._state_channel_cache[cache_key] = channel_names
        return channel_names

    def read_constants(
        self,
        channels: Sequence[str],
        *,
        dtype: Any = jnp.float32,
    ) -> jax.Array:
        """Read constants as (constant, longitude, latitude)."""
        indices = self._constant_indices(channels)
        values = self._constants_dataset[CONSTANTS_VARIABLE].isel(
            {CONSTANT_CHANNEL_COORDINATE: indices}
        )
        values = values.transpose(
            CONSTANT_CHANNEL_COORDINATE,
            LONGITUDE_COORDINATE,
            LATITUDE_COORDINATE,
        )
        return jnp.asarray(values.to_numpy(), dtype=dtype)

    def spatial_coordinates(
        self,
        *,
        time: Any | None = None,
        year: int | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return longitude and latitude coordinates in degrees."""
        if year is not None:
            cache_key = int(year)
        elif time is not None and self._is_collection:
            cache_key = int(np.datetime64(time, "Y").astype(np.int64) + 1970)
        else:
            assert not self._is_collection, (
                "collection metadata reads require time or year"
            )
            cache_key = None

        coordinates = self._spatial_coordinate_cache.get(cache_key)
        if coordinates is None:
            dataset = self._dataset if cache_key is None else self._open_year(cache_key)
            assert LONGITUDE_COORDINATE in dataset.coords
            assert LATITUDE_COORDINATE in dataset.coords
            longitude = np.asarray(
                dataset[LONGITUDE_COORDINATE].values,
                dtype=np.float64,
            )
            latitude = np.asarray(
                dataset[LATITUDE_COORDINATE].values,
                dtype=np.float64,
            )
            longitude.setflags(write=False)
            latitude.setflags(write=False)
            coordinates = (longitude, latitude)
            self._spatial_coordinate_cache[cache_key] = coordinates
        return coordinates

    def area_weights(
        self,
        *,
        time: Any | None = None,
        year: int | None = None,
    ) -> np.ndarray:
        """Return spherical cell area weights with shape (longitude, latitude)."""
        if year is not None:
            cache_key = int(year)
        elif time is not None and self._is_collection:
            cache_key = int(np.datetime64(time, "Y").astype(np.int64) + 1970)
        else:
            assert not self._is_collection, (
                "collection metadata reads require time or year"
            )
            cache_key = None

        area_weights = self._area_weight_cache.get(cache_key)
        if area_weights is not None:
            return area_weights

        longitude, latitude = self.spatial_coordinates(time=time, year=year)
        longitude_weight = 2 * np.pi / longitude.size
        latitude_radians = np.deg2rad(latitude)
        differences = np.diff(latitude_radians)
        if not (np.all(differences > 0.0) or np.all(differences < 0.0)):
            raise ValueError("latitude coordinates must be strictly monotonic")
        ascending_latitude = (
            latitude_radians if differences[0] > 0.0 else latitude_radians[::-1]
        )
        latitude_bounds = np.concatenate(
            (
                np.asarray([-np.pi / 2], dtype=np.float64),
                (ascending_latitude[:-1] + ascending_latitude[1:]) / 2.0,
                np.asarray([np.pi / 2], dtype=np.float64),
            )
        )
        latitude_weights = np.diff(np.sin(latitude_bounds))
        if differences[0] < 0.0:
            latitude_weights = latitude_weights[::-1]
        area_weights = np.broadcast_to(
            longitude_weight * latitude_weights[np.newaxis, :],
            (longitude.size, latitude.size),
        )
        area_weights.setflags(write=False)
        self._area_weight_cache[cache_key] = area_weights
        return area_weights

    def _channel_indices(
        self,
        channels: Sequence[str],
        *,
        time: Any | None = None,
        year: int | None = None,
    ) -> np.ndarray:
        """Return integer indices for packed state channel names."""
        if year is not None:
            dataset_key = int(year)
        elif time is not None and self._is_collection:
            dataset_key = int(np.datetime64(time, "Y").astype(np.int64) + 1970)
        else:
            assert not self._is_collection, (
                "collection metadata reads require time or year"
            )
            dataset_key = None

        cache_key = (dataset_key, tuple(map(str, channels)))
        cached_indices = self._channel_index_cache.get(cache_key)
        if cached_indices is not None:
            return cached_indices

        dataset = self._dataset if dataset_key is None else self._open_year(dataset_key)
        assert CHANNEL_COORDINATE in dataset.coords
        channel_values = np.asarray(dataset[CHANNEL_COORDINATE].values)
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
        indices = np.asarray(
            [channel_to_index[str(channel_name)] for channel_name in channels],
            dtype=np.int64,
        )
        indices.setflags(write=False)
        self._channel_index_cache[cache_key] = indices
        return indices

    def _constant_indices(self, channels: Sequence[str]) -> np.ndarray:
        """Return integer indices for constant channel names."""
        cache_key = tuple(map(str, channels))
        cached_indices = self._constant_index_cache.get(cache_key)
        if cached_indices is not None:
            return cached_indices

        assert CONSTANT_CHANNEL_COORDINATE in self._constants_dataset.coords
        constant_values = np.asarray(
            self._constants_dataset[CONSTANT_CHANNEL_COORDINATE].values
        )
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
        indices = np.asarray(
            [constant_to_index[str(channel_name)] for channel_name in channels],
            dtype=np.int64,
        )
        indices.setflags(write=False)
        self._constant_index_cache[cache_key] = indices
        return indices

    def _read_state_indices(
        self,
        dataset: xr.Dataset,
        indices: np.ndarray,
        *,
        channel_indices: np.ndarray | None = None,
        dtype: Any,
    ) -> np.ndarray:
        state_values = dataset[STATE_VARIABLE].isel({TIME_COORDINATE: indices})
        if channel_indices is not None:
            state_values = state_values.isel({CHANNEL_COORDINATE: channel_indices})
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
        expected_dimensions = (
            *leading_dimensions,
            CHANNEL_COORDINATE,
            LONGITUDE_COORDINATE,
            LATITUDE_COORDINATE,
        )
        if state_values.dims != expected_dimensions:
            state_values = state_values.transpose(*expected_dimensions)
        return np.asarray(state_values.to_numpy(), dtype=np.dtype(dtype))

    def _time_indices(self, time_axis: np.ndarray, times: np.ndarray) -> np.ndarray:
        indices = np.searchsorted(time_axis, times)
        assert np.all(indices < time_axis.size)
        assert np.array_equal(time_axis[indices], times)
        return indices.astype(np.int64)
