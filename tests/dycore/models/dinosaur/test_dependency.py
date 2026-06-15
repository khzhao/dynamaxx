# Copyright 2026 dynamaxx

import os
import subprocess
import sys

from dynamaxx.dycore.models.dinosaur import (
    UPSTREAM_VERSION,
    hybrid_coordinates,
    primitive_equations,
)
from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names


def test_dinosaur_imports_without_external_dinosaur_package():
    """The vendored dycore runs when top-level Dinosaur imports are blocked."""
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
from dynamaxx.dycore.models.dinosaur import (
    DinosaurPrimitiveEquationsDycoreModel,
    hybrid_coordinates,
)
from dynamaxx.weather import ForecastInput, WeatherState
import jax.numpy as jnp
import numpy as np

assert dinosaur.default_dinosaur_dycore_model().name == "dinosaur"
assert hybrid_coordinates.HybridCoordinates.ECMWF137().layers == 137

fields = {
    "temperature_250": 250.0,
    "temperature_750": 285.0,
    "u_component_of_wind_250": 0.0,
    "u_component_of_wind_750": 0.0,
    "v_component_of_wind_250": 0.0,
    "v_component_of_wind_750": 0.0,
    "mean_sea_level_pressure": 100000.0,
}
initial_state = WeatherState(
    values=jnp.stack(
        [
            jnp.full((1, 4, 3), fill_value, dtype=jnp.float32)
            for fill_value in fields.values()
        ],
        axis=1,
    ),
    variables=tuple(fields),
)
forecast_input = ForecastInput(
    initial_times=np.array(["2020-01-01T00:00:00"], dtype="datetime64[ns]"),
    valid_times=np.array([["2020-01-01T00:00:00"]], dtype="datetime64[ns]"),
    lead_steps=(0,),
    lead_hours=(0,),
    step_seconds=3600.0,
    longitude=np.array([0.0, 90.0, 180.0, 270.0]),
    latitude=np.array([90.0, 0.0, -90.0]),
    initial_state=initial_state,
)
forecast = DinosaurPrimitiveEquationsDycoreModel(
    inner_step_seconds=3600.0,
    output_variables=("temperature_250",),
    include_vertical_advection=False,
    jit_forecast=False,
).forecast(forecast_input)
assert forecast.values.shape == (1, 1, 1, 4, 3)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        env={**os.environ, "JAX_PLATFORMS": "cpu"},
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_dinosaur_is_registered_as_canonical_dycore_model():
    """The registry exposes the vendored Dinosaur dycore under its final name."""
    assert dycore_model_names() == ("persistence", "dinosaur")

    model = create_dycore_model("dinosaur")

    assert model.name == "dinosaur"


def test_dinosaur_has_local_runtime_modules_and_data():
    """The vendored runtime resolves classes and data from Dynamaxx."""
    assert UPSTREAM_VERSION == "1.3.6"
    assert primitive_equations.PrimitiveEquations.__module__ == (
        "dynamaxx.dycore.models.dinosaur.primitive_equations"
    )

    ecmwf_coordinates = hybrid_coordinates.HybridCoordinates.ECMWF137()

    assert ecmwf_coordinates.layers == 137
    assert ecmwf_coordinates.a_boundaries.shape == (138,)
    assert ecmwf_coordinates.b_boundaries.shape == (138,)
