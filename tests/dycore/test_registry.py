# Copyright 2026 dynamaxx

import pytest

from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names


def test_registry_lists_default_dycore_models():
    """The registry lists the default dycore models."""
    assert dycore_model_names() == ("persistence", "dinosaur")


def test_registry_creates_dinosaur_dycore_model():
    """The vendored Dinosaur dycore is registered under the canonical name."""
    assert create_dycore_model("dinosaur").name == "dinosaur"


def test_registry_rejects_unknown_dycore_model():
    """Unknown dycore names fail with the registry assertion."""
    with pytest.raises(AssertionError, match="unknown dycore model"):
        create_dycore_model("missing")
