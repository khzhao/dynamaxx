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


DYCORE_MODEL_FACTORIES: dict[str, DycoreModelFactory] = {
    "persistence": persistence_model,
    "dinosaur": dinosaur_model,
}


def dycore_model_names() -> tuple[str, ...]:
    """Return registered dycore model names."""
    return tuple(DYCORE_MODEL_FACTORIES)


def create_dycore_model(name: str) -> DycoreModel:
    """Create a registered dycore model by name."""
    assert name in DYCORE_MODEL_FACTORIES, f"unknown dycore model {name}"
    return DYCORE_MODEL_FACTORIES[name]()
