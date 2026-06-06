# Copyright 2026 dynamaxx

from __future__ import annotations

import functools
import re
from collections.abc import Sequence

TEMPERATURE_VARIABLE = "temperature"
U_WIND_VARIABLE = "u_component_of_wind"
V_WIND_VARIABLE = "v_component_of_wind"
GEOPOTENTIAL_VARIABLE = "geopotential"
SPECIFIC_HUMIDITY_VARIABLE = "specific_humidity"
SURFACE_PRESSURE_VARIABLE = "surface_pressure"
MEAN_SEA_LEVEL_PRESSURE_VARIABLE = "mean_sea_level_pressure"
TWO_METER_TEMPERATURE_VARIABLE = "2m_temperature"
TEN_METER_U_WIND_VARIABLE = "10m_u_component_of_wind"
TEN_METER_V_WIND_VARIABLE = "10m_v_component_of_wind"

PRESSURE_LEVELS_HPA = frozenset(
    {
        1,
        2,
        3,
        5,
        7,
        10,
        20,
        30,
        50,
        70,
        100,
        125,
        150,
        175,
        200,
        225,
        250,
        300,
        350,
        400,
        450,
        500,
        550,
        600,
        650,
        700,
        750,
        775,
        800,
        825,
        850,
        875,
        900,
        925,
        950,
        975,
        1000,
    }
)


def infer_dinosaur_pressure_levels(variables: Sequence[str]) -> tuple[int, ...]:
    """Infer pressure levels that have temperature and horizontal wind channels."""
    level_sets = [
        _pressure_levels_for_variable(variables, variable_name)
        for variable_name in (
            TEMPERATURE_VARIABLE,
            U_WIND_VARIABLE,
            V_WIND_VARIABLE,
        )
    ]
    pressure_levels = tuple(sorted(functools.reduce(set.intersection, level_sets)))
    assert pressure_levels, (
        "Dinosaur requires pressure-level temperature, u-wind, and v-wind channels"
    )
    return pressure_levels


def supported_output_variables(
    input_variables: Sequence[str],
    *,
    pressure_levels_hpa: tuple[int, ...],
    has_humidity: bool,
    requested_variables: Sequence[str] | None,
) -> tuple[str, ...]:
    """Return supported output channels in stable WeatherState order."""
    if requested_variables is not None:
        output_variables = tuple(map(str, requested_variables))
        unsupported_variables = [
            variable
            for variable in output_variables
            if not can_output_variable(
                variable,
                pressure_levels_hpa=pressure_levels_hpa,
                has_humidity=has_humidity,
            )
        ]
        assert not unsupported_variables, (
            f"Dinosaur cannot output variables {unsupported_variables}"
        )
        return output_variables

    output_variables = tuple(
        variable
        for variable in map(str, input_variables)
        if can_output_variable(
            variable,
            pressure_levels_hpa=pressure_levels_hpa,
            has_humidity=has_humidity,
        )
    )
    assert output_variables, "Dinosaur found no supported output variables"
    return output_variables


def has_pressure_level_stack(
    variables: Sequence[str],
    variable_name: str,
    pressure_levels_hpa: tuple[int, ...],
) -> bool:
    """Return whether all model pressure levels exist for one variable."""
    return set(pressure_levels_hpa).issubset(
        _pressure_levels_for_variable(variables, variable_name)
    )


def can_output_variable(
    channel: str,
    *,
    pressure_levels_hpa: tuple[int, ...],
    has_humidity: bool,
) -> bool:
    """Return whether the Dinosaur adapter can emit a packed channel."""
    variable_name, pressure_level = split_pressure_level_channel(channel)
    pressure_level_outputs = {
        TEMPERATURE_VARIABLE,
        U_WIND_VARIABLE,
        V_WIND_VARIABLE,
        GEOPOTENTIAL_VARIABLE,
    }
    if has_humidity:
        pressure_level_outputs.add(SPECIFIC_HUMIDITY_VARIABLE)
    if pressure_level is not None:
        return (
            variable_name in pressure_level_outputs
            and pressure_level in pressure_levels_hpa
        )
    return channel in {
        SURFACE_PRESSURE_VARIABLE,
        MEAN_SEA_LEVEL_PRESSURE_VARIABLE,
        TWO_METER_TEMPERATURE_VARIABLE,
        TEN_METER_U_WIND_VARIABLE,
        TEN_METER_V_WIND_VARIABLE,
    }


def split_pressure_level_channel(channel: str) -> tuple[str, int | None]:
    """Split packed WeatherBench pressure-level channel names."""
    match = re.match(r"^(?P<variable>.+)_(?P<level>[0-9]+)$", str(channel))
    if match is None:
        return str(channel), None
    pressure_level = int(match.group("level"))
    if pressure_level not in PRESSURE_LEVELS_HPA:
        return str(channel), None
    return match.group("variable"), pressure_level


def _pressure_levels_for_variable(
    variables: Sequence[str],
    variable_name: str,
) -> set[int]:
    pressure_levels = set()
    for channel in variables:
        channel_variable, pressure_level = split_pressure_level_channel(str(channel))
        if channel_variable == variable_name and pressure_level is not None:
            pressure_levels.add(pressure_level)
    return pressure_levels
