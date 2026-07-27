# Copyright 2026 dynamaxx

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import partial
from typing import Any, cast

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.dinosaur import (
    coordinate_systems,
    held_suarez,
    primitive_equations,
    radiation,
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


@jax.custom_jvp
def _sqrt_nonnegative_with_finite_gradient(value: jax.Array) -> jax.Array:
    """Return ``sqrt(max(value, 0))`` with a finite derivative at zero.

    Physical vector magnitudes are exactly zero at calm grid points.  The
    ordinary square-root derivative is singular there, which can turn a zero
    cotangent into a NaN during reverse-mode differentiation.  The forward
    value remains unchanged while the derivative at nonpositive inputs is
    defined as zero, matching the limiting gradient of a vector norm at the
    origin used by these closures.
    """
    return jnp.sqrt(jnp.maximum(value, 0.0))


@_sqrt_nonnegative_with_finite_gradient.defjvp
def _sqrt_nonnegative_with_finite_gradient_jvp(
    primals: tuple[jax.Array],
    tangents: tuple[jax.Array],
) -> tuple[jax.Array, jax.Array]:
    """Propagate finite tangents through a nonnegative square root."""
    (value,) = primals
    (value_tangent,) = tangents
    result = _sqrt_nonnegative_with_finite_gradient(value)
    positive = value > 0.0
    safe_result = jnp.where(positive, result, jnp.ones_like(result))
    derivative = jnp.where(positive, 0.5 / safe_result, 0.0)
    return result, derivative * value_tangent


DEFAULT_INNER_STEP_SECONDS = 900.0
DEFAULT_SPECTRAL_WAVENUMBERS = 80
DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY = 0.0
DEFAULT_WEAK_HELD_SUAREZ_KA_TIMESCALE_DAYS = 160.0
DEFAULT_WEAK_HELD_SUAREZ_KS_TIMESCALE_DAYS = 16.0
DEFAULT_SEMI_IMPLICIT_OFFCENTERING = 0.05
_ANALYSIS_OFFSET_HELD_SUAREZ_MAX_KELVIN = 20.0
_ANALYSIS_OFFSET_HELD_SUAREZ_MAX_LONGITUDE_WAVENUMBER = 3
_ANALYSIS_OFFSET_HELD_SUAREZ_MAX_TOTAL_WAVENUMBER = 12
_FINITE_SIGMA_TO_PRESSURE_INTERPOLATE = (
    vertical_interpolation.vectorize_vertical_interpolation(
        vertical_interpolation.linear_interp_with_nearest_extrap
    )
)
_NEAR_SURFACE_RESIDUAL_VARIABLES = (
    TWO_METER_TEMPERATURE_VARIABLE,
    TEN_METER_U_WIND_VARIABLE,
)
_STABILITY_AWARE_MIN_RESIDUAL_DECAY_HOURS = 18.0
_STABILITY_AWARE_MAX_RESIDUAL_DECAY_HOURS = 72.0
_STABILITY_AWARE_POTENTIAL_TEMPERATURE_EXPONENT = 2.0 / 7.0
_STABILITY_AWARE_SHEAR_FLOOR_METERS_PER_SECOND = 2.0
_STABILITY_AWARE_TEMPERATURE_RESIDUAL_SCALE_KELVIN = 4.0
_STABILITY_AWARE_WIND_RESIDUAL_SCALE_METERS_PER_SECOND = 4.0
_STABILITY_AWARE_WEAK_FLOW_SCALE_METERS_PER_SECOND = 12.0
_SCALE_SEPARATED_RESIDUAL_LOW_MODE_CUTOFF = 12
_SCALE_SEPARATED_RESIDUAL_TAPER_ZERO_MODE = 20
_SCALE_SEPARATED_RESIDUAL_LOW_DECAY_HOURS = 96.0
_LAND_SEA_MASK_CHANNEL = "land_sea_mask"
_LAND_SEA_SURFACE_TEMPERATURE_OCEAN_DECAY_EXPONENT = 0.5
_LAND_OCEAN_LOW_MODE_T2M_MEMORY_DECAY_HOURS = 360.0
_LAND_OCEAN_LOW_MODE_T2M_MEMORY_RAMP_START_HOURS = 120.0
_LAND_OCEAN_LOW_MODE_T2M_MEMORY_RAMP_FULL_HOURS = 240.0
_LAND_OCEAN_LOW_MODE_T2M_MEMORY_MAX_CORRECTION_KELVIN = 1.5
_OCEAN_BULK_SHF_TRANSFER_COEFFICIENT = 1.0e-3
_OCEAN_BULK_SHF_EXCHANGE_DEPTH_METERS = 10_000.0
_OCEAN_BULK_SHF_MIN_EFOLDING_DAYS = 6.0
_OCEAN_BULK_SHF_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN = 0.05
_LAND_SKIN_RESERVOIR_TRANSFER_COEFFICIENT = 1.5e-3
_LAND_SKIN_RESERVOIR_EXCHANGE_DEPTH_METERS = 50.0
_LAND_SKIN_RESERVOIR_MIN_EFOLDING_HOURS = 6.0
_LAND_SKIN_RESERVOIR_HEAT_CAPACITY_RATIO = 4.0
_LAND_SKIN_RESERVOIR_DEEP_RESTORE_DAYS = 10.0
_LAND_SKIN_RESERVOIR_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN = 0.05
_LAND_SKIN_RESERVOIR_MIN_LAND_FRACTION = 0.01
_LAND_SKIN_RESERVOIR_RAMP_START_HOURS = 120.0
_LAND_SKIN_RESERVOIR_RAMP_FULL_HOURS = 240.0
_LAND_SKIN_RADIATIVE_ABSORBED_SHORTWAVE_FRACTION = 0.7
_STEFAN_BOLTZMANN_CONSTANT_SI = 5.670374419e-8
_SURFACE_LAYER_WIND_MIN_FACTOR = 0.55
_SURFACE_LAYER_WIND_MAX_FACTOR = 1.05
_SURFACE_LAYER_SHEAR_FLOOR_METERS_PER_SECOND = 2.0
_SURFACE_LAYER_REFERENCE_HEIGHT_METERS = 10.0
_SURFACE_LAYER_TEMPERATURE_REFERENCE_HEIGHT_METERS = 2.0
_SURFACE_LAYER_TEMPERATURE_MAX_DEPARTURE_KELVIN = 1.5
_TROPICAL_WTG_FULL_LATITUDE_DEGREES = 12.0
_TROPICAL_WTG_ZERO_LATITUDE_DEGREES = 27.0
_TROPICAL_WTG_SIGMA_ZERO_TOP = 0.20
_TROPICAL_WTG_SIGMA_FULL_TOP = 0.40
_TROPICAL_WTG_SIGMA_FULL_BOTTOM = 0.60
_TROPICAL_WTG_SIGMA_ZERO_BOTTOM = 0.82
_TROPICAL_WTG_LOW_MODE_CUTOFF = 8.0
_TROPICAL_WTG_LOW_MODE_TAPER_ZERO = 16.0
_TROPICAL_WTG_RELAXATION_TIMESCALE_DAYS = 5.0
_TROPICAL_WTG_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN = 0.25
_EKMAN_COUPLED_DRAG_COEFFICIENT = 3.0e-4
_EKMAN_COUPLED_BOUNDARY_LAYER_DEPTH_METERS = 2_000.0
_EKMAN_COUPLED_SECOND_LAYER_FRACTION = 0.35
_EKMAN_CORIOLIS_DEPTH_COEFFICIENT = 1.2
_EKMAN_CORIOLIS_DEPTH_MIN_METERS = 500.0
_EKMAN_CORIOLIS_DEPTH_MAX_METERS = 2_500.0
_EKMAN_COUPLED_MAX_WIND_STEP_INCREMENT_METERS_PER_SECOND = 0.25
_EKMAN_COUPLED_MAX_LOGP_STEP_INCREMENT = 2.0e-5
_EKMAN_COUPLED_LOGP_PER_WIND_STEP_RATIO = 0.08
_EKMAN_COUPLED_PROJECTION_SAFETY_FACTOR = 0.85
_EKMAN_COUPLED_EQUATORIAL_ZERO_LATITUDE_DEGREES = 5.0
_EKMAN_COUPLED_EQUATORIAL_FULL_LATITUDE_DEGREES = 15.0
_GEOPOTENTIAL_AT_SURFACE_CHANNEL = "geopotential_at_surface"
_OROGRAPHIC_LIFT_LOW_MODE_CUTOFF = 12.0
_OROGRAPHIC_LIFT_TAPER_ZERO_MODE = 20.0
_OROGRAPHIC_LIFT_RAMP_FULL_HOURS = 48.0
_OROGRAPHIC_LIFT_SIGMA_ZERO_TOP = 0.35
_OROGRAPHIC_LIFT_SIGMA_FULL_TOP = 0.45
_OROGRAPHIC_LIFT_SIGMA_FULL_BOTTOM = 0.80
_OROGRAPHIC_LIFT_SIGMA_ZERO_BOTTOM = 0.90
_OROGRAPHIC_LIFT_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN = 0.05
_OROGRAPHIC_LIFT_EQUATORIAL_ZERO_LATITUDE_DEGREES = 5.0
_OROGRAPHIC_LIFT_EQUATORIAL_FULL_LATITUDE_DEGREES = 15.0
_OROGRAPHIC_LIFT_WEAK_FLOW_FULL_METERS_PER_SECOND = 2.0
_OROGRAPHIC_LIFT_LOWER_COLUMN_WIND_WEIGHTS = (0.15, 0.30, 0.55)
_TERRAIN_WORK_FORM_DRAG_SLOPE_FULL = 2.0e-3
_TERRAIN_WORK_FORM_DRAG_WORK_FULL_METERS_PER_SECOND = 0.03
_TERRAIN_WORK_FORM_DRAG_MAX_WIND_FRACTION = 0.08
_TERRAIN_WORK_FORM_DRAG_MAX_WIND_STEP_INCREMENT_METERS_PER_SECOND = 0.04
_TERRAIN_WORK_FORM_DRAG_HEAT_RETURN_FRACTION = 0.05
_TERRAIN_WORK_FORM_DRAG_MAX_HEAT_INCREMENT_KELVIN = 0.01
_DRY_AIR_GAS_CONSTANT_SI = float(
    scales.IDEAL_GAS_CONSTANT.to("meter ** 2 / second ** 2 / kelvin").magnitude
)
_GRAVITY_ACCELERATION_SI = float(
    scales.GRAVITY_ACCELERATION.to("meter / second ** 2").magnitude
)
_WATER_VAPOR_GAS_CONSTANT_SI = float(
    scales.IDEAL_GAS_CONSTANT_H20.to("meter ** 2 / second ** 2 / kelvin").magnitude
)
_LandSeaMaskCacheKey = tuple[str, tuple[int, ...], bytes, tuple[int, ...], bytes]
_LAND_SEA_FRACTION_CACHE: dict[_LandSeaMaskCacheKey, jax.Array] = {}
_TerrainHeightCacheKey = tuple[str, tuple[int, ...], bytes, tuple[int, ...], bytes]
_TERRAIN_HEIGHT_CACHE: dict[_TerrainHeightCacheKey, jax.Array] = {}


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
    use_log_pressure_initialization: bool = False
    use_hydrostatic_temperature_initialization: bool = False
    use_layer_mean_hydrostatic_temperature_initialization: bool = False
    apply_spectral_filter: bool = True
    horizontal_diffusion_order: int = 2
    horizontal_diffusion_tau_seconds: float | None = None
    apply_digital_filter_initialization: bool = False
    digital_filter_time_span_seconds: float = 6 * 3600.0
    digital_filter_cutoff_seconds: float = 6 * 3600.0
    apply_weak_held_suarez_relaxation: bool = False
    weak_held_suarez_kf_per_day: float = DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY
    weak_held_suarez_ka_timescale_days: float = (
        DEFAULT_WEAK_HELD_SUAREZ_KA_TIMESCALE_DAYS
    )
    weak_held_suarez_ks_timescale_days: float = (
        DEFAULT_WEAK_HELD_SUAREZ_KS_TIMESCALE_DAYS
    )
    use_analysis_offset_weak_held_suarez_equilibrium: bool = False
    apply_near_surface_residual_correction: bool = False
    near_surface_residual_decay_hours: float = 48.0
    use_stability_aware_near_surface_residual_decay: bool = False
    use_scale_separated_near_surface_residual: bool = False
    use_land_sea_surface_temperature_residual: bool = False
    use_land_ocean_low_mode_t2m_memory: bool = False
    apply_ocean_bulk_sensible_heat_flux: bool = False
    apply_land_skin_reservoir: bool = False
    use_analysis_2m_initialized_land_skin: bool = False
    apply_zero_mean_radiative_land_skin_energy: bool = False
    use_surface_layer_richardson_10m_wind_diagnostic: bool = False
    use_bulk_richardson_2m_temperature_diagnostic: bool = False
    use_pressure_thickness_weighted_ri2m_temperature: bool = False
    use_prognostic_skin_ri2m_lower_boundary: bool = False
    use_ocean_anchor_ri2m_lower_boundary: bool = False
    apply_exact_coriolis_rotation_split: bool = False
    apply_symmetric_exact_coriolis_rotation_split: bool = False
    temperature_tendency_formulation: str = (
        primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_TEMPERATURE
    )
    apply_theta_layer_mean_recentering: bool = False
    use_horizontal_semilagrangian_theta_transport: bool = False
    use_midpoint_semilagrangian_theta_departure: bool = False
    use_dry_static_energy_hsl_transport: bool = False
    use_layer_mass_weighted_dse_hsl_transport: bool = False
    use_pressure_ramped_vertical_dse_increment: bool = False
    apply_anticipated_pv_flux: bool = False
    apply_tropical_wtg_mass_dse_relaxation: bool = False
    apply_coupled_ekman_surface_closure: bool = False
    use_coriolis_scaled_ekman_depth: bool = False
    apply_orographic_lift_theta_tendency: bool = False
    use_depth_weighted_orographic_lift_wind: bool = False
    apply_terrain_work_form_drag_heating: bool = False
    semi_implicit_offcentering: float = 0.0
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
        land_sea_fraction = None
        if (
            self.use_land_sea_surface_temperature_residual
            or self.use_land_ocean_low_mode_t2m_memory
            or self.apply_ocean_bulk_sensible_heat_flux
            or self.apply_land_skin_reservoir
            or self.use_prognostic_skin_ri2m_lower_boundary
            or self.use_ocean_anchor_ri2m_lower_boundary
        ):
            land_sea_fraction = _load_land_sea_fraction_for_grid(
                longitude=forecast_input.longitude,
                latitude=forecast_input.latitude,
                initial_time=forecast_input.initial_times[0],
            )
        ocean_bulk_shf_ocean_weight = None
        if self.apply_ocean_bulk_sensible_heat_flux:
            valid_land_sea_fraction = _valid_land_sea_fraction_or_none(
                land_sea_fraction,
                (forecast_input.longitude.size, forecast_input.latitude.size),
            )
            if valid_land_sea_fraction is not None:
                ocean_bulk_shf_ocean_weight = 1.0 - _to_dinosaur_latitude_order(
                    valid_land_sea_fraction,
                    grid.latitude_reversed,
                )
        land_skin_reservoir_land_weight = None
        if self.apply_land_skin_reservoir:
            valid_land_sea_fraction = _valid_land_sea_fraction_or_none(
                land_sea_fraction,
                (forecast_input.longitude.size, forecast_input.latitude.size),
            )
            if valid_land_sea_fraction is not None:
                land_skin_reservoir_land_weight = _to_dinosaur_latitude_order(
                    valid_land_sea_fraction,
                    grid.latitude_reversed,
                )
        terrain_height_meters = None
        if (
            self.apply_orographic_lift_theta_tendency
            or self.apply_terrain_work_form_drag_heating
        ):
            terrain_height_meters = _load_surface_geopotential_height_for_grid(
                longitude=forecast_input.longitude,
                latitude=forecast_input.latitude,
                initial_time=forecast_input.initial_times[0],
            )
            if terrain_height_meters is not None:
                terrain_height_meters = _to_dinosaur_latitude_order(
                    terrain_height_meters,
                    grid.latitude_reversed,
                )
        radiative_land_skin_reference_time = None
        if self.apply_zero_mean_radiative_land_skin_energy:
            radiative_land_skin_reference_time = _radiative_land_skin_reference_time(
                forecast_input.initial_times
            )

        trajectory_fn = self._trajectory_function(
            coords=grid.coords,
            physics_specs=physics_specs,
            reference_temperature=reference_temperature,
            inner_steps=inner_steps,
            output_count=max(forecast_input.lead_steps) + 1,
            use_humidity_in_dynamics=has_humidity and self.use_humidity_in_dynamics,
            ocean_bulk_shf_ocean_weight=ocean_bulk_shf_ocean_weight,
            land_skin_reservoir_land_weight=land_skin_reservoir_land_weight,
            terrain_height_meters=terrain_height_meters,
            radiative_land_skin_reference_time=(radiative_land_skin_reference_time),
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
                use_log_pressure_initialization=self.use_log_pressure_initialization,
                use_hydrostatic_temperature_initialization=(
                    self.use_hydrostatic_temperature_initialization
                ),
                use_layer_mean_hydrostatic_temperature_initialization=(
                    self.use_layer_mean_hydrostatic_temperature_initialization
                ),
                initialize_sim_time=(
                    self.use_pressure_ramped_vertical_dse_increment
                    or self.apply_orographic_lift_theta_tendency
                    or self.apply_land_skin_reservoir
                ),
            )
            analysis_2m_land_skin_temperature = None
            if self.use_analysis_2m_initialized_land_skin:
                analysis_2m_land_skin_temperature = _analysis_2m_land_skin_temperature(
                    single_state,
                    spatial_shape=grid.coords.horizontal.nodal_shape,
                    latitude_reversed=grid.latitude_reversed,
                    physics_specs=physics_specs,
                )
            radiative_trajectory_arguments: tuple[Any, ...] = ()
            if self.apply_zero_mean_radiative_land_skin_energy:
                radiative_trajectory_arguments = (
                    _radiative_land_skin_initial_time_offset(
                        forecast_input.initial_times[initial_index],
                        reference_time=radiative_land_skin_reference_time,
                        physics_specs=physics_specs,
                    ),
                )
            ocean_bulk_shf_temperature_anchor = None
            if (
                self.apply_ocean_bulk_sensible_heat_flux
                and ocean_bulk_shf_ocean_weight is not None
            ):
                ocean_bulk_shf_temperature_anchor = (
                    _ocean_bulk_sensible_heat_flux_temperature_anchor(
                        single_state,
                        dinosaur_state=dinosaur_state,
                        coords=grid.coords,
                        latitude_reversed=grid.latitude_reversed,
                        physics_specs=physics_specs,
                        reference_temperature=reference_temperature,
                    )
                )
                if self.use_analysis_2m_initialized_land_skin:
                    _, trajectory_output = trajectory_fn(
                        dinosaur_state,
                        ocean_bulk_shf_temperature_anchor,
                        analysis_2m_land_skin_temperature,
                        *radiative_trajectory_arguments,
                    )
                else:
                    _, trajectory_output = trajectory_fn(
                        dinosaur_state,
                        ocean_bulk_shf_temperature_anchor,
                        *radiative_trajectory_arguments,
                    )
            else:
                if self.use_analysis_2m_initialized_land_skin:
                    _, trajectory_output = trajectory_fn(
                        dinosaur_state,
                        analysis_2m_land_skin_temperature,
                        *radiative_trajectory_arguments,
                    )
                else:
                    _, trajectory_output = trajectory_fn(
                        dinosaur_state,
                        *radiative_trajectory_arguments,
                    )
            retain_skin_trajectory = (
                self.use_prognostic_skin_ri2m_lower_boundary
                and land_skin_reservoir_land_weight is not None
            )
            prognostic_skin_temperature = None
            if retain_skin_trajectory:
                trajectory, skin_trajectory = trajectory_output
                prognostic_skin_temperature = skin_trajectory[0]
            else:
                trajectory = trajectory_output
            trajectory_state = dinosaur_state_to_weather_state(
                trajectory,
                coords=grid.coords,
                pressure_levels_hpa=pressure_levels_hpa,
                latitude_reversed=grid.latitude_reversed,
                physics_specs=physics_specs,
                reference_temperature=reference_temperature,
                output_variables=output_variables,
                use_surface_layer_richardson_10m_wind_diagnostic=(
                    self.use_surface_layer_richardson_10m_wind_diagnostic
                ),
                use_bulk_richardson_2m_temperature_diagnostic=(
                    self.use_bulk_richardson_2m_temperature_diagnostic
                ),
                use_pressure_thickness_weighted_ri2m_temperature=(
                    self.use_pressure_thickness_weighted_ri2m_temperature
                ),
                use_prognostic_skin_ri2m_lower_boundary=(
                    self.use_prognostic_skin_ri2m_lower_boundary
                ),
                prognostic_skin_temperature=prognostic_skin_temperature,
                land_weight=land_skin_reservoir_land_weight,
                use_ocean_anchor_ri2m_lower_boundary=(
                    self.use_ocean_anchor_ri2m_lower_boundary
                ),
                ocean_temperature_anchor=(
                    ocean_bulk_shf_temperature_anchor
                    if self.use_ocean_anchor_ri2m_lower_boundary
                    else None
                ),
            )
            if self.apply_near_surface_residual_correction:
                residual_correction = (
                    _apply_scale_separated_near_surface_residual_correction
                    if self.use_scale_separated_near_surface_residual
                    else _apply_near_surface_residual_correction
                )
                residual_kwargs: dict[str, Any] = {}
                if self.use_scale_separated_near_surface_residual:
                    residual_kwargs = {
                        "horizontal_grid": grid.coords.horizontal,
                        "latitude_reversed": grid.latitude_reversed,
                    }
                    if self.use_land_sea_surface_temperature_residual:
                        residual_kwargs["land_sea_fraction"] = land_sea_fraction
                    if self.use_land_ocean_low_mode_t2m_memory:
                        residual_kwargs["land_sea_fraction"] = land_sea_fraction
                        residual_kwargs["use_land_ocean_low_mode_t2m_memory"] = True
                trajectory_state = residual_correction(
                    trajectory_state,
                    initial_state=single_state,
                    lead_steps=forecast_input.lead_steps,
                    lead_hours=forecast_input.lead_hours,
                    decay_hours=self.near_surface_residual_decay_hours,
                    use_stability_aware_decay=(
                        self.use_stability_aware_near_surface_residual_decay
                    ),
                    **residual_kwargs,
                )
                forecasts.append(trajectory_state.values)
            else:
                lead_indices = jnp.asarray(forecast_input.lead_steps, dtype=jnp.int32)
                forecasts.append(
                    jnp.take(trajectory_state.values, lead_indices, axis=0)
                )

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
        ocean_bulk_shf_ocean_weight: jax.Array | None = None,
        land_skin_reservoir_land_weight: jax.Array | None = None,
        terrain_height_meters: jax.Array | None = None,
        radiative_land_skin_reference_time: np.datetime64 | None = None,
    ):
        orography = jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32)
        use_coriolis_rotation_split = (
            self.apply_exact_coriolis_rotation_split
            or self.apply_symmetric_exact_coriolis_rotation_split
        )
        rollout_physics_specs = (
            replace(physics_specs, angular_velocity=0.0)
            if use_coriolis_rotation_split
            else physics_specs
        )
        anticipated_pv_coriolis_parameter = None
        if self.apply_anticipated_pv_flux:
            _, sin_latitude = coords.horizontal.nodal_mesh
            anticipated_pv_coriolis_parameter = (
                2.0 * physics_specs.angular_velocity * sin_latitude
            )
        humidity_key = SPECIFIC_HUMIDITY_VARIABLE if use_humidity_in_dynamics else None
        use_analysis_offset_equilibrium = (
            self.apply_weak_held_suarez_relaxation
            and self.use_analysis_offset_weak_held_suarez_equilibrium
        )
        use_ocean_bulk_sensible_heat_flux = (
            self.apply_ocean_bulk_sensible_heat_flux
            and ocean_bulk_shf_ocean_weight is not None
        )
        use_land_skin_reservoir = (
            self.apply_land_skin_reservoir
            and land_skin_reservoir_land_weight is not None
        )
        solar_radiation_model = None
        if (
            self.apply_zero_mean_radiative_land_skin_energy
            and radiative_land_skin_reference_time is not None
        ):
            try:
                solar_radiation_model = radiation.SolarRadiation(
                    coords=coords,
                    physics_specs=physics_specs,
                    reference_datetime=radiative_land_skin_reference_time,
                )
            except (OverflowError, TypeError, ValueError):
                solar_radiation_model = None

        def build_equation(
            equation_physics_specs: Any,
            equilibrium_temperature_offset: jax.Array | None = None,
            ocean_bulk_shf_temperature_anchor: jax.Array | None = None,
            use_anticipated_pv_flux: bool = False,
        ) -> Any:
            equation = _primitive_equation(
                reference_temperature=reference_temperature,
                orography=orography,
                coords=coords,
                physics_specs=equation_physics_specs,
                include_vertical_advection=self.include_vertical_advection,
                humidity_key=humidity_key,
                temperature_tendency_formulation=self.temperature_tendency_formulation,
                use_horizontal_semilagrangian_theta_transport=(
                    self.use_horizontal_semilagrangian_theta_transport
                ),
                use_midpoint_semilagrangian_theta_departure=(
                    self.use_midpoint_semilagrangian_theta_departure
                ),
                use_dry_static_energy_hsl_transport=(
                    self.use_dry_static_energy_hsl_transport
                ),
                use_layer_mass_weighted_dse_hsl_transport=(
                    self.use_layer_mass_weighted_dse_hsl_transport
                ),
                use_pressure_ramped_vertical_dse_increment=(
                    self.use_pressure_ramped_vertical_dse_increment
                ),
                use_anticipated_pv_flux=use_anticipated_pv_flux,
                anticipated_pv_step_seconds=(
                    step_seconds if use_anticipated_pv_flux else 0.0
                ),
                anticipated_pv_coriolis_parameter=(
                    anticipated_pv_coriolis_parameter
                    if use_anticipated_pv_flux
                    else None
                ),
                horizontal_semilagrangian_theta_transport_step=step_seconds,
            )
            if self.apply_weak_held_suarez_relaxation:
                equation = _compose_weak_held_suarez_equation(
                    equation=equation,
                    coords=coords,
                    physics_specs=equation_physics_specs,
                    reference_temperature=reference_temperature,
                    kf_per_day=self.weak_held_suarez_kf_per_day,
                    ka_timescale_days=self.weak_held_suarez_ka_timescale_days,
                    ks_timescale_days=self.weak_held_suarez_ks_timescale_days,
                    equilibrium_temperature_offset=equilibrium_temperature_offset,
                )
            if (
                use_ocean_bulk_sensible_heat_flux
                and ocean_bulk_shf_temperature_anchor is not None
            ):
                equation = _compose_ocean_bulk_sensible_heat_flux_equation(
                    equation=equation,
                    coords=coords,
                    physics_specs=equation_physics_specs,
                    reference_temperature=reference_temperature,
                    ocean_weight=cast(jax.Array, ocean_bulk_shf_ocean_weight),
                    temperature_anchor=ocean_bulk_shf_temperature_anchor,
                    step_seconds=step_seconds,
                )
            return equation

        step_seconds = _nondimensionalize_seconds(
            physics_specs,
            self.inner_step_seconds,
        )
        ode_solver = self._ode_solver()

        def build_filters(filter_physics_specs: Any) -> list[Any]:
            filters = []
            if self.apply_spectral_filter:
                filters.append(
                    _horizontal_diffusion_step_filter(
                        coords=coords,
                        physics_specs=filter_physics_specs,
                        step_seconds=step_seconds,
                        tau_seconds=self.horizontal_diffusion_tau_seconds,
                        order=self.horizontal_diffusion_order,
                    )
                )
            return filters

        def build_trajectory(
            equilibrium_temperature_offset: jax.Array | None = None,
            ocean_bulk_shf_temperature_anchor: jax.Array | None = None,
            analysis_2m_land_skin_temperature: jax.Array | None = None,
            radiative_land_skin_initial_time_offset: jax.Array | None = None,
        ) -> Any:
            equation = build_equation(
                rollout_physics_specs,
                equilibrium_temperature_offset=equilibrium_temperature_offset,
                ocean_bulk_shf_temperature_anchor=ocean_bulk_shf_temperature_anchor,
                use_anticipated_pv_flux=self.apply_anticipated_pv_flux,
            )
            filters = build_filters(rollout_physics_specs)
            if (
                self.apply_exact_coriolis_rotation_split
                and not self.apply_symmetric_exact_coriolis_rotation_split
            ):
                filters.append(
                    _exact_coriolis_rotation_step_filter(
                        coords=coords,
                        physics_specs=physics_specs,
                        step_seconds=step_seconds,
                    )
                )
            dfi_equation = equation
            dfi_filters = list(filters)
            if use_coriolis_rotation_split:
                dfi_equation = build_equation(
                    physics_specs,
                    equilibrium_temperature_offset=equilibrium_temperature_offset,
                    use_anticipated_pv_flux=False,
                )
                dfi_filters = build_filters(physics_specs)
            elif use_ocean_bulk_sensible_heat_flux or self.apply_anticipated_pv_flux:
                dfi_equation = build_equation(
                    rollout_physics_specs,
                    equilibrium_temperature_offset=equilibrium_temperature_offset,
                    use_anticipated_pv_flux=False,
                )
            if self.apply_tropical_wtg_mass_dse_relaxation:
                filters.append(
                    _tropical_wtg_mass_dse_relaxation_step_filter(
                        coords=coords,
                        physics_specs=physics_specs,
                        reference_temperature=reference_temperature,
                        step_seconds=step_seconds,
                    )
                )
            if self.apply_coupled_ekman_surface_closure:
                filters.append(
                    _ekman_coupled_surface_step_filter(
                        coords=coords,
                        physics_specs=physics_specs,
                        reference_temperature=reference_temperature,
                        step_seconds=step_seconds,
                        use_coriolis_scaled_ekman_depth=(
                            self.use_coriolis_scaled_ekman_depth
                        ),
                    )
                )
            if self.apply_orographic_lift_theta_tendency:
                filters.append(
                    _orographic_lift_theta_tendency_step_filter(
                        coords=coords,
                        physics_specs=physics_specs,
                        reference_temperature=reference_temperature,
                        terrain_height_meters=terrain_height_meters,
                        step_seconds=step_seconds,
                        use_depth_weighted_wind=(
                            self.use_depth_weighted_orographic_lift_wind
                        ),
                    )
                )
            if self.apply_terrain_work_form_drag_heating:
                filters.append(
                    _terrain_work_form_drag_heating_step_filter(
                        coords=coords,
                        physics_specs=physics_specs,
                        terrain_height_meters=terrain_height_meters,
                        step_seconds=step_seconds,
                    )
                )
            if self.apply_theta_layer_mean_recentering:
                filters.append(
                    _theta_layer_mean_recenter_step_filter(
                        coords=coords,
                        physics_specs=physics_specs,
                        reference_temperature=reference_temperature,
                    )
                )
            step_fn = ode_solver(equation, time_step=step_seconds)
            if filters:
                step_fn = time_integration.step_with_filters(step_fn, filters)
            if self.apply_symmetric_exact_coriolis_rotation_split:
                step_fn = _symmetric_exact_coriolis_rotation_step(
                    step_fn,
                    coords=coords,
                    physics_specs=physics_specs,
                    step_seconds=step_seconds,
                )
            initialize_state = None
            if self.apply_digital_filter_initialization:
                digital_filter_time_span = _nondimensionalize_seconds(
                    physics_specs,
                    self.digital_filter_time_span_seconds,
                )
                digital_filter_cutoff_period = _nondimensionalize_seconds(
                    physics_specs,
                    self.digital_filter_cutoff_seconds,
                )
                initialize_state = time_integration.digital_filter_initialization(
                    dfi_equation,
                    ode_solver,
                    dfi_filters,
                    time_span=digital_filter_time_span,
                    cutoff_period=digital_filter_cutoff_period,
                    dt=step_seconds,
                )
            if use_land_skin_reservoir:
                land_skin_step_fn = _land_skin_reservoir_step(
                    step_fn,
                    coords=coords,
                    physics_specs=physics_specs,
                    reference_temperature=reference_temperature,
                    land_weight=cast(jax.Array, land_skin_reservoir_land_weight),
                    step_seconds_si=self.inner_step_seconds,
                    solar_radiation_model=solar_radiation_model,
                    radiation_time_offset=(radiative_land_skin_initial_time_offset),
                )
                land_skin_trajectory_fn = time_integration.trajectory_from_step(
                    land_skin_step_fn,
                    outer_steps=output_count,
                    inner_steps=inner_steps,
                    start_with_input=True,
                    post_process_fn=(
                        (lambda carry: carry)
                        if self.use_prognostic_skin_ri2m_lower_boundary
                        else (lambda carry: carry[0])
                    ),
                )

                def land_skin_trajectory(dinosaur_state):
                    rollout_state = dinosaur_state
                    if initialize_state is not None:
                        rollout_state = initialize_state(rollout_state)
                    skin = _land_skin_reservoir_initial_skin(
                        rollout_state,
                        coords=coords,
                        reference_temperature=reference_temperature,
                    )
                    if self.use_analysis_2m_initialized_land_skin:
                        skin = _analysis_2m_initialized_land_skin(
                            skin,
                            analyzed_temperature=analysis_2m_land_skin_temperature,
                            land_weight=land_skin_reservoir_land_weight,
                        )
                    return land_skin_trajectory_fn((rollout_state, skin))

                return land_skin_trajectory

            trajectory_fn = time_integration.trajectory_from_step(
                step_fn,
                outer_steps=output_count,
                inner_steps=inner_steps,
                start_with_input=True,
            )
            if initialize_state is not None:
                base_trajectory_fn = trajectory_fn

                def initialized_trajectory_fn(dinosaur_state):
                    return base_trajectory_fn(initialize_state(dinosaur_state))

                trajectory_fn = initialized_trajectory_fn
            return trajectory_fn

        if self.use_analysis_2m_initialized_land_skin:

            def build_analysis_2m_trajectory(
                dinosaur_state,
                analysis_2m_land_skin_temperature,
                ocean_bulk_shf_temperature_anchor=None,
                radiative_land_skin_initial_time_offset=None,
            ):
                equilibrium_temperature_offset = None
                if use_analysis_offset_equilibrium:
                    equilibrium_temperature_offset = (
                        _analysis_offset_weak_held_suarez_equilibrium(
                            dinosaur_state,
                            coords=coords,
                            physics_specs=physics_specs,
                            reference_temperature=reference_temperature,
                        )
                    )
                analysis_2m_trajectory_fn = build_trajectory(
                    equilibrium_temperature_offset=equilibrium_temperature_offset,
                    ocean_bulk_shf_temperature_anchor=(
                        ocean_bulk_shf_temperature_anchor
                    ),
                    analysis_2m_land_skin_temperature=(
                        analysis_2m_land_skin_temperature
                    ),
                    radiative_land_skin_initial_time_offset=(
                        radiative_land_skin_initial_time_offset
                    ),
                )
                return analysis_2m_trajectory_fn(dinosaur_state)

            if use_ocean_bulk_sensible_heat_flux:

                def trajectory_fn(
                    dinosaur_state,
                    ocean_bulk_shf_temperature_anchor,
                    analysis_2m_land_skin_temperature,
                    radiative_land_skin_initial_time_offset=None,
                ):
                    return build_analysis_2m_trajectory(
                        dinosaur_state,
                        analysis_2m_land_skin_temperature,
                        ocean_bulk_shf_temperature_anchor,
                        radiative_land_skin_initial_time_offset,
                    )

            else:

                def trajectory_fn(
                    dinosaur_state,
                    analysis_2m_land_skin_temperature,
                    radiative_land_skin_initial_time_offset=None,
                ):
                    return build_analysis_2m_trajectory(
                        dinosaur_state,
                        analysis_2m_land_skin_temperature,
                        radiative_land_skin_initial_time_offset=(
                            radiative_land_skin_initial_time_offset
                        ),
                    )

        elif use_analysis_offset_equilibrium:
            if use_ocean_bulk_sensible_heat_flux:

                def trajectory_fn(
                    dinosaur_state,
                    ocean_bulk_shf_temperature_anchor,
                    radiative_land_skin_initial_time_offset=None,
                ):
                    equilibrium_temperature_offset = (
                        _analysis_offset_weak_held_suarez_equilibrium(
                            dinosaur_state,
                            coords=coords,
                            physics_specs=physics_specs,
                            reference_temperature=reference_temperature,
                        )
                    )
                    offset_trajectory_fn = build_trajectory(
                        equilibrium_temperature_offset=(equilibrium_temperature_offset),
                        ocean_bulk_shf_temperature_anchor=(
                            ocean_bulk_shf_temperature_anchor
                        ),
                        radiative_land_skin_initial_time_offset=(
                            radiative_land_skin_initial_time_offset
                        ),
                    )
                    return offset_trajectory_fn(dinosaur_state)

            else:

                def trajectory_fn(
                    dinosaur_state,
                    radiative_land_skin_initial_time_offset=None,
                ):
                    equilibrium_temperature_offset = (
                        _analysis_offset_weak_held_suarez_equilibrium(
                            dinosaur_state,
                            coords=coords,
                            physics_specs=physics_specs,
                            reference_temperature=reference_temperature,
                        )
                    )
                    offset_trajectory_fn = build_trajectory(
                        equilibrium_temperature_offset=equilibrium_temperature_offset,
                        radiative_land_skin_initial_time_offset=(
                            radiative_land_skin_initial_time_offset
                        ),
                    )
                    return offset_trajectory_fn(dinosaur_state)

        elif use_ocean_bulk_sensible_heat_flux:

            def trajectory_fn(
                dinosaur_state,
                ocean_bulk_shf_temperature_anchor,
                radiative_land_skin_initial_time_offset=None,
            ):
                ocean_bulk_shf_trajectory_fn = build_trajectory(
                    ocean_bulk_shf_temperature_anchor=(
                        ocean_bulk_shf_temperature_anchor
                    ),
                    radiative_land_skin_initial_time_offset=(
                        radiative_land_skin_initial_time_offset
                    ),
                )
                return ocean_bulk_shf_trajectory_fn(dinosaur_state)

        else:
            if self.apply_zero_mean_radiative_land_skin_energy:

                def trajectory_fn(
                    dinosaur_state,
                    radiative_land_skin_initial_time_offset=None,
                ):
                    radiative_trajectory_fn = build_trajectory(
                        radiative_land_skin_initial_time_offset=(
                            radiative_land_skin_initial_time_offset
                        )
                    )
                    return radiative_trajectory_fn(dinosaur_state)

            else:
                trajectory_fn = build_trajectory()
        return jax.jit(trajectory_fn) if self.jit_forecast else trajectory_fn

    def _ode_solver(
        self,
        *,
        fallback_to_centered_on_nonfinite: bool = True,
    ) -> Any:
        """Return SIL3 with the requested off-centered non-finite policy."""
        if self.semi_implicit_offcentering == 0.0:
            return time_integration.imex_rk_sil3
        solver_arguments = {
            "implicit_offcentering": self.semi_implicit_offcentering,
        }
        if not fallback_to_centered_on_nonfinite:
            solver_arguments["fallback_to_centered_on_nonfinite"] = False
        return partial(time_integration.imex_rk_sil3, **solver_arguments)


def _analysis_offset_weak_held_suarez_equilibrium(
    state: Any,
    *,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    reference_temperature: np.ndarray,
) -> jax.Array:
    """Return a bounded low-order offset to the standard HS equilibrium."""
    nodal_temperature = (
        coords.horizontal.to_nodal(state.temperature_variation)
        + jnp.asarray(reference_temperature)[:, jnp.newaxis, jnp.newaxis]
    )
    nodal_surface_pressure = jnp.exp(
        coords.horizontal.to_nodal(state.log_surface_pressure)
    )
    forcing = _TracerSafeHeldSuarezForcingSigma(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
    )
    standard_equilibrium = forcing.equilibrium_temperature(nodal_surface_pressure)
    raw_offset = nodal_temperature - standard_equilibrium
    modal_offset = coords.horizontal.to_modal(raw_offset)
    low_mode_mask = _analysis_offset_weak_hs_low_mode_mask(coords.horizontal)
    filtered_offset = coords.horizontal.to_nodal(modal_offset * low_mode_mask)
    offset_is_finite = jnp.all(jnp.isfinite(filtered_offset))
    offset_cap = _unit_factor(physics_specs, "kelvin") * (
        _ANALYSIS_OFFSET_HELD_SUAREZ_MAX_KELVIN
    )
    clipped_offset = jnp.clip(filtered_offset, -offset_cap, offset_cap)
    return jnp.where(
        offset_is_finite,
        clipped_offset,
        jnp.zeros_like(clipped_offset),
    )


def _analysis_offset_weak_hs_low_mode_mask(
    horizontal_grid: spherical_harmonic.Grid,
) -> jax.Array:
    """Return the fixed low-order spectral mask for analysis HS offsets."""
    longitude_wavenumber, total_wavenumber = horizontal_grid.modal_mesh
    low_mode_mask = (
        np.asarray(horizontal_grid.mask)
        & (
            np.abs(longitude_wavenumber)
            <= _ANALYSIS_OFFSET_HELD_SUAREZ_MAX_LONGITUDE_WAVENUMBER
        )
        & (total_wavenumber <= _ANALYSIS_OFFSET_HELD_SUAREZ_MAX_TOTAL_WAVENUMBER)
    )
    return jnp.asarray(low_mode_mask, dtype=jnp.float32)


def _exact_coriolis_rotation_step_filter(
    *,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    step_seconds: float,
) -> Any:
    """Return a filter applying the exact positive-time planetary rotation."""
    _, sin_latitude = coords.horizontal.nodal_mesh
    coriolis_angle = jnp.asarray(
        2.0 * physics_specs.angular_velocity * sin_latitude * step_seconds
    )
    cosine_angle = jnp.cos(coriolis_angle)
    sine_angle = jnp.sin(coriolis_angle)

    def exact_coriolis_rotation_filter(prev_state: Any, next_state: Any) -> Any:
        del prev_state
        u_wind, v_wind = spherical_harmonic.vor_div_to_uv_nodal(
            coords.horizontal,
            next_state.vorticity,
            next_state.divergence,
        )
        u_rotated = u_wind * cosine_angle + v_wind * sine_angle
        v_rotated = v_wind * cosine_angle - u_wind * sine_angle
        vorticity, divergence = spherical_harmonic.uv_nodal_to_vor_div_modal(
            coords.horizontal,
            u_rotated,
            v_rotated,
        )
        return _primitive_equation_state(
            vorticity=vorticity,
            divergence=divergence,
            temperature_variation=next_state.temperature_variation,
            log_surface_pressure=next_state.log_surface_pressure,
            tracers=next_state.tracers,
            sim_time=next_state.sim_time,
        )

    return exact_coriolis_rotation_filter


def _symmetric_exact_coriolis_rotation_step(
    step_fn: Any,
    *,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    step_seconds: float,
) -> Any:
    """Return a Strang-split step around non-Coriolis dynamics."""
    half_rotation_filter = _exact_coriolis_rotation_step_filter(
        coords=coords,
        physics_specs=physics_specs,
        step_seconds=0.5 * step_seconds,
    )

    def symmetric_exact_coriolis_rotation_step(state: Any) -> Any:
        half_rotated_state = half_rotation_filter(state, state)
        next_state = step_fn(half_rotated_state)
        return half_rotation_filter(half_rotated_state, next_state)

    return symmetric_exact_coriolis_rotation_step


def _theta_layer_mean_recenter_step_filter(
    *,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    reference_temperature: np.ndarray,
) -> Any:
    """Return a filter that preserves layerwise area-mean dry theta."""
    sigma_centers = jnp.asarray(coords.vertical.centers)[:, jnp.newaxis, jnp.newaxis]
    reference_temperature = jnp.asarray(reference_temperature)[
        :, jnp.newaxis, jnp.newaxis
    ]
    unit_registry = cast(Any, scales.units)
    reference_pressure = float(
        physics_specs.nondimensionalize(unit_registry.Quantity(100000.0, "pascal"))
    )
    quadrature_weights = jnp.asarray(coords.horizontal.quadrature_weights)
    weight_sum = jnp.sum(quadrature_weights)

    def layer_mean(nodal_field: jax.Array) -> jax.Array:
        return jnp.sum(nodal_field * quadrature_weights, axis=(-2, -1)) / weight_sum

    def nodal_pressure(state: Any) -> jax.Array:
        surface_pressure = jnp.exp(
            coords.horizontal.to_nodal(state.log_surface_pressure)
        )
        return sigma_centers * surface_pressure

    def full_temperature(state: Any) -> jax.Array:
        return (
            coords.horizontal.to_nodal(state.temperature_variation)
            + reference_temperature
        )

    def theta_layer_mean_recenter_filter(prev_state: Any, next_state: Any) -> Any:
        prev_pressure = nodal_pressure(prev_state)
        next_pressure = nodal_pressure(next_state)
        prev_temperature = full_temperature(prev_state)
        next_temperature = full_temperature(next_state)
        prev_theta = primitive_equations.potential_temperature_from_temperature(
            prev_temperature,
            prev_pressure,
            reference_pressure,
            physics_specs.kappa,
        )
        next_theta = primitive_equations.potential_temperature_from_temperature(
            next_temperature,
            next_pressure,
            reference_pressure,
            physics_specs.kappa,
        )
        next_temperature_to_theta_factor = (
            reference_pressure / next_pressure
        ) ** physics_specs.kappa
        temperature_increment = (
            layer_mean(prev_theta) - layer_mean(next_theta)
        ) / layer_mean(next_temperature_to_theta_factor)
        corrected_temperature_variation = spherical_harmonic.add_constant(
            next_state.temperature_variation,
            temperature_increment,
        )
        finite_diagnostics = jnp.all(
            jnp.asarray(
                [
                    jnp.all(jnp.isfinite(prev_pressure)),
                    jnp.all(prev_pressure > 0),
                    jnp.all(jnp.isfinite(next_pressure)),
                    jnp.all(next_pressure > 0),
                    jnp.all(jnp.isfinite(prev_theta)),
                    jnp.all(jnp.isfinite(next_theta)),
                    jnp.all(jnp.isfinite(next_temperature_to_theta_factor)),
                    jnp.all(jnp.isfinite(temperature_increment)),
                    jnp.all(jnp.isfinite(corrected_temperature_variation)),
                ]
            )
        )
        temperature_variation = jnp.where(
            finite_diagnostics,
            corrected_temperature_variation,
            next_state.temperature_variation,
        )
        return _primitive_equation_state(
            vorticity=next_state.vorticity,
            divergence=next_state.divergence,
            temperature_variation=temperature_variation,
            log_surface_pressure=next_state.log_surface_pressure,
            tracers=next_state.tracers,
            sim_time=next_state.sim_time,
        )

    return theta_layer_mean_recenter_filter


def _tropical_wtg_mass_dse_relaxation_step_filter(
    *,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    reference_temperature: np.ndarray,
    step_seconds: float,
) -> Any:
    """Return a rollout-only weak tropical free-tropospheric mass-DSE filter."""
    orography = jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32)
    equation = primitive_equations.PrimitiveEquations(
        reference_temperature,
        orography,
        coords,
        physics_specs,
        include_vertical_advection=True,
    )
    latitude_envelope = _tropical_wtg_latitude_envelope(coords.horizontal)
    sigma_envelope = _tropical_wtg_sigma_envelope(coords.vertical)
    mask = sigma_envelope[:, jnp.newaxis, jnp.newaxis] * latitude_envelope
    low_mode_mask = _tropical_wtg_low_mode_mask(coords.horizontal)
    quadrature_weights = jnp.asarray(coords.horizontal.quadrature_weights)
    tropical_weights = latitude_envelope * quadrature_weights
    tropical_weight_sum = jnp.sum(tropical_weights)
    mask_weights = mask * quadrature_weights[jnp.newaxis, ...]
    mask_weight_sum = jnp.sum(mask_weights, axis=(-2, -1))
    tiny_weight = jnp.asarray(jnp.finfo(mask.dtype).tiny, dtype=mask.dtype)
    safe_tropical_weight_sum = jnp.where(
        tropical_weight_sum > tiny_weight,
        tropical_weight_sum,
        jnp.ones_like(tropical_weight_sum),
    )
    safe_mask_weight_sum = jnp.where(
        mask_weight_sum > tiny_weight,
        mask_weight_sum,
        jnp.ones_like(mask_weight_sum),
    )
    relaxation_timescale = _nondimensionalize_seconds(
        physics_specs,
        _TROPICAL_WTG_RELAXATION_TIMESCALE_DAYS * 24.0 * 3600.0,
    )
    relaxation_fraction = jnp.asarray(step_seconds / relaxation_timescale)
    temperature_increment_cap = _unit_factor(physics_specs, "kelvin") * (
        _TROPICAL_WTG_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN
    )

    def tropical_wtg_mass_dse_relaxation_filter(
        prev_state: Any,
        next_state: Any,
    ) -> Any:
        del prev_state
        aux_state = primitive_equations.compute_diagnostic_state_sigma(
            next_state,
            coords,
        )
        dry_static_energy_anomaly, geopotential = (
            equation.nodal_dry_static_energy_anomaly(aux_state)
        )
        layer_pressure_thickness = equation.nodal_sigma_layer_pressure_thickness(
            next_state
        )
        valid_layer_pressure_thickness = jnp.isfinite(layer_pressure_thickness) & (
            layer_pressure_thickness > 0.0
        )
        safe_layer_pressure_thickness = jnp.where(
            valid_layer_pressure_thickness,
            layer_pressure_thickness,
            jnp.ones_like(layer_pressure_thickness),
        )
        mass_dse_anomaly = layer_pressure_thickness * dry_static_energy_anomaly
        low_mode_mass_dse_anomaly = coords.horizontal.to_nodal(
            coords.horizontal.to_modal(mass_dse_anomaly) * low_mode_mask
        )
        tropical_layer_mean = (
            jnp.sum(
                low_mode_mass_dse_anomaly * tropical_weights,
                axis=(-2, -1),
            )
            / safe_tropical_weight_sum
        )
        masked_mass_dse_anomaly = mask * (
            low_mode_mass_dse_anomaly - tropical_layer_mean[:, jnp.newaxis, jnp.newaxis]
        )
        mass_dse_increment = -relaxation_fraction * masked_mass_dse_anomaly
        raw_temperature_increment = (
            mass_dse_increment / safe_layer_pressure_thickness / physics_specs.Cp
        )
        clipped_temperature_increment = jnp.clip(
            raw_temperature_increment,
            -temperature_increment_cap,
            temperature_increment_cap,
        )
        layer_heat_offset = (
            jnp.sum(
                clipped_temperature_increment * quadrature_weights,
                axis=(-2, -1),
            )
            / safe_mask_weight_sum
        )
        temperature_increment = clipped_temperature_increment - (
            mask * layer_heat_offset[:, jnp.newaxis, jnp.newaxis]
        )
        temperature_increment = jnp.where(
            mask_weight_sum[:, jnp.newaxis, jnp.newaxis] > tiny_weight,
            temperature_increment,
            jnp.zeros_like(temperature_increment),
        )
        corrected_temperature_variation = next_state.temperature_variation + (
            coords.horizontal.to_modal(temperature_increment)
        )
        finite_diagnostics = jnp.all(
            jnp.asarray(
                [
                    jnp.all(jnp.isfinite(latitude_envelope)),
                    jnp.all(jnp.isfinite(sigma_envelope)),
                    jnp.all(jnp.isfinite(mask)),
                    jnp.all(jnp.isfinite(low_mode_mask)),
                    jnp.all(valid_layer_pressure_thickness),
                    jnp.all(jnp.isfinite(dry_static_energy_anomaly)),
                    jnp.all(jnp.isfinite(geopotential)),
                    jnp.all(jnp.isfinite(mass_dse_anomaly)),
                    jnp.all(jnp.isfinite(low_mode_mass_dse_anomaly)),
                    jnp.all(jnp.isfinite(masked_mass_dse_anomaly)),
                    jnp.all(jnp.isfinite(mass_dse_increment)),
                    jnp.all(jnp.isfinite(raw_temperature_increment)),
                    jnp.all(jnp.isfinite(clipped_temperature_increment)),
                    jnp.all(jnp.isfinite(temperature_increment)),
                    jnp.all(jnp.isfinite(corrected_temperature_variation)),
                ]
            )
        )
        temperature_variation = jnp.where(
            finite_diagnostics,
            corrected_temperature_variation,
            next_state.temperature_variation,
        )
        return _primitive_equation_state(
            vorticity=next_state.vorticity,
            divergence=next_state.divergence,
            temperature_variation=temperature_variation,
            log_surface_pressure=next_state.log_surface_pressure,
            tracers=next_state.tracers,
            sim_time=next_state.sim_time,
        )

    return tropical_wtg_mass_dse_relaxation_filter


def _ekman_coupled_surface_step_filter(
    *,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    reference_temperature: np.ndarray,
    step_seconds: float,
    use_coriolis_scaled_ekman_depth: bool = False,
) -> Any:
    """Return a weak coupled stress and pressure filter for the lower layers."""
    assert step_seconds > 0.0
    horizontal_grid = coords.horizontal
    sigma_centers = jnp.asarray(coords.vertical.centers)
    lowest_sigma = sigma_centers[-1]
    quadrature_weights = jnp.asarray(horizontal_grid.quadrature_weights)
    vertical_taper = _ekman_coupled_vertical_taper(coords.vertical)
    equatorial_taper = _ekman_coupled_equatorial_taper(horizontal_grid)
    _, sin_latitude = horizontal_grid.nodal_mesh
    coriolis_parameter = 2.0 * physics_specs.angular_velocity * sin_latitude
    coriolis_floor = (
        2.0
        * physics_specs.angular_velocity
        * jnp.sin(jnp.deg2rad(_EKMAN_COUPLED_EQUATORIAL_FULL_LATITUDE_DEGREES))
    )
    safe_coriolis = jnp.where(
        coriolis_parameter >= 0.0,
        jnp.maximum(coriolis_parameter, coriolis_floor),
        jnp.minimum(coriolis_parameter, -coriolis_floor),
    )
    step_seconds = jnp.asarray(step_seconds, dtype=jnp.float32)
    reference_temperature = jnp.asarray(reference_temperature)
    wind_unit_factor = _unit_factor(physics_specs, "meter / second")
    acceleration_unit_factor = _unit_factor(physics_specs, "meter / second ** 2")
    pressure_unit_factor = _unit_factor(physics_specs, "pascal")
    temperature_unit_factor = _unit_factor(physics_specs, "kelvin")
    wind_increment_cap = jnp.asarray(
        _EKMAN_COUPLED_PROJECTION_SAFETY_FACTOR
        * _EKMAN_COUPLED_MAX_WIND_STEP_INCREMENT_METERS_PER_SECOND
        * wind_unit_factor,
        dtype=jnp.float32,
    )
    pressure_increment_cap = jnp.asarray(
        _EKMAN_COUPLED_MAX_LOGP_STEP_INCREMENT,
        dtype=jnp.float32,
    )
    fallback_temperature = jnp.asarray(
        250.0 * temperature_unit_factor, dtype=jnp.float32
    )
    fallback_pressure = jnp.asarray(100_000.0 * pressure_unit_factor, dtype=jnp.float32)

    def ekman_coupled_surface_filter(prev_state: Any, next_state: Any) -> Any:
        del prev_state
        u_wind, v_wind = spherical_harmonic.vor_div_to_uv_nodal(
            horizontal_grid,
            next_state.vorticity,
            next_state.divergence,
        )
        lowest_u_wind = u_wind[-1]
        lowest_v_wind = v_wind[-1]
        nodal_temperature = (
            horizontal_grid.to_nodal(next_state.temperature_variation)
            + reference_temperature[:, jnp.newaxis, jnp.newaxis]
        )
        lowest_temperature = nodal_temperature[-1]
        surface_pressure = jnp.exp(
            horizontal_grid.to_nodal(next_state.log_surface_pressure)[0]
        )
        lower_pressure = lowest_sigma * surface_pressure
        lower_temperature_si = lowest_temperature / temperature_unit_factor
        lower_pressure_si = lower_pressure / pressure_unit_factor
        density = lower_pressure_si / (_DRY_AIR_GAS_CONSTANT_SI * lower_temperature_si)
        finite_stress_inputs = (
            jnp.isfinite(lowest_u_wind)
            & jnp.isfinite(lowest_v_wind)
            & jnp.isfinite(lowest_temperature)
            & jnp.isfinite(surface_pressure)
            & jnp.isfinite(density)
            & (lowest_temperature > 0.0)
            & (surface_pressure > 0.0)
            & (lower_pressure > 0.0)
            & (density > 0.0)
        )
        safe_lowest_u_wind = jnp.where(
            finite_stress_inputs,
            lowest_u_wind,
            jnp.zeros_like(lowest_u_wind),
        )
        safe_lowest_v_wind = jnp.where(
            finite_stress_inputs,
            lowest_v_wind,
            jnp.zeros_like(lowest_v_wind),
        )
        safe_density = jnp.where(finite_stress_inputs, density, 1.0)
        safe_temperature = jnp.where(
            finite_stress_inputs,
            lowest_temperature,
            fallback_temperature,
        )
        safe_lower_pressure = jnp.where(
            finite_stress_inputs,
            lower_pressure,
            lowest_sigma * fallback_pressure,
        )
        lowest_u_wind_si = safe_lowest_u_wind / wind_unit_factor
        lowest_v_wind_si = safe_lowest_v_wind / wind_unit_factor
        wind_speed_si = _sqrt_nonnegative_with_finite_gradient(
            lowest_u_wind_si**2 + lowest_v_wind_si**2
        )
        stress_u = (
            safe_density
            * _EKMAN_COUPLED_DRAG_COEFFICIENT
            * wind_speed_si
            * lowest_u_wind_si
        )
        stress_v = (
            safe_density
            * _EKMAN_COUPLED_DRAG_COEFFICIENT
            * wind_speed_si
            * lowest_v_wind_si
        )
        fixed_surface_u_acceleration = (
            -stress_u
            / (safe_density * _EKMAN_COUPLED_BOUNDARY_LAYER_DEPTH_METERS)
            * acceleration_unit_factor
        )
        fixed_surface_v_acceleration = (
            -stress_v
            / (safe_density * _EKMAN_COUPLED_BOUNDARY_LAYER_DEPTH_METERS)
            * acceleration_unit_factor
        )
        fixed_raw_u_increment = (
            step_seconds
            * vertical_taper[:, jnp.newaxis, jnp.newaxis]
            * fixed_surface_u_acceleration[jnp.newaxis, ...]
        )
        fixed_raw_v_increment = (
            step_seconds
            * vertical_taper[:, jnp.newaxis, jnp.newaxis]
            * fixed_surface_v_acceleration[jnp.newaxis, ...]
        )
        if use_coriolis_scaled_ekman_depth:
            friction_velocity = (
                jnp.sqrt(_EKMAN_COUPLED_DRAG_COEFFICIENT) * wind_speed_si
            )
            ekman_depth = _ekman_coriolis_scaled_depth(
                friction_velocity,
                coriolis_parameter=coriolis_parameter,
                coriolis_floor=coriolis_floor,
            )
            depth_weights, valid_depth_weights = _ekman_depth_vertical_weights(
                temperature=nodal_temperature,
                surface_pressure=surface_pressure,
                sigma_centers=sigma_centers,
                ekman_depth_meters=ekman_depth,
                pressure_unit_factor=pressure_unit_factor,
                temperature_unit_factor=temperature_unit_factor,
            )
            depth_surface_u_acceleration = (
                -stress_u / (safe_density * ekman_depth) * acceleration_unit_factor
            )
            depth_surface_v_acceleration = (
                -stress_v / (safe_density * ekman_depth) * acceleration_unit_factor
            )
            valid_depth_diagnostics = (
                finite_stress_inputs
                & valid_depth_weights
                & jnp.isfinite(friction_velocity)
                & jnp.isfinite(ekman_depth)
                & jnp.isfinite(depth_surface_u_acceleration)
                & jnp.isfinite(depth_surface_v_acceleration)
            )
            depth_raw_u_increment = (
                step_seconds
                * depth_weights
                * depth_surface_u_acceleration[jnp.newaxis, ...]
            )
            depth_raw_v_increment = (
                step_seconds
                * depth_weights
                * depth_surface_v_acceleration[jnp.newaxis, ...]
            )
            use_depth_column = valid_depth_diagnostics[jnp.newaxis, ...]
            raw_u_increment = jnp.where(
                use_depth_column,
                depth_raw_u_increment,
                fixed_raw_u_increment,
            )
            raw_v_increment = jnp.where(
                use_depth_column,
                depth_raw_v_increment,
                fixed_raw_v_increment,
            )
            surface_u_acceleration = jnp.where(
                valid_depth_diagnostics,
                depth_surface_u_acceleration,
                fixed_surface_u_acceleration,
            )
            surface_v_acceleration = jnp.where(
                valid_depth_diagnostics,
                depth_surface_v_acceleration,
                fixed_surface_v_acceleration,
            )
        else:
            raw_u_increment = fixed_raw_u_increment
            raw_v_increment = fixed_raw_v_increment
            surface_u_acceleration = fixed_surface_u_acceleration
            surface_v_acceleration = fixed_surface_v_acceleration
        u_increment = jax.vmap(
            lambda layer_increment: _bounded_area_neutral_field(
                layer_increment,
                wind_increment_cap,
                quadrature_weights,
            )
        )(raw_u_increment)
        v_increment = jnp.clip(
            raw_v_increment,
            -wind_increment_cap,
            wind_increment_cap,
        )
        provisional_vorticity_increment, provisional_divergence_increment = (
            spherical_harmonic.uv_nodal_to_vor_div_modal(
                horizontal_grid,
                u_increment,
                v_increment,
            )
        )
        projected_u_increment, projected_v_increment = (
            spherical_harmonic.vor_div_to_uv_nodal(
                horizontal_grid,
                provisional_vorticity_increment,
                provisional_divergence_increment,
            )
        )
        projected_wind_increment_max = jnp.maximum(
            jnp.max(jnp.abs(projected_u_increment)),
            jnp.max(jnp.abs(projected_v_increment)),
        )
        wind_projection_scale = jnp.minimum(
            1.0,
            wind_increment_cap / jnp.maximum(projected_wind_increment_max, 1.0e-30),
        )
        u_increment = u_increment * wind_projection_scale
        v_increment = v_increment * wind_projection_scale
        vorticity_increment, divergence_increment = (
            spherical_harmonic.uv_nodal_to_vor_div_modal(
                horizontal_grid,
                u_increment,
                v_increment,
            )
        )
        projected_u_increment, projected_v_increment = (
            spherical_harmonic.vor_div_to_uv_nodal(
                horizontal_grid,
                vorticity_increment,
                divergence_increment,
            )
        )
        projected_u_increment = jax.vmap(
            lambda layer_increment: _bounded_area_neutral_field(
                layer_increment,
                wind_increment_cap,
                quadrature_weights,
            )
        )(projected_u_increment)
        projected_v_increment = _bounded_field(
            projected_v_increment, wind_increment_cap
        )
        vorticity_increment, divergence_increment = (
            spherical_harmonic.uv_nodal_to_vor_div_modal(
                horizontal_grid,
                projected_u_increment,
                projected_v_increment,
            )
        )
        projected_u_increment, projected_v_increment = (
            spherical_harmonic.vor_div_to_uv_nodal(
                horizontal_grid,
                vorticity_increment,
                divergence_increment,
            )
        )
        u_increment = projected_u_increment
        v_increment = projected_v_increment

        applied_surface_u_acceleration = u_increment[-1] / step_seconds
        applied_surface_v_acceleration = v_increment[-1] / step_seconds
        ekman_transport_u = (
            -equatorial_taper * applied_surface_v_acceleration / safe_coriolis
        )
        ekman_transport_v = (
            equatorial_taper * applied_surface_u_acceleration / safe_coriolis
        )
        _, ekman_transport_divergence = spherical_harmonic.uv_nodal_to_vor_div_modal(
            horizontal_grid,
            ekman_transport_u,
            ekman_transport_v,
        )
        raw_log_pressure_increment = -step_seconds * horizontal_grid.to_nodal(
            ekman_transport_divergence
        )
        applied_wind_increment = _sqrt_nonnegative_with_finite_gradient(
            u_increment[-1] ** 2 + v_increment[-1] ** 2
        )
        coupled_pressure_cap = jnp.minimum(
            pressure_increment_cap,
            _EKMAN_COUPLED_LOGP_PER_WIND_STEP_RATIO * jnp.max(applied_wind_increment),
        )
        log_pressure_increment = _bounded_area_neutral_field(
            raw_log_pressure_increment,
            coupled_pressure_cap,
            quadrature_weights,
        )
        projected_log_pressure_increment = horizontal_grid.to_nodal(
            horizontal_grid.to_modal(log_pressure_increment)
        )
        projected_log_pressure_increment_max = jnp.max(
            jnp.abs(projected_log_pressure_increment)
        )
        pressure_projection_scale = jnp.minimum(
            1.0,
            coupled_pressure_cap
            / jnp.maximum(projected_log_pressure_increment_max, 1.0e-30),
        )
        log_pressure_increment = log_pressure_increment * pressure_projection_scale

        corrected_vorticity = next_state.vorticity + vorticity_increment
        corrected_divergence = next_state.divergence + divergence_increment
        corrected_log_surface_pressure = (
            next_state.log_surface_pressure
            + (horizontal_grid.to_modal(log_pressure_increment)[jnp.newaxis])
        )
        finite_diagnostics = jnp.all(
            jnp.asarray(
                [
                    jnp.all(finite_stress_inputs),
                    jnp.all(jnp.isfinite(safe_temperature)),
                    jnp.all(jnp.isfinite(safe_lower_pressure)),
                    jnp.all(jnp.isfinite(stress_u)),
                    jnp.all(jnp.isfinite(stress_v)),
                    jnp.all(jnp.isfinite(surface_u_acceleration)),
                    jnp.all(jnp.isfinite(surface_v_acceleration)),
                    jnp.all(jnp.isfinite(u_increment)),
                    jnp.all(jnp.isfinite(v_increment)),
                    jnp.all(jnp.isfinite(ekman_transport_u)),
                    jnp.all(jnp.isfinite(ekman_transport_v)),
                    jnp.all(jnp.isfinite(raw_log_pressure_increment)),
                    jnp.all(jnp.isfinite(log_pressure_increment)),
                    jnp.all(jnp.isfinite(corrected_vorticity)),
                    jnp.all(jnp.isfinite(corrected_divergence)),
                    jnp.all(jnp.isfinite(corrected_log_surface_pressure)),
                ]
            )
        )
        candidate_has_effect = (
            jnp.max(jnp.abs(u_increment))
            + jnp.max(jnp.abs(v_increment))
            + jnp.max(jnp.abs(log_pressure_increment))
        ) > 0.0
        use_candidate = finite_diagnostics & candidate_has_effect
        return _primitive_equation_state(
            vorticity=jnp.where(
                use_candidate,
                corrected_vorticity,
                next_state.vorticity,
            ),
            divergence=jnp.where(
                use_candidate,
                corrected_divergence,
                next_state.divergence,
            ),
            temperature_variation=next_state.temperature_variation,
            log_surface_pressure=jnp.where(
                use_candidate,
                corrected_log_surface_pressure,
                next_state.log_surface_pressure,
            ),
            tracers=next_state.tracers,
            sim_time=next_state.sim_time,
        )

    return ekman_coupled_surface_filter


def _ekman_coupled_vertical_taper(
    vertical_coords: sigma_coordinates.SigmaCoordinates,
) -> jax.Array:
    """Return the fixed lower-layer taper for coupled Ekman momentum forcing."""
    layer_count = vertical_coords.layers
    taper = np.zeros((layer_count,), dtype=np.float32)
    taper[-1] = 1.0
    if layer_count > 1:
        taper[-2] = _EKMAN_COUPLED_SECOND_LAYER_FRACTION
    return jnp.asarray(taper)


def _ekman_coriolis_scaled_depth(
    friction_velocity: jax.Array,
    *,
    coriolis_parameter: jax.Array,
    coriolis_floor: jax.Array | float,
) -> jax.Array:
    """Return bounded neutral Ekman depth from friction velocity over rotation."""
    safe_coriolis = jnp.maximum(jnp.abs(coriolis_parameter), coriolis_floor)
    raw_depth = _EKMAN_CORIOLIS_DEPTH_COEFFICIENT * friction_velocity / safe_coriolis
    return jnp.clip(
        raw_depth,
        _EKMAN_CORIOLIS_DEPTH_MIN_METERS,
        _EKMAN_CORIOLIS_DEPTH_MAX_METERS,
    )


def _ekman_depth_vertical_weights(
    *,
    temperature: jax.Array,
    surface_pressure: jax.Array,
    sigma_centers: jax.Array,
    ekman_depth_meters: jax.Array,
    pressure_unit_factor: float | jax.Array,
    temperature_unit_factor: float | jax.Array,
) -> tuple[jax.Array, jax.Array]:
    """Return normalized lower-column weights for depth-varying Ekman stress."""
    sigma = sigma_centers[:, jnp.newaxis, jnp.newaxis]
    layer_pressure = sigma * surface_pressure[jnp.newaxis, ...]
    temperature_si = temperature / temperature_unit_factor
    surface_pressure_si = surface_pressure / pressure_unit_factor
    layer_pressure_si = layer_pressure / pressure_unit_factor
    height_meters = (
        _DRY_AIR_GAS_CONSTANT_SI
        * temperature_si
        / _GRAVITY_ACCELERATION_SI
        * jnp.log(jnp.maximum(surface_pressure_si, 1.0) / layer_pressure_si)
    )
    raw_weights = jnp.exp(-jnp.maximum(height_meters, 0.0) / ekman_depth_meters)
    weight_sum = jnp.sum(raw_weights, axis=0)
    valid_columns = (
        jnp.all(jnp.isfinite(temperature), axis=0)
        & jnp.isfinite(surface_pressure)
        & jnp.isfinite(ekman_depth_meters)
        & jnp.all(jnp.isfinite(height_meters), axis=0)
        & jnp.all(jnp.isfinite(raw_weights), axis=0)
        & (surface_pressure > 0.0)
        & (ekman_depth_meters > 0.0)
        & (weight_sum > 0.0)
    )
    safe_weight_sum = jnp.where(valid_columns, weight_sum, 1.0)
    weights = raw_weights / safe_weight_sum[jnp.newaxis, ...]
    weights = jnp.where(valid_columns[jnp.newaxis, ...], weights, 0.0)
    return weights, valid_columns


def _ekman_coupled_equatorial_taper(
    horizontal_grid: spherical_harmonic.Grid,
) -> jax.Array:
    """Return a smooth mass-pumping taper that is zero near the equator."""
    _, sin_latitude = horizontal_grid.nodal_mesh
    absolute_sin_latitude = jnp.abs(sin_latitude)
    zero_sin_latitude = jnp.sin(
        jnp.deg2rad(_EKMAN_COUPLED_EQUATORIAL_ZERO_LATITUDE_DEGREES)
    )
    full_sin_latitude = jnp.sin(
        jnp.deg2rad(_EKMAN_COUPLED_EQUATORIAL_FULL_LATITUDE_DEGREES)
    )
    taper_fraction = jnp.clip(
        (absolute_sin_latitude - zero_sin_latitude)
        / (full_sin_latitude - zero_sin_latitude),
        0.0,
        1.0,
    )
    return taper_fraction * taper_fraction * (3.0 - 2.0 * taper_fraction)


def _analysis_2m_land_skin_temperature(
    initial_state: WeatherState,
    *,
    spatial_shape: tuple[int, int],
    latitude_reversed: bool,
    physics_specs: Any,
) -> jax.Array | None:
    """Return lead-zero T2m in Dinosaur units and latitude order when available."""
    if TWO_METER_TEMPERATURE_VARIABLE not in initial_state.variables:
        return None
    temperature_index = int(
        initial_state.variable_indices((TWO_METER_TEMPERATURE_VARIABLE,))[0]
    )
    analyzed_temperature = initial_state.values[temperature_index]
    if analyzed_temperature.shape != tuple(spatial_shape):
        return None
    analyzed_temperature = analyzed_temperature * _unit_factor(
        physics_specs,
        "kelvin",
    )
    return _to_dinosaur_latitude_order(
        analyzed_temperature,
        latitude_reversed,
    )


def _analysis_2m_initialized_land_skin(
    incumbent_skin: tuple[jax.Array, jax.Array],
    *,
    analyzed_temperature: jax.Array | None,
    land_weight: jax.Array | None,
) -> tuple[jax.Array, jax.Array]:
    """Override valid active-land cells while preserving incumbent fallback cells."""
    incumbent_skin_temperature, incumbent_deep_temperature = incumbent_skin
    expected_shape = incumbent_skin_temperature.shape
    if (
        analyzed_temperature is None
        or land_weight is None
        or incumbent_deep_temperature.shape != expected_shape
        or analyzed_temperature.shape != expected_shape
        or land_weight.shape != expected_shape
    ):
        return incumbent_skin

    analyzed_temperature = jnp.asarray(
        analyzed_temperature,
        dtype=incumbent_skin_temperature.dtype,
    )
    land_weight = jnp.asarray(land_weight, dtype=incumbent_skin_temperature.dtype)
    land_mask_is_valid = (
        jnp.all(jnp.isfinite(land_weight))
        & jnp.all(land_weight >= 0.0)
        & jnp.all(land_weight <= 1.0)
    )
    analysis_cell_is_valid = jnp.isfinite(analyzed_temperature) & (
        analyzed_temperature > 0.0
    )
    active_land_cell = _active_land_skin_weight(land_weight) > 0.0
    use_analysis = land_mask_is_valid & active_land_cell & analysis_cell_is_valid
    return (
        jnp.where(
            use_analysis,
            analyzed_temperature,
            incumbent_skin_temperature,
        ),
        jnp.where(
            use_analysis,
            analyzed_temperature,
            incumbent_deep_temperature,
        ),
    )


def _radiative_land_skin_reference_time(
    initial_times: np.ndarray,
) -> np.datetime64:
    """Return one valid batch reference for dynamic per-sample solar offsets."""
    initial_times = np.asarray(initial_times, dtype="datetime64[ns]")
    valid_indices = np.flatnonzero(~np.isnat(initial_times))
    if valid_indices.size:
        return initial_times[int(valid_indices[0])]
    return np.datetime64(radiation.WB_REFERENCE_DATETIME, "ns")


def _radiative_land_skin_initial_time_offset(
    initial_time: np.datetime64,
    *,
    reference_time: np.datetime64 | None,
    physics_specs: Any,
) -> jax.Array:
    """Return a finite nondimensional offset or NaN for exact fallback."""
    if reference_time is None:
        return jnp.asarray(jnp.nan, dtype=jnp.float32)
    try:
        initial_time = np.asarray(initial_time, dtype="datetime64[ns]")
        reference_time = np.asarray(reference_time, dtype="datetime64[ns]")
        if (
            initial_time.shape
            or reference_time.shape
            or np.isnat(initial_time)
            or np.isnat(reference_time)
        ):
            return jnp.asarray(jnp.nan, dtype=jnp.float32)
        time_offset = np.float32(
            radiation.datetime_to_time(
                initial_time[()],
                physics_specs,
                reference_time[()],
            )
        )
    except (OverflowError, TypeError, ValueError):
        return jnp.asarray(jnp.nan, dtype=jnp.float32)
    if not np.isfinite(time_offset):
        return jnp.asarray(jnp.nan, dtype=jnp.float32)
    return jnp.asarray(time_offset, dtype=jnp.float32)


def _land_skin_reservoir_initial_skin(
    state: Any,
    *,
    coords: coordinate_systems.CoordinateSystem,
    reference_temperature: np.ndarray,
) -> tuple[jax.Array, jax.Array]:
    """Initialize the external skin and deep memory from post-DFI air."""
    lowest_temperature = _lowest_layer_temperature(
        state,
        coords=coords,
        reference_temperature=reference_temperature,
    )
    temperature_is_valid = jnp.all(jnp.isfinite(lowest_temperature)) & jnp.all(
        lowest_temperature > 0.0
    )
    fallback_temperature = jnp.full_like(
        lowest_temperature,
        jnp.asarray(reference_temperature)[-1],
    )
    skin_temperature = jnp.where(
        temperature_is_valid,
        lowest_temperature,
        fallback_temperature,
    )
    return skin_temperature, skin_temperature


def _land_skin_reservoir_step(
    step_fn: Any,
    *,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    reference_temperature: np.ndarray,
    land_weight: jax.Array,
    step_seconds_si: float,
    solar_radiation_model: radiation.SolarRadiation | None = None,
    radiation_time_offset: jax.Array | None = None,
) -> Any:
    """Wrap a rollout step with a late-ramped external land reservoir."""

    def land_skin_step(carry: tuple[Any, tuple[jax.Array, jax.Array]]):
        state, skin = carry
        next_state = step_fn(state)
        if next_state.sim_time is None:
            return next_state, skin
        coupling_weight = _land_skin_reservoir_forecast_time_ramp(
            next_state.sim_time,
            physics_specs,
        )

        def apply_reservoir(
            active_carry: tuple[Any, tuple[jax.Array, jax.Array]],
        ) -> tuple[Any, tuple[jax.Array, jax.Array]]:
            active_state, active_skin = active_carry
            return _apply_land_skin_reservoir_step(
                active_state,
                active_skin,
                coords=coords,
                physics_specs=physics_specs,
                reference_temperature=reference_temperature,
                land_weight=land_weight,
                step_seconds_si=step_seconds_si,
                solar_radiation_model=solar_radiation_model,
                radiation_time_offset=radiation_time_offset,
            )

        return jax.lax.cond(
            coupling_weight > 0.0,
            apply_reservoir,
            lambda inactive_carry: inactive_carry,
            (next_state, skin),
        )

    return land_skin_step


def _apply_land_skin_reservoir_step(
    state: Any,
    skin: tuple[jax.Array, jax.Array],
    *,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    reference_temperature: np.ndarray,
    land_weight: jax.Array,
    step_seconds_si: float,
    deep_restore_days: float = _LAND_SKIN_RESERVOIR_DEEP_RESTORE_DAYS,
    solar_radiation_model: radiation.SolarRadiation | None = None,
    radiation_time_offset: jax.Array | None = None,
) -> tuple[Any, tuple[jax.Array, jax.Array]]:
    """Apply one bounded skin/air exchange after a resolved rollout step."""
    if state.sim_time is None:
        return state, skin

    horizontal_grid = coords.horizontal
    skin_temperature, deep_temperature = skin
    expected_shape = horizontal_grid.nodal_shape
    if (
        skin_temperature.shape != expected_shape
        or deep_temperature.shape != expected_shape
        or land_weight.shape != expected_shape
    ):
        return state, skin

    lowest_temperature = _lowest_layer_temperature(
        state,
        coords=coords,
        reference_temperature=reference_temperature,
    )
    u_wind, v_wind = spherical_harmonic.vor_div_to_uv_nodal(
        horizontal_grid,
        state.vorticity,
        state.divergence,
    )
    coupling_weight = _land_skin_reservoir_forecast_time_ramp(
        state.sim_time,
        physics_specs,
    )
    (
        air_increment,
        skin_exchange_increment,
        skin_restore_increment,
    ) = _land_skin_reservoir_local_increments(
        air_temperature=lowest_temperature,
        skin_temperature=skin_temperature,
        deep_temperature=deep_temperature,
        land_weight=land_weight,
        lowest_u_wind=u_wind[-1],
        lowest_v_wind=v_wind[-1],
        coupling_weight=coupling_weight,
        physics_specs=physics_specs,
        step_seconds_si=step_seconds_si,
        deep_restore_days=deep_restore_days,
    )

    nodal_temperature_increment = (
        jnp.zeros(
            (coords.vertical.layers, *horizontal_grid.nodal_shape),
            dtype=state.temperature_variation.dtype,
        )
        .at[-1]
        .set(air_increment)
    )
    modal_temperature_increment = horizontal_grid.to_modal(nodal_temperature_increment)
    projected_lowest_increment = horizontal_grid.to_nodal(modal_temperature_increment)[
        -1
    ]
    increment_cap = _land_skin_temperature_increment_cap(physics_specs)
    projection_scale = jnp.minimum(
        1.0,
        increment_cap
        / jnp.maximum(jnp.max(jnp.abs(projected_lowest_increment)), 1.0e-30),
    )
    modal_temperature_increment = modal_temperature_increment * projection_scale
    projected_lowest_increment = horizontal_grid.to_nodal(modal_temperature_increment)[
        -1
    ]
    corrected_temperature_variation = (
        state.temperature_variation + modal_temperature_increment
    )
    updated_skin_temperature = (
        skin_temperature
        + skin_exchange_increment * projection_scale
        + skin_restore_increment
    )
    if solar_radiation_model is not None and radiation_time_offset is not None:
        radiative_skin_increment = _zero_mean_radiative_land_skin_increment(
            state=state,
            air_temperature=lowest_temperature,
            skin_temperature=skin_temperature,
            deep_temperature=deep_temperature,
            land_weight=land_weight,
            coupling_weight=coupling_weight,
            coords=coords,
            physics_specs=physics_specs,
            step_seconds_si=step_seconds_si,
            solar_radiation_model=solar_radiation_model,
            radiation_time_offset=radiation_time_offset,
        )
        updated_skin_temperature = updated_skin_temperature + radiative_skin_increment

    finite_diagnostics = jnp.all(
        jnp.asarray(
            [
                jnp.all(jnp.isfinite(lowest_temperature)),
                jnp.all(jnp.isfinite(skin_temperature)),
                jnp.all(jnp.isfinite(deep_temperature)),
                jnp.all(jnp.isfinite(land_weight)),
                jnp.all(jnp.isfinite(u_wind[-1])),
                jnp.all(jnp.isfinite(v_wind[-1])),
                jnp.all(jnp.isfinite(coupling_weight)),
                jnp.all(jnp.isfinite(air_increment)),
                jnp.all(jnp.isfinite(updated_skin_temperature)),
                jnp.all(jnp.isfinite(modal_temperature_increment)),
                jnp.all(jnp.isfinite(projected_lowest_increment)),
                jnp.all(jnp.isfinite(corrected_temperature_variation)),
                jnp.all(land_weight >= 0.0),
                jnp.all(land_weight <= 1.0),
                jnp.all(lowest_temperature > 0.0),
                jnp.all(skin_temperature > 0.0),
                jnp.all(deep_temperature > 0.0),
            ]
        )
    )
    candidate_has_effect = (
        jnp.max(jnp.abs(projected_lowest_increment))
        + jnp.max(jnp.abs(updated_skin_temperature - skin_temperature))
    ) > 0.0
    use_candidate = finite_diagnostics & candidate_has_effect
    corrected_state = _primitive_equation_state(
        vorticity=state.vorticity,
        divergence=state.divergence,
        temperature_variation=jnp.where(
            use_candidate,
            corrected_temperature_variation,
            state.temperature_variation,
        ),
        log_surface_pressure=state.log_surface_pressure,
        tracers=state.tracers,
        sim_time=state.sim_time,
    )
    updated_skin = (
        jnp.where(use_candidate, updated_skin_temperature, skin_temperature),
        deep_temperature,
    )
    return corrected_state, updated_skin


def _land_skin_reservoir_local_increments(
    *,
    air_temperature: jax.Array,
    skin_temperature: jax.Array,
    deep_temperature: jax.Array,
    land_weight: jax.Array,
    lowest_u_wind: jax.Array,
    lowest_v_wind: jax.Array,
    coupling_weight: jax.Array | float,
    physics_specs: Any,
    step_seconds_si: float,
    deep_restore_days: float = _LAND_SKIN_RESERVOIR_DEEP_RESTORE_DAYS,
) -> tuple[jax.Array, jax.Array, jax.Array]:
    """Return conservative air/skin exchange and deep-restore increments."""
    coupling_weight = jnp.asarray(coupling_weight, dtype=air_temperature.dtype)
    active_land_weight = _active_land_skin_weight(land_weight) * jnp.clip(
        coupling_weight, 0.0, 1.0
    )
    exchange_fraction = _land_skin_reservoir_exchange_fraction(
        lowest_u_wind=lowest_u_wind,
        lowest_v_wind=lowest_v_wind,
        physics_specs=physics_specs,
        step_seconds_si=step_seconds_si,
    )
    restore_fraction = _land_skin_reservoir_restore_fraction(
        step_seconds_si=step_seconds_si,
        deep_restore_days=deep_restore_days,
    )
    temperature_difference = skin_temperature - air_temperature
    increment_cap = _land_skin_temperature_increment_cap(physics_specs)
    air_increment = jnp.clip(
        active_land_weight * exchange_fraction * temperature_difference,
        -increment_cap,
        increment_cap,
    )
    skin_exchange_increment = -_LAND_SKIN_RESERVOIR_HEAT_CAPACITY_RATIO * air_increment
    skin_restore_increment = (
        jnp.clip(coupling_weight, 0.0, 1.0)
        * restore_fraction
        * (deep_temperature - skin_temperature)
    )
    finite_diagnostics = jnp.all(
        jnp.asarray(
            [
                jnp.all(jnp.isfinite(air_temperature)),
                jnp.all(jnp.isfinite(skin_temperature)),
                jnp.all(jnp.isfinite(deep_temperature)),
                jnp.all(jnp.isfinite(active_land_weight)),
                jnp.all(jnp.isfinite(lowest_u_wind)),
                jnp.all(jnp.isfinite(lowest_v_wind)),
                jnp.all(jnp.isfinite(coupling_weight)),
                jnp.all(jnp.isfinite(exchange_fraction)),
                jnp.all(jnp.isfinite(restore_fraction)),
                jnp.all(jnp.isfinite(air_increment)),
                jnp.all(jnp.isfinite(skin_exchange_increment)),
                jnp.all(jnp.isfinite(skin_restore_increment)),
                jnp.all(active_land_weight >= 0.0),
                jnp.all(active_land_weight <= 1.0),
                jnp.all(air_temperature > 0.0),
                jnp.all(skin_temperature > 0.0),
                jnp.all(deep_temperature > 0.0),
            ]
        )
    )
    zero_air_increment = jnp.zeros_like(air_increment)
    zero_skin_increment = jnp.zeros_like(skin_exchange_increment)
    return (
        jnp.where(finite_diagnostics, air_increment, zero_air_increment),
        jnp.where(finite_diagnostics, skin_exchange_increment, zero_skin_increment),
        jnp.where(finite_diagnostics, skin_restore_increment, zero_skin_increment),
    )


def _active_land_area_neutral_power(
    power: jax.Array,
    *,
    active_land_weight: jax.Array,
    area_weights: jax.Array,
) -> jax.Array:
    """Center one power field over active land, then apply the land weight."""
    combined_weights = active_land_weight * area_weights
    combined_weight_sum = jnp.sum(combined_weights)
    safe_weight_sum = jnp.where(
        jnp.isfinite(combined_weight_sum) & (combined_weight_sum > 0.0),
        combined_weight_sum,
        jnp.asarray(1.0, dtype=power.dtype),
    )
    weighted_mean = jnp.sum(power * combined_weights) / safe_weight_sum
    weighted_anomaly = active_land_weight * (power - weighted_mean)
    residual_mean = jnp.sum(weighted_anomaly * area_weights) / safe_weight_sum
    return weighted_anomaly - active_land_weight * residual_mean


def _zero_mean_radiative_land_skin_power(
    *,
    toa_radiation_flux_si: jax.Array,
    skin_temperature_si: jax.Array,
    deep_temperature_si: jax.Array,
    active_land_weight: jax.Array,
    area_weights: jax.Array,
) -> tuple[jax.Array, jax.Array]:
    """Return separately centered shortwave and longwave land power in W/m2."""
    shortwave_power = (
        _LAND_SKIN_RADIATIVE_ABSORBED_SHORTWAVE_FRACTION * toa_radiation_flux_si
    )
    longwave_power = _STEFAN_BOLTZMANN_CONSTANT_SI * (
        deep_temperature_si**4 - skin_temperature_si**4
    )
    return (
        _active_land_area_neutral_power(
            shortwave_power,
            active_land_weight=active_land_weight,
            area_weights=area_weights,
        ),
        _active_land_area_neutral_power(
            longwave_power,
            active_land_weight=active_land_weight,
            area_weights=area_weights,
        ),
    )


def _zero_mean_radiative_land_skin_temperature_increment(
    *,
    toa_radiation_flux: jax.Array,
    air_temperature: jax.Array,
    skin_temperature: jax.Array,
    deep_temperature: jax.Array,
    surface_pressure: jax.Array,
    land_weight: jax.Array,
    area_weights: jax.Array,
    lowest_sigma: jax.Array | float,
    coupling_weight: jax.Array | float,
    physics_specs: Any,
    step_seconds_si: float,
) -> jax.Array:
    """Convert zero-net land power to one guarded, commonly capped skin dT."""
    zero_increment = jnp.zeros_like(skin_temperature)
    expected_shape = skin_temperature.shape
    shaped_inputs = (
        toa_radiation_flux,
        air_temperature,
        deep_temperature,
        surface_pressure,
        land_weight,
        area_weights,
    )
    if any(value.shape != expected_shape for value in shaped_inputs):
        return zero_increment

    dtype = skin_temperature.dtype
    toa_radiation_flux = jnp.asarray(toa_radiation_flux, dtype=dtype)
    air_temperature = jnp.asarray(air_temperature, dtype=dtype)
    deep_temperature = jnp.asarray(deep_temperature, dtype=dtype)
    surface_pressure = jnp.asarray(surface_pressure, dtype=dtype)
    land_weight = jnp.asarray(land_weight, dtype=dtype)
    area_weights = jnp.asarray(area_weights, dtype=dtype)
    lowest_sigma = jnp.asarray(lowest_sigma, dtype=dtype)
    coupling_weight = jnp.asarray(coupling_weight, dtype=dtype)
    step_seconds = jnp.asarray(step_seconds_si, dtype=dtype)

    temperature_unit_factor = jnp.asarray(
        _unit_factor(physics_specs, "kelvin"), dtype=dtype
    )
    pressure_unit_factor = jnp.asarray(
        _unit_factor(physics_specs, "pascal"), dtype=dtype
    )
    power_flux_unit_factor = jnp.asarray(
        _unit_factor(physics_specs, "watt / meter ** 2"), dtype=dtype
    )
    specific_heat_unit_factor = jnp.asarray(
        _unit_factor(physics_specs, "joule / kilogram / kelvin"), dtype=dtype
    )
    active_land_weight = _active_land_skin_weight(land_weight).astype(dtype)
    toa_radiation_flux_si = toa_radiation_flux / power_flux_unit_factor
    air_temperature_si = air_temperature / temperature_unit_factor
    skin_temperature_si = skin_temperature / temperature_unit_factor
    deep_temperature_si = deep_temperature / temperature_unit_factor
    lowest_pressure_si = lowest_sigma * surface_pressure / pressure_unit_factor
    density_si = lowest_pressure_si / (
        jnp.asarray(_DRY_AIR_GAS_CONSTANT_SI, dtype=dtype) * air_temperature_si
    )
    cp_si = jnp.asarray(physics_specs.Cp, dtype=dtype) / specific_heat_unit_factor
    skin_heat_capacity_si = (
        density_si
        * cp_si
        * _LAND_SKIN_RESERVOIR_EXCHANGE_DEPTH_METERS
        / _LAND_SKIN_RESERVOIR_HEAT_CAPACITY_RATIO
    )
    shortwave_power, longwave_power = _zero_mean_radiative_land_skin_power(
        toa_radiation_flux_si=toa_radiation_flux_si,
        skin_temperature_si=skin_temperature_si,
        deep_temperature_si=deep_temperature_si,
        active_land_weight=active_land_weight,
        area_weights=area_weights,
    )
    radiative_power = shortwave_power + longwave_power
    raw_increment = (
        jnp.clip(coupling_weight, 0.0, 1.0)
        * radiative_power
        * step_seconds
        / skin_heat_capacity_si
        * temperature_unit_factor
    )
    active_increment_magnitude = jnp.max(
        jnp.where(
            active_land_weight > 0.0,
            jnp.abs(raw_increment),
            jnp.zeros_like(raw_increment),
        )
    )
    increment_cap = _land_skin_temperature_increment_cap(physics_specs).astype(dtype)
    common_scale = jnp.minimum(
        jnp.asarray(1.0, dtype=dtype),
        increment_cap
        / jnp.maximum(active_increment_magnitude, jnp.asarray(1.0e-30, dtype=dtype)),
    )
    capped_increment = raw_increment * common_scale
    active_area_sum = jnp.sum(active_land_weight * area_weights)
    finite_diagnostics = jnp.all(
        jnp.asarray(
            [
                jnp.all(jnp.isfinite(toa_radiation_flux)),
                jnp.all(toa_radiation_flux >= 0.0),
                jnp.all(jnp.isfinite(air_temperature)),
                jnp.all(jnp.isfinite(skin_temperature)),
                jnp.all(jnp.isfinite(deep_temperature)),
                jnp.all(air_temperature > 0.0),
                jnp.all(skin_temperature > 0.0),
                jnp.all(deep_temperature > 0.0),
                jnp.all(jnp.isfinite(surface_pressure)),
                jnp.all(surface_pressure > 0.0),
                jnp.all(jnp.isfinite(land_weight)),
                jnp.all(land_weight >= 0.0),
                jnp.all(land_weight <= 1.0),
                jnp.all(jnp.isfinite(area_weights)),
                jnp.all(area_weights > 0.0),
                jnp.isfinite(active_area_sum),
                active_area_sum > 0.0,
                jnp.isfinite(lowest_sigma),
                lowest_sigma > 0.0,
                jnp.isfinite(coupling_weight),
                coupling_weight >= 0.0,
                coupling_weight <= 1.0,
                jnp.isfinite(step_seconds),
                step_seconds > 0.0,
                jnp.isfinite(temperature_unit_factor),
                temperature_unit_factor > 0.0,
                jnp.isfinite(pressure_unit_factor),
                pressure_unit_factor > 0.0,
                jnp.isfinite(power_flux_unit_factor),
                power_flux_unit_factor > 0.0,
                jnp.isfinite(specific_heat_unit_factor),
                specific_heat_unit_factor > 0.0,
                jnp.isfinite(cp_si),
                cp_si > 0.0,
                jnp.all(jnp.isfinite(lowest_pressure_si)),
                jnp.all(lowest_pressure_si > 0.0),
                jnp.all(jnp.isfinite(density_si)),
                jnp.all(density_si > 0.0),
                jnp.all(jnp.isfinite(skin_heat_capacity_si)),
                jnp.all(skin_heat_capacity_si > 0.0),
                jnp.all(jnp.isfinite(shortwave_power)),
                jnp.all(jnp.isfinite(longwave_power)),
                jnp.all(jnp.isfinite(radiative_power)),
                jnp.all(jnp.isfinite(raw_increment)),
                jnp.isfinite(active_increment_magnitude),
                jnp.isfinite(increment_cap),
                increment_cap > 0.0,
                jnp.isfinite(common_scale),
                jnp.all(jnp.isfinite(capped_increment)),
            ]
        )
    )
    return jnp.where(finite_diagnostics, capped_increment, zero_increment)


def _zero_mean_radiative_land_skin_increment(
    *,
    state: Any,
    air_temperature: jax.Array,
    skin_temperature: jax.Array,
    deep_temperature: jax.Array,
    land_weight: jax.Array,
    coupling_weight: jax.Array | float,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    step_seconds_si: float,
    solar_radiation_model: radiation.SolarRadiation,
    radiation_time_offset: jax.Array,
) -> jax.Array:
    """Evaluate the current per-sample solar phase and guarded skin increment."""
    if state.sim_time is None:
        return jnp.zeros_like(skin_temperature)
    radiation_time_offset = jnp.asarray(
        radiation_time_offset, dtype=skin_temperature.dtype
    )
    sim_time = jnp.asarray(state.sim_time, dtype=skin_temperature.dtype)
    radiation_time = radiation_time_offset + sim_time
    toa_radiation_flux = solar_radiation_model.radiation_flux(radiation_time)
    surface_pressure = jnp.exp(
        coords.horizontal.to_nodal(state.log_surface_pressure)[0]
    )
    increment = _zero_mean_radiative_land_skin_temperature_increment(
        toa_radiation_flux=toa_radiation_flux,
        air_temperature=air_temperature,
        skin_temperature=skin_temperature,
        deep_temperature=deep_temperature,
        surface_pressure=surface_pressure,
        land_weight=land_weight,
        area_weights=jnp.asarray(coords.horizontal.quadrature_weights),
        lowest_sigma=jnp.asarray(coords.vertical.centers)[-1],
        coupling_weight=coupling_weight,
        physics_specs=physics_specs,
        step_seconds_si=step_seconds_si,
    )
    valid_time = (
        jnp.all(jnp.isfinite(radiation_time_offset))
        & jnp.all(jnp.isfinite(sim_time))
        & jnp.all(jnp.isfinite(radiation_time))
    )
    return jnp.where(valid_time, increment, jnp.zeros_like(increment))


def _lowest_layer_temperature(
    state: Any,
    *,
    coords: coordinate_systems.CoordinateSystem,
    reference_temperature: np.ndarray,
) -> jax.Array:
    """Return absolute lowest-layer temperature on the nodal grid."""
    return (
        coords.horizontal.to_nodal(state.temperature_variation)[-1]
        + jnp.asarray(reference_temperature)[-1]
    )


def _active_land_skin_weight(land_weight: jax.Array) -> jax.Array:
    """Mask numerical ocean points while retaining fractional land cells."""
    land_weight = jnp.asarray(land_weight, dtype=jnp.float32)
    return jnp.where(
        land_weight >= _LAND_SKIN_RESERVOIR_MIN_LAND_FRACTION,
        jnp.clip(land_weight, 0.0, 1.0),
        0.0,
    )


def _land_skin_reservoir_exchange_fraction(
    *,
    lowest_u_wind: jax.Array,
    lowest_v_wind: jax.Array,
    physics_specs: Any,
    step_seconds_si: float,
) -> jax.Array:
    """Return the wind-scaled, capped air-skin exchange fraction."""
    wind_unit_factor = _unit_factor(physics_specs, "meter / second")
    lowest_u_wind_si = lowest_u_wind / wind_unit_factor
    lowest_v_wind_si = lowest_v_wind / wind_unit_factor
    wind_speed_si = _sqrt_nonnegative_with_finite_gradient(
        lowest_u_wind_si**2 + lowest_v_wind_si**2
    )
    wind_exchange_fraction = (
        _LAND_SKIN_RESERVOIR_TRANSFER_COEFFICIENT
        * wind_speed_si
        * step_seconds_si
        / _LAND_SKIN_RESERVOIR_EXCHANGE_DEPTH_METERS
    )
    max_exchange_fraction = step_seconds_si / (
        _LAND_SKIN_RESERVOIR_MIN_EFOLDING_HOURS * 3600.0
    )
    return jnp.clip(
        jnp.minimum(wind_exchange_fraction, max_exchange_fraction),
        0.0,
        1.0,
    )


def _land_skin_reservoir_restore_fraction(
    *,
    step_seconds_si: float,
    deep_restore_days: float,
) -> jax.Array:
    """Return the explicit deep-reservoir restore fraction."""
    if np.isinf(deep_restore_days):
        return jnp.asarray(0.0, dtype=jnp.float32)
    assert deep_restore_days > 0.0
    return jnp.asarray(
        np.clip(
            step_seconds_si / (float(deep_restore_days) * 24.0 * 3600.0),
            0.0,
            1.0,
        ),
        dtype=jnp.float32,
    )


def _land_skin_temperature_increment_cap(physics_specs: Any) -> jax.Array:
    """Return the per-step lowest-layer temperature increment cap."""
    return jnp.asarray(
        _LAND_SKIN_RESERVOIR_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN
        * _unit_factor(physics_specs, "kelvin"),
        dtype=jnp.float32,
    )


def _land_skin_reservoir_forecast_time_ramp(
    sim_time: jax.Array,
    physics_specs: Any,
) -> jax.Array:
    """Return a smooth ramp that is zero through 120 h and full at 240 h."""
    sim_time = jnp.asarray(sim_time)
    ramp_start_time = _nondimensionalize_seconds(
        physics_specs,
        _LAND_SKIN_RESERVOIR_RAMP_START_HOURS * 3600.0,
    )
    ramp_full_time = _nondimensionalize_seconds(
        physics_specs,
        _LAND_SKIN_RESERVOIR_RAMP_FULL_HOURS * 3600.0,
    )
    ramp_fraction = jnp.clip(
        (sim_time - jnp.asarray(ramp_start_time, dtype=sim_time.dtype))
        / jnp.asarray(ramp_full_time - ramp_start_time, dtype=sim_time.dtype),
        0.0,
        1.0,
    )
    smooth_weight = ramp_fraction * ramp_fraction * (3.0 - 2.0 * ramp_fraction)
    return jnp.where(
        sim_time <= ramp_start_time,
        0.0,
        jnp.where(sim_time >= ramp_full_time, 1.0, smooth_weight),
    )


def _orographic_lift_theta_tendency_step_filter(
    *,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    reference_temperature: np.ndarray,
    terrain_height_meters: jax.Array | None,
    step_seconds: float,
    use_depth_weighted_wind: bool = False,
) -> Any:
    """Return a thermal-only orographic lift filter for positive forecast times."""
    assert step_seconds > 0.0
    horizontal_grid = coords.horizontal
    terrain_height = _valid_terrain_height_or_none(
        terrain_height_meters,
        horizontal_grid.nodal_shape,
    )
    if terrain_height is None:

        def no_orographic_lift_filter(prev_state: Any, next_state: Any) -> Any:
            del prev_state
            return next_state

        return no_orographic_lift_filter

    length_unit_factor = _unit_factor(physics_specs, "meter")
    wind_unit_factor = _unit_factor(physics_specs, "meter / second")
    temperature_unit_factor = _unit_factor(physics_specs, "kelvin")
    terrain_height = jnp.asarray(terrain_height, dtype=jnp.float32) * length_unit_factor
    low_mode_mask = _orographic_lift_low_mode_mask(horizontal_grid)
    smoothed_terrain = horizontal_grid.to_nodal(
        horizontal_grid.to_modal(terrain_height) * low_mode_mask
    )
    terrain_gradient = _terrain_gradient(horizontal_grid, smoothed_terrain)
    sigma_envelope = _orographic_lift_sigma_envelope(coords.vertical)
    latitude_envelope = _orographic_lift_equatorial_taper(horizontal_grid)
    quadrature_weights = jnp.asarray(horizontal_grid.quadrature_weights)
    reference_temperature = jnp.asarray(reference_temperature)
    reference_pressure = _unit_factor(physics_specs, "pascal") * 100_000.0
    temperature_increment_cap = (
        _OROGRAPHIC_LIFT_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN * temperature_unit_factor
    )

    def orographic_lift_filter(prev_state: Any, next_state: Any) -> Any:
        del prev_state
        if next_state.sim_time is None:
            return next_state

        ramp = _orographic_lift_forecast_time_ramp(
            next_state.sim_time,
            physics_specs,
        )
        u_wind, v_wind = spherical_harmonic.vor_div_to_uv_nodal(
            horizontal_grid,
            next_state.vorticity,
            next_state.divergence,
        )
        lowest_u_wind = u_wind[-1]
        lowest_v_wind = v_wind[-1]
        if use_depth_weighted_wind:
            effective_u_wind, effective_v_wind = (
                _orographic_lift_lower_column_weighted_wind(
                    u_wind=u_wind,
                    v_wind=v_wind,
                    sigma_envelope=sigma_envelope,
                )
            )
        else:
            effective_u_wind = lowest_u_wind
            effective_v_wind = lowest_v_wind
        wind_speed = _sqrt_nonnegative_with_finite_gradient(
            effective_u_wind**2 + effective_v_wind**2
        )
        weak_flow_taper = jnp.clip(
            wind_speed
            / (_OROGRAPHIC_LIFT_WEAK_FLOW_FULL_METERS_PER_SECOND * wind_unit_factor),
            0.0,
            1.0,
        )
        weak_flow_taper = (
            weak_flow_taper * weak_flow_taper * (3.0 - 2.0 * weak_flow_taper)
        )
        w_terrain = (
            effective_u_wind * terrain_gradient[0]
            + effective_v_wind * terrain_gradient[1]
        )
        w_terrain = w_terrain * latitude_envelope * weak_flow_taper * ramp

        nodal_temperature = (
            horizontal_grid.to_nodal(next_state.temperature_variation)
            + reference_temperature[:, jnp.newaxis, jnp.newaxis]
        )
        surface_pressure = jnp.exp(
            horizontal_grid.to_nodal(next_state.log_surface_pressure)[0]
        )
        theta = _orographic_lift_potential_temperature(
            temperature=nodal_temperature,
            surface_pressure=surface_pressure,
            sigma_centers=jnp.asarray(coords.vertical.centers),
            reference_pressure=reference_pressure,
            kappa=physics_specs.kappa,
        )
        height = _orographic_lift_layer_height(
            temperature=nodal_temperature,
            sigma_centers=jnp.asarray(coords.vertical.centers),
            gas_constant=physics_specs.R,
            gravity=physics_specs.g,
        )
        dtheta_dz = _vertical_derivative(theta, height)
        raw_temperature_increment = (
            -step_seconds
            * w_terrain[jnp.newaxis, ...]
            * dtheta_dz
            * sigma_envelope[:, jnp.newaxis, jnp.newaxis]
        )
        temperature_increment = jax.vmap(
            lambda layer_increment: _bounded_area_neutral_field(
                layer_increment,
                temperature_increment_cap,
                quadrature_weights,
            )
        )(raw_temperature_increment)
        modal_temperature_increment = horizontal_grid.to_modal(temperature_increment)
        projected_temperature_increment = horizontal_grid.to_nodal(
            modal_temperature_increment
        )
        projected_increment_max = jnp.max(jnp.abs(projected_temperature_increment))
        projection_scale = jnp.minimum(
            1.0,
            temperature_increment_cap / jnp.maximum(projected_increment_max, 1.0e-30),
        )
        temperature_increment = projected_temperature_increment * projection_scale
        modal_temperature_increment = modal_temperature_increment * projection_scale
        corrected_temperature_variation = (
            next_state.temperature_variation + modal_temperature_increment
        )
        finite_diagnostics = jnp.all(
            jnp.asarray(
                [
                    jnp.all(jnp.isfinite(smoothed_terrain)),
                    jnp.all(jnp.isfinite(terrain_gradient[0])),
                    jnp.all(jnp.isfinite(terrain_gradient[1])),
                    jnp.all(jnp.isfinite(sigma_envelope)),
                    jnp.all(jnp.isfinite(latitude_envelope)),
                    jnp.all(jnp.isfinite(lowest_u_wind)),
                    jnp.all(jnp.isfinite(lowest_v_wind)),
                    jnp.all(jnp.isfinite(effective_u_wind)),
                    jnp.all(jnp.isfinite(effective_v_wind)),
                    jnp.all(jnp.isfinite(wind_speed)),
                    jnp.all(jnp.isfinite(w_terrain)),
                    jnp.all(jnp.isfinite(nodal_temperature)),
                    jnp.all(jnp.isfinite(surface_pressure)),
                    jnp.all(surface_pressure > 0.0),
                    jnp.all(nodal_temperature > 0.0),
                    jnp.all(jnp.isfinite(theta)),
                    jnp.all(jnp.isfinite(height)),
                    jnp.all(jnp.isfinite(dtheta_dz)),
                    jnp.all(jnp.isfinite(raw_temperature_increment)),
                    jnp.all(jnp.isfinite(projected_temperature_increment)),
                    jnp.isfinite(projection_scale),
                    jnp.all(jnp.isfinite(temperature_increment)),
                    jnp.all(jnp.isfinite(corrected_temperature_variation)),
                    jnp.isfinite(ramp),
                ]
            )
        )
        candidate_has_effect = jnp.max(jnp.abs(temperature_increment)) > 0.0
        use_candidate = finite_diagnostics & candidate_has_effect
        return _primitive_equation_state(
            vorticity=next_state.vorticity,
            divergence=next_state.divergence,
            temperature_variation=jnp.where(
                use_candidate,
                corrected_temperature_variation,
                next_state.temperature_variation,
            ),
            log_surface_pressure=next_state.log_surface_pressure,
            tracers=next_state.tracers,
            sim_time=next_state.sim_time,
        )

    return orographic_lift_filter


def _orographic_lift_lower_column_weighted_wind(
    *,
    u_wind: jax.Array,
    v_wind: jax.Array,
    sigma_envelope: jax.Array,
) -> tuple[jax.Array, jax.Array]:
    """Return shallow lower-column terrain-lift wind with lowest-layer fallback."""
    lowest_u_wind = u_wind[-1]
    lowest_v_wind = v_wind[-1]
    layer_count = u_wind.shape[0]
    if layer_count < 2:
        return lowest_u_wind, lowest_v_wind

    selected_layer_count = min(
        layer_count,
        len(_OROGRAPHIC_LIFT_LOWER_COLUMN_WIND_WEIGHTS),
    )
    lower_column_profile = np.zeros(layer_count, dtype=np.float32)
    lower_column_profile[-selected_layer_count:] = np.asarray(
        _OROGRAPHIC_LIFT_LOWER_COLUMN_WIND_WEIGHTS[-selected_layer_count:],
        dtype=np.float32,
    )
    layer_weights = jnp.asarray(lower_column_profile, dtype=u_wind.dtype) * jnp.asarray(
        sigma_envelope,
        dtype=u_wind.dtype,
    )
    finite_layer_weights = jnp.isfinite(layer_weights) & (layer_weights > 0.0)
    finite_winds = jnp.isfinite(u_wind) & jnp.isfinite(v_wind)
    valid_weights = jnp.where(
        finite_layer_weights[:, jnp.newaxis, jnp.newaxis] & finite_winds,
        layer_weights[:, jnp.newaxis, jnp.newaxis],
        0.0,
    )
    weight_sum = jnp.sum(valid_weights, axis=0)
    degenerate_weights = weight_sum <= jnp.finfo(u_wind.dtype).tiny
    safe_weight_sum = jnp.where(
        degenerate_weights,
        jnp.ones_like(weight_sum),
        weight_sum,
    )
    weighted_u_wind = (
        jnp.sum(jnp.where(finite_winds, u_wind, 0.0) * valid_weights, axis=0)
        / safe_weight_sum
    )
    weighted_v_wind = (
        jnp.sum(jnp.where(finite_winds, v_wind, 0.0) * valid_weights, axis=0)
        / safe_weight_sum
    )
    valid_weighted_wind = (
        ~degenerate_weights
        & jnp.isfinite(weighted_u_wind)
        & jnp.isfinite(weighted_v_wind)
    )
    return (
        jnp.where(valid_weighted_wind, weighted_u_wind, lowest_u_wind),
        jnp.where(valid_weighted_wind, weighted_v_wind, lowest_v_wind),
    )


def _terrain_work_form_drag_heating_step_filter(
    *,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    terrain_height_meters: jax.Array | None,
    step_seconds: float,
) -> Any:
    """Return a lower-column terrain-work drag filter with neutral heat return."""
    assert step_seconds > 0.0
    horizontal_grid = coords.horizontal
    terrain_height = _valid_terrain_height_or_none(
        terrain_height_meters,
        horizontal_grid.nodal_shape,
    )
    if terrain_height is None:

        def no_terrain_work_drag_filter(prev_state: Any, next_state: Any) -> Any:
            del prev_state
            return next_state

        return no_terrain_work_drag_filter

    length_unit_factor = _unit_factor(physics_specs, "meter")
    wind_unit_factor = _unit_factor(physics_specs, "meter / second")
    temperature_unit_factor = _unit_factor(physics_specs, "kelvin")
    terrain_height = jnp.asarray(terrain_height, dtype=jnp.float32) * length_unit_factor
    low_mode_mask = _orographic_lift_low_mode_mask(horizontal_grid)
    smoothed_terrain = horizontal_grid.to_nodal(
        horizontal_grid.to_modal(terrain_height) * low_mode_mask
    )
    terrain_gradient = _terrain_gradient(horizontal_grid, smoothed_terrain)
    sigma_envelope = _orographic_lift_sigma_envelope(coords.vertical)
    latitude_envelope = _orographic_lift_equatorial_taper(horizontal_grid)
    lower_column_weights = _terrain_work_form_drag_lower_column_weights(
        coords.vertical,
        dtype=jnp.float32,
    )
    quadrature_weights = jnp.asarray(horizontal_grid.quadrature_weights)
    terrain_work_full = (
        _TERRAIN_WORK_FORM_DRAG_WORK_FULL_METERS_PER_SECOND * wind_unit_factor
    )
    wind_increment_cap = (
        _TERRAIN_WORK_FORM_DRAG_MAX_WIND_STEP_INCREMENT_METERS_PER_SECOND
        * wind_unit_factor
    )
    heat_increment_cap = (
        _TERRAIN_WORK_FORM_DRAG_MAX_HEAT_INCREMENT_KELVIN * temperature_unit_factor
    )

    def terrain_work_form_drag_filter(prev_state: Any, next_state: Any) -> Any:
        del prev_state
        if next_state.sim_time is None:
            return next_state

        ramp = _orographic_lift_forecast_time_ramp(
            next_state.sim_time,
            physics_specs,
        )
        u_wind, v_wind = spherical_harmonic.vor_div_to_uv_nodal(
            horizontal_grid,
            next_state.vorticity,
            next_state.divergence,
        )
        effective_u_wind, effective_v_wind = (
            _orographic_lift_lower_column_weighted_wind(
                u_wind=u_wind,
                v_wind=v_wind,
                sigma_envelope=sigma_envelope,
            )
        )
        wind_speed = _sqrt_nonnegative_with_finite_gradient(
            effective_u_wind**2 + effective_v_wind**2
        )
        weak_flow_taper = _smooth_unit_ramp(
            wind_speed
            / (_OROGRAPHIC_LIFT_WEAK_FLOW_FULL_METERS_PER_SECOND * wind_unit_factor)
        )
        w_terrain = (
            effective_u_wind * terrain_gradient[0]
            + effective_v_wind * terrain_gradient[1]
        )
        w_terrain = w_terrain * latitude_envelope * weak_flow_taper * ramp
        slope_magnitude = _sqrt_nonnegative_with_finite_gradient(
            terrain_gradient[0] ** 2 + terrain_gradient[1] ** 2
        )
        slope_taper = _smooth_unit_ramp(
            slope_magnitude / _TERRAIN_WORK_FORM_DRAG_SLOPE_FULL
        )
        terrain_work_taper = _smooth_unit_ramp(jnp.abs(w_terrain) / terrain_work_full)
        drag_fraction = (
            _TERRAIN_WORK_FORM_DRAG_MAX_WIND_FRACTION * slope_taper * terrain_work_taper
        )
        lower_column_drag = (
            lower_column_weights[:, jnp.newaxis, jnp.newaxis]
            * sigma_envelope[:, jnp.newaxis, jnp.newaxis]
            * drag_fraction[jnp.newaxis, ...]
        )
        raw_u_increment = -lower_column_drag * u_wind
        raw_v_increment = -lower_column_drag * v_wind
        u_increment = _cap_vector_increment_without_reversal(
            wind_component=u_wind,
            raw_increment=raw_u_increment,
            cap=wind_increment_cap,
        )
        v_increment = _cap_vector_increment_without_reversal(
            wind_component=v_wind,
            raw_increment=raw_v_increment,
            cap=wind_increment_cap,
        )
        vorticity_increment, divergence_increment = (
            spherical_harmonic.uv_nodal_to_vor_div_modal(
                horizontal_grid,
                u_increment,
                v_increment,
            )
        )
        projected_u_increment, projected_v_increment = (
            spherical_harmonic.vor_div_to_uv_nodal(
                horizontal_grid,
                vorticity_increment,
                divergence_increment,
            )
        )
        projected_wind_increment_max = jnp.maximum(
            jnp.max(jnp.abs(projected_u_increment)),
            jnp.max(jnp.abs(projected_v_increment)),
        )
        wind_projection_scale = jnp.minimum(
            1.0,
            0.95
            * wind_increment_cap
            / jnp.maximum(projected_wind_increment_max, 1.0e-30),
        )
        vorticity_increment = vorticity_increment * wind_projection_scale
        divergence_increment = divergence_increment * wind_projection_scale
        projected_u_increment, projected_v_increment = (
            spherical_harmonic.vor_div_to_uv_nodal(
                horizontal_grid,
                vorticity_increment,
                divergence_increment,
            )
        )
        u_after_drag = u_wind + projected_u_increment
        v_after_drag = v_wind + projected_v_increment
        kinetic_energy_loss = 0.5 * jnp.maximum(
            u_wind**2 + v_wind**2 - u_after_drag**2 - v_after_drag**2,
            0.0,
        )
        raw_temperature_increment = (
            _TERRAIN_WORK_FORM_DRAG_HEAT_RETURN_FRACTION
            * kinetic_energy_loss
            / physics_specs.Cp
            * sigma_envelope[:, jnp.newaxis, jnp.newaxis]
        )
        temperature_increment = jax.vmap(
            lambda layer_increment: _bounded_area_neutral_field(
                layer_increment,
                heat_increment_cap,
                quadrature_weights,
            )
        )(raw_temperature_increment)
        modal_temperature_increment = horizontal_grid.to_modal(temperature_increment)
        projected_temperature_increment = horizontal_grid.to_nodal(
            modal_temperature_increment
        )
        projected_temperature_increment_max = jnp.max(
            jnp.abs(projected_temperature_increment)
        )
        heat_projection_scale = jnp.minimum(
            1.0,
            heat_increment_cap
            / jnp.maximum(projected_temperature_increment_max, 1.0e-30),
        )
        modal_temperature_increment = (
            modal_temperature_increment * heat_projection_scale
        )
        projected_temperature_increment = (
            projected_temperature_increment * heat_projection_scale
        )
        corrected_vorticity = next_state.vorticity + vorticity_increment
        corrected_divergence = next_state.divergence + divergence_increment
        corrected_temperature_variation = (
            next_state.temperature_variation + modal_temperature_increment
        )
        finite_diagnostics = jnp.all(
            jnp.asarray(
                [
                    jnp.all(jnp.isfinite(smoothed_terrain)),
                    jnp.all(jnp.isfinite(terrain_gradient[0])),
                    jnp.all(jnp.isfinite(terrain_gradient[1])),
                    jnp.all(jnp.isfinite(sigma_envelope)),
                    jnp.all(jnp.isfinite(latitude_envelope)),
                    jnp.all(jnp.isfinite(lower_column_weights)),
                    jnp.all(jnp.isfinite(u_wind)),
                    jnp.all(jnp.isfinite(v_wind)),
                    jnp.all(jnp.isfinite(effective_u_wind)),
                    jnp.all(jnp.isfinite(effective_v_wind)),
                    jnp.all(jnp.isfinite(wind_speed)),
                    jnp.all(jnp.isfinite(w_terrain)),
                    jnp.all(jnp.isfinite(slope_magnitude)),
                    jnp.all(jnp.isfinite(drag_fraction)),
                    jnp.all(jnp.isfinite(raw_u_increment)),
                    jnp.all(jnp.isfinite(raw_v_increment)),
                    jnp.all(jnp.isfinite(projected_u_increment)),
                    jnp.all(jnp.isfinite(projected_v_increment)),
                    jnp.all(jnp.isfinite(kinetic_energy_loss)),
                    jnp.all(jnp.isfinite(raw_temperature_increment)),
                    jnp.all(jnp.isfinite(projected_temperature_increment)),
                    jnp.all(jnp.isfinite(corrected_vorticity)),
                    jnp.all(jnp.isfinite(corrected_divergence)),
                    jnp.all(jnp.isfinite(corrected_temperature_variation)),
                    jnp.isfinite(wind_projection_scale),
                    jnp.isfinite(heat_projection_scale),
                    jnp.isfinite(ramp),
                ]
            )
        )
        candidate_has_effect = (
            jnp.max(jnp.abs(projected_u_increment))
            + jnp.max(jnp.abs(projected_v_increment))
            + jnp.max(jnp.abs(projected_temperature_increment))
        ) > 0.0
        use_candidate = finite_diagnostics & candidate_has_effect
        return _primitive_equation_state(
            vorticity=jnp.where(
                use_candidate,
                corrected_vorticity,
                next_state.vorticity,
            ),
            divergence=jnp.where(
                use_candidate,
                corrected_divergence,
                next_state.divergence,
            ),
            temperature_variation=jnp.where(
                use_candidate,
                corrected_temperature_variation,
                next_state.temperature_variation,
            ),
            log_surface_pressure=next_state.log_surface_pressure,
            tracers=next_state.tracers,
            sim_time=next_state.sim_time,
        )

    return terrain_work_form_drag_filter


def _terrain_work_form_drag_lower_column_weights(
    vertical_coords: sigma_coordinates.SigmaCoordinates,
    *,
    dtype: Any,
) -> jax.Array:
    """Return lower-column terrain-work drag weights using the lift wind profile."""
    layer_count = vertical_coords.layers
    selected_layer_count = min(
        layer_count,
        len(_OROGRAPHIC_LIFT_LOWER_COLUMN_WIND_WEIGHTS),
    )
    weight_profile = np.zeros(layer_count, dtype=np.float32)
    weight_profile[-selected_layer_count:] = np.asarray(
        _OROGRAPHIC_LIFT_LOWER_COLUMN_WIND_WEIGHTS[-selected_layer_count:],
        dtype=np.float32,
    )
    weight_sum = np.sum(weight_profile)
    if weight_sum > 0.0:
        weight_profile = weight_profile / weight_sum
    return jnp.asarray(weight_profile, dtype=dtype)


def _cap_vector_increment_without_reversal(
    *,
    wind_component: jax.Array,
    raw_increment: jax.Array,
    cap: jax.Array,
) -> jax.Array:
    """Limit component drag so it stays below the local wind and fixed cap."""
    same_direction_as_drag = raw_increment * wind_component <= 0.0
    reversal_cap = jnp.maximum(jnp.abs(wind_component) * 0.95, 0.0)
    bounded_component_cap = jnp.minimum(cap, reversal_cap)
    clipped_increment = jnp.clip(
        raw_increment,
        -bounded_component_cap,
        bounded_component_cap,
    )
    return jnp.where(same_direction_as_drag, clipped_increment, 0.0)


def _smooth_unit_ramp(value: jax.Array) -> jax.Array:
    """Return a smoothstep ramp over [0, 1]."""
    ramp = jnp.clip(value, 0.0, 1.0)
    return ramp * ramp * (3.0 - 2.0 * ramp)


def _valid_terrain_height_or_none(
    terrain_height_meters: jax.Array | None,
    spatial_shape: tuple[int, int],
) -> jax.Array | None:
    """Return finite terrain height matching the Dinosaur grid or `None`."""
    if terrain_height_meters is None:
        return None
    try:
        candidate = np.asarray(jax.device_get(terrain_height_meters), dtype=np.float32)
    except Exception:
        return None
    if candidate.shape != tuple(spatial_shape):
        return None
    if candidate.size == 0:
        return None
    if not bool(np.isfinite(candidate).all()):
        return None
    candidate.setflags(write=False)
    return jnp.asarray(candidate, dtype=jnp.float32)


def _terrain_gradient(
    horizontal_grid: spherical_harmonic.Grid,
    terrain_height: jax.Array,
) -> tuple[jax.Array, jax.Array]:
    """Return nodal eastward and northward terrain slopes."""
    modal_terrain = horizontal_grid.to_modal(terrain_height)
    cos_lat_gradient = horizontal_grid.cos_lat_grad(modal_terrain)
    tiny_cos_lat = jnp.asarray(1.0e-6, dtype=terrain_height.dtype)
    safe_cos_lat = jnp.where(
        horizontal_grid.cos_lat >= 0.0,
        jnp.maximum(horizontal_grid.cos_lat, tiny_cos_lat),
        jnp.minimum(horizontal_grid.cos_lat, -tiny_cos_lat),
    )
    return (
        horizontal_grid.to_nodal(cos_lat_gradient[0]) / safe_cos_lat,
        horizontal_grid.to_nodal(cos_lat_gradient[1]) / safe_cos_lat,
    )


def _orographic_lift_potential_temperature(
    *,
    temperature: jax.Array,
    surface_pressure: jax.Array,
    sigma_centers: jax.Array,
    reference_pressure: float,
    kappa: float,
) -> jax.Array:
    """Return dry potential temperature on sigma layers."""
    pressure = sigma_centers[:, jnp.newaxis, jnp.newaxis] * surface_pressure
    safe_pressure = jnp.maximum(pressure, jnp.finfo(temperature.dtype).tiny)
    return temperature * (reference_pressure / safe_pressure) ** kappa


def _orographic_lift_layer_height(
    *,
    temperature: jax.Array,
    sigma_centers: jax.Array,
    gas_constant: float,
    gravity: float,
) -> jax.Array:
    """Return a hydrostatic layer height proxy above the lower boundary."""
    sigma = jnp.maximum(
        sigma_centers[:, jnp.newaxis, jnp.newaxis],
        jnp.finfo(temperature.dtype).tiny,
    )
    return (gas_constant * temperature / gravity) * jnp.log(1.0 / sigma)


def _vertical_derivative(field: jax.Array, coordinate: jax.Array) -> jax.Array:
    """Differentiate layer fields along the leading vertical axis."""
    if field.shape[0] < 2:
        return jnp.zeros_like(field)
    coordinate_difference = coordinate[1:] - coordinate[:-1]
    safe_difference = jnp.where(
        jnp.abs(coordinate_difference) > jnp.finfo(field.dtype).tiny,
        coordinate_difference,
        jnp.where(coordinate_difference >= 0.0, 1.0, -1.0)
        * jnp.finfo(field.dtype).tiny,
    )
    layer_derivative = (field[1:] - field[:-1]) / safe_difference
    if field.shape[0] == 2:
        return jnp.concatenate([layer_derivative[:1], layer_derivative[-1:]], axis=0)
    return jnp.concatenate(
        [
            layer_derivative[:1],
            0.5 * (layer_derivative[1:] + layer_derivative[:-1]),
            layer_derivative[-1:],
        ],
        axis=0,
    )


def _orographic_lift_forecast_time_ramp(
    sim_time: jax.Array,
    physics_specs: Any,
) -> jax.Array:
    """Return a raised-cosine ramp that is full after 48 forecast hours."""
    full_time = _nondimensionalize_seconds(
        physics_specs,
        _OROGRAPHIC_LIFT_RAMP_FULL_HOURS * 3600.0,
    )
    ramp_fraction = jnp.clip(
        sim_time / jnp.asarray(full_time, dtype=sim_time.dtype), 0.0, 1.0
    )
    return 0.5 * (1.0 - jnp.cos(jnp.pi * ramp_fraction))


def _orographic_lift_sigma_envelope(
    vertical_coords: sigma_coordinates.SigmaCoordinates,
) -> jax.Array:
    """Return the lower/mid-tropospheric envelope for terrain-lift heating."""
    sigma = jnp.asarray(vertical_coords.centers)
    upper_fraction = jnp.clip(
        (sigma - _OROGRAPHIC_LIFT_SIGMA_ZERO_TOP)
        / (_OROGRAPHIC_LIFT_SIGMA_FULL_TOP - _OROGRAPHIC_LIFT_SIGMA_ZERO_TOP),
        0.0,
        1.0,
    )
    lower_fraction = jnp.clip(
        (_OROGRAPHIC_LIFT_SIGMA_ZERO_BOTTOM - sigma)
        / (_OROGRAPHIC_LIFT_SIGMA_ZERO_BOTTOM - _OROGRAPHIC_LIFT_SIGMA_FULL_BOTTOM),
        0.0,
        1.0,
    )
    upper_taper = 0.5 * (1.0 - jnp.cos(jnp.pi * upper_fraction))
    lower_taper = 0.5 * (1.0 - jnp.cos(jnp.pi * lower_fraction))
    return jnp.where(
        (sigma >= _OROGRAPHIC_LIFT_SIGMA_FULL_TOP)
        & (sigma <= _OROGRAPHIC_LIFT_SIGMA_FULL_BOTTOM),
        1.0,
        upper_taper * lower_taper,
    )


def _orographic_lift_equatorial_taper(
    horizontal_grid: spherical_harmonic.Grid,
) -> jax.Array:
    """Return a smooth taper that suppresses terrain lift near the equator."""
    _, sin_latitude = horizontal_grid.nodal_mesh
    absolute_sin_latitude = jnp.abs(sin_latitude)
    zero_sin_latitude = jnp.sin(
        jnp.deg2rad(_OROGRAPHIC_LIFT_EQUATORIAL_ZERO_LATITUDE_DEGREES)
    )
    full_sin_latitude = jnp.sin(
        jnp.deg2rad(_OROGRAPHIC_LIFT_EQUATORIAL_FULL_LATITUDE_DEGREES)
    )
    taper_fraction = jnp.clip(
        (absolute_sin_latitude - zero_sin_latitude)
        / (full_sin_latitude - zero_sin_latitude),
        0.0,
        1.0,
    )
    return taper_fraction * taper_fraction * (3.0 - 2.0 * taper_fraction)


def _orographic_lift_low_mode_mask(
    horizontal_grid: spherical_harmonic.Grid,
) -> jax.Array:
    """Return the fixed terrain taper: full through wavenumber 12, zero by 20."""
    _, total_wavenumber = horizontal_grid.modal_mesh
    total_wavenumber = jnp.asarray(total_wavenumber, dtype=jnp.float32)
    transition = jnp.clip(
        (total_wavenumber - _OROGRAPHIC_LIFT_LOW_MODE_CUTOFF)
        / (_OROGRAPHIC_LIFT_TAPER_ZERO_MODE - _OROGRAPHIC_LIFT_LOW_MODE_CUTOFF),
        0.0,
        1.0,
    )
    taper = 0.5 * (1.0 + jnp.cos(jnp.pi * transition))
    return jnp.where(
        total_wavenumber <= _OROGRAPHIC_LIFT_LOW_MODE_CUTOFF,
        1.0,
        jnp.where(total_wavenumber >= _OROGRAPHIC_LIFT_TAPER_ZERO_MODE, 0.0, taper),
    ) * jnp.asarray(horizontal_grid.mask, dtype=jnp.float32)


def _area_weighted_mean(nodal_field: jax.Array, weights: jax.Array) -> jax.Array:
    """Return the horizontal area mean over the final two axes."""
    return jnp.sum(nodal_field * weights, axis=(-2, -1)) / jnp.sum(weights)


def _bounded_area_neutral_field(
    nodal_field: jax.Array,
    cap: jax.Array,
    weights: jax.Array,
) -> jax.Array:
    """Project a nodal field into a bounded, area-neutral perturbation."""
    cap = jnp.asarray(jnp.maximum(cap, 0.0), dtype=nodal_field.dtype)
    centered_field = nodal_field - _area_weighted_mean(nodal_field, weights)
    centered_field_is_bounded = jnp.max(jnp.abs(centered_field)) <= cap
    lower_offset = jnp.min(nodal_field) - cap
    upper_offset = jnp.max(nodal_field) + cap

    def bisection_step(_, offsets):
        lower, upper = offsets
        midpoint = 0.5 * (lower + upper)
        trial = jnp.clip(nodal_field - midpoint, -cap, cap)
        trial_mean = _area_weighted_mean(trial, weights)
        lower = jnp.where(trial_mean > 0.0, midpoint, lower)
        upper = jnp.where(trial_mean > 0.0, upper, midpoint)
        return lower, upper

    lower_offset, upper_offset = jax.lax.fori_loop(
        0,
        32,
        bisection_step,
        (lower_offset, upper_offset),
    )
    neutral_offset = 0.5 * (lower_offset + upper_offset)
    projected_field = jnp.clip(nodal_field - neutral_offset, -cap, cap)
    return jnp.where(centered_field_is_bounded, centered_field, projected_field)


def _bounded_field(nodal_field: jax.Array, cap: jax.Array) -> jax.Array:
    """Scale a nodal perturbation so its component maximum stays within cap."""
    cap = jnp.asarray(jnp.maximum(cap, 0.0), dtype=nodal_field.dtype)
    max_abs = jnp.max(jnp.abs(nodal_field))
    scale = jnp.where(max_abs > cap, cap / jnp.maximum(max_abs, 1.0e-30), 1.0)
    return nodal_field * scale


def _tropical_wtg_latitude_envelope(
    horizontal_grid: spherical_harmonic.Grid,
) -> jax.Array:
    """Return the fixed tropical WTG envelope: full inside 12 deg, zero by 27 deg."""
    _, sin_latitude = horizontal_grid.nodal_mesh
    absolute_sin_latitude = jnp.abs(sin_latitude)
    full_sin_latitude = jnp.sin(jnp.deg2rad(_TROPICAL_WTG_FULL_LATITUDE_DEGREES))
    zero_sin_latitude = jnp.sin(jnp.deg2rad(_TROPICAL_WTG_ZERO_LATITUDE_DEGREES))
    taper_fraction = jnp.clip(
        (absolute_sin_latitude - full_sin_latitude)
        / (zero_sin_latitude - full_sin_latitude),
        0.0,
        1.0,
    )
    taper = 0.5 * (1.0 + jnp.cos(jnp.pi * taper_fraction))
    return jnp.where(
        absolute_sin_latitude <= full_sin_latitude,
        1.0,
        jnp.where(absolute_sin_latitude >= zero_sin_latitude, 0.0, taper),
    )


def _tropical_wtg_sigma_envelope(
    vertical_coords: sigma_coordinates.SigmaCoordinates,
) -> jax.Array:
    """Return the fixed free-tropospheric WTG sigma envelope."""
    sigma = jnp.asarray(vertical_coords.centers)
    upper_fraction = jnp.clip(
        (sigma - _TROPICAL_WTG_SIGMA_ZERO_TOP)
        / (_TROPICAL_WTG_SIGMA_FULL_TOP - _TROPICAL_WTG_SIGMA_ZERO_TOP),
        0.0,
        1.0,
    )
    lower_fraction = jnp.clip(
        (_TROPICAL_WTG_SIGMA_ZERO_BOTTOM - sigma)
        / (_TROPICAL_WTG_SIGMA_ZERO_BOTTOM - _TROPICAL_WTG_SIGMA_FULL_BOTTOM),
        0.0,
        1.0,
    )
    upper_taper = 0.5 * (1.0 - jnp.cos(jnp.pi * upper_fraction))
    lower_taper = 0.5 * (1.0 - jnp.cos(jnp.pi * lower_fraction))
    return jnp.where(
        (sigma >= _TROPICAL_WTG_SIGMA_FULL_TOP)
        & (sigma <= _TROPICAL_WTG_SIGMA_FULL_BOTTOM),
        1.0,
        upper_taper * lower_taper,
    )


def _tropical_wtg_low_mode_mask(
    horizontal_grid: spherical_harmonic.Grid,
) -> jax.Array:
    """Return the fixed smooth low-mode mask for WTG mass-DSE anomalies."""
    _, total_wavenumber = horizontal_grid.modal_mesh
    total_wavenumber = jnp.asarray(total_wavenumber, dtype=jnp.float32)
    taper_fraction = jnp.clip(
        (total_wavenumber - _TROPICAL_WTG_LOW_MODE_CUTOFF)
        / (_TROPICAL_WTG_LOW_MODE_TAPER_ZERO - _TROPICAL_WTG_LOW_MODE_CUTOFF),
        0.0,
        1.0,
    )
    taper = 0.5 * (1.0 + jnp.cos(jnp.pi * taper_fraction))
    low_mode_mask = jnp.where(
        total_wavenumber <= _TROPICAL_WTG_LOW_MODE_CUTOFF,
        1.0,
        jnp.where(total_wavenumber >= _TROPICAL_WTG_LOW_MODE_TAPER_ZERO, 0.0, taper),
    )
    return low_mode_mask * jnp.asarray(horizontal_grid.mask, dtype=jnp.float32)


def default_dinosaur_dycore_model() -> DinosaurPrimitiveEquationsDycoreModel:
    """Return the default Dinosaur primitive-equation dycore model."""
    return DinosaurPrimitiveEquationsDycoreModel()


def production_dinosaur_dycore_model() -> DinosaurPrimitiveEquationsDycoreModel:
    """Return the frozen production dycore used by the hybrid model."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name="dino_rskin_apv",
        use_log_pressure_initialization=True,
        use_hydrostatic_temperature_initialization=True,
        use_layer_mean_hydrostatic_temperature_initialization=True,
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        use_analysis_offset_weak_held_suarez_equilibrium=True,
        apply_near_surface_residual_correction=True,
        use_stability_aware_near_surface_residual_decay=True,
        use_scale_separated_near_surface_residual=True,
        use_land_sea_surface_temperature_residual=True,
        use_land_ocean_low_mode_t2m_memory=True,
        apply_ocean_bulk_sensible_heat_flux=True,
        apply_land_skin_reservoir=True,
        use_analysis_2m_initialized_land_skin=True,
        apply_zero_mean_radiative_land_skin_energy=True,
        use_surface_layer_richardson_10m_wind_diagnostic=True,
        use_bulk_richardson_2m_temperature_diagnostic=True,
        use_pressure_thickness_weighted_ri2m_temperature=True,
        use_prognostic_skin_ri2m_lower_boundary=True,
        use_ocean_anchor_ri2m_lower_boundary=True,
        apply_exact_coriolis_rotation_split=True,
        apply_symmetric_exact_coriolis_rotation_split=True,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        apply_theta_layer_mean_recentering=True,
        use_horizontal_semilagrangian_theta_transport=True,
        use_midpoint_semilagrangian_theta_departure=True,
        use_dry_static_energy_hsl_transport=True,
        use_layer_mass_weighted_dse_hsl_transport=True,
        use_pressure_ramped_vertical_dse_increment=True,
        apply_anticipated_pv_flux=True,
        apply_tropical_wtg_mass_dse_relaxation=True,
        apply_coupled_ekman_surface_closure=True,
        use_coriolis_scaled_ekman_depth=True,
        apply_orographic_lift_theta_tendency=True,
        use_depth_weighted_orographic_lift_wind=True,
        apply_terrain_work_form_drag_heating=True,
        semi_implicit_offcentering=DEFAULT_SEMI_IMPLICIT_OFFCENTERING,
    )


def weather_state_to_dinosaur_state(
    state: WeatherState,
    *,
    coords: coordinate_systems.CoordinateSystem,
    pressure_levels_hpa: tuple[int, ...],
    latitude_reversed: bool,
    physics_specs: Any,
    reference_temperature: np.ndarray,
    include_humidity: bool,
    use_log_pressure_initialization: bool = False,
    use_hydrostatic_temperature_initialization: bool = False,
    use_layer_mean_hydrostatic_temperature_initialization: bool = False,
    initialize_sim_time: bool = False,
) -> Any:
    """Convert one packed WeatherState initialization into Dinosaur state."""
    temperature = _stack_pressure_level_channels(
        state,
        TEMPERATURE_VARIABLE,
        pressure_levels_hpa,
    )
    if use_hydrostatic_temperature_initialization and has_pressure_level_stack(
        state.variables,
        GEOPOTENTIAL_VARIABLE,
        pressure_levels_hpa,
    ):
        geopotential = _stack_pressure_level_channels(
            state,
            GEOPOTENTIAL_VARIABLE,
            pressure_levels_hpa,
        )
        specific_humidity = None
        if has_pressure_level_stack(
            state.variables,
            SPECIFIC_HUMIDITY_VARIABLE,
            pressure_levels_hpa,
        ):
            specific_humidity = _stack_pressure_level_channels(
                state,
                SPECIFIC_HUMIDITY_VARIABLE,
                pressure_levels_hpa,
            )
        if use_layer_mean_hydrostatic_temperature_initialization:
            temperature = (
                _layer_mean_hydrostatic_temperature_from_geopotential_thickness(
                    analyzed_temperature=temperature,
                    geopotential=geopotential,
                    pressure_levels_hpa=pressure_levels_hpa,
                    specific_humidity=specific_humidity,
                )
            )
        else:
            temperature = _hydrostatic_temperature_from_geopotential_thickness(
                analyzed_temperature=temperature,
                geopotential=geopotential,
                pressure_levels_hpa=pressure_levels_hpa,
                specific_humidity=specific_humidity,
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
    pressure_to_sigma = (
        vertical_interpolation.interp_pressure_to_sigma_log_pressure
        if use_log_pressure_initialization
        else vertical_interpolation.interp_pressure_to_sigma
    )
    nodal_inputs = pressure_to_sigma(
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
        sim_time=(
            jnp.asarray(0.0, dtype=temperature_variation.dtype)
            if initialize_sim_time
            else None
        ),
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
    use_surface_layer_richardson_10m_wind_diagnostic: bool = False,
    use_bulk_richardson_2m_temperature_diagnostic: bool = False,
    use_pressure_thickness_weighted_ri2m_temperature: bool = False,
    use_prognostic_skin_ri2m_lower_boundary: bool = False,
    prognostic_skin_temperature: jax.Array | None = None,
    land_weight: jax.Array | None = None,
    use_ocean_anchor_ri2m_lower_boundary: bool = False,
    ocean_temperature_anchor: jax.Array | None = None,
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
    ten_meter_u_wind = u_wind[:, -1]
    ten_meter_v_wind = v_wind[:, -1]
    if use_surface_layer_richardson_10m_wind_diagnostic:
        ten_meter_u_wind, ten_meter_v_wind = _surface_layer_richardson_10m_wind(
            temperature=temperature,
            u_wind=u_wind,
            v_wind=v_wind,
            surface_pressure_hpa=surface_pressure_hpa,
            sigma_coords=cast(sigma_coordinates.SigmaCoordinates, coords.vertical),
        )
    two_meter_temperature = temperature[:, -1]
    if use_bulk_richardson_2m_temperature_diagnostic:
        two_meter_temperature = _bulk_richardson_2m_temperature(
            temperature=temperature,
            u_wind=u_wind,
            v_wind=v_wind,
            surface_pressure_hpa=surface_pressure_hpa,
            sigma_coords=cast(sigma_coordinates.SigmaCoordinates, coords.vertical),
            use_pressure_thickness_weighted_ri2m_temperature=(
                use_pressure_thickness_weighted_ri2m_temperature
            ),
        )
    atmospheric_two_meter_temperature = two_meter_temperature
    if use_prognostic_skin_ri2m_lower_boundary:
        skin_temperature_kelvin = (
            None
            if prognostic_skin_temperature is None
            else prognostic_skin_temperature / _unit_factor(physics_specs, "kelvin")
        )
        two_meter_temperature = _prognostic_skin_ri2m_temperature(
            incumbent_temperature=two_meter_temperature,
            skin_temperature=skin_temperature_kelvin,
            land_weight=land_weight,
            forecast_time=trajectory.sim_time,
            temperature=temperature,
            u_wind=u_wind,
            v_wind=v_wind,
            surface_pressure_hpa=surface_pressure_hpa,
            sigma_coords=cast(sigma_coordinates.SigmaCoordinates, coords.vertical),
            physics_specs=physics_specs,
        )
    if use_ocean_anchor_ri2m_lower_boundary:
        ocean_temperature_anchor_kelvin = (
            None
            if ocean_temperature_anchor is None
            else ocean_temperature_anchor / _unit_factor(physics_specs, "kelvin")
        )
        two_meter_temperature = _ocean_anchor_ri2m_temperature(
            incumbent_temperature=atmospheric_two_meter_temperature,
            land_observed_temperature=two_meter_temperature,
            ocean_temperature_anchor=ocean_temperature_anchor_kelvin,
            land_weight=land_weight,
            forecast_time=trajectory.sim_time,
            temperature=temperature,
            u_wind=u_wind,
            v_wind=v_wind,
            surface_pressure_hpa=surface_pressure_hpa,
            sigma_coords=cast(sigma_coordinates.SigmaCoordinates, coords.vertical),
            physics_specs=physics_specs,
        )

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
            field = two_meter_temperature
        elif channel == TEN_METER_U_WIND_VARIABLE:
            field = ten_meter_u_wind
        elif channel == TEN_METER_V_WIND_VARIABLE:
            field = ten_meter_v_wind
        elif channel in (SURFACE_PRESSURE_VARIABLE, MEAN_SEA_LEVEL_PRESSURE_VARIABLE):
            field = surface_pressure
        else:
            raise AssertionError(f"Dinosaur cannot output {channel}")
        fields.append(_from_dinosaur_latitude_order(field, latitude_reversed))

    return WeatherState(
        values=jnp.stack(fields, axis=1),
        variables=output_variables,
    )


def _bulk_richardson_2m_temperature(
    *,
    temperature: jax.Array,
    u_wind: jax.Array,
    v_wind: jax.Array,
    surface_pressure_hpa: jax.Array,
    sigma_coords: sigma_coordinates.SigmaCoordinates,
    use_pressure_thickness_weighted_ri2m_temperature: bool = False,
) -> jax.Array:
    """Diagnose 2 m temperature with bounded lower-column theta extrapolation."""
    lowest_temperature = temperature[:, -1]
    if sigma_coords.layers < 2:
        return lowest_temperature

    incumbent_temperature = _bulk_richardson_2m_temperature_from_reference_states(
        lower_temperature=lowest_temperature,
        upper_temperature=temperature[:, -2],
        lower_u_wind=u_wind[:, -1],
        upper_u_wind=u_wind[:, -2],
        lower_v_wind=v_wind[:, -1],
        upper_v_wind=v_wind[:, -2],
        surface_pressure_hpa=surface_pressure_hpa,
        lower_sigma=float(sigma_coords.centers[-1]),
        upper_sigma=float(sigma_coords.centers[-2]),
        fallback_temperature=lowest_temperature,
    )
    if not use_pressure_thickness_weighted_ri2m_temperature or sigma_coords.layers < 4:
        return incumbent_temperature

    weighted_references = _pressure_thickness_weighted_ri2m_reference_states(
        temperature=temperature,
        u_wind=u_wind,
        v_wind=v_wind,
        sigma_coords=sigma_coords,
    )
    if weighted_references is None:
        return incumbent_temperature

    weighted_temperature = _bulk_richardson_2m_temperature_from_reference_states(
        lower_temperature=weighted_references.lower_temperature,
        upper_temperature=weighted_references.upper_temperature,
        lower_u_wind=weighted_references.lower_u_wind,
        upper_u_wind=weighted_references.upper_u_wind,
        lower_v_wind=weighted_references.lower_v_wind,
        upper_v_wind=weighted_references.upper_v_wind,
        surface_pressure_hpa=surface_pressure_hpa,
        lower_sigma=weighted_references.lower_sigma,
        upper_sigma=weighted_references.upper_sigma,
        fallback_temperature=incumbent_temperature,
    )
    return jnp.where(
        weighted_references.finite_mask,
        weighted_temperature,
        incumbent_temperature,
    )


def _prognostic_skin_ri2m_temperature(
    *,
    incumbent_temperature: jax.Array,
    skin_temperature: jax.Array | None,
    land_weight: jax.Array | None,
    forecast_time: jax.Array | None,
    temperature: jax.Array,
    u_wind: jax.Array,
    v_wind: jax.Array,
    surface_pressure_hpa: jax.Array,
    sigma_coords: sigma_coordinates.SigmaCoordinates,
    physics_specs: Any,
) -> jax.Array:
    """Blend a bounded skin-to-lower-layer RI2m estimate over valid land."""
    if (
        skin_temperature is None
        or land_weight is None
        or forecast_time is None
        or sigma_coords.layers < 4
        or skin_temperature.shape != incumbent_temperature.shape
        or land_weight.shape != incumbent_temperature.shape[-2:]
        or forecast_time.shape != incumbent_temperature.shape[:1]
    ):
        return incumbent_temperature

    references = _pressure_thickness_weighted_ri2m_reference_states(
        temperature=temperature,
        u_wind=u_wind,
        v_wind=v_wind,
        sigma_coords=sigma_coords,
    )
    if references is None:
        return incumbent_temperature

    lower_sigma = references.lower_sigma
    if not np.isfinite(lower_sigma) or lower_sigma <= 0.0 or lower_sigma > 1.0:
        return incumbent_temperature

    valid_skin = jnp.isfinite(skin_temperature) & (skin_temperature > 0.0)
    valid_land = jnp.isfinite(land_weight) & (land_weight >= 0.0) & (land_weight <= 1.0)
    valid_pressure = jnp.isfinite(surface_pressure_hpa) & (surface_pressure_hpa > 0.0)
    valid_lower_temperature = jnp.isfinite(references.lower_temperature) & (
        references.lower_temperature > 0.0
    )
    safe_lower_temperature = jnp.where(
        valid_lower_temperature,
        references.lower_temperature,
        jnp.ones_like(references.lower_temperature),
    )
    safe_skin_temperature = jnp.where(
        valid_skin,
        skin_temperature,
        safe_lower_temperature,
    )
    safe_surface_pressure_hpa = jnp.where(
        valid_pressure,
        surface_pressure_hpa,
        jnp.ones_like(surface_pressure_hpa),
    )

    lower_pressure_hpa = jnp.maximum(
        safe_surface_pressure_hpa * lower_sigma,
        1.0,
    )
    screen_pressure_hpa = jnp.maximum(safe_surface_pressure_hpa, 1.0)
    lower_theta = (
        safe_lower_temperature
        * (1000.0 / lower_pressure_hpa)
        ** _STABILITY_AWARE_POTENTIAL_TEMPERATURE_EXPONENT
    )
    skin_theta = (
        safe_skin_temperature
        * (1000.0 / screen_pressure_hpa)
        ** _STABILITY_AWARE_POTENTIAL_TEMPERATURE_EXPONENT
    )
    mean_theta = jnp.maximum(0.5 * (skin_theta + lower_theta), 1.0)
    lower_height_meters = (
        _DRY_AIR_GAS_CONSTANT_SI * safe_lower_temperature / _GRAVITY_ACCELERATION_SI
    ) * jnp.log(1.0 / max(lower_sigma, 1.0e-6))
    lower_height_meters = jnp.maximum(
        lower_height_meters,
        _SURFACE_LAYER_TEMPERATURE_REFERENCE_HEIGHT_METERS,
    )

    squared_shear = references.lower_u_wind**2 + references.lower_v_wind**2
    squared_shear = jnp.maximum(
        squared_shear,
        _SURFACE_LAYER_SHEAR_FLOOR_METERS_PER_SECOND**2,
    )
    richardson_number = (
        (_GRAVITY_ACCELERATION_SI / mean_theta)
        * (lower_theta - skin_theta)
        * lower_height_meters
        / squared_shear
    )
    richardson_number = jnp.clip(richardson_number, -1.0, 1.0)
    screen_fraction = jnp.clip(
        _SURFACE_LAYER_TEMPERATURE_REFERENCE_HEIGHT_METERS / lower_height_meters,
        0.0,
        1.0,
    )
    stability_limiter = 1.0 / (1.0 + 2.0 * jnp.abs(richardson_number))
    screen_theta = skin_theta + (
        (lower_theta - skin_theta) * screen_fraction * stability_limiter
    )
    screen_temperature = screen_theta / (
        (1000.0 / screen_pressure_hpa)
        ** _STABILITY_AWARE_POTENTIAL_TEMPERATURE_EXPONENT
    )
    temperature_departure = jnp.clip(
        screen_temperature - safe_lower_temperature,
        -_SURFACE_LAYER_TEMPERATURE_MAX_DEPARTURE_KELVIN,
        _SURFACE_LAYER_TEMPERATURE_MAX_DEPARTURE_KELVIN,
    )
    skin_aware_temperature = safe_lower_temperature + temperature_departure

    active_land_weight = jnp.where(
        valid_land,
        _active_land_skin_weight(land_weight),
        jnp.zeros_like(land_weight),
    )
    ramp_weight = _land_skin_reservoir_forecast_time_ramp(
        forecast_time,
        physics_specs,
    )
    valid_ramp = jnp.isfinite(ramp_weight)
    blend_weight = (
        active_land_weight[jnp.newaxis]
        * jnp.clip(ramp_weight, 0.0, 1.0)[:, jnp.newaxis, jnp.newaxis]
    )
    blended_temperature = incumbent_temperature + blend_weight * (
        skin_aware_temperature - incumbent_temperature
    )
    finite_diagnostic = jnp.all(
        jnp.isfinite(
            jnp.stack(
                [
                    lower_theta,
                    skin_theta,
                    lower_height_meters,
                    squared_shear,
                    richardson_number,
                    screen_temperature,
                    skin_aware_temperature,
                    blended_temperature,
                ]
            )
        ),
        axis=0,
    )
    use_candidate = (
        references.finite_mask
        & valid_skin
        & valid_pressure
        & valid_lower_temperature
        & valid_land[jnp.newaxis]
        & valid_ramp[:, jnp.newaxis, jnp.newaxis]
        & jnp.isfinite(incumbent_temperature)
        & finite_diagnostic
        & (blend_weight > 0.0)
    )
    return jnp.where(use_candidate, blended_temperature, incumbent_temperature)


def _ocean_anchor_ri2m_temperature(
    *,
    incumbent_temperature: jax.Array,
    land_observed_temperature: jax.Array,
    ocean_temperature_anchor: jax.Array | None,
    land_weight: jax.Array | None,
    forecast_time: jax.Array | None,
    temperature: jax.Array,
    u_wind: jax.Array,
    v_wind: jax.Array,
    surface_pressure_hpa: jax.Array | None,
    sigma_coords: sigma_coordinates.SigmaCoordinates,
    physics_specs: Any,
) -> jax.Array:
    """Add a bounded ocean RI2m endpoint without changing the land observer."""
    expected_spatial_shape = incumbent_temperature.shape[-2:]
    expected_trajectory_shape = (
        incumbent_temperature.shape[0],
        sigma_coords.layers,
        *expected_spatial_shape,
    )
    if (
        ocean_temperature_anchor is None
        or land_weight is None
        or forecast_time is None
        or surface_pressure_hpa is None
        or incumbent_temperature.ndim != 3
        or land_observed_temperature.shape != incumbent_temperature.shape
        or ocean_temperature_anchor.shape != expected_spatial_shape
        or land_weight.shape != expected_spatial_shape
        or forecast_time.shape != incumbent_temperature.shape[:1]
        or temperature.shape != expected_trajectory_shape
        or u_wind.shape != expected_trajectory_shape
        or v_wind.shape != expected_trajectory_shape
        or surface_pressure_hpa.shape != incumbent_temperature.shape
    ):
        return land_observed_temperature

    land_fraction = jnp.asarray(land_weight, dtype=incumbent_temperature.dtype)
    valid_land_fraction = (
        jnp.isfinite(land_fraction) & (land_fraction >= 0.0) & (land_fraction <= 1.0)
    )
    ocean_fraction = jnp.where(
        valid_land_fraction,
        1.0 - jnp.clip(land_fraction, 0.0, 1.0),
        jnp.zeros_like(land_fraction),
    )
    anchor = jnp.asarray(
        ocean_temperature_anchor,
        dtype=incumbent_temperature.dtype,
    )
    valid_anchor = jnp.isfinite(anchor) & (anchor > 0.0)
    anchor_trajectory = jnp.broadcast_to(
        anchor[jnp.newaxis],
        incumbent_temperature.shape,
    )
    fully_ocean_observed_temperature = _prognostic_skin_ri2m_temperature(
        incumbent_temperature=incumbent_temperature,
        skin_temperature=anchor_trajectory,
        land_weight=jnp.ones_like(land_fraction),
        forecast_time=forecast_time,
        temperature=temperature,
        u_wind=u_wind,
        v_wind=v_wind,
        surface_pressure_hpa=surface_pressure_hpa,
        sigma_coords=sigma_coords,
        physics_specs=physics_specs,
    )
    ocean_correction = ocean_fraction[jnp.newaxis] * (
        fully_ocean_observed_temperature - incumbent_temperature
    )
    combined_temperature = land_observed_temperature + ocean_correction
    use_ocean_correction = (
        valid_land_fraction[jnp.newaxis]
        & valid_anchor[jnp.newaxis]
        & (ocean_fraction[jnp.newaxis] > 0.0)
        & jnp.isfinite(ocean_correction)
        & jnp.isfinite(combined_temperature)
        & (fully_ocean_observed_temperature != incumbent_temperature)
    )
    return jnp.where(
        use_ocean_correction,
        combined_temperature,
        land_observed_temperature,
    )


@dataclass(frozen=True)
class _BulkRichardson2mReferenceStates:
    """Reference states for the bounded RI2m 2 m temperature diagnostic."""

    lower_temperature: jax.Array
    upper_temperature: jax.Array
    lower_u_wind: jax.Array
    upper_u_wind: jax.Array
    lower_v_wind: jax.Array
    upper_v_wind: jax.Array
    lower_sigma: float
    upper_sigma: float
    finite_mask: jax.Array


def _pressure_thickness_weighted_ri2m_reference_states(
    *,
    temperature: jax.Array,
    u_wind: jax.Array,
    v_wind: jax.Array,
    sigma_coords: sigma_coordinates.SigmaCoordinates,
) -> _BulkRichardson2mReferenceStates | None:
    """Return shallow pressure-thickness weighted lower/upper RI2m states."""
    if sigma_coords.layers < 4:
        return None

    layer_thickness = np.asarray(sigma_coords.layer_thickness, dtype=np.float32)
    sigma_centers = np.asarray(sigma_coords.centers, dtype=np.float32)
    lower_weights = _normalized_positive_sigma_weights(layer_thickness[-2:])
    upper_weights = _normalized_positive_sigma_weights(layer_thickness[-4:-2])
    if lower_weights is None or upper_weights is None:
        return None

    lower_temperature = _weighted_layer_band_mean(temperature[:, -2:], lower_weights)
    upper_temperature = _weighted_layer_band_mean(temperature[:, -4:-2], upper_weights)
    lower_u_wind = _weighted_layer_band_mean(u_wind[:, -2:], lower_weights)
    upper_u_wind = _weighted_layer_band_mean(u_wind[:, -4:-2], upper_weights)
    lower_v_wind = _weighted_layer_band_mean(v_wind[:, -2:], lower_weights)
    upper_v_wind = _weighted_layer_band_mean(v_wind[:, -4:-2], upper_weights)
    finite_mask = jnp.all(
        jnp.isfinite(
            jnp.stack(
                [
                    lower_temperature,
                    upper_temperature,
                    lower_u_wind,
                    upper_u_wind,
                    lower_v_wind,
                    upper_v_wind,
                ]
            )
        ),
        axis=0,
    )
    return _BulkRichardson2mReferenceStates(
        lower_temperature=lower_temperature,
        upper_temperature=upper_temperature,
        lower_u_wind=lower_u_wind,
        upper_u_wind=upper_u_wind,
        lower_v_wind=lower_v_wind,
        upper_v_wind=upper_v_wind,
        lower_sigma=float(np.sum(sigma_centers[-2:] * lower_weights)),
        upper_sigma=float(np.sum(sigma_centers[-4:-2] * upper_weights)),
        finite_mask=finite_mask,
    )


def _normalized_positive_sigma_weights(
    layer_thickness: np.ndarray,
) -> np.ndarray | None:
    """Normalize a fixed sigma layer-thickness band or reject invalid weights."""
    valid_weight_mask = np.isfinite(layer_thickness) & (layer_thickness > 0.0)
    if not bool(np.all(valid_weight_mask)):
        return None
    weight_sum = float(np.sum(layer_thickness))
    if not np.isfinite(weight_sum) or weight_sum <= 0.0:
        return None
    return layer_thickness / weight_sum


def _weighted_layer_band_mean(field: jax.Array, weights: np.ndarray) -> jax.Array:
    """Return the weighted mean of a fixed layer band along the layer axis."""
    weight_array = jnp.asarray(weights, dtype=field.dtype)
    return jnp.sum(
        field * weight_array[jnp.newaxis, :, jnp.newaxis, jnp.newaxis],
        axis=1,
    )


def _bulk_richardson_2m_temperature_from_reference_states(
    *,
    lower_temperature: jax.Array,
    upper_temperature: jax.Array,
    lower_u_wind: jax.Array,
    upper_u_wind: jax.Array,
    lower_v_wind: jax.Array,
    upper_v_wind: jax.Array,
    surface_pressure_hpa: jax.Array,
    lower_sigma: float,
    upper_sigma: float,
    fallback_temperature: jax.Array,
) -> jax.Array:
    """Apply the RI2m stability algebra to supplied lower/upper references."""
    lower_pressure_hpa = jnp.maximum(surface_pressure_hpa * lower_sigma, 1.0)
    upper_pressure_hpa = jnp.maximum(surface_pressure_hpa * upper_sigma, 1.0)
    screen_pressure_hpa = jnp.maximum(surface_pressure_hpa, 1.0)
    lower_theta = (
        lower_temperature
        * (1000.0 / lower_pressure_hpa)
        ** _STABILITY_AWARE_POTENTIAL_TEMPERATURE_EXPONENT
    )
    upper_theta = (
        upper_temperature
        * (1000.0 / upper_pressure_hpa)
        ** _STABILITY_AWARE_POTENTIAL_TEMPERATURE_EXPONENT
    )
    mean_temperature = jnp.maximum(0.5 * (lower_temperature + upper_temperature), 1.0)
    mean_theta = jnp.maximum(0.5 * (lower_theta + upper_theta), 1.0)

    pressure_ratio = jnp.maximum(lower_pressure_hpa / upper_pressure_hpa, 1.0)
    layer_separation_meters = (
        _DRY_AIR_GAS_CONSTANT_SI * mean_temperature / _GRAVITY_ACCELERATION_SI
    ) * jnp.log(pressure_ratio)
    lowest_layer_height_meters = (
        _DRY_AIR_GAS_CONSTANT_SI * lower_temperature / _GRAVITY_ACCELERATION_SI
    ) * jnp.log(1.0 / max(lower_sigma, 1.0e-6))
    layer_separation_meters = jnp.maximum(layer_separation_meters, 1.0)
    lowest_layer_height_meters = jnp.maximum(
        lowest_layer_height_meters,
        _SURFACE_LAYER_TEMPERATURE_REFERENCE_HEIGHT_METERS,
    )

    squared_shear = (upper_u_wind - lower_u_wind) ** 2 + (
        upper_v_wind - lower_v_wind
    ) ** 2
    squared_shear = jnp.maximum(
        squared_shear,
        _SURFACE_LAYER_SHEAR_FLOOR_METERS_PER_SECOND**2,
    )
    richardson_number = (
        (_GRAVITY_ACCELERATION_SI / mean_theta)
        * (upper_theta - lower_theta)
        * layer_separation_meters
        / squared_shear
    )
    richardson_number = jnp.clip(richardson_number, -1.0, 1.0)

    screen_fraction = (
        lowest_layer_height_meters - _SURFACE_LAYER_TEMPERATURE_REFERENCE_HEIGHT_METERS
    ) / layer_separation_meters
    screen_fraction = jnp.clip(screen_fraction, 0.0, 1.0)
    stability_limiter = 1.0 / (1.0 + 2.0 * jnp.abs(richardson_number))
    screen_theta = lower_theta + (
        (lower_theta - upper_theta) * screen_fraction * stability_limiter
    )
    screen_temperature = screen_theta / (
        (1000.0 / screen_pressure_hpa)
        ** _STABILITY_AWARE_POTENTIAL_TEMPERATURE_EXPONENT
    )
    temperature_departure = jnp.clip(
        screen_temperature - lower_temperature,
        -_SURFACE_LAYER_TEMPERATURE_MAX_DEPARTURE_KELVIN,
        _SURFACE_LAYER_TEMPERATURE_MAX_DEPARTURE_KELVIN,
    )
    diagnosed_temperature = lower_temperature + temperature_departure

    required_values = jnp.stack(
        [
            lower_temperature,
            upper_temperature,
            lower_u_wind,
            upper_u_wind,
            lower_v_wind,
            upper_v_wind,
            surface_pressure_hpa,
            layer_separation_meters,
            lowest_layer_height_meters,
            diagnosed_temperature,
        ]
    )
    finite_mask = jnp.all(jnp.isfinite(required_values), axis=0) & (
        surface_pressure_hpa > 0.0
    )
    return jnp.where(finite_mask, diagnosed_temperature, fallback_temperature)


def _surface_layer_richardson_10m_wind(
    *,
    temperature: jax.Array,
    u_wind: jax.Array,
    v_wind: jax.Array,
    surface_pressure_hpa: jax.Array,
    sigma_coords: sigma_coordinates.SigmaCoordinates,
) -> tuple[jax.Array, jax.Array]:
    """Diagnose 10 m wind by bounded Richardson scaling of the lowest wind."""
    lowest_u_wind = u_wind[:, -1]
    lowest_v_wind = v_wind[:, -1]
    if sigma_coords.layers < 2:
        return lowest_u_wind, lowest_v_wind

    lower_sigma = float(sigma_coords.centers[-1])
    upper_sigma = float(sigma_coords.centers[-2])
    lower_pressure_hpa = jnp.maximum(surface_pressure_hpa * lower_sigma, 1.0)
    upper_pressure_hpa = jnp.maximum(surface_pressure_hpa * upper_sigma, 1.0)
    lower_temperature = temperature[:, -1]
    upper_temperature = temperature[:, -2]
    lower_theta = (
        lower_temperature
        * (1000.0 / lower_pressure_hpa)
        ** _STABILITY_AWARE_POTENTIAL_TEMPERATURE_EXPONENT
    )
    upper_theta = (
        upper_temperature
        * (1000.0 / upper_pressure_hpa)
        ** _STABILITY_AWARE_POTENTIAL_TEMPERATURE_EXPONENT
    )
    mean_temperature = jnp.maximum(0.5 * (lower_temperature + upper_temperature), 1.0)
    mean_theta = jnp.maximum(0.5 * (lower_theta + upper_theta), 1.0)

    pressure_ratio = jnp.maximum(lower_pressure_hpa / upper_pressure_hpa, 1.0)
    layer_separation_meters = (
        _DRY_AIR_GAS_CONSTANT_SI * mean_temperature / _GRAVITY_ACCELERATION_SI
    ) * jnp.log(pressure_ratio)
    lowest_layer_height_meters = (
        _DRY_AIR_GAS_CONSTANT_SI * lower_temperature / _GRAVITY_ACCELERATION_SI
    ) * jnp.log(1.0 / max(lower_sigma, 1.0e-6))
    layer_separation_meters = jnp.maximum(layer_separation_meters, 1.0)
    lowest_layer_height_meters = jnp.maximum(lowest_layer_height_meters, 10.0)

    squared_shear = (u_wind[:, -2] - lowest_u_wind) ** 2 + (
        v_wind[:, -2] - lowest_v_wind
    ) ** 2
    squared_shear = jnp.maximum(
        squared_shear,
        _SURFACE_LAYER_SHEAR_FLOOR_METERS_PER_SECOND**2,
    )
    richardson_number = (
        (_GRAVITY_ACCELERATION_SI / mean_theta)
        * (upper_theta - lower_theta)
        * layer_separation_meters
        / squared_shear
    )
    richardson_number = jnp.clip(richardson_number, -1.0, 1.0)

    neutral_factor = jnp.log1p(_SURFACE_LAYER_REFERENCE_HEIGHT_METERS) / jnp.log1p(
        lowest_layer_height_meters
    )
    stable_damping = 1.0 / (1.0 + 2.0 * jnp.maximum(richardson_number, 0.0))
    unstable_mixing = (1.0 - neutral_factor) * jnp.minimum(
        jnp.maximum(-richardson_number, 0.0), 1.0
    )
    wind_factor = neutral_factor * stable_damping + unstable_mixing
    wind_factor = jnp.clip(
        wind_factor,
        _SURFACE_LAYER_WIND_MIN_FACTOR,
        _SURFACE_LAYER_WIND_MAX_FACTOR,
    )

    required_values = jnp.stack(
        [
            lower_temperature,
            upper_temperature,
            lowest_u_wind,
            u_wind[:, -2],
            lowest_v_wind,
            v_wind[:, -2],
            surface_pressure_hpa,
            layer_separation_meters,
            lowest_layer_height_meters,
            wind_factor,
        ]
    )
    finite_mask = jnp.all(jnp.isfinite(required_values), axis=0)
    wind_factor = jnp.where(finite_mask, wind_factor, 1.0)
    return lowest_u_wind * wind_factor, lowest_v_wind * wind_factor


def _apply_near_surface_residual_correction(
    trajectory_state: WeatherState,
    *,
    initial_state: WeatherState,
    lead_steps: tuple[int, ...],
    lead_hours: tuple[int, ...],
    decay_hours: float,
    use_stability_aware_decay: bool = False,
) -> WeatherState:
    """Apply forecast-time near-surface residuals to requested output leads."""
    assert decay_hours > 0.0
    assert len(lead_steps) == len(lead_hours)

    lead_indices = jnp.asarray(lead_steps, dtype=jnp.int32)
    corrected_values = jnp.take(trajectory_state.values, lead_indices, axis=0)
    lead_hours_array = jnp.asarray(lead_hours, dtype=corrected_values.dtype)
    if use_stability_aware_decay:
        decay_hours_array = _stability_aware_near_surface_residual_decay_hours(
            trajectory_state,
            initial_state=initial_state,
            lead_indices=lead_indices,
            base_decay_hours=decay_hours,
        )
        decay = jnp.exp(
            -lead_hours_array[:, jnp.newaxis, jnp.newaxis] / decay_hours_array
        )
    else:
        decay = jnp.exp(-lead_hours_array / jnp.asarray(decay_hours))
    lead_zero_mask = lead_indices == 0

    for channel in _NEAR_SURFACE_RESIDUAL_VARIABLES:
        if (
            channel not in initial_state.variables
            or channel not in trajectory_state.variables
        ):
            continue
        output_index = int(trajectory_state.variable_indices((channel,))[0])
        initial_index = int(initial_state.variable_indices((channel,))[0])
        initial_channel = initial_state.values[initial_index]
        raw_lead_zero = trajectory_state.values[0, output_index]
        residual = initial_channel - raw_lead_zero
        if use_stability_aware_decay:
            residual_decay = decay
        else:
            residual_decay = decay[:, jnp.newaxis, jnp.newaxis]
        channel_values = corrected_values[:, output_index] + (
            residual[jnp.newaxis, ...] * residual_decay
        )
        channel_values = jnp.where(
            lead_zero_mask[:, jnp.newaxis, jnp.newaxis],
            initial_channel[jnp.newaxis, ...],
            channel_values,
        )
        corrected_values = corrected_values.at[:, output_index].set(channel_values)

    return WeatherState(
        values=corrected_values,
        variables=trajectory_state.variables,
    )


def _apply_scale_separated_near_surface_residual_correction(
    trajectory_state: WeatherState,
    *,
    initial_state: WeatherState,
    lead_steps: tuple[int, ...],
    lead_hours: tuple[int, ...],
    decay_hours: float,
    use_stability_aware_decay: bool = False,
    horizontal_grid: spherical_harmonic.Grid | None = None,
    latitude_reversed: bool = False,
    land_sea_fraction: jax.Array | None = None,
    use_land_ocean_low_mode_t2m_memory: bool = False,
) -> WeatherState:
    """Apply low- and high-wavenumber residual memory to near-surface outputs."""
    incumbent_state = _apply_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=lead_steps,
        lead_hours=lead_hours,
        decay_hours=decay_hours,
        use_stability_aware_decay=use_stability_aware_decay,
    )
    if horizontal_grid is None:
        return incumbent_state
    valid_land_sea_fraction = _valid_land_sea_fraction_or_none(
        land_sea_fraction,
        trajectory_state.spatial_shape,
    )

    assert decay_hours > 0.0
    assert len(lead_steps) == len(lead_hours)

    lead_indices = jnp.asarray(lead_steps, dtype=jnp.int32)
    corrected_values = jnp.take(trajectory_state.values, lead_indices, axis=0)
    lead_hours_array = jnp.asarray(lead_hours, dtype=corrected_values.dtype)
    high_mode_decay, low_mode_decay = _scale_separated_residual_decays(
        trajectory_state,
        initial_state=initial_state,
        lead_indices=lead_indices,
        lead_hours_array=lead_hours_array,
        decay_hours=decay_hours,
        use_stability_aware_decay=use_stability_aware_decay,
    )
    lead_zero_mask = lead_indices == 0

    for channel in _NEAR_SURFACE_RESIDUAL_VARIABLES:
        if (
            channel not in initial_state.variables
            or channel not in trajectory_state.variables
        ):
            continue
        output_index = int(trajectory_state.variable_indices((channel,))[0])
        initial_index = int(initial_state.variable_indices((channel,))[0])
        initial_channel = initial_state.values[initial_index]
        raw_lead_zero = trajectory_state.values[0, output_index]
        residual = initial_channel - raw_lead_zero
        try:
            low_mode_residual, high_mode_residual, split_is_valid = (
                _split_near_surface_residual_by_scale(
                    residual,
                    horizontal_grid=horizontal_grid,
                    latitude_reversed=latitude_reversed,
                )
            )
        except (AssertionError, AttributeError, TypeError, ValueError):
            return incumbent_state

        channel_high_mode_decay = high_mode_decay
        channel_low_mode_decay = low_mode_decay
        if (
            channel == TWO_METER_TEMPERATURE_VARIABLE
            and valid_land_sea_fraction is not None
        ):
            channel_high_mode_decay, channel_low_mode_decay = (
                _land_sea_surface_temperature_residual_decays(
                    high_mode_decay=high_mode_decay,
                    low_mode_decay=low_mode_decay,
                    land_sea_fraction=valid_land_sea_fraction,
                )
            )

        candidate_channel_values = corrected_values[:, output_index] + (
            low_mode_residual[jnp.newaxis, ...] * channel_low_mode_decay
            + high_mode_residual[jnp.newaxis, ...] * channel_high_mode_decay
        )
        if (
            channel == TWO_METER_TEMPERATURE_VARIABLE
            and use_land_ocean_low_mode_t2m_memory
            and valid_land_sea_fraction is not None
        ):
            memory_correction, memory_is_valid = (
                _land_ocean_low_mode_t2m_memory_correction(
                    low_mode_residual,
                    land_sea_fraction=valid_land_sea_fraction,
                    horizontal_grid=horizontal_grid,
                    latitude_reversed=latitude_reversed,
                    lead_hours_array=lead_hours_array,
                    incumbent_low_mode_decay=channel_low_mode_decay,
                )
            )
            candidate_channel_values = jnp.where(
                memory_is_valid,
                candidate_channel_values + memory_correction,
                candidate_channel_values,
            )
        candidate_channel_values = jnp.where(
            lead_zero_mask[:, jnp.newaxis, jnp.newaxis],
            initial_channel[jnp.newaxis, ...],
            candidate_channel_values,
        )
        channel_values = jnp.where(
            split_is_valid,
            candidate_channel_values,
            incumbent_state.values[:, output_index],
        )
        corrected_values = corrected_values.at[:, output_index].set(channel_values)

    return WeatherState(
        values=corrected_values,
        variables=trajectory_state.variables,
    )


def _land_ocean_low_mode_t2m_memory_correction(
    low_mode_residual: jax.Array,
    *,
    land_sea_fraction: jax.Array,
    horizontal_grid: spherical_harmonic.Grid,
    latitude_reversed: bool,
    lead_hours_array: jax.Array,
    incumbent_low_mode_decay: jax.Array,
) -> tuple[jax.Array, jax.Array]:
    """Return a capped late-lead broad land/ocean T2m memory correction."""
    broad_residual, residual_is_valid = _land_ocean_low_mode_t2m_residual(
        low_mode_residual,
        land_sea_fraction=land_sea_fraction,
        horizontal_grid=horizontal_grid,
        latitude_reversed=latitude_reversed,
    )
    lead_hours = lead_hours_array[:, jnp.newaxis, jnp.newaxis]
    ramp_fraction = jnp.clip(
        (lead_hours - _LAND_OCEAN_LOW_MODE_T2M_MEMORY_RAMP_START_HOURS)
        / (
            _LAND_OCEAN_LOW_MODE_T2M_MEMORY_RAMP_FULL_HOURS
            - _LAND_OCEAN_LOW_MODE_T2M_MEMORY_RAMP_START_HOURS
        ),
        0.0,
        1.0,
    )
    ramp = ramp_fraction * ramp_fraction * (3.0 - 2.0 * ramp_fraction)
    memory_decay = jnp.exp(
        -lead_hours
        / jnp.asarray(
            _LAND_OCEAN_LOW_MODE_T2M_MEMORY_DECAY_HOURS,
            dtype=lead_hours.dtype,
        )
    )
    extra_decay = jnp.maximum(memory_decay - incumbent_low_mode_decay, 0.0) * ramp
    uncapped_correction = broad_residual[jnp.newaxis, ...] * extra_decay
    correction = jnp.clip(
        uncapped_correction,
        -_LAND_OCEAN_LOW_MODE_T2M_MEMORY_MAX_CORRECTION_KELVIN,
        _LAND_OCEAN_LOW_MODE_T2M_MEMORY_MAX_CORRECTION_KELVIN,
    )
    correction_is_valid = (
        residual_is_valid
        & jnp.all(jnp.isfinite(extra_decay))
        & jnp.all(jnp.isfinite(correction))
        & jnp.all(extra_decay >= 0.0)
        & jnp.all(extra_decay <= 1.0)
    )
    return correction, correction_is_valid


def _land_ocean_low_mode_t2m_residual(
    low_mode_residual: jax.Array,
    *,
    land_sea_fraction: jax.Array,
    horizontal_grid: spherical_harmonic.Grid,
    latitude_reversed: bool,
) -> tuple[jax.Array, jax.Array]:
    """Return land/ocean broad means of the low-mode T2m residual."""
    residual = jnp.asarray(low_mode_residual)
    land_fraction = jnp.asarray(land_sea_fraction, dtype=residual.dtype)
    ocean_fraction = 1.0 - land_fraction
    quadrature_weights = jnp.asarray(
        horizontal_grid.quadrature_weights,
        dtype=residual.dtype,
    )
    quadrature_weights = _from_dinosaur_latitude_order(
        quadrature_weights,
        latitude_reversed,
    )
    land_weights = quadrature_weights * land_fraction
    ocean_weights = quadrature_weights * ocean_fraction
    tiny_weight = jnp.asarray(jnp.finfo(residual.dtype).tiny, dtype=residual.dtype)
    land_weight_sum = jnp.sum(land_weights)
    ocean_weight_sum = jnp.sum(ocean_weights)
    safe_land_weight_sum = jnp.where(
        land_weight_sum > tiny_weight,
        land_weight_sum,
        jnp.ones_like(land_weight_sum),
    )
    safe_ocean_weight_sum = jnp.where(
        ocean_weight_sum > tiny_weight,
        ocean_weight_sum,
        jnp.ones_like(ocean_weight_sum),
    )
    land_mean = jnp.where(
        land_weight_sum > tiny_weight,
        jnp.sum(residual * land_weights) / safe_land_weight_sum,
        jnp.zeros_like(land_weight_sum),
    )
    ocean_mean = jnp.where(
        ocean_weight_sum > tiny_weight,
        jnp.sum(residual * ocean_weights) / safe_ocean_weight_sum,
        jnp.zeros_like(ocean_weight_sum),
    )
    broad_residual = land_fraction * land_mean + ocean_fraction * ocean_mean
    residual_is_valid = jnp.all(
        jnp.asarray(
            [
                jnp.all(jnp.isfinite(residual)),
                jnp.all(jnp.isfinite(land_fraction)),
                jnp.all(jnp.isfinite(quadrature_weights)),
                jnp.all(land_fraction >= 0.0),
                jnp.all(land_fraction <= 1.0),
                jnp.all(quadrature_weights >= 0.0),
                jnp.all(jnp.isfinite(broad_residual)),
            ]
        )
    )
    return broad_residual, residual_is_valid


def _land_sea_surface_temperature_residual_decays(
    *,
    high_mode_decay: jax.Array,
    low_mode_decay: jax.Array,
    land_sea_fraction: jax.Array,
) -> tuple[jax.Array, jax.Array]:
    """Return T2m residual decays that keep land incumbent and ocean persistent."""
    land_fraction = jnp.asarray(land_sea_fraction, dtype=high_mode_decay.dtype)
    ocean_fraction = 1.0 - land_fraction
    ocean_high_mode_decay = jnp.power(
        jnp.clip(high_mode_decay, 0.0, 1.0),
        _LAND_SEA_SURFACE_TEMPERATURE_OCEAN_DECAY_EXPONENT,
    )
    ocean_low_mode_decay = jnp.power(
        jnp.clip(low_mode_decay, 0.0, 1.0),
        _LAND_SEA_SURFACE_TEMPERATURE_OCEAN_DECAY_EXPONENT,
    )
    land_fraction = land_fraction[jnp.newaxis, ...]
    ocean_fraction = ocean_fraction[jnp.newaxis, ...]
    return (
        land_fraction * high_mode_decay + ocean_fraction * ocean_high_mode_decay,
        land_fraction * low_mode_decay + ocean_fraction * ocean_low_mode_decay,
    )


def _valid_land_sea_fraction_or_none(
    land_sea_fraction: jax.Array | None,
    spatial_shape: tuple[int, int],
) -> jax.Array | None:
    """Return a finite `[0, 1]` land fraction or `None` for exact fallback."""
    if land_sea_fraction is None:
        return None
    try:
        candidate = np.asarray(jax.device_get(land_sea_fraction), dtype=np.float32)
    except Exception:
        return None
    if candidate.shape != tuple(spatial_shape):
        return None
    if not bool(np.isfinite(candidate).all()):
        return None
    if candidate.size == 0:
        return None
    if float(np.min(candidate)) < 0.0 or float(np.max(candidate)) > 1.0:
        return None
    candidate.setflags(write=False)
    return jnp.asarray(candidate, dtype=jnp.float32)


def _ocean_bulk_sensible_heat_flux_temperature_anchor(
    initial_state: WeatherState,
    *,
    dinosaur_state: Any,
    coords: coordinate_systems.CoordinateSystem,
    latitude_reversed: bool,
    physics_specs: Any,
    reference_temperature: np.ndarray,
) -> jax.Array | None:
    """Return a finite lead-zero ocean thermal anchor in Dinosaur latitude order."""
    if TWO_METER_TEMPERATURE_VARIABLE in initial_state.variables:
        temperature_index = int(
            initial_state.variable_indices((TWO_METER_TEMPERATURE_VARIABLE,))[0]
        )
        anchor_temperature = initial_state.values[temperature_index] * _unit_factor(
            physics_specs, "kelvin"
        )
        anchor_temperature = _to_dinosaur_latitude_order(
            anchor_temperature,
            latitude_reversed,
        )
    else:
        full_temperature = (
            coords.horizontal.to_nodal(dinosaur_state.temperature_variation)
            + jnp.asarray(reference_temperature)[:, jnp.newaxis, jnp.newaxis]
        )
        anchor_temperature = full_temperature[-1]
    return _valid_ocean_bulk_shf_temperature_anchor_or_none(
        anchor_temperature,
        coords.horizontal.nodal_shape,
    )


def _valid_ocean_bulk_shf_temperature_anchor_or_none(
    temperature_anchor: jax.Array | None,
    spatial_shape: tuple[int, int],
) -> jax.Array | None:
    """Return a positive finite anchor field or `None` for incumbent fallback."""
    if temperature_anchor is None:
        return None
    try:
        candidate = np.asarray(jax.device_get(temperature_anchor), dtype=np.float32)
    except Exception:
        return None
    if candidate.shape != tuple(spatial_shape):
        return None
    if candidate.size == 0:
        return None
    if not bool(np.isfinite(candidate).all()):
        return None
    if float(np.min(candidate)) <= 0.0:
        return None
    candidate.setflags(write=False)
    return jnp.asarray(candidate, dtype=jnp.float32)


def _load_land_sea_fraction_for_grid(
    *,
    longitude: np.ndarray,
    latitude: np.ndarray,
    initial_time: np.datetime64,
) -> jax.Array | None:
    """Load a WeatherBench2 land fraction only when it exactly matches the grid."""
    from dynamaxx.data.weatherbench2 import WeatherBench2Source

    longitude = np.asarray(longitude, dtype=np.float64)
    latitude = np.asarray(latitude, dtype=np.float64)
    source = WeatherBench2Source()
    cache_key = _land_sea_fraction_cache_key(source.path, longitude, latitude)
    cached_mask = _LAND_SEA_FRACTION_CACHE.get(cache_key)
    if cached_mask is not None:
        return cached_mask

    try:
        source_longitude, source_latitude = source.spatial_coordinates(
            time=initial_time
        )
        if not (
            np.array_equal(source_longitude, longitude)
            and np.array_equal(source_latitude, latitude)
        ):
            return None
        constants = source.read_constants([_LAND_SEA_MASK_CHANNEL])
        constants_array = np.asarray(jax.device_get(constants))
    except Exception:
        return None

    if constants_array.shape != (1, longitude.size, latitude.size):
        return None
    mask = _valid_land_sea_fraction_or_none(
        constants_array[0],
        (longitude.size, latitude.size),
    )
    if mask is None:
        return None
    _LAND_SEA_FRACTION_CACHE[cache_key] = mask
    return mask


def _load_surface_geopotential_height_for_grid(
    *,
    longitude: np.ndarray,
    latitude: np.ndarray,
    initial_time: np.datetime64,
) -> jax.Array | None:
    """Load fixed surface geopotential as terrain height in meters."""
    from dynamaxx.data.weatherbench2 import WeatherBench2Source

    longitude = np.asarray(longitude, dtype=np.float64)
    latitude = np.asarray(latitude, dtype=np.float64)
    source = WeatherBench2Source()
    cache_key = _terrain_height_cache_key(source.path, longitude, latitude)
    cached_height = _TERRAIN_HEIGHT_CACHE.get(cache_key)
    if cached_height is not None:
        return cached_height

    try:
        source_longitude, source_latitude = source.spatial_coordinates(
            time=initial_time
        )
        if not (
            np.array_equal(source_longitude, longitude)
            and np.array_equal(source_latitude, latitude)
        ):
            return None
        constants = source.read_constants([_GEOPOTENTIAL_AT_SURFACE_CHANNEL])
        constants_array = np.asarray(jax.device_get(constants))
    except Exception:
        return None

    if constants_array.shape != (1, longitude.size, latitude.size):
        return None
    terrain_height = _valid_terrain_height_or_none(
        constants_array[0] / _GRAVITY_ACCELERATION_SI,
        (longitude.size, latitude.size),
    )
    if terrain_height is None:
        return None
    _TERRAIN_HEIGHT_CACHE[cache_key] = terrain_height
    return terrain_height


def _land_sea_fraction_cache_key(
    path: str,
    longitude: np.ndarray,
    latitude: np.ndarray,
) -> _LandSeaMaskCacheKey:
    """Build a value-based key so cached masks cannot cross grids."""
    longitude = np.ascontiguousarray(np.asarray(longitude, dtype=np.float64))
    latitude = np.ascontiguousarray(np.asarray(latitude, dtype=np.float64))
    return (
        str(path),
        tuple(int(size) for size in longitude.shape),
        longitude.tobytes(),
        tuple(int(size) for size in latitude.shape),
        latitude.tobytes(),
    )


def _terrain_height_cache_key(
    path: str,
    longitude: np.ndarray,
    latitude: np.ndarray,
) -> _TerrainHeightCacheKey:
    """Build a value-based key so terrain constants cannot cross grids."""
    longitude = np.ascontiguousarray(np.asarray(longitude, dtype=np.float64))
    latitude = np.ascontiguousarray(np.asarray(latitude, dtype=np.float64))
    return (
        str(path),
        tuple(int(size) for size in longitude.shape),
        longitude.tobytes(),
        tuple(int(size) for size in latitude.shape),
        latitude.tobytes(),
    )


def _scale_separated_residual_decays(
    trajectory_state: WeatherState,
    *,
    initial_state: WeatherState,
    lead_indices: jax.Array,
    lead_hours_array: jax.Array,
    decay_hours: float,
    use_stability_aware_decay: bool,
) -> tuple[jax.Array, jax.Array]:
    """Return incumbent high-mode and longer low-mode residual decay factors."""
    if use_stability_aware_decay:
        high_mode_decay_hours = _stability_aware_near_surface_residual_decay_hours(
            trajectory_state,
            initial_state=initial_state,
            lead_indices=lead_indices,
            base_decay_hours=decay_hours,
        )
        base_decay_hours = float(
            np.clip(
                decay_hours,
                _STABILITY_AWARE_MIN_RESIDUAL_DECAY_HOURS,
                _STABILITY_AWARE_MAX_RESIDUAL_DECAY_HOURS,
            )
        )
        local_decay_multiplier = high_mode_decay_hours / jnp.asarray(
            base_decay_hours,
            dtype=high_mode_decay_hours.dtype,
        )
        low_mode_decay_hours = (
            jnp.asarray(
                _SCALE_SEPARATED_RESIDUAL_LOW_DECAY_HOURS,
                dtype=high_mode_decay_hours.dtype,
            )
            * local_decay_multiplier
        )
        lead_hours = lead_hours_array[:, jnp.newaxis, jnp.newaxis]
        return (
            jnp.exp(-lead_hours / high_mode_decay_hours),
            jnp.exp(-lead_hours / low_mode_decay_hours),
        )

    lead_hours = lead_hours_array[:, jnp.newaxis, jnp.newaxis]
    high_mode_decay_hours = jnp.asarray(decay_hours, dtype=lead_hours_array.dtype)
    low_mode_decay_hours = jnp.asarray(
        _SCALE_SEPARATED_RESIDUAL_LOW_DECAY_HOURS,
        dtype=lead_hours_array.dtype,
    )
    return (
        jnp.exp(-lead_hours / high_mode_decay_hours),
        jnp.exp(-lead_hours / low_mode_decay_hours),
    )


def _split_near_surface_residual_by_scale(
    residual: jax.Array,
    *,
    horizontal_grid: spherical_harmonic.Grid,
    latitude_reversed: bool,
) -> tuple[jax.Array, jax.Array, jax.Array]:
    """Split a gridpoint residual into low and high horizontal-scale parts."""
    if tuple(residual.shape[-2:]) != tuple(horizontal_grid.nodal_shape):
        raise ValueError(
            "near-surface residual shape does not match Dinosaur horizontal grid"
        )

    residual_in_model_order = _to_dinosaur_latitude_order(residual, latitude_reversed)
    modal_residual = horizontal_grid.to_modal(residual_in_model_order)
    low_mode_mask = _scale_separated_residual_low_mode_mask(horizontal_grid)
    low_mode_residual = horizontal_grid.to_nodal(modal_residual * low_mode_mask)
    low_mode_residual = _from_dinosaur_latitude_order(
        low_mode_residual,
        latitude_reversed,
    )
    high_mode_residual = residual - low_mode_residual
    split_is_valid = (
        jnp.all(jnp.isfinite(residual))
        & jnp.all(jnp.isfinite(low_mode_residual))
        & jnp.all(jnp.isfinite(high_mode_residual))
    )
    return low_mode_residual, high_mode_residual, split_is_valid


def _scale_separated_residual_low_mode_mask(
    horizontal_grid: spherical_harmonic.Grid,
) -> jax.Array:
    """Return the fixed spectral taper for low-mode residual memory."""
    _, total_wavenumber = horizontal_grid.modal_mesh
    transition = (total_wavenumber - _SCALE_SEPARATED_RESIDUAL_LOW_MODE_CUTOFF) / (
        _SCALE_SEPARATED_RESIDUAL_TAPER_ZERO_MODE
        - _SCALE_SEPARATED_RESIDUAL_LOW_MODE_CUTOFF
    )
    transition = np.clip(transition, 0.0, 1.0)
    taper = 0.5 * (1.0 + np.cos(np.pi * transition))
    taper = np.where(
        total_wavenumber >= _SCALE_SEPARATED_RESIDUAL_TAPER_ZERO_MODE,
        0.0,
        taper,
    )
    taper = np.where(np.asarray(horizontal_grid.mask), taper, 0.0)
    return jnp.asarray(taper, dtype=jnp.float32)


def _stability_aware_near_surface_residual_decay_hours(
    trajectory_state: WeatherState,
    *,
    initial_state: WeatherState,
    lead_indices: jax.Array,
    base_decay_hours: float,
) -> jax.Array:
    """Return bounded local near-surface residual decay timescales."""
    base_decay = float(
        np.clip(
            base_decay_hours,
            _STABILITY_AWARE_MIN_RESIDUAL_DECAY_HOURS,
            _STABILITY_AWARE_MAX_RESIDUAL_DECAY_HOURS,
        )
    )
    lower_column_levels = _lower_column_stability_levels(trajectory_state.variables)
    if lower_column_levels is None:
        stability_score = _near_surface_residual_stability_proxy(
            trajectory_state,
            initial_state=initial_state,
            lead_count=int(lead_indices.shape[0]),
        )
    else:
        low_level_hpa, upper_level_hpa = lower_column_levels
        selected_values = jnp.take(trajectory_state.values, lead_indices, axis=0)
        stability_score = _lower_column_stability_score(
            selected_values,
            trajectory_state.variables,
            low_level_hpa=low_level_hpa,
            upper_level_hpa=upper_level_hpa,
        )
    return _bounded_residual_decay_hours(stability_score, base_decay)


def _lower_column_stability_levels(
    variables: tuple[str, ...],
) -> tuple[int, int] | None:
    common_levels = []
    for channel in variables:
        variable_name, pressure_level = split_pressure_level_channel(channel)
        if variable_name != TEMPERATURE_VARIABLE or pressure_level is None:
            continue
        if f"{U_WIND_VARIABLE}_{pressure_level}" in variables:
            common_levels.append(pressure_level)
    if len(common_levels) < 2:
        return None
    ordered_levels = tuple(sorted(common_levels, reverse=True))
    return ordered_levels[0], ordered_levels[1]


def _lower_column_stability_score(
    selected_values: jax.Array,
    variables: tuple[str, ...],
    *,
    low_level_hpa: int,
    upper_level_hpa: int,
) -> jax.Array:
    low_temperature = _selected_channel(
        selected_values,
        variables,
        f"{TEMPERATURE_VARIABLE}_{low_level_hpa}",
    )
    upper_temperature = _selected_channel(
        selected_values,
        variables,
        f"{TEMPERATURE_VARIABLE}_{upper_level_hpa}",
    )
    low_theta = _potential_temperature(low_temperature, low_level_hpa)
    upper_theta = _potential_temperature(upper_temperature, upper_level_hpa)
    static_stability_kelvin = upper_theta - low_theta

    low_u_wind = _selected_channel(
        selected_values,
        variables,
        f"{U_WIND_VARIABLE}_{low_level_hpa}",
    )
    upper_u_wind = _selected_channel(
        selected_values,
        variables,
        f"{U_WIND_VARIABLE}_{upper_level_hpa}",
    )
    squared_shear = (upper_u_wind - low_u_wind) ** 2
    low_v_channel = f"{V_WIND_VARIABLE}_{low_level_hpa}"
    upper_v_channel = f"{V_WIND_VARIABLE}_{upper_level_hpa}"
    if low_v_channel in variables and upper_v_channel in variables:
        low_v_wind = _selected_channel(selected_values, variables, low_v_channel)
        upper_v_wind = _selected_channel(selected_values, variables, upper_v_channel)
        squared_shear = squared_shear + (upper_v_wind - low_v_wind) ** 2
    shear = _sqrt_nonnegative_with_finite_gradient(squared_shear)
    stability_index = static_stability_kelvin / (
        _STABILITY_AWARE_SHEAR_FLOOR_METERS_PER_SECOND + shear
    )
    return jnp.clip(stability_index, -1.0, 1.0)


def _near_surface_residual_stability_proxy(
    trajectory_state: WeatherState,
    *,
    initial_state: WeatherState,
    lead_count: int,
) -> jax.Array:
    if (
        TWO_METER_TEMPERATURE_VARIABLE not in initial_state.variables
        or TWO_METER_TEMPERATURE_VARIABLE not in trajectory_state.variables
        or TEN_METER_U_WIND_VARIABLE not in initial_state.variables
        or TEN_METER_U_WIND_VARIABLE not in trajectory_state.variables
    ):
        sample_field = trajectory_state.values[0, 0]
        return jnp.zeros(
            (lead_count,) + sample_field.shape,
            dtype=trajectory_state.values.dtype,
        )

    temperature_output_index = int(
        trajectory_state.variable_indices((TWO_METER_TEMPERATURE_VARIABLE,))[0]
    )
    temperature_initial_index = int(
        initial_state.variable_indices((TWO_METER_TEMPERATURE_VARIABLE,))[0]
    )
    wind_output_index = int(
        trajectory_state.variable_indices((TEN_METER_U_WIND_VARIABLE,))[0]
    )
    wind_initial_index = int(
        initial_state.variable_indices((TEN_METER_U_WIND_VARIABLE,))[0]
    )
    temperature_residual = (
        initial_state.values[temperature_initial_index]
        - trajectory_state.values[0, temperature_output_index]
    )
    wind_residual = (
        initial_state.values[wind_initial_index]
        - trajectory_state.values[0, wind_output_index]
    )
    weak_flow_factor = 1.0 - jnp.clip(
        jnp.abs(initial_state.values[wind_initial_index])
        / _STABILITY_AWARE_WEAK_FLOW_SCALE_METERS_PER_SECOND,
        0.0,
        1.0,
    )
    decoupling_score = (
        jnp.abs(temperature_residual)
        / _STABILITY_AWARE_TEMPERATURE_RESIDUAL_SCALE_KELVIN
    ) * weak_flow_factor
    wind_mixing_score = (
        jnp.abs(wind_residual) / _STABILITY_AWARE_WIND_RESIDUAL_SCALE_METERS_PER_SECOND
    )
    stability_score = jnp.clip(decoupling_score - wind_mixing_score, -1.0, 1.0)
    return jnp.broadcast_to(
        stability_score[jnp.newaxis, ...],
        (lead_count,) + stability_score.shape,
    )


def _bounded_residual_decay_hours(
    stability_score: jax.Array,
    base_decay_hours: float,
) -> jax.Array:
    positive_score = jnp.maximum(stability_score, 0.0)
    negative_score = jnp.maximum(-stability_score, 0.0)
    decay_hours = (
        base_decay_hours
        + positive_score
        * (_STABILITY_AWARE_MAX_RESIDUAL_DECAY_HOURS - base_decay_hours)
        + negative_score
        * (_STABILITY_AWARE_MIN_RESIDUAL_DECAY_HOURS - base_decay_hours)
    )
    return jnp.clip(
        decay_hours,
        _STABILITY_AWARE_MIN_RESIDUAL_DECAY_HOURS,
        _STABILITY_AWARE_MAX_RESIDUAL_DECAY_HOURS,
    )


def _potential_temperature(
    temperature_kelvin: jax.Array,
    pressure_hpa: int,
) -> jax.Array:
    return (
        temperature_kelvin
        * (1000.0 / float(pressure_hpa))
        ** _STABILITY_AWARE_POTENTIAL_TEMPERATURE_EXPONENT
    )


def _selected_channel(
    selected_values: jax.Array,
    variables: tuple[str, ...],
    channel: str,
) -> jax.Array:
    return selected_values[:, variables.index(channel)]


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


def _hydrostatic_temperature_from_geopotential_thickness(
    *,
    analyzed_temperature: jax.Array,
    geopotential: jax.Array,
    pressure_levels_hpa: tuple[int, ...],
    specific_humidity: jax.Array | None = None,
    dry_air_gas_constant: float = _DRY_AIR_GAS_CONSTANT_SI,
    water_vapor_gas_constant: float = _WATER_VAPOR_GAS_CONSTANT_SI,
) -> jax.Array:
    """Estimate dry temperature from pressure-level geopotential thickness.

    Inputs are SI WeatherBench quantities: geopotential in m^2 s^-2,
    temperature in K, pressure in hPa, and dimensionless specific humidity.
    The hypsometric derivative is evaluated in log pressure; one-sided
    differences are used at the top and bottom levels and centered differences
    at interior levels.
    """
    if len(pressure_levels_hpa) < 2:
        return analyzed_temperature

    log_pressure = jnp.log(jnp.asarray(pressure_levels_hpa, dtype=geopotential.dtype))
    dry_air_gas_constant = jnp.asarray(
        dry_air_gas_constant,
        dtype=geopotential.dtype,
    )

    geopotential_difference = jnp.concatenate(
        [
            geopotential[1:2] - geopotential[:1],
            geopotential[2:] - geopotential[:-2],
            geopotential[-1:] - geopotential[-2:-1],
        ],
        axis=0,
    )
    log_pressure_difference = jnp.concatenate(
        [
            log_pressure[1:2] - log_pressure[:1],
            log_pressure[2:] - log_pressure[:-2],
            log_pressure[-1:] - log_pressure[-2:-1],
        ],
        axis=0,
    )
    minimum_difference = jnp.finfo(log_pressure_difference.dtype).tiny
    safe_log_pressure_difference = jnp.where(
        jnp.abs(log_pressure_difference) > minimum_difference,
        log_pressure_difference,
        jnp.where(log_pressure_difference < 0.0, -1.0, 1.0) * minimum_difference,
    )

    virtual_temperature = -geopotential_difference / (
        dry_air_gas_constant * safe_log_pressure_difference[:, jnp.newaxis, jnp.newaxis]
    )
    dry_temperature = virtual_temperature
    if specific_humidity is not None:
        gas_constant_ratio = jnp.asarray(
            water_vapor_gas_constant / dry_air_gas_constant,
            dtype=geopotential.dtype,
        )
        bounded_humidity = jnp.clip(specific_humidity, 0.0, 1.0)
        virtual_temperature_factor = 1.0 + (gas_constant_ratio - 1.0) * bounded_humidity
        dry_temperature = virtual_temperature / virtual_temperature_factor

    valid_temperature = jnp.isfinite(dry_temperature) & (dry_temperature > 0.0)
    return jnp.where(valid_temperature, dry_temperature, analyzed_temperature)


def _layer_mean_hydrostatic_temperature_from_geopotential_thickness(
    *,
    analyzed_temperature: jax.Array,
    geopotential: jax.Array,
    pressure_levels_hpa: tuple[int, ...],
    specific_humidity: jax.Array | None = None,
    dry_air_gas_constant: float = _DRY_AIR_GAS_CONSTANT_SI,
    water_vapor_gas_constant: float = _WATER_VAPOR_GAS_CONSTANT_SI,
) -> jax.Array:
    """Estimate dry temperature from adjacent-layer hypsometric thicknesses."""
    if len(pressure_levels_hpa) < 2:
        return analyzed_temperature

    log_pressure = jnp.log(jnp.asarray(pressure_levels_hpa, dtype=geopotential.dtype))
    dry_air_gas_constant = jnp.asarray(
        dry_air_gas_constant,
        dtype=geopotential.dtype,
    )
    log_pressure_difference = log_pressure[1:] - log_pressure[:-1]
    geopotential_difference = geopotential[1:] - geopotential[:-1]
    layer_virtual_temperature = -geopotential_difference / (
        dry_air_gas_constant * log_pressure_difference[:, jnp.newaxis, jnp.newaxis]
    )

    layer_dry_temperature = layer_virtual_temperature
    if specific_humidity is not None:
        gas_constant_ratio = jnp.asarray(
            water_vapor_gas_constant / dry_air_gas_constant,
            dtype=geopotential.dtype,
        )
        layer_specific_humidity = 0.5 * (specific_humidity[1:] + specific_humidity[:-1])
        bounded_humidity = jnp.clip(layer_specific_humidity, 0.0, 1.0)
        virtual_temperature_factor = 1.0 + (gas_constant_ratio - 1.0) * bounded_humidity
        layer_dry_temperature = layer_virtual_temperature / virtual_temperature_factor

    level_dry_temperature = jnp.concatenate(
        [
            layer_dry_temperature[:1],
            0.5 * (layer_dry_temperature[1:] + layer_dry_temperature[:-1]),
            layer_dry_temperature[-1:],
        ],
        axis=0,
    )
    valid_temperature = jnp.isfinite(level_dry_temperature) & (
        level_dry_temperature > 0.0
    )
    return jnp.where(valid_temperature, level_dry_temperature, analyzed_temperature)


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
    temperature_tendency_formulation: str = (
        primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_TEMPERATURE
    ),
    use_horizontal_semilagrangian_theta_transport: bool = False,
    use_midpoint_semilagrangian_theta_departure: bool = False,
    use_dry_static_energy_hsl_transport: bool = False,
    use_layer_mass_weighted_dse_hsl_transport: bool = False,
    use_pressure_ramped_vertical_dse_increment: bool = False,
    use_anticipated_pv_flux: bool = False,
    anticipated_pv_step_seconds: float = 0.0,
    anticipated_pv_coriolis_parameter: jax.Array | None = None,
    horizontal_semilagrangian_theta_transport_step: float = 0.0,
) -> Any:
    """Build the Dinosaur primitive-equation object for this adapter."""
    if humidity_key is None:
        return primitive_equations.PrimitiveEquations(
            reference_temperature,
            orography,
            coords,
            physics_specs,
            include_vertical_advection=include_vertical_advection,
            temperature_tendency_formulation=temperature_tendency_formulation,
            use_horizontal_semilagrangian_theta_transport=(
                use_horizontal_semilagrangian_theta_transport
            ),
            use_midpoint_semilagrangian_theta_departure=(
                use_midpoint_semilagrangian_theta_departure
            ),
            use_dry_static_energy_hsl_transport=(use_dry_static_energy_hsl_transport),
            use_layer_mass_weighted_dse_hsl_transport=(
                use_layer_mass_weighted_dse_hsl_transport
            ),
            use_pressure_ramped_vertical_dse_increment=(
                use_pressure_ramped_vertical_dse_increment
            ),
            use_anticipated_pv_flux=use_anticipated_pv_flux,
            anticipated_pv_step_seconds=anticipated_pv_step_seconds,
            anticipated_pv_coriolis_parameter=(anticipated_pv_coriolis_parameter),
            horizontal_semilagrangian_theta_transport_step=(
                horizontal_semilagrangian_theta_transport_step
            ),
        )
    return primitive_equations.PrimitiveEquationsSigma(
        reference_temperature,
        orography,
        coords,
        physics_specs,
        include_vertical_advection=include_vertical_advection,
        humidity_key=humidity_key,
        temperature_tendency_formulation=temperature_tendency_formulation,
        use_horizontal_semilagrangian_theta_transport=(
            use_horizontal_semilagrangian_theta_transport
        ),
        use_midpoint_semilagrangian_theta_departure=(
            use_midpoint_semilagrangian_theta_departure
        ),
        use_dry_static_energy_hsl_transport=(use_dry_static_energy_hsl_transport),
        use_layer_mass_weighted_dse_hsl_transport=(
            use_layer_mass_weighted_dse_hsl_transport
        ),
        use_pressure_ramped_vertical_dse_increment=(
            use_pressure_ramped_vertical_dse_increment
        ),
        use_anticipated_pv_flux=use_anticipated_pv_flux,
        anticipated_pv_step_seconds=anticipated_pv_step_seconds,
        anticipated_pv_coriolis_parameter=anticipated_pv_coriolis_parameter,
        horizontal_semilagrangian_theta_transport_step=(
            horizontal_semilagrangian_theta_transport_step
        ),
    )


class _TracerSafeHeldSuarezForcingSigma(held_suarez.HeldSuarezForcingSigma):
    """Thermal-only Held-Suarez forcing with passive tracer tendency leaves."""

    def __init__(
        self,
        *args: Any,
        equilibrium_temperature_offset: jax.Array | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.equilibrium_temperature_offset = equilibrium_temperature_offset

    def _equilibrium_temperature(
        self,
        nodal_surface_pressure: jax.Array,
    ) -> jax.Array:
        equilibrium_temperature = self.equilibrium_temperature(nodal_surface_pressure)
        if self.equilibrium_temperature_offset is None:
            return equilibrium_temperature
        return equilibrium_temperature + self.equilibrium_temperature_offset

    def explicit_terms(
        self,
        state: primitive_equations.State,
    ) -> primitive_equations.State:
        aux_state = primitive_equations.compute_diagnostic_state_sigma(
            state=state,
            coords=self.coords,
        )
        nodal_temperature = (
            self.reference_temperature[:, np.newaxis, np.newaxis]
            + aux_state.temperature_variation
        )
        nodal_log_surface_pressure = self.coords.horizontal.to_nodal(
            state.log_surface_pressure
        )
        nodal_surface_pressure = jnp.exp(nodal_log_surface_pressure)
        equilibrium_temperature = self._equilibrium_temperature(nodal_surface_pressure)
        nodal_temperature_tendency = -self.kt() * (
            nodal_temperature - equilibrium_temperature
        )
        temperature_tendency = self.coords.horizontal.to_modal(
            nodal_temperature_tendency
        )
        return primitive_equations.State(
            vorticity=jnp.zeros_like(state.vorticity),
            divergence=jnp.zeros_like(state.divergence),
            temperature_variation=temperature_tendency,
            log_surface_pressure=jnp.zeros_like(state.log_surface_pressure),
            tracers=jax.tree_util.tree_map(jnp.zeros_like, state.tracers),
            sim_time=None if state.sim_time is None else 0.0,
        )


class _OceanBulkSensibleHeatFluxForcingSigma(time_integration.ExplicitODE):
    """Weak ocean-weighted bulk sensible heat flux for the lowest sigma layer."""

    def __init__(
        self,
        *,
        coords: coordinate_systems.CoordinateSystem,
        physics_specs: Any,
        reference_temperature: np.ndarray,
        ocean_weight: jax.Array,
        temperature_anchor: jax.Array,
        step_seconds: float,
    ):
        assert step_seconds > 0.0
        self.coords = coords
        self.physics_specs = physics_specs
        self.reference_temperature = jnp.asarray(reference_temperature)
        self.ocean_weight = jnp.asarray(ocean_weight, dtype=jnp.float32)
        self.temperature_anchor = jnp.asarray(temperature_anchor, dtype=jnp.float32)
        self.step_seconds = float(step_seconds)
        self.wind_unit_factor = _unit_factor(physics_specs, "meter / second")
        self.rate_unit_factor = _unit_factor(physics_specs, "1 / second")
        self.temperature_unit_factor = _unit_factor(physics_specs, "kelvin")

    def explicit_terms(
        self,
        state: primitive_equations.State,
    ) -> primitive_equations.State:
        nodal_temperature = (
            self.coords.horizontal.to_nodal(state.temperature_variation)
            + self.reference_temperature[:, jnp.newaxis, jnp.newaxis]
        )
        current_temperature = nodal_temperature[-1]
        u_wind, v_wind = spherical_harmonic.vor_div_to_uv_nodal(
            self.coords.horizontal,
            state.vorticity,
            state.divergence,
        )
        lowest_u_wind = u_wind[-1]
        lowest_v_wind = v_wind[-1]
        wind_speed = _sqrt_nonnegative_with_finite_gradient(
            lowest_u_wind**2 + lowest_v_wind**2
        )
        wind_speed_meters_per_second = wind_speed / self.wind_unit_factor
        exchange_rate_per_second = (
            _OCEAN_BULK_SHF_TRANSFER_COEFFICIENT
            * wind_speed_meters_per_second
            / _OCEAN_BULK_SHF_EXCHANGE_DEPTH_METERS
        )
        max_exchange_rate_per_second = 1.0 / (
            _OCEAN_BULK_SHF_MIN_EFOLDING_DAYS * 24.0 * 3600.0
        )
        exchange_rate = (
            jnp.minimum(exchange_rate_per_second, max_exchange_rate_per_second)
            * self.rate_unit_factor
        )
        temperature_tendency = (
            self.ocean_weight
            * exchange_rate
            * (self.temperature_anchor - current_temperature)
        )
        max_temperature_tendency = (
            _OCEAN_BULK_SHF_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN
            * self.temperature_unit_factor
            / self.step_seconds
        )
        temperature_tendency = jnp.clip(
            temperature_tendency,
            -max_temperature_tendency,
            max_temperature_tendency,
        )
        finite_diagnostics = jnp.all(
            jnp.asarray(
                [
                    jnp.all(jnp.isfinite(self.ocean_weight)),
                    jnp.all(jnp.isfinite(self.temperature_anchor)),
                    jnp.all(jnp.isfinite(current_temperature)),
                    jnp.all(jnp.isfinite(lowest_u_wind)),
                    jnp.all(jnp.isfinite(lowest_v_wind)),
                    jnp.all(jnp.isfinite(wind_speed_meters_per_second)),
                    jnp.all(jnp.isfinite(exchange_rate)),
                    jnp.all(jnp.isfinite(temperature_tendency)),
                ]
            )
        )
        temperature_tendency = jnp.where(
            finite_diagnostics,
            temperature_tendency,
            jnp.zeros_like(temperature_tendency),
        )
        nodal_temperature_tendency = (
            jnp.zeros_like(nodal_temperature).at[-1].set(temperature_tendency)
        )
        modal_temperature_tendency = self.coords.horizontal.to_modal(
            nodal_temperature_tendency
        )
        modal_temperature_tendency = jnp.where(
            jnp.all(jnp.isfinite(modal_temperature_tendency)),
            modal_temperature_tendency,
            jnp.zeros_like(modal_temperature_tendency),
        )
        return primitive_equations.State(
            vorticity=jnp.zeros_like(state.vorticity),
            divergence=jnp.zeros_like(state.divergence),
            temperature_variation=modal_temperature_tendency,
            log_surface_pressure=jnp.zeros_like(state.log_surface_pressure),
            tracers=jax.tree_util.tree_map(jnp.zeros_like, state.tracers),
            sim_time=None if state.sim_time is None else 0.0,
        )


def _compose_ocean_bulk_sensible_heat_flux_equation(
    *,
    equation: Any,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    reference_temperature: np.ndarray,
    ocean_weight: jax.Array,
    temperature_anchor: jax.Array | None,
    step_seconds: float,
) -> Any:
    """Compose primitive equations with the opt-in ocean sensible heat flux."""
    if temperature_anchor is None:
        return equation
    forcing = _OceanBulkSensibleHeatFluxForcingSigma(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        ocean_weight=ocean_weight,
        temperature_anchor=temperature_anchor,
        step_seconds=step_seconds,
    )
    return time_integration.compose_equations([equation, forcing])


def _compose_weak_held_suarez_equation(
    *,
    equation: Any,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    reference_temperature: np.ndarray,
    kf_per_day: float,
    ka_timescale_days: float,
    ks_timescale_days: float,
    equilibrium_temperature_offset: jax.Array | None = None,
) -> Any:
    """Compose primitive equations with the fixed weak Held-Suarez forcing."""
    assert ka_timescale_days > 0.0
    assert ks_timescale_days > 0.0
    unit_registry = cast(Any, scales.units)
    day = unit_registry.day
    forcing = _TracerSafeHeldSuarezForcingSigma(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        kf=float(kf_per_day) / day,
        ka=1 / (float(ka_timescale_days) * day),
        ks=1 / (float(ks_timescale_days) * day),
        equilibrium_temperature_offset=equilibrium_temperature_offset,
    )
    return time_integration.compose_equations([equation, forcing])


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
