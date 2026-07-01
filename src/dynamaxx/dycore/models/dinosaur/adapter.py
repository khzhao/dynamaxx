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
    use_surface_layer_richardson_10m_wind_diagnostic: bool = False
    use_bulk_richardson_2m_temperature_diagnostic: bool = False
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
    apply_tropical_wtg_mass_dse_relaxation: bool = False
    apply_coupled_ekman_surface_closure: bool = False
    use_coriolis_scaled_ekman_depth: bool = False
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

        trajectory_fn = self._trajectory_function(
            coords=grid.coords,
            physics_specs=physics_specs,
            reference_temperature=reference_temperature,
            inner_steps=inner_steps,
            output_count=max(forecast_input.lead_steps) + 1,
            use_humidity_in_dynamics=has_humidity and self.use_humidity_in_dynamics,
            ocean_bulk_shf_ocean_weight=ocean_bulk_shf_ocean_weight,
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
                initialize_sim_time=self.use_pressure_ramped_vertical_dse_increment,
            )
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
                _, trajectory = trajectory_fn(
                    dinosaur_state,
                    ocean_bulk_shf_temperature_anchor,
                )
            else:
                _, trajectory = trajectory_fn(dinosaur_state)
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
        humidity_key = SPECIFIC_HUMIDITY_VARIABLE if use_humidity_in_dynamics else None
        use_analysis_offset_equilibrium = (
            self.apply_weak_held_suarez_relaxation
            and self.use_analysis_offset_weak_held_suarez_equilibrium
        )
        use_ocean_bulk_sensible_heat_flux = (
            self.apply_ocean_bulk_sensible_heat_flux
            and ocean_bulk_shf_ocean_weight is not None
        )

        def build_equation(
            equation_physics_specs: Any,
            equilibrium_temperature_offset: jax.Array | None = None,
            ocean_bulk_shf_temperature_anchor: jax.Array | None = None,
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
        ) -> Any:
            equation = build_equation(
                rollout_physics_specs,
                equilibrium_temperature_offset=equilibrium_temperature_offset,
                ocean_bulk_shf_temperature_anchor=ocean_bulk_shf_temperature_anchor,
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
                )
                dfi_filters = build_filters(physics_specs)
            elif use_ocean_bulk_sensible_heat_flux:
                dfi_equation = build_equation(
                    rollout_physics_specs,
                    equilibrium_temperature_offset=equilibrium_temperature_offset,
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
            trajectory_fn = time_integration.trajectory_from_step(
                step_fn,
                outer_steps=output_count,
                inner_steps=inner_steps,
                start_with_input=True,
            )
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
                base_trajectory_fn = trajectory_fn

                def initialized_trajectory_fn(dinosaur_state):
                    return base_trajectory_fn(initialize_state(dinosaur_state))

                trajectory_fn = initialized_trajectory_fn
            return trajectory_fn

        if use_analysis_offset_equilibrium:
            if use_ocean_bulk_sensible_heat_flux:

                def trajectory_fn(
                    dinosaur_state,
                    ocean_bulk_shf_temperature_anchor,
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
                    )
                    return offset_trajectory_fn(dinosaur_state)

            else:

                def trajectory_fn(dinosaur_state):
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
                    )
                    return offset_trajectory_fn(dinosaur_state)

        elif use_ocean_bulk_sensible_heat_flux:

            def trajectory_fn(
                dinosaur_state,
                ocean_bulk_shf_temperature_anchor,
            ):
                ocean_bulk_shf_trajectory_fn = build_trajectory(
                    ocean_bulk_shf_temperature_anchor=(
                        ocean_bulk_shf_temperature_anchor
                    ),
                )
                return ocean_bulk_shf_trajectory_fn(dinosaur_state)

        else:
            trajectory_fn = build_trajectory()
        return jax.jit(trajectory_fn) if self.jit_forecast else trajectory_fn

    def _ode_solver(self) -> Any:
        """Return the SIL3 solver, off-centered only for explicit opt-in models."""
        if self.semi_implicit_offcentering == 0.0:
            return time_integration.imex_rk_sil3
        return partial(
            time_integration.imex_rk_sil3,
            implicit_offcentering=self.semi_implicit_offcentering,
        )


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
        wind_speed_si = jnp.sqrt(
            jnp.maximum(lowest_u_wind_si**2 + lowest_v_wind_si**2, 0.0)
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
        applied_wind_increment = jnp.sqrt(
            jnp.maximum(u_increment[-1] ** 2 + v_increment[-1] ** 2, 0.0)
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


def digital_filter_dinosaur_dycore_model() -> DinosaurPrimitiveEquationsDycoreModel:
    """Return the side-by-side Dinosaur candidate with fixed short DFI enabled."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name="dinosaur_dfi",
        apply_digital_filter_initialization=True,
    )


def digital_filter_surface_residual_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the DFI candidate with decaying near-surface diagnostic residuals."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name="dinosaur_dfi_surface_residual",
        apply_digital_filter_initialization=True,
        apply_near_surface_residual_correction=True,
    )


def weak_held_suarez_dinosaur_dycore_model() -> DinosaurPrimitiveEquationsDycoreModel:
    """Return the DFI plus residual candidate with weak thermal HS relaxation."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name="dinosaur_dfi_surface_residual_weak_hs",
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
    )


def log_pressure_initialization_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the incumbent with log-pressure pressure-to-sigma initialization."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name="dinosaur_dfi_surface_residual_weak_hs_logp_init",
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
        use_log_pressure_initialization=True,
    )


def hydrostatic_temperature_initialization_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the incumbent plus hydrostatic-thickness temperature initialization."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name="dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init",
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
        use_log_pressure_initialization=True,
        use_hydrostatic_temperature_initialization=True,
    )


def layer_mean_hydrostatic_temperature_initialization_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the hydrostatic candidate with layer-mean temperature estimates."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name="dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init",
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
        use_log_pressure_initialization=True,
        use_hydrostatic_temperature_initialization=True,
        use_layer_mean_hydrostatic_temperature_initialization=True,
    )


def coriolis_split_dinosaur_dycore_model() -> DinosaurPrimitiveEquationsDycoreModel:
    """Return the incumbent with rollout-only exact Coriolis rotation splitting."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name=(
            "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
            "hydrostatic_layer_init_coriolis_split"
        ),
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
        use_log_pressure_initialization=True,
        use_hydrostatic_temperature_initialization=True,
        use_layer_mean_hydrostatic_temperature_initialization=True,
        apply_exact_coriolis_rotation_split=True,
    )


def coriolis_strang_split_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the exact-Coriolis split with symmetric rollout ordering."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name=(
            "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
            "hydrostatic_layer_init_coriolis_strang"
        ),
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
        use_log_pressure_initialization=True,
        use_hydrostatic_temperature_initialization=True,
        use_layer_mean_hydrostatic_temperature_initialization=True,
        apply_exact_coriolis_rotation_split=True,
        apply_symmetric_exact_coriolis_rotation_split=True,
    )


def stability_aware_surface_residual_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the Strang incumbent with stability-aware residual decay."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name=(
            "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
            "hydrostatic_layer_init_coriolis_strang_stability_surface_residual"
        ),
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
        use_stability_aware_near_surface_residual_decay=True,
        use_log_pressure_initialization=True,
        use_hydrostatic_temperature_initialization=True,
        use_layer_mean_hydrostatic_temperature_initialization=True,
        apply_exact_coriolis_rotation_split=True,
        apply_symmetric_exact_coriolis_rotation_split=True,
    )


def richardson_10m_wind_diagnostic_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the stability residual incumbent with Richardson 10 m wind output."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name=(
            "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
            "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
            "ri_10m_wind"
        ),
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
        use_stability_aware_near_surface_residual_decay=True,
        use_surface_layer_richardson_10m_wind_diagnostic=True,
        use_log_pressure_initialization=True,
        use_hydrostatic_temperature_initialization=True,
        use_layer_mean_hydrostatic_temperature_initialization=True,
        apply_exact_coriolis_rotation_split=True,
        apply_symmetric_exact_coriolis_rotation_split=True,
    )


def theta_tendency_dinosaur_dycore_model() -> DinosaurPrimitiveEquationsDycoreModel:
    """Return the Richardson 10 m incumbent with theta-form thermal tendency."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name=(
            "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
            "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
            "ri_10m_wind_theta_tendency"
        ),
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
        use_stability_aware_near_surface_residual_decay=True,
        use_surface_layer_richardson_10m_wind_diagnostic=True,
        use_log_pressure_initialization=True,
        use_hydrostatic_temperature_initialization=True,
        use_layer_mean_hydrostatic_temperature_initialization=True,
        apply_exact_coriolis_rotation_split=True,
        apply_symmetric_exact_coriolis_rotation_split=True,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
    )


def theta_mean_recenter_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the theta incumbent with rollout-only theta mean recentering."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name=(
            "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
            "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
            "ri_10m_wind_theta_tendency_theta_mean_recenter"
        ),
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
        use_stability_aware_near_surface_residual_decay=True,
        use_surface_layer_richardson_10m_wind_diagnostic=True,
        use_log_pressure_initialization=True,
        use_hydrostatic_temperature_initialization=True,
        use_layer_mean_hydrostatic_temperature_initialization=True,
        apply_exact_coriolis_rotation_split=True,
        apply_symmetric_exact_coriolis_rotation_split=True,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        apply_theta_layer_mean_recentering=True,
    )


def semi_implicit_offcenter_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the theta incumbent with fixed SIL3 implicit off-centering."""
    return DinosaurPrimitiveEquationsDycoreModel(
        name=(
            "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
            "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
            "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter"
        ),
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
        use_stability_aware_near_surface_residual_decay=True,
        use_surface_layer_richardson_10m_wind_diagnostic=True,
        use_log_pressure_initialization=True,
        use_hydrostatic_temperature_initialization=True,
        use_layer_mean_hydrostatic_temperature_initialization=True,
        apply_exact_coriolis_rotation_split=True,
        apply_symmetric_exact_coriolis_rotation_split=True,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        apply_theta_layer_mean_recentering=True,
        semi_implicit_offcentering=DEFAULT_SEMI_IMPLICIT_OFFCENTERING,
    )


def scale_separated_surface_residual_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the offcenter incumbent with scale-separated residual memory."""
    return replace(
        semi_implicit_offcenter_dinosaur_dycore_model(),
        name=(
            "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
            "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
            "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
            "scale_surface_residual"
        ),
        use_scale_separated_near_surface_residual=True,
    )


def analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the scale-residual incumbent with analysis-offset HS equilibrium."""
    return replace(
        scale_separated_surface_residual_dinosaur_dycore_model(),
        name=(
            "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
            "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
            "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
            "scale_surface_residual_analysis_hs_eq"
        ),
        use_analysis_offset_weak_held_suarez_equilibrium=True,
    )


def land_sea_surface_temperature_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the incumbent with land-sea-aware 2 m temperature residual memory."""
    return replace(
        analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model(),
        name=(
            "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
            "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
            "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
            "scale_surface_residual_analysis_hs_eq_landsea_surface"
        ),
        use_land_sea_surface_temperature_residual=True,
    )


def ocean_bulk_sensible_heat_flux_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the incumbent with weak ocean-only bulk sensible heat exchange."""
    return replace(
        land_sea_surface_temperature_dinosaur_dycore_model(),
        name=(
            "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
            "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
            "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
            "scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf"
        ),
        apply_ocean_bulk_sensible_heat_flux=True,
    )


def horizontal_semilagrangian_theta_transport_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the ocean-bulk incumbent with horizontal SL theta transport."""
    return replace(
        ocean_bulk_sensible_heat_flux_dinosaur_dycore_model(),
        name="dino_hsl_theta",
        use_horizontal_semilagrangian_theta_transport=True,
    )


def midpoint_semilagrangian_theta_departure_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return HSL theta with midpoint departure estimates for theta only."""
    return replace(
        horizontal_semilagrangian_theta_transport_dinosaur_dycore_model(),
        name="dino_hsl2_theta",
        use_midpoint_semilagrangian_theta_departure=True,
    )


def dry_static_energy_hsl_transport_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return HSL2 theta with dry-static-energy horizontal thermal transport."""
    return replace(
        midpoint_semilagrangian_theta_departure_dinosaur_dycore_model(),
        name="dino_hsl2_theta_dse_hsl",
        use_dry_static_energy_hsl_transport=True,
    )


def layer_mass_weighted_dse_hsl_transport_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return DSE-HSL with layer-mass-weighted horizontal thermal transport."""
    return replace(
        dry_static_energy_hsl_transport_dinosaur_dycore_model(),
        name="dino_hsl2_mass_dse",
        use_layer_mass_weighted_dse_hsl_transport=True,
    )


def tropical_wtg_mass_dse_relaxation_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return mass-DSE HSL with rollout-only tropical WTG thermal relaxation."""
    return replace(
        layer_mass_weighted_dse_hsl_transport_dinosaur_dycore_model(),
        name="dino_hsl2_mass_dse_wtg",
        apply_tropical_wtg_mass_dse_relaxation=True,
    )


def pressure_ramped_vertical_dse_wtg_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return WTG mass-DSE with guarded pressure-ramped vertical-DSE transport."""
    return replace(
        tropical_wtg_mass_dse_relaxation_dinosaur_dycore_model(),
        name="dino_hsl2_mass_dse_wtg_vdse_ramp",
        use_pressure_ramped_vertical_dse_increment=True,
    )


def land_ocean_low_mode_t2m_memory_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return vertical-DSE incumbent with late broad land/ocean T2m memory."""
    return replace(
        pressure_ramped_vertical_dse_wtg_dinosaur_dycore_model(),
        name="dino_hsl2_mass_dse_wtg_vdse_t2m_lomem",
        use_land_ocean_low_mode_t2m_memory=True,
    )


def bulk_richardson_2m_temperature_diagnostic_dinosaur_dycore_model() -> (
    DinosaurPrimitiveEquationsDycoreModel
):
    """Return the low-mode T2m incumbent with bounded raw 2 m temperature output."""
    return replace(
        land_ocean_low_mode_t2m_memory_dinosaur_dycore_model(),
        name="dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m",
        use_bulk_richardson_2m_temperature_diagnostic=True,
    )


def ekman_coupled_dinosaur_dycore_model() -> DinosaurPrimitiveEquationsDycoreModel:
    """Return the RI2m incumbent with weak coupled Ekman stress and pumping."""
    return replace(
        bulk_richardson_2m_temperature_diagnostic_dinosaur_dycore_model(),
        name="dino_ri2m_ekman_coupled",
        apply_coupled_ekman_surface_closure=True,
    )


def ekman_depth_dinosaur_dycore_model() -> DinosaurPrimitiveEquationsDycoreModel:
    """Return coupled Ekman with bounded Coriolis-scaled stress depth."""
    return replace(
        ekman_coupled_dinosaur_dycore_model(),
        name="dino_ri2m_ekman_depth",
        use_coriolis_scaled_ekman_depth=True,
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
) -> jax.Array:
    """Diagnose 2 m temperature with bounded lower-column theta extrapolation."""
    lowest_temperature = temperature[:, -1]
    if sigma_coords.layers < 2:
        return lowest_temperature

    lower_sigma = float(sigma_coords.centers[-1])
    upper_sigma = float(sigma_coords.centers[-2])
    lower_pressure_hpa = jnp.maximum(surface_pressure_hpa * lower_sigma, 1.0)
    upper_pressure_hpa = jnp.maximum(surface_pressure_hpa * upper_sigma, 1.0)
    screen_pressure_hpa = jnp.maximum(surface_pressure_hpa, 1.0)
    upper_temperature = temperature[:, -2]
    lower_theta = (
        lowest_temperature
        * (1000.0 / lower_pressure_hpa)
        ** _STABILITY_AWARE_POTENTIAL_TEMPERATURE_EXPONENT
    )
    upper_theta = (
        upper_temperature
        * (1000.0 / upper_pressure_hpa)
        ** _STABILITY_AWARE_POTENTIAL_TEMPERATURE_EXPONENT
    )
    mean_temperature = jnp.maximum(0.5 * (lowest_temperature + upper_temperature), 1.0)
    mean_theta = jnp.maximum(0.5 * (lower_theta + upper_theta), 1.0)

    pressure_ratio = jnp.maximum(lower_pressure_hpa / upper_pressure_hpa, 1.0)
    layer_separation_meters = (
        _DRY_AIR_GAS_CONSTANT_SI * mean_temperature / _GRAVITY_ACCELERATION_SI
    ) * jnp.log(pressure_ratio)
    lowest_layer_height_meters = (
        _DRY_AIR_GAS_CONSTANT_SI * lowest_temperature / _GRAVITY_ACCELERATION_SI
    ) * jnp.log(1.0 / max(lower_sigma, 1.0e-6))
    layer_separation_meters = jnp.maximum(layer_separation_meters, 1.0)
    lowest_layer_height_meters = jnp.maximum(
        lowest_layer_height_meters,
        _SURFACE_LAYER_TEMPERATURE_REFERENCE_HEIGHT_METERS,
    )

    lowest_u_wind = u_wind[:, -1]
    lowest_v_wind = v_wind[:, -1]
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
        screen_temperature - lowest_temperature,
        -_SURFACE_LAYER_TEMPERATURE_MAX_DEPARTURE_KELVIN,
        _SURFACE_LAYER_TEMPERATURE_MAX_DEPARTURE_KELVIN,
    )
    diagnosed_temperature = lowest_temperature + temperature_departure

    required_values = jnp.stack(
        [
            lowest_temperature,
            upper_temperature,
            lowest_u_wind,
            u_wind[:, -2],
            lowest_v_wind,
            v_wind[:, -2],
            surface_pressure_hpa,
            layer_separation_meters,
            lowest_layer_height_meters,
            diagnosed_temperature,
        ]
    )
    finite_mask = jnp.all(jnp.isfinite(required_values), axis=0) & (
        surface_pressure_hpa > 0.0
    )
    return jnp.where(finite_mask, diagnosed_temperature, lowest_temperature)


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
    shear = jnp.sqrt(jnp.maximum(squared_shear, 0.0))
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
        wind_speed = jnp.sqrt(jnp.maximum(lowest_u_wind**2 + lowest_v_wind**2, 0.0))
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
