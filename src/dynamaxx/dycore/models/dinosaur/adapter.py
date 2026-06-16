# Copyright 2026 dynamaxx

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.dinosaur import (
    coordinate_systems,
    primitive_equations,
    scales,
    sigma_coordinates,
    spherical_harmonic,
    time_integration,
    units,
    vertical_interpolation,
)
from dynamaxx.dycore.models.dinosaur.channels import (
    GEOPOTENTIAL_VARIABLE,
    MEAN_SEA_LEVEL_PRESSURE_VARIABLE,
    SPECIFIC_HUMIDITY_VARIABLE,
    SURFACE_PRESSURE_VARIABLE,
    TEMPERATURE_VARIABLE,
    TEN_METER_U_WIND_VARIABLE,
    TEN_METER_V_WIND_VARIABLE,
    TWO_METER_TEMPERATURE_VARIABLE,
    U_WIND_VARIABLE,
    V_WIND_VARIABLE,
    has_pressure_level_stack,
    infer_dinosaur_pressure_levels,
    split_pressure_level_channel,
    supported_output_variables,
)
from dynamaxx.dycore.models.dinosaur.coordinates import grid_metadata
from dynamaxx.weather import ForecastInput, WeatherState

DEFAULT_INNER_STEP_SECONDS = 900.0
DEFAULT_SPECTRAL_WAVENUMBERS = 80
_FINITE_SIGMA_TO_PRESSURE_INTERPOLATE = (
    vertical_interpolation.vectorize_vertical_interpolation(
        vertical_interpolation.linear_interp_with_nearest_extrap
    )
)


@dataclass(frozen=True)
class DinosaurPrimitiveEquationsDycoreModel:
    """Dinosaur primitive-equation dycore adapter for packed WeatherState data."""

    name: str = "dinosaur"
    inner_step_seconds: float = DEFAULT_INNER_STEP_SECONDS
    spectral_wavenumbers: int | None = DEFAULT_SPECTRAL_WAVENUMBERS
    reference_temperature_kelvin: float = 250.0
    output_variables: tuple[str, ...] | None = None
    include_vertical_advection: bool = True
    use_humidity_in_dynamics: bool = False
    apply_spectral_filter: bool = True
    horizontal_diffusion_order: int = 2
    horizontal_diffusion_tau_seconds: float | None = None
    jit_forecast: bool = True

    def forecast(self, forecast_input: ForecastInput) -> WeatherState:
        """Run Dinosaur primitive equations and return supported WeatherState channels."""
        assert forecast_input.lead_steps
        assert all(lead_step >= 0 for lead_step in forecast_input.lead_steps)

        pressure_levels_hpa = infer_dinosaur_pressure_levels(
            forecast_input.initial_state.variables
        )
        grid = grid_metadata(
            longitude=forecast_input.longitude,
            latitude=forecast_input.latitude,
            layer_count=len(pressure_levels_hpa),
            spectral_wavenumbers=self.spectral_wavenumbers,
        )
        physics_specs = units.SimUnits.from_si()
        reference_temperature = _reference_temperature(
            layer_count=len(pressure_levels_hpa),
            temperature_kelvin=self.reference_temperature_kelvin,
        )
        has_humidity = has_pressure_level_stack(
            forecast_input.initial_state.variables,
            SPECIFIC_HUMIDITY_VARIABLE,
            pressure_levels_hpa,
        )
        output_variables = supported_output_variables(
            forecast_input.initial_state.variables,
            pressure_levels_hpa=pressure_levels_hpa,
            has_humidity=has_humidity,
            requested_variables=self.output_variables,
        )

        inner_steps = _inner_steps_per_forecast_step(
            forecast_input.step_seconds,
            self.inner_step_seconds,
        )
        trajectory_fn = self._trajectory_function(
            coords=grid.coords,
            physics_specs=physics_specs,
            reference_temperature=reference_temperature,
            inner_steps=inner_steps,
            output_count=max(forecast_input.lead_steps) + 1,
            use_humidity_in_dynamics=has_humidity and self.use_humidity_in_dynamics,
        )

        forecasts = []
        for initial_index in range(forecast_input.initial_times.size):
            single_state = WeatherState(
                values=forecast_input.initial_state.values[initial_index],
                variables=forecast_input.initial_state.variables,
            )
            dinosaur_state = weather_state_to_dinosaur_state(
                single_state,
                coords=grid.coords,
                pressure_levels_hpa=pressure_levels_hpa,
                latitude_reversed=grid.latitude_reversed,
                physics_specs=physics_specs,
                reference_temperature=reference_temperature,
                include_humidity=has_humidity,
            )
            _, trajectory = trajectory_fn(dinosaur_state)
            trajectory_state = dinosaur_state_to_weather_state(
                trajectory,
                coords=grid.coords,
                pressure_levels_hpa=pressure_levels_hpa,
                latitude_reversed=grid.latitude_reversed,
                physics_specs=physics_specs,
                reference_temperature=reference_temperature,
                output_variables=output_variables,
            )
            lead_indices = jnp.asarray(forecast_input.lead_steps, dtype=jnp.int32)
            forecasts.append(jnp.take(trajectory_state.values, lead_indices, axis=0))

        return WeatherState(
            values=jnp.stack(forecasts, axis=1),
            variables=output_variables,
        )

    def _trajectory_function(
        self,
        *,
        coords: coordinate_systems.CoordinateSystem,
        physics_specs: Any,
        reference_temperature: np.ndarray,
        inner_steps: int,
        output_count: int,
        use_humidity_in_dynamics: bool,
    ):
        orography = jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32)
        equation = _primitive_equation(
            reference_temperature=reference_temperature,
            orography=orography,
            coords=coords,
            physics_specs=physics_specs,
            include_vertical_advection=self.include_vertical_advection,
            humidity_key=(
                SPECIFIC_HUMIDITY_VARIABLE if use_humidity_in_dynamics else None
            ),
        )
        step_seconds = _nondimensionalize_seconds(
            physics_specs,
            self.inner_step_seconds,
        )
        step_fn = time_integration.imex_rk_sil3(equation, time_step=step_seconds)
        if self.apply_spectral_filter:
            step_fn = time_integration.step_with_filters(
                step_fn,
                [
                    _horizontal_diffusion_step_filter(
                        coords=coords,
                        physics_specs=physics_specs,
                        step_seconds=step_seconds,
                        tau_seconds=self.horizontal_diffusion_tau_seconds,
                        order=self.horizontal_diffusion_order,
                    )
                ],
            )
        trajectory_fn = time_integration.trajectory_from_step(
            step_fn,
            outer_steps=output_count,
            inner_steps=inner_steps,
            start_with_input=True,
        )
        return jax.jit(trajectory_fn) if self.jit_forecast else trajectory_fn


def default_dinosaur_dycore_model() -> DinosaurPrimitiveEquationsDycoreModel:
    """Return the default Dinosaur primitive-equation dycore model."""
    return DinosaurPrimitiveEquationsDycoreModel()


def weather_state_to_dinosaur_state(
    state: WeatherState,
    *,
    coords: coordinate_systems.CoordinateSystem,
    pressure_levels_hpa: tuple[int, ...],
    latitude_reversed: bool,
    physics_specs: Any,
    reference_temperature: np.ndarray,
    include_humidity: bool,
) -> Any:
    """Convert one packed WeatherState initialization into Dinosaur state."""
    temperature = _stack_pressure_level_channels(
        state,
        TEMPERATURE_VARIABLE,
        pressure_levels_hpa,
    )
    u_wind = _stack_pressure_level_channels(state, U_WIND_VARIABLE, pressure_levels_hpa)
    v_wind = _stack_pressure_level_channels(state, V_WIND_VARIABLE, pressure_levels_hpa)

    temperature = _to_dinosaur_latitude_order(temperature, latitude_reversed)
    u_wind = _to_dinosaur_latitude_order(u_wind, latitude_reversed)
    v_wind = _to_dinosaur_latitude_order(v_wind, latitude_reversed)
    surface_pressure = _surface_pressure_values(state)
    surface_pressure = _to_dinosaur_latitude_order(surface_pressure, latitude_reversed)
    surface_pressure = jnp.maximum(surface_pressure, 1.0)

    temperature = temperature * _unit_factor(physics_specs, "kelvin")
    u_wind = u_wind * _unit_factor(physics_specs, "meter / second")
    v_wind = v_wind * _unit_factor(physics_specs, "meter / second")

    sigma_coords = cast(sigma_coordinates.SigmaCoordinates, coords.vertical)
    pressure_coords = _pressure_coordinates(pressure_levels_hpa)
    surface_pressure_hpa = surface_pressure / 100.0
    nodal_inputs = {
        TEMPERATURE_VARIABLE: temperature,
        U_WIND_VARIABLE: u_wind,
        V_WIND_VARIABLE: v_wind,
    }
    if include_humidity:
        humidity = _stack_pressure_level_channels(
            state,
            SPECIFIC_HUMIDITY_VARIABLE,
            pressure_levels_hpa,
        )
        humidity = _to_dinosaur_latitude_order(humidity, latitude_reversed)
        nodal_inputs[SPECIFIC_HUMIDITY_VARIABLE] = humidity
    nodal_inputs = vertical_interpolation.interp_pressure_to_sigma(
        nodal_inputs,
        pressure_coords,
        sigma_coords,
        surface_pressure_hpa,
    )
    temperature = nodal_inputs[TEMPERATURE_VARIABLE]
    u_wind = nodal_inputs[U_WIND_VARIABLE]
    v_wind = nodal_inputs[V_WIND_VARIABLE]

    vorticity, divergence = spherical_harmonic.uv_nodal_to_vor_div_modal(
        coords.horizontal,
        u_wind,
        v_wind,
    )
    temperature_variation = coords.horizontal.to_modal(
        temperature - reference_temperature[:, np.newaxis, np.newaxis]
    )
    pressure_factor = _unit_factor(physics_specs, "pascal")
    log_surface_pressure = coords.horizontal.to_modal(
        jnp.log(surface_pressure * pressure_factor)
    )[jnp.newaxis]
    tracers = {}
    if include_humidity:
        tracers[SPECIFIC_HUMIDITY_VARIABLE] = coords.horizontal.to_modal(
            nodal_inputs[SPECIFIC_HUMIDITY_VARIABLE]
        )

    dinosaur_state = _primitive_equation_state(
        vorticity=vorticity,
        divergence=divergence,
        temperature_variation=temperature_variation,
        log_surface_pressure=log_surface_pressure,
        tracers=tracers,
    )
    return coords.horizontal.clip_wavenumbers(dinosaur_state)


def dinosaur_state_to_weather_state(
    trajectory: Any,
    *,
    coords: coordinate_systems.CoordinateSystem,
    pressure_levels_hpa: tuple[int, ...],
    latitude_reversed: bool,
    physics_specs: Any,
    reference_temperature: np.ndarray,
    output_variables: tuple[str, ...],
) -> WeatherState:
    """Convert a Dinosaur trajectory into packed WeatherState channels."""
    temperature = (
        coords.horizontal.to_nodal(trajectory.temperature_variation)
        + reference_temperature[np.newaxis, :, np.newaxis, np.newaxis]
    )
    u_wind, v_wind = spherical_harmonic.vor_div_to_uv_nodal(
        coords.horizontal,
        trajectory.vorticity,
        trajectory.divergence,
    )
    surface_pressure = jnp.exp(
        coords.horizontal.to_nodal(trajectory.log_surface_pressure)[:, 0]
    )
    humidity = None
    if SPECIFIC_HUMIDITY_VARIABLE in trajectory.tracers:
        humidity = coords.horizontal.to_nodal(
            trajectory.tracers[SPECIFIC_HUMIDITY_VARIABLE]
        )
    geopotential = primitive_equations.get_geopotential_on_sigma(
        temperature,
        specific_humidity=humidity,
        nodal_orography=jnp.zeros(coords.horizontal.nodal_shape, dtype=jnp.float32),
        sigma=cast(sigma_coordinates.SigmaCoordinates, coords.vertical),
        gravity_acceleration=physics_specs.g,
        ideal_gas_constant=physics_specs.R,
        water_vapor_gas_constant=physics_specs.R_vapor,
    )

    pressure_factor = _unit_factor(physics_specs, "pascal")
    surface_pressure_pa = surface_pressure / pressure_factor
    surface_pressure_hpa = surface_pressure_pa / 100.0
    sigma_fields = {
        TEMPERATURE_VARIABLE: temperature,
        U_WIND_VARIABLE: u_wind,
        V_WIND_VARIABLE: v_wind,
        GEOPOTENTIAL_VARIABLE: geopotential,
    }
    if humidity is not None:
        sigma_fields[SPECIFIC_HUMIDITY_VARIABLE] = humidity
    pressure_fields = _interp_sigma_to_pressure_by_time(
        sigma_fields,
        _pressure_coordinates(pressure_levels_hpa),
        cast(sigma_coordinates.SigmaCoordinates, coords.vertical),
        surface_pressure_hpa,
    )

    temperature = temperature / _unit_factor(physics_specs, "kelvin")
    u_wind = u_wind / _unit_factor(physics_specs, "meter / second")
    v_wind = v_wind / _unit_factor(physics_specs, "meter / second")
    surface_pressure = surface_pressure_pa
    geopotential = geopotential / _unit_factor(
        physics_specs,
        "meter ** 2 / second ** 2",
    )
    pressure_fields = {
        TEMPERATURE_VARIABLE: pressure_fields[TEMPERATURE_VARIABLE]
        / _unit_factor(physics_specs, "kelvin"),
        U_WIND_VARIABLE: pressure_fields[U_WIND_VARIABLE]
        / _unit_factor(physics_specs, "meter / second"),
        V_WIND_VARIABLE: pressure_fields[V_WIND_VARIABLE]
        / _unit_factor(physics_specs, "meter / second"),
        GEOPOTENTIAL_VARIABLE: pressure_fields[GEOPOTENTIAL_VARIABLE]
        / _unit_factor(physics_specs, "meter ** 2 / second ** 2"),
        **(
            {SPECIFIC_HUMIDITY_VARIABLE: pressure_fields[SPECIFIC_HUMIDITY_VARIABLE]}
            if SPECIFIC_HUMIDITY_VARIABLE in pressure_fields
            else {}
        ),
    }

    level_to_index = {
        pressure_level: level_index
        for level_index, pressure_level in enumerate(pressure_levels_hpa)
    }

    fields = []
    for channel in output_variables:
        variable_name, pressure_level = split_pressure_level_channel(channel)
        if variable_name == TEMPERATURE_VARIABLE and pressure_level is not None:
            field = pressure_fields[TEMPERATURE_VARIABLE][
                :, level_to_index[pressure_level]
            ]
        elif variable_name == U_WIND_VARIABLE and pressure_level is not None:
            field = pressure_fields[U_WIND_VARIABLE][:, level_to_index[pressure_level]]
        elif variable_name == V_WIND_VARIABLE and pressure_level is not None:
            field = pressure_fields[V_WIND_VARIABLE][:, level_to_index[pressure_level]]
        elif variable_name == GEOPOTENTIAL_VARIABLE and pressure_level is not None:
            field = pressure_fields[GEOPOTENTIAL_VARIABLE][
                :, level_to_index[pressure_level]
            ]
        elif variable_name == SPECIFIC_HUMIDITY_VARIABLE and pressure_level is not None:
            assert SPECIFIC_HUMIDITY_VARIABLE in pressure_fields
            field = pressure_fields[SPECIFIC_HUMIDITY_VARIABLE][
                :, level_to_index[pressure_level]
            ]
        elif channel == TWO_METER_TEMPERATURE_VARIABLE:
            field = temperature[:, -1]
        elif channel == TEN_METER_U_WIND_VARIABLE:
            field = u_wind[:, -1]
        elif channel == TEN_METER_V_WIND_VARIABLE:
            field = v_wind[:, -1]
        elif channel in (SURFACE_PRESSURE_VARIABLE, MEAN_SEA_LEVEL_PRESSURE_VARIABLE):
            field = surface_pressure
        else:
            raise AssertionError(f"Dinosaur cannot output {channel}")
        fields.append(_from_dinosaur_latitude_order(field, latitude_reversed))

    return WeatherState(
        values=jnp.stack(fields, axis=1),
        variables=output_variables,
    )


def _reference_temperature(
    *,
    layer_count: int,
    temperature_kelvin: float,
) -> np.ndarray:
    reference_temperature = np.full(
        (layer_count,),
        float(temperature_kelvin),
        dtype=np.float32,
    )
    assert np.all(np.isfinite(reference_temperature))
    return reference_temperature


def _inner_steps_per_forecast_step(
    step_seconds: float,
    inner_step_seconds: float,
) -> int:
    inner_steps = int(round(float(step_seconds) / float(inner_step_seconds)))
    assert inner_steps >= 1
    assert np.isclose(inner_steps * inner_step_seconds, step_seconds)
    return inner_steps


def _stack_pressure_level_channels(
    state: WeatherState,
    variable_name: str,
    pressure_levels_hpa: tuple[int, ...],
) -> jax.Array:
    channels = tuple(
        f"{variable_name}_{pressure_level}" for pressure_level in pressure_levels_hpa
    )
    indices = jnp.asarray(state.variable_indices(channels), dtype=jnp.int32)
    return jnp.take(state.values, indices, axis=-3)


def _surface_pressure_values(state: WeatherState) -> jax.Array:
    for channel in (SURFACE_PRESSURE_VARIABLE, MEAN_SEA_LEVEL_PRESSURE_VARIABLE):
        if channel in state.variables:
            return state.select((channel,)).values[0]
    longitude_count, latitude_count = state.spatial_shape
    return jnp.full(
        (longitude_count, latitude_count), 100000.0, dtype=state.values.dtype
    )


def _to_dinosaur_latitude_order(
    values: jax.Array, latitude_reversed: bool
) -> jax.Array:
    if latitude_reversed:
        return values[..., ::-1]
    return values


def _from_dinosaur_latitude_order(
    values: jax.Array, latitude_reversed: bool
) -> jax.Array:
    if latitude_reversed:
        return values[..., ::-1]
    return values


def _primitive_equation(
    *,
    reference_temperature: np.ndarray,
    orography: jax.Array,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    include_vertical_advection: bool,
    humidity_key: str | None,
) -> Any:
    """Build the Dinosaur primitive-equation object for this adapter."""
    if humidity_key is None:
        return primitive_equations.PrimitiveEquations(
            reference_temperature,
            orography,
            coords,
            physics_specs,
            include_vertical_advection=include_vertical_advection,
        )
    return primitive_equations.PrimitiveEquationsSigma(
        reference_temperature,
        orography,
        coords,
        physics_specs,
        include_vertical_advection=include_vertical_advection,
        humidity_key=humidity_key,
    )


def _horizontal_diffusion_step_filter(
    *,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    step_seconds: float,
    tau_seconds: float | None,
    order: int,
) -> Any:
    """Return the horizontal diffusion step filter used by Dinosaur examples."""
    if tau_seconds is None:
        resolution_factor = coords.horizontal.latitude_nodes / 128.0
        tau_hours = 8.6 / (2.4 ** np.log2(resolution_factor))
        tau_seconds = tau_hours * 3600.0
    tau = _nondimensionalize_seconds(physics_specs, tau_seconds)
    return time_integration.horizontal_diffusion_step_filter(
        coords.horizontal,
        dt=step_seconds,
        tau=tau,
        order=order,
    )


def _nondimensionalize_seconds(physics_specs: Any, seconds: float) -> float:
    """Convert SI seconds to Dinosaur nondimensional time."""
    unit_registry = cast(Any, scales.units)
    quantity = unit_registry.Quantity(float(seconds), "second")
    return float(physics_specs.nondimensionalize(quantity))


def _pressure_coordinates(
    pressure_levels_hpa: tuple[int, ...],
) -> vertical_interpolation.PressureCoordinates:
    """Return Dinosaur pressure coordinates in hPa, ordered top to bottom."""
    return vertical_interpolation.PressureCoordinates(
        np.asarray(pressure_levels_hpa, dtype=np.float32)
    )


def _interp_sigma_to_pressure_by_time(
    fields: dict[str, jax.Array],
    pressure_coords: vertical_interpolation.PressureCoordinates,
    sigma_coords: sigma_coordinates.SigmaCoordinates,
    surface_pressure_hpa: jax.Array,
) -> dict[str, jax.Array]:
    """Interpolate sigma fields to pressure levels for each trajectory time."""
    if surface_pressure_hpa.ndim == 2:
        return vertical_interpolation.interp_sigma_to_pressure(
            fields,
            pressure_coords,
            sigma_coords,
            surface_pressure_hpa,
            interpolate_fn=_FINITE_SIGMA_TO_PRESSURE_INTERPOLATE,
        )

    def interpolate_one_time(single_fields, single_surface_pressure):
        return vertical_interpolation.interp_sigma_to_pressure(
            single_fields,
            pressure_coords,
            sigma_coords,
            single_surface_pressure,
            interpolate_fn=_FINITE_SIGMA_TO_PRESSURE_INTERPOLATE,
        )

    return jax.vmap(interpolate_one_time)(fields, surface_pressure_hpa)


def _primitive_equation_state(**kwargs: Any) -> Any:
    state_cls = getattr(primitive_equations, "State")
    return state_cls(**kwargs)


def _unit_factor(physics_specs: Any, unit_name: str) -> float:
    unit_registry = cast(Any, scales.units)
    unit = unit_registry.Quantity(1.0, unit_name)
    return float(physics_specs.nondimensionalize(unit))
