import pytest

from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names


def test_registry_lists_default_dycore_models():
    assert dycore_model_names() == ("persistence",)


def test_registry_rejects_unknown_dycore_model():
    with pytest.raises(AssertionError, match="unknown dycore model"):
        create_dycore_model("missing")
