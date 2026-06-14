# Copyright 2026 dynamaxx

import pytest

from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names


def test_registry_lists_default_dycore_models():
    """Registry should expose model names in stable display order."""
    assert dycore_model_names() == (
        "advected_persistence",
        "barotropic_vorticity",
        "geostrophic_advection",
        "inertial_layered_balanced_zonal_advection",
        "layered_balanced_zonal_advection",
        "optical_flow_advection",
        "persistence",
        "pressure_inertia_layered_balanced_zonal_advection",
        "tendency_advection",
        "thermal_inertia_geostrophic_advection",
        "thermal_inertia_zonal_advection",
        "transported_inertia_layered_balanced_zonal_advection",
        "wind_advection",
        "zonal_advection",
    )


def test_registry_rejects_unknown_dycore_model():
    """Unknown model names should fail clearly."""
    with pytest.raises(AssertionError, match="unknown dycore model"):
        create_dycore_model("missing")
