# Copyright 2023 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Vendored Dinosaur dycore implementation used by Dynamaxx."""

from dynamaxx.dycore.models.dinosaur import (
    associated_legendre,
    coordinate_systems,
    filtering,
    fourier,
    held_suarez,
    horizontal_interpolation,
    hybrid_coordinates,
    jax_numpy_utils,
    layer_coordinates,
    leapfrog_utils,
    primitive_equations,
    primitive_equations_states,
    pytree_utils,
    radiation,
    scales,
    shallow_water,
    shallow_water_states,
    sigma_coordinates,
    spherical_harmonic,
    time_integration,
    typing,
    units,
    vertical_interpolation,
    weatherbench_utils,
    xarray_utils,
)
from dynamaxx.dycore.models.dinosaur.adapter import (
    DEFAULT_SEMI_IMPLICIT_OFFCENTERING,
    DinosaurPrimitiveEquationsDycoreModel,
    analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model,
    coriolis_split_dinosaur_dycore_model,
    coriolis_strang_split_dinosaur_dycore_model,
    default_dinosaur_dycore_model,
    digital_filter_dinosaur_dycore_model,
    digital_filter_surface_residual_dinosaur_dycore_model,
    hydrostatic_temperature_initialization_dinosaur_dycore_model,
    land_sea_surface_temperature_dinosaur_dycore_model,
    layer_mean_hydrostatic_temperature_initialization_dinosaur_dycore_model,
    log_pressure_initialization_dinosaur_dycore_model,
    richardson_10m_wind_diagnostic_dinosaur_dycore_model,
    scale_separated_surface_residual_dinosaur_dycore_model,
    semi_implicit_offcenter_dinosaur_dycore_model,
    stability_aware_surface_residual_dinosaur_dycore_model,
    theta_mean_recenter_dinosaur_dycore_model,
    theta_tendency_dinosaur_dycore_model,
    weak_held_suarez_dinosaur_dycore_model,
)

__version__ = "1.3.6"
UPSTREAM_PACKAGE = "dinosaur"
UPSTREAM_VERSION = "1.3.6"

__all__ = [
    "UPSTREAM_PACKAGE",
    "UPSTREAM_VERSION",
    "__version__",
    "DEFAULT_SEMI_IMPLICIT_OFFCENTERING",
    "DinosaurPrimitiveEquationsDycoreModel",
    "analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model",
    "associated_legendre",
    "coordinate_systems",
    "coriolis_split_dinosaur_dycore_model",
    "coriolis_strang_split_dinosaur_dycore_model",
    "default_dinosaur_dycore_model",
    "digital_filter_dinosaur_dycore_model",
    "digital_filter_surface_residual_dinosaur_dycore_model",
    "filtering",
    "fourier",
    "held_suarez",
    "hydrostatic_temperature_initialization_dinosaur_dycore_model",
    "horizontal_interpolation",
    "hybrid_coordinates",
    "jax_numpy_utils",
    "land_sea_surface_temperature_dinosaur_dycore_model",
    "layer_mean_hydrostatic_temperature_initialization_dinosaur_dycore_model",
    "layer_coordinates",
    "leapfrog_utils",
    "log_pressure_initialization_dinosaur_dycore_model",
    "primitive_equations",
    "primitive_equations_states",
    "pytree_utils",
    "radiation",
    "richardson_10m_wind_diagnostic_dinosaur_dycore_model",
    "scales",
    "scale_separated_surface_residual_dinosaur_dycore_model",
    "semi_implicit_offcenter_dinosaur_dycore_model",
    "shallow_water",
    "shallow_water_states",
    "sigma_coordinates",
    "spherical_harmonic",
    "stability_aware_surface_residual_dinosaur_dycore_model",
    "theta_mean_recenter_dinosaur_dycore_model",
    "theta_tendency_dinosaur_dycore_model",
    "time_integration",
    "typing",
    "units",
    "vertical_interpolation",
    "weatherbench_utils",
    "weak_held_suarez_dinosaur_dycore_model",
    "xarray_utils",
]
