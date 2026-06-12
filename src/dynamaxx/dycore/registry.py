# Copyright 2026 dynamaxx

from collections.abc import Callable

from dynamaxx.dycore.api import DycoreModel

DycoreModelFactory = Callable[[], DycoreModel]


def spectral_dycore_model() -> DycoreModel:
    """Return the default spectral dycore model."""
    from dynamaxx.dycore.models.spectral import (
        default_spectral_dycore_model,
    )

    return default_spectral_dycore_model()


DYCORE_MODEL_FACTORIES: dict[str, DycoreModelFactory] = {
    "spectral_dycore": spectral_dycore_model,
}


def dycore_model_names() -> tuple[str, ...]:
    """Return registered dycore model names."""
    return tuple(DYCORE_MODEL_FACTORIES)


def create_dycore_model(name: str) -> DycoreModel:
    """Create a registered dycore model by name."""
    assert name in DYCORE_MODEL_FACTORIES, f"unknown dycore model {name}"
    return DYCORE_MODEL_FACTORIES[name]()
