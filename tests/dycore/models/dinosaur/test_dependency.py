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
assert dinosaur.weak_held_suarez_dinosaur_dycore_model().name == (
    "dinosaur_dfi_surface_residual_weak_hs"
)
assert dinosaur.log_pressure_initialization_dinosaur_dycore_model().name == (
    "dinosaur_dfi_surface_residual_weak_hs_logp_init"
)
assert dinosaur.hydrostatic_temperature_initialization_dinosaur_dycore_model().name == (
    "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init"
)
assert (
    dinosaur.layer_mean_hydrostatic_temperature_initialization_dinosaur_dycore_model().name
    == "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init"
)
assert (
    dinosaur.coriolis_split_dinosaur_dycore_model().name
    == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
    "hydrostatic_layer_init_coriolis_split"
)
assert (
    dinosaur.coriolis_strang_split_dinosaur_dycore_model().name
    == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
    "hydrostatic_layer_init_coriolis_strang"
)
assert (
    dinosaur.stability_aware_surface_residual_dinosaur_dycore_model().name
    == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
    "hydrostatic_layer_init_coriolis_strang_stability_surface_residual"
)
assert (
    dinosaur.richardson_10m_wind_diagnostic_dinosaur_dycore_model().name
    == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
    "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
    "ri_10m_wind"
)
assert (
    dinosaur.theta_tendency_dinosaur_dycore_model().name
    == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
    "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
    "ri_10m_wind_theta_tendency"
)
assert (
    dinosaur.theta_mean_recenter_dinosaur_dycore_model().name
    == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
    "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
    "ri_10m_wind_theta_tendency_theta_mean_recenter"
)
assert (
    dinosaur.semi_implicit_offcenter_dinosaur_dycore_model().name
    == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
    "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
    "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter"
)
assert (
    dinosaur.scale_separated_surface_residual_dinosaur_dycore_model().name
    == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
    "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
    "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
    "scale_surface_residual"
)
assert (
    dinosaur.analysis_offset_held_suarez_equilibrium_dinosaur_dycore_model().name
    == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
    "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
    "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
    "scale_surface_residual_analysis_hs_eq"
)
assert (
    dinosaur.land_sea_surface_temperature_dinosaur_dycore_model().name
    == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
    "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
    "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
    "scale_surface_residual_analysis_hs_eq_landsea_surface"
)
assert (
    dinosaur.ocean_bulk_sensible_heat_flux_dinosaur_dycore_model().name
    == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
    "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
    "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
    "scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf"
)
assert dinosaur.horizontal_semilagrangian_theta_transport_dinosaur_dycore_model().name == (
    "dino_hsl_theta"
)
assert dinosaur.midpoint_semilagrangian_theta_departure_dinosaur_dycore_model().name == (
    "dino_hsl2_theta"
)
assert dinosaur.dry_static_energy_hsl_transport_dinosaur_dycore_model().name == (
    "dino_hsl2_theta_dse_hsl"
)
assert dinosaur.layer_mass_weighted_dse_hsl_transport_dinosaur_dycore_model().name == (
    "dino_hsl2_mass_dse"
)
assert dinosaur.tropical_wtg_mass_dse_relaxation_dinosaur_dycore_model().name == (
    "dino_hsl2_mass_dse_wtg"
)
assert dinosaur.pressure_ramped_vertical_dse_wtg_dinosaur_dycore_model().name == (
    "dino_hsl2_mass_dse_wtg_vdse_ramp"
)
assert dinosaur.land_ocean_low_mode_t2m_memory_dinosaur_dycore_model().name == (
    "dino_hsl2_mass_dse_wtg_vdse_t2m_lomem"
)
assert (
    dinosaur.bulk_richardson_2m_temperature_diagnostic_dinosaur_dycore_model().name
    == "dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m"
)
assert dinosaur.ekman_coupled_dinosaur_dycore_model().name == (
    "dino_ri2m_ekman_coupled"
)
assert dinosaur.ekman_depth_dinosaur_dycore_model().name == "dino_ri2m_ekman_depth"
assert dinosaur.orographic_lift_theta_dinosaur_dycore_model().name == (
    "dino_ri2m_ekman_depth_orolift_theta"
)
assert dinosaur.orographic_lift_lower_column_wind_dinosaur_dycore_model().name == (
    "dino_ri2m_ekman_depth_orolift_lwind"
)
assert dinosaur.terrain_work_form_drag_heating_dinosaur_dycore_model().name == (
    "dino_ri2m_ekman_depth_orolift_lwind_twork_drag"
)
assert dinosaur.pressure_thickness_ri2m_temperature_dinosaur_dycore_model().name == (
    "dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m"
)
assert dinosaur.late_ramped_land_skin_reservoir_dinosaur_dycore_model().name == (
    "dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin"
)
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
    assert dycore_model_names() == (
        "persistence",
        "dinosaur",
        "dinosaur_dfi",
        "dinosaur_dfi_surface_residual",
        "dinosaur_dfi_surface_residual_weak_hs",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_split",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface",
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf",
        "dino_hsl_theta",
        "dino_hsl2_theta",
        "dino_hsl2_theta_dse_hsl",
        "dino_hsl2_mass_dse",
        "dino_hsl2_mass_dse_wtg",
        "dino_hsl2_mass_dse_wtg_vdse_ramp",
        "dino_hsl2_mass_dse_wtg_vdse_t2m_lomem",
        "dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m",
        "dino_ri2m_ekman_coupled",
        "dino_ri2m_ekman_depth",
        "dino_ri2m_ekman_depth_orolift_theta",
        "dino_ri2m_ekman_depth_orolift_lwind",
        "dino_ri2m_ekman_depth_orolift_lwind_twork_drag",
        "dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m",
        "dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin",
    )

    model = create_dycore_model("dinosaur")

    assert model.name == "dinosaur"
    assert not model.apply_digital_filter_initialization
    assert not model.apply_near_surface_residual_correction


def test_dinosaur_dfi_is_registered_as_side_by_side_candidate():
    """The DFI candidate is available without replacing canonical Dinosaur."""
    model = create_dycore_model("dinosaur_dfi")

    assert model.name == "dinosaur_dfi"
    assert model.apply_digital_filter_initialization
    assert not model.apply_near_surface_residual_correction


def test_dinosaur_dfi_surface_residual_is_registered_as_candidate():
    """The residual candidate is available without replacing DFI."""
    model = create_dycore_model("dinosaur_dfi_surface_residual")

    assert model.name == "dinosaur_dfi_surface_residual"
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction


def test_dinosaur_weak_held_suarez_is_registered_as_candidate():
    """The weak HS candidate preserves the accepted incumbent mechanisms."""
    model = create_dycore_model("dinosaur_dfi_surface_residual_weak_hs")

    assert model.name == "dinosaur_dfi_surface_residual_weak_hs"
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert not model.use_log_pressure_initialization


def test_dinosaur_log_pressure_initialization_is_registered_as_candidate():
    """The log-pressure candidate is available without replacing the incumbent."""
    model = create_dycore_model("dinosaur_dfi_surface_residual_weak_hs_logp_init")
    incumbent = create_dycore_model("dinosaur_dfi_surface_residual_weak_hs")

    assert model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init"
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == 80
    assert model.apply_spectral_filter
    assert model.horizontal_diffusion_order == 2
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection
    assert not incumbent.use_log_pressure_initialization


def test_dinosaur_hydrostatic_initialization_is_registered_as_candidate():
    """The hydrostatic candidate preserves the accepted incumbent mechanisms."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init"
    )
    incumbent = create_dycore_model("dinosaur_dfi_surface_residual_weak_hs_logp_init")

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == 80
    assert model.apply_spectral_filter
    assert model.horizontal_diffusion_order == 2
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection
    assert not incumbent.use_hydrostatic_temperature_initialization


def test_dinosaur_layer_mean_hydrostatic_initialization_is_registered():
    """The layer-mean candidate preserves the accepted incumbent mechanisms."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init"
    )

    assert (
        model.name
        == "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == 80
    assert model.apply_spectral_filter
    assert model.horizontal_diffusion_order == 2
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection
    assert not incumbent.use_layer_mean_hydrostatic_temperature_initialization


def test_dinosaur_coriolis_split_is_registered():
    """The exact-Coriolis split is side-by-side with the layer-mean incumbent."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_split"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_split"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert not incumbent.apply_exact_coriolis_rotation_split


def test_dinosaur_coriolis_strang_split_is_registered():
    """The symmetric exact-Coriolis split is side-by-side with the incumbent."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_split"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert not incumbent.apply_symmetric_exact_coriolis_rotation_split


def test_dinosaur_stability_aware_surface_residual_is_registered():
    """The stability-aware residual decay candidate is side-by-side."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.use_stability_aware_near_surface_residual_decay
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert not incumbent.use_stability_aware_near_surface_residual_decay


def test_dinosaur_richardson_10m_wind_diagnostic_is_registered():
    """The Richardson diagnostic candidate is side-by-side with the incumbent."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.use_stability_aware_near_surface_residual_decay
    assert model.use_surface_layer_richardson_10m_wind_diagnostic
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert not incumbent.use_surface_layer_richardson_10m_wind_diagnostic


def test_dinosaur_theta_tendency_is_registered():
    """The theta-tendency candidate is side-by-side with the incumbent."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.use_stability_aware_near_surface_residual_decay
    assert model.use_surface_layer_richardson_10m_wind_diagnostic
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert model.temperature_tendency_formulation == "potential_temperature"
    assert incumbent.temperature_tendency_formulation == "temperature"


def test_dinosaur_theta_mean_recenter_is_registered():
    """The theta recentering candidate is side-by-side with the incumbent."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.use_stability_aware_near_surface_residual_decay
    assert model.use_surface_layer_richardson_10m_wind_diagnostic
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert model.temperature_tendency_formulation == "potential_temperature"
    assert model.apply_theta_layer_mean_recentering
    assert not incumbent.apply_theta_layer_mean_recentering


def test_dinosaur_semi_implicit_offcenter_is_registered():
    """The SIL3 off-centering candidate is side-by-side with the incumbent."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.use_stability_aware_near_surface_residual_decay
    assert model.use_surface_layer_richardson_10m_wind_diagnostic
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert model.use_layer_mean_hydrostatic_temperature_initialization
    assert model.apply_exact_coriolis_rotation_split
    assert model.apply_symmetric_exact_coriolis_rotation_split
    assert model.temperature_tendency_formulation == "potential_temperature"
    assert model.apply_theta_layer_mean_recentering
    assert model.semi_implicit_offcentering == 0.05
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "semi_implicit_offcentering"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_analysis_offset_hs_eq_is_registered():
    """The analysis-offset HS equilibrium candidate is side-by-side."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq"
    )
    assert model.use_analysis_offset_weak_held_suarez_equilibrium
    assert not incumbent.use_analysis_offset_weak_held_suarez_equilibrium
    for field_name in model.__dataclass_fields__:
        if field_name in {
            "name",
            "use_analysis_offset_weak_held_suarez_equilibrium",
        }:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_land_sea_surface_temperature_is_registered():
    """The land-sea T2m residual candidate is side-by-side."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface"
    )
    assert model.use_land_sea_surface_temperature_residual
    assert not incumbent.use_land_sea_surface_temperature_residual
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_land_sea_surface_temperature_residual"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_ocean_bulk_shf_is_registered():
    """The ocean bulk SHF candidate is side-by-side with the incumbent."""
    model = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf"
    )
    incumbent = create_dycore_model(
        "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface"
    )

    assert (
        model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init_"
        "hydrostatic_layer_init_coriolis_strang_stability_surface_residual_"
        "ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_"
        "scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf"
    )
    assert model.apply_ocean_bulk_sensible_heat_flux
    assert not incumbent.apply_ocean_bulk_sensible_heat_flux
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "apply_ocean_bulk_sensible_heat_flux"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_dse_hsl_is_registered():
    """The DSE-HSL candidate is side-by-side with the HSL2 theta incumbent."""
    model = create_dycore_model("dino_hsl2_theta_dse_hsl")
    incumbent = create_dycore_model("dino_hsl2_theta")

    assert model.name == "dino_hsl2_theta_dse_hsl"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert incumbent.use_horizontal_semilagrangian_theta_transport
    assert incumbent.use_midpoint_semilagrangian_theta_departure
    assert not incumbent.use_dry_static_energy_hsl_transport
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_dry_static_energy_hsl_transport"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_layer_mass_dse_is_registered():
    """The mass-DSE candidate is side-by-side with the DSE-HSL incumbent."""
    model = create_dycore_model("dino_hsl2_mass_dse")
    incumbent = create_dycore_model("dino_hsl2_theta_dse_hsl")

    assert model.name == "dino_hsl2_mass_dse"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert incumbent.use_dry_static_energy_hsl_transport
    assert not incumbent.use_layer_mass_weighted_dse_hsl_transport
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_layer_mass_weighted_dse_hsl_transport"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_tropical_wtg_mass_dse_is_registered():
    """The WTG candidate is side-by-side with the mass-DSE incumbent."""
    model = create_dycore_model("dino_hsl2_mass_dse_wtg")
    incumbent = create_dycore_model("dino_hsl2_mass_dse")

    assert model.name == "dino_hsl2_mass_dse_wtg"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert not incumbent.apply_tropical_wtg_mass_dse_relaxation
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "apply_tropical_wtg_mass_dse_relaxation"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_pressure_ramped_vertical_dse_wtg_is_registered():
    """The vertical-DSE ramp candidate is side-by-side with the WTG incumbent."""
    model = create_dycore_model("dino_hsl2_mass_dse_wtg_vdse_ramp")
    incumbent = create_dycore_model("dino_hsl2_mass_dse_wtg")

    assert model.name == "dino_hsl2_mass_dse_wtg_vdse_ramp"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert model.use_pressure_ramped_vertical_dse_increment
    assert not incumbent.use_pressure_ramped_vertical_dse_increment
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_pressure_ramped_vertical_dse_increment"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_land_ocean_low_mode_t2m_memory_is_registered():
    """The broad T2m memory candidate is side-by-side with the ramp incumbent."""
    model = create_dycore_model("dino_hsl2_mass_dse_wtg_vdse_t2m_lomem")
    incumbent = create_dycore_model("dino_hsl2_mass_dse_wtg_vdse_ramp")

    assert model.name == "dino_hsl2_mass_dse_wtg_vdse_t2m_lomem"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert model.use_pressure_ramped_vertical_dse_increment
    assert model.use_land_ocean_low_mode_t2m_memory
    assert not incumbent.use_land_ocean_low_mode_t2m_memory
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_land_ocean_low_mode_t2m_memory"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_bulk_richardson_2m_temperature_is_registered():
    """The bounded raw T2m diagnostic is side-by-side with the incumbent."""
    model = create_dycore_model("dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m")
    incumbent = create_dycore_model("dino_hsl2_mass_dse_wtg_vdse_t2m_lomem")

    assert model.name == "dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert model.use_pressure_ramped_vertical_dse_increment
    assert model.use_land_ocean_low_mode_t2m_memory
    assert model.use_bulk_richardson_2m_temperature_diagnostic
    assert not incumbent.use_bulk_richardson_2m_temperature_diagnostic
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_bulk_richardson_2m_temperature_diagnostic"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_ekman_coupled_model_is_registered():
    """The coupled Ekman candidate is side-by-side with the RI2m incumbent."""
    model = create_dycore_model("dino_ri2m_ekman_coupled")
    incumbent = create_dycore_model("dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m")

    assert model.name == "dino_ri2m_ekman_coupled"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert model.use_pressure_ramped_vertical_dse_increment
    assert model.use_land_ocean_low_mode_t2m_memory
    assert model.use_bulk_richardson_2m_temperature_diagnostic
    assert model.apply_coupled_ekman_surface_closure
    assert not incumbent.apply_coupled_ekman_surface_closure
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "apply_coupled_ekman_surface_closure"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_ekman_depth_model_is_registered():
    """The Coriolis-depth Ekman candidate is side-by-side with the incumbent."""
    model = create_dycore_model("dino_ri2m_ekman_depth")
    incumbent = create_dycore_model("dino_ri2m_ekman_coupled")

    assert model.name == "dino_ri2m_ekman_depth"
    assert model.use_horizontal_semilagrangian_theta_transport
    assert model.use_midpoint_semilagrangian_theta_departure
    assert model.use_dry_static_energy_hsl_transport
    assert model.use_layer_mass_weighted_dse_hsl_transport
    assert model.apply_tropical_wtg_mass_dse_relaxation
    assert model.use_pressure_ramped_vertical_dse_increment
    assert model.use_land_ocean_low_mode_t2m_memory
    assert model.use_bulk_richardson_2m_temperature_diagnostic
    assert model.apply_coupled_ekman_surface_closure
    assert model.use_coriolis_scaled_ekman_depth
    assert not incumbent.use_coriolis_scaled_ekman_depth
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_coriolis_scaled_ekman_depth"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_orographic_lift_theta_model_is_registered():
    """The orographic lift thermal candidate is side-by-side with incumbent."""
    model = create_dycore_model("dino_ri2m_ekman_depth_orolift_theta")
    incumbent = create_dycore_model("dino_ri2m_ekman_depth")

    assert model.name == "dino_ri2m_ekman_depth_orolift_theta"
    assert model.apply_orographic_lift_theta_tendency
    assert not incumbent.apply_orographic_lift_theta_tendency
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "apply_orographic_lift_theta_tendency"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_orographic_lift_lower_column_wind_model_is_registered():
    """The lower-column terrain-wind candidate preserves orographic lift."""
    model = create_dycore_model("dino_ri2m_ekman_depth_orolift_lwind")
    incumbent = create_dycore_model("dino_ri2m_ekman_depth_orolift_theta")

    assert model.name == "dino_ri2m_ekman_depth_orolift_lwind"
    assert model.apply_orographic_lift_theta_tendency
    assert model.use_depth_weighted_orographic_lift_wind
    assert not incumbent.use_depth_weighted_orographic_lift_wind
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "use_depth_weighted_orographic_lift_wind"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_terrain_work_form_drag_model_is_registered():
    """The terrain-work drag candidate preserves lower-column orographic lift."""
    model = create_dycore_model("dino_ri2m_ekman_depth_orolift_lwind_twork_drag")
    incumbent = create_dycore_model("dino_ri2m_ekman_depth_orolift_lwind")

    assert model.name == "dino_ri2m_ekman_depth_orolift_lwind_twork_drag"
    assert model.apply_orographic_lift_theta_tendency
    assert model.use_depth_weighted_orographic_lift_wind
    assert model.apply_terrain_work_form_drag_heating
    assert not incumbent.apply_terrain_work_form_drag_heating
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "apply_terrain_work_form_drag_heating"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_pressure_thickness_ri2m_model_is_registered():
    """The weighted RI2m T2m candidate preserves the terrain-work incumbent."""
    model = create_dycore_model(
        "dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m"
    )
    incumbent = create_dycore_model("dino_ri2m_ekman_depth_orolift_lwind_twork_drag")

    assert model.name == "dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m"
    assert model.use_bulk_richardson_2m_temperature_diagnostic
    assert model.apply_terrain_work_form_drag_heating
    assert model.use_pressure_thickness_weighted_ri2m_temperature
    assert not incumbent.use_pressure_thickness_weighted_ri2m_temperature
    for field_name in model.__dataclass_fields__:
        if field_name in {
            "name",
            "use_pressure_thickness_weighted_ri2m_temperature",
        }:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


def test_dinosaur_late_skin_model_is_registered():
    """The late-ramped reservoir preserves the pressure-thickness incumbent."""
    model = create_dycore_model(
        "dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin"
    )
    incumbent = create_dycore_model(
        "dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m"
    )

    assert model.apply_land_skin_reservoir
    assert not incumbent.apply_land_skin_reservoir
    for field_name in model.__dataclass_fields__:
        if field_name in {"name", "apply_land_skin_reservoir"}:
            continue
        assert getattr(model, field_name) == getattr(incumbent, field_name)


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
