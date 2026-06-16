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
    assert not create_dycore_model(
        "dinosaur_dfi_surface_residual"
    ).apply_weak_held_suarez_relaxation


def test_registry_rejects_unknown_dycore_model():
    """Unknown dycore names fail with the registry assertion."""
    with pytest.raises(AssertionError, match="unknown dycore model"):
        create_dycore_model("missing")
