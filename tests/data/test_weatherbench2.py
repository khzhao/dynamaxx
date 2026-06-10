import jax.numpy as jnp
import numpy as np
import xarray as xr

from dynamaxx.data.weatherbench2 import (
    PROCESSED_ERA5_1P5DEG_6H_PATH,
    WeatherBench2Source,
)
from dynamaxx.dycore.grid import SphericalGrid


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


def test_channel_name_uses_processed_dataset_convention():
    source = WeatherBench2Source()

    assert source.channel_name("2m_temperature") == "2m_temperature"
    assert source.channel_name("geopotential", level=500) == "geopotential_500"


def test_select_field_loads_surface_and_pressure_level_channels(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_test_state_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))

    surface_values = source.select_field(
        "2m_temperature",
        time=np.datetime64("2020-01-01T06:00:00"),
    )
    pressure_values = source.select_field("geopotential", level=500)

    assert surface_values.dims == ("longitude", "latitude")
    assert pressure_values.dims == ("time", "longitude", "latitude")
    np.testing.assert_allclose(
        surface_values.sel(latitude=90.0, longitude=180.0),
        270.0,
    )
    np.testing.assert_allclose(pressure_values, 5000.0)


def test_select_field_infers_year_store_for_processed_collection(tmp_path):
    collection_path = tmp_path / "processed"
    year_path = collection_path / "years" / "2020.zarr"
    year_path.parent.mkdir(parents=True)
    _write_test_state_dataset(year_path)
    source = WeatherBench2Source(path=str(collection_path))

    field_values = source.select_field(
        "2m_temperature",
        time=np.datetime64("2020-01-01T06:00:00"),
    )

    assert field_values.dims == ("longitude", "latitude")
    np.testing.assert_allclose(field_values.sel(latitude=90.0, longitude=180.0), 270.0)


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


def test_channel_indices_resolve_packed_state_channels(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_test_state_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))

    indices = source.channel_indices(["geopotential_500", "2m_temperature"])

    np.testing.assert_array_equal(indices, np.array([1, 0]))


def test_read_constants_returns_requested_constant_channels(tmp_path):
    collection_path = tmp_path / "processed"
    collection_path.mkdir()
    _write_test_constants_dataset(collection_path / "constants.zarr")
    source = WeatherBench2Source(path=str(collection_path))

    values = source.read_constants(["orography", "land_sea_mask"])

    assert values.shape == (2, 4, 3)
    np.testing.assert_allclose(values[0, :, 0], np.arange(4))
    np.testing.assert_allclose(values[1], 1.0)


def test_read_state_range_returns_time_channel_longitude_latitude_array(tmp_path):
    collection_path = tmp_path / "processed"
    years_path = collection_path / "years"
    years_path.mkdir(parents=True)
    _write_test_state_dataset_for_year(years_path / "2020.zarr", 2020, 20.0)
    _write_test_state_dataset_for_year(years_path / "2021.zarr", 2021, 21.0)
    source = WeatherBench2Source(path=str(collection_path))

    state_values = source.read_state_range(
        start_time=np.datetime64("2020-01-01T06:00:00"),
        end_time=np.datetime64("2021-01-01T00:00:00"),
    )

    assert state_values.shape == (2, 2, 4, 3)
    np.testing.assert_allclose(state_values[:, 0, 0, 0], np.array([20.0, 21.0]))


def test_year_datasets_and_time_axes_are_cached(tmp_path):
    collection_path = tmp_path / "processed"
    years_path = collection_path / "years"
    years_path.mkdir(parents=True)
    _write_test_state_dataset_for_year(years_path / "2020.zarr", 2020, 20.0)
    source = WeatherBench2Source(path=str(collection_path))

    first_dataset = source.open_year(2020)
    first_time_axis = source.year_time_axis(2020)

    assert first_dataset is source.open_year(2020)
    assert first_time_axis is source.year_time_axis(2020)
    assert sorted(source.year_datasets) == [2020]
    assert sorted(source.year_time_axes) == [2020]


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


def test_read_state_trajectory_uses_regular_time_steps(tmp_path):
    collection_path = tmp_path / "processed"
    years_path = collection_path / "years"
    years_path.mkdir(parents=True)
    _write_test_state_dataset_for_year(years_path / "2020.zarr", 2020, 20.0)
    source = WeatherBench2Source(path=str(collection_path))

    state_values = source.read_state_trajectory(
        np.datetime64("2020-01-01T00:00:00"),
        steps=2,
    )

    assert state_values.shape == (2, 2, 4, 3)
    np.testing.assert_allclose(state_values[:, 0, 0, 0], np.array([20.0, 20.0]))


def test_read_modal_state_projects_all_channels(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_test_state_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    grid = SphericalGrid(
        total_wavenumbers=2,
        longitude_nodes=4,
        latitude_nodes=3,
        latitude_spacing="equiangular_with_poles",
    )

    state_values = source.read_state(np.datetime64("2020-01-01T00:00:00"))
    modal_state = source.read_modal_state(np.datetime64("2020-01-01T00:00:00"), grid)

    assert modal_state.shape == (3, *grid.modal_shape)
    np.testing.assert_allclose(modal_state, grid.nodal_to_modal(state_values))


def test_read_modal_state_range_projects_trajectory_targets(tmp_path):
    collection_path = tmp_path / "processed"
    years_path = collection_path / "years"
    years_path.mkdir(parents=True)
    _write_test_state_dataset_for_year(years_path / "2020.zarr", 2020, 20.0)
    source = WeatherBench2Source(path=str(collection_path))
    grid = SphericalGrid(
        total_wavenumbers=2,
        longitude_nodes=4,
        latitude_nodes=3,
        latitude_spacing="equiangular_with_poles",
    )

    modal_state = source.read_modal_state_range(
        start_time=np.datetime64("2020-01-01T00:00:00"),
        end_time=np.datetime64("2020-01-01T06:00:00"),
        grid=grid,
    )

    assert modal_state.shape == (2, 2, *grid.modal_shape)


def test_read_modal_state_trajectory_projects_trajectory_targets(tmp_path):
    collection_path = tmp_path / "processed"
    years_path = collection_path / "years"
    years_path.mkdir(parents=True)
    _write_test_state_dataset_for_year(years_path / "2020.zarr", 2020, 20.0)
    source = WeatherBench2Source(path=str(collection_path))
    grid = SphericalGrid(
        total_wavenumbers=2,
        longitude_nodes=4,
        latitude_nodes=3,
        latitude_spacing="equiangular_with_poles",
    )

    modal_state = source.read_modal_state_trajectory(
        np.datetime64("2020-01-01T00:00:00"),
        steps=2,
        grid=grid,
    )

    assert modal_state.shape == (2, 2, *grid.modal_shape)


def test_field_to_grid_matches_spherical_grid_node_order(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_test_state_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    grid = SphericalGrid(
        total_wavenumbers=2,
        longitude_nodes=4,
        latitude_nodes=3,
        latitude_spacing="equiangular_with_poles",
    )
    field_values = source.select_field(
        "2m_temperature",
        time=source.dataset.time[0],
    )

    nodal_values = source.field_to_grid(field_values, grid)
    expected = np.array(
        [
            [-90.0, 0.0, 90.0],
            [0.0, 90.0, 180.0],
            [90.0, 180.0, 270.0],
            [180.0, 270.0, 360.0],
        ],
        dtype=np.float32,
    )

    assert nodal_values.shape == grid.nodal_shape
    np.testing.assert_allclose(nodal_values, expected)


def test_field_to_grid_preserves_leading_dimensions(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_test_state_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    grid = SphericalGrid(
        total_wavenumbers=2,
        longitude_nodes=4,
        latitude_nodes=3,
        latitude_spacing="equiangular_with_poles",
    )
    field_values = source.select_field("2m_temperature")

    nodal_values = source.field_to_grid(field_values, grid)

    assert nodal_values.shape == (2, *grid.nodal_shape)


def test_field_to_modal_matches_grid_projection(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_test_state_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    grid = SphericalGrid(
        total_wavenumbers=2,
        longitude_nodes=4,
        latitude_nodes=3,
        latitude_spacing="equiangular_with_poles",
    )
    field_values = source.select_field("constant", time=source.dataset.time[0])

    nodal_values = source.field_to_grid(field_values, grid)
    modal_values = source.field_to_modal(field_values, grid)

    np.testing.assert_allclose(modal_values, grid.nodal_to_modal(nodal_values))
    np.testing.assert_allclose(modal_values[0, 0], 2 * jnp.sqrt(jnp.pi), atol=2e-5)
