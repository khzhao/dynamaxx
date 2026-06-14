# Copyright 2026 dynamaxx

from collections.abc import Callable

from dynamaxx.dycore.api import DycoreModel

DycoreModelFactory = Callable[[], DycoreModel]


def advected_persistence_model() -> DycoreModel:
    """Return the default advected persistence dycore model."""
    from dynamaxx.dycore.models.advected_persistence import (
        default_advected_persistence_dycore_model,
    )

    return default_advected_persistence_dycore_model()


def barotropic_vorticity_model() -> DycoreModel:
    """Return the default barotropic-vorticity dycore model."""
    from dynamaxx.dycore.models.barotropic_vorticity import (
        default_barotropic_vorticity_dycore_model,
    )

    return default_barotropic_vorticity_dycore_model()


def geostrophic_advection_model() -> DycoreModel:
    """Return the default geostrophic advection dycore model."""
    from dynamaxx.dycore.models.geostrophic_advection import (
        default_geostrophic_advection_dycore_model,
    )

    return default_geostrophic_advection_dycore_model()


def inertial_layered_balanced_zonal_advection_model() -> DycoreModel:
    """Return the default inertial layered balanced-zonal advection dycore model."""
    from dynamaxx.dycore.models.inertial_layered_balanced_zonal_advection import (
        default_inertial_layered_balanced_zonal_advection_dycore_model,
    )

    return default_inertial_layered_balanced_zonal_advection_dycore_model()


def layered_balanced_zonal_advection_model() -> DycoreModel:
    """Return the default layered balanced-zonal advection dycore model."""
    from dynamaxx.dycore.models.layered_balanced_zonal_advection import (
        default_layered_balanced_zonal_advection_dycore_model,
    )

    return default_layered_balanced_zonal_advection_dycore_model()


def persistence_model() -> DycoreModel:
    """Return the default persistence dycore model."""
    from dynamaxx.dycore.models.persistence import default_persistence_dycore_model

    return default_persistence_dycore_model()


def pressure_inertia_layered_balanced_zonal_advection_model() -> DycoreModel:
    """Return the default pressure-inertia layered balanced-zonal dycore model."""
    from dynamaxx.dycore.models.pressure_inertia_layered_balanced_zonal_advection import (
        default_pressure_inertia_layered_balanced_zonal_advection_dycore_model,
    )

    return default_pressure_inertia_layered_balanced_zonal_advection_dycore_model()


def optical_flow_advection_model() -> DycoreModel:
    """Return the default optical-flow advection dycore model."""
    from dynamaxx.dycore.models.optical_flow_advection import (
        default_optical_flow_advection_dycore_model,
    )

    return default_optical_flow_advection_dycore_model()


def tendency_advection_model() -> DycoreModel:
    """Return the default tendency advection dycore model."""
    from dynamaxx.dycore.models.tendency_advection import (
        default_tendency_advection_dycore_model,
    )

    return default_tendency_advection_dycore_model()


def thermal_inertia_zonal_advection_model() -> DycoreModel:
    """Return the default thermal-inertia zonal advection dycore model."""
    from dynamaxx.dycore.models.thermal_inertia_zonal_advection import (
        default_thermal_inertia_zonal_advection_dycore_model,
    )

    return default_thermal_inertia_zonal_advection_dycore_model()


def transported_inertia_layered_balanced_zonal_advection_model() -> DycoreModel:
    """Return the default transported-inertia layered balanced-zonal dycore model."""
    from dynamaxx.dycore.models.transported_inertia_layered_balanced_zonal_advection import (
        default_transported_inertia_layered_balanced_zonal_advection_dycore_model,
    )

    return default_transported_inertia_layered_balanced_zonal_advection_dycore_model()


def thermal_inertia_geostrophic_advection_model() -> DycoreModel:
    """Return the default thermal-inertia geostrophic advection dycore model."""
    from dynamaxx.dycore.models.thermal_inertia_geostrophic_advection import (
        default_thermal_inertia_geostrophic_advection_dycore_model,
    )

    return default_thermal_inertia_geostrophic_advection_dycore_model()


def wind_advection_model() -> DycoreModel:
    """Return the default wind advection dycore model."""
    from dynamaxx.dycore.models.wind_advection import (
        default_wind_advection_dycore_model,
    )

    return default_wind_advection_dycore_model()


def zonal_advection_model() -> DycoreModel:
    """Return the default zonal advection dycore model."""
    from dynamaxx.dycore.models.zonal_advection import (
        default_zonal_advection_dycore_model,
    )

    return default_zonal_advection_dycore_model()


DYCORE_MODEL_FACTORIES: dict[str, DycoreModelFactory] = {
    "advected_persistence": advected_persistence_model,
    "barotropic_vorticity": barotropic_vorticity_model,
    "geostrophic_advection": geostrophic_advection_model,
    "inertial_layered_balanced_zonal_advection": (
        inertial_layered_balanced_zonal_advection_model
    ),
    "layered_balanced_zonal_advection": layered_balanced_zonal_advection_model,
    "optical_flow_advection": optical_flow_advection_model,
    "persistence": persistence_model,
    "pressure_inertia_layered_balanced_zonal_advection": (
        pressure_inertia_layered_balanced_zonal_advection_model
    ),
    "tendency_advection": tendency_advection_model,
    "thermal_inertia_geostrophic_advection": (
        thermal_inertia_geostrophic_advection_model
    ),
    "thermal_inertia_zonal_advection": thermal_inertia_zonal_advection_model,
    "transported_inertia_layered_balanced_zonal_advection": (
        transported_inertia_layered_balanced_zonal_advection_model
    ),
    "wind_advection": wind_advection_model,
    "zonal_advection": zonal_advection_model,
}


def dycore_model_names() -> tuple[str, ...]:
    """Return registered dycore model names."""
    return tuple(DYCORE_MODEL_FACTORIES)


def create_dycore_model(name: str) -> DycoreModel:
    """Create a registered dycore model by name."""
    assert name in DYCORE_MODEL_FACTORIES, f"unknown dycore model {name}"
    return DYCORE_MODEL_FACTORIES[name]()
