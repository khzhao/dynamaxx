import jax.numpy as jnp
import numpy as np
import xarray as xr

from dynamaxx.data.weatherbench2 import (
    PROCESSED_ERA5_1P5DEG_6H_PATH,
    WeatherBench2Source,
)


def _write_test_state_dataset(path):
    time = np.array(["2020-01-01T00:00:00", "2020-01-01T06:00:00"], dtype="datetime64")
    channel = np.array(["2m_temperature", "geopotential_500", "constant"])
    latitude = np.array([90.0, 0.0, -90.0])
    longitude = np.array([0.0, 90.0, 180.0, 270.0])
    values = np.zeros((time.size, channel.size, longitude.size, latitude.size))

    for longitude_index, longitude_value in enumerate(longitude):
        for latitude_index, latitude_value in enumerate(latitude):
            values[:, 0, longitude_index, latitude_index] = (
                latitude_value + longitude_value
            )
    values[:, 1] = 5000.0
    values[:, 2] = 1.0

    dataset = xr.Dataset(
        {
            "state": (
                ("time", "channel", "longitude", "latitude"),
                values,
            ),
        },
        coords={
            "time": time,
            "channel": channel,
            "latitude": latitude,
            "longitude": longitude,
        },
    )
    dataset.to_zarr(path, mode="w")


def _write_test_state_dataset_for_year(path, year: int, value: float):
    time = np.array(
        [f"{year}-01-01T00:00:00", f"{year}-01-01T06:00:00"],
        dtype="datetime64",
    )
    channel = np.array(["2m_temperature", "constant"])
    latitude = np.array([90.0, 0.0, -90.0])
    longitude = np.array([0.0, 90.0, 180.0, 270.0])
    values = np.full(
        (time.size, channel.size, longitude.size, latitude.size),
        value,
    )
    values[:, 1] = 1.0

    dataset = xr.Dataset(
        {
            "state": (
                ("time", "channel", "longitude", "latitude"),
                values,
            ),
        },
        coords={
            "time": time,
            "channel": channel,
            "latitude": latitude,
            "longitude": longitude,
        },
    )
    dataset.to_zarr(path, mode="w")


def _write_test_constants_dataset(path):
    constant_channel = np.array(["land_sea_mask", "orography"])
    latitude = np.array([90.0, 0.0, -90.0])
    longitude = np.array([0.0, 90.0, 180.0, 270.0])
    values = np.zeros((constant_channel.size, longitude.size, latitude.size))
    values[0] = 1.0
    values[1] = np.arange(longitude.size)[:, np.newaxis]

    dataset = xr.Dataset(
        {
            "constants": (
                ("constant_channel", "longitude", "latitude"),
                values,
            ),
        },
        coords={
            "constant_channel": constant_channel,
            "latitude": latitude,
            "longitude": longitude,
        },
    )
    dataset.to_zarr(path, mode="w")


def test_weatherbench2_source_uses_processed_project_dataset_path_by_default():
    assert WeatherBench2Source().path == PROCESSED_ERA5_1P5DEG_6H_PATH


def test_read_state_returns_channel_longitude_latitude_array(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_test_state_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))

    state_values = source.read_state(np.datetime64("2020-01-01T06:00:00"))

    assert state_values.shape == (3, 4, 3)
    np.testing.assert_allclose(state_values[0, 2, 0], 270.0)
    np.testing.assert_allclose(state_values[1], 5000.0)
    assert state_values.dtype == jnp.float32


def test_read_state_can_select_channels(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_test_state_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))

    state_values = source.read_state(
        np.datetime64("2020-01-01T06:00:00"),
        channels=["constant", "2m_temperature"],
    )

    assert state_values.shape == (2, 4, 3)
    np.testing.assert_allclose(state_values[0], 1.0)
    np.testing.assert_allclose(state_values[1, 2, 0], 270.0)


def test_read_constants_returns_requested_constant_channels(tmp_path):
    collection_path = tmp_path / "processed"
    collection_path.mkdir()
    _write_test_constants_dataset(collection_path / "constants.zarr")
    source = WeatherBench2Source(path=str(collection_path))

    values = source.read_constants(["orography", "land_sea_mask"])

    assert values.shape == (2, 4, 3)
    np.testing.assert_allclose(values[0, :, 0], np.arange(4))
    np.testing.assert_allclose(values[1], 1.0)


def test_year_datasets_and_time_axes_are_cached(tmp_path):
    collection_path = tmp_path / "processed"
    years_path = collection_path / "years"
    years_path.mkdir(parents=True)
    _write_test_state_dataset_for_year(years_path / "2020.zarr", 2020, 20.0)
    source = WeatherBench2Source(path=str(collection_path))

    source.prefetch_years([2020])
    first_dataset = source._year_datasets[2020]
    first_time_axis = source._year_time_axes[2020]

    source.prefetch_years([2020])
    assert first_dataset is source._year_datasets[2020]
    assert first_time_axis is source._year_time_axes[2020]
    assert sorted(source._year_datasets) == [2020]
    assert sorted(source._year_time_axes) == [2020]


def test_read_state_times_preserves_requested_order_across_years(tmp_path):
    collection_path = tmp_path / "processed"
    years_path = collection_path / "years"
    years_path.mkdir(parents=True)
    _write_test_state_dataset_for_year(years_path / "2020.zarr", 2020, 20.0)
    _write_test_state_dataset_for_year(years_path / "2021.zarr", 2021, 21.0)
    source = WeatherBench2Source(path=str(collection_path))

    state_values = source.read_state_times(
        [
            np.datetime64("2021-01-01T00:00:00"),
            np.datetime64("2020-01-01T06:00:00"),
        ],
    )

    assert state_values.shape == (2, 2, 4, 3)
    np.testing.assert_allclose(state_values[:, 0, 0, 0], np.array([21.0, 20.0]))


def test_spatial_coordinates_return_weatherbench_axes(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_test_state_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))

    longitude, latitude = source.spatial_coordinates()

    np.testing.assert_array_equal(longitude, np.array([0.0, 90.0, 180.0, 270.0]))
    np.testing.assert_array_equal(latitude, np.array([90.0, 0.0, -90.0]))


def test_area_weights_match_grid_shape_and_sphere_area(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_test_state_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))

    area_weights = source.area_weights()

    assert area_weights.shape == (4, 3)
    np.testing.assert_allclose(np.sum(area_weights), 4.0 * np.pi)


def test_metadata_helpers_reuse_cached_arrays(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_test_state_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))

    longitude, latitude = source.spatial_coordinates()
    cached_longitude, cached_latitude = source.spatial_coordinates()
    area_weights = source.area_weights()

    assert longitude is cached_longitude
    assert latitude is cached_latitude
    assert area_weights is source.area_weights()
    assert not longitude.flags.writeable
    assert not latitude.flags.writeable
    assert not area_weights.flags.writeable
