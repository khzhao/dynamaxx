# Copyright 2026 dynamaxx

from __future__ import annotations

import argparse
import logging
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr

STATE_VARIABLE = "state"
CONSTANTS_VARIABLE = "constants"
CHANNEL_COORDINATE = "channel"
CONSTANT_CHANNEL_COORDINATE = "constant_channel"
TIME_COORDINATE = "time"
LONGITUDE_COORDINATE = "longitude"
LATITUDE_COORDINATE = "latitude"
PACKED_SCHEMA_VERSION = "packed-weatherbench2-state-v1"

logger = logging.getLogger("packed_state_zarr")


@dataclass(frozen=True)
class PackedStateZarrConfig:
    """Configuration for a WeatherBench2 packed-state Zarr conversion."""

    source_path: str
    output_path: str
    state_variables: tuple[str, ...] | None = None
    constant_variables: tuple[str, ...] | None = None
    years: tuple[int, ...] | None = None
    start_time: str | None = None
    stop_time: str | None = None
    source_chunks: Mapping[str, int] = field(default_factory=dict)
    time_chunk_size: int = 1
    channel_chunk_size: int | None = None
    longitude_chunk_size: int | None = None
    latitude_chunk_size: int | None = None
    consolidated: bool | None = None
    overwrite: bool = False
    split_by_year: bool = True


def pack_weatherbench2_state_zarr(config: PackedStateZarrConfig) -> None:
    """Convert a WeatherBench2-style source Zarr into packed state Zarr stores."""
    source = _open_source_zarr(config)
    source = _select_time_range(source, config.start_time, config.stop_time)

    state_variables = _variable_names(
        source,
        selected_variables=config.state_variables,
        requires_time=True,
    )
    constant_variables = _variable_names(
        source,
        selected_variables=config.constant_variables,
        requires_time=False,
    )
    assert state_variables, "no state variables selected for packing"

    _prepare_output_path(config.output_path, overwrite=config.overwrite)
    if config.split_by_year:
        _write_yearly_state_collection(
            source, config.output_path, state_variables, config
        )
    else:
        packed_state = _packed_state_dataset(source, state_variables, config)
        _write_zarr(packed_state, config.output_path)

    if constant_variables:
        constants_output_path = (
            f"{config.output_path.rstrip('/')}/constants.zarr"
            if config.split_by_year
            else f"{_without_zarr_suffix(config.output_path)}_constants.zarr"
        )
        constants = _packed_constants_dataset(source, constant_variables, config)
        _write_zarr(constants, constants_output_path)


def _open_source_zarr(config: PackedStateZarrConfig) -> xr.Dataset:
    options: dict[str, Any] = {"chunks": dict(config.source_chunks)}
    if config.consolidated is not None:
        options["consolidated"] = config.consolidated
    return xr.open_zarr(config.source_path, **options)


def _select_time_range(
    dataset: xr.Dataset,
    start_time: str | None,
    stop_time: str | None,
) -> xr.Dataset:
    if start_time is None and stop_time is None:
        return dataset
    assert TIME_COORDINATE in dataset.coords, "source dataset has no time coordinate"
    return dataset.sel({TIME_COORDINATE: slice(start_time, stop_time)})


def _variable_names(
    dataset: xr.Dataset,
    *,
    selected_variables: tuple[str, ...] | None,
    requires_time: bool,
) -> tuple[str, ...]:
    if selected_variables is not None:
        missing_variables = [
            variable_name
            for variable_name in selected_variables
            if variable_name not in dataset.data_vars
        ]
        assert not missing_variables, f"unknown source variables {missing_variables}"
        return selected_variables

    inferred_variables = []
    for variable_name, data_array in dataset.data_vars.items():
        has_time = TIME_COORDINATE in data_array.dims
        has_spatial_axes = (
            LONGITUDE_COORDINATE in data_array.dims
            and LATITUDE_COORDINATE in data_array.dims
        )
        if has_time == requires_time and has_spatial_axes:
            inferred_variables.append(variable_name)
    return tuple(inferred_variables)


def _write_yearly_state_collection(
    source: xr.Dataset,
    output_path: str,
    state_variables: tuple[str, ...],
    config: PackedStateZarrConfig,
) -> None:
    years = config.years if config.years is not None else _available_years(source)
    assert years, "no years selected for packing"

    years_path = Path(output_path) / "years"
    years_path.mkdir(parents=True, exist_ok=True)
    for year in years:
        year_dataset = _select_year(source, int(year))
        assert year_dataset.sizes.get(TIME_COORDINATE, 0), (
            f"source dataset has no time steps for year {year}"
        )
        packed_state = _packed_state_dataset(year_dataset, state_variables, config)
        year_output_path = years_path / f"{int(year)}.zarr"
        logger.info("writing %s", year_output_path)
        _write_zarr(packed_state, str(year_output_path))


def _available_years(dataset: xr.Dataset) -> tuple[int, ...]:
    assert TIME_COORDINATE in dataset.coords, "source dataset has no time coordinate"
    time_values = np.asarray(dataset[TIME_COORDINATE].values, dtype="datetime64[ns]")
    years = time_values.astype("datetime64[Y]").astype(np.int64) + 1970
    return tuple(int(year) for year in np.unique(years))


def _select_year(dataset: xr.Dataset, year: int) -> xr.Dataset:
    start_time = np.datetime64(f"{year:04d}-01-01T00:00:00", "ns")
    stop_time = np.datetime64(f"{year + 1:04d}-01-01T00:00:00", "ns")
    time_values = np.asarray(dataset[TIME_COORDINATE].values, dtype="datetime64[ns]")
    mask = (time_values >= start_time) & (time_values < stop_time)
    return dataset.isel({TIME_COORDINATE: np.nonzero(mask)[0]})


def _packed_state_dataset(
    source: xr.Dataset,
    state_variables: tuple[str, ...],
    config: PackedStateZarrConfig,
) -> xr.Dataset:
    packed_state = _pack_variables(
        source,
        state_variables,
        channel_coordinate=CHANNEL_COORDINATE,
        requires_time=True,
    )
    packed_state = packed_state.chunk(_output_chunks(packed_state, config))
    _clear_encoding(packed_state)
    return xr.Dataset(
        {STATE_VARIABLE: packed_state},
        attrs=_dataset_attrs(config),
    )


def _packed_constants_dataset(
    source: xr.Dataset,
    constant_variables: tuple[str, ...],
    config: PackedStateZarrConfig,
) -> xr.Dataset:
    packed_constants = _pack_variables(
        source,
        constant_variables,
        channel_coordinate=CONSTANT_CHANNEL_COORDINATE,
        requires_time=False,
    )
    packed_constants = packed_constants.chunk(_output_chunks(packed_constants, config))
    _clear_encoding(packed_constants)
    return xr.Dataset(
        {CONSTANTS_VARIABLE: packed_constants},
        attrs=_dataset_attrs(config),
    )


def _dataset_attrs(config: PackedStateZarrConfig) -> dict[str, str]:
    return {
        "dynamaxx_schema": PACKED_SCHEMA_VERSION,
        "source_path": config.source_path,
    }


def _pack_variables(
    source: xr.Dataset,
    variable_names: tuple[str, ...],
    *,
    channel_coordinate: str,
    requires_time: bool,
) -> xr.DataArray:
    arrays = []
    channel_names = []
    for variable_name in variable_names:
        data_array = source[variable_name]
        _validate_packable_variable(
            variable_name,
            data_array,
            requires_time=requires_time,
        )
        vertical_dimensions = _vertical_dimensions(data_array, requires_time)
        if vertical_dimensions:
            vertical_dimension = vertical_dimensions[0]
            vertical_values = _coordinate_values(data_array, vertical_dimension)
            for vertical_index, vertical_value in enumerate(vertical_values):
                arrays.append(
                    _spatial_array(
                        data_array.isel({vertical_dimension: vertical_index}),
                        requires_time=requires_time,
                    )
                )
                channel_names.append(_channel_name(variable_name, vertical_value))
        else:
            arrays.append(_spatial_array(data_array, requires_time=requires_time))
            channel_names.append(variable_name)

    channel = xr.IndexVariable(channel_coordinate, np.asarray(channel_names, dtype=str))
    packed = xr.concat(arrays, dim=channel)
    target_dimensions = (
        (TIME_COORDINATE, channel_coordinate, LONGITUDE_COORDINATE, LATITUDE_COORDINATE)
        if requires_time
        else (channel_coordinate, LONGITUDE_COORDINATE, LATITUDE_COORDINATE)
    )
    return packed.transpose(*target_dimensions)


def _validate_packable_variable(
    variable_name: str,
    data_array: xr.DataArray,
    *,
    requires_time: bool,
) -> None:
    if requires_time:
        assert TIME_COORDINATE in data_array.dims, (
            f"{variable_name!r} has no time dimension"
        )
    else:
        assert TIME_COORDINATE not in data_array.dims, (
            f"{variable_name!r} is time-varying and cannot be packed as a constant"
        )
    assert LONGITUDE_COORDINATE in data_array.dims, (
        f"{variable_name!r} has no longitude dimension"
    )
    assert LATITUDE_COORDINATE in data_array.dims, (
        f"{variable_name!r} has no latitude dimension"
    )
    vertical_dimensions = _vertical_dimensions(data_array, requires_time)
    assert len(vertical_dimensions) <= 1, (
        f"{variable_name!r} has too many non-spatial dimensions: {vertical_dimensions}"
    )


def _vertical_dimensions(
    data_array: xr.DataArray,
    requires_time: bool,
) -> tuple[str, ...]:
    base_dimensions = {LONGITUDE_COORDINATE, LATITUDE_COORDINATE}
    if requires_time:
        base_dimensions.add(TIME_COORDINATE)
    return tuple(
        dimension for dimension in data_array.dims if dimension not in base_dimensions
    )


def _spatial_array(data_array: xr.DataArray, *, requires_time: bool) -> xr.DataArray:
    target_dimensions = (
        (TIME_COORDINATE, LONGITUDE_COORDINATE, LATITUDE_COORDINATE)
        if requires_time
        else (LONGITUDE_COORDINATE, LATITUDE_COORDINATE)
    )
    return data_array.transpose(*target_dimensions).reset_coords(drop=True)


def _coordinate_values(data_array: xr.DataArray, dimension: str) -> np.ndarray:
    if dimension in data_array.coords:
        return np.asarray(data_array[dimension].values)
    return np.arange(data_array.sizes[dimension])


def _channel_name(variable_name: str, vertical_value: Any) -> str:
    if np.issubdtype(np.asarray(vertical_value).dtype, np.number):
        value = float(vertical_value)
        suffix = str(int(value)) if value.is_integer() else f"{value:g}"
    else:
        suffix = str(vertical_value)
    return f"{variable_name}_{suffix}"


def _output_chunks(
    data_array: xr.DataArray,
    config: PackedStateZarrConfig,
) -> dict[str, int]:
    chunk_sizes: dict[str, int | None] = {
        TIME_COORDINATE: config.time_chunk_size,
        CHANNEL_COORDINATE: config.channel_chunk_size,
        CONSTANT_CHANNEL_COORDINATE: config.channel_chunk_size,
        LONGITUDE_COORDINATE: config.longitude_chunk_size,
        LATITUDE_COORDINATE: config.latitude_chunk_size,
    }
    chunks = {}
    for dimension in data_array.dims:
        requested_size = chunk_sizes.get(dimension)
        dimension_size = int(data_array.sizes[dimension])
        chunks[dimension] = min(requested_size or dimension_size, dimension_size)
    return chunks


def _without_zarr_suffix(path: str) -> str:
    return path[: -len(".zarr")] if path.endswith(".zarr") else path


def _clear_encoding(data_array: xr.DataArray) -> None:
    data_array.encoding.clear()
    for coordinate in data_array.coords.values():
        coordinate.encoding.clear()


def _prepare_output_path(output_path: str, *, overwrite: bool) -> None:
    if "://" in output_path:
        return
    path = Path(output_path)
    if not path.exists():
        return
    if not overwrite:
        raise FileExistsError(
            f"{path} already exists; pass overwrite=True to replace it"
        )
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _write_zarr(dataset: xr.Dataset, output_path: str) -> None:
    dataset.to_zarr(output_path, mode="w", consolidated=True)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the packed WeatherBench2 state Zarr converter."""
    args = _parser().parse_args(argv)
    _configure_logging()
    pack_weatherbench2_state_zarr(
        PackedStateZarrConfig(
            source_path=args.source,
            output_path=args.output,
            state_variables=tuple(args.state_variable) if args.state_variable else None,
            constant_variables=tuple(args.constant_variable)
            if args.constant_variable
            else None,
            years=tuple(args.year) if args.year else None,
            start_time=args.start,
            stop_time=args.stop,
            overwrite=args.overwrite,
            split_by_year=not args.single_store,
        )
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="packed_state_zarr.py",
        description=(
            "Pack WeatherBench2-style variables into dynamaxx state Zarr stores."
        ),
    )
    parser.add_argument("source", help="input WeatherBench2-compatible Zarr path")
    parser.add_argument("output", help="output collection directory or Zarr path")
    parser.add_argument(
        "--state-variable",
        action="append",
        default=[],
        help="time-varying variable to pack; repeat to control channel order",
    )
    parser.add_argument(
        "--constant-variable",
        action="append",
        default=[],
        help="constant variable to pack; repeat to control channel order",
    )
    parser.add_argument(
        "--year",
        action="append",
        type=int,
        default=[],
        help="year to write; repeat for multiple years",
    )
    parser.add_argument("--start", help="inclusive start time for source selection")
    parser.add_argument("--stop", help="inclusive stop time for source selection")
    parser.add_argument(
        "--single-store",
        action="store_true",
        help="write one state Zarr instead of a yearly collection",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace an existing local output path",
    )
    return parser


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


if __name__ == "__main__":
    raise SystemExit(main())
