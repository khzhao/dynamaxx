# Copyright 2026 dynamaxx

from dataclasses import replace
from typing import Any, cast

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from dynamaxx.dycore.models.dinosaur import (
    held_suarez,
    primitive_equations,
    scales,
    sigma_coordinates,
    spherical_harmonic,
    time_integration,
    units,
    vertical_interpolation,
)
from dynamaxx.dycore.models.dinosaur.adapter import (
    _DRY_AIR_GAS_CONSTANT_SI,
    DEFAULT_INNER_STEP_SECONDS,
    DEFAULT_SPECTRAL_WAVENUMBERS,
    DEFAULT_WEAK_HELD_SUAREZ_KA_TIMESCALE_DAYS,
    DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY,
    DEFAULT_WEAK_HELD_SUAREZ_KS_TIMESCALE_DAYS,
    DinosaurPrimitiveEquationsDycoreModel,
    _apply_near_surface_residual_correction,
    _compose_weak_held_suarez_equation,
    _horizontal_diffusion_step_filter,
    _hydrostatic_temperature_from_geopotential_thickness,
    _inner_steps_per_forecast_step,
    _interp_sigma_to_pressure_by_time,
    _layer_mean_hydrostatic_temperature_from_geopotential_thickness,
    _nondimensionalize_seconds,
    _pressure_coordinates,
    _primitive_equation,
    _primitive_equation_state,
    _reference_temperature,
    _TracerSafeHeldSuarezForcingSigma,
    _unit_factor,
    digital_filter_dinosaur_dycore_model,
    digital_filter_surface_residual_dinosaur_dycore_model,
    dinosaur_state_to_weather_state,
    hydrostatic_temperature_initialization_dinosaur_dycore_model,
    infer_dinosaur_pressure_levels,
    layer_mean_hydrostatic_temperature_initialization_dinosaur_dycore_model,
    log_pressure_initialization_dinosaur_dycore_model,
    split_pressure_level_channel,
    supported_output_variables,
    weak_held_suarez_dinosaur_dycore_model,
    weather_state_to_dinosaur_state,
)
from dynamaxx.dycore.models.dinosaur.coordinates import grid_metadata
from dynamaxx.utils.consts import SECONDS_PER_HOUR
from dynamaxx.weather import ForecastInput, WeatherState


def test_split_pressure_level_channel_keeps_non_pressure_suffixes():
    """Pressure-level parsing ignores non-pressure numeric suffixes."""
    assert split_pressure_level_channel("temperature_500") == ("temperature", 500)
    assert split_pressure_level_channel("soil_temperature_level_4") == (
        "soil_temperature_level_4",
        None,
    )


def test_infer_dinosaur_pressure_levels_requires_temperature_and_winds():
    """Pressure levels require temperature and horizontal wind channels."""
    levels = infer_dinosaur_pressure_levels(
        (
            "temperature_500",
            "temperature_850",
            "u_component_of_wind_500",
            "u_component_of_wind_850",
            "v_component_of_wind_500",
            "v_component_of_wind_850",
        )
    )

    assert levels == (500, 850)

    with pytest.raises(AssertionError, match="pressure-level temperature"):
        infer_dinosaur_pressure_levels(("temperature_500",))


def test_supported_output_variables_filters_to_dinosaur_outputs():
    """Supported output filtering keeps only Dinosaur-emittable channels."""
    variables = supported_output_variables(
        (
            "temperature_500",
            "u_component_of_wind_500",
            "v_component_of_wind_500",
            "geopotential_500",
            "2m_temperature",
            "10m_u_component_of_wind",
            "mean_sea_level_pressure",
            "total_precipitation",
        ),
        pressure_levels_hpa=(500,),
        has_humidity=False,
        requested_variables=None,
    )

    assert variables == (
        "temperature_500",
        "u_component_of_wind_500",
        "v_component_of_wind_500",
        "geopotential_500",
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
    )


def test_default_dinosaur_configuration_keeps_t80_with_stable_inner_step():
    """Default Dinosaur settings keep T80 while using a stable inner step."""
    model = DinosaurPrimitiveEquationsDycoreModel()

    assert model.spectral_wavenumbers == DEFAULT_SPECTRAL_WAVENUMBERS == 80
    assert model.inner_step_seconds == DEFAULT_INNER_STEP_SECONDS == 900.0
    assert not model.apply_digital_filter_initialization
    assert model.digital_filter_time_span_seconds == 6 * SECONDS_PER_HOUR
    assert model.digital_filter_cutoff_seconds == 6 * SECONDS_PER_HOUR
    assert not model.apply_near_surface_residual_correction
    assert model.near_surface_residual_decay_hours == 48.0
    assert not model.use_log_pressure_initialization
    assert not model.apply_weak_held_suarez_relaxation
    assert model.weak_held_suarez_kf_per_day == DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY
    assert (
        model.weak_held_suarez_ka_timescale_days
        == DEFAULT_WEAK_HELD_SUAREZ_KA_TIMESCALE_DAYS
    )
    assert (
        model.weak_held_suarez_ks_timescale_days
        == DEFAULT_WEAK_HELD_SUAREZ_KS_TIMESCALE_DAYS
    )
    assert (
        _inner_steps_per_forecast_step(
            step_seconds=6 * SECONDS_PER_HOUR,
            inner_step_seconds=model.inner_step_seconds,
        )
        == 24
    )


def test_digital_filter_dinosaur_factory_enables_fixed_initialization():
    """The DFI candidate opts into the fixed short Lanczos initialization."""
    model = digital_filter_dinosaur_dycore_model()

    assert model.name == "dinosaur_dfi"
    assert model.apply_digital_filter_initialization
    assert not model.apply_near_surface_residual_correction
    assert model.digital_filter_time_span_seconds == 6 * SECONDS_PER_HOUR
    assert model.digital_filter_cutoff_seconds == 6 * SECONDS_PER_HOUR


def test_digital_filter_surface_residual_factory_enables_guarded_correction():
    """The near-surface residual candidate preserves DFI and opts into correction."""
    model = digital_filter_surface_residual_dinosaur_dycore_model()

    assert model.name == "dinosaur_dfi_surface_residual"
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.near_surface_residual_decay_hours == 48.0


def test_weak_held_suarez_factory_preserves_incumbent_corrections():
    """The weak HS candidate keeps DFI and near-surface residual correction."""
    model = weak_held_suarez_dinosaur_dycore_model()

    assert model.name == "dinosaur_dfi_surface_residual_weak_hs"
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert not model.use_log_pressure_initialization
    assert model.weak_held_suarez_kf_per_day == 0.0
    assert model.weak_held_suarez_ka_timescale_days == 160.0
    assert model.weak_held_suarez_ks_timescale_days == 16.0


def test_log_pressure_initialization_factory_preserves_incumbent_settings():
    """The log-pressure candidate keeps the accepted weak HS configuration."""
    model = log_pressure_initialization_dinosaur_dycore_model()
    incumbent = weak_held_suarez_dinosaur_dycore_model()

    assert model.name == "dinosaur_dfi_surface_residual_weak_hs_logp_init"
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert not incumbent.use_log_pressure_initialization
    assert model.inner_step_seconds == DEFAULT_INNER_STEP_SECONDS == 900.0
    assert model.spectral_wavenumbers == DEFAULT_SPECTRAL_WAVENUMBERS == 80
    assert model.apply_spectral_filter
    assert model.horizontal_diffusion_order == 2
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection
    assert model.reference_temperature_kelvin == 250.0
    assert model.output_variables is None
    assert model.weak_held_suarez_kf_per_day == 0.0
    assert model.weak_held_suarez_ka_timescale_days == 160.0
    assert model.weak_held_suarez_ks_timescale_days == 16.0


def test_hydrostatic_temperature_initialization_factory_extends_incumbent():
    """The hydrostatic candidate preserves incumbent settings and adds one flag."""
    model = hydrostatic_temperature_initialization_dinosaur_dycore_model()
    incumbent = log_pressure_initialization_dinosaur_dycore_model()

    assert (
        model.name
        == "dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init"
    )
    assert model.apply_digital_filter_initialization
    assert model.apply_near_surface_residual_correction
    assert model.apply_weak_held_suarez_relaxation
    assert model.use_log_pressure_initialization
    assert model.use_hydrostatic_temperature_initialization
    assert not incumbent.use_hydrostatic_temperature_initialization
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert model.reference_temperature_kelvin == incumbent.reference_temperature_kelvin
    assert model.output_variables == incumbent.output_variables
    assert model.weak_held_suarez_kf_per_day == incumbent.weak_held_suarez_kf_per_day
    assert (
        model.weak_held_suarez_ka_timescale_days
        == incumbent.weak_held_suarez_ka_timescale_days
    )
    assert (
        model.weak_held_suarez_ks_timescale_days
        == incumbent.weak_held_suarez_ks_timescale_days
    )


def test_layer_mean_hydrostatic_temperature_initialization_factory_extends_incumbent():
    """The layer-mean candidate preserves incumbent settings and changes estimator."""
    model = layer_mean_hydrostatic_temperature_initialization_dinosaur_dycore_model()
    incumbent = hydrostatic_temperature_initialization_dinosaur_dycore_model()

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
    assert not incumbent.use_layer_mean_hydrostatic_temperature_initialization
    assert model.inner_step_seconds == incumbent.inner_step_seconds == 900.0
    assert model.spectral_wavenumbers == incumbent.spectral_wavenumbers == 80
    assert model.apply_spectral_filter == incumbent.apply_spectral_filter
    assert model.horizontal_diffusion_order == incumbent.horizontal_diffusion_order
    assert model.horizontal_diffusion_tau_seconds is None
    assert model.include_vertical_advection == incumbent.include_vertical_advection
    assert model.reference_temperature_kelvin == incumbent.reference_temperature_kelvin
    assert model.output_variables == incumbent.output_variables
    assert model.weak_held_suarez_kf_per_day == incumbent.weak_held_suarez_kf_per_day
    assert (
        model.weak_held_suarez_ka_timescale_days
        == incumbent.weak_held_suarez_ka_timescale_days
    )
    assert (
        model.weak_held_suarez_ks_timescale_days
        == incumbent.weak_held_suarez_ks_timescale_days
    )


def test_dinosaur_forecast_returns_requested_channels():
    """Dinosaur forecasts return requested channels in requested order."""
    output_variables = (
        "temperature_250",
        "u_component_of_wind_750",
        "v_component_of_wind_750",
        "geopotential_250",
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
    )
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        output_variables=output_variables,
        include_vertical_advection=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0, 1, 2))

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (3, 1, len(output_variables), 4, 3)
    np.testing.assert_allclose(
        forecast.values[0, 0, 0],
        np.full((4, 3), 250.0),
        atol=1e-4,
    )
    np.testing.assert_allclose(
        forecast.values[0, 0, 4],
        np.full((4, 3), 285.0),
        atol=1e-4,
    )
    np.testing.assert_allclose(
        forecast.values[0, 0, 6],
        np.full((4, 3), 100000.0),
        rtol=1e-5,
    )


def test_dinosaur_forecast_with_digital_filter_initialization_is_finite(monkeypatch):
    """DFI preserves the forecast contract and emits finite requested outputs."""
    dfi_calls = []

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        dfi_calls.append(
            {
                "equation": equation,
                "ode_solver": ode_solver,
                "filters": filters,
                "time_span": time_span,
                "cutoff_period": cutoff_period,
                "dt": dt,
            }
        )
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "temperature_250",
        "u_component_of_wind_750",
        "mean_sea_level_pressure",
    )
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        output_variables=output_variables,
        include_vertical_advection=False,
        apply_digital_filter_initialization=True,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0, 1))

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())
    assert len(dfi_calls) == 1


def test_weak_held_suarez_forecast_returns_finite_requested_channels(monkeypatch):
    """The forced DFI path preserves requested output channels and shapes."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        include_vertical_advection=False,
        apply_digital_filter_initialization=True,
        apply_weak_held_suarez_relaxation=True,
        apply_near_surface_residual_correction=True,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())
    np.testing.assert_array_equal(
        forecast.select(("2m_temperature",)).values[0],
        forecast_input.initial_state.select(("2m_temperature",)).values,
    )
    np.testing.assert_array_equal(
        forecast.select(("10m_u_component_of_wind",)).values[0],
        forecast_input.initial_state.select(("10m_u_component_of_wind",)).values,
    )


def test_log_pressure_initialization_candidate_forecast_is_finite(monkeypatch):
    """The side-by-side log-pressure candidate runs a small non-JIT forecast."""
    log_pressure_calls = []
    real_log_pressure_interpolation = (
        vertical_interpolation.interp_pressure_to_sigma_log_pressure
    )

    def record_log_pressure_interpolation(*args, **kwargs):
        log_pressure_calls.append(True)
        return real_log_pressure_interpolation(*args, **kwargs)

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        vertical_interpolation,
        "interp_pressure_to_sigma_log_pressure",
        record_log_pressure_interpolation,
    )
    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        log_pressure_initialization_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert log_pressure_calls == [True]
    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())


def test_hydrostatic_temperature_initialization_candidate_forecast_is_finite(
    monkeypatch,
):
    """The side-by-side hydrostatic candidate runs a small non-JIT forecast."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    model = replace(
        hydrostatic_temperature_initialization_dinosaur_dycore_model(),
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )

    forecast = model.forecast(forecast_input)

    assert forecast.variables == output_variables
    assert forecast.values.shape == (2, 1, len(output_variables), 4, 3)
    assert bool(jnp.isfinite(forecast.values).all())


def test_near_surface_residual_forecast_preserves_mass_diagnostics(monkeypatch):
    """The residual candidate changes only selected near-surface diagnostics."""

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    output_variables = (
        "2m_temperature",
        "10m_u_component_of_wind",
        "mean_sea_level_pressure",
        "geopotential_500",
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0, 1),
    )
    dfi_model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        include_vertical_advection=False,
        apply_digital_filter_initialization=True,
        jit_forecast=False,
    )
    residual_model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        output_variables=output_variables,
        include_vertical_advection=False,
        apply_digital_filter_initialization=True,
        apply_near_surface_residual_correction=True,
        jit_forecast=False,
    )

    raw_forecast = dfi_model.forecast(forecast_input)
    corrected_forecast = residual_model.forecast(forecast_input)

    initial_temperature = forecast_input.initial_state.select(("2m_temperature",))
    initial_u_wind = forecast_input.initial_state.select(("10m_u_component_of_wind",))
    np.testing.assert_array_equal(
        corrected_forecast.select(("2m_temperature",)).values[0],
        initial_temperature.values,
    )
    np.testing.assert_array_equal(
        corrected_forecast.select(("10m_u_component_of_wind",)).values[0],
        initial_u_wind.values,
    )
    np.testing.assert_array_equal(
        corrected_forecast.select(("geopotential_500",)).values,
        raw_forecast.select(("geopotential_500",)).values,
    )
    np.testing.assert_array_equal(
        corrected_forecast.select(("mean_sea_level_pressure",)).values,
        raw_forecast.select(("mean_sea_level_pressure",)).values,
    )


def test_near_surface_residual_correction_matches_initial_and_decays():
    """Corrected diagnostics match analysis at lead 0 and decay afterward."""
    spatial_pattern = jnp.arange(12, dtype=jnp.float32).reshape(4, 3) / 10.0
    raw_temperature = jnp.stack(
        [
            280.0 + spatial_pattern,
            281.0 + spatial_pattern,
            282.0 + spatial_pattern,
        ]
    )
    raw_u_wind = jnp.stack(
        [
            1.0 + spatial_pattern,
            1.5 + spatial_pattern,
            2.0 + spatial_pattern,
        ]
    )
    raw_geopotential = jnp.stack(
        [
            5000.0 + spatial_pattern,
            5001.0 + spatial_pattern,
            5002.0 + spatial_pattern,
        ]
    )
    raw_pressure = jnp.stack(
        [
            100000.0 + spatial_pattern,
            99900.0 + spatial_pattern,
            99800.0 + spatial_pattern,
        ]
    )
    trajectory_state = WeatherState(
        values=jnp.stack(
            [raw_temperature, raw_u_wind, raw_geopotential, raw_pressure],
            axis=1,
        ),
        variables=(
            "2m_temperature",
            "10m_u_component_of_wind",
            "geopotential_500",
            "mean_sea_level_pressure",
        ),
    )
    initial_temperature = 285.0 + spatial_pattern
    initial_u_wind = 4.0 + spatial_pattern
    initial_state = WeatherState(
        values=jnp.stack([initial_temperature, initial_u_wind]),
        variables=("2m_temperature", "10m_u_component_of_wind"),
    )

    corrected = _apply_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(0, 1, 2),
        lead_hours=(0, 24, 96),
        decay_hours=48.0,
    )

    decay = jnp.exp(-jnp.asarray([0.0, 24.0, 96.0]) / 48.0)
    expected_temperature = (
        raw_temperature
        + (initial_temperature - raw_temperature[0])[jnp.newaxis, ...]
        * decay[:, jnp.newaxis, jnp.newaxis]
    )
    expected_u_wind = (
        raw_u_wind
        + (initial_u_wind - raw_u_wind[0])[jnp.newaxis, ...]
        * decay[:, jnp.newaxis, jnp.newaxis]
    )
    expected_temperature = expected_temperature.at[0].set(initial_temperature)
    expected_u_wind = expected_u_wind.at[0].set(initial_u_wind)

    np.testing.assert_array_equal(
        corrected.select(("2m_temperature",)).values[0, 0],
        initial_temperature,
    )
    np.testing.assert_array_equal(
        corrected.select(("10m_u_component_of_wind",)).values[0, 0],
        initial_u_wind,
    )
    np.testing.assert_allclose(
        corrected.select(("2m_temperature",)).values[:, 0],
        expected_temperature,
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        corrected.select(("10m_u_component_of_wind",)).values[:, 0],
        expected_u_wind,
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_array_equal(
        corrected.select(("geopotential_500", "mean_sea_level_pressure")).values,
        trajectory_state.select(("geopotential_500", "mean_sea_level_pressure")).values,
    )


def test_near_surface_residual_correction_skips_missing_channels():
    """Residuals are skipped when either analysis or output channel is absent."""
    raw_u_wind = jnp.stack(
        [
            jnp.full((4, 3), 1.0, dtype=jnp.float32),
            jnp.full((4, 3), 2.0, dtype=jnp.float32),
        ]
    )
    raw_geopotential = jnp.stack(
        [
            jnp.full((4, 3), 5000.0, dtype=jnp.float32),
            jnp.full((4, 3), 5001.0, dtype=jnp.float32),
        ]
    )
    trajectory_state = WeatherState(
        values=jnp.stack([raw_u_wind, raw_geopotential], axis=1),
        variables=("10m_u_component_of_wind", "geopotential_500"),
    )
    initial_state = WeatherState(
        values=jnp.stack([jnp.full((4, 3), 285.0, dtype=jnp.float32)]),
        variables=("2m_temperature",),
    )

    corrected = _apply_near_surface_residual_correction(
        trajectory_state,
        initial_state=initial_state,
        lead_steps=(1,),
        lead_hours=(24,),
        decay_hours=48.0,
    )

    np.testing.assert_array_equal(corrected.values, trajectory_state.values[1:2])


def test_dinosaur_forecast_handles_multiple_initial_times():
    """Dinosaur forecasts preserve the initialization-time axis."""
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        output_variables=("temperature_250",),
        include_vertical_advection=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=2), lead_steps=(0,))

    forecast = model.forecast(forecast_input)

    assert forecast.variables == ("temperature_250",)
    assert forecast.values.shape == (1, 2, 1, 4, 3)
    np.testing.assert_allclose(forecast.values[0, :, 0], 250.0, atol=1e-4)


def test_weather_state_to_dinosaur_state_regrids_pressure_levels_to_sigma():
    """WeatherBench pressure-level inputs are regridded to Dinosaur sigma layers."""
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )

    state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=(250, 750),
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )

    sigma_temperature = (
        grid.coords.horizontal.to_nodal(state.temperature_variation)
        + reference_temperature[:, np.newaxis, np.newaxis]
    )
    np.testing.assert_allclose(sigma_temperature[0], 250.0, atol=1e-4)
    np.testing.assert_allclose(sigma_temperature[1], 285.0, atol=1e-4)


def test_weather_state_to_dinosaur_state_selects_initialization_coordinate(
    monkeypatch,
):
    """Default initialization stays linear; the candidate option uses log pressure."""
    calls = []

    def record_linear(fields, pressure_coords, sigma_coords, surface_pressure):
        calls.append("linear")
        return fields

    def record_log_pressure(fields, pressure_coords, sigma_coords, surface_pressure):
        calls.append("log_pressure")
        return fields

    monkeypatch.setattr(
        vertical_interpolation,
        "interp_pressure_to_sigma",
        record_linear,
    )
    monkeypatch.setattr(
        vertical_interpolation,
        "interp_pressure_to_sigma_log_pressure",
        record_log_pressure,
    )
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0,),
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    weather_state = WeatherState(
        values=forecast_input.initial_state.values[0],
        variables=forecast_input.initial_state.variables,
    )

    weather_state_to_dinosaur_state(
        weather_state,
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )
    assert calls == ["linear"]

    calls.clear()
    weather_state_to_dinosaur_state(
        weather_state,
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
        use_log_pressure_initialization=True,
    )
    assert calls == ["log_pressure"]


def test_log_pressure_initialization_matches_log_linear_profile():
    """Log-pressure interpolation matches profiles linear in log pressure."""
    pressure_coords = _pressure_coordinates((100, 500, 1000))
    sigma_coords = sigma_coordinates.SigmaCoordinates.equidistant(3)
    source_pressure = jnp.asarray(pressure_coords.centers, dtype=jnp.float32)
    field = (2.5 + 4.0 * jnp.log(source_pressure))[:, np.newaxis, np.newaxis]
    fields = {"temperature": field}
    surface_pressure = jnp.full((1, 1), 900.0, dtype=jnp.float32)

    log_pressure_result = vertical_interpolation.interp_pressure_to_sigma_log_pressure(
        fields,
        pressure_coords,
        sigma_coords,
        surface_pressure,
    )["temperature"]
    linear_pressure_result = vertical_interpolation.interp_pressure_to_sigma(
        fields,
        pressure_coords,
        sigma_coords,
        surface_pressure,
    )["temperature"]
    target_pressure = sigma_coords.centers[:, np.newaxis, np.newaxis] * surface_pressure
    expected = 2.5 + 4.0 * jnp.log(target_pressure)

    np.testing.assert_allclose(log_pressure_result, expected, rtol=1e-6, atol=1e-6)
    assert float(jnp.max(jnp.abs(linear_pressure_result - expected))) > 0.05


def test_hydrostatic_temperature_initialization_matches_isothermal_thickness():
    """Hydrostatic reconstruction differentiates geopotential in log pressure."""
    pressure_levels_hpa = (100, 300, 900)
    temperature_kelvin = 270.0
    log_pressure = jnp.log(jnp.asarray(pressure_levels_hpa, dtype=jnp.float32))
    spatial_offset = jnp.arange(12, dtype=jnp.float32).reshape(4, 3)
    geopotential = (
        80_000.0
        - _DRY_AIR_GAS_CONSTANT_SI
        * temperature_kelvin
        * log_pressure[:, jnp.newaxis, jnp.newaxis]
        + spatial_offset[jnp.newaxis, ...]
    )
    analyzed_temperature = jnp.full_like(geopotential, 250.0)

    actual = _hydrostatic_temperature_from_geopotential_thickness(
        analyzed_temperature=analyzed_temperature,
        geopotential=geopotential,
        pressure_levels_hpa=pressure_levels_hpa,
    )

    np.testing.assert_allclose(actual, temperature_kelvin, rtol=1e-6, atol=1e-4)


def test_hydrostatic_temperature_initialization_converts_virtual_temperature():
    """Complete humidity stacks convert hydrostatic virtual temperature to dry T."""
    pressure_levels_hpa = (100, 300, 900)
    dry_temperature_kelvin = 280.0
    specific_humidity = jnp.full((3, 4, 3), 0.01, dtype=jnp.float32)
    gas_constant_ratio = 461.0 / _DRY_AIR_GAS_CONSTANT_SI
    virtual_temperature = dry_temperature_kelvin * (
        1.0 + (gas_constant_ratio - 1.0) * specific_humidity
    )
    log_pressure = jnp.log(jnp.asarray(pressure_levels_hpa, dtype=jnp.float32))
    geopotential = (
        100_000.0
        - _DRY_AIR_GAS_CONSTANT_SI
        * virtual_temperature
        * log_pressure[:, jnp.newaxis, jnp.newaxis]
    )
    analyzed_temperature = jnp.full_like(geopotential, 250.0)

    actual = _hydrostatic_temperature_from_geopotential_thickness(
        analyzed_temperature=analyzed_temperature,
        geopotential=geopotential,
        pressure_levels_hpa=pressure_levels_hpa,
        specific_humidity=specific_humidity,
    )

    np.testing.assert_allclose(
        actual,
        dry_temperature_kelvin,
        rtol=1e-6,
        atol=1e-4,
    )


def test_layer_mean_hydrostatic_temperature_initialization_uses_adjacent_layers():
    """Layer-mean reconstruction maps hypsometric layer temperatures to levels."""
    pressure_levels_hpa = (100, 300, 600, 900)
    layer_virtual_temperature = jnp.asarray([220.0, 250.0, 280.0], dtype=jnp.float32)
    log_pressure = jnp.log(jnp.asarray(pressure_levels_hpa, dtype=jnp.float32))
    layer_thickness = (
        _DRY_AIR_GAS_CONSTANT_SI
        * layer_virtual_temperature
        * (log_pressure[1:] - log_pressure[:-1])
    )
    base_geopotential = 90_000.0
    geopotential_profile = jnp.concatenate(
        [
            jnp.asarray([base_geopotential], dtype=jnp.float32),
            base_geopotential - jnp.cumsum(layer_thickness),
        ]
    )
    geopotential = geopotential_profile[:, jnp.newaxis, jnp.newaxis] + jnp.zeros(
        (4, 2, 3),
        dtype=jnp.float32,
    )
    analyzed_temperature = jnp.full_like(geopotential, 260.0)

    actual = _layer_mean_hydrostatic_temperature_from_geopotential_thickness(
        analyzed_temperature=analyzed_temperature,
        geopotential=geopotential,
        pressure_levels_hpa=pressure_levels_hpa,
    )

    expected_profile = jnp.asarray([220.0, 235.0, 265.0, 280.0], dtype=jnp.float32)
    expected = expected_profile[:, jnp.newaxis, jnp.newaxis] + jnp.zeros(
        (4, 2, 3),
        dtype=jnp.float32,
    )
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-4)


def test_layer_mean_hydrostatic_temperature_initialization_converts_humidity():
    """Layer humidity converts virtual layer means to dry level temperatures."""
    pressure_levels_hpa = (100, 300, 900)
    dry_layer_temperature = jnp.asarray([270.0, 290.0], dtype=jnp.float32)
    specific_humidity = jnp.stack(
        [
            jnp.full((2, 3), 0.01, dtype=jnp.float32),
            jnp.full((2, 3), 0.03, dtype=jnp.float32),
            jnp.full((2, 3), 0.05, dtype=jnp.float32),
        ],
        axis=0,
    )
    layer_specific_humidity = 0.5 * (
        specific_humidity[1:, 0, 0] + specific_humidity[:-1, 0, 0]
    )
    gas_constant_ratio = 461.0 / _DRY_AIR_GAS_CONSTANT_SI
    layer_virtual_temperature = dry_layer_temperature * (
        1.0 + (gas_constant_ratio - 1.0) * layer_specific_humidity
    )
    log_pressure = jnp.log(jnp.asarray(pressure_levels_hpa, dtype=jnp.float32))
    layer_thickness = (
        _DRY_AIR_GAS_CONSTANT_SI
        * layer_virtual_temperature
        * (log_pressure[1:] - log_pressure[:-1])
    )
    geopotential_profile = jnp.concatenate(
        [
            jnp.asarray([100_000.0], dtype=jnp.float32),
            100_000.0 - jnp.cumsum(layer_thickness),
        ]
    )
    geopotential = geopotential_profile[:, jnp.newaxis, jnp.newaxis] + jnp.zeros(
        (3, 2, 3),
        dtype=jnp.float32,
    )
    analyzed_temperature = jnp.full_like(geopotential, 250.0)

    actual = _layer_mean_hydrostatic_temperature_from_geopotential_thickness(
        analyzed_temperature=analyzed_temperature,
        geopotential=geopotential,
        pressure_levels_hpa=pressure_levels_hpa,
        specific_humidity=specific_humidity,
    )

    expected_profile = jnp.asarray([270.0, 280.0, 290.0], dtype=jnp.float32)
    expected = expected_profile[:, jnp.newaxis, jnp.newaxis] + jnp.zeros(
        (3, 2, 3),
        dtype=jnp.float32,
    )
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-4)


def test_layer_mean_hydrostatic_temperature_initialization_falls_back_pointwise():
    """Invalid reconstructed level temperatures fall back to analyzed values."""
    pressure_levels_hpa = (100, 300, 900)
    analyzed_temperature = jnp.asarray(
        [
            [[251.0, 252.0]],
            [[261.0, 262.0]],
            [[271.0, 272.0]],
        ],
        dtype=jnp.float32,
    )
    log_pressure = jnp.log(jnp.asarray(pressure_levels_hpa, dtype=jnp.float32))
    positive_temperature = 280.0
    negative_temperature = -700.0
    layer_0 = (
        _DRY_AIR_GAS_CONSTANT_SI
        * positive_temperature
        * (log_pressure[1] - log_pressure[0])
    )
    layer_1 = (
        _DRY_AIR_GAS_CONSTANT_SI
        * negative_temperature
        * (log_pressure[2] - log_pressure[1])
    )
    geopotential = jnp.asarray(
        [
            [[100_000.0, 100_000.0]],
            [[100_000.0 - layer_0, jnp.nan]],
            [[100_000.0 - layer_0 - layer_1, jnp.nan]],
        ],
        dtype=jnp.float32,
    )

    actual = _layer_mean_hydrostatic_temperature_from_geopotential_thickness(
        analyzed_temperature=analyzed_temperature,
        geopotential=geopotential,
        pressure_levels_hpa=pressure_levels_hpa,
    )

    expected = jnp.asarray(
        [
            [[positive_temperature, 252.0]],
            [[261.0, 262.0]],
            [[271.0, 272.0]],
        ],
        dtype=jnp.float32,
    )
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-4)


def test_layer_mean_hydrostatic_temperature_initialization_needs_two_levels():
    """Single-level stacks cannot define thickness and preserve analyzed T."""
    analyzed_temperature = jnp.asarray([[[255.0, 256.0]]], dtype=jnp.float32)
    geopotential = jnp.asarray([[[10_000.0, 11_000.0]]], dtype=jnp.float32)

    actual = _layer_mean_hydrostatic_temperature_from_geopotential_thickness(
        analyzed_temperature=analyzed_temperature,
        geopotential=geopotential,
        pressure_levels_hpa=(500,),
    )

    np.testing.assert_array_equal(actual, analyzed_temperature)


def test_hydrostatic_temperature_initialization_falls_back_without_geopotential():
    """Incomplete geopotential stacks preserve incumbent initialized state exactly."""
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    weather_state = WeatherState(
        values=forecast_input.initial_state.values[0],
        variables=forecast_input.initial_state.variables,
    )
    common_kwargs = {
        "state": weather_state,
        "coords": grid.coords,
        "pressure_levels_hpa": (250, 750),
        "latitude_reversed": grid.latitude_reversed,
        "physics_specs": physics_specs,
        "reference_temperature": reference_temperature,
        "include_humidity": True,
        "use_log_pressure_initialization": True,
    }

    incumbent = weather_state_to_dinosaur_state(**common_kwargs)
    candidate = weather_state_to_dinosaur_state(
        **common_kwargs,
        use_hydrostatic_temperature_initialization=True,
    )

    _assert_pytree_allclose(candidate, incumbent)


def test_weather_state_to_dinosaur_state_matches_direct_dinosaur_initialization():
    """State initialization mirrors explicit Dinosaur initialization calls."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0,),
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    weather_state = WeatherState(
        values=forecast_input.initial_state.values[0],
        variables=forecast_input.initial_state.variables,
    )

    actual = weather_state_to_dinosaur_state(
        weather_state,
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )

    direct_inputs = {
        "temperature": _structured_field(
            weather_state,
            "temperature",
            pressure_levels_hpa,
            grid.latitude_reversed,
        )
        * _unit_factor(physics_specs, "kelvin"),
        "u_component_of_wind": _structured_field(
            weather_state,
            "u_component_of_wind",
            pressure_levels_hpa,
            grid.latitude_reversed,
        )
        * _unit_factor(physics_specs, "meter / second"),
        "v_component_of_wind": _structured_field(
            weather_state,
            "v_component_of_wind",
            pressure_levels_hpa,
            grid.latitude_reversed,
        )
        * _unit_factor(physics_specs, "meter / second"),
        "specific_humidity": _structured_field(
            weather_state,
            "specific_humidity",
            pressure_levels_hpa,
            grid.latitude_reversed,
        ),
    }
    surface_pressure = _surface_pressure_field(weather_state, grid.latitude_reversed)
    sigma_inputs = vertical_interpolation.interp_pressure_to_sigma(
        direct_inputs,
        _pressure_coordinates(pressure_levels_hpa),
        grid.coords.vertical,
        surface_pressure / 100.0,
    )
    direct_vorticity, direct_divergence = spherical_harmonic.uv_nodal_to_vor_div_modal(
        grid.coords.horizontal,
        sigma_inputs["u_component_of_wind"],
        sigma_inputs["v_component_of_wind"],
    )
    pressure_factor = _unit_factor(physics_specs, "pascal")
    direct = _primitive_equation_state(
        vorticity=direct_vorticity,
        divergence=direct_divergence,
        temperature_variation=grid.coords.horizontal.to_modal(
            sigma_inputs["temperature"]
            - reference_temperature[:, np.newaxis, np.newaxis]
        ),
        log_surface_pressure=grid.coords.horizontal.to_modal(
            jnp.log(surface_pressure * pressure_factor)
        )[jnp.newaxis],
        tracers={
            "specific_humidity": grid.coords.horizontal.to_modal(
                sigma_inputs["specific_humidity"]
            )
        },
    )
    expected = grid.coords.horizontal.clip_wavenumbers(direct)

    _assert_pytree_allclose(actual, expected)


def test_sigma_to_pressure_interpolation_vectorizes_over_trajectory_time():
    """Trajectory diagnostics interpolate each time slice with Dinosaur."""
    sigma_coords = sigma_coordinates.SigmaCoordinates.equidistant(3)
    pressure_coords = _pressure_coordinates((250, 500, 750))
    fields = {
        "temperature": jnp.arange(2 * 3 * 4 * 3, dtype=jnp.float32).reshape(
            2,
            3,
            4,
            3,
        ),
    }
    surface_pressure = jnp.stack(
        [
            jnp.full((4, 3), 1000.0, dtype=jnp.float32),
            jnp.full((4, 3), 925.0, dtype=jnp.float32),
        ]
    )

    actual = _interp_sigma_to_pressure_by_time(
        fields,
        pressure_coords,
        sigma_coords,
        surface_pressure,
    )
    expected = jnp.stack(
        [
            vertical_interpolation.interp_sigma_to_pressure(
                {"temperature": fields["temperature"][time_index]},
                pressure_coords,
                sigma_coords,
                surface_pressure[time_index],
            )["temperature"]
            for time_index in range(surface_pressure.shape[0])
        ]
    )

    np.testing.assert_allclose(actual["temperature"], expected)


def test_dinosaur_state_to_weather_state_extrapolates_finite_pressure_outputs():
    """Below-surface pressure diagnostics remain finite in packed WeatherState."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1, surface_pressure_pa=70_000.0),
        lead_steps=(0,),
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )
    trajectory = jax.tree_util.tree_map(lambda value: jnp.stack([value]), state)
    fixed_target_variables = (
        "2m_temperature",
        "mean_sea_level_pressure",
        "geopotential_500",
        "10m_u_component_of_wind",
    )
    output_variables = (
        "temperature_900",
        "u_component_of_wind_900",
        "v_component_of_wind_900",
        "geopotential_900",
        "specific_humidity_900",
        *fixed_target_variables,
    )

    actual = dinosaur_state_to_weather_state(
        trajectory,
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        output_variables=output_variables,
    )

    assert actual.variables == output_variables
    maximum_surface_pressure = jnp.max(
        actual.select(("mean_sea_level_pressure",)).values
    )
    assert float(maximum_surface_pressure) < 90_000.0
    assert bool(jnp.isfinite(actual.values).all())
    assert bool(jnp.isfinite(actual.select(fixed_target_variables).values).all())


def test_dinosaur_state_to_weather_state_matches_direct_diagnostics():
    """WeatherState diagnostics mirror explicit Dinosaur diagnostic calls."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1),
        lead_steps=(0,),
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )
    trajectory = jax.tree_util.tree_map(lambda value: jnp.stack([value, value]), state)
    output_variables = (
        "temperature_500",
        "u_component_of_wind_500",
        "v_component_of_wind_900",
        "geopotential_500",
        "specific_humidity_500",
        "mean_sea_level_pressure",
        "2m_temperature",
        "10m_u_component_of_wind",
    )

    actual = dinosaur_state_to_weather_state(
        trajectory,
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        output_variables=output_variables,
    )

    temperature = (
        grid.coords.horizontal.to_nodal(trajectory.temperature_variation)
        + reference_temperature[np.newaxis, :, np.newaxis, np.newaxis]
    )
    u_wind, v_wind = spherical_harmonic.vor_div_to_uv_nodal(
        grid.coords.horizontal,
        trajectory.vorticity,
        trajectory.divergence,
    )
    surface_pressure = jnp.exp(
        grid.coords.horizontal.to_nodal(trajectory.log_surface_pressure)[:, 0]
    )
    humidity = grid.coords.horizontal.to_nodal(trajectory.tracers["specific_humidity"])
    geopotential = primitive_equations.get_geopotential_on_sigma(
        temperature,
        specific_humidity=humidity,
        nodal_orography=jnp.zeros(grid.coords.horizontal.nodal_shape),
        sigma=cast(sigma_coordinates.SigmaCoordinates, grid.coords.vertical),
        gravity_acceleration=physics_specs.g,
        ideal_gas_constant=physics_specs.R,
        water_vapor_gas_constant=physics_specs.R_vapor,
    )
    pressure_factor = _unit_factor(physics_specs, "pascal")
    pressure_fields = _interp_sigma_to_pressure_by_time(
        {
            "temperature": temperature,
            "u_component_of_wind": u_wind,
            "v_component_of_wind": v_wind,
            "geopotential": geopotential,
            "specific_humidity": humidity,
        },
        _pressure_coordinates(pressure_levels_hpa),
        cast(sigma_coordinates.SigmaCoordinates, grid.coords.vertical),
        (surface_pressure / pressure_factor) / 100.0,
    )
    level_to_index = {level: index for index, level in enumerate(pressure_levels_hpa)}
    expected_values = jnp.stack(
        [
            pressure_fields["temperature"][:, level_to_index[500]]
            / _unit_factor(physics_specs, "kelvin"),
            pressure_fields["u_component_of_wind"][:, level_to_index[500]]
            / _unit_factor(physics_specs, "meter / second"),
            pressure_fields["v_component_of_wind"][:, level_to_index[900]]
            / _unit_factor(physics_specs, "meter / second"),
            pressure_fields["geopotential"][:, level_to_index[500]]
            / _unit_factor(physics_specs, "meter ** 2 / second ** 2"),
            pressure_fields["specific_humidity"][:, level_to_index[500]],
            surface_pressure / pressure_factor,
            temperature[:, -1] / _unit_factor(physics_specs, "kelvin"),
            u_wind[:, -1] / _unit_factor(physics_specs, "meter / second"),
        ],
        axis=1,
    )
    if grid.latitude_reversed:
        expected_values = expected_values[..., ::-1]

    assert actual.variables == output_variables
    np.testing.assert_allclose(actual.values, expected_values, rtol=1e-5, atol=1e-5)


def test_equation_and_filter_helpers_match_direct_dinosaur_calls():
    """Equation and filter helpers instantiate the expected Dinosaur objects."""
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    orography = jnp.zeros(grid.coords.horizontal.modal_shape, dtype=jnp.float32)

    dry_equation = _primitive_equation(
        reference_temperature=reference_temperature,
        orography=orography,
        coords=grid.coords,
        physics_specs=cast(Any, physics_specs),
        include_vertical_advection=False,
        humidity_key=None,
    )
    moist_equation = _primitive_equation(
        reference_temperature=reference_temperature,
        orography=orography,
        coords=grid.coords,
        physics_specs=cast(Any, physics_specs),
        include_vertical_advection=False,
        humidity_key="specific_humidity",
    )

    assert isinstance(dry_equation, primitive_equations.PrimitiveEquations)
    assert dry_equation.humidity_key is None
    assert isinstance(moist_equation, primitive_equations.PrimitiveEquationsSigma)
    assert moist_equation.humidity_key == "specific_humidity"

    step_seconds = _nondimensionalize_seconds(physics_specs, 3600.0)
    helper_filter = _horizontal_diffusion_step_filter(
        coords=grid.coords,
        physics_specs=physics_specs,
        step_seconds=step_seconds,
        tau_seconds=None,
        order=2,
    )
    resolution_factor = grid.coords.horizontal.latitude_nodes / 128.0
    tau_seconds = 8.6 / (2.4 ** np.log2(resolution_factor)) * 3600.0
    direct_filter = time_integration.horizontal_diffusion_step_filter(
        grid.coords.horizontal,
        dt=step_seconds,
        tau=_nondimensionalize_seconds(physics_specs, tau_seconds),
        order=2,
    )
    state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=(250, 750),
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )

    _assert_pytree_allclose(helper_filter(state, state), direct_filter(state, state))


def test_weak_held_suarez_composes_one_equation_with_fixed_forcing(monkeypatch):
    """Weak HS composition combines one primitive equation with fixed forcing."""
    compose_calls = []
    real_compose_equations = time_integration.compose_equations

    def capture_compose_equations(equations):
        compose_calls.append(tuple(equations))
        return real_compose_equations(equations)

    monkeypatch.setattr(
        time_integration,
        "compose_equations",
        capture_compose_equations,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        spectral_wavenumbers=None,
        include_vertical_advection=False,
        apply_weak_held_suarez_relaxation=True,
        jit_forecast=False,
    )

    model._trajectory_function(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        inner_steps=1,
        output_count=1,
        use_humidity_in_dynamics=False,
    )

    assert len(compose_calls) == 1
    primitive_equation, forcing = compose_calls[0]
    assert isinstance(primitive_equation, primitive_equations.PrimitiveEquations)
    assert isinstance(forcing, _TracerSafeHeldSuarezForcingSigma)
    day = scales.units.day
    assert forcing.kf == physics_specs.nondimensionalize(0.0 / day)
    np.testing.assert_allclose(
        forcing.ka,
        physics_specs.nondimensionalize(1 / (160.0 * day)),
    )
    np.testing.assert_allclose(
        forcing.ks,
        physics_specs.nondimensionalize(1 / (16.0 * day)),
    )


def test_weak_held_suarez_forcing_is_thermal_only_and_tracer_safe():
    """The local forcing emits zero wind and matching zero tracer tendencies."""
    forecast_input = _forecast_input(
        _structured_initial_state(init_count=1), lead_steps=(0,)
    )
    pressure_levels_hpa = (100, 500, 900)
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=len(pressure_levels_hpa),
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=len(pressure_levels_hpa),
        temperature_kelvin=250.0,
    )
    dinosaur_state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=pressure_levels_hpa,
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )
    forcing = _TracerSafeHeldSuarezForcingSigma(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        kf=0.0 / scales.units.day,
        ka=1 / (160.0 * scales.units.day),
        ks=1 / (16.0 * scales.units.day),
    )

    tendency = forcing.explicit_terms(dinosaur_state)

    np.testing.assert_array_equal(
        tendency.vorticity, jnp.zeros_like(tendency.vorticity)
    )
    np.testing.assert_array_equal(
        tendency.divergence,
        jnp.zeros_like(tendency.divergence),
    )
    assert tendency.tracers.keys() == dinosaur_state.tracers.keys()
    for tracer_name, tracer_tendency in tendency.tracers.items():
        np.testing.assert_array_equal(
            tracer_tendency,
            jnp.zeros_like(dinosaur_state.tracers[tracer_name]),
        )


def test_weak_held_suarez_helper_uses_dinosaur_forcing_type():
    """The helper composes a Dinosaur explicit forcing with primitive equations."""
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0,))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=None,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=250.0,
    )
    orography = jnp.zeros(grid.coords.horizontal.modal_shape, dtype=jnp.float32)
    equation = _primitive_equation(
        reference_temperature=reference_temperature,
        orography=orography,
        coords=grid.coords,
        physics_specs=cast(Any, physics_specs),
        include_vertical_advection=False,
        humidity_key=None,
    )

    composed_equation = _compose_weak_held_suarez_equation(
        equation=equation,
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        kf_per_day=0.0,
        ka_timescale_days=160.0,
        ks_timescale_days=16.0,
    )

    assert isinstance(composed_equation, time_integration.ImplicitExplicitODE)
    assert issubclass(
        _TracerSafeHeldSuarezForcingSigma, held_suarez.HeldSuarezForcingSigma
    )


def test_trajectory_function_matches_direct_dinosaur_package_call():
    """The wrapper trajectory uses the same Dinosaur calls as a direct setup."""
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        include_vertical_advection=False,
        use_humidity_in_dynamics=False,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0, 1, 2))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=model.spectral_wavenumbers,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=model.reference_temperature_kelvin,
    )
    dinosaur_state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=(250, 750),
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )

    wrapped_fn = model._trajectory_function(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        inner_steps=1,
        output_count=3,
        use_humidity_in_dynamics=False,
    )
    _, wrapped_trajectory = wrapped_fn(dinosaur_state)

    orography = jnp.zeros(grid.coords.horizontal.modal_shape, dtype=jnp.float32)
    equation = primitive_equations.PrimitiveEquations(
        reference_temperature,
        orography,
        grid.coords,
        cast(Any, physics_specs),
        include_vertical_advection=False,
    )
    step_seconds = _nondimensionalize_seconds(
        physics_specs,
        model.inner_step_seconds,
    )
    step_fn = time_integration.imex_rk_sil3(equation, step_seconds)
    step_fn = time_integration.step_with_filters(
        step_fn,
        [
            _horizontal_diffusion_step_filter(
                coords=grid.coords,
                physics_specs=physics_specs,
                step_seconds=step_seconds,
                tau_seconds=model.horizontal_diffusion_tau_seconds,
                order=model.horizontal_diffusion_order,
            )
        ],
    )
    direct_fn = time_integration.trajectory_from_step(
        step_fn,
        outer_steps=3,
        inner_steps=1,
        start_with_input=True,
    )
    _, direct_trajectory = direct_fn(dinosaur_state)

    for actual, expected in zip(
        jax.tree_util.tree_leaves(wrapped_trajectory),
        jax.tree_util.tree_leaves(direct_trajectory),
        strict=True,
    ):
        np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-6)


def test_trajectory_function_sets_up_digital_filter_initialization(monkeypatch):
    """DFI uses the forecast equation, stepper, filters, and nondimensional units."""
    dfi_calls = []
    initialized_states = []

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        dfi_calls.append(
            {
                "equation": equation,
                "ode_solver": ode_solver,
                "filters": filters,
                "time_span": time_span,
                "cutoff_period": cutoff_period,
                "dt": dt,
            }
        )

        def initialize_state(dinosaur_state):
            initialized_state = _primitive_equation_state(
                vorticity=dinosaur_state.vorticity,
                divergence=dinosaur_state.divergence,
                temperature_variation=dinosaur_state.temperature_variation
                + jnp.float32(0.25),
                log_surface_pressure=dinosaur_state.log_surface_pressure,
                tracers=dinosaur_state.tracers,
            )
            initialized_states.append(initialized_state)
            return initialized_state

        return initialize_state

    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    model = DinosaurPrimitiveEquationsDycoreModel(
        inner_step_seconds=3600.0,
        include_vertical_advection=False,
        use_humidity_in_dynamics=False,
        apply_digital_filter_initialization=True,
        jit_forecast=False,
    )
    forecast_input = _forecast_input(_initial_state(init_count=1), lead_steps=(0, 1, 2))
    grid = grid_metadata(
        longitude=forecast_input.longitude,
        latitude=forecast_input.latitude,
        layer_count=2,
        spectral_wavenumbers=model.spectral_wavenumbers,
    )
    physics_specs = units.SimUnits.from_si()
    reference_temperature = _reference_temperature(
        layer_count=2,
        temperature_kelvin=model.reference_temperature_kelvin,
    )
    dinosaur_state = weather_state_to_dinosaur_state(
        WeatherState(
            values=forecast_input.initial_state.values[0],
            variables=forecast_input.initial_state.variables,
        ),
        coords=grid.coords,
        pressure_levels_hpa=(250, 750),
        latitude_reversed=grid.latitude_reversed,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        include_humidity=True,
    )

    wrapped_fn = model._trajectory_function(
        coords=grid.coords,
        physics_specs=physics_specs,
        reference_temperature=reference_temperature,
        inner_steps=1,
        output_count=1,
        use_humidity_in_dynamics=False,
    )
    _, wrapped_trajectory = wrapped_fn(dinosaur_state)

    step_seconds = _nondimensionalize_seconds(
        physics_specs,
        model.inner_step_seconds,
    )
    filters = [
        _horizontal_diffusion_step_filter(
            coords=grid.coords,
            physics_specs=physics_specs,
            step_seconds=step_seconds,
            tau_seconds=model.horizontal_diffusion_tau_seconds,
            order=model.horizontal_diffusion_order,
        )
    ]
    first_wrapped_state = jax.tree_util.tree_map(
        lambda trajectory_leaf: trajectory_leaf[0],
        wrapped_trajectory,
    )

    assert len(dfi_calls) == 1
    call = dfi_calls[0]
    assert isinstance(call["equation"], primitive_equations.PrimitiveEquations)
    assert call["ode_solver"] is time_integration.imex_rk_sil3
    assert call["dt"] == step_seconds
    assert call["time_span"] == _nondimensionalize_seconds(
        physics_specs,
        model.digital_filter_time_span_seconds,
    )
    assert call["cutoff_period"] == _nondimensionalize_seconds(
        physics_specs,
        model.digital_filter_cutoff_seconds,
    )
    assert len(call["filters"]) == len(filters) == 1
    _assert_pytree_allclose(
        call["filters"][0](dinosaur_state, dinosaur_state),
        filters[0](dinosaur_state, dinosaur_state),
    )
    assert len(initialized_states) == 1
    _assert_pytree_allclose(first_wrapped_state, initialized_states[0])


def _initial_state(*, init_count: int) -> WeatherState:
    longitude_count = 4
    latitude_count = 3
    fields = {
        "temperature_250": 250.0,
        "temperature_750": 285.0,
        "u_component_of_wind_250": 0.0,
        "u_component_of_wind_750": 0.0,
        "v_component_of_wind_250": 0.0,
        "v_component_of_wind_750": 0.0,
        "specific_humidity_250": 0.0,
        "specific_humidity_750": 0.0,
        "geopotential_250": 0.0,
        "2m_temperature": 285.0,
        "10m_u_component_of_wind": 0.0,
        "mean_sea_level_pressure": 100000.0,
        "total_precipitation": 0.0,
    }
    values = jnp.stack(
        [
            jnp.full(
                (init_count, longitude_count, latitude_count),
                fill_value,
                dtype=jnp.float32,
            )
            for fill_value in fields.values()
        ],
        axis=1,
    )
    return WeatherState(values=values, variables=tuple(fields))


def _structured_initial_state(
    *, init_count: int, surface_pressure_pa: float = 100_000.0
) -> WeatherState:
    longitude_count = 4
    latitude_count = 3
    lon_pattern = jnp.arange(longitude_count, dtype=jnp.float32)[:, np.newaxis]
    lat_pattern = jnp.arange(latitude_count, dtype=jnp.float32)[np.newaxis, :]
    spatial_pattern = lon_pattern + 0.25 * lat_pattern
    pressure_levels = (100, 500, 900)
    fields = {}
    for pressure_level in pressure_levels:
        pressure_scale = pressure_level / 100.0
        fields[f"temperature_{pressure_level}"] = (
            220.0 + 0.04 * pressure_level + spatial_pattern
        )
        fields[f"u_component_of_wind_{pressure_level}"] = (
            0.4 * pressure_scale + 0.1 * spatial_pattern
        )
        fields[f"v_component_of_wind_{pressure_level}"] = (
            -0.2 * pressure_scale + 0.05 * spatial_pattern
        )
        fields[f"specific_humidity_{pressure_level}"] = (
            0.001 + pressure_level / 1_000_000.0 + 0.00001 * spatial_pattern
        )
        fields[f"geopotential_{pressure_level}"] = (
            1000.0 + pressure_level + 5.0 * spatial_pattern
        )
    fields["mean_sea_level_pressure"] = surface_pressure_pa + 50.0 * spatial_pattern
    fields["2m_temperature"] = 285.0 + spatial_pattern
    fields["10m_u_component_of_wind"] = 2.0 + 0.1 * spatial_pattern
    fields["total_precipitation"] = jnp.zeros_like(spatial_pattern)

    values = jnp.stack(
        [
            jnp.broadcast_to(
                field_value,
                (init_count, longitude_count, latitude_count),
            )
            for field_value in fields.values()
        ],
        axis=1,
    )
    return WeatherState(values=values, variables=tuple(fields))


def _structured_field(
    state: WeatherState,
    variable_name: str,
    pressure_levels_hpa: tuple[int, ...],
    latitude_reversed: bool,
) -> jax.Array:
    channels = tuple(
        f"{variable_name}_{pressure_level}" for pressure_level in pressure_levels_hpa
    )
    values = jnp.take(
        state.values,
        jnp.asarray(state.variable_indices(channels), dtype=jnp.int32),
        axis=-3,
    )
    if latitude_reversed:
        return values[..., ::-1]
    return values


def _surface_pressure_field(
    state: WeatherState,
    latitude_reversed: bool,
) -> jax.Array:
    values = state.select(("mean_sea_level_pressure",)).values[0]
    if latitude_reversed:
        return values[..., ::-1]
    return values


def _assert_pytree_allclose(actual, expected):
    for actual_leaf, expected_leaf in zip(
        jax.tree_util.tree_leaves(actual),
        jax.tree_util.tree_leaves(expected),
        strict=True,
    ):
        np.testing.assert_allclose(actual_leaf, expected_leaf, rtol=1e-6, atol=1e-6)


def _forecast_input(
    initial_state: WeatherState,
    *,
    lead_steps: tuple[int, ...],
) -> ForecastInput:
    initial_count = initial_state.leading_shape[0]
    initial_times = np.datetime64("2020-01-01T00:00:00", "ns") + np.arange(
        initial_count
    ).astype("timedelta64[h]")
    lead_hours = tuple(lead_steps)
    valid_times = (
        initial_times[:, np.newaxis]
        + np.asarray(lead_hours, dtype="timedelta64[h]")[np.newaxis, :]
    )
    return ForecastInput(
        initial_times=initial_times,
        valid_times=valid_times,
        lead_steps=lead_steps,
        lead_hours=lead_hours,
        step_seconds=3600.0,
        longitude=np.array([0.0, 90.0, 180.0, 270.0]),
        latitude=np.array([90.0, 0.0, -90.0]),
        initial_state=initial_state,
    )
