import pytest

from dynamaxx.registry import create_forecast_model, forecast_model_names


def test_registry_lists_default_forecast_models():
    assert forecast_model_names() == ("spectral_dycore",)


def test_registry_rejects_unknown_forecast_model():
    with pytest.raises(AssertionError, match="unknown forecast model"):
        create_forecast_model("missing")
