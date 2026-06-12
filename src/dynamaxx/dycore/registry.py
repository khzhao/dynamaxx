# Copyright 2026 dynamaxx

from collections.abc import Callable

ForecastModelFactory = Callable[[], object]


def spectral_dycore_forecast_model() -> object:
    """Return the default spectral dycore forecast model."""
    from dynamaxx.dycore.forecast import default_spectral_dycore_forecast_model

    return default_spectral_dycore_forecast_model()


FORECAST_MODEL_FACTORIES: dict[str, ForecastModelFactory] = {
    "spectral_dycore": spectral_dycore_forecast_model,
}


def forecast_model_names() -> tuple[str, ...]:
    """Return registered dycore forecast model names."""
    return tuple(FORECAST_MODEL_FACTORIES)


def create_forecast_model(name: str) -> object:
    """Create a registered dycore forecast model by name."""
    assert name in FORECAST_MODEL_FACTORIES, f"unknown forecast model {name}"
    return FORECAST_MODEL_FACTORIES[name]()
