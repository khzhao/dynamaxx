# Copyright 2026 dynamaxx

import pytest

from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names


def test_registry_lists_default_dycore_models():
    """The registry lists the default and side-by-side candidate dycore models."""
    assert dycore_model_names() == (
        "persistence",
        "dinosaur",
        "dinosaur_dfi",
        "dinosaur_dfi_surface_residual",
        "dinosaur_dfi_surface_residual_weak_hs",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_split",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf",
        "dino_hsl_theta",
        "dino_hsl2_theta",
        "dino_hsl2_theta_dse_hsl",
        "dino_hsl2_mass_dse",
        "dino_hsl2_mass_dse_wtg",
        "dino_hsl2_mass_dse_wtg_vdse_ramp",
        "dino_hsl2_mass_dse_wtg_vdse_t2m_lomem",
    )


def test_registry_creates_dinosaur_dycore_model():
    """The vendored Dinosaur dycore is registered under the canonical name."""
    assert create_dycore_model("dinosaur").name == "dinosaur"


def test_registry_creates_dinosaur_dfi_candidate_model():
    """The DFI candidate is registered without changing the canonical model."""
    model = create_dycore_model("dinosaur_dfi")

    assert model.name == "dinosaur_dfi"
    assert model.apply_digital_filter_initialization
    assert not model.apply_near_surface_residual_correction
    assert not create_dycore_model("dinosaur").apply_digital_filter_initialization


def test_registry_creates_dinosaur_dfi_surface_residual_candidate_model():
    """The residual candidate is registered without changing existing factories."""
    model = create_dycore_model("dinosaur_dfi_surface_residual")

    assert model.name == "dinosaur_dfi_surface_residual"
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert not create_dycore_model(
        "dinosaur_dfi"
    ).apply_near_surface_residual_correction


def test_registry_creates_weak_held_suarez_candidate_model():
    """The weak HS candidate is registered side by side with the incumbent."""
    model = create_dycore_model("dinosaur_dfi_surface_residual_weak_hs")

    assert model.name == "dinosaur_dfi_surface_residual_weak_hs"
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert not model.use_log_pressure_initialization
    assert not create_dycore_model(
        "dinosaur_dfi_surface_residual"
    ).apply_weak_held_suarez_relaxation


def test_registry_creates_log_pressure_initialization_candidate_model():
    """The log-pressure candidate is registered without replacing the incumbent."""
    model = create_dycore_model("dinosaur_dfi_surface_residual_weak_hs_logp_init")
    incumbent = create_dycore_model("dinosaur_dfi_surface_residual_weak_hs")

    assert model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init"
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == 80
    assert model.apply_spectral_filter
    assert model.horizontal_diffusion_order == 2
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection
    assert not incumbent.use_log_pressure_initialization


def test_registry_creates_hydrostatic_initialization_candidate_model():
    """The hydrostatic candidate is registered without replacing the incumbent."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init"
    )
    incumbent = create_dycore_model("dinosaur_dfi_surface_residual_weak_hs_logp_init")

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == 80
    assert model.apply_spectral_filter
    assert model.horizontal_diffusion_order == 2
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection
    assert not incumbent.use_hydrostatic_temperature_initialization


def test_registry_creates_layer_mean_hydrostatic_initialization_candidate_model():
    """The layer-mean candidate is registered without replacing the incumbent."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init"
    )

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
    assert model.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == 80
    assert model.apply_spectral_filter
    assert model.horizontal_diffusion_order == 2
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection
    assert not incumbent.use_layer_mean_hydrostatic_temperature_initialization


def test_registry_creates_coriolis_split_candidate_model():
    """The exact-Coriolis split is registered without replacing the incumbent."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_split"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_split"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert not incumbent.apply_exact_coriolis_rotation_split


def test_registry_creates_coriolis_strang_candidate_model():
    """The symmetric exact-Coriolis split is registered side by side."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_split"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert not incumbent.apply_symmetric_exact_coriolis_rotation_split


def test_registry_creates_stability_aware_surface_residual_candidate_model():
    """The stability-aware residual decay candidate is registered side by side."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.use_stability_aware_near_surface_residual_decay
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert not incumbent.use_stability_aware_near_surface_residual_decay


def test_registry_creates_richardson_10m_wind_candidate_model():
    """The Richardson 10 m wind diagnostic is registered side by side."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.use_stability_aware_near_surface_residual_decay
    assert model.use_surface_layer_richardson_10m_wind_diagnostic
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert not incumbent.use_surface_layer_richardson_10m_wind_diagnostic


def test_registry_creates_theta_tendency_candidate_model():
    """The theta-tendency candidate is registered without replacing incumbent."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.use_stability_aware_near_surface_residual_decay
    assert model.use_surface_layer_richardson_10m_wind_diagnostic
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert model.temperature_tendency_formulation == "potential_temperature"
    assert incumbent.temperature_tendency_formulation == "temperature"


def test_registry_creates_theta_mean_recenter_candidate_model():
    """The theta recentering candidate is registered without replacing incumbent."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.use_stability_aware_near_surface_residual_decay
    assert model.use_surface_layer_richardson_10m_wind_diagnostic
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert model.temperature_tendency_formulation == "potential_temperature"
    assert model.apply_theta_layer_mean_recentering
    assert not incumbent.apply_theta_layer_mean_recentering


def test_registry_creates_semi_implicit_offcenter_candidate_model():
    """The fixed SIL3 off-centering candidate is registered side by side."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.use_stability_aware_near_surface_residual_decay
    assert model.use_surface_layer_richardson_10m_wind_diagnostic
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.temperature_tendency_formulation == "potential_temperature"
    assert model.apply_theta_layer_mean_recentering
    assert model.semi_implicit_offcentering == 0.05
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "semi_implicit_offcentering"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_registry_creates_scale_separated_residual_candidate_model():
    """The scale-separated residual candidate is registered side by side."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.use_stability_aware_near_surface_residual_decay
    assert model.use_surface_layer_richardson_10m_wind_diagnostic
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.temperature_tendency_formulation == "potential_temperature"
    assert model.apply_theta_layer_mean_recentering
    assert model.semi_implicit_offcentering == 0.05
    assert model.use_scale_separated_near_surface_residual
    assert not incumbent.use_scale_separated_near_surface_residual
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_scale_separated_near_surface_residual"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_registry_creates_analysis_offset_hs_eq_candidate_model():
    """The analysis-offset HS equilibrium candidate is registered side by side."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq"
    )
    assert model.use_analysis_offset_weak_held_suarez_equilibrium
    assert not incumbent.use_analysis_offset_weak_held_suarez_equilibrium
    for field_name in model.__dataclass_fields__:
        if field_name in {
            "name",
            "use_analysis_offset_weak_held_suarez_equilibrium",
        }:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_registry_creates_land_sea_surface_temperature_candidate_model():
    """The land-sea T2m residual candidate is registered side by side."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface"
    )
    assert model.use_land_sea_surface_temperature_residual
    assert not incumbent.use_land_sea_surface_temperature_residual
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_land_sea_surface_temperature_residual"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_registry_creates_ocean_bulk_shf_candidate_model():
    """The ocean bulk SHF candidate is registered side by side."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf"
    )
    assert model.apply_ocean_bulk_sensible_heat_flux
    assert not incumbent.apply_ocean_bulk_sensible_heat_flux
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "apply_ocean_bulk_sensible_heat_flux"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_registry_creates_hsl_theta_candidate_model():
    """The short alias adds only the horizontal SL theta selector."""
    model = create_dycore_model("dino_hsl_theta")
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf"
    )

    assert model.name == "dino_hsl_theta"
    assert len(model.name) < 32
    assert model.use_horizontal_semilagrangian_theta_transport
    assert not incumbent.use_horizontal_semilagrangian_theta_transport
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_horizontal_semilagrangian_theta_transport"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_registry_creates_hsl2_theta_candidate_model():
    """The midpoint alias adds only the theta midpoint departure selector."""
    model = create_dycore_model("dino_hsl2_theta")
    incumbent = create_dycore_model("dino_hsl_theta")

    assert model.name == "dino_hsl2_theta"
    assert len(model.name) < 32
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert incumbent.use_horizontal_semilagrangian_theta_transport
    assert not incumbent.use_midpoint_semilagrangian_theta_departure
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_midpoint_semilagrangian_theta_departure"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_registry_creates_dse_hsl_candidate_model():
    """The DSE-HSL alias adds only the DSE transport selector."""
    model = create_dycore_model("dino_hsl2_theta_dse_hsl")
    incumbent = create_dycore_model("dino_hsl2_theta")

    assert model.name == "dino_hsl2_theta_dse_hsl"
    assert len(model.name) < 32
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert incumbent.use_horizontal_semilagrangian_theta_transport
    assert incumbent.use_midpoint_semilagrangian_theta_departure
    assert not incumbent.use_dry_static_energy_hsl_transport
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_dry_static_energy_hsl_transport"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_registry_creates_layer_mass_dse_candidate_model():
    """The mass-DSE alias adds only the layer-mass-weighted DSE selector."""
    model = create_dycore_model("dino_hsl2_mass_dse")
    incumbent = create_dycore_model("dino_hsl2_theta_dse_hsl")

    assert model.name == "dino_hsl2_mass_dse"
    assert len(model.name) < 32
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert incumbent.use_dry_static_energy_hsl_transport
    assert not incumbent.use_layer_mass_weighted_dse_hsl_transport
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_layer_mass_weighted_dse_hsl_transport"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_registry_creates_tropical_wtg_mass_dse_candidate_model():
    """The WTG alias adds only the rollout tropical WTG selector."""
    model = create_dycore_model("dino_hsl2_mass_dse_wtg")
    incumbent = create_dycore_model("dino_hsl2_mass_dse")

    assert model.name == "dino_hsl2_mass_dse_wtg"
    assert len(model.name) < 32
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert not incumbent.apply_tropical_wtg_mass_dse_relaxation
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "apply_tropical_wtg_mass_dse_relaxation"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_registry_creates_pressure_ramped_vertical_dse_candidate_model():
    """The vertical-DSE ramp alias adds only the guarded increment selector."""
    model = create_dycore_model("dino_hsl2_mass_dse_wtg_vdse_ramp")
    incumbent = create_dycore_model("dino_hsl2_mass_dse_wtg")

    assert model.name == "dino_hsl2_mass_dse_wtg_vdse_ramp"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert model.use_pressure_ramped_vertical_dse_increment
    assert not incumbent.use_pressure_ramped_vertical_dse_increment
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_pressure_ramped_vertical_dse_increment"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_registry_creates_land_ocean_low_mode_t2m_memory_candidate_model():
    """The broad T2m memory alias adds only the output-memory selector."""
    model = create_dycore_model("dino_hsl2_mass_dse_wtg_vdse_t2m_lomem")
    incumbent = create_dycore_model("dino_hsl2_mass_dse_wtg_vdse_ramp")

    assert model.name == "dino_hsl2_mass_dse_wtg_vdse_t2m_lomem"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert model.use_pressure_ramped_vertical_dse_increment
    assert model.use_land_ocean_low_mode_t2m_memory
    assert not incumbent.use_land_ocean_low_mode_t2m_memory
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_land_ocean_low_mode_t2m_memory"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_registry_rejects_unknown_dycore_model():
    """Unknown dycore names fail with the registry assertion."""
    with pytest.raises(AssertionError, match="unknown dycore model"):
        create_dycore_model("missing")
