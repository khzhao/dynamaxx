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
}


def dycore_model_names() -> tuple[str, ...]:
    """Return registered dycore model names."""
    return tuple(DYCORE_MODEL_FACTORIES)


def create_dycore_model(name: str) -> DycoreModel:
    """Create a registered dycore model by name."""
    assert name in DYCORE_MODEL_FACTORIES, f"unknown dycore model {name}"
    return DYCORE_MODEL_FACTORIES[name]()
