# Copyright 2026 dynamaxx

from dataclasses import fields

import pytest

from dynamaxx.dycore.models.dinosaur import DinosaurPrimitiveEquationsDycoreModel
from dynamaxx.dycore.models.persistence import PersistenceDycoreModel
from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names


def test_registry_exposes_only_supported_models():
    """The registry contains reference models and the production dycore only."""
    assert dycore_model_names() == ("persistence", "dinosaur", "dino_rskin_apv")
    assert isinstance(create_dycore_model("persistence"), PersistenceDycoreModel)
    assert isinstance(
        create_dycore_model("dinosaur"), DinosaurPrimitiveEquationsDycoreModel
    )
    assert create_dycore_model("dino_rskin_apv").name == "dino_rskin_apv"


def test_registry_rejects_unknown_model_with_supported_names():
    """Unknown names report the complete supported model set."""
    with pytest.raises(
        ValueError,
        match="expected one of: persistence, dinosaur, dino_rskin_apv",
    ):
        create_dycore_model("historical_experiment")


def test_production_dinosaur_configuration_is_pinned():
    """The collapsed production factory matches the accepted configuration."""
    baseline = DinosaurPrimitiveEquationsDycoreModel()
    production = create_dycore_model("dino_rskin_apv")

    changed_fields = {
        field.name: getattr(production, field.name)
        for field in fields(production)
        if getattr(production, field.name) != getattr(baseline, field.name)
    }
    assert changed_fields == {
        "name": "dino_rskin_apv",
        "use_log_pressure_initialization": True,
        "use_hydrostatic_temperature_initialization": True,
        "use_layer_mean_hydrostatic_temperature_initialization": True,
        "apply_digital_filter_initialization": True,
        "apply_weak_held_suarez_relaxation": True,
        "use_analysis_offset_weak_held_suarez_equilibrium": True,
        "apply_near_surface_residual_correction": True,
        "use_stability_aware_near_surface_residual_decay": True,
        "use_scale_separated_near_surface_residual": True,
        "use_land_sea_surface_temperature_residual": True,
        "use_land_ocean_low_mode_t2m_memory": True,
        "apply_ocean_bulk_sensible_heat_flux": True,
        "apply_land_skin_reservoir": True,
        "use_analysis_2m_initialized_land_skin": True,
        "apply_zero_mean_radiative_land_skin_energy": True,
        "use_surface_layer_richardson_10m_wind_diagnostic": True,
        "use_bulk_richardson_2m_temperature_diagnostic": True,
        "use_pressure_thickness_weighted_ri2m_temperature": True,
        "use_prognostic_skin_ri2m_lower_boundary": True,
        "use_ocean_anchor_ri2m_lower_boundary": True,
        "apply_exact_coriolis_rotation_split": True,
        "apply_symmetric_exact_coriolis_rotation_split": True,
        "temperature_tendency_formulation": "potential_temperature",
        "apply_theta_layer_mean_recentering": True,
        "use_horizontal_semilagrangian_theta_transport": True,
        "use_midpoint_semilagrangian_theta_departure": True,
        "use_dry_static_energy_hsl_transport": True,
        "use_layer_mass_weighted_dse_hsl_transport": True,
        "use_pressure_ramped_vertical_dse_increment": True,
        "apply_anticipated_pv_flux": True,
        "apply_tropical_wtg_mass_dse_relaxation": True,
        "apply_coupled_ekman_surface_closure": True,
        "use_coriolis_scaled_ekman_depth": True,
        "apply_orographic_lift_theta_tendency": True,
        "use_depth_weighted_orographic_lift_wind": True,
        "apply_terrain_work_form_drag_heating": True,
        "semi_implicit_offcentering": 0.05,
    }
