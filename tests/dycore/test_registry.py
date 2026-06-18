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


def test_registry_rejects_unknown_dycore_model():
    """Unknown dycore names fail with the registry assertion."""
    with pytest.raises(AssertionError, match="unknown dycore model"):
        create_dycore_model("missing")
