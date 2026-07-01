# Copyright 2026 dynamaxx

from collections.abc import Callable

from dynamaxx.dycore.api import DycoreModel

DycoreModelFactory = Callable[[], DycoreModel]


def persistence_model() -> DycoreModel:
    """Return the default persistence dycore model."""
    from dynamaxx.dycore.models.persistence import default_persistence_dycore_model

    return default_persistence_dycore_model()


def dinosaur_model() -> DycoreModel:
    """Return the default Dinosaur primitive-equation dycore model."""
    from dynamaxx.dycore.models.dinosaur import default_dinosaur_dycore_model

    return default_dinosaur_dycore_model()


def dinosaur_dfi_model() -> DycoreModel:
    """Return the Dinosaur primitive-equation dycore with DFI enabled."""
    from dynamaxx.dycore.models.dinosaur import digital_filter_dinosaur_dycore_model

    return digital_filter_dinosaur_dycore_model()


def dinosaur_dfi_surface_residual_model() -> DycoreModel:
    """Return the DFI dycore with near-surface diagnostic residual correction."""
    from dynamaxx.dycore.models.dinosaur import (
        digital_filter_surface_residual_dinosaur_dycore_model,
    )

    return digital_filter_surface_residual_dinosaur_dycore_model()


def dinosaur_dfi_surface_residual_weak_hs_model() -> DycoreModel:
    """Return the DFI and residual dycore with weak HS thermal relaxation."""
    from dynamaxx.dycore.models.dinosaur import weak_held_suarez_dinosaur_dycore_model

    return weak_held_suarez_dinosaur_dycore_model()


def dinosaur_dfi_surface_residual_weak_hs_logp_init_model() -> DycoreModel:
    """Return the weak HS dycore with log-pressure initialization."""
    from dynamaxx.dycore.models.dinosaur import (
        log_pressure_initialization_dinosaur_dycore_model,
    )

    return log_pressure_initialization_dinosaur_dycore_model()


def dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init_model() -> (
    DycoreModel
):
    """Return the log-pressure dycore with hydrostatic temperature initialization."""
    from dynamaxx.dycore.models.dinosaur import (
        hydrostatic_temperature_initialization_dinosaur_dycore_model,
    )

    return hydrostatic_temperature_initialization_dinosaur_dycore_model()


def dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_model() -> (
    DycoreModel
):
    """Return the hydrostatic dycore with layer-mean temperature initialization."""
    from dynamaxx.dycore.models.dinosaur import (
        layer_mean_hydrostatic_temperature_initialization_dinosaur_dycore_model,
    )

    return layer_mean_hydrostatic_temperature_initialization_dinosaur_dycore_model()


def dinosaur_coriolis_split_model() -> DycoreModel:
    """Return the layer-mean incumbent with exact Coriolis rollout splitting."""
    from dynamaxx.dycore.models.dinosaur import coriolis_split_dinosaur_dycore_model

    return coriolis_split_dinosaur_dycore_model()


def dinosaur_coriolis_strang_model() -> DycoreModel:
    """Return the exact-Coriolis split with symmetric rollout ordering."""
    from dynamaxx.dycore.models.dinosaur import (
        coriolis_strang_split_dinosaur_dycore_model,
    )

    return coriolis_strang_split_dinosaur_dycore_model()


def dinosaur_stability_surface_residual_model() -> DycoreModel:
    """Return the Strang dycore with stability-aware residual decay."""
    from dynamaxx.dycore.models.dinosaur import (
        stability_aware_surface_residual_dinosaur_dycore_model,
    )

    return stability_aware_surface_residual_dinosaur_dycore_model()


def dinosaur_ri_10m_wind_model() -> DycoreModel:
    """Return the stability residual dycore with Richardson 10 m wind output."""
    from dynamaxx.dycore.models.dinosaur import (
        richardson_10m_wind_diagnostic_dinosaur_dycore_model,
    )

    return richardson_10m_wind_diagnostic_dinosaur_dycore_model()


def dinosaur_theta_tendency_model() -> DycoreModel:
    """Return the Richardson 10 m wind dycore with theta-form thermal tendency."""
    from dynamaxx.dycore.models.dinosaur import theta_tendency_dinosaur_dycore_model

    return theta_tendency_dinosaur_dycore_model()


def dinosaur_theta_mean_recenter_model() -> DycoreModel:
    """Return the theta incumbent with rollout-only theta mean recentering."""
    from dynamaxx.dycore.models.dinosaur import (
        theta_mean_recenter_dinosaur_dycore_model,
    )

    return theta_mean_recenter_dinosaur_dycore_model()


def dinosaur_semi_implicit_offcenter_model() -> DycoreModel:
    """Return the theta incumbent with fixed SIL3 implicit off-centering."""
    from dynamaxx.dycore.models.dinosaur import (
        semi_implicit_offcenter_dinosaur_dycore_model,
    )

    return semi_implicit_offcenter_dinosaur_dycore_model()


def dinosaur_scale_separated_surface_residual_model() -> DycoreModel:
    """Return the offcenter dycore with scale-separated residual memory."""
    from dynamaxx.dycore.models.dinosaur import (
        scale_separated_surface_residual_dinosaur_dycore_model,
    )

    return scale_separated_surface_residual_dinosaur_dycore_model()


def dinosaur_analysis_offset_held_suarez_equilibrium_model() -> DycoreModel:
    """Return the scale-residual dycore with analysis-offset HS equilibrium."""
    from dynamaxx.dycore.models.dinosaur import (
        analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model,
    )

    return analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model()


def dinosaur_land_sea_surface_temperature_model() -> DycoreModel:
    """Return the analysis-HS dycore with land-sea T2m residual memory."""
    from dynamaxx.dycore.models.dinosaur import (
        land_sea_surface_temperature_dinosaur_dycore_model,
    )

    return land_sea_surface_temperature_dinosaur_dycore_model()


def dinosaur_ocean_bulk_sensible_heat_flux_model() -> DycoreModel:
    """Return the land-sea incumbent with weak ocean bulk SHF forcing."""
    from dynamaxx.dycore.models.dinosaur import (
        ocean_bulk_sensible_heat_flux_dinosaur_dycore_model,
    )

    return ocean_bulk_sensible_heat_flux_dinosaur_dycore_model()


def dino_hsl_theta_model() -> DycoreModel:
    """Return the ocean-bulk incumbent with horizontal SL theta transport."""
    from dynamaxx.dycore.models.dinosaur import (
        horizontal_semilagrangian_theta_transport_dinosaur_dycore_model,
    )

    return horizontal_semilagrangian_theta_transport_dinosaur_dycore_model()


def dino_hsl2_theta_model() -> DycoreModel:
    """Return HSL theta with midpoint departure estimates for theta only."""
    from dynamaxx.dycore.models.dinosaur import (
        midpoint_semilagrangian_theta_departure_dinosaur_dycore_model,
    )

    return midpoint_semilagrangian_theta_departure_dinosaur_dycore_model()


def dino_hsl2_theta_dse_hsl_model() -> DycoreModel:
    """Return HSL2 theta with DSE horizontal thermal transport."""
    from dynamaxx.dycore.models.dinosaur import (
        dry_static_energy_hsl_transport_dinosaur_dycore_model,
    )

    return dry_static_energy_hsl_transport_dinosaur_dycore_model()


def dino_hsl2_mass_dse_model() -> DycoreModel:
    """Return DSE-HSL with layer-mass-weighted DSE thermal transport."""
    from dynamaxx.dycore.models.dinosaur import (
        layer_mass_weighted_dse_hsl_transport_dinosaur_dycore_model,
    )

    return layer_mass_weighted_dse_hsl_transport_dinosaur_dycore_model()


def dino_hsl2_mass_dse_wtg_model() -> DycoreModel:
    """Return mass-DSE HSL with rollout-only tropical WTG relaxation."""
    from dynamaxx.dycore.models.dinosaur import (
        tropical_wtg_mass_dse_relaxation_dinosaur_dycore_model,
    )

    return tropical_wtg_mass_dse_relaxation_dinosaur_dycore_model()


def dino_hsl2_mass_dse_wtg_vdse_ramp_model() -> DycoreModel:
    """Return WTG mass-DSE with pressure-ramped vertical-DSE increments."""
    from dynamaxx.dycore.models.dinosaur import (
        pressure_ramped_vertical_dse_wtg_dinosaur_dycore_model,
    )

    return pressure_ramped_vertical_dse_wtg_dinosaur_dycore_model()


def dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_model() -> DycoreModel:
    """Return vertical-DSE incumbent with broad land/ocean T2m memory."""
    from dynamaxx.dycore.models.dinosaur import (
        land_ocean_low_mode_t2m_memory_dinosaur_dycore_model,
    )

    return land_ocean_low_mode_t2m_memory_dinosaur_dycore_model()


def dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_model() -> DycoreModel:
    """Return low-mode T2m incumbent with bounded raw 2 m temperature output."""
    from dynamaxx.dycore.models.dinosaur import (
        bulk_richardson_2m_temperature_diagnostic_dinosaur_dycore_model,
    )

    return bulk_richardson_2m_temperature_diagnostic_dinosaur_dycore_model()


def dino_ri2m_ekman_coupled_model() -> DycoreModel:
    """Return RI2m incumbent with weak coupled Ekman stress and pumping."""
    from dynamaxx.dycore.models.dinosaur import ekman_coupled_dinosaur_dycore_model

    return ekman_coupled_dinosaur_dycore_model()


def dino_ri2m_ekman_depth_model() -> DycoreModel:
    """Return coupled Ekman with bounded Coriolis-scaled stress depth."""
    from dynamaxx.dycore.models.dinosaur import ekman_depth_dinosaur_dycore_model

    return ekman_depth_dinosaur_dycore_model()


DYCORE_MODEL_FACTORIES: dict[str, DycoreModelFactory] = {
    "persistence": persistence_model,
    "dinosaur": dinosaur_model,
    "dinosaur_dfi": dinosaur_dfi_model,
    "dinosaur_dfi_surface_residual": dinosaur_dfi_surface_residual_model,
    "dinosaur_dfi_surface_residual_weak_hs": (
        dinosaur_dfi_surface_residual_weak_hs_model
    ),
    "dinosaur_dfi_surface_residual_weak_hs_logp_init": (
        dinosaur_dfi_surface_residual_weak_hs_logp_init_model
    ),
    "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init": (
        dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init_model
    ),
    "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init": (
        dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_model
    ),
    (
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_split"
    ): dinosaur_coriolis_split_model,
    (
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang"
    ): dinosaur_coriolis_strang_model,
    (
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual"
    ): dinosaur_stability_surface_residual_model,
    (
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind"
    ): dinosaur_ri_10m_wind_model,
    (
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency"
    ): dinosaur_theta_tendency_model,
    (
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter"
    ): dinosaur_theta_mean_recenter_model,
    (
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter"
    ): dinosaur_semi_implicit_offcenter_model,
    (
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual"
    ): dinosaur_scale_separated_surface_residual_model,
    (
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq"
    ): dinosaur_analysis_offset_held_suarez_equilibrium_model,
    (
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface"
    ): dinosaur_land_sea_surface_temperature_model,
    (
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf"
    ): dinosaur_ocean_bulk_sensible_heat_flux_model,
    "dino_hsl_theta": dino_hsl_theta_model,
    "dino_hsl2_theta": dino_hsl2_theta_model,
    "dino_hsl2_theta_dse_hsl": dino_hsl2_theta_dse_hsl_model,
    "dino_hsl2_mass_dse": dino_hsl2_mass_dse_model,
    "dino_hsl2_mass_dse_wtg": dino_hsl2_mass_dse_wtg_model,
    "dino_hsl2_mass_dse_wtg_vdse_ramp": (dino_hsl2_mass_dse_wtg_vdse_ramp_model),
    "dino_hsl2_mass_dse_wtg_vdse_t2m_lomem": (
        dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_model
    ),
    "dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m": (
        dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_model
    ),
    "dino_ri2m_ekman_coupled": dino_ri2m_ekman_coupled_model,
    "dino_ri2m_ekman_depth": dino_ri2m_ekman_depth_model,
}


def dycore_model_names() -> tuple[str, ...]:
    """Return registered dycore model names."""
    return tuple(DYCORE_MODEL_FACTORIES)


def create_dycore_model(name: str) -> DycoreModel:
    """Create a registered dycore model by name."""
    assert name in DYCORE_MODEL_FACTORIES, f"unknown dycore model {name}"
    return DYCORE_MODEL_FACTORIES[name]()
