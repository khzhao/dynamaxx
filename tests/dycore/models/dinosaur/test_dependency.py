# Copyright 2026 dynamaxx

import os
import subprocess
import sys

from dynamaxx.dycore.models.dinosaur import (
    UPSTREAM_VERSION,
    hybrid_coordinates,
    primitive_equations,
)


def test_vendored_dinosaur_does_not_require_external_package():
    """The local runtime imports with the external Dinosaur package blocked."""
    script = """
import importlib.abc


class BlockExternalDinosaur(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "dinosaur" or fullname.startswith("dinosaur."):
            raise ImportError(f"blocked external Dinosaur import: {fullname}")
        return None


import sys
sys.meta_path.insert(0, BlockExternalDinosaur())

from dynamaxx.dycore.models import dinosaur

assert dinosaur.default_dinosaur_dycore_model().name == "dinosaur"
assert dinosaur.production_dinosaur_dycore_model().name == "dino_rskin_apv"
assert dinosaur.hybrid_coordinates.HybridCoordinates.ECMWF137().layers == 137
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        env={**os.environ, "JAX_PLATFORMS": "cpu"},
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_dinosaur_runtime_modules_and_data_are_local():
    """Runtime modules and bundled vertical-coordinate data stay local."""
    assert UPSTREAM_VERSION == "1.3.6"
    assert primitive_equations.PrimitiveEquations.__module__ == (
        "dynamaxx.dycore.models.dinosaur.primitive_equations"
    )

    ecmwf_coordinates = hybrid_coordinates.HybridCoordinates.ECMWF137()

    assert ecmwf_coordinates.layers == 137
    assert ecmwf_coordinates.a_boundaries.shape == (138,)
    assert ecmwf_coordinates.b_boundaries.shape == (138,)
