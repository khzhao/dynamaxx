# Copyright 2026 dynamaxx

from dataclasses import replace
from typing import Any, cast

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from dynamaxx.dycore.models.dinosaur import adapter as dinosaur_adapter
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
from dynamaxx.dycore.models.dinosaur.adapter import (
    _ANALYSIS_OFFSET_HELD_SUAREZ_MAX_KELVIN,
    _ANALYSIS_OFFSET_HELD_SUAREZ_MAX_LONGITUDE_WAVENUMBER,
    _ANALYSIS_OFFSET_HELD_SUAREZ_MAX_TOTAL_WAVENUMBER,
    _DRY_AIR_GAS_CONSTANT_SI,
    _LAND_SEA_SURFACE_TEMPERATURE_OCEAN_DECAY_EXPONENT,
    _OCEAN_BULK_SHF_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN,
    _SCALE_SEPARATED_RESIDUAL_LOW_MODE_CUTOFF,
    _SCALE_SEPARATED_RESIDUAL_TAPER_ZERO_MODE,
    _TROPICAL_WTG_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN,
    DEFAULT_INNER_STEP_SECONDS,
    DEFAULT_SEMI_IMPLICIT_OFFCENTERING,
    DEFAULT_SPECTRAL_WAVENUMBERS,
    DEFAULT_WEAK_HELD_SUAREZ_KA_TIMESCALE_DAYS,
    DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY,
    DEFAULT_WEAK_HELD_SUAREZ_KS_TIMESCALE_DAYS,
    DinosaurPrimitiveEquationsDycoreModel,
    _analysis_offset_weak_held_suarez_equilibrium,
    _analysis_offset_weak_hs_low_mode_mask,
    _apply_near_surface_residual_correction,
    _apply_scale_separated_near_surface_residual_correction,
    _compose_ocean_bulk_sensible_heat_flux_equation,
    _compose_weak_held_suarez_equation,
    _exact_coriolis_rotation_step_filter,
    _horizontal_diffusion_step_filter,
    _hydrostatic_temperature_from_geopotential_thickness,
    _inner_steps_per_forecast_step,
    _interp_sigma_to_pressure_by_time,
    _land_sea_surface_temperature_residual_decays,
    _layer_mean_hydrostatic_temperature_from_geopotential_thickness,
    _nondimensionalize_seconds,
    _ocean_bulk_sensible_heat_flux_temperature_anchor,
    _OceanBulkSensibleHeatFluxForcingSigma,
    _pressure_coordinates,
    _primitive_equation,
    _primitive_equation_state,
    _reference_temperature,
    _scale_separated_residual_low_mode_mask,
    _split_near_surface_residual_by_scale,
    _stability_aware_near_surface_residual_decay_hours,
    _surface_layer_richardson_10m_wind,
    _symmetric_exact_coriolis_rotation_step,
    _theta_layer_mean_recenter_step_filter,
    _to_dinosaur_latitude_order,
    _TracerSafeHeldSuarezForcingSigma,
    _tropical_wtg_mass_dse_relaxation_step_filter,
    _unit_factor,
    _valid_land_sea_fraction_or_none,
    analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model,
    coriolis_split_dinosaur_dycore_model,
    coriolis_strang_split_dinosaur_dycore_model,
    digital_filter_dinosaur_dycore_model,
    digital_filter_surface_residual_dinosaur_dycore_model,
    dinosaur_state_to_weather_state,
    dry_static_energy_hsl_transport_dinosaur_dycore_model,
    horizontal_semilagrangian_theta_transport_dinosaur_dycore_model,
    hydrostatic_temperature_initialization_dinosaur_dycore_model,
    infer_dinosaur_pressure_levels,
    land_sea_surface_temperature_dinosaur_dycore_model,
    layer_mass_weighted_dse_hsl_transport_dinosaur_dycore_model,
    layer_mean_hydrostatic_temperature_initialization_dinosaur_dycore_model,
    log_pressure_initialization_dinosaur_dycore_model,
    midpoint_semilagrangian_theta_departure_dinosaur_dycore_model,
    ocean_bulk_sensible_heat_flux_dinosaur_dycore_model,
    pressure_ramped_vertical_dse_wtg_dinosaur_dycore_model,
    richardson_10m_wind_diagnostic_dinosaur_dycore_model,
    scale_separated_surface_residual_dinosaur_dycore_model,
    semi_implicit_offcenter_dinosaur_dycore_model,
    split_pressure_level_channel,
    stability_aware_surface_residual_dinosaur_dycore_model,
    supported_output_variables,
    theta_mean_recenter_dinosaur_dycore_model,
    theta_tendency_dinosaur_dycore_model,
    tropical_wtg_mass_dse_relaxation_dinosaur_dycore_model,
    weak_held_suarez_dinosaur_dycore_model,
    weather_state_to_dinosaur_state,
)
from dynamaxx.dycore.models.dinosaur.coordinates import grid_metadata
from dynamaxx.utils.consts import SECONDS_PER_HOUR
from dynamaxx.weather import ForecastInput, WeatherState


def test_split_pressure_level_channel_keeps_non_pressure_suffixes():
    """Pressure-level parsing ignores non-pressure numeric suffixes."""
    assert split_pressure_level_channel("temperature_500") == ("temperature", 500)
    assert split_pressure_level_channel("soil_temperature_level_4") == (
        "soil_temperature_level_4",
        None,
    )


def test_infer_dinosaur_pressure_levels_requires_temperature_and_winds():
    """Pressure levels require temperature and horizontal wind channels."""
    levels = infer_dinosaur_pressure_levels(
        (
            "temperature_500",
            "temperature_850",
            "u_component_of_wind_500",
            "u_component_of_wind_850",
            "v_component_of_wind_500",
            "v_component_of_wind_850",
        )
    )

    assert levels == (500, 850)

    with pytest.raises(AssertionError, match="pressure-level temperature"):
        infer_dinosaur_pressure_levels(("temperature_500",))


def test_supported_output_variables_filters_to_dinosaur_outputs():
    """Supported output filtering keeps only Dinosaur-emittable channels."""
    variables = supported_output_variables(
        (
            "temperature_500",
            "u_component_of_wind_500",
            "v_component_of_wind_500",
            "geopotential_500",
            "2m_temperature",
            "10m_u_component_of_wind",
            "mean_sea_level_pressure",
            "total_precipitation",
        ),
        pressure_levels_hpa=(500,),
        has_humidity=False,
        requested_variables=None,
    )

    assert variables == (
        "temperature_500",
        "u_component_of_wind_500",
        "v_component_of_wind_500",
        "geopotential_500",
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
    )


def test_default_dinosaur_configuration_keeps_t80_with_stable_inner_step():
    """Default Dinosaur settings keep T80 while using a stable inner step."""
    model = DinosaurPrimitiveEquationsDycoreModel()

    assert model.spectral_wavenumbers == DEFAULT_SPECTRAL_WAVENUMBERS == 80
    assert model.inner_step_seconds == DEFAULT_INNER_STEP_SECONDS == 900.0
    assert not model.apply_digital_filter_initialization
    assert model.digital_filter_time_span_seconds == 6 * SECONDS_PER_HOUR
    assert model.digital_filter_cutoff_seconds == 6 * SECONDS_PER_HOUR
    assert not model.apply_near_surface_residual_correction
    assert model.near_surface_residual_decay_hours == 48.0
    assert not model.use_analysis_offset_weak_held_suarez_equilibrium
    assert not model.use_stability_aware_near_surface_residual_decay
    assert not model.use_scale_separated_near_surface_residual
    assert not model.use_land_sea_surface_temperature_residual
    assert not model.use_surface_layer_richardson_10m_wind_diagnostic
    assert not model.use_log_pressure_initialization
    assert not model.apply_weak_held_suarez_relaxation
    assert not model.apply_exact_coriolis_rotation_split
    assert not model.apply_symmetric_exact_coriolis_rotation_split
    assert not model.apply_theta_layer_mean_recentering
    assert not model.use_midpoint_semilagrangian_theta_departure
    assert model.semi_implicit_offcentering == 0.0
    assert (
        model.temperature_tendency_formulation
        == primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_TEMPERATURE
    )
    assert model.weak_held_suarez_kf_per_day == DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY
    assert (
        model.weak_held_suarez_ka_timescale_days
        == DEFAULT_WEAK_HELD_SUAREZ_KA_TIMESCALE_DAYS
    )
    assert (
        model.weak_held_suarez_ks_timescale_days
        == DEFAULT_WEAK_HELD_SUAREZ_KS_TIMESCALE_DAYS
    )
    assert (
        _inner_steps_per_forecast_step(
            step_seconds=6 * SECONDS_PER_HOUR,
            inner_step_seconds=model.inner_step_seconds,
        )
        == 24
    )


def test_digital_filter_dinosaur_factory_enables_fixed_initialization():
    """The DFI candidate opts into the fixed short Lanczos initialization."""
    model = digital_filter_dinosaur_dycore_model()

    assert model.name == "dinosaur_dfi"
    assert model.apply_digital_filter_initialization
    assert not model.apply_near_surface_residual_correction
    assert model.digital_filter_time_span_seconds == 6 * SECONDS_PER_HOUR
    assert model.digital_filter_cutoff_seconds == 6 * SECONDS_PER_HOUR


def test_digital_filter_surface_residual_factory_enables_guarded_correction():
    """The near-surface residual candidate preserves DFI and opts into correction."""
    model = digital_filter_surface_residual_dinosaur_dycore_model()

    assert model.name == "dinosaur_dfi_surface_residual"
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.near_surface_residual_decay_hours == 48.0


def test_weak_held_suarez_factory_preserves_incumbent_corrections():
    """The weak HS candidate keeps DFI and near-surface residual correction."""
    model = weak_held_suarez_dinosaur_dycore_model()

    assert model.name == "dinosaur_dfi_surface_residual_weak_hs"
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert not model.use_log_pressure_initialization
    assert model.weak_held_suarez_kf_per_day == 0.0
    assert model.weak_held_suarez_ka_timescale_days == 160.0
    assert model.weak_held_suarez_ks_timescale_days == 16.0


def test_log_pressure_initialization_factory_preserves_incumbent_settings():
    """The log-pressure candidate keeps the accepted weak HS configuration."""
    model = log_pressure_initialization_dinosaur_dycore_model()
    incumbent = weak_held_suarez_dinosaur_dycore_model()

    assert model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init"
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert not incumbent.use_log_pressure_initialization
    assert model.inner_step_seconds == DEFAULT_INNER_STEP_SECONDS == 900.0
    assert model.spectral_wavenumbers == DEFAULT_SPECTRAL_WAVENUMBERS == 80
    assert model.apply_spectral_filter
    assert model.horizontal_diffusion_order == 2
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection
    assert model.reference_temperature_kelvin == 250.0
    assert model.output_variables is None
    assert model.weak_held_suarez_kf_per_day == 0.0
    assert model.weak_held_suarez_ka_timescale_days == 160.0
    assert model.weak_held_suarez_ks_timescale_days == 16.0


def test_hydrostatic_temperature_initialization_factory_extends_incumbent():
    """The hydrostatic candidate preserves incumbent settings and adds one flag."""
    model = hydrostatic_temperature_initialization_dinosaur_dycore_model()
    incumbent = log_pressure_initialization_dinosaur_dycore_model()

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert not incumbent.use_hydrostatic_temperature_initialization
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert model.reference_temperature_kelvin == incumbent.reference_temperature_kelvin
    assert model.output_variables == incumbent.output_variables
    assert model.weak_held_suarez_kf_per_day == incumbent.weak_held_suarez_kf_per_day
    assert (
        model.weak_held_suarez_ka_timescale_days
        == incumbent.weak_held_suarez_ka_timescale_days
    )
    assert (
        model.weak_held_suarez_ks_timescale_days
        == incumbent.weak_held_suarez_ks_timescale_days
    )


def test_layer_mean_hydrostatic_temperature_initialization_factory_extends_incumbent():
    """The layer-mean candidate preserves incumbent settings and changes estimator."""
    model = layer_mean_hydrostatic_temperature_initialization_dinosaur_dycore_model()
    incumbent = hydrostatic_temperature_initialization_dinosaur_dycore_model()

    assert (
        model.name
        == "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert not incumbent.use_layer_mean_hydrostatic_temperature_initialization
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert model.reference_temperature_kelvin == incumbent.reference_temperature_kelvin
    assert model.output_variables == incumbent.output_variables
    assert model.weak_held_suarez_kf_per_day == incumbent.weak_held_suarez_kf_per_day
    assert (
        model.weak_held_suarez_ka_timescale_days
        == incumbent.weak_held_suarez_ka_timescale_days
    )
    assert (
        model.weak_held_suarez_ks_timescale_days
        == incumbent.weak_held_suarez_ks_timescale_days
    )
    assert not model.apply_exact_coriolis_rotation_split


def test_coriolis_split_factory_preserves_incumbent_options_except_split():
    """The split candidate changes only name and the exact-Coriolis option."""
    model = coriolis_split_dinosaur_dycore_model()
    incumbent = (
        layer_mean_hydrostatic_temperature_initialization_dinosaur_dycore_model()
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_split"
    )
    assert model.apply_exact_coriolis_rotation_split
    assert not incumbent.apply_exact_coriolis_rotation_split
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "apply_exact_coriolis_rotation_split"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_coriolis_strang_factory_preserves_incumbent_options_except_ordering():
    """The Strang candidate changes only name and symmetric split ordering."""
    model = coriolis_strang_split_dinosaur_dycore_model()
    incumbent = coriolis_split_dinosaur_dycore_model()

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang"
    )
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert not incumbent.apply_symmetric_exact_coriolis_rotation_split
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "apply_symmetric_exact_coriolis_rotation_split"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_stability_aware_residual_factory_preserves_incumbent_except_decay():
    """The candidate changes only the residual decay option and model name."""
    model = stability_aware_surface_residual_dinosaur_dycore_model()
    incumbent = coriolis_strang_split_dinosaur_dycore_model()

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual"
    )
    assert model.use_stability_aware_near_surface_residual_decay
    assert not incumbent.use_stability_aware_near_surface_residual_decay
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {
            "name",
            "use_stability_aware_near_surface_residual_decay",
        }:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_richardson_10m_wind_factory_preserves_incumbent_except_diagnostic():
    """The candidate changes only name and the raw 10 m wind diagnostic option."""
    model = richardson_10m_wind_diagnostic_dinosaur_dycore_model()
    incumbent = stability_aware_surface_residual_dinosaur_dycore_model()

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind"
    )
    assert model.use_surface_layer_richardson_10m_wind_diagnostic
    assert not incumbent.use_surface_layer_richardson_10m_wind_diagnostic
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {
            "name",
            "use_surface_layer_richardson_10m_wind_diagnostic",
        }:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_theta_tendency_factory_preserves_incumbent_except_thermal_formulation():
    """The theta candidate changes only name and thermodynamic tendency form."""
    model = theta_tendency_dinosaur_dycore_model()
    incumbent = richardson_10m_wind_diagnostic_dinosaur_dycore_model()

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency"
    )
    assert (
        model.temperature_tendency_formulation
        == primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
    )
    assert (
        incumbent.temperature_tendency_formulation
        == primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_TEMPERATURE
    )
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "temperature_tendency_formulation"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_theta_mean_recenter_factory_preserves_incumbent_except_wrapper():
    """The recentering candidate changes only name and the rollout wrapper."""
    model = theta_mean_recenter_dinosaur_dycore_model()
    incumbent = theta_tendency_dinosaur_dycore_model()

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter"
    )
    assert model.apply_theta_layer_mean_recentering
    assert not incumbent.apply_theta_layer_mean_recentering
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "apply_theta_layer_mean_recentering"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_semi_implicit_offcenter_factory_preserves_incumbent_except_epsilon():
    """The candidate changes only name and the SIL3 off-centering weight."""
    model = semi_implicit_offcenter_dinosaur_dycore_model()
    incumbent = theta_mean_recenter_dinosaur_dycore_model()

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter"
    )
    assert (
        model.semi_implicit_offcentering == DEFAULT_SEMI_IMPLICIT_OFFCENTERING == 0.05
    )
    assert incumbent.semi_implicit_offcentering == 0.0
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "semi_implicit_offcentering"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_scale_separated_residual_factory_preserves_incumbent_except_selector():
    """The candidate changes only name and the residual scale selector."""
    model = scale_separated_surface_residual_dinosaur_dycore_model()
    incumbent = semi_implicit_offcenter_dinosaur_dycore_model()

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual"
    )
    assert model.use_scale_separated_near_surface_residual
    assert not incumbent.use_scale_separated_near_surface_residual
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "use_scale_separated_near_surface_residual"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_analysis_offset_hs_eq_factory_preserves_incumbent_except_selector():
    """The candidate changes only name and the analysis-HS-equilibrium selector."""
    model = analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model()
    incumbent = scale_separated_surface_residual_dinosaur_dycore_model()

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq"
    )
    assert model.use_analysis_offset_weak_held_suarez_equilibrium
    assert not incumbent.use_analysis_offset_weak_held_suarez_equilibrium
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {
            "name",
            "use_analysis_offset_weak_held_suarez_equilibrium",
        }:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_land_sea_surface_temperature_factory_preserves_incumbent_except_selector():
    """The candidate changes only name and the land-sea residual selector."""
    model = land_sea_surface_temperature_dinosaur_dycore_model()
    incumbent = analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model()

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface"
    )
    assert model.use_land_sea_surface_temperature_residual
    assert not incumbent.use_land_sea_surface_temperature_residual
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "use_land_sea_surface_temperature_residual"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_ocean_bulk_shf_factory_preserves_incumbent_except_selector():
    """The candidate changes only name and the ocean bulk SHF selector."""
    model = ocean_bulk_sensible_heat_flux_dinosaur_dycore_model()
    incumbent = land_sea_surface_temperature_dinosaur_dycore_model()

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf"
    )
    assert model.apply_ocean_bulk_sensible_heat_flux
    assert not incumbent.apply_ocean_bulk_sensible_heat_flux
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "apply_ocean_bulk_sensible_heat_flux"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_hsl_theta_factory_preserves_incumbent_except_selector():
    """The short candidate changes only name and horizontal theta transport."""
    model = horizontal_semilagrangian_theta_transport_dinosaur_dycore_model()
    incumbent = ocean_bulk_sensible_heat_flux_dinosaur_dycore_model()

    assert model.name == "dino_hsl_theta"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert not incumbent.use_horizontal_semilagrangian_theta_transport
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "use_horizontal_semilagrangian_theta_transport"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_hsl2_theta_factory_preserves_hsl_theta_except_midpoint_selector():
    """The midpoint candidate changes only name and theta departure selector."""
    model = midpoint_semilagrangian_theta_departure_dinosaur_dycore_model()
    incumbent = horizontal_semilagrangian_theta_transport_dinosaur_dycore_model()

    assert model.name == "dino_hsl2_theta"
    assert len(model.name) < 32
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert incumbent.use_horizontal_semilagrangian_theta_transport
    assert not incumbent.use_midpoint_semilagrangian_theta_departure
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "use_midpoint_semilagrangian_theta_departure"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dse_hsl_factory_preserves_hsl2_theta_except_selector():
    """The DSE-HSL candidate changes only name and the DSE transport selector."""
    model = dry_static_energy_hsl_transport_dinosaur_dycore_model()
    incumbent = midpoint_semilagrangian_theta_departure_dinosaur_dycore_model()

    assert model.name == "dino_hsl2_theta_dse_hsl"
    assert len(model.name) < 32
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert not incumbent.use_dry_static_energy_hsl_transport
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "use_dry_static_energy_hsl_transport"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_layer_mass_dse_factory_preserves_dse_hsl_except_selector():
    """The mass-DSE candidate changes only name and mass-DSE selector."""
    model = layer_mass_weighted_dse_hsl_transport_dinosaur_dycore_model()
    incumbent = dry_static_energy_hsl_transport_dinosaur_dycore_model()

    assert model.name == "dino_hsl2_mass_dse"
    assert len(model.name) < 32
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert not incumbent.use_layer_mass_weighted_dse_hsl_transport
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "use_layer_mass_weighted_dse_hsl_transport"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_tropical_wtg_factory_preserves_mass_dse_except_selector():
    """The WTG candidate changes only name and rollout WTG selector."""
    model = tropical_wtg_mass_dse_relaxation_dinosaur_dycore_model()
    incumbent = layer_mass_weighted_dse_hsl_transport_dinosaur_dycore_model()

    assert model.name == "dino_hsl2_mass_dse_wtg"
    assert len(model.name) < 32
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert not incumbent.apply_tropical_wtg_mass_dse_relaxation
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "apply_tropical_wtg_mass_dse_relaxation"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_pressure_ramped_vertical_dse_factory_preserves_wtg_except_selector():
    """The candidate changes only name and the vertical-DSE ramp selector."""
    model = pressure_ramped_vertical_dse_wtg_dinosaur_dycore_model()
    incumbent = tropical_wtg_mass_dse_relaxation_dinosaur_dycore_model()

    assert model.name == "dino_hsl2_mass_dse_wtg_vdse_ramp"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert model.use_pressure_ramped_vertical_dse_increment
    assert not incumbent.use_pressure_ramped_vertical_dse_increment
    for field_name in DinosaurPrimitiveEquationsDycoreModel.__dataclass_fields__:
        if field_name in {"name", "use_pressure_ramped_vertical_dse_increment"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_imex_rk_sil3_zero_offcentering_matches_centered_step():
    """SIL3 epsilon=0 keeps the incumbent centered tableau path unchanged."""
    equation = _linear_implicit_oscillator_equation(frequency=2.0)
    initial_state = jnp.asarray([1.0, 0.25], dtype=jnp.float32)

    centered_step = time_integration.imex_rk_sil3(equation, time_step=0.1)
    zero_offcentered_step = time_integration.imex_rk_sil3(
        equation,
        time_step=0.1,
        implicit_offcentering=0.0,
    )

    np.testing.assert_array_equal(
        zero_offcentered_step(initial_state),
        centered_step(initial_state),
    )


def test_imex_rk_sil3_offcentering_damps_fast_implicit_mode():
    """Positive off-centering damps a fast mode while preserving a slow one."""
    initial_state = jnp.asarray([1.0, 0.0], dtype=jnp.float32)
    fast_equation = _linear_implicit_oscillator_equation(frequency=20.0)
    slow_equation = _linear_implicit_oscillator_equation(frequency=0.1)

    centered_fast_step = time_integration.imex_rk_sil3(
        fast_equation,
        time_step=0.2,
    )
    offcentered_fast_step = time_integration.imex_rk_sil3(
        fast_equation,
        time_step=0.2,
        implicit_offcentering=DEFAULT_SEMI_IMPLICIT_OFFCENTERING,
    )
    fast_centered_amplitude = jnp.linalg.norm(centered_fast_step(initial_state))
    fast_offcentered_amplitude = jnp.linalg.norm(offcentered_fast_step(initial_state))

    centered_slow_step = time_integration.imex_rk_sil3(
        slow_equation,
        time_step=0.2,
    )
    offcentered_slow_step = time_integration.imex_rk_sil3(
        slow_equation,
        time_step=0.2,
        implicit_offcentering=DEFAULT_SEMI_IMPLICIT_OFFCENTERING,
    )
    slow_centered_amplitude = jnp.linalg.norm(centered_slow_step(initial_state))
    slow_offcentered_amplitude = jnp.linalg.norm(offcentered_slow_step(initial_state))

    assert fast_offcentered_amplitude < 0.95 * fast_centered_amplitude
    assert abs(float(slow_offcentered_amplitude) - 1.0) < 1e-3
    assert abs(float(slow_offcentered_amplitude - slow_centered_amplitude)) < 1e-3


def test_imex_rk_sil3_offcentered_step_falls_back_on_nonfinite_state():
    """The positive-offcentering path locally falls back to centered SIL3."""

    def explicit_terms(state):
        return jnp.zeros_like(state)

    def implicit_terms(state):
        return state

    def implicit_inverse(state, step_size):
        return jnp.where(
            step_size > 0.36,
            jnp.full_like(state, jnp.nan),
            state,
        )

    equation = time_integration.ImplicitExplicitODE.from_functions(
        explicit_terms,
        implicit_terms,
        implicit_inverse,
    )
    initial_state = jnp.asarray([1.0, -0.5], dtype=jnp.float32)
    centered_step = time_integration.imex_rk_sil3(equation, time_step=1.0)
    offcentered_step = time_integration.imex_rk_sil3(
        equation,
        time_step=1.0,
        implicit_offcentering=DEFAULT_SEMI_IMPLICIT_OFFCENTERING,
    )

    np.testing.assert_array_equal(
        offcentered_step(initial_state),
        centered_step(initial_state),
    )


def test_dinosaur_forecast_returns_requested_channels():
    """Dinosaur forecasts return requested channels in requested order."""
    output_variables = (
        "temperature_250",
        "u_component_of_wind_750",
        "v_component_of_wind_750",
        "geopotential_250",
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
    )
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        output_variables=output_variables,
        include_vertical_advection=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0, 1, 2))

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (3, 1, len(output_variables), 4, 3)
    np.testing.assert_allclose(
        forecast.values[0, 0, 0],
        np.full((4, 3), 250.0),
        atol=1e-4,
    )
    np.testing.assert_allclose(
        forecast.values[0, 0, 4],
        np.full((4, 3), 285.0),
        atol=1e-4,
    )
    np.testing.assert_allclose(
        forecast.values[0, 0, 6],
        np.full((4, 3), 100000.0),
        rtol=1e-5,
    )


def test_dinosaur_forecast_with_digital_filter_initialization_is_finite(monkeypatch):
    """DFI preserves the forecast contract and emits finite requested outputs."""
    dfi_calls = []

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        dfi_calls.append(
            {
                "equation": equation,
                "ode_solver": ode_solver,
                "filters": filters,
                "time_span": time_span,
                "cutoff_period": cutoff_period,
                "dt": dt,
            }
        )
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "temperature_250",
        "u_component_of_wind_750",
        "mean_sea_level_pressure",
    )
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        output_variables=output_variables,
        include_vertical_advection=False,
        apply_digital_filter_initialization=True,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0, 1))

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())
    assert len(dfi_calls) == 1


def test_weak_held_suarez_forecast_returns_finite_requested_channels(monkeypatch):
    """The forced DFI path preserves requested output channels and shapes."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        include_vertical_advection=False,
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())
    np.testing.assert_array_equal(
        forecast.select(("2m_temperature",)).values[0],
        forecast_input.initial_state.select(("2m_temperature",)).values,
    )
    np.testing.assert_array_equal(
        forecast.select(("10m_u_component_of_wind",)).values[0],
        forecast_input.initial_state.select(("10m_u_component_of_wind",)).values,
    )


def test_log_pressure_initialization_candidate_forecast_is_finite(monkeypatch):
    """The side-by-side log-pressure candidate runs a small non-JIT forecast."""
    log_pressure_calls = []
    real_log_pressure_interpolation = (
        vertical_interpolation.interp_pressure_to_sigma_log_pressure
    )

    def record_log_pressure_interpolation(*args, **kwargs):
        log_pressure_calls.append(True)
        return real_log_pressure_interpolation(*args, **kwargs)

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        vertical_interpolation,
        "interp_pressure_to_sigma_log_pressure",
        record_log_pressure_interpolation,
    )
    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        log_pressure_initialization_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert log_pressure_calls == [True]
    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())


def test_hydrostatic_temperature_initialization_candidate_forecast_is_finite(
    monkeypatch,
):
    """The side-by-side hydrostatic candidate runs a small non-JIT forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        hydrostatic_temperature_initialization_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())


def test_coriolis_split_candidate_forecast_is_finite(monkeypatch):
    """The exact-Coriolis split candidate runs a small non-JIT forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        coriolis_split_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())


def test_coriolis_strang_split_candidate_forecast_is_finite(monkeypatch):
    """The symmetric exact-Coriolis split runs a small non-JIT forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        coriolis_strang_split_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())


def test_stability_aware_surface_residual_candidate_forecast_is_finite(monkeypatch):
    """The stability-aware residual candidate runs a small non-JIT forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        stability_aware_surface_residual_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())


def test_richardson_10m_wind_candidate_forecast_is_finite(monkeypatch):
    """The Richardson 10 m wind candidate runs a small non-JIT forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        richardson_10m_wind_diagnostic_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())
    np.testing.assert_array_equal(
        forecast.select(("10m_u_component_of_wind",)).values[0],
        forecast_input.initial_state.select(("10m_u_component_of_wind",)).values,
    )


def test_theta_tendency_candidate_forecast_is_finite(monkeypatch):
    """The theta-tendency candidate runs a small non-JIT smoke forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        theta_tendency_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())
    np.testing.assert_array_equal(
        forecast.select(("10m_u_component_of_wind",)).values[0],
        forecast_input.initial_state.select(("10m_u_component_of_wind",)).values,
    )


def test_theta_mean_recenter_candidate_forecast_is_finite(monkeypatch):
    """The theta-recenter candidate runs a small non-JIT smoke forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        theta_mean_recenter_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())
    np.testing.assert_array_equal(
        forecast.select(("10m_u_component_of_wind",)).values[0],
        forecast_input.initial_state.select(("10m_u_component_of_wind",)).values,
    )


def test_semi_implicit_offcenter_candidate_forecast_is_finite(monkeypatch):
    """The offcentered SIL3 candidate runs a small non-JIT smoke forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        semi_implicit_offcenter_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())
    np.testing.assert_array_equal(
        forecast.select(("10m_u_component_of_wind",)).values[0],
        forecast_input.initial_state.select(("10m_u_component_of_wind",)).values,
    )


def test_scale_separated_residual_candidate_forecast_is_finite(monkeypatch):
    """The scale-separated residual candidate runs a small non-JIT forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        scale_separated_surface_residual_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())
    np.testing.assert_array_equal(
        forecast.select(("2m_temperature",)).values[0],
        forecast_input.initial_state.select(("2m_temperature",)).values,
    )
    np.testing.assert_array_equal(
        forecast.select(("10m_u_component_of_wind",)).values[0],
        forecast_input.initial_state.select(("10m_u_component_of_wind",)).values,
    )


def test_analysis_offset_hs_eq_candidate_forecast_is_finite(monkeypatch):
    """The analysis-offset HS-equilibrium candidate runs a non-JIT smoke forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())
    np.testing.assert_array_equal(
        forecast.select(("2m_temperature",)).values[0],
        forecast_input.initial_state.select(("2m_temperature",)).values,
    )
    np.testing.assert_array_equal(
        forecast.select(("10m_u_component_of_wind",)).values[0],
        forecast_input.initial_state.select(("10m_u_component_of_wind",)).values,
    )


def test_land_sea_surface_temperature_candidate_forecast_is_finite(monkeypatch):
    """The land-sea T2m residual candidate runs a non-JIT smoke forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    def fake_land_sea_fraction(*, longitude, latitude, initial_time):
        del initial_time
        return jnp.ones((longitude.size, latitude.size), dtype=jnp.float32)

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    monkeypatch.setattr(
        dinosaur_adapter,
        "_load_land_sea_fraction_for_grid",
        fake_land_sea_fraction,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        land_sea_surface_temperature_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())
    np.testing.assert_array_equal(
        forecast.select(("2m_temperature",)).values[0],
        forecast_input.initial_state.select(("2m_temperature",)).values,
    )
    np.testing.assert_array_equal(
        forecast.select(("10m_u_component_of_wind",)).values[0],
        forecast_input.initial_state.select(("10m_u_component_of_wind",)).values,
    )


def test_near_surface_residual_forecast_preserves_mass_diagnostics(monkeypatch):
    """The residual candidate changes only selected near-surface diagnostics."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )
    dfi_model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        include_vertical_advection=False,
        apply_digital_filter_initialization=True,
        jit_forecast=False,
    )
    residual_model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        include_vertical_advection=False,
        apply_digital_filter_initialization=True,
        apply_near_surface_residual_correction=True,
        jit_forecast=False,
    )

    raw_forecast = dfi_model.forecast(forecast_input)
    corrected_forecast = residual_model.forecast(forecast_input)

    initial_temperature = forecast_input.initial_state.select(("2m_temperature",))
    initial_u_wind = forecast_input.initial_state.select(("10m_u_component_of_wind",))
    np.testing.assert_array_equal(
        corrected_forecast.select(("2m_temperature",)).values[0],
        initial_temperature.values,
    )
    np.testing.assert_array_equal(
        corrected_forecast.select(("10m_u_component_of_wind",)).values[0],
        initial_u_wind.values,
    )
    np.testing.assert_array_equal(
        corrected_forecast.select(("geopotential_500",)).values,
        raw_forecast.select(("geopotential_500",)).values,
    )
    np.testing.assert_array_equal(
        corrected_forecast.select(("mean_sea_level_pressure",)).values,
        raw_forecast.select(("mean_sea_level_pressure",)).values,
    )


def test_near_surface_residual_correction_matches_initial_and_decays():
    """Corrected diagnostics match analysis at lead 0 and decay afterward."""
    spatial_pattern = jnp.arange(12, dtype=jnp.float32).reshape(4, 3) / 10.0
    raw_temperature = jnp.stack(
        [
            280.0 + spatial_pattern,
            281.0 + spatial_pattern,
            282.0 + spatial_pattern,
        ]
    )
    raw_u_wind = jnp.stack(
        [
            1.0 + spatial_pattern,
            1.5 + spatial_pattern,
            2.0 + spatial_pattern,
        ]
    )
    raw_geopotential = jnp.stack(
        [
            5000.0 + spatial_pattern,
            5001.0 + spatial_pattern,
            5002.0 + spatial_pattern,
        ]
    )
    raw_pressure = jnp.stack(
        [
            100000.0 + spatial_pattern,
            99900.0 + spatial_pattern,
            99800.0 + spatial_pattern,
        ]
    )
    trajectory_state = WeatherState(
        values=jnp.stack(
            [raw_temperature, raw_u_wind, raw_geopotential, raw_pressure],
            axis=1,
        ),
        variables=(
            "2m_temperature",
            "10m_u_component_of_wind",
            "geopotential_500",
            "mean_sea_level_pressure",
        ),
    )
    initial_temperature = 285.0 + spatial_pattern
    initial_u_wind = 4.0 + spatial_pattern
    initial_state = WeatherState(
        values=jnp.stack([initial_temperature, initial_u_wind]),
        variables=("2m_temperature", "10m_u_component_of_wind"),
    )

    corrected = _apply_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(0, 1, 2),
        lead_hours=(0, 24, 96),
        decay_hours=48.0,
    )

    decay = jnp.exp(-jnp.asarray([0.0, 24.0, 96.0]) / 48.0)
    expected_temperature = (
        raw_temperature
        + (initial_temperature - raw_temperature[0])[jnp.newaxis, ...]
        * decay[:, jnp.newaxis, jnp.newaxis]
    )
    expected_u_wind = (
        raw_u_wind
        + (initial_u_wind - raw_u_wind[0])[jnp.newaxis, ...]
        * decay[:, jnp.newaxis, jnp.newaxis]
    )
    expected_temperature = expected_temperature.at[0].set(initial_temperature)
    expected_u_wind = expected_u_wind.at[0].set(initial_u_wind)

    np.testing.assert_array_equal(
        corrected.select(("2m_temperature",)).values[0, 0],
        initial_temperature,
    )
    np.testing.assert_array_equal(
        corrected.select(("10m_u_component_of_wind",)).values[0, 0],
        initial_u_wind,
    )
    np.testing.assert_allclose(
        corrected.select(("2m_temperature",)).values[:, 0],
        expected_temperature,
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        corrected.select(("10m_u_component_of_wind",)).values[:, 0],
        expected_u_wind,
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_array_equal(
        corrected.select(("geopotential_500", "mean_sea_level_pressure")).values,
        trajectory_state.select(("geopotential_500", "mean_sea_level_pressure")).values,
    )


def test_near_surface_residual_correction_skips_missing_channels():
    """Residuals are skipped when either analysis or output channel is absent."""
    raw_u_wind = jnp.stack(
        [
            jnp.full((4, 3), 1.0, dtype=jnp.float32),
            jnp.full((4, 3), 2.0, dtype=jnp.float32),
        ]
    )
    raw_geopotential = jnp.stack(
        [
            jnp.full((4, 3), 5000.0, dtype=jnp.float32),
            jnp.full((4, 3), 5001.0, dtype=jnp.float32),
        ]
    )
    trajectory_state = WeatherState(
        values=jnp.stack([raw_u_wind, raw_geopotential], axis=1),
        variables=("10m_u_component_of_wind", "geopotential_500"),
    )
    initial_state = WeatherState(
        values=jnp.stack([jnp.full((4, 3), 285.0, dtype=jnp.float32)]),
        variables=("2m_temperature",),
    )

    corrected = _apply_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(1,),
        lead_hours=(24,),
        decay_hours=48.0,
    )

    np.testing.assert_array_equal(corrected.values, trajectory_state.values[1:2])


def test_scale_separated_residual_mask_protects_low_modes_and_tapers():
    """The fixed low-mode mask protects n<=12 and tapers to zero by n=20."""
    horizontal_grid = _residual_split_test_grid()

    low_mode_mask = np.asarray(_scale_separated_residual_low_mode_mask(horizontal_grid))

    _, total_wavenumber = horizontal_grid.modal_mesh
    valid_modes = np.asarray(horizontal_grid.mask)
    assert np.isfinite(low_mode_mask).all()
    np.testing.assert_array_equal(low_mode_mask[~valid_modes], 0.0)
    np.testing.assert_allclose(
        low_mode_mask[
            valid_modes
            & (total_wavenumber <= _SCALE_SEPARATED_RESIDUAL_LOW_MODE_CUTOFF)
        ],
        1.0,
        rtol=0.0,
        atol=0.0,
    )
    np.testing.assert_array_equal(
        low_mode_mask[
            valid_modes
            & (total_wavenumber >= _SCALE_SEPARATED_RESIDUAL_TAPER_ZERO_MODE)
        ],
        0.0,
    )
    taper_modes = low_mode_mask[valid_modes & (total_wavenumber == 16)]
    assert taper_modes.size > 0
    assert float(np.min(taper_modes)) > 0.0
    assert float(np.max(taper_modes)) < 1.0


def test_scale_separated_residual_split_reconstructs_and_keeps_low_modes():
    """Low plus high residual reconstructs, and pure low modes do not leak."""
    horizontal_grid = _residual_split_test_grid()
    _, total_wavenumber = horizontal_grid.modal_mesh
    valid_low_modes = np.asarray(horizontal_grid.mask) & (total_wavenumber <= 4)
    modal_residual = jnp.asarray(
        np.where(
            valid_low_modes,
            0.02 * (1.0 + total_wavenumber),
            0.0,
        ),
        dtype=jnp.float32,
    )
    residual_model_order = horizontal_grid.to_nodal(modal_residual)
    residual_weather_order = residual_model_order[:, ::-1]

    low_mode_residual, high_mode_residual, split_is_valid = (
        _split_near_surface_residual_by_scale(
            residual_weather_order,
            horizontal_grid=horizontal_grid,
            latitude_reversed=True,
        )
    )

    assert bool(split_is_valid)
    np.testing.assert_allclose(
        low_mode_residual + high_mode_residual,
        residual_weather_order,
        rtol=1e-5,
        atol=1e-5,
    )
    np.testing.assert_allclose(
        low_mode_residual,
        residual_weather_order,
        rtol=1e-4,
        atol=1e-4,
    )
    np.testing.assert_allclose(high_mode_residual, 0.0, rtol=1e-4, atol=1e-4)


def test_scale_separated_residual_correction_keeps_low_modes_longer():
    """Low modes use the fixed 96 h memory while other channels stay unchanged."""
    raw_temperature = jnp.stack(
        [
            jnp.full((4, 3), 280.0, dtype=jnp.float32),
            jnp.full((4, 3), 282.0, dtype=jnp.float32),
        ]
    )
    raw_u_wind = jnp.stack(
        [
            jnp.full((4, 3), 1.0, dtype=jnp.float32),
            jnp.full((4, 3), 1.5, dtype=jnp.float32),
        ]
    )
    raw_pressure = jnp.stack(
        [
            jnp.full((4, 3), 100000.0, dtype=jnp.float32),
            jnp.full((4, 3), 99900.0, dtype=jnp.float32),
        ]
    )
    trajectory_state = WeatherState(
        values=jnp.stack([raw_temperature, raw_u_wind, raw_pressure], axis=1),
        variables=(
            "2m_temperature",
            "10m_u_component_of_wind",
            "mean_sea_level_pressure",
        ),
    )
    initial_temperature = jnp.full((4, 3), 284.0, dtype=jnp.float32)
    initial_u_wind = jnp.full((4, 3), 4.0, dtype=jnp.float32)
    initial_state = WeatherState(
        values=jnp.stack([initial_temperature, initial_u_wind]),
        variables=("2m_temperature", "10m_u_component_of_wind"),
    )
    grid = grid_metadata(
        longitude=np.array([0.0, 90.0, 180.0, 270.0]),
        latitude=np.array([90.0, 0.0, -90.0]),
        layer_count=2,
        spectral_wavenumbers=None,
    )

    corrected = _apply_scale_separated_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(0, 1),
        lead_hours=(0, 96),
        decay_hours=48.0,
        horizontal_grid=grid.coords.horizontal,
        latitude_reversed=grid.latitude_reversed,
    )

    low_mode_decay = np.exp(-1.0)
    expected_temperature = raw_temperature.at[0].set(initial_temperature)
    expected_temperature = expected_temperature.at[1].set(
        raw_temperature[1] + (initial_temperature - raw_temperature[0]) * low_mode_decay
    )
    expected_u_wind = raw_u_wind.at[0].set(initial_u_wind)
    expected_u_wind = expected_u_wind.at[1].set(
        raw_u_wind[1] + (initial_u_wind - raw_u_wind[0]) * low_mode_decay
    )
    np.testing.assert_allclose(
        corrected.select(("2m_temperature",)).values[:, 0],
        expected_temperature,
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        corrected.select(("10m_u_component_of_wind",)).values[:, 0],
        expected_u_wind,
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_array_equal(
        corrected.select(("mean_sea_level_pressure",)).values,
        trajectory_state.select(("mean_sea_level_pressure",)).values,
    )


def test_land_sea_surface_temperature_decay_blends_land_ocean_and_coast():
    """Land keeps incumbent memory, ocean lengthens it, and coasts interpolate."""
    high_mode_decay = jnp.asarray([[[0.25, 0.25, 0.25]]], dtype=jnp.float32)
    low_mode_decay = jnp.asarray([[[0.36, 0.36, 0.36]]], dtype=jnp.float32)
    land_sea_fraction = jnp.asarray([[1.0, 0.0, 0.25]], dtype=jnp.float32)

    high_decay, low_decay = _land_sea_surface_temperature_residual_decays(
        high_mode_decay=high_mode_decay,
        low_mode_decay=low_mode_decay,
        land_sea_fraction=land_sea_fraction,
    )

    expected_high_ocean = 0.25**_LAND_SEA_SURFACE_TEMPERATURE_OCEAN_DECAY_EXPONENT
    expected_low_ocean = 0.36**_LAND_SEA_SURFACE_TEMPERATURE_OCEAN_DECAY_EXPONENT
    np.testing.assert_allclose(
        high_decay,
        [[[0.25, expected_high_ocean, 0.25 * 0.25 + 0.75 * expected_high_ocean]]],
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        low_decay,
        [[[0.36, expected_low_ocean, 0.25 * 0.36 + 0.75 * expected_low_ocean]]],
        rtol=1e-6,
        atol=1e-6,
    )


def test_land_sea_fraction_validation_rejects_unsafe_masks():
    """Invalid masks are rejected before they can alter residual memory."""
    assert _valid_land_sea_fraction_or_none(None, (2, 2)) is None
    assert _valid_land_sea_fraction_or_none(jnp.ones((2, 3)), (2, 2)) is None
    assert (
        _valid_land_sea_fraction_or_none(
            jnp.asarray([[1.0, jnp.nan], [0.5, 0.0]]),
            (2, 2),
        )
        is None
    )
    assert (
        _valid_land_sea_fraction_or_none(
            jnp.asarray([[1.1, 0.0], [0.5, 0.0]]),
            (2, 2),
        )
        is None
    )
    valid = _valid_land_sea_fraction_or_none(
        jnp.asarray([[1.0, 0.0], [0.5, 0.25]]),
        (2, 2),
    )

    assert valid is not None
    np.testing.assert_array_equal(valid, [[1.0, 0.0], [0.5, 0.25]])


def test_land_sea_surface_temperature_correction_preserves_non_t2m_channels():
    """The land-sea residual blend changes only T2m and keeps lead zero exact."""
    raw_temperature = jnp.stack(
        [
            jnp.full((4, 3), 280.0, dtype=jnp.float32),
            jnp.full((4, 3), 282.0, dtype=jnp.float32),
        ]
    )
    raw_u_wind = jnp.stack(
        [
            jnp.full((4, 3), 1.0, dtype=jnp.float32),
            jnp.full((4, 3), 1.5, dtype=jnp.float32),
        ]
    )
    raw_pressure = jnp.stack(
        [
            jnp.full((4, 3), 100000.0, dtype=jnp.float32),
            jnp.full((4, 3), 99900.0, dtype=jnp.float32),
        ]
    )
    trajectory_state = WeatherState(
        values=jnp.stack([raw_temperature, raw_u_wind, raw_pressure], axis=1),
        variables=(
            "2m_temperature",
            "10m_u_component_of_wind",
            "mean_sea_level_pressure",
        ),
    )
    initial_temperature = jnp.full((4, 3), 284.0, dtype=jnp.float32)
    initial_u_wind = jnp.full((4, 3), 4.0, dtype=jnp.float32)
    initial_state = WeatherState(
        values=jnp.stack([initial_temperature, initial_u_wind]),
        variables=("2m_temperature", "10m_u_component_of_wind"),
    )
    grid = grid_metadata(
        longitude=np.array([0.0, 90.0, 180.0, 270.0]),
        latitude=np.array([90.0, 0.0, -90.0]),
        layer_count=2,
        spectral_wavenumbers=None,
    )
    land_sea_fraction = jnp.asarray(
        [
            [1.0, 0.0, 0.25],
            [1.0, 0.0, 0.25],
            [1.0, 0.0, 0.25],
            [1.0, 0.0, 0.25],
        ],
        dtype=jnp.float32,
    )

    incumbent = _apply_scale_separated_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(0, 1),
        lead_hours=(0, 96),
        decay_hours=48.0,
        horizontal_grid=grid.coords.horizontal,
        latitude_reversed=grid.latitude_reversed,
    )
    corrected = _apply_scale_separated_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(0, 1),
        lead_hours=(0, 96),
        decay_hours=48.0,
        horizontal_grid=grid.coords.horizontal,
        latitude_reversed=grid.latitude_reversed,
        land_sea_fraction=land_sea_fraction,
    )

    incumbent_decay = np.exp(-1.0)
    ocean_decay = incumbent_decay**_LAND_SEA_SURFACE_TEMPERATURE_OCEAN_DECAY_EXPONENT
    expected_decay = (
        land_sea_fraction * incumbent_decay + (1.0 - land_sea_fraction) * ocean_decay
    )
    expected_temperature = raw_temperature.at[0].set(initial_temperature)
    expected_temperature = expected_temperature.at[1].set(
        raw_temperature[1] + (initial_temperature - raw_temperature[0]) * expected_decay
    )
    np.testing.assert_allclose(
        corrected.select(("2m_temperature",)).values[:, 0],
        expected_temperature,
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        corrected.select(("10m_u_component_of_wind",)).values,
        incumbent.select(("10m_u_component_of_wind",)).values,
        rtol=0.0,
        atol=0.0,
    )
    np.testing.assert_array_equal(
        corrected.select(("mean_sea_level_pressure",)).values,
        trajectory_state.select(("mean_sea_level_pressure",)).values,
    )


def test_land_sea_surface_temperature_invalid_mask_reproduces_incumbent():
    """Missing or unsafe masks leave the scale-separated incumbent unchanged."""
    raw_temperature = jnp.stack(
        [
            jnp.full((4, 3), 280.0, dtype=jnp.float32),
            jnp.full((4, 3), 282.0, dtype=jnp.float32),
        ]
    )
    raw_u_wind = jnp.stack(
        [
            jnp.full((4, 3), 1.0, dtype=jnp.float32),
            jnp.full((4, 3), 1.5, dtype=jnp.float32),
        ]
    )
    trajectory_state = WeatherState(
        values=jnp.stack([raw_temperature, raw_u_wind], axis=1),
        variables=("2m_temperature", "10m_u_component_of_wind"),
    )
    initial_state = WeatherState(
        values=jnp.stack([raw_temperature[0] + 5.0, raw_u_wind[0] + 2.0]),
        variables=("2m_temperature", "10m_u_component_of_wind"),
    )
    grid = grid_metadata(
        longitude=np.array([0.0, 90.0, 180.0, 270.0]),
        latitude=np.array([90.0, 0.0, -90.0]),
        layer_count=2,
        spectral_wavenumbers=None,
    )
    incumbent = _apply_scale_separated_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(0, 1),
        lead_hours=(0, 24),
        decay_hours=48.0,
        horizontal_grid=grid.coords.horizontal,
        latitude_reversed=grid.latitude_reversed,
    )

    for invalid_mask in (
        jnp.ones((5, 3), dtype=jnp.float32),
        jnp.full((4, 3), jnp.nan, dtype=jnp.float32),
        jnp.full((4, 3), 1.1, dtype=jnp.float32),
    ):
        fallback = _apply_scale_separated_near_surface_residual_correction(
            trajectory_state,
            initial_state=initial_state,
            lead_steps=(0, 1),
            lead_hours=(0, 24),
            decay_hours=48.0,
            horizontal_grid=grid.coords.horizontal,
            latitude_reversed=grid.latitude_reversed,
            land_sea_fraction=invalid_mask,
        )

        np.testing.assert_array_equal(fallback.values, incumbent.values)


def test_scale_separated_residual_correction_falls_back_to_incumbent(monkeypatch):
    """Invalid or incompatible spectral splits use the incumbent correction."""
    raw_temperature = jnp.stack(
        [
            jnp.full((4, 3), 280.0, dtype=jnp.float32),
            jnp.full((4, 3), 282.0, dtype=jnp.float32),
        ]
    )
    raw_u_wind = jnp.stack(
        [
            jnp.full((4, 3), 1.0, dtype=jnp.float32),
            jnp.full((4, 3), 1.5, dtype=jnp.float32),
        ]
    )
    trajectory_state = WeatherState(
        values=jnp.stack([raw_temperature, raw_u_wind], axis=1),
        variables=("2m_temperature", "10m_u_component_of_wind"),
    )
    initial_state = WeatherState(
        values=jnp.stack([raw_temperature[0] + 5.0, raw_u_wind[0] + 2.0]),
        variables=("2m_temperature", "10m_u_component_of_wind"),
    )
    incumbent = _apply_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(0, 1),
        lead_hours=(0, 24),
        decay_hours=48.0,
    )
    incompatible_grid = spherical_harmonic.Grid(
        longitude_wavenumbers=2,
        total_wavenumbers=3,
        longitude_nodes=5,
        latitude_nodes=4,
        latitude_spacing="gauss",
    )
    shape_fallback = _apply_scale_separated_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(0, 1),
        lead_hours=(0, 24),
        decay_hours=48.0,
        horizontal_grid=incompatible_grid,
    )
    np.testing.assert_array_equal(shape_fallback.values, incumbent.values)

    grid = grid_metadata(
        longitude=np.array([0.0, 90.0, 180.0, 270.0]),
        latitude=np.array([90.0, 0.0, -90.0]),
        layer_count=2,
        spectral_wavenumbers=None,
    )

    def invalid_split(residual, *, horizontal_grid, latitude_reversed):
        del horizontal_grid, latitude_reversed
        return (
            jnp.full_like(residual, jnp.nan),
            jnp.zeros_like(residual),
            jnp.asarray(False),
        )

    monkeypatch.setattr(
        dinosaur_adapter,
        "_split_near_surface_residual_by_scale",
        invalid_split,
    )
    nonfinite_fallback = _apply_scale_separated_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(0, 1),
        lead_hours=(0, 24),
        decay_hours=48.0,
        horizontal_grid=grid.coords.horizontal,
        latitude_reversed=grid.latitude_reversed,
    )

    assert bool(jnp.isfinite(nonfinite_fallback.values).all())
    np.testing.assert_array_equal(nonfinite_fallback.values, incumbent.values)


def test_stability_aware_residual_decay_hours_are_bounded_by_column_state():
    """Synthetic lower-column states map to fixed min, base, and max decay."""
    low_temperature = 290.0
    neutral_upper_temperature = low_temperature * (850.0 / 1000.0) ** (2.0 / 7.0)
    upper_temperature = jnp.asarray(
        [
            neutral_upper_temperature + 12.0,
            neutral_upper_temperature,
            neutral_upper_temperature - 12.0,
        ],
        dtype=jnp.float32,
    )[jnp.newaxis, :]
    low_temperature_field = jnp.full_like(upper_temperature, low_temperature)
    low_wind = jnp.zeros_like(upper_temperature)
    trajectory_state = WeatherState(
        values=jnp.stack(
            [
                low_temperature_field[jnp.newaxis, ...],
                upper_temperature[jnp.newaxis, ...],
                low_wind[jnp.newaxis, ...],
                low_wind[jnp.newaxis, ...],
                low_wind[jnp.newaxis, ...],
                low_wind[jnp.newaxis, ...],
                low_temperature_field[jnp.newaxis, ...],
                low_wind[jnp.newaxis, ...],
            ],
            axis=1,
        ),
        variables=(
            "temperature_1000",
            "temperature_850",
            "u_component_of_wind_1000",
            "u_component_of_wind_850",
            "v_component_of_wind_1000",
            "v_component_of_wind_850",
            "2m_temperature",
            "10m_u_component_of_wind",
        ),
    )
    initial_state = WeatherState(
        values=jnp.stack([low_temperature_field, low_wind]),
        variables=("2m_temperature", "10m_u_component_of_wind"),
    )

    decay_hours = _stability_aware_near_surface_residual_decay_hours(
        trajectory_state,
        initial_state=initial_state,
        lead_indices=jnp.asarray((0,), dtype=jnp.int32),
        base_decay_hours=48.0,
    )

    np.testing.assert_allclose(
        decay_hours[0, 0],
        jnp.asarray([72.0, 48.0, 18.0], dtype=jnp.float32),
        rtol=1e-6,
        atol=1e-5,
    )


def test_stability_aware_residual_correction_preserves_zero_residual_trajectory():
    """Zero initial residual leaves all requested leads unchanged."""
    raw_temperature = jnp.stack(
        [
            jnp.full((2, 2), 280.0, dtype=jnp.float32),
            jnp.full((2, 2), 281.0, dtype=jnp.float32),
        ]
    )
    raw_u_wind = jnp.stack(
        [
            jnp.full((2, 2), 3.0, dtype=jnp.float32),
            jnp.full((2, 2), 4.0, dtype=jnp.float32),
        ]
    )
    trajectory_state = WeatherState(
        values=jnp.stack([raw_temperature, raw_u_wind], axis=1),
        variables=("2m_temperature", "10m_u_component_of_wind"),
    )
    initial_state = WeatherState(
        values=jnp.stack([raw_temperature[0], raw_u_wind[0]]),
        variables=("2m_temperature", "10m_u_component_of_wind"),
    )

    corrected = _apply_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(0, 1),
        lead_hours=(0, 24),
        decay_hours=48.0,
        use_stability_aware_decay=True,
    )

    np.testing.assert_array_equal(corrected.values, trajectory_state.values)


def test_stability_aware_residual_correction_preserves_uncorrected_channels():
    """Only the two accepted near-surface residual channels are modified."""
    spatial_pattern = jnp.arange(4, dtype=jnp.float32).reshape(2, 2)
    raw_temperature = jnp.stack([280.0 + spatial_pattern, 281.0 + spatial_pattern])
    raw_u_wind = jnp.stack([1.0 + spatial_pattern, 2.0 + spatial_pattern])
    raw_pressure = jnp.stack([100000.0 + spatial_pattern, 99900.0 + spatial_pattern])
    raw_geopotential = jnp.stack([5000.0 + spatial_pattern, 5001.0 + spatial_pattern])
    trajectory_state = WeatherState(
        values=jnp.stack(
            [
                raw_temperature,
                raw_u_wind,
                raw_pressure,
                raw_geopotential,
            ],
            axis=1,
        ),
        variables=(
            "2m_temperature",
            "10m_u_component_of_wind",
            "mean_sea_level_pressure",
            "geopotential_500",
        ),
    )
    initial_state = WeatherState(
        values=jnp.stack([raw_temperature[0] + 5.0, raw_u_wind[0] - 1.0]),
        variables=("2m_temperature", "10m_u_component_of_wind"),
    )

    corrected = _apply_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(0, 1),
        lead_hours=(0, 24),
        decay_hours=48.0,
        use_stability_aware_decay=True,
    )

    np.testing.assert_array_equal(
        corrected.select(("mean_sea_level_pressure", "geopotential_500")).values,
        trajectory_state.select(("mean_sea_level_pressure", "geopotential_500")).values,
    )
    np.testing.assert_array_equal(
        corrected.select(("2m_temperature",)).values[0, 0],
        initial_state.select(("2m_temperature",)).values[0],
    )
    np.testing.assert_array_equal(
        corrected.select(("10m_u_component_of_wind",)).values[0, 0],
        initial_state.select(("10m_u_component_of_wind",)).values[0],
    )


def test_surface_layer_richardson_10m_wind_scales_stability_regimes():
    """Stable columns damp and unstable columns relax toward lowest-layer wind."""
    sigma_coords = sigma_coordinates.SigmaCoordinates(
        np.asarray([0.0, 0.99, 1.0], dtype=np.float32)
    )
    lower_temperature = 290.0
    neutral_upper_temperature = lower_temperature * (
        sigma_coords.centers[-2] / sigma_coords.centers[-1]
    ) ** (2.0 / 7.0)
    upper_temperature = jnp.asarray(
        [
            neutral_upper_temperature + 12.0,
            neutral_upper_temperature,
            neutral_upper_temperature - 12.0,
        ],
        dtype=jnp.float32,
    )
    temperature = jnp.stack(
        [
            upper_temperature,
            jnp.full_like(upper_temperature, lower_temperature),
        ],
        axis=0,
    )[jnp.newaxis, :, jnp.newaxis, :]
    u_wind = jnp.stack(
        [
            jnp.full_like(upper_temperature, 10.0),
            jnp.full_like(upper_temperature, 10.0),
        ],
        axis=0,
    )[jnp.newaxis, :, jnp.newaxis, :]
    v_wind = jnp.stack(
        [
            jnp.full_like(upper_temperature, -4.0),
            jnp.full_like(upper_temperature, -4.0),
        ],
        axis=0,
    )[jnp.newaxis, :, jnp.newaxis, :]
    surface_pressure_hpa = jnp.full((1, 1, 3), 1000.0, dtype=jnp.float32)

    diagnosed_u_wind, diagnosed_v_wind = _surface_layer_richardson_10m_wind(
        temperature=temperature,
        u_wind=u_wind,
        v_wind=v_wind,
        surface_pressure_hpa=surface_pressure_hpa,
        sigma_coords=sigma_coords,
    )

    u_factor = diagnosed_u_wind[0, 0] / u_wind[0, -1, 0]
    v_factor = diagnosed_v_wind[0, 0] / v_wind[0, -1, 0]
    assert float(u_factor[0]) < float(u_factor[1]) < float(u_factor[2])
    np.testing.assert_allclose(v_factor, u_factor, rtol=1e-6, atol=1e-6)
    assert float(jnp.min(u_factor)) >= 0.55
    assert float(jnp.max(u_factor)) <= 1.05


def test_surface_layer_richardson_10m_wind_falls_back_for_invalid_columns():
    """Nonfinite lower-column values preserve the incumbent lowest-layer wind."""
    sigma_coords = sigma_coordinates.SigmaCoordinates(
        np.asarray([0.0, 0.99, 1.0], dtype=np.float32)
    )
    temperature = jnp.asarray(
        [[[[280.0, jnp.nan]], [[290.0, 290.0]]]],
        dtype=jnp.float32,
    )
    u_wind = jnp.asarray([[[[12.0, 12.0]], [[8.0, 8.0]]]], dtype=jnp.float32)
    v_wind = jnp.asarray([[[[-6.0, -6.0]], [[4.0, 4.0]]]], dtype=jnp.float32)
    surface_pressure_hpa = jnp.full((1, 1, 2), 1000.0, dtype=jnp.float32)

    diagnosed_u_wind, diagnosed_v_wind = _surface_layer_richardson_10m_wind(
        temperature=temperature,
        u_wind=u_wind,
        v_wind=v_wind,
        surface_pressure_hpa=surface_pressure_hpa,
        sigma_coords=sigma_coords,
    )

    assert float(diagnosed_u_wind[0, 0, 0]) != float(u_wind[0, -1, 0, 0])
    assert float(diagnosed_v_wind[0, 0, 0]) != float(v_wind[0, -1, 0, 0])
    np.testing.assert_array_equal(diagnosed_u_wind[0, 0, 1], u_wind[0, -1, 0, 1])
    np.testing.assert_array_equal(diagnosed_v_wind[0, 0, 1], v_wind[0, -1, 0, 1])


def test_dinosaur_forecast_handles_multiple_initial_times():
    """Dinosaur forecasts preserve the initialization-time axis."""
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        output_variables=("temperature_250",),
        include_vertical_advection=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=2), lead_steps=(0,))

    forecast = model.forecast(forecast_input)

    assert forecast.variables == ("temperature_250",)
    assert forecast.values.shape == (1, 2, 1, 4, 3)
    np.testing.assert_allclose(forecast.values[0, :, 0], 250.0, atol=1e-4)


def test_weather_state_to_dinosaur_state_regrids_pressure_levels_to_sigma():
    """WeatherBench pressure-level inputs are regridded to Dinosaur sigma layers."""
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )

    state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=(250, 750),
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )

    sigma_temperature = (
        grid.coords.horizontal.to_nodal(state.temperature_variation)
        + reference_temperature[:, np.newaxis, np.newaxis]
    )
    np.testing.assert_allclose(sigma_temperature[0], 250.0, atol=1e-4)
    np.testing.assert_allclose(sigma_temperature[1], 285.0, atol=1e-4)


def test_weather_state_to_dinosaur_state_selects_initialization_coordinate(
    monkeypatch,
):
    """Default initialization stays linear; the candidate option uses log pressure."""
    calls = []

    def record_linear(fields, pressure_coords, sigma_coords, surface_pressure):
        calls.append("linear")
        return fields

    def record_log_pressure(fields, pressure_coords, sigma_coords, surface_pressure):
        calls.append("log_pressure")
        return fields

    monkeypatch.setattr(
        vertical_interpolation,
        "interp_pressure_to_sigma",
        record_linear,
    )
    monkeypatch.setattr(
        vertical_interpolation,
        "interp_pressure_to_sigma_log_pressure",
        record_log_pressure,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0,),
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    weather_state = WeatherState(
        values=forecast_input.initial_state.values[0],
        variables=forecast_input.initial_state.variables,
    )

    weather_state_to_dinosaur_state(
        weather_state,
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )
    assert calls == ["linear"]

    calls.clear()
    weather_state_to_dinosaur_state(
        weather_state,
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
        use_log_pressure_initialization=True,
    )
    assert calls == ["log_pressure"]


def test_log_pressure_initialization_matches_log_linear_profile():
    """Log-pressure interpolation matches profiles linear in log pressure."""
    pressure_coords = _pressure_coordinates((100, 500, 1000))
    sigma_coords = sigma_coordinates.SigmaCoordinates.equidistant(3)
    source_pressure = jnp.asarray(pressure_coords.centers, dtype=jnp.float32)
    field = (2.5 + 4.0 * jnp.log(source_pressure))[:, np.newaxis, np.newaxis]
    fields = {"temperature": field}
    surface_pressure = jnp.full((1, 1), 900.0, dtype=jnp.float32)

    log_pressure_result = vertical_interpolation.interp_pressure_to_sigma_log_pressure(
        fields,
        pressure_coords,
        sigma_coords,
        surface_pressure,
    )["temperature"]
    linear_pressure_result = vertical_interpolation.interp_pressure_to_sigma(
        fields,
        pressure_coords,
        sigma_coords,
        surface_pressure,
    )["temperature"]
    target_pressure = sigma_coords.centers[:, np.newaxis, np.newaxis] * surface_pressure
    expected = 2.5 + 4.0 * jnp.log(target_pressure)

    np.testing.assert_allclose(log_pressure_result, expected, rtol=1e-6, atol=1e-6)
    assert float(jnp.max(jnp.abs(linear_pressure_result - expected))) > 0.05


def test_hydrostatic_temperature_initialization_matches_isothermal_thickness():
    """Hydrostatic reconstruction differentiates geopotential in log pressure."""
    pressure_levels_hpa = (100, 300, 900)
    temperature_kelvin = 270.0
    log_pressure = jnp.log(jnp.asarray(pressure_levels_hpa, dtype=jnp.float32))
    spatial_offset = jnp.arange(12, dtype=jnp.float32).reshape(4, 3)
    geopotential = (
        80_000.0
        - _DRY_AIR_GAS_CONSTANT_SI
        * temperature_kelvin
        * log_pressure[:, jnp.newaxis, jnp.newaxis]
        + spatial_offset[jnp.newaxis, ...]
    )
    analyzed_temperature = jnp.full_like(geopotential, 250.0)

    actual = _hydrostatic_temperature_from_geopotential_thickness(
        analyzed_temperature=analyzed_temperature,
        geopotential=geopotential,
        pressure_levels_hpa=pressure_levels_hpa,
    )

    np.testing.assert_allclose(actual, temperature_kelvin, rtol=1e-6, atol=1e-4)


def test_hydrostatic_temperature_initialization_converts_virtual_temperature():
    """Complete humidity stacks convert hydrostatic virtual temperature to dry T."""
    pressure_levels_hpa = (100, 300, 900)
    dry_temperature_kelvin = 280.0
    specific_humidity = jnp.full((3, 4, 3), 0.01, dtype=jnp.float32)
    gas_constant_ratio = 461.0 / _DRY_AIR_GAS_CONSTANT_SI
    virtual_temperature = dry_temperature_kelvin * (
        1.0 + (gas_constant_ratio - 1.0) * specific_humidity
    )
    log_pressure = jnp.log(jnp.asarray(pressure_levels_hpa, dtype=jnp.float32))
    geopotential = (
        100_000.0
        - _DRY_AIR_GAS_CONSTANT_SI
        * virtual_temperature
        * log_pressure[:, jnp.newaxis, jnp.newaxis]
    )
    analyzed_temperature = jnp.full_like(geopotential, 250.0)

    actual = _hydrostatic_temperature_from_geopotential_thickness(
        analyzed_temperature=analyzed_temperature,
        geopotential=geopotential,
        pressure_levels_hpa=pressure_levels_hpa,
        specific_humidity=specific_humidity,
    )

    np.testing.assert_allclose(
        actual,
        dry_temperature_kelvin,
        rtol=1e-6,
        atol=1e-4,
    )


def test_layer_mean_hydrostatic_temperature_initialization_uses_adjacent_layers():
    """Layer-mean reconstruction maps hypsometric layer temperatures to levels."""
    pressure_levels_hpa = (100, 300, 600, 900)
    layer_virtual_temperature = jnp.asarray([220.0, 250.0, 280.0], dtype=jnp.float32)
    log_pressure = jnp.log(jnp.asarray(pressure_levels_hpa, dtype=jnp.float32))
    layer_thickness = (
        _DRY_AIR_GAS_CONSTANT_SI
        * layer_virtual_temperature
        * (log_pressure[1:] - log_pressure[:-1])
    )
    base_geopotential = 90_000.0
    geopotential_profile = jnp.concatenate(
        [
            jnp.asarray([base_geopotential], dtype=jnp.float32),
            base_geopotential - jnp.cumsum(layer_thickness),
        ]
    )
    geopotential = geopotential_profile[:, jnp.newaxis, jnp.newaxis] + jnp.zeros(
        (4, 2, 3),
        dtype=jnp.float32,
    )
    analyzed_temperature = jnp.full_like(geopotential, 260.0)

    actual = _layer_mean_hydrostatic_temperature_from_geopotential_thickness(
        analyzed_temperature=analyzed_temperature,
        geopotential=geopotential,
        pressure_levels_hpa=pressure_levels_hpa,
    )

    expected_profile = jnp.asarray([220.0, 235.0, 265.0, 280.0], dtype=jnp.float32)
    expected = expected_profile[:, jnp.newaxis, jnp.newaxis] + jnp.zeros(
        (4, 2, 3),
        dtype=jnp.float32,
    )
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-4)


def test_layer_mean_hydrostatic_temperature_initialization_converts_humidity():
    """Layer humidity converts virtual layer means to dry level temperatures."""
    pressure_levels_hpa = (100, 300, 900)
    dry_layer_temperature = jnp.asarray([270.0, 290.0], dtype=jnp.float32)
    specific_humidity = jnp.stack(
        [
            jnp.full((2, 3), 0.01, dtype=jnp.float32),
            jnp.full((2, 3), 0.03, dtype=jnp.float32),
            jnp.full((2, 3), 0.05, dtype=jnp.float32),
        ],
        axis=0,
    )
    layer_specific_humidity = 0.5 * (
        specific_humidity[1:, 0, 0] + specific_humidity[:-1, 0, 0]
    )
    gas_constant_ratio = 461.0 / _DRY_AIR_GAS_CONSTANT_SI
    layer_virtual_temperature = dry_layer_temperature * (
        1.0 + (gas_constant_ratio - 1.0) * layer_specific_humidity
    )
    log_pressure = jnp.log(jnp.asarray(pressure_levels_hpa, dtype=jnp.float32))
    layer_thickness = (
        _DRY_AIR_GAS_CONSTANT_SI
        * layer_virtual_temperature
        * (log_pressure[1:] - log_pressure[:-1])
    )
    geopotential_profile = jnp.concatenate(
        [
            jnp.asarray([100_000.0], dtype=jnp.float32),
            100_000.0 - jnp.cumsum(layer_thickness),
        ]
    )
    geopotential = geopotential_profile[:, jnp.newaxis, jnp.newaxis] + jnp.zeros(
        (3, 2, 3),
        dtype=jnp.float32,
    )
    analyzed_temperature = jnp.full_like(geopotential, 250.0)

    actual = _layer_mean_hydrostatic_temperature_from_geopotential_thickness(
        analyzed_temperature=analyzed_temperature,
        geopotential=geopotential,
        pressure_levels_hpa=pressure_levels_hpa,
        specific_humidity=specific_humidity,
    )

    expected_profile = jnp.asarray([270.0, 280.0, 290.0], dtype=jnp.float32)
    expected = expected_profile[:, jnp.newaxis, jnp.newaxis] + jnp.zeros(
        (3, 2, 3),
        dtype=jnp.float32,
    )
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-4)


def test_layer_mean_hydrostatic_temperature_initialization_falls_back_pointwise():
    """Invalid reconstructed level temperatures fall back to analyzed values."""
    pressure_levels_hpa = (100, 300, 900)
    analyzed_temperature = jnp.asarray(
        [
            [[251.0, 252.0]],
            [[261.0, 262.0]],
            [[271.0, 272.0]],
        ],
        dtype=jnp.float32,
    )
    log_pressure = jnp.log(jnp.asarray(pressure_levels_hpa, dtype=jnp.float32))
    positive_temperature = 280.0
    negative_temperature = -700.0
    layer_0 = (
        _DRY_AIR_GAS_CONSTANT_SI
        * positive_temperature
        * (log_pressure[1] - log_pressure[0])
    )
    layer_1 = (
        _DRY_AIR_GAS_CONSTANT_SI
        * negative_temperature
        * (log_pressure[2] - log_pressure[1])
    )
    geopotential = jnp.asarray(
        [
            [[100_000.0, 100_000.0]],
            [[100_000.0 - layer_0, jnp.nan]],
            [[100_000.0 - layer_0 - layer_1, jnp.nan]],
        ],
        dtype=jnp.float32,
    )

    actual = _layer_mean_hydrostatic_temperature_from_geopotential_thickness(
        analyzed_temperature=analyzed_temperature,
        geopotential=geopotential,
        pressure_levels_hpa=pressure_levels_hpa,
    )

    expected = jnp.asarray(
        [
            [[positive_temperature, 252.0]],
            [[261.0, 262.0]],
            [[271.0, 272.0]],
        ],
        dtype=jnp.float32,
    )
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-4)


def test_layer_mean_hydrostatic_temperature_initialization_needs_two_levels():
    """Single-level stacks cannot define thickness and preserve analyzed T."""
    analyzed_temperature = jnp.asarray([[[255.0, 256.0]]], dtype=jnp.float32)
    geopotential = jnp.asarray([[[10_000.0, 11_000.0]]], dtype=jnp.float32)

    actual = _layer_mean_hydrostatic_temperature_from_geopotential_thickness(
        analyzed_temperature=analyzed_temperature,
        geopotential=geopotential,
        pressure_levels_hpa=(500,),
    )

    np.testing.assert_array_equal(actual, analyzed_temperature)


def test_hydrostatic_temperature_initialization_falls_back_without_geopotential():
    """Incomplete geopotential stacks preserve incumbent initialized state exactly."""
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    weather_state = WeatherState(
        values=forecast_input.initial_state.values[0],
        variables=forecast_input.initial_state.variables,
    )
    common_kwargs = {
        "state": weather_state,
        "coords": grid.coords,
        "pressure_levels_hpa": (250, 750),
        "latitude_reversed": grid.latitude_reversed,
        "physics_specs": physics_specs,
        "reference_temperature": reference_temperature,
        "include_humidity": True,
        "use_log_pressure_initialization": True,
    }

    incumbent = weather_state_to_dinosaur_state(**common_kwargs)
    candidate = weather_state_to_dinosaur_state(
        **common_kwargs,
        use_hydrostatic_temperature_initialization=True,
    )

    _assert_pytree_allclose(candidate, incumbent)


def test_weather_state_to_dinosaur_state_matches_direct_dinosaur_initialization():
    """State initialization mirrors explicit Dinosaur initialization calls."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0,),
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    weather_state = WeatherState(
        values=forecast_input.initial_state.values[0],
        variables=forecast_input.initial_state.variables,
    )

    actual = weather_state_to_dinosaur_state(
        weather_state,
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )

    direct_inputs = {
        "temperature": _structured_field(
            weather_state,
            "temperature",
            pressure_levels_hpa,
            grid.latitude_reversed,
        )
        * _unit_factor(physics_specs, "kelvin"),
        "u_component_of_wind": _structured_field(
            weather_state,
            "u_component_of_wind",
            pressure_levels_hpa,
            grid.latitude_reversed,
        )
        * _unit_factor(physics_specs, "meter / second"),
        "v_component_of_wind": _structured_field(
            weather_state,
            "v_component_of_wind",
            pressure_levels_hpa,
            grid.latitude_reversed,
        )
        * _unit_factor(physics_specs, "meter / second"),
        "specific_humidity": _structured_field(
            weather_state,
            "specific_humidity",
            pressure_levels_hpa,
            grid.latitude_reversed,
        ),
    }
    surface_pressure = _surface_pressure_field(weather_state, grid.latitude_reversed)
    sigma_inputs = vertical_interpolation.interp_pressure_to_sigma(
        direct_inputs,
        _pressure_coordinates(pressure_levels_hpa),
        grid.coords.vertical,
        surface_pressure / 100.0,
    )
    direct_vorticity, direct_divergence = spherical_harmonic.uv_nodal_to_vor_div_modal(
        grid.coords.horizontal,
        sigma_inputs["u_component_of_wind"],
        sigma_inputs["v_component_of_wind"],
    )
    pressure_factor = _unit_factor(physics_specs, "pascal")
    direct = _primitive_equation_state(
        vorticity=direct_vorticity,
        divergence=direct_divergence,
        temperature_variation=grid.coords.horizontal.to_modal(
            sigma_inputs["temperature"]
            - reference_temperature[:, np.newaxis, np.newaxis]
        ),
        log_surface_pressure=grid.coords.horizontal.to_modal(
            jnp.log(surface_pressure * pressure_factor)
        )[jnp.newaxis],
        tracers={
            "specific_humidity": grid.coords.horizontal.to_modal(
                sigma_inputs["specific_humidity"]
            )
        },
    )
    expected = grid.coords.horizontal.clip_wavenumbers(direct)

    _assert_pytree_allclose(actual, expected)


def test_weather_state_to_dinosaur_state_initializes_sim_time_on_request():
    """The vertical-DSE ramp candidate can opt into forecast-time tracking."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0,),
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    weather_state = WeatherState(
        values=forecast_input.initial_state.values[0],
        variables=forecast_input.initial_state.variables,
    )
    common_kwargs = {
        "state": weather_state,
        "coords": grid.coords,
        "pressure_levels_hpa": pressure_levels_hpa,
        "latitude_reversed": grid.latitude_reversed,
        "physics_specs": physics_specs,
        "reference_temperature": reference_temperature,
        "include_humidity": False,
    }

    untimed_state = weather_state_to_dinosaur_state(**common_kwargs)
    timed_state = weather_state_to_dinosaur_state(
        **common_kwargs,
        initialize_sim_time=True,
    )

    assert untimed_state.sim_time is None
    np.testing.assert_array_equal(timed_state.sim_time, jnp.asarray(0.0))


def test_sigma_to_pressure_interpolation_vectorizes_over_trajectory_time():
    """Trajectory diagnostics interpolate each time slice with Dinosaur."""
    sigma_coords = sigma_coordinates.SigmaCoordinates.equidistant(3)
    pressure_coords = _pressure_coordinates((250, 500, 750))
    fields = {
        "temperature": jnp.arange(2 * 3 * 4 * 3, dtype=jnp.float32).reshape(
            2,
            3,
            4,
            3,
        ),
    }
    surface_pressure = jnp.stack(
        [
            jnp.full((4, 3), 1000.0, dtype=jnp.float32),
            jnp.full((4, 3), 925.0, dtype=jnp.float32),
        ]
    )

    actual = _interp_sigma_to_pressure_by_time(
        fields,
        pressure_coords,
        sigma_coords,
        surface_pressure,
    )
    expected = jnp.stack(
        [
            vertical_interpolation.interp_sigma_to_pressure(
                {"temperature": fields["temperature"][time_index]},
                pressure_coords,
                sigma_coords,
                surface_pressure[time_index],
            )["temperature"]
            for time_index in range(surface_pressure.shape[0])
        ]
    )

    np.testing.assert_allclose(actual["temperature"], expected)


def test_dinosaur_state_to_weather_state_extrapolates_finite_pressure_outputs():
    """Below-surface pressure diagnostics remain finite in packed WeatherState."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1, surface_pressure_pa=70_000.0),
        lead_steps=(0,),
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )
    trajectory = jax.tree_util.tree_map(lambda value: jnp.stack([value]), state)
    fixed_target_variables = (
        "2m_temperature",
        "mean_sea_level_pressure",
        "geopotential_500",
        "10m_u_component_of_wind",
    )
    output_variables = (
        "temperature_900",
        "u_component_of_wind_900",
        "v_component_of_wind_900",
        "geopotential_900",
        "specific_humidity_900",
        *fixed_target_variables,
    )

    actual = dinosaur_state_to_weather_state(
        trajectory,
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        output_variables=output_variables,
    )

    assert actual.variables == output_variables
    maximum_surface_pressure = jnp.max(
        actual.select(("mean_sea_level_pressure",)).values
    )
    assert float(maximum_surface_pressure) < 90_000.0
    assert bool(jnp.isfinite(actual.values).all())
    assert bool(jnp.isfinite(actual.select(fixed_target_variables).values).all())


def test_dinosaur_state_to_weather_state_matches_direct_diagnostics():
    """WeatherState diagnostics mirror explicit Dinosaur diagnostic calls."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0,),
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )
    trajectory = jax.tree_util.tree_map(lambda value: jnp.stack([value, value]), state)
    output_variables = (
        "temperature_500",
        "u_component_of_wind_500",
        "v_component_of_wind_900",
        "geopotential_500",
        "specific_humidity_500",
        "mean_sea_level_pressure",
        "2m_temperature",
        "10m_u_component_of_wind",
    )

    actual = dinosaur_state_to_weather_state(
        trajectory,
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        output_variables=output_variables,
    )

    temperature = (
        grid.coords.horizontal.to_nodal(trajectory.temperature_variation)
        + reference_temperature[np.newaxis, :, np.newaxis, np.newaxis]
    )
    u_wind, v_wind = spherical_harmonic.vor_div_to_uv_nodal(
        grid.coords.horizontal,
        trajectory.vorticity,
        trajectory.divergence,
    )
    surface_pressure = jnp.exp(
        grid.coords.horizontal.to_nodal(trajectory.log_surface_pressure)[:, 0]
    )
    humidity = grid.coords.horizontal.to_nodal(trajectory.tracers["specific_humidity"])
    geopotential = primitive_equations.get_geopotential_on_sigma(
        temperature,
        specific_humidity=humidity,
        nodal_orography=jnp.zeros(grid.coords.horizontal.nodal_shape),
        sigma=cast(sigma_coordinates.SigmaCoordinates, grid.coords.vertical),
        gravity_acceleration=physics_specs.g,
        ideal_gas_constant=physics_specs.R,
        water_vapor_gas_constant=physics_specs.R_vapor,
    )
    pressure_factor = _unit_factor(physics_specs, "pascal")
    pressure_fields = _interp_sigma_to_pressure_by_time(
        {
            "temperature": temperature,
            "u_component_of_wind": u_wind,
            "v_component_of_wind": v_wind,
            "geopotential": geopotential,
            "specific_humidity": humidity,
        },
        _pressure_coordinates(pressure_levels_hpa),
        cast(sigma_coordinates.SigmaCoordinates, grid.coords.vertical),
        (surface_pressure / pressure_factor) / 100.0,
    )
    level_to_index = {level: index for index, level in enumerate(pressure_levels_hpa)}
    expected_values = jnp.stack(
        [
            pressure_fields["temperature"][:, level_to_index[500]]
            / _unit_factor(physics_specs, "kelvin"),
            pressure_fields["u_component_of_wind"][:, level_to_index[500]]
            / _unit_factor(physics_specs, "meter / second"),
            pressure_fields["v_component_of_wind"][:, level_to_index[900]]
            / _unit_factor(physics_specs, "meter / second"),
            pressure_fields["geopotential"][:, level_to_index[500]]
            / _unit_factor(physics_specs, "meter ** 2 / second ** 2"),
            pressure_fields["specific_humidity"][:, level_to_index[500]],
            surface_pressure / pressure_factor,
            temperature[:, -1] / _unit_factor(physics_specs, "kelvin"),
            u_wind[:, -1] / _unit_factor(physics_specs, "meter / second"),
        ],
        axis=1,
    )
    if grid.latitude_reversed:
        expected_values = expected_values[..., ::-1]

    assert actual.variables == output_variables
    np.testing.assert_allclose(actual.values, expected_values, rtol=1e-5, atol=1e-5)


def test_richardson_10m_wind_diagnostic_only_changes_raw_surface_wind():
    """The opt-in diagnostic leaves non-10 m wind packed outputs unchanged."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0,),
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )
    trajectory = jax.tree_util.tree_map(lambda value: jnp.stack([value, value]), state)
    output_variables = (
        "temperature_500",
        "u_component_of_wind_500",
        "v_component_of_wind_500",
        "geopotential_500",
        "specific_humidity_500",
        "surface_pressure",
        "mean_sea_level_pressure",
        "2m_temperature",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
    )
    common_kwargs = {
        "trajectory": trajectory,
        "coords": grid.coords,
        "pressure_levels_hpa": pressure_levels_hpa,
        "latitude_reversed": grid.latitude_reversed,
        "physics_specs": physics_specs,
        "reference_temperature": reference_temperature,
        "output_variables": output_variables,
    }

    incumbent = dinosaur_state_to_weather_state(**common_kwargs)
    candidate = dinosaur_state_to_weather_state(
        **common_kwargs,
        use_surface_layer_richardson_10m_wind_diagnostic=True,
    )

    unchanged_variables = tuple(output_variables[:-2])
    np.testing.assert_array_equal(
        candidate.select(unchanged_variables).values,
        incumbent.select(unchanged_variables).values,
    )
    assert bool(jnp.isfinite(candidate.values).all())
    assert bool(
        jnp.any(
            candidate.select(("10m_u_component_of_wind",)).values
            != incumbent.select(("10m_u_component_of_wind",)).values
        )
    )
    assert bool(
        jnp.any(
            candidate.select(("10m_v_component_of_wind",)).values
            != incumbent.select(("10m_v_component_of_wind",)).values
        )
    )


def test_potential_temperature_conversion_round_trips_finite_pressure():
    """Dry theta conversion is an inverse pair for finite pressure."""
    temperature = jnp.asarray([[250.0, 280.0], [300.0, 260.0]], dtype=jnp.float32)
    pressure = jnp.asarray([[100000.0, 85000.0], [50000.0, 25000.0]], dtype=jnp.float32)
    reference_pressure = jnp.asarray(100000.0, dtype=jnp.float32)
    kappa = 2.0 / 7.0

    theta = primitive_equations.potential_temperature_from_temperature(
        temperature,
        pressure,
        reference_pressure,
        kappa,
    )
    restored_temperature = primitive_equations.temperature_from_potential_temperature(
        theta,
        pressure,
        reference_pressure,
        kappa,
    )

    np.testing.assert_allclose(restored_temperature, temperature, rtol=1e-6, atol=1e-6)


def test_potential_temperature_conversion_guards_invalid_pressure():
    """Invalid pressure diagnostics use reference pressure and stay finite."""
    temperature = jnp.asarray([250.0, 280.0, 300.0], dtype=jnp.float32)
    pressure = jnp.asarray([jnp.nan, -10.0, jnp.inf], dtype=jnp.float32)
    reference_pressure = jnp.asarray(100000.0, dtype=jnp.float32)

    theta = primitive_equations.potential_temperature_from_temperature(
        temperature,
        pressure,
        reference_pressure,
        2.0 / 7.0,
    )

    np.testing.assert_allclose(theta, temperature, rtol=1e-6, atol=1e-6)
    assert bool(jnp.isfinite(theta).all())


def test_theta_tendency_changes_only_temperature_explicit_term():
    """The opt-in theta tendency leaves nonthermal explicit terms unchanged."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0,),
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=False,
        use_log_pressure_initialization=True,
    )
    common_kwargs = {
        "reference_temperature": reference_temperature,
        "orography": jnp.zeros(grid.coords.horizontal.modal_shape, dtype=jnp.float32),
        "coords": grid.coords,
        "physics_specs": cast(Any, physics_specs),
        "include_vertical_advection": True,
    }
    temperature_equation = primitive_equations.PrimitiveEquations(**common_kwargs)
    theta_equation = primitive_equations.PrimitiveEquations(
        **common_kwargs,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
    )

    temperature_terms = temperature_equation.explicit_terms(state)
    theta_terms = theta_equation.explicit_terms(state)

    np.testing.assert_allclose(
        theta_terms.vorticity,
        temperature_terms.vorticity,
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        theta_terms.divergence,
        temperature_terms.divergence,
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        theta_terms.log_surface_pressure,
        temperature_terms.log_surface_pressure,
        rtol=1e-6,
        atol=1e-6,
    )
    assert theta_terms.tracers == temperature_terms.tracers == {}
    assert bool(jnp.isfinite(theta_terms.temperature_variation).all())
    assert bool(
        jnp.any(
            jnp.abs(
                theta_terms.temperature_variation
                - temperature_terms.temperature_variation
            )
            > 1e-9
        )
    )


def test_theta_tendency_uniform_theta_zero_velocity_has_zero_tendency():
    """Uniform theta under zero velocity has no opt-in thermal tendency."""
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    equation = primitive_equations.PrimitiveEquations(
        reference_temperature,
        jnp.zeros(grid.coords.horizontal.modal_shape, dtype=jnp.float32),
        grid.coords,
        cast(Any, physics_specs),
        include_vertical_advection=True,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
    )
    surface_pressure = (
        jnp.ones(grid.coords.horizontal.nodal_shape, dtype=jnp.float32)
        * 100000.0
        * _unit_factor(physics_specs, "pascal")
    )
    log_surface_pressure = grid.coords.horizontal.to_modal(jnp.log(surface_pressure))[
        jnp.newaxis
    ]
    zero_modal = jnp.zeros(grid.coords.modal_shape, dtype=jnp.float32)
    provisional_state = _primitive_equation_state(
        vorticity=zero_modal,
        divergence=zero_modal,
        temperature_variation=zero_modal,
        log_surface_pressure=log_surface_pressure,
        tracers={},
    )
    pressure = equation.nodal_pressure_sigma(provisional_state)
    uniform_theta = jnp.full_like(pressure, 300.0)
    temperature = primitive_equations.temperature_from_potential_temperature(
        uniform_theta,
        pressure,
        equation._potential_temperature_reference_pressure,
        physics_specs.kappa,
    )
    state = _primitive_equation_state(
        vorticity=zero_modal,
        divergence=zero_modal,
        temperature_variation=grid.coords.horizontal.to_modal(
            temperature - reference_temperature[:, np.newaxis, np.newaxis]
        ),
        log_surface_pressure=log_surface_pressure,
        tracers={},
    )
    aux_state = primitive_equations.compute_diagnostic_state_sigma(state, grid.coords)

    tendency = equation.temperature_tendency(state, aux_state)

    np.testing.assert_allclose(tendency, jnp.zeros_like(tendency), atol=1e-6)


def test_theta_tendency_falls_back_to_temperature_form_for_invalid_pressure():
    """Nonfinite theta pressure diagnostics recover the incumbent tendency."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0,),
    )
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=3,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=3,
        temperature_kelvin=250.0,
    )
    state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=(100, 500, 900),
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=False,
        use_log_pressure_initialization=True,
    )
    equation = primitive_equations.PrimitiveEquations(
        reference_temperature,
        jnp.zeros(grid.coords.horizontal.modal_shape, dtype=jnp.float32),
        grid.coords,
        cast(Any, physics_specs),
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
    )
    aux_state = primitive_equations.compute_diagnostic_state_sigma(state, grid.coords)
    bad_pressure_state = _primitive_equation_state(
        vorticity=state.vorticity,
        divergence=state.divergence,
        temperature_variation=state.temperature_variation,
        log_surface_pressure=state.log_surface_pressure.at[0, 0, 0].set(jnp.nan),
        tracers=state.tracers,
    )

    fallback_tendency = equation.temperature_tendency(
        bad_pressure_state,
        aux_state,
    )
    incumbent_tendency = equation.temperature_tendency_temperature_form(aux_state)

    np.testing.assert_allclose(
        fallback_tendency,
        incumbent_tendency,
        rtol=1e-6,
        atol=1e-6,
    )


def test_equation_and_filter_helpers_match_direct_dinosaur_calls():
    """Equation and filter helpers instantiate the expected Dinosaur objects."""
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    orography = jnp.zeros(grid.coords.horizontal.modal_shape, dtype=jnp.float32)

    dry_equation = _primitive_equation(
        reference_temperature=reference_temperature,
        orography=orography,
        coords=grid.coords,
        physics_specs=cast(Any, physics_specs),
        include_vertical_advection=False,
        humidity_key=None,
    )
    moist_equation = _primitive_equation(
        reference_temperature=reference_temperature,
        orography=orography,
        coords=grid.coords,
        physics_specs=cast(Any, physics_specs),
        include_vertical_advection=False,
        humidity_key="specific_humidity",
    )

    assert isinstance(dry_equation, primitive_equations.PrimitiveEquations)
    assert dry_equation.humidity_key is None
    assert isinstance(moist_equation, primitive_equations.PrimitiveEquationsSigma)
    assert moist_equation.humidity_key == "specific_humidity"

    step_seconds = _nondimensionalize_seconds(physics_specs, 3600.0)
    helper_filter = _horizontal_diffusion_step_filter(
        coords=grid.coords,
        physics_specs=physics_specs,
        step_seconds=step_seconds,
        tau_seconds=None,
        order=2,
    )
    resolution_factor = grid.coords.horizontal.latitude_nodes / 128.0
    tau_seconds = 8.6 / (2.4 ** np.log2(resolution_factor)) * 3600.0
    direct_filter = time_integration.horizontal_diffusion_step_filter(
        grid.coords.horizontal,
        dt=step_seconds,
        tau=_nondimensionalize_seconds(physics_specs, tau_seconds),
        order=2,
    )
    state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=(250, 750),
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )

    _assert_pytree_allclose(helper_filter(state, state), direct_filter(state, state))


def test_exact_coriolis_rotation_filter_preserves_small_angle_kinetic_energy():
    """The wind-space rotation is skew-symmetric before truncation dominates."""
    coords, physics_specs, state = _synthetic_coriolis_split_state()
    step_seconds = 1e-6
    step_filter = _exact_coriolis_rotation_step_filter(
        coords=coords,
        physics_specs=physics_specs,
        step_seconds=step_seconds,
    )

    rotated = step_filter(state, state)

    u_wind, v_wind = spherical_harmonic.vor_div_to_uv_nodal(
        coords.horizontal,
        state.vorticity,
        state.divergence,
    )
    u_rotated, v_rotated = spherical_harmonic.vor_div_to_uv_nodal(
        coords.horizontal,
        rotated.vorticity,
        rotated.divergence,
    )
    kinetic_energy = 0.5 * jnp.sum(u_wind**2 + v_wind**2)
    rotated_kinetic_energy = 0.5 * jnp.sum(u_rotated**2 + v_rotated**2)

    assert float(kinetic_energy) > 0.0
    np.testing.assert_allclose(
        rotated_kinetic_energy,
        kinetic_energy,
        rtol=1e-6,
        atol=1e-7,
    )


def test_symmetric_exact_coriolis_step_matches_full_rotation_for_identity_step():
    """Two exact half rotations match one full rotation without dynamics between."""
    coords, physics_specs, state = _synthetic_coriolis_split_state()
    step_seconds = 1e-6
    step_inputs = []
    half_rotation_filter = _exact_coriolis_rotation_step_filter(
        coords=coords,
        physics_specs=physics_specs,
        step_seconds=0.5 * step_seconds,
    )
    full_rotation_filter = _exact_coriolis_rotation_step_filter(
        coords=coords,
        physics_specs=physics_specs,
        step_seconds=step_seconds,
    )

    def identity_step(step_state):
        step_inputs.append(step_state)
        return step_state

    symmetric_step = _symmetric_exact_coriolis_rotation_step(
        identity_step,
        coords=coords,
        physics_specs=physics_specs,
        step_seconds=step_seconds,
    )

    actual = symmetric_step(state)
    expected_step_input = half_rotation_filter(state, state)
    expected = full_rotation_filter(state, state)

    assert len(step_inputs) == 1
    _assert_pytree_allclose(step_inputs[0], expected_step_input)
    _assert_pytree_allclose(actual, expected)


def test_exact_coriolis_rotation_sign_matches_source_negative_curl_convention():
    """Source `-curl/div(f(-v, u))` implies wind tendency `(f v, -f u)`."""
    coords, physics_specs, state = _synthetic_coriolis_split_state()
    equation = _primitive_equation(
        reference_temperature=np.zeros((coords.vertical.layers,), dtype=np.float32),
        orography=jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        coords=coords,
        physics_specs=physics_specs,
        include_vertical_advection=False,
        humidity_key=None,
    )
    u_wind, v_wind = spherical_harmonic.vor_div_to_uv_nodal(
        coords.horizontal,
        state.vorticity,
        state.divergence,
    )
    step_seconds = 1e-3
    angle = equation.coriolis_parameter * step_seconds

    u_rotated = u_wind * jnp.cos(angle) + v_wind * jnp.sin(angle)
    v_rotated = v_wind * jnp.cos(angle) - u_wind * jnp.sin(angle)
    u_tendency = (u_rotated - u_wind) / step_seconds
    v_tendency = (v_rotated - v_wind) / step_seconds

    np.testing.assert_allclose(
        u_tendency,
        equation.coriolis_parameter * v_wind,
        rtol=2e-3,
        atol=3e-5,
    )
    np.testing.assert_allclose(
        v_tendency,
        -equation.coriolis_parameter * u_wind,
        rtol=2e-3,
        atol=3e-5,
    )


def test_exact_coriolis_rotation_filter_preserves_non_wind_state_exactly():
    """The rotation filter only replaces modal vorticity and divergence."""
    coords, physics_specs, next_state = _synthetic_coriolis_split_state()
    prev_state = _primitive_equation_state(
        vorticity=jnp.zeros_like(next_state.vorticity),
        divergence=jnp.zeros_like(next_state.divergence),
        temperature_variation=jnp.zeros_like(next_state.temperature_variation),
        log_surface_pressure=jnp.zeros_like(next_state.log_surface_pressure),
        tracers={
            name: jnp.zeros_like(value) for name, value in next_state.tracers.items()
        },
        sim_time=jnp.asarray(-1.0, dtype=jnp.float32),
    )
    step_filter = _exact_coriolis_rotation_step_filter(
        coords=coords,
        physics_specs=physics_specs,
        step_seconds=1e-2,
    )

    rotated = step_filter(prev_state, next_state)

    assert float(jnp.max(jnp.abs(rotated.vorticity - next_state.vorticity))) > 0.0
    assert float(jnp.max(jnp.abs(rotated.divergence - next_state.divergence))) > 0.0
    np.testing.assert_array_equal(
        rotated.temperature_variation,
        next_state.temperature_variation,
    )
    np.testing.assert_array_equal(
        rotated.log_surface_pressure,
        next_state.log_surface_pressure,
    )
    assert rotated.tracers.keys() == next_state.tracers.keys()
    for tracer_name, tracer_value in rotated.tracers.items():
        np.testing.assert_array_equal(tracer_value, next_state.tracers[tracer_name])
    np.testing.assert_array_equal(rotated.sim_time, next_state.sim_time)


def test_exact_coriolis_half_rotation_preserves_non_wind_state_exactly():
    """A half rotation leaves thermodynamic, tracer, and time leaves unchanged."""
    coords, physics_specs, next_state = _synthetic_coriolis_split_state()
    half_rotation_filter = _exact_coriolis_rotation_step_filter(
        coords=coords,
        physics_specs=physics_specs,
        step_seconds=0.5e-2,
    )

    rotated = half_rotation_filter(next_state, next_state)

    assert float(jnp.max(jnp.abs(rotated.vorticity - next_state.vorticity))) > 0.0
    assert float(jnp.max(jnp.abs(rotated.divergence - next_state.divergence))) > 0.0
    np.testing.assert_array_equal(
        rotated.temperature_variation,
        next_state.temperature_variation,
    )
    np.testing.assert_array_equal(
        rotated.log_surface_pressure,
        next_state.log_surface_pressure,
    )
    assert rotated.tracers.keys() == next_state.tracers.keys()
    for tracer_name, tracer_value in rotated.tracers.items():
        np.testing.assert_array_equal(tracer_value, next_state.tracers[tracer_name])
    np.testing.assert_array_equal(rotated.sim_time, next_state.sim_time)


def test_theta_layer_mean_recenter_matches_previous_theta_zero_mode_only():
    """The theta recentering filter changes only layerwise temperature zero modes."""
    coords, physics_specs, prev_state = _synthetic_coriolis_split_state()
    reference_temperature = _reference_temperature(
        layer_count=coords.vertical.layers,
        temperature_kelvin=250.0,
    )
    next_temperature_variation = (
        spherical_harmonic.add_constant(
            prev_state.temperature_variation,
            jnp.asarray([2.0, -1.5], dtype=jnp.float32),
        )
        .at[:, 1, 1]
        .set(jnp.asarray([0.05, -0.03], dtype=jnp.float32))
    )
    next_state = _primitive_equation_state(
        vorticity=prev_state.vorticity + jnp.float32(0.01),
        divergence=prev_state.divergence - jnp.float32(0.02),
        temperature_variation=next_temperature_variation,
        log_surface_pressure=prev_state.log_surface_pressure,
        tracers={
            name: value + jnp.float32(0.001)
            for name, value in prev_state.tracers.items()
        },
        sim_time=jnp.asarray(4.0, dtype=jnp.float32),
    )
    step_filter = _theta_layer_mean_recenter_step_filter(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
    )

    corrected = step_filter(prev_state, next_state)

    assert (
        float(
            jnp.max(
                jnp.abs(
                    corrected.temperature_variation - next_state.temperature_variation
                )
            )
        )
        > 0.0
    )
    modal_delta = corrected.temperature_variation - next_state.temperature_variation
    np.testing.assert_allclose(
        modal_delta.at[:, 0, 0].set(0.0),
        0.0,
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        _theta_layer_mean(coords, physics_specs, reference_temperature, corrected),
        _theta_layer_mean(coords, physics_specs, reference_temperature, prev_state),
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_array_equal(corrected.vorticity, next_state.vorticity)
    np.testing.assert_array_equal(corrected.divergence, next_state.divergence)
    np.testing.assert_array_equal(
        corrected.log_surface_pressure,
        next_state.log_surface_pressure,
    )
    assert corrected.tracers.keys() == next_state.tracers.keys()
    for tracer_name, tracer_value in corrected.tracers.items():
        np.testing.assert_array_equal(tracer_value, next_state.tracers[tracer_name])
    np.testing.assert_array_equal(corrected.sim_time, next_state.sim_time)


def test_theta_layer_mean_recenter_falls_back_for_nonfinite_pressure():
    """Invalid pressure diagnostics preserve the incumbent next state exactly."""
    coords, physics_specs, prev_state = _synthetic_coriolis_split_state()
    reference_temperature = _reference_temperature(
        layer_count=coords.vertical.layers,
        temperature_kelvin=250.0,
    )
    bad_next_state = _primitive_equation_state(
        vorticity=prev_state.vorticity,
        divergence=prev_state.divergence,
        temperature_variation=spherical_harmonic.add_constant(
            prev_state.temperature_variation,
            jnp.asarray([1.0, -2.0], dtype=jnp.float32),
        ),
        log_surface_pressure=prev_state.log_surface_pressure.at[0, 0, 0].set(jnp.nan),
        tracers=prev_state.tracers,
        sim_time=prev_state.sim_time,
    )
    step_filter = _theta_layer_mean_recenter_step_filter(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
    )

    corrected = step_filter(prev_state, bad_next_state)

    np.testing.assert_array_equal(
        corrected.temperature_variation,
        bad_next_state.temperature_variation,
    )
    np.testing.assert_array_equal(corrected.vorticity, bad_next_state.vorticity)
    np.testing.assert_array_equal(corrected.divergence, bad_next_state.divergence)
    np.testing.assert_array_equal(
        corrected.log_surface_pressure,
        bad_next_state.log_surface_pressure,
    )
    assert corrected.tracers.keys() == bad_next_state.tracers.keys()
    for tracer_name, tracer_value in corrected.tracers.items():
        np.testing.assert_array_equal(
            tracer_value,
            bad_next_state.tracers[tracer_name],
        )


def test_tropical_wtg_mass_dse_filter_changes_only_temperature_and_is_neutral():
    """WTG relaxation is thermal-only, masked vertically, and layer neutral."""
    coords, physics_specs, prev_state, next_state = _synthetic_wtg_mass_dse_state()
    reference_temperature = _reference_temperature(
        layer_count=coords.vertical.layers,
        temperature_kelvin=250.0,
    )
    step_filter = _tropical_wtg_mass_dse_relaxation_step_filter(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        step_seconds=_nondimensionalize_seconds(physics_specs, 3600.0),
    )

    corrected = step_filter(prev_state, next_state)

    modal_delta = corrected.temperature_variation - next_state.temperature_variation
    nodal_delta = coords.horizontal.to_nodal(modal_delta)
    assert float(jnp.max(jnp.abs(nodal_delta))) > 0.0
    np.testing.assert_allclose(nodal_delta[0], 0.0, rtol=1e-6, atol=1e-6)
    np.testing.assert_allclose(nodal_delta[2], 0.0, rtol=1e-6, atol=1e-6)
    temperature_increment_cap = _unit_factor(physics_specs, "kelvin") * (
        _TROPICAL_WTG_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN
    )
    polar_leakage = jnp.maximum(
        jnp.max(jnp.abs(nodal_delta[:, :, 0])),
        jnp.max(jnp.abs(nodal_delta[:, :, -1])),
    )
    assert float(polar_leakage) <= 0.01 * temperature_increment_cap + 1.0e-6
    quadrature_weights = jnp.asarray(coords.horizontal.quadrature_weights)
    layer_mean_delta = (
        jnp.sum(nodal_delta * quadrature_weights, axis=(-2, -1))
        / jnp.sum(quadrature_weights)
    )
    np.testing.assert_allclose(layer_mean_delta, 0.0, rtol=1e-6, atol=1e-6)
    assert float(jnp.max(jnp.abs(nodal_delta))) <= temperature_increment_cap + 1.0e-6
    np.testing.assert_array_equal(corrected.vorticity, next_state.vorticity)
    np.testing.assert_array_equal(corrected.divergence, next_state.divergence)
    np.testing.assert_array_equal(
        corrected.log_surface_pressure,
        next_state.log_surface_pressure,
    )
    assert corrected.tracers.keys() == next_state.tracers.keys()
    for tracer_name, tracer_value in corrected.tracers.items():
        np.testing.assert_array_equal(tracer_value, next_state.tracers[tracer_name])
    np.testing.assert_array_equal(corrected.sim_time, next_state.sim_time)


def test_tropical_wtg_mass_dse_filter_falls_back_for_nonfinite_dse():
    """Invalid DSE diagnostics preserve the incumbent next state exactly."""
    coords, physics_specs, prev_state, next_state = _synthetic_wtg_mass_dse_state()
    reference_temperature = _reference_temperature(
        layer_count=coords.vertical.layers,
        temperature_kelvin=250.0,
    )
    reference_temperature = reference_temperature.copy()
    reference_temperature[1] = np.nan
    step_filter = _tropical_wtg_mass_dse_relaxation_step_filter(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        step_seconds=_nondimensionalize_seconds(physics_specs, 3600.0),
    )

    corrected = step_filter(prev_state, next_state)

    np.testing.assert_array_equal(
        corrected.temperature_variation,
        next_state.temperature_variation,
    )
    np.testing.assert_array_equal(corrected.vorticity, next_state.vorticity)
    np.testing.assert_array_equal(corrected.divergence, next_state.divergence)
    np.testing.assert_array_equal(
        corrected.log_surface_pressure,
        next_state.log_surface_pressure,
    )
    assert corrected.tracers.keys() == next_state.tracers.keys()
    for tracer_name, tracer_value in corrected.tracers.items():
        np.testing.assert_array_equal(tracer_value, next_state.tracers[tracer_name])
    np.testing.assert_array_equal(corrected.sim_time, next_state.sim_time)


def test_weak_held_suarez_composes_one_equation_with_fixed_forcing(monkeypatch):
    """Weak HS composition combines one primitive equation with fixed forcing."""
    compose_calls = []
    real_compose_equations = time_integration.compose_equations

    def capture_compose_equations(equations):
        compose_calls.append(tuple(equations))
        return real_compose_equations(equations)

    monkeypatch.setattr(
        time_integration,
        "compose_equations",
        capture_compose_equations,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        include_vertical_advection=False,
        apply_weak_held_suarez_relaxation=True,
        jit_forecast=False,
    )

    model._trajectory_function(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        inner_steps=1,
        output_count=1,
        use_humidity_in_dynamics=False,
    )

    assert len(compose_calls) == 1
    primitive_equation, forcing = compose_calls[0]
    assert isinstance(primitive_equation, primitive_equations.PrimitiveEquations)
    assert isinstance(forcing, _TracerSafeHeldSuarezForcingSigma)
    day = scales.units.day
    assert forcing.kf == physics_specs.nondimensionalize(0.0 / day)
    np.testing.assert_allclose(
        forcing.ka,
        physics_specs.nondimensionalize(1 / (160.0 * day)),
    )
    np.testing.assert_allclose(
        forcing.ks,
        physics_specs.nondimensionalize(1 / (16.0 * day)),
    )


def test_weak_held_suarez_forcing_is_thermal_only_and_tracer_safe():
    """The local forcing emits zero wind and matching zero tracer tendencies."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1), lead_steps=(0,)
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    dinosaur_state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )
    forcing = _TracerSafeHeldSuarezForcingSigma(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        kf=0.0 / scales.units.day,
        ka=1 / (160.0 * scales.units.day),
        ks=1 / (16.0 * scales.units.day),
    )

    tendency = forcing.explicit_terms(dinosaur_state)

    np.testing.assert_array_equal(
        tendency.vorticity, jnp.zeros_like(tendency.vorticity)
    )
    np.testing.assert_array_equal(
        tendency.divergence,
        jnp.zeros_like(tendency.divergence),
    )
    assert tendency.tracers.keys() == dinosaur_state.tracers.keys()
    for tracer_name, tracer_tendency in tendency.tracers.items():
        np.testing.assert_array_equal(
            tracer_tendency,
            jnp.zeros_like(dinosaur_state.tracers[tracer_name]),
        )


def test_weak_held_suarez_zero_offset_reproduces_incumbent_tendency():
    """A zero HS-equilibrium offset leaves the incumbent tendency unchanged."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1), lead_steps=(0,)
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    dinosaur_state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )
    incumbent_forcing = _TracerSafeHeldSuarezForcingSigma(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        kf=0.0 / scales.units.day,
        ka=1 / (160.0 * scales.units.day),
        ks=1 / (16.0 * scales.units.day),
    )
    zero_offset_forcing = _TracerSafeHeldSuarezForcingSigma(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        kf=0.0 / scales.units.day,
        ka=1 / (160.0 * scales.units.day),
        ks=1 / (16.0 * scales.units.day),
        equilibrium_temperature_offset=jnp.zeros(
            grid.coords.nodal_shape,
            dtype=jnp.float32,
        ),
    )

    incumbent_tendency = incumbent_forcing.explicit_terms(dinosaur_state)
    zero_offset_tendency = zero_offset_forcing.explicit_terms(dinosaur_state)

    _assert_pytree_allclose(zero_offset_tendency, incumbent_tendency)


def test_analysis_offset_hs_eq_mask_uses_fixed_wavenumber_cutoffs():
    """The analysis-offset mask keeps the area mean and fixed low-order modes."""
    horizontal_grid = _residual_split_test_grid()

    low_mode_mask = np.asarray(_analysis_offset_weak_hs_low_mode_mask(horizontal_grid))

    longitude_wavenumber, total_wavenumber = horizontal_grid.modal_mesh
    expected_mask = (
        np.asarray(horizontal_grid.mask)
        & (
            np.abs(longitude_wavenumber)
            <= _ANALYSIS_OFFSET_HELD_SUAREZ_MAX_LONGITUDE_WAVENUMBER
        )
        & (total_wavenumber <= _ANALYSIS_OFFSET_HELD_SUAREZ_MAX_TOTAL_WAVENUMBER)
    )
    np.testing.assert_array_equal(low_mode_mask, expected_mask.astype(np.float32))
    assert low_mode_mask[0, 0] == 1.0


def test_analysis_offset_hs_eq_offset_clips_and_falls_back_to_zero():
    """Offset construction clips finite amplitudes and zeros nonfinite offsets."""
    coords, physics_specs, reference_temperature = _analysis_offset_test_setup()
    offset_cap = _ANALYSIS_OFFSET_HELD_SUAREZ_MAX_KELVIN * _unit_factor(
        physics_specs, "kelvin"
    )
    raw_offset = jnp.full(coords.nodal_shape, 3.0 * offset_cap, dtype=jnp.float32)
    dinosaur_state = _dinosaur_state_with_hs_equilibrium_offset(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        equilibrium_offset=raw_offset,
    )

    offset = _analysis_offset_weak_held_suarez_equilibrium(
        dinosaur_state,
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
    )

    assert bool(jnp.isfinite(offset).all())
    np.testing.assert_allclose(offset, offset_cap, rtol=1e-5, atol=1e-5)

    invalid_state = _dinosaur_state_with_hs_equilibrium_offset(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        equilibrium_offset=raw_offset.at[0, 0, 0].set(jnp.nan),
    )
    fallback_offset = _analysis_offset_weak_held_suarez_equilibrium(
        invalid_state,
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
    )

    np.testing.assert_array_equal(fallback_offset, jnp.zeros_like(fallback_offset))


def test_analysis_offset_hs_eq_offset_applies_low_order_mask():
    """Offset construction removes modes outside the fixed low-order mask."""
    coords, physics_specs, reference_temperature = _analysis_offset_test_setup()
    longitude_wavenumber, total_wavenumber = coords.horizontal.modal_mesh
    valid_modes = np.asarray(coords.horizontal.mask)
    low_mode_index = tuple(
        np.argwhere(
            valid_modes & (np.abs(longitude_wavenumber) == 2) & (total_wavenumber == 4)
        )[0]
    )
    high_mode_index = tuple(
        np.argwhere(
            valid_modes
            & (
                np.abs(longitude_wavenumber)
                > _ANALYSIS_OFFSET_HELD_SUAREZ_MAX_LONGITUDE_WAVENUMBER
            )
            & (total_wavenumber == 4)
        )[0]
    )
    modal_offset = jnp.zeros(coords.modal_shape, dtype=jnp.float32)
    modal_offset = modal_offset.at[:, low_mode_index[0], low_mode_index[1]].set(0.2)
    modal_offset = modal_offset.at[:, high_mode_index[0], high_mode_index[1]].set(0.2)
    raw_offset = coords.horizontal.to_nodal(modal_offset)
    dinosaur_state = _dinosaur_state_with_hs_equilibrium_offset(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        equilibrium_offset=raw_offset,
    )

    filtered_offset = _analysis_offset_weak_held_suarez_equilibrium(
        dinosaur_state,
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
    )

    filtered_modal_offset = coords.horizontal.to_modal(filtered_offset)
    low_mode_mask = _analysis_offset_weak_hs_low_mode_mask(coords.horizontal)
    np.testing.assert_allclose(
        filtered_modal_offset * (1.0 - low_mode_mask),
        0.0,
        rtol=1e-5,
        atol=1e-5,
    )
    retained_low_mode = filtered_modal_offset[
        :,
        low_mode_index[0],
        low_mode_index[1],
    ]
    assert float(jnp.abs(retained_low_mode).max()) > 0.1


def test_weak_held_suarez_helper_uses_dinosaur_forcing_type():
    """The helper composes a Dinosaur explicit forcing with primitive equations."""
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    orography = jnp.zeros(grid.coords.horizontal.modal_shape, dtype=jnp.float32)
    equation = _primitive_equation(
        reference_temperature=reference_temperature,
        orography=orography,
        coords=grid.coords,
        physics_specs=cast(Any, physics_specs),
        include_vertical_advection=False,
        humidity_key=None,
    )

    composed_equation = _compose_weak_held_suarez_equation(
        equation=equation,
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        kf_per_day=0.0,
        ka_timescale_days=160.0,
        ks_timescale_days=16.0,
    )

    assert isinstance(composed_equation, time_integration.ImplicitExplicitODE)
    assert issubclass(
        _TracerSafeHeldSuarezForcingSigma, held_suarez.HeldSuarezForcingSigma
    )


def test_ocean_bulk_shf_zero_ocean_weight_reproduces_incumbent_tendency():
    """Zero ocean weight adds no explicit tendency to the primitive equations."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    equation = _primitive_equation(
        reference_temperature=reference_temperature,
        orography=jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        coords=coords,
        physics_specs=cast(Any, physics_specs),
        include_vertical_advection=False,
        humidity_key=None,
    )
    current_temperature = (
        coords.horizontal.to_nodal(state.temperature_variation)[-1]
        + reference_temperature[-1]
    )
    candidate_equation = _compose_ocean_bulk_sensible_heat_flux_equation(
        equation=equation,
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        ocean_weight=jnp.zeros(coords.horizontal.nodal_shape, dtype=jnp.float32),
        temperature_anchor=current_temperature + 5.0,
        step_seconds=_nondimensionalize_seconds(physics_specs, 900.0),
    )

    incumbent_tendency = equation.explicit_terms(state)
    candidate_tendency = candidate_equation.explicit_terms(state)

    _assert_pytree_allclose(candidate_tendency, incumbent_tendency)


def test_hsl_theta_zero_wind_reproduces_incumbent_theta_transport():
    """Zero horizontal wind keeps the accepted theta tendency bitwise unchanged."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    zero_wind_state = _primitive_equation_state(
        vorticity=jnp.zeros_like(state.vorticity),
        divergence=jnp.zeros_like(state.divergence),
        temperature_variation=state.temperature_variation,
        log_surface_pressure=state.log_surface_pressure,
        tracers={},
    )
    common_kwargs = {
        "reference_temperature": reference_temperature,
        "orography": jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        "coords": coords,
        "physics_specs": cast(Any, physics_specs),
        "include_vertical_advection": False,
        "temperature_tendency_formulation": (
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
    }
    incumbent_equation = primitive_equations.PrimitiveEquations(**common_kwargs)
    candidate_equation = primitive_equations.PrimitiveEquations(
        **common_kwargs,
        use_horizontal_semilagrangian_theta_transport=True,
        horizontal_semilagrangian_theta_transport_step=_nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    )
    aux_state = primitive_equations.compute_diagnostic_state_sigma(
        zero_wind_state,
        coords,
    )

    incumbent_tendency = (
        incumbent_equation.temperature_tendency_potential_temperature_form(
            zero_wind_state,
            aux_state,
        )
    )
    candidate_tendency = (
        candidate_equation.temperature_tendency_potential_temperature_form(
            zero_wind_state,
            aux_state,
        )
    )

    np.testing.assert_array_equal(candidate_tendency, incumbent_tendency)


def test_hsl2_theta_zero_and_uniform_wind_match_first_order_transport():
    """Midpoint departure is identical to first order for zero or uniform winds."""
    coords, physics_specs, reference_temperature, _ = _ocean_bulk_shf_test_setup()
    common_kwargs = {
        "reference_temperature": reference_temperature,
        "orography": jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        "coords": coords,
        "physics_specs": cast(Any, physics_specs),
        "include_vertical_advection": False,
        "temperature_tendency_formulation": (
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        "use_horizontal_semilagrangian_theta_transport": True,
        "horizontal_semilagrangian_theta_transport_step": _nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    }
    first_order_equation = primitive_equations.PrimitiveEquations(**common_kwargs)
    midpoint_equation = primitive_equations.PrimitiveEquations(
        **common_kwargs,
        use_midpoint_semilagrangian_theta_departure=True,
    )
    theta_anomaly = jnp.arange(
        np.prod(coords.nodal_shape),
        dtype=jnp.float32,
    ).reshape(coords.nodal_shape)
    incumbent_horizontal_tendency = jnp.full_like(theta_anomaly, 0.75)
    zero_aux_state = _hsl_theta_aux_state(
        coords,
        u_cos_lat=jnp.zeros(coords.nodal_shape, dtype=jnp.float32),
        v_cos_lat=jnp.zeros(coords.nodal_shape, dtype=jnp.float32),
        temperature_variation=theta_anomaly,
    )
    uniform_aux_state = _hsl_theta_aux_state(
        coords,
        u_cos_lat=jnp.full(coords.nodal_shape, 1.0e-3, dtype=jnp.float32),
        v_cos_lat=jnp.full(coords.nodal_shape, -5.0e-4, dtype=jnp.float32),
        temperature_variation=theta_anomaly,
    )

    for aux_state in (zero_aux_state, uniform_aux_state):
        expected_tendency = (
            first_order_equation.horizontal_semilagrangian_theta_transport(
                theta_anomaly,
                aux_state,
                incumbent_horizontal_tendency,
            )
        )
        actual_tendency = midpoint_equation.horizontal_semilagrangian_theta_transport(
            theta_anomaly,
            aux_state,
            incumbent_horizontal_tendency,
        )

        np.testing.assert_allclose(actual_tendency, expected_tendency, atol=1.0e-7)


def test_hsl_theta_semilagrangian_transport_is_finite_and_bounded():
    """Capped departures stay finite at polar and equatorial rows."""
    physics_specs = units.SimUnits.from_si()
    horizontal_grid = spherical_harmonic.Grid(
        longitude_wavenumbers=4,
        total_wavenumbers=6,
        longitude_nodes=16,
        latitude_nodes=9,
        latitude_spacing="equiangular_with_poles",
        radius=physics_specs.radius,
    )
    coords = coordinate_systems.CoordinateSystem(
        horizontal_grid,
        sigma_coordinates.SigmaCoordinates.equidistant(2),
    )
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    equation = primitive_equations.PrimitiveEquations(
        reference_temperature,
        jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        coords,
        cast(Any, physics_specs),
        include_vertical_advection=False,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        use_horizontal_semilagrangian_theta_transport=True,
        horizontal_semilagrangian_theta_transport_step=1.0e-3,
    )
    longitude_pattern = jnp.arange(
        coords.horizontal.nodal_shape[0],
        dtype=jnp.float32,
    )[:, jnp.newaxis]
    latitude_pattern = jnp.arange(
        coords.horizontal.nodal_shape[1],
        dtype=jnp.float32,
    )[jnp.newaxis, :]
    theta_anomaly = jnp.stack(
        [
            longitude_pattern + 0.25 * latitude_pattern,
            0.5 * longitude_pattern - 0.1 * latitude_pattern,
        ],
        axis=0,
    )
    wind_shape = coords.nodal_shape
    equator_index = coords.horizontal.nodal_shape[1] // 2
    u_cos_lat = (
        jnp.zeros(wind_shape, dtype=jnp.float32)
        .at[:, :, 0]
        .set(2.0e-3)
        .at[:, :, equator_index]
        .set(1.0e-1)
        .at[:, :, -1]
        .set(-2.0e-3)
    )
    v_cos_lat = (
        jnp.zeros(wind_shape, dtype=jnp.float32)
        .at[:, :, 0]
        .set(1.0e-3)
        .at[:, :, equator_index]
        .set(-5.0e-2)
        .at[:, :, -1]
        .set(-1.0e-3)
    )
    zero_layer_boundaries = jnp.zeros(
        (coords.vertical.layers - 1,) + coords.horizontal.nodal_shape,
        dtype=jnp.float32,
    )
    aux_state = primitive_equations.DiagnosticStateSigma(
        vorticity=jnp.zeros(wind_shape, dtype=jnp.float32),
        divergence=jnp.zeros(wind_shape, dtype=jnp.float32),
        temperature_variation=theta_anomaly,
        cos_lat_u=(u_cos_lat, v_cos_lat),
        sigma_dot_explicit=zero_layer_boundaries,
        sigma_dot_full=zero_layer_boundaries,
        cos_lat_grad_log_sp=(
            jnp.zeros((1,) + coords.horizontal.nodal_shape, dtype=jnp.float32),
            jnp.zeros((1,) + coords.horizontal.nodal_shape, dtype=jnp.float32),
        ),
        u_dot_grad_log_sp=jnp.zeros(wind_shape, dtype=jnp.float32),
        tracers={},
    )

    longitude_displacement, latitude_displacement, valid_displacement = (
        equation._horizontal_semilagrangian_theta_departure_displacement(
            aux_state,
            theta_anomaly.dtype,
        )
    )
    tendency = equation.horizontal_semilagrangian_theta_transport(
        theta_anomaly,
        aux_state,
        incumbent_horizontal_tendency=jnp.zeros_like(theta_anomaly),
    )
    longitude_spacing = 2.0 * np.pi / coords.horizontal.nodal_shape[0]
    latitude_spacing = float(
        jnp.min(jnp.diff(jnp.asarray(coords.horizontal.latitudes)))
    )
    inspected_rows = jnp.asarray(
        [0, equator_index, coords.horizontal.nodal_shape[1] - 1]
    )

    assert bool(valid_displacement)
    assert bool(jnp.isfinite(longitude_displacement[:, :, inspected_rows]).all())
    assert bool(jnp.isfinite(latitude_displacement[:, :, inspected_rows]).all())
    cap_tolerance = 1.0e-6
    assert float(jnp.max(jnp.abs(longitude_displacement))) <= (
        primitive_equations.HORIZONTAL_SEMILAGRANGIAN_THETA_MAX_CFL * longitude_spacing
        + cap_tolerance
    )
    assert float(jnp.max(jnp.abs(latitude_displacement))) <= (
        primitive_equations.HORIZONTAL_SEMILAGRANGIAN_THETA_MAX_CFL * latitude_spacing
        + cap_tolerance
    )
    assert bool(jnp.isfinite(tendency).all())
    assert float(jnp.max(jnp.abs(tendency))) > 0.0


def test_hsl2_theta_midpoint_displacement_is_finite_and_bounded():
    """Midpoint departures keep the same finite CFL cap near all latitude rows."""
    physics_specs = units.SimUnits.from_si()
    horizontal_grid = spherical_harmonic.Grid(
        longitude_wavenumbers=4,
        total_wavenumbers=6,
        longitude_nodes=16,
        latitude_nodes=9,
        latitude_spacing="equiangular_with_poles",
        radius=physics_specs.radius,
    )
    coords = coordinate_systems.CoordinateSystem(
        horizontal_grid,
        sigma_coordinates.SigmaCoordinates.equidistant(2),
    )
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    equation = primitive_equations.PrimitiveEquations(
        reference_temperature,
        jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        coords,
        cast(Any, physics_specs),
        include_vertical_advection=False,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        use_horizontal_semilagrangian_theta_transport=True,
        use_midpoint_semilagrangian_theta_departure=True,
        horizontal_semilagrangian_theta_transport_step=1.0e-3,
    )
    longitude_pattern = jnp.arange(
        coords.horizontal.nodal_shape[0],
        dtype=jnp.float32,
    )[:, jnp.newaxis]
    latitude_pattern = jnp.arange(
        coords.horizontal.nodal_shape[1],
        dtype=jnp.float32,
    )[jnp.newaxis, :]
    theta_anomaly = jnp.stack(
        [
            longitude_pattern + 0.25 * latitude_pattern,
            0.5 * longitude_pattern - 0.1 * latitude_pattern,
        ],
        axis=0,
    )
    equator_index = coords.horizontal.nodal_shape[1] // 2
    u_cos_lat = (
        jnp.broadcast_to(
            2.0e-2 + 1.0e-3 * longitude_pattern,
            coords.horizontal.nodal_shape,
        )[jnp.newaxis]
        .repeat(coords.vertical.layers, axis=0)
        .at[:, :, 0]
        .set(2.0e-3)
        .at[:, :, equator_index]
        .set(1.0e-1)
        .at[:, :, -1]
        .set(-2.0e-3)
    )
    v_cos_lat = (
        jnp.broadcast_to(
            -1.0e-2 + 5.0e-4 * latitude_pattern,
            coords.horizontal.nodal_shape,
        )[jnp.newaxis]
        .repeat(coords.vertical.layers, axis=0)
        .at[:, :, 0]
        .set(1.0e-3)
        .at[:, :, equator_index]
        .set(-5.0e-2)
        .at[:, :, -1]
        .set(-1.0e-3)
    )
    aux_state = _hsl_theta_aux_state(
        coords,
        u_cos_lat=u_cos_lat,
        v_cos_lat=v_cos_lat,
        temperature_variation=theta_anomaly,
    )

    longitude_displacement, latitude_displacement, valid_displacement = (
        equation._horizontal_semilagrangian_theta_midpoint_departure_displacement(
            aux_state,
            theta_anomaly.dtype,
        )
    )
    tendency = equation.horizontal_semilagrangian_theta_transport(
        theta_anomaly,
        aux_state,
        incumbent_horizontal_tendency=jnp.zeros_like(theta_anomaly),
    )
    longitude_spacing = 2.0 * np.pi / coords.horizontal.nodal_shape[0]
    latitude_spacing = float(
        jnp.min(jnp.diff(jnp.asarray(coords.horizontal.latitudes)))
    )
    inspected_rows = jnp.asarray(
        [0, equator_index, coords.horizontal.nodal_shape[1] - 1]
    )

    assert bool(valid_displacement)
    assert bool(jnp.isfinite(longitude_displacement[:, :, inspected_rows]).all())
    assert bool(jnp.isfinite(latitude_displacement[:, :, inspected_rows]).all())
    cap_tolerance = 1.0e-6
    assert float(jnp.max(jnp.abs(longitude_displacement))) <= (
        primitive_equations.HORIZONTAL_SEMILAGRANGIAN_THETA_MAX_CFL * longitude_spacing
        + cap_tolerance
    )
    assert float(jnp.max(jnp.abs(latitude_displacement))) <= (
        primitive_equations.HORIZONTAL_SEMILAGRANGIAN_THETA_MAX_CFL * latitude_spacing
        + cap_tolerance
    )
    assert bool(jnp.isfinite(tendency).all())
    assert float(jnp.max(jnp.abs(tendency))) > 0.0


def test_hsl_theta_nonfinite_remap_falls_back_to_incumbent_theta_transport():
    """A nonfinite wind diagnostic selects the incumbent theta horizontal term."""
    coords, physics_specs, reference_temperature, _ = _ocean_bulk_shf_test_setup()
    equation = primitive_equations.PrimitiveEquations(
        reference_temperature,
        jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        coords,
        cast(Any, physics_specs),
        include_vertical_advection=False,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        use_horizontal_semilagrangian_theta_transport=True,
        horizontal_semilagrangian_theta_transport_step=_nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    )
    theta_anomaly = jnp.arange(
        np.prod(coords.nodal_shape),
        dtype=jnp.float32,
    ).reshape(coords.nodal_shape)
    u_cos_lat = jnp.ones(coords.nodal_shape, dtype=jnp.float32).at[0, 0, 0].set(jnp.nan)
    v_cos_lat = jnp.ones(coords.nodal_shape, dtype=jnp.float32)
    zero_layer_boundaries = jnp.zeros(
        (coords.vertical.layers - 1,) + coords.horizontal.nodal_shape,
        dtype=jnp.float32,
    )
    aux_state = primitive_equations.DiagnosticStateSigma(
        vorticity=jnp.zeros(coords.nodal_shape, dtype=jnp.float32),
        divergence=jnp.zeros(coords.nodal_shape, dtype=jnp.float32),
        temperature_variation=theta_anomaly,
        cos_lat_u=(u_cos_lat, v_cos_lat),
        sigma_dot_explicit=zero_layer_boundaries,
        sigma_dot_full=zero_layer_boundaries,
        cos_lat_grad_log_sp=(
            jnp.zeros((1,) + coords.horizontal.nodal_shape, dtype=jnp.float32),
            jnp.zeros((1,) + coords.horizontal.nodal_shape, dtype=jnp.float32),
        ),
        u_dot_grad_log_sp=jnp.zeros(coords.nodal_shape, dtype=jnp.float32),
        tracers={},
    )
    incumbent_horizontal_tendency = jnp.full_like(theta_anomaly, 1.25)

    tendency = equation.horizontal_semilagrangian_theta_transport(
        theta_anomaly,
        aux_state,
        incumbent_horizontal_tendency,
    )

    np.testing.assert_array_equal(tendency, incumbent_horizontal_tendency)


def test_hsl2_theta_nonfinite_midpoint_wind_falls_back_to_first_order(monkeypatch):
    """Nonfinite midpoint wind diagnostics select accepted first-order HSL theta."""
    coords, physics_specs, reference_temperature, _ = _ocean_bulk_shf_test_setup()
    common_kwargs = {
        "reference_temperature": reference_temperature,
        "orography": jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        "coords": coords,
        "physics_specs": cast(Any, physics_specs),
        "include_vertical_advection": False,
        "temperature_tendency_formulation": (
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        "use_horizontal_semilagrangian_theta_transport": True,
        "horizontal_semilagrangian_theta_transport_step": _nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    }
    first_order_equation = primitive_equations.PrimitiveEquations(**common_kwargs)
    midpoint_equation = primitive_equations.PrimitiveEquations(
        **common_kwargs,
        use_midpoint_semilagrangian_theta_departure=True,
    )
    theta_anomaly = jnp.arange(
        np.prod(coords.nodal_shape),
        dtype=jnp.float32,
    ).reshape(coords.nodal_shape)
    aux_state = _hsl_theta_aux_state(
        coords,
        u_cos_lat=jnp.full(coords.nodal_shape, 1.0e-3, dtype=jnp.float32),
        v_cos_lat=jnp.full(coords.nodal_shape, 5.0e-4, dtype=jnp.float32),
        temperature_variation=theta_anomaly,
    )
    incumbent_horizontal_tendency = jnp.full_like(theta_anomaly, -0.25)

    def nonfinite_midpoint_wind_components(
        aux_state,
        longitude_displacement,
        latitude_displacement,
    ):
        del longitude_displacement, latitude_displacement
        return (
            jnp.full_like(aux_state.cos_lat_u[0], jnp.nan),
            jnp.full_like(aux_state.cos_lat_u[1], jnp.nan),
        )

    monkeypatch.setattr(
        midpoint_equation,
        "_horizontal_semilagrangian_remap_wind_components",
        nonfinite_midpoint_wind_components,
    )

    expected_tendency = first_order_equation.horizontal_semilagrangian_theta_transport(
        theta_anomaly,
        aux_state,
        incumbent_horizontal_tendency,
    )
    actual_tendency = midpoint_equation.horizontal_semilagrangian_theta_transport(
        theta_anomaly,
        aux_state,
        incumbent_horizontal_tendency,
    )

    np.testing.assert_array_equal(actual_tendency, expected_tendency)


def test_hsl_theta_leaves_non_theta_explicit_tendencies_unchanged():
    """The selector only changes the thermodynamic theta transport hook."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    common_kwargs = {
        "reference_temperature": reference_temperature,
        "orography": jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        "coords": coords,
        "physics_specs": cast(Any, physics_specs),
        "include_vertical_advection": False,
        "temperature_tendency_formulation": (
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
    }
    incumbent_equation = primitive_equations.PrimitiveEquations(**common_kwargs)
    candidate_equation = primitive_equations.PrimitiveEquations(
        **common_kwargs,
        use_horizontal_semilagrangian_theta_transport=True,
        horizontal_semilagrangian_theta_transport_step=_nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    )

    incumbent_tendency = incumbent_equation.explicit_terms(state)
    candidate_tendency = candidate_equation.explicit_terms(state)

    np.testing.assert_array_equal(
        candidate_tendency.vorticity, incumbent_tendency.vorticity
    )
    np.testing.assert_array_equal(
        candidate_tendency.divergence, incumbent_tendency.divergence
    )
    np.testing.assert_array_equal(
        candidate_tendency.log_surface_pressure,
        incumbent_tendency.log_surface_pressure,
    )
    assert candidate_tendency.tracers == incumbent_tendency.tracers == {}
    assert bool(jnp.isfinite(candidate_tendency.temperature_variation).all())


def test_hsl2_theta_leaves_non_theta_explicit_tendencies_unchanged():
    """Midpoint departure changes only the horizontal theta transport hook."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    common_kwargs = {
        "reference_temperature": reference_temperature,
        "orography": jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        "coords": coords,
        "physics_specs": cast(Any, physics_specs),
        "include_vertical_advection": False,
        "temperature_tendency_formulation": (
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        "use_horizontal_semilagrangian_theta_transport": True,
        "horizontal_semilagrangian_theta_transport_step": _nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    }
    incumbent_equation = primitive_equations.PrimitiveEquations(**common_kwargs)
    candidate_equation = primitive_equations.PrimitiveEquations(
        **common_kwargs,
        use_midpoint_semilagrangian_theta_departure=True,
    )

    incumbent_tendency = incumbent_equation.explicit_terms(state)
    candidate_tendency = candidate_equation.explicit_terms(state)

    np.testing.assert_array_equal(
        candidate_tendency.vorticity, incumbent_tendency.vorticity
    )
    np.testing.assert_array_equal(
        candidate_tendency.divergence, incumbent_tendency.divergence
    )
    np.testing.assert_array_equal(
        candidate_tendency.log_surface_pressure,
        incumbent_tendency.log_surface_pressure,
    )
    assert candidate_tendency.tracers == incumbent_tendency.tracers == {}
    assert bool(jnp.isfinite(candidate_tendency.temperature_variation).all())


def test_dse_hsl_default_hsl2_theta_behavior_is_unchanged():
    """The HSL2 theta incumbent keeps DSE-HSL disabled by default."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    common_kwargs = {
        "reference_temperature": reference_temperature,
        "orography": jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        "coords": coords,
        "physics_specs": cast(Any, physics_specs),
        "include_vertical_advection": False,
        "temperature_tendency_formulation": (
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        "use_horizontal_semilagrangian_theta_transport": True,
        "use_midpoint_semilagrangian_theta_departure": True,
        "horizontal_semilagrangian_theta_transport_step": _nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    }
    default_equation = primitive_equations.PrimitiveEquations(**common_kwargs)
    explicit_false_equation = primitive_equations.PrimitiveEquations(
        **common_kwargs,
        use_dry_static_energy_hsl_transport=False,
    )

    assert not midpoint_semilagrangian_theta_departure_dinosaur_dycore_model().use_dry_static_energy_hsl_transport
    default_tendency = default_equation.explicit_terms(state)
    explicit_false_tendency = explicit_false_equation.explicit_terms(state)

    _assert_pytree_allclose(default_tendency, explicit_false_tendency)


def test_dse_hsl_uses_accepted_hsl2_transport_helper_with_dse_anomaly(monkeypatch):
    """DSE-HSL changes only the scalar passed through the accepted HSL2 helper."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    longitude_pattern = jnp.arange(
        coords.horizontal.nodal_shape[0],
        dtype=jnp.float32,
    )[:, jnp.newaxis]
    latitude_pattern = jnp.arange(
        coords.horizontal.nodal_shape[1],
        dtype=jnp.float32,
    )[jnp.newaxis, :]
    full_temperature = jnp.stack(
        [
            260.0 + 0.4 * longitude_pattern + 0.1 * latitude_pattern,
            280.0 - 0.2 * longitude_pattern + 0.3 * latitude_pattern,
        ],
        axis=0,
    )
    nonuniform_state = _primitive_equation_state(
        vorticity=state.vorticity,
        divergence=state.divergence,
        temperature_variation=coords.horizontal.to_modal(
            full_temperature - reference_temperature[:, np.newaxis, np.newaxis]
        ),
        log_surface_pressure=state.log_surface_pressure,
        tracers={},
    )
    equation = primitive_equations.PrimitiveEquations(
        reference_temperature,
        jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        coords,
        cast(Any, physics_specs),
        include_vertical_advection=False,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        use_horizontal_semilagrangian_theta_transport=True,
        use_midpoint_semilagrangian_theta_departure=True,
        use_dry_static_energy_hsl_transport=True,
        horizontal_semilagrangian_theta_transport_step=_nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    )
    aux_state = primitive_equations.compute_diagnostic_state_sigma(
        nonuniform_state,
        coords,
    )
    expected_dse_anomaly, _ = equation.nodal_dry_static_energy_anomaly(aux_state)
    theta_anomaly, _ = equation.nodal_potential_temperature_anomaly(
        nonuniform_state,
        aux_state,
    )
    captured: dict[str, jax.Array] = {}

    def capture_transport(scalar, aux_state, incumbent_horizontal_tendency):
        del aux_state
        captured["scalar"] = scalar
        return incumbent_horizontal_tendency

    monkeypatch.setattr(
        equation,
        "horizontal_semilagrangian_theta_transport",
        capture_transport,
    )

    tendency = equation.temperature_tendency_potential_temperature_form(
        nonuniform_state,
        aux_state,
    )

    assert bool(jnp.isfinite(tendency).all())
    np.testing.assert_allclose(captured["scalar"], expected_dse_anomaly, rtol=1e-6)
    assert not np.allclose(np.asarray(captured["scalar"]), np.asarray(theta_anomaly))
    quadrature_weights = jnp.asarray(coords.horizontal.quadrature_weights)
    layer_mean = (
        jnp.sum(captured["scalar"] * quadrature_weights, axis=(-2, -1))
        / jnp.sum(quadrature_weights)
    )
    np.testing.assert_allclose(layer_mean, jnp.zeros_like(layer_mean), atol=1.0e-5)


def test_dse_hsl_invalid_geopotential_falls_back_to_theta_hsl(monkeypatch):
    """Invalid DSE diagnostics reproduce the accepted theta-HSL tendency."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    common_kwargs = {
        "reference_temperature": reference_temperature,
        "orography": jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        "coords": coords,
        "physics_specs": cast(Any, physics_specs),
        "include_vertical_advection": False,
        "temperature_tendency_formulation": (
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        "use_horizontal_semilagrangian_theta_transport": True,
        "use_midpoint_semilagrangian_theta_departure": True,
        "horizontal_semilagrangian_theta_transport_step": _nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    }
    theta_equation = primitive_equations.PrimitiveEquations(**common_kwargs)
    dse_equation = primitive_equations.PrimitiveEquations(
        **common_kwargs,
        use_dry_static_energy_hsl_transport=True,
    )
    aux_state = primitive_equations.compute_diagnostic_state_sigma(state, coords)
    expected_tendency = theta_equation.temperature_tendency_potential_temperature_form(
        state,
        aux_state,
    )

    def nonfinite_geopotential(temperature, *args, **kwargs):
        del args, kwargs
        return jnp.full_like(temperature, jnp.nan)

    monkeypatch.setattr(
        primitive_equations,
        "get_geopotential_on_sigma",
        nonfinite_geopotential,
    )

    actual_tendency = dse_equation.temperature_tendency_potential_temperature_form(
        state,
        aux_state,
    )

    np.testing.assert_array_equal(actual_tendency, expected_tendency)


def test_layer_mass_dse_uses_sigma_pressure_thickness_and_dse_anomaly(monkeypatch):
    """Mass-DSE transports sigma-layer pressure thickness times DSE anomaly."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    longitude_pattern = jnp.arange(
        coords.horizontal.nodal_shape[0],
        dtype=jnp.float32,
    )[:, jnp.newaxis]
    latitude_pattern = jnp.arange(
        coords.horizontal.nodal_shape[1],
        dtype=jnp.float32,
    )[jnp.newaxis, :]
    full_temperature = jnp.stack(
        [
            260.0 + 0.4 * longitude_pattern + 0.1 * latitude_pattern,
            280.0 - 0.2 * longitude_pattern + 0.3 * latitude_pattern,
        ],
        axis=0,
    )
    surface_pressure = (
        100_000.0
        * _unit_factor(physics_specs, "pascal")
        * (1.0 + 0.02 * longitude_pattern + 0.01 * latitude_pattern)
    )
    nonuniform_state = _primitive_equation_state(
        vorticity=state.vorticity,
        divergence=state.divergence,
        temperature_variation=coords.horizontal.to_modal(
            full_temperature - reference_temperature[:, np.newaxis, np.newaxis]
        ),
        log_surface_pressure=coords.horizontal.to_modal(jnp.log(surface_pressure))[
            jnp.newaxis
        ],
        tracers={},
    )
    equation = primitive_equations.PrimitiveEquations(
        reference_temperature,
        jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        coords,
        cast(Any, physics_specs),
        include_vertical_advection=False,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        use_horizontal_semilagrangian_theta_transport=True,
        use_midpoint_semilagrangian_theta_departure=True,
        use_dry_static_energy_hsl_transport=True,
        use_layer_mass_weighted_dse_hsl_transport=True,
        horizontal_semilagrangian_theta_transport_step=_nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    )
    aux_state = primitive_equations.compute_diagnostic_state_sigma(
        nonuniform_state,
        coords,
    )
    dse_anomaly, _ = equation.nodal_dry_static_energy_anomaly(aux_state)
    layer_pressure_thickness = equation.nodal_sigma_layer_pressure_thickness(
        nonuniform_state
    )
    captured_scalars: list[jax.Array] = []

    def capture_transport(scalar, aux_state, incumbent_horizontal_tendency):
        del aux_state
        captured_scalars.append(scalar)
        return incumbent_horizontal_tendency

    monkeypatch.setattr(
        equation,
        "horizontal_semilagrangian_theta_transport",
        capture_transport,
    )

    tendency = equation.temperature_tendency_potential_temperature_form(
        nonuniform_state,
        aux_state,
    )

    diagnosed_surface_pressure = jnp.exp(
        coords.horizontal.to_nodal(nonuniform_state.log_surface_pressure)
    )
    expected_layer_pressure_thickness = (
        jnp.asarray(coords.vertical.layer_thickness, dtype=surface_pressure.dtype)[
            :, jnp.newaxis, jnp.newaxis
        ]
        * diagnosed_surface_pressure
    )
    assert bool(jnp.isfinite(tendency).all())
    assert bool(jnp.all(layer_pressure_thickness > 0.0))
    np.testing.assert_allclose(
        layer_pressure_thickness,
        expected_layer_pressure_thickness,
        rtol=1.0e-6,
    )
    np.testing.assert_allclose(
        captured_scalars[-1],
        expected_layer_pressure_thickness * dse_anomaly,
        rtol=1.0e-6,
    )


def test_layer_mass_dse_invalid_pressure_thickness_falls_back_to_dse_hsl(
    monkeypatch,
):
    """Unsafe layer mass diagnostics reproduce the incumbent DSE-HSL tendency."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    common_kwargs = {
        "reference_temperature": reference_temperature,
        "orography": jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        "coords": coords,
        "physics_specs": cast(Any, physics_specs),
        "include_vertical_advection": False,
        "temperature_tendency_formulation": (
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        "use_horizontal_semilagrangian_theta_transport": True,
        "use_midpoint_semilagrangian_theta_departure": True,
        "use_dry_static_energy_hsl_transport": True,
        "horizontal_semilagrangian_theta_transport_step": _nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    }
    incumbent_equation = primitive_equations.PrimitiveEquations(**common_kwargs)
    candidate_equation = primitive_equations.PrimitiveEquations(
        **common_kwargs,
        use_layer_mass_weighted_dse_hsl_transport=True,
    )
    aux_state = primitive_equations.compute_diagnostic_state_sigma(state, coords)
    expected_tendency = (
        incumbent_equation.temperature_tendency_potential_temperature_form(
            state,
            aux_state,
        )
    )

    def nonfinite_layer_pressure_thickness(state):
        del state
        return jnp.full(coords.nodal_shape, jnp.nan, dtype=jnp.float32)

    monkeypatch.setattr(
        candidate_equation,
        "nodal_sigma_layer_pressure_thickness",
        nonfinite_layer_pressure_thickness,
    )

    actual_tendency = (
        candidate_equation.temperature_tendency_potential_temperature_form(
            state,
            aux_state,
        )
    )

    np.testing.assert_array_equal(actual_tendency, expected_tendency)


def test_pressure_ramped_vertical_dse_weight_endpoints():
    """The fixed vertical-DSE ramp is zero through 24h and full by 72h."""
    physics_specs = units.SimUnits.from_si()
    hour = _nondimensionalize_seconds(physics_specs, SECONDS_PER_HOUR)
    sim_time = jnp.asarray([0.0, 24.0, 48.0, 72.0], dtype=jnp.float32) * hour

    weights = primitive_equations._pressure_ramped_vertical_dse_increment_weight(
        sim_time,
        physics_specs,
    )

    weights_np = np.asarray(weights)
    np.testing.assert_allclose(weights_np[[0, 1, 3]], [0.0, 0.0, 1.0])
    assert 0.0 < weights_np[2] < 1.0


def test_pressure_ramped_vertical_dse_noop_before_ramp():
    """At 24h and earlier, the selected tendency matches the WTG incumbent path."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    hour = _nondimensionalize_seconds(physics_specs, SECONDS_PER_HOUR)
    timed_state = _primitive_equation_state(
        vorticity=state.vorticity,
        divergence=state.divergence,
        temperature_variation=state.temperature_variation,
        log_surface_pressure=state.log_surface_pressure,
        tracers=state.tracers,
        sim_time=jnp.asarray(24.0 * hour, dtype=jnp.float32),
    )
    common_kwargs = {
        "reference_temperature": reference_temperature,
        "orography": jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        "coords": coords,
        "physics_specs": cast(Any, physics_specs),
        "include_vertical_advection": True,
        "temperature_tendency_formulation": (
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        "use_horizontal_semilagrangian_theta_transport": True,
        "use_midpoint_semilagrangian_theta_departure": True,
        "use_dry_static_energy_hsl_transport": True,
        "use_layer_mass_weighted_dse_hsl_transport": True,
        "horizontal_semilagrangian_theta_transport_step": _nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    }
    incumbent_equation = primitive_equations.PrimitiveEquations(**common_kwargs)
    candidate_equation = primitive_equations.PrimitiveEquations(
        **common_kwargs,
        use_pressure_ramped_vertical_dse_increment=True,
    )
    aux_state = primitive_equations.compute_diagnostic_state_sigma(
        timed_state,
        coords,
    )

    incumbent_tendency = (
        incumbent_equation.temperature_tendency_potential_temperature_form(
            timed_state,
            aux_state,
        )
    )
    candidate_tendency = (
        candidate_equation.temperature_tendency_potential_temperature_form(
            timed_state,
            aux_state,
        )
    )

    np.testing.assert_array_equal(candidate_tendency, incumbent_tendency)


def test_pressure_ramped_vertical_dse_missing_time_falls_back(monkeypatch):
    """Unavailable model time returns the incumbent tendency without candidate math."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    equation = primitive_equations.PrimitiveEquations(
        reference_temperature,
        jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        coords,
        cast(Any, physics_specs),
        include_vertical_advection=True,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        use_dry_static_energy_hsl_transport=True,
        use_layer_mass_weighted_dse_hsl_transport=True,
        use_pressure_ramped_vertical_dse_increment=True,
        horizontal_semilagrangian_theta_transport_step=_nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    )
    aux_state = primitive_equations.compute_diagnostic_state_sigma(state, coords)
    incumbent_tendency = jnp.ones(coords.modal_shape, dtype=jnp.float32)

    def fail_vertical_tendency(*args, **kwargs):
        del args, kwargs
        raise AssertionError("candidate vertical tendency should not run")

    monkeypatch.setattr(equation, "_vertical_tendency", fail_vertical_tendency)

    actual_tendency = (
        equation.pressure_ramped_vertical_dse_increment_temperature_tendency(
            state=state,
            aux_state=aux_state,
            incumbent_temperature_tendency=incumbent_tendency,
            dry_static_energy_anomaly=jnp.full(coords.nodal_shape, jnp.nan),
            geopotential=jnp.full(coords.nodal_shape, jnp.nan),
            theta_vertical_temperature_tendency=jnp.zeros(
                coords.nodal_shape,
                dtype=jnp.float32,
            ),
            valid_layer_pressure_thickness=jnp.zeros(
                coords.nodal_shape,
                dtype=bool,
            ),
            finite_theta_diagnostics=jnp.asarray(False),
            finite_dse_diagnostics=jnp.asarray(False),
            finite_mass_dse_diagnostics=jnp.asarray(False),
        )
    )

    np.testing.assert_array_equal(actual_tendency, incumbent_tendency)


def test_pressure_ramped_vertical_dse_caps_increment(monkeypatch):
    """A finite vertical-DSE candidate is capped by the per-inner-step limit."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    hour = _nondimensionalize_seconds(physics_specs, SECONDS_PER_HOUR)
    timed_state = _primitive_equation_state(
        vorticity=state.vorticity,
        divergence=state.divergence,
        temperature_variation=state.temperature_variation,
        log_surface_pressure=state.log_surface_pressure,
        tracers=state.tracers,
        sim_time=jnp.asarray(72.0 * hour, dtype=jnp.float32),
    )
    step_seconds = _nondimensionalize_seconds(physics_specs, 900.0)
    equation = primitive_equations.PrimitiveEquations(
        reference_temperature,
        jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        coords,
        cast(Any, physics_specs),
        include_vertical_advection=True,
        temperature_tendency_formulation=(
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        use_dry_static_energy_hsl_transport=True,
        use_layer_mass_weighted_dse_hsl_transport=True,
        use_pressure_ramped_vertical_dse_increment=True,
        horizontal_semilagrangian_theta_transport_step=step_seconds,
    )
    aux_state = primitive_equations.compute_diagnostic_state_sigma(
        timed_state,
        coords,
    )
    incumbent_tendency = jnp.zeros(coords.modal_shape, dtype=jnp.float32)

    def large_vertical_tendency(unused_sigma_dot, scalar):
        del unused_sigma_dot
        return jnp.ones_like(scalar) * physics_specs.Cp * 10_000.0

    monkeypatch.setattr(equation, "_vertical_tendency", large_vertical_tendency)

    capped_tendency = (
        equation.pressure_ramped_vertical_dse_increment_temperature_tendency(
            state=timed_state,
            aux_state=aux_state,
            incumbent_temperature_tendency=incumbent_tendency,
            dry_static_energy_anomaly=jnp.ones(coords.nodal_shape, dtype=jnp.float32),
            geopotential=jnp.zeros(coords.nodal_shape, dtype=jnp.float32),
            theta_vertical_temperature_tendency=jnp.zeros(
                coords.nodal_shape,
                dtype=jnp.float32,
            ),
            valid_layer_pressure_thickness=jnp.ones(
                coords.nodal_shape,
                dtype=bool,
            ),
            finite_theta_diagnostics=jnp.asarray(True),
            finite_dse_diagnostics=jnp.asarray(True),
            finite_mass_dse_diagnostics=jnp.asarray(True),
        )
    )
    nodal_tendency = coords.horizontal.to_nodal(capped_tendency)
    max_tendency = (
        primitive_equations.PRESSURE_RAMPED_VERTICAL_DSE_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN
        * _unit_factor(physics_specs, "kelvin")
        / step_seconds
    )

    assert bool(jnp.isfinite(nodal_tendency).all())
    assert float(jnp.max(jnp.abs(nodal_tendency))) <= max_tendency * 1.0001


def test_dse_hsl_leaves_non_temperature_explicit_tendencies_unchanged():
    """DSE-HSL changes only the horizontal thermal transport hook."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    common_kwargs = {
        "reference_temperature": reference_temperature,
        "orography": jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        "coords": coords,
        "physics_specs": cast(Any, physics_specs),
        "include_vertical_advection": False,
        "temperature_tendency_formulation": (
            primitive_equations.TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE
        ),
        "use_horizontal_semilagrangian_theta_transport": True,
        "use_midpoint_semilagrangian_theta_departure": True,
        "horizontal_semilagrangian_theta_transport_step": _nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
    }
    incumbent_equation = primitive_equations.PrimitiveEquations(**common_kwargs)
    candidate_equation = primitive_equations.PrimitiveEquations(
        **common_kwargs,
        use_dry_static_energy_hsl_transport=True,
    )

    incumbent_tendency = incumbent_equation.explicit_terms(state)
    candidate_tendency = candidate_equation.explicit_terms(state)

    np.testing.assert_array_equal(
        candidate_tendency.vorticity, incumbent_tendency.vorticity
    )
    np.testing.assert_array_equal(
        candidate_tendency.divergence, incumbent_tendency.divergence
    )
    np.testing.assert_array_equal(
        candidate_tendency.log_surface_pressure,
        incumbent_tendency.log_surface_pressure,
    )
    assert candidate_tendency.tracers == incumbent_tendency.tracers == {}
    assert bool(jnp.isfinite(candidate_tendency.temperature_variation).all())


def test_ocean_bulk_shf_drives_lowest_temperature_toward_anchor_only():
    """The opt-in flux changes only the lowest-layer temperature tendency."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    current_temperature = (
        coords.horizontal.to_nodal(state.temperature_variation)[-1]
        + reference_temperature[-1]
    )
    forcing = _OceanBulkSensibleHeatFluxForcingSigma(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        ocean_weight=jnp.ones(coords.horizontal.nodal_shape, dtype=jnp.float32),
        temperature_anchor=current_temperature + 4.0,
        step_seconds=_nondimensionalize_seconds(physics_specs, 900.0),
    )

    tendency = forcing.explicit_terms(state)
    nodal_temperature_tendency = coords.horizontal.to_nodal(
        tendency.temperature_variation
    )

    np.testing.assert_array_equal(tendency.vorticity, jnp.zeros_like(state.vorticity))
    np.testing.assert_array_equal(tendency.divergence, jnp.zeros_like(state.divergence))
    np.testing.assert_array_equal(
        tendency.log_surface_pressure,
        jnp.zeros_like(state.log_surface_pressure),
    )
    assert tendency.tracers == {}
    np.testing.assert_allclose(nodal_temperature_tendency[0], 0.0, atol=1e-7)
    assert float(jnp.min(nodal_temperature_tendency[-1])) > 0.0

    equilibrium_forcing = _OceanBulkSensibleHeatFluxForcingSigma(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        ocean_weight=jnp.ones(coords.horizontal.nodal_shape, dtype=jnp.float32),
        temperature_anchor=current_temperature,
        step_seconds=_nondimensionalize_seconds(physics_specs, 900.0),
    )
    equilibrium_tendency = equilibrium_forcing.explicit_terms(state)
    np.testing.assert_allclose(
        equilibrium_tendency.temperature_variation,
        0.0,
        atol=1e-7,
    )


def test_ocean_bulk_shf_caps_step_increment_and_finite_falls_back():
    """Strong forcing is capped, and nonfinite anchors add no tendency."""
    coords, physics_specs, reference_temperature, state = _ocean_bulk_shf_test_setup()
    current_temperature = (
        coords.horizontal.to_nodal(state.temperature_variation)[-1]
        + reference_temperature[-1]
    )
    step_seconds = _nondimensionalize_seconds(physics_specs, 900.0)
    forcing = _OceanBulkSensibleHeatFluxForcingSigma(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        ocean_weight=jnp.ones(coords.horizontal.nodal_shape, dtype=jnp.float32),
        temperature_anchor=current_temperature + 10_000.0,
        step_seconds=step_seconds,
    )

    tendency = forcing.explicit_terms(state)
    nodal_temperature_tendency = coords.horizontal.to_nodal(
        tendency.temperature_variation
    )
    max_increment = (
        _OCEAN_BULK_SHF_MAX_STEP_TEMPERATURE_INCREMENT_KELVIN
        * _unit_factor(physics_specs, "kelvin")
    )
    assert float(jnp.max(jnp.abs(nodal_temperature_tendency[-1] * step_seconds))) <= (
        max_increment + 1.0e-6
    )

    invalid_forcing = _OceanBulkSensibleHeatFluxForcingSigma(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        ocean_weight=jnp.ones(coords.horizontal.nodal_shape, dtype=jnp.float32),
        temperature_anchor=(current_temperature + 4.0).at[0, 0].set(jnp.nan),
        step_seconds=step_seconds,
    )

    invalid_tendency = invalid_forcing.explicit_terms(state)

    np.testing.assert_array_equal(
        invalid_tendency.temperature_variation,
        jnp.zeros_like(invalid_tendency.temperature_variation),
    )


def test_ocean_bulk_shf_anchor_uses_lead_zero_t2m_before_lowest_layer():
    """Anchor construction uses initial T2m and rejects nonfinite lead-zero fields."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1), lead_steps=(0,)
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    single_state = WeatherState(
        values=forecast_input.initial_state.values[0],
        variables=forecast_input.initial_state.variables,
    )
    dinosaur_state = weather_state_to_dinosaur_state(
        single_state,
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=False,
    )

    anchor = _ocean_bulk_sensible_heat_flux_temperature_anchor(
        single_state,
        dinosaur_state=dinosaur_state,
        coords=grid.coords,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
    )

    expected_anchor = _to_dinosaur_latitude_order(
        single_state.select(("2m_temperature",)).values[0]
        * _unit_factor(physics_specs, "kelvin"),
        grid.latitude_reversed,
    )
    np.testing.assert_array_equal(anchor, expected_anchor)

    bad_temperature_index = int(single_state.variable_indices(("2m_temperature",))[0])
    invalid_state = WeatherState(
        values=single_state.values.at[bad_temperature_index, 0, 0].set(jnp.nan),
        variables=single_state.variables,
    )

    assert (
        _ocean_bulk_sensible_heat_flux_temperature_anchor(
            invalid_state,
            dinosaur_state=dinosaur_state,
            coords=grid.coords,
            latitude_reversed=grid.latitude_reversed,
            physics_specs=physics_specs,
            reference_temperature=reference_temperature,
        )
        is None
    )


def test_ocean_bulk_shf_composes_rollout_not_dfi(monkeypatch):
    """The ocean SHF term leaves the incumbent DFI equation path unchanged."""
    ocean_compose_calls = []

    def capture_ocean_composition(**kwargs):
        ocean_compose_calls.append(kwargs)
        return kwargs["equation"]

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        del equation, ode_solver, filters, time_span, cutoff_period, dt
        return lambda dinosaur_state: dinosaur_state

    def fake_land_sea_fraction(*, longitude, latitude, initial_time):
        del initial_time
        return jnp.zeros((longitude.size, latitude.size), dtype=jnp.float32)

    monkeypatch.setattr(
        dinosaur_adapter,
        "_compose_ocean_bulk_sensible_heat_flux_equation",
        capture_ocean_composition,
    )
    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    monkeypatch.setattr(
        dinosaur_adapter,
        "_load_land_sea_fraction_for_grid",
        fake_land_sea_fraction,
    )
    model = replace(
        ocean_bulk_sensible_heat_flux_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=("2m_temperature",),
        apply_spectral_filter=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1), lead_steps=(0,)
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == ("2m_temperature",)
    assert len(ocean_compose_calls) == 1


def test_hsl_theta_non_jit_forecast_smoke_is_finite(monkeypatch):
    """The registered candidate runs a small non-JIT finite forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        del equation, ode_solver, filters, time_span, cutoff_period, dt
        return lambda dinosaur_state: dinosaur_state

    def fake_land_sea_fraction(*, longitude, latitude, initial_time):
        del initial_time
        return jnp.zeros((longitude.size, latitude.size), dtype=jnp.float32)

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    monkeypatch.setattr(
        dinosaur_adapter,
        "_load_land_sea_fraction_for_grid",
        fake_land_sea_fraction,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        horizontal_semilagrangian_theta_transport_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        apply_spectral_filter=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert model.name == "dino_hsl_theta"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())


def test_hsl2_theta_non_jit_forecast_smoke_is_finite(monkeypatch):
    """The midpoint departure candidate runs a small non-JIT finite forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        del equation, ode_solver, filters, time_span, cutoff_period, dt
        return lambda dinosaur_state: dinosaur_state

    def fake_land_sea_fraction(*, longitude, latitude, initial_time):
        del initial_time
        return jnp.zeros((longitude.size, latitude.size), dtype=jnp.float32)

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    monkeypatch.setattr(
        dinosaur_adapter,
        "_load_land_sea_fraction_for_grid",
        fake_land_sea_fraction,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        midpoint_semilagrangian_theta_departure_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        apply_spectral_filter=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert model.name == "dino_hsl2_theta"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())


def test_dse_hsl_non_jit_forecast_smoke_is_finite(monkeypatch):
    """The DSE-HSL candidate runs a small non-JIT finite forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        del equation, ode_solver, filters, time_span, cutoff_period, dt
        return lambda dinosaur_state: dinosaur_state

    def fake_land_sea_fraction(*, longitude, latitude, initial_time):
        del initial_time
        return jnp.zeros((longitude.size, latitude.size), dtype=jnp.float32)

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    monkeypatch.setattr(
        dinosaur_adapter,
        "_load_land_sea_fraction_for_grid",
        fake_land_sea_fraction,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        dry_static_energy_hsl_transport_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        apply_spectral_filter=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert model.name == "dino_hsl2_theta_dse_hsl"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())


def test_tropical_wtg_mass_dse_non_jit_forecast_smoke_is_finite(monkeypatch):
    """The WTG mass-DSE candidate runs a small non-JIT finite forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        del equation, ode_solver, filters, time_span, cutoff_period, dt
        return lambda dinosaur_state: dinosaur_state

    def fake_land_sea_fraction(*, longitude, latitude, initial_time):
        del initial_time
        return jnp.zeros((longitude.size, latitude.size), dtype=jnp.float32)

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    monkeypatch.setattr(
        dinosaur_adapter,
        "_load_land_sea_fraction_for_grid",
        fake_land_sea_fraction,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        tropical_wtg_mass_dse_relaxation_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        apply_spectral_filter=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert model.name == "dino_hsl2_mass_dse_wtg"
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())


def test_pressure_ramped_vertical_dse_non_jit_forecast_smoke_is_finite(monkeypatch):
    """The pressure-ramped vertical-DSE candidate runs a small finite forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        del equation, ode_solver, filters, time_span, cutoff_period, dt
        return lambda dinosaur_state: dinosaur_state

    def fake_land_sea_fraction(*, longitude, latitude, initial_time):
        del initial_time
        return jnp.zeros((longitude.size, latitude.size), dtype=jnp.float32)

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    monkeypatch.setattr(
        dinosaur_adapter,
        "_load_land_sea_fraction_for_grid",
        fake_land_sea_fraction,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        pressure_ramped_vertical_dse_wtg_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        apply_spectral_filter=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert model.name == "dino_hsl2_mass_dse_wtg_vdse_ramp"
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert model.use_pressure_ramped_vertical_dse_increment
    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())


def test_analysis_offset_hs_eq_trajectory_uses_offset_for_rollout_and_dfi(
    monkeypatch,
):
    """The candidate passes one initial-state offset into rollout and DFI forcing."""
    compose_calls = []
    real_compose_equations = time_integration.compose_equations

    def capture_compose_equations(equations):
        compose_calls.append(tuple(equations))
        return real_compose_equations(equations)

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "compose_equations",
        capture_compose_equations,
    )
    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1), lead_steps=(0,)
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    dinosaur_state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=False,
        use_log_pressure_initialization=True,
        use_hydrostatic_temperature_initialization=True,
        use_layer_mean_hydrostatic_temperature_initialization=True,
    )
    model = replace(
        analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        apply_spectral_filter=False,
        jit_forecast=False,
    )
    trajectory_fn = model._trajectory_function(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        inner_steps=1,
        output_count=1,
        use_humidity_in_dynamics=False,
    )

    trajectory_fn(dinosaur_state)

    assert len(compose_calls) == 2
    for primitive_equation, forcing in compose_calls:
        assert isinstance(primitive_equation, primitive_equations.PrimitiveEquations)
        assert isinstance(forcing, _TracerSafeHeldSuarezForcingSigma)
        assert forcing.equilibrium_temperature_offset is not None
        assert forcing.equilibrium_temperature_offset.shape == grid.coords.nodal_shape
        assert bool(jnp.isfinite(forcing.equilibrium_temperature_offset).all())


def test_trajectory_function_matches_direct_dinosaur_package_call():
    """The wrapper trajectory uses the same Dinosaur calls as a direct setup."""
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        include_vertical_advection=False,
        use_humidity_in_dynamics=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0, 1, 2))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=model.spectral_wavenumbers,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=model.reference_temperature_kelvin,
    )
    dinosaur_state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=(250, 750),
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )

    wrapped_fn = model._trajectory_function(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        inner_steps=1,
        output_count=3,
        use_humidity_in_dynamics=False,
    )
    _, wrapped_trajectory = wrapped_fn(dinosaur_state)

    orography = jnp.zeros(grid.coords.horizontal.modal_shape, dtype=jnp.float32)
    equation = primitive_equations.PrimitiveEquations(
        reference_temperature,
        orography,
        grid.coords,
        cast(Any, physics_specs),
        include_vertical_advection=False,
    )
    step_seconds = _nondimensionalize_seconds(
        physics_specs,
        model.inner_step_seconds,
    )
    step_fn = time_integration.imex_rk_sil3(equation, step_seconds)
    step_fn = time_integration.step_with_filters(
        step_fn,
        [
            _horizontal_diffusion_step_filter(
                coords=grid.coords,
                physics_specs=physics_specs,
                step_seconds=step_seconds,
                tau_seconds=model.horizontal_diffusion_tau_seconds,
                order=model.horizontal_diffusion_order,
            )
        ],
    )
    direct_fn = time_integration.trajectory_from_step(
        step_fn,
        outer_steps=3,
        inner_steps=1,
        start_with_input=True,
    )
    _, direct_trajectory = direct_fn(dinosaur_state)

    for actual, expected in zip(
        jax.tree_util.tree_leaves(wrapped_trajectory),
        jax.tree_util.tree_leaves(direct_trajectory),
        strict=True,
    ):
        np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-6)


def test_trajectory_function_sets_up_digital_filter_initialization(monkeypatch):
    """DFI uses the forecast equation, stepper, filters, and nondimensional units."""
    dfi_calls = []
    initialized_states = []

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        dfi_calls.append(
            {
                "equation": equation,
                "ode_solver": ode_solver,
                "filters": filters,
                "time_span": time_span,
                "cutoff_period": cutoff_period,
                "dt": dt,
            }
        )

        def initialize_state(dinosaur_state):
            initialized_state = _primitive_equation_state(
                vorticity=dinosaur_state.vorticity,
                divergence=dinosaur_state.divergence,
                temperature_variation=dinosaur_state.temperature_variation
                + jnp.float32(0.25),
                log_surface_pressure=dinosaur_state.log_surface_pressure,
                tracers=dinosaur_state.tracers,
            )
            initialized_states.append(initialized_state)
            return initialized_state

        return initialize_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        include_vertical_advection=False,
        use_humidity_in_dynamics=False,
        apply_digital_filter_initialization=True,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0, 1, 2))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=model.spectral_wavenumbers,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=model.reference_temperature_kelvin,
    )
    dinosaur_state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=(250, 750),
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )

    wrapped_fn = model._trajectory_function(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        inner_steps=1,
        output_count=1,
        use_humidity_in_dynamics=False,
    )
    _, wrapped_trajectory = wrapped_fn(dinosaur_state)

    step_seconds = _nondimensionalize_seconds(
        physics_specs,
        model.inner_step_seconds,
    )
    filters = [
        _horizontal_diffusion_step_filter(
            coords=grid.coords,
            physics_specs=physics_specs,
            step_seconds=step_seconds,
            tau_seconds=model.horizontal_diffusion_tau_seconds,
            order=model.horizontal_diffusion_order,
        )
    ]
    first_wrapped_state = jax.tree_util.tree_map(
        lambda trajectory_leaf: trajectory_leaf[0],
        wrapped_trajectory,
    )

    assert len(dfi_calls) == 1
    call = dfi_calls[0]
    assert isinstance(call["equation"], primitive_equations.PrimitiveEquations)
    assert call["ode_solver"] is time_integration.imex_rk_sil3
    assert call["dt"] == step_seconds
    assert call["time_span"] == _nondimensionalize_seconds(
        physics_specs,
        model.digital_filter_time_span_seconds,
    )
    assert call["cutoff_period"] == _nondimensionalize_seconds(
        physics_specs,
        model.digital_filter_cutoff_seconds,
    )
    assert len(call["filters"]) == len(filters) == 1
    _assert_pytree_allclose(
        call["filters"][0](dinosaur_state, dinosaur_state),
        filters[0](dinosaur_state, dinosaur_state),
    )
    assert len(initialized_states) == 1
    _assert_pytree_allclose(first_wrapped_state, initialized_states[0])


def test_trajectory_function_threads_offcentered_solver_to_rollout_and_dfi(
    monkeypatch,
):
    """The offcentered candidate uses the same epsilon-bound solver in DFI."""
    solver_calls = []
    dfi_calls = []

    def capture_imex_rk_sil3(
        equation,
        time_step,
        *,
        implicit_offcentering=0.0,
    ):
        solver_calls.append(
            {
                "equation": equation,
                "time_step": time_step,
                "implicit_offcentering": implicit_offcentering,
            }
        )
        return lambda state: state

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        dfi_calls.append(
            {
                "equation": equation,
                "ode_solver": ode_solver,
                "filters": tuple(filters),
                "time_span": time_span,
                "cutoff_period": cutoff_period,
                "dt": dt,
            }
        )
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "imex_rk_sil3",
        capture_imex_rk_sil3,
    )
    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    incumbent = replace(
        theta_mean_recenter_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        include_vertical_advection=False,
        jit_forecast=False,
    )
    candidate = replace(
        semi_implicit_offcenter_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        include_vertical_advection=False,
        jit_forecast=False,
    )

    for model in (incumbent, candidate):
        model._trajectory_function(
            coords=grid.coords,
            physics_specs=physics_specs,
            reference_temperature=reference_temperature,
            inner_steps=1,
            output_count=1,
            use_humidity_in_dynamics=False,
        )

    assert [call["implicit_offcentering"] for call in solver_calls] == [
        0.0,
        DEFAULT_SEMI_IMPLICIT_OFFCENTERING,
    ]
    assert dfi_calls[0]["ode_solver"] is time_integration.imex_rk_sil3
    candidate_ode_solver = dfi_calls[1]["ode_solver"]
    assert candidate_ode_solver.func is time_integration.imex_rk_sil3
    assert candidate_ode_solver.keywords == {
        "implicit_offcentering": DEFAULT_SEMI_IMPLICIT_OFFCENTERING
    }


def test_trajectory_function_splits_rollout_and_dfi_coriolis_physics(monkeypatch):
    """Exact-Coriolis rollout uses zero Ω while DFI keeps normal physics."""
    primitive_calls = []
    rollout_filter_calls = []
    dfi_calls = []
    real_primitive_equation = dinosaur_adapter._primitive_equation
    real_step_with_filters = time_integration.step_with_filters

    def capture_primitive_equation(*args, **kwargs):
        primitive_calls.append(kwargs["physics_specs"])
        return real_primitive_equation(*args, **kwargs)

    def capture_step_with_filters(step_fn, filters):
        rollout_filter_calls.append(tuple(filters))
        return real_step_with_filters(step_fn, filters)

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        dfi_calls.append(
            {
                "equation": equation,
                "ode_solver": ode_solver,
                "filters": tuple(filters),
                "time_span": time_span,
                "cutoff_period": cutoff_period,
                "dt": dt,
            }
        )
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        dinosaur_adapter,
        "_primitive_equation",
        capture_primitive_equation,
    )
    monkeypatch.setattr(
        time_integration,
        "step_with_filters",
        capture_step_with_filters,
    )
    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    model = replace(
        coriolis_split_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        include_vertical_advection=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()

    model._trajectory_function(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=_reference_temperature(
            layer_count=2,
            temperature_kelvin=model.reference_temperature_kelvin,
        ),
        inner_steps=1,
        output_count=1,
        use_humidity_in_dynamics=False,
    )

    assert len(primitive_calls) == 2
    rollout_physics_specs, dfi_physics_specs = primitive_calls
    assert rollout_physics_specs.angular_velocity == 0.0
    assert dfi_physics_specs.angular_velocity == physics_specs.angular_velocity
    for field_name in physics_specs.__dataclass_fields__:
        if field_name == "angular_velocity":
            continue
        assert getattr(rollout_physics_specs, field_name) == getattr(
            physics_specs,
            field_name,
        )
    assert len(rollout_filter_calls) == 1
    assert len(rollout_filter_calls[0]) == 2
    assert rollout_filter_calls[0][-1].__name__ == "exact_coriolis_rotation_filter"
    assert len(dfi_calls) == 1
    assert len(dfi_calls[0]["filters"]) == 1
    assert dfi_calls[0]["ode_solver"] is time_integration.imex_rk_sil3


def test_trajectory_function_uses_strang_rollout_and_unsplit_dfi(monkeypatch):
    """Strang rollout wraps diffusion-filtered zero-Ω dynamics and normal-Ω DFI."""
    primitive_calls = []
    rollout_filter_calls = []
    symmetric_step_calls = []
    dfi_calls = []
    real_primitive_equation = dinosaur_adapter._primitive_equation
    real_step_with_filters = time_integration.step_with_filters
    real_symmetric_step = dinosaur_adapter._symmetric_exact_coriolis_rotation_step

    def capture_primitive_equation(*args, **kwargs):
        primitive_calls.append(kwargs["physics_specs"])
        return real_primitive_equation(*args, **kwargs)

    def capture_step_with_filters(step_fn, filters):
        rollout_filter_calls.append(tuple(filters))
        return real_step_with_filters(step_fn, filters)

    def capture_symmetric_step(step_fn, *, coords, physics_specs, step_seconds):
        symmetric_step_calls.append(
            {
                "coords": coords,
                "physics_specs": physics_specs,
                "step_seconds": step_seconds,
            }
        )
        return real_symmetric_step(
            step_fn,
            coords=coords,
            physics_specs=physics_specs,
            step_seconds=step_seconds,
        )

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        dfi_calls.append(
            {
                "equation": equation,
                "ode_solver": ode_solver,
                "filters": tuple(filters),
                "time_span": time_span,
                "cutoff_period": cutoff_period,
                "dt": dt,
            }
        )
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        dinosaur_adapter,
        "_primitive_equation",
        capture_primitive_equation,
    )
    monkeypatch.setattr(
        time_integration,
        "step_with_filters",
        capture_step_with_filters,
    )
    monkeypatch.setattr(
        dinosaur_adapter,
        "_symmetric_exact_coriolis_rotation_step",
        capture_symmetric_step,
    )
    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    model = replace(
        coriolis_strang_split_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        include_vertical_advection=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    step_seconds = _nondimensionalize_seconds(
        physics_specs,
        model.inner_step_seconds,
    )

    model._trajectory_function(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=_reference_temperature(
            layer_count=2,
            temperature_kelvin=model.reference_temperature_kelvin,
        ),
        inner_steps=1,
        output_count=1,
        use_humidity_in_dynamics=False,
    )

    assert len(primitive_calls) == 2
    rollout_physics_specs, dfi_physics_specs = primitive_calls
    assert rollout_physics_specs.angular_velocity == 0.0
    assert dfi_physics_specs.angular_velocity == physics_specs.angular_velocity
    assert len(rollout_filter_calls) == 1
    assert len(rollout_filter_calls[0]) == 1
    assert rollout_filter_calls[0][0].__name__ != "exact_coriolis_rotation_filter"
    assert len(symmetric_step_calls) == 1
    assert symmetric_step_calls[0]["coords"] is grid.coords
    assert symmetric_step_calls[0]["physics_specs"] is physics_specs
    assert symmetric_step_calls[0]["step_seconds"] == step_seconds
    assert len(dfi_calls) == 1
    assert len(dfi_calls[0]["filters"]) == 1
    assert dfi_calls[0]["ode_solver"] is time_integration.imex_rk_sil3


def test_trajectory_function_applies_theta_recenter_to_rollout_only(monkeypatch):
    """The theta recentering wrapper is excluded from time-reversed DFI filters."""
    rollout_filter_calls = []
    dfi_calls = []
    real_step_with_filters = time_integration.step_with_filters

    def capture_step_with_filters(step_fn, filters):
        rollout_filter_calls.append(tuple(filters))
        return real_step_with_filters(step_fn, filters)

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        dfi_calls.append(tuple(filters))
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "step_with_filters",
        capture_step_with_filters,
    )
    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    model = replace(
        theta_mean_recenter_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        include_vertical_advection=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()

    model._trajectory_function(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=_reference_temperature(
            layer_count=2,
            temperature_kelvin=model.reference_temperature_kelvin,
        ),
        inner_steps=1,
        output_count=1,
        use_humidity_in_dynamics=False,
    )

    assert len(rollout_filter_calls) == 1
    rollout_filter_names = [filter_fn.__name__ for filter_fn in rollout_filter_calls[0]]
    assert rollout_filter_names[-1] == "theta_layer_mean_recenter_filter"
    assert len(rollout_filter_names) == 2
    assert len(dfi_calls) == 1
    assert [filter_fn.__name__ for filter_fn in dfi_calls[0]] == rollout_filter_names[
        :-1
    ]


def test_trajectory_function_applies_tropical_wtg_to_rollout_only(monkeypatch):
    """The WTG relaxation wrapper is excluded from time-reversed DFI filters."""
    rollout_filter_calls = []
    dfi_calls = []
    real_step_with_filters = time_integration.step_with_filters

    def capture_step_with_filters(step_fn, filters):
        rollout_filter_calls.append(tuple(filters))
        return real_step_with_filters(step_fn, filters)

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        dfi_calls.append(tuple(filters))
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "step_with_filters",
        capture_step_with_filters,
    )
    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    coords, physics_specs, _, dinosaur_state = _synthetic_wtg_mass_dse_state()
    model = replace(
        tropical_wtg_mass_dse_relaxation_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        include_vertical_advection=False,
        jit_forecast=False,
    )

    trajectory_fn = model._trajectory_function(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=_reference_temperature(
            layer_count=3,
            temperature_kelvin=model.reference_temperature_kelvin,
        ),
        inner_steps=1,
        output_count=1,
        use_humidity_in_dynamics=False,
    )
    trajectory_fn(dinosaur_state)

    assert len(rollout_filter_calls) == 1
    rollout_filter_names = [filter_fn.__name__ for filter_fn in rollout_filter_calls[0]]
    assert rollout_filter_names[-2:] == [
        "tropical_wtg_mass_dse_relaxation_filter",
        "theta_layer_mean_recenter_filter",
    ]
    assert len(dfi_calls) == 1
    assert "tropical_wtg_mass_dse_relaxation_filter" not in [
        filter_fn.__name__ for filter_fn in dfi_calls[0]
    ]
    assert "theta_layer_mean_recenter_filter" not in [
        filter_fn.__name__ for filter_fn in dfi_calls[0]
    ]


def test_trajectory_function_keeps_normal_incumbent_physics_when_split_disabled(
    monkeypatch,
):
    """Without the split flag, rollout and DFI share the normal incumbent setup."""
    primitive_calls = []
    rollout_filter_calls = []
    dfi_calls = []
    real_primitive_equation = dinosaur_adapter._primitive_equation
    real_step_with_filters = time_integration.step_with_filters

    def capture_primitive_equation(*args, **kwargs):
        primitive_calls.append(kwargs["physics_specs"])
        return real_primitive_equation(*args, **kwargs)

    def capture_step_with_filters(step_fn, filters):
        rollout_filter_calls.append(tuple(filters))
        return real_step_with_filters(step_fn, filters)

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        dfi_calls.append(tuple(filters))
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        dinosaur_adapter,
        "_primitive_equation",
        capture_primitive_equation,
    )
    monkeypatch.setattr(
        time_integration,
        "step_with_filters",
        capture_step_with_filters,
    )
    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    model = replace(
        layer_mean_hydrostatic_temperature_initialization_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        include_vertical_advection=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()

    model._trajectory_function(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=_reference_temperature(
            layer_count=2,
            temperature_kelvin=model.reference_temperature_kelvin,
        ),
        inner_steps=1,
        output_count=1,
        use_humidity_in_dynamics=False,
    )

    assert len(primitive_calls) == 1
    assert primitive_calls[0].angular_velocity == physics_specs.angular_velocity
    assert len(rollout_filter_calls) == 1
    assert len(rollout_filter_calls[0]) == 1
    assert len(dfi_calls) == 1
    assert len(dfi_calls[0]) == 1


def _synthetic_coriolis_split_state():
    physics_specs = units.SimUnits.from_si()
    horizontal_grid = spherical_harmonic.Grid(
        longitude_wavenumbers=3,
        total_wavenumbers=5,
        longitude_nodes=8,
        latitude_nodes=5,
        latitude_spacing="equiangular",
        radius=physics_specs.radius,
    )
    coords = coordinate_systems.CoordinateSystem(
        horizontal_grid,
        sigma_coordinates.SigmaCoordinates.equidistant(2),
    )
    state_shape = (coords.vertical.layers, *coords.horizontal.modal_shape)
    vorticity = (
        jnp.zeros(state_shape, dtype=jnp.float32)
        .at[:, 0, 1]
        .set(jnp.asarray([0.3, -0.2], dtype=jnp.float32))
        .at[:, 1, 2]
        .set(jnp.asarray([0.05, 0.08], dtype=jnp.float32))
    )
    divergence = (
        jnp.zeros(state_shape, dtype=jnp.float32)
        .at[:, 1, 1]
        .set(jnp.asarray([0.1, 0.05], dtype=jnp.float32))
        .at[:, 2, 2]
        .set(jnp.asarray([0.02, -0.03], dtype=jnp.float32))
    )
    temperature_variation = (
        jnp.zeros(state_shape, dtype=jnp.float32)
        .at[:, 0, 0]
        .set(jnp.asarray([0.4, -0.1], dtype=jnp.float32))
    )
    log_surface_pressure = (
        jnp.zeros((1, *coords.horizontal.modal_shape), dtype=jnp.float32)
        .at[0, 0, 0]
        .set(jnp.float32(0.03))
    )
    tracers = {
        "specific_humidity": (
            jnp.zeros(state_shape, dtype=jnp.float32)
            .at[:, 0, 0]
            .set(jnp.asarray([0.001, 0.002], dtype=jnp.float32))
        )
    }
    return (
        coords,
        physics_specs,
        _primitive_equation_state(
            vorticity=vorticity,
            divergence=divergence,
            temperature_variation=temperature_variation,
            log_surface_pressure=log_surface_pressure,
            tracers=tracers,
            sim_time=jnp.asarray(3.5, dtype=jnp.float32),
        ),
    )


def _synthetic_wtg_mass_dse_state():
    physics_specs = units.SimUnits.from_si()
    horizontal_grid = spherical_harmonic.Grid(
        longitude_wavenumbers=6,
        total_wavenumbers=8,
        longitude_nodes=16,
        latitude_nodes=9,
        latitude_spacing="equiangular",
        radius=physics_specs.radius,
    )
    coords = coordinate_systems.CoordinateSystem(
        horizontal_grid,
        sigma_coordinates.SigmaCoordinates.equidistant(3),
    )
    state_shape = (coords.vertical.layers, *coords.horizontal.modal_shape)
    longitude, sin_latitude = coords.horizontal.nodal_mesh
    tropical_wave = jnp.cos(longitude) * (1.0 - sin_latitude**2)
    temperature_variation_nodal = (
        jnp.zeros(coords.nodal_shape, dtype=jnp.float32)
        .at[1]
        .set(jnp.float32(4.0) * tropical_wave)
    )
    next_state = _primitive_equation_state(
        vorticity=(
            jnp.zeros(state_shape, dtype=jnp.float32)
            .at[1, 1, 1]
            .set(jnp.float32(0.05))
        ),
        divergence=(
            jnp.zeros(state_shape, dtype=jnp.float32)
            .at[1, 2, 1]
            .set(jnp.float32(-0.03))
        ),
        temperature_variation=coords.horizontal.to_modal(temperature_variation_nodal),
        log_surface_pressure=coords.horizontal.to_modal(
            jnp.zeros(coords.horizontal.nodal_shape, dtype=jnp.float32)
        )[jnp.newaxis],
        tracers={
            "specific_humidity": (
                jnp.zeros(state_shape, dtype=jnp.float32)
                .at[1, 0, 0]
                .set(jnp.float32(0.001))
            )
        },
        sim_time=jnp.asarray(6.0, dtype=jnp.float32),
    )
    prev_state = _primitive_equation_state(
        vorticity=next_state.vorticity,
        divergence=next_state.divergence,
        temperature_variation=jnp.zeros_like(next_state.temperature_variation),
        log_surface_pressure=next_state.log_surface_pressure,
        tracers=next_state.tracers,
        sim_time=jnp.asarray(5.0, dtype=jnp.float32),
    )
    return coords, physics_specs, prev_state, next_state


def _linear_implicit_oscillator_equation(
    frequency: float,
) -> time_integration.ImplicitExplicitODE:
    """Return a linear two-component oscillator in the implicit terms."""
    operator = jnp.asarray(
        [[0.0, -frequency], [frequency, 0.0]],
        dtype=jnp.float32,
    )

    def explicit_terms(state):
        return jnp.zeros_like(state)

    def implicit_terms(state):
        return operator @ state

    def implicit_inverse(state, step_size):
        identity = jnp.eye(2, dtype=state.dtype)
        return jnp.linalg.solve(identity - step_size * operator, state)

    return time_integration.ImplicitExplicitODE.from_functions(
        explicit_terms,
        implicit_terms,
        implicit_inverse,
    )


def _initial_state(*, init_count: int) -> WeatherState:
    longitude_count = 4
    latitude_count = 3
    fields = {
        "temperature_250": 250.0,
        "temperature_750": 285.0,
        "u_component_of_wind_250": 0.0,
        "u_component_of_wind_750": 0.0,
        "v_component_of_wind_250": 0.0,
        "v_component_of_wind_750": 0.0,
        "specific_humidity_250": 0.0,
        "specific_humidity_750": 0.0,
        "geopotential_250": 0.0,
        "2m_temperature": 285.0,
        "10m_u_component_of_wind": 0.0,
        "mean_sea_level_pressure": 100000.0,
        "total_precipitation": 0.0,
    }
    values = jnp.stack(
        [
            jnp.full(
                (init_count, longitude_count, latitude_count),
                fill_value,
                dtype=jnp.float32,
            )
            for fill_value in fields.values()
        ],
        axis=1,
    )
    return WeatherState(values=values, variables=tuple(fields))


def _structured_initial_state(
    *, init_count: int, surface_pressure_pa: float = 100_000.0
) -> WeatherState:
    longitude_count = 4
    latitude_count = 3
    lon_pattern = jnp.arange(longitude_count, dtype=jnp.float32)[:, np.newaxis]
    lat_pattern = jnp.arange(latitude_count, dtype=jnp.float32)[np.newaxis, :]
    spatial_pattern = lon_pattern + 0.25 * lat_pattern
    pressure_levels = (100, 500, 900)
    fields = {}
    for pressure_level in pressure_levels:
        pressure_scale = pressure_level / 100.0
        fields[f"temperature_{pressure_level}"] = (
            220.0 + 0.04 * pressure_level + spatial_pattern
        )
        fields[f"u_component_of_wind_{pressure_level}"] = (
            0.4 * pressure_scale + 0.1 * spatial_pattern
        )
        fields[f"v_component_of_wind_{pressure_level}"] = (
            -0.2 * pressure_scale + 0.05 * spatial_pattern
        )
        fields[f"specific_humidity_{pressure_level}"] = (
            0.001 + pressure_level / 1_000_000.0 + 0.00001 * spatial_pattern
        )
        fields[f"geopotential_{pressure_level}"] = (
            1000.0 + pressure_level + 5.0 * spatial_pattern
        )
    fields["mean_sea_level_pressure"] = surface_pressure_pa + 50.0 * spatial_pattern
    fields["2m_temperature"] = 285.0 + spatial_pattern
    fields["10m_u_component_of_wind"] = 2.0 + 0.1 * spatial_pattern
    fields["total_precipitation"] = jnp.zeros_like(spatial_pattern)

    values = jnp.stack(
        [
            jnp.broadcast_to(
                field_value,
                (init_count, longitude_count, latitude_count),
            )
            for field_value in fields.values()
        ],
        axis=1,
    )
    return WeatherState(values=values, variables=tuple(fields))


def _structured_field(
    state: WeatherState,
    variable_name: str,
    pressure_levels_hpa: tuple[int, ...],
    latitude_reversed: bool,
) -> jax.Array:
    channels = tuple(
        f"{variable_name}_{pressure_level}" for pressure_level in pressure_levels_hpa
    )
    values = jnp.take(
        state.values,
        jnp.asarray(state.variable_indices(channels), dtype=jnp.int32),
        axis=-3,
    )
    if latitude_reversed:
        return values[..., ::-1]
    return values


def _surface_pressure_field(
    state: WeatherState,
    latitude_reversed: bool,
) -> jax.Array:
    values = state.select(("mean_sea_level_pressure",)).values[0]
    if latitude_reversed:
        return values[..., ::-1]
    return values


def _residual_split_test_grid() -> spherical_harmonic.Grid:
    return spherical_harmonic.Grid(
        longitude_wavenumbers=10,
        total_wavenumbers=24,
        longitude_nodes=64,
        latitude_nodes=48,
        latitude_spacing="gauss",
    )


def _analysis_offset_test_setup(
    *,
    layer_count: int = 2,
) -> tuple[coordinate_systems.CoordinateSystem, Any, np.ndarray]:
    coords = coordinate_systems.CoordinateSystem(
        horizontal=_residual_split_test_grid(),
        vertical=sigma_coordinates.SigmaCoordinates.equidistant(layer_count),
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=layer_count,
        temperature_kelvin=250.0,
    )
    return coords, physics_specs, reference_temperature


def _ocean_bulk_shf_test_setup() -> tuple[
    coordinate_systems.CoordinateSystem,
    Any,
    np.ndarray,
    Any,
]:
    physics_specs = units.SimUnits.from_si()
    horizontal_grid = spherical_harmonic.Grid(
        longitude_wavenumbers=4,
        total_wavenumbers=6,
        longitude_nodes=16,
        latitude_nodes=8,
        latitude_spacing="gauss",
        radius=physics_specs.radius,
    )
    coords = coordinate_systems.CoordinateSystem(
        horizontal_grid,
        sigma_coordinates.SigmaCoordinates.equidistant(2),
    )
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    wind_unit = _unit_factor(physics_specs, "meter / second")
    u_wind = (
        jnp.zeros(coords.nodal_shape, dtype=jnp.float32).at[-1].set(12.0 * wind_unit)
    )
    v_wind = (
        jnp.zeros(coords.nodal_shape, dtype=jnp.float32).at[-1].set(3.0 * wind_unit)
    )
    vorticity, divergence = spherical_harmonic.uv_nodal_to_vor_div_modal(
        coords.horizontal,
        u_wind,
        v_wind,
    )
    full_temperature = jnp.stack(
        [
            jnp.full(coords.horizontal.nodal_shape, 260.0, dtype=jnp.float32),
            jnp.full(coords.horizontal.nodal_shape, 280.0, dtype=jnp.float32),
        ],
        axis=0,
    )
    surface_pressure = jnp.full(
        coords.horizontal.nodal_shape,
        100_000.0 * _unit_factor(physics_specs, "pascal"),
        dtype=jnp.float32,
    )
    state = _primitive_equation_state(
        vorticity=vorticity,
        divergence=divergence,
        temperature_variation=coords.horizontal.to_modal(
            full_temperature - reference_temperature[:, np.newaxis, np.newaxis]
        ),
        log_surface_pressure=coords.horizontal.to_modal(jnp.log(surface_pressure))[
            jnp.newaxis
        ],
        tracers={},
    )
    return coords, physics_specs, reference_temperature, state


def _hsl_theta_aux_state(
    coords: coordinate_systems.CoordinateSystem,
    *,
    u_cos_lat: jax.Array,
    v_cos_lat: jax.Array,
    temperature_variation: jax.Array,
) -> primitive_equations.DiagnosticStateSigma:
    """Build a minimal diagnostic state for horizontal theta transport tests."""
    zero_layer_boundaries = jnp.zeros(
        (coords.vertical.layers - 1,) + coords.horizontal.nodal_shape,
        dtype=temperature_variation.dtype,
    )
    zero_surface_vector = jnp.zeros(
        (1,) + coords.horizontal.nodal_shape,
        dtype=temperature_variation.dtype,
    )
    return primitive_equations.DiagnosticStateSigma(
        vorticity=jnp.zeros(coords.nodal_shape, dtype=temperature_variation.dtype),
        divergence=jnp.zeros(coords.nodal_shape, dtype=temperature_variation.dtype),
        temperature_variation=temperature_variation,
        cos_lat_u=(u_cos_lat, v_cos_lat),
        sigma_dot_explicit=zero_layer_boundaries,
        sigma_dot_full=zero_layer_boundaries,
        cos_lat_grad_log_sp=(zero_surface_vector, zero_surface_vector),
        u_dot_grad_log_sp=jnp.zeros(
            coords.nodal_shape,
            dtype=temperature_variation.dtype,
        ),
        tracers={},
    )


def _dinosaur_state_with_hs_equilibrium_offset(
    *,
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    reference_temperature: np.ndarray,
    equilibrium_offset: jax.Array,
) -> Any:
    surface_pressure = jnp.full(
        coords.horizontal.nodal_shape,
        100_000.0 * _unit_factor(physics_specs, "pascal"),
        dtype=jnp.float32,
    )
    forcing = _TracerSafeHeldSuarezForcingSigma(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
    )
    equilibrium_temperature = forcing.equilibrium_temperature(surface_pressure)
    temperature = equilibrium_temperature + equilibrium_offset
    return _primitive_equation_state(
        vorticity=jnp.zeros(coords.modal_shape, dtype=jnp.float32),
        divergence=jnp.zeros(coords.modal_shape, dtype=jnp.float32),
        temperature_variation=coords.horizontal.to_modal(
            temperature - reference_temperature[:, np.newaxis, np.newaxis]
        ),
        log_surface_pressure=coords.horizontal.to_modal(jnp.log(surface_pressure))[
            jnp.newaxis
        ],
        tracers={},
    )


def _assert_pytree_allclose(actual, expected):
    for actual_leaf, expected_leaf in zip(
        jax.tree_util.tree_leaves(actual),
        jax.tree_util.tree_leaves(expected),
        strict=True,
    ):
        np.testing.assert_allclose(actual_leaf, expected_leaf, rtol=1e-6, atol=1e-6)


def _theta_layer_mean(
    coords: coordinate_systems.CoordinateSystem,
    physics_specs: Any,
    reference_temperature: np.ndarray,
    state: Any,
) -> jax.Array:
    pressure = jnp.asarray(coords.vertical.centers)[
        :, jnp.newaxis, jnp.newaxis
    ] * jnp.exp(coords.horizontal.to_nodal(state.log_surface_pressure))
    temperature = (
        coords.horizontal.to_nodal(state.temperature_variation)
        + jnp.asarray(reference_temperature)[:, jnp.newaxis, jnp.newaxis]
    )
    unit_registry = cast(Any, scales.units)
    reference_pressure = float(
        physics_specs.nondimensionalize(unit_registry.Quantity(100000.0, "pascal"))
    )
    theta = primitive_equations.potential_temperature_from_temperature(
        temperature,
        pressure,
        reference_pressure,
        physics_specs.kappa,
    )
    weights = jnp.asarray(coords.horizontal.quadrature_weights)
    return jnp.sum(theta * weights, axis=(-2, -1)) / jnp.sum(weights)


def _forecast_input(
    initial_state: WeatherState,
    *,
    lead_steps: tuple[int, ...],
) -> ForecastInput:
    initial_count = initial_state.leading_shape[0]
    initial_times = np.datetime64("2020-01-01T00:00:00", "ns") + np.arange(
        initial_count
    ).astype("timedelta64[h]")
    lead_hours = tuple(lead_steps)
    valid_times = (
        initial_times[:, np.newaxis]
        + np.asarray(lead_hours, dtype="timedelta64[h]")[np.newaxis, :]
    )
    return ForecastInput(
        initial_times=initial_times,
        valid_times=valid_times,
        lead_steps=lead_steps,
        lead_hours=lead_hours,
        step_seconds=3600.0,
        longitude=np.array([0.0, 90.0, 180.0, 270.0]),
        latitude=np.array([90.0, 0.0, -90.0]),
        initial_state=initial_state,
    )
