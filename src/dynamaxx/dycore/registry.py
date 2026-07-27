# Copyright 2026 dynamaxx

"""Named constructors for the supported dynamical cores."""

from collections.abc import Callable

from dynamaxx.dycore.api import DycoreModel

_DycoreModelFactory = Callable[[], DycoreModel]


def _persistence_model() -> DycoreModel:
    from dynamaxx.dycore.models.persistence import default_persistence_dycore_model

    return default_persistence_dycore_model()


def _dinosaur_model() -> DycoreModel:
    from dynamaxx.dycore.models.dinosaur import default_dinosaur_dycore_model

    return default_dinosaur_dycore_model()


def _production_dinosaur_model() -> DycoreModel:
    from dynamaxx.dycore.models.dinosaur import production_dinosaur_dycore_model

    return production_dinosaur_dycore_model()


_DYCORE_MODEL_FACTORIES: dict[str, _DycoreModelFactory] = {
    "persistence": _persistence_model,
    "dinosaur": _dinosaur_model,
    "dino_rskin_apv": _production_dinosaur_model,
}


def dycore_model_names() -> tuple[str, ...]:
    """Return the supported dycore model names."""
    return tuple(_DYCORE_MODEL_FACTORIES)


def create_dycore_model(name: str) -> DycoreModel:
    """Create a supported dycore model by name."""
    try:
        factory = _DYCORE_MODEL_FACTORIES[name]
    except KeyError as error:
        supported = ", ".join(_DYCORE_MODEL_FACTORIES)
        raise ValueError(
            f"unknown dycore model {name!r}; expected one of: {supported}"
        ) from error
    return factory()
