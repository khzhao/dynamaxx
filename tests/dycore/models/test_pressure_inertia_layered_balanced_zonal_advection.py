# Copyright 2026 dynamaxx

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.pressure_inertia_layered_balanced_zonal_advection import (
    PressureInertiaLayeredBalancedZonalAdvectionDycoreModel,
    add_barotropic_vorticity_phase_nudge,
    add_highpass_tendency_residual,
    add_lower_air_surface_temperature_anchor,
    add_lower_temperature_tendency,
    add_optical_flow_residual,
    add_phase_propagated_tendency,
    add_ramped_thermal_thickness_phase_nudge,
    add_scale_split_residual,
    add_surface_temperature_tendency,
    add_surface_wind_tendency,
    add_thermal_height_tendency,
    add_two_dimensional_phase_nudge,
    add_upper_vorticity_phase_nudge,
    add_zonal_phase_forecast,
    add_zonal_phase_nudge,
    apply_history_eddy_growth_memory,
    baroclinic_eddy_activity,
    baroclinic_residual_memory_factor,
    cap_increment_to_current_eddy_rms,
    cumulative_decayed_displacement,
    highpass_tendency_residual_correction,
    partially_restore_initialized_anomaly_rms,
    phase_blended_zonal_displacement,
    phase_nudged_values,
    phase_propagated_tendency_correction,
    phase_steered_lower_temperature_tendency_correction,
    restore_initialized_anomaly_rms,
    scale_split_residual_correction,
    spectral_phase_residual_correction,
    surface_pressure_tendency_correction,
    surface_temperature_memory_forecast,
    surface_temperature_tendency_correction,
    surface_wind_tendency_correction,
    thermal_height_tendency_correction,
    transported_boundary_layer_offset_forecast,
    two_dimensional_phase_forecast,
    upper_absolute_vorticity_geopotential_increment,
    upper_pressure_tendency_correction,
    zonal_phase_forecast,
)


def test_surface_pressure_tendency_correction_decays_pressure_tendency_only():
    """Pressure tendency correction should only change pressure."""
    initial_state = jnp.zeros((1, 8, 4, 3), dtype=jnp.float32)
    initial_state = initial_state.at[:, 1].set(7.0)
    initial_state = initial_state.at[:, 5].set(2.0)

    correction = surface_pressure_tendency_correction(
        initial_state,
        (0, 4),
        21_600.0,
        current_count=4,
        pressure_index=1,
        surface_u_indices=(2,),
        surface_v_indices=(3,),
        surface_weights=(1.0,),
        wind_scale=0.0,
        max_wind_speed=55.0,
        decay_days=1.0,
    )

    np.testing.assert_allclose(correction[0, :, 1], 5.0)
    np.testing.assert_allclose(correction[1, :, 1], 5.0 * np.exp(-1.0), rtol=1e-6)
    np.testing.assert_allclose(correction[:, :, 0], 0.0)
    np.testing.assert_allclose(correction[:, :, 2], 0.0)
    np.testing.assert_allclose(correction[:, :, 3], 0.0)


def test_surface_wind_tendency_correction_decays_selected_winds_only():
    """Surface wind tendency correction should only change selected winds."""
    initial_state = jnp.zeros((1, 8, 4, 3), dtype=jnp.float32)
    initial_state = initial_state.at[:, 2].set(7.0)
    initial_state = initial_state.at[:, 3].set(-4.0)
    initial_state = initial_state.at[:, 6].set(3.0)
    initial_state = initial_state.at[:, 7].set(-1.0)

    correction = surface_wind_tendency_correction(
        initial_state,
        (0, 4),
        21_600.0,
        current_count=4,
        wind_indices=(2, 3),
        surface_u_indices=(2,),
        surface_v_indices=(3,),
        surface_weights=(1.0,),
        wind_scale=0.0,
        max_wind_speed=55.0,
        decay_days=1.0,
    )

    np.testing.assert_allclose(correction[0, :, 2], 4.0)
    np.testing.assert_allclose(correction[0, :, 3], -3.0)
    np.testing.assert_allclose(correction[1, :, 2], 4.0 * np.exp(-1.0), rtol=1e-6)
    np.testing.assert_allclose(correction[1, :, 3], -3.0 * np.exp(-1.0), rtol=1e-6)
    np.testing.assert_allclose(correction[:, :, 0], 0.0)
    np.testing.assert_allclose(correction[:, :, 1], 0.0)


def test_upper_pressure_tendency_correction_uses_upper_wind_channels():
    """Upper-steered pressure correction should match zero-wind decay."""
    initial_state = jnp.zeros((1, 8, 4, 3), dtype=jnp.float32)
    initial_state = initial_state.at[:, 1].set(7.0)
    initial_state = initial_state.at[:, 5].set(2.0)

    correction = upper_pressure_tendency_correction(
        initial_state,
        (0, 4),
        21_600.0,
        current_count=4,
        pressure_index=1,
        upper_u_index=2,
        upper_v_index=3,
        wind_scale=0.0,
        max_wind_speed=55.0,
        decay_days=1.0,
    )

    np.testing.assert_allclose(correction[0, :, 1], 5.0)
    np.testing.assert_allclose(correction[1, :, 1], 5.0 * np.exp(-1.0), rtol=1e-6)
    np.testing.assert_allclose(correction[:, :, 0], 0.0)
    np.testing.assert_allclose(correction[:, :, 2], 0.0)
    np.testing.assert_allclose(correction[:, :, 3], 0.0)


def test_surface_temperature_memory_forecast_transports_temperature_anomaly():
    """Thermal memory should move boundary-layer offsets with lower wind."""
    longitude_count = 16
    latitude_count = 5
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    latitude = jnp.linspace(-1.0, 1.0, latitude_count)
    lower_temperature = 270.0 + latitude[jnp.newaxis, :]
    temperature = lower_temperature + jnp.sin(longitude)[:, jnp.newaxis]
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 0].set(temperature)
    initial_state = initial_state.at[:, 5].set(lower_temperature)
    initial_state = initial_state.at[:, 8].set(30.0)
    initial_state = initial_state.at[:, 9].set(5.0)
    lower_forecast = jnp.broadcast_to(
        lower_temperature, (2, 1, longitude_count, latitude_count)
    )

    forecast = surface_temperature_memory_forecast(
        initial_state,
        lower_forecast,
        (0, 1),
        21_600.0,
        current_count=10,
        temperature_index=0,
        lower_temperature_index=5,
        lower_u_index=8,
        lower_v_index=9,
        wind_scale=1.0,
        max_wind_speed=100.0,
        zonal_damping_days=10.0,
        memory_decay_days=1.0,
    )

    np.testing.assert_allclose(forecast[0, 0], temperature)
    assert not np.allclose(forecast[1, 0], temperature)
    assert jnp.min(forecast[1, 0]) >= jnp.min(temperature)
    assert jnp.max(forecast[1, 0]) <= jnp.max(temperature)


def test_transported_boundary_layer_offset_forecast_starts_from_temperature_offset():
    """Boundary-layer offset forecast should start at current T2m minus T850."""
    initial_state = jnp.zeros((1, 10, 6, 4), dtype=jnp.float32)
    initial_state = initial_state.at[:, 0].set(285.0)
    initial_state = initial_state.at[:, 5].set(280.0)
    initial_state = initial_state.at[:, 8].set(0.0)
    initial_state = initial_state.at[:, 9].set(0.0)

    offset = transported_boundary_layer_offset_forecast(
        initial_state,
        (0, 1),
        21_600.0,
        current_count=10,
        temperature_index=0,
        lower_temperature_index=5,
        lower_u_index=8,
        lower_v_index=9,
        wind_scale=1.0,
        max_wind_speed=100.0,
        zonal_damping_days=10.0,
    )

    np.testing.assert_allclose(offset, 5.0)


def test_lower_air_surface_temperature_anchor_preserves_lead_zero_and_channels():
    """Lower-air anchoring should only pull later T2m toward T850 plus offset."""
    initial_state = jnp.zeros((1, 10, 4, 3), dtype=jnp.float32)
    initial_state = initial_state.at[:, 0].set(285.0)
    initial_state = initial_state.at[:, 5].set(280.0)
    forecast = jnp.zeros((2, 1, 10, 4, 3), dtype=jnp.float32)
    forecast = forecast.at[:, :, 0].set(285.0)
    forecast = forecast.at[:, :, 1].set(7.0)
    forecast = forecast.at[:, :, 5].set(282.0)

    updated = add_lower_air_surface_temperature_anchor(
        forecast,
        initial_state,
        (0, 4),
        21_600.0,
        temperature_index=0,
        lower_temperature_index=5,
        anchor_weight=0.5,
        ramp_days=0.25,
        decay_days=100.0,
    )

    np.testing.assert_allclose(updated[0], forecast[0], atol=1.0e-6)
    np.testing.assert_allclose(updated[:, :, 1], forecast[:, :, 1], atol=1.0e-6)
    np.testing.assert_allclose(updated[:, :, 5], forecast[:, :, 5], atol=1.0e-6)
    assert jnp.all(updated[1, :, 0] > forecast[1, :, 0])
    assert jnp.all(updated[1, :, 0] < 287.0)


def test_surface_temperature_tendency_correction_has_short_memory():
    """Surface-temperature tendency should decay quickly and preserve lead zero."""
    initial_state = jnp.zeros((1, 20, 4, 3), dtype=jnp.float32)
    initial_state = initial_state.at[:, 0].set(10.0)
    initial_state = initial_state.at[:, 10].set(8.0)

    correction = surface_temperature_tendency_correction(
        initial_state,
        (0, 4),
        21_600.0,
        current_count=10,
        temperature_index=0,
        decay_days=0.25,
    )

    np.testing.assert_allclose(correction[0], 0.0, atol=1.0e-6)
    np.testing.assert_allclose(correction[1], 2.0 * np.exp(-4.0), rtol=1.0e-6)


def test_add_surface_temperature_tendency_updates_only_temperature():
    """Surface-temperature tendency should not directly alter other channels."""
    initial_state = jnp.zeros((1, 20, 4, 3), dtype=jnp.float32)
    initial_state = initial_state.at[:, 0].set(10.0)
    initial_state = initial_state.at[:, 10].set(8.0)
    forecast = jnp.zeros((1, 1, 20, 4, 3), dtype=jnp.float32)

    updated = add_surface_temperature_tendency(
        forecast,
        initial_state,
        (4,),
        21_600.0,
        current_count=10,
        temperature_index=0,
        decay_days=0.25,
        tendency_weight=1.0,
    )

    np.testing.assert_allclose(updated[0, 0, 0], 2.0 * np.exp(-4.0), rtol=1.0e-6)
    np.testing.assert_allclose(updated[:, :, 1], 0.0, atol=1.0e-6)
    np.testing.assert_allclose(updated[:, :, 2], 0.0, atol=1.0e-6)


def test_add_lower_temperature_tendency_updates_only_lower_temperature():
    """Lower temperature tendency should not directly alter other channels."""
    initial_state = jnp.zeros((1, 20, 4, 3), dtype=jnp.float32)
    initial_state = initial_state.at[:, 5].set(10.0)
    initial_state = initial_state.at[:, 15].set(7.0)
    forecast = jnp.zeros((2, 1, 10, 4, 3), dtype=jnp.float32)

    updated = add_lower_temperature_tendency(
        forecast,
        initial_state,
        (0, 4),
        21_600.0,
        current_count=10,
        lower_temperature_index=5,
        lower_u_index=8,
        lower_v_index=9,
        wind_scale=0.0,
        max_wind_speed=55.0,
        decay_days=1.0,
    )

    np.testing.assert_allclose(updated[0, :, 5], 3.0)
    np.testing.assert_allclose(updated[1, :, 5], 3.0 * np.exp(-1.0), rtol=1e-6)
    np.testing.assert_allclose(updated[:, :, 0], 0.0)
    np.testing.assert_allclose(updated[:, :, 6], 0.0)


def test_add_surface_wind_tendency_updates_only_selected_winds():
    """Surface wind tendency should not directly alter other channels."""
    initial_state = jnp.zeros((1, 20, 4, 3), dtype=jnp.float32)
    initial_state = initial_state.at[:, 3].set(6.0)
    initial_state = initial_state.at[:, 4].set(-5.0)
    initial_state = initial_state.at[:, 13].set(1.0)
    initial_state = initial_state.at[:, 14].set(-2.0)
    forecast = jnp.zeros((2, 1, 10, 4, 3), dtype=jnp.float32)

    updated = add_surface_wind_tendency(
        forecast,
        initial_state,
        (0, 4),
        21_600.0,
        current_count=10,
        wind_indices=(3, 4),
        surface_u_indices=(3,),
        surface_v_indices=(4,),
        surface_weights=(1.0,),
        wind_scale=0.0,
        max_wind_speed=55.0,
        decay_days=1.0,
    )

    np.testing.assert_allclose(updated[0, :, 3], 5.0)
    np.testing.assert_allclose(updated[0, :, 4], -3.0)
    np.testing.assert_allclose(updated[1, :, 3], 5.0 * np.exp(-1.0), rtol=1e-6)
    np.testing.assert_allclose(updated[1, :, 4], -3.0 * np.exp(-1.0), rtol=1e-6)
    np.testing.assert_allclose(updated[:, :, 0], 0.0)
    np.testing.assert_allclose(updated[:, :, 2], 0.0)


def test_phase_steered_lower_temperature_tendency_moves_history_phase():
    """Lower-temperature tendency should follow observed zonal phase motion."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    previous_temperature = jnp.sin(longitude)[:, jnp.newaxis]
    current_temperature = jnp.roll(previous_temperature, shift=1, axis=0)
    previous_field = jnp.broadcast_to(
        previous_temperature,
        (longitude_count, latitude_count),
    )
    current_field = jnp.broadcast_to(
        current_temperature + 0.2,
        (longitude_count, latitude_count),
    )
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 5].set(current_field)
    initial_state = initial_state.at[:, 15].set(previous_field)
    initial_state = initial_state.at[:, 8].set(100.0)
    initial_state = initial_state.at[:, 9].set(0.0)

    correction = phase_steered_lower_temperature_tendency_correction(
        initial_state,
        (0, 1),
        21_600.0,
        current_count=10,
        lower_temperature_index=5,
        lower_u_index=8,
        lower_v_index=9,
        wind_scale=1.0,
        max_wind_speed=200.0,
        decay_days=100.0,
    )

    expected_tendency = current_field - previous_field
    np.testing.assert_allclose(correction[0, 0], expected_tendency, atol=1.0e-6)
    assert not np.allclose(correction[1, 0], expected_tendency)
    assert jnp.isfinite(correction).all()


def test_partially_restore_initialized_anomaly_rms_scales_damped_anomalies():
    """Anomaly restoration should use the geometric RMS deficit."""
    longitude_count = 8
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    initial_wave = jnp.sin(longitude)[:, jnp.newaxis]
    initial_state = jnp.zeros((1, 10, longitude_count, 1), dtype=jnp.float32)
    initial_state = initial_state.at[:, 1].set(initial_wave)
    forecast = jnp.zeros((1, 1, 10, longitude_count, 1), dtype=jnp.float32)
    forecast = forecast.at[:, :, 1].set(0.25 * initial_wave)

    restored = partially_restore_initialized_anomaly_rms(
        forecast,
        initial_state,
        current_count=10,
        variable_indices=(1,),
    )

    np.testing.assert_allclose(
        restored[0, 0, 1],
        0.5 * initial_wave,
        atol=1.0e-6,
    )


def test_partially_restore_initialized_anomaly_rms_leaves_strong_anomalies_unchanged():
    """Anomaly restoration should not amplify fields above initialized RMS."""
    longitude_count = 8
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    initial_wave = jnp.sin(longitude)[:, jnp.newaxis]
    initial_state = jnp.zeros((1, 10, longitude_count, 1), dtype=jnp.float32)
    initial_state = initial_state.at[:, 1].set(initial_wave)
    forecast = jnp.zeros((1, 1, 10, longitude_count, 1), dtype=jnp.float32)
    forecast = forecast.at[:, :, 1].set(2.0 * initial_wave)

    restored = partially_restore_initialized_anomaly_rms(
        forecast,
        initial_state,
        current_count=10,
        variable_indices=(1,),
    )

    np.testing.assert_allclose(restored, forecast, atol=1.0e-6)


def test_restore_initialized_anomaly_rms_fully_restores_damped_anomalies():
    """Full anomaly restoration should recover initialized RMS."""
    longitude_count = 8
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    initial_wave = jnp.sin(longitude)[:, jnp.newaxis]
    initial_state = jnp.zeros((1, 10, longitude_count, 1), dtype=jnp.float32)
    initial_state = initial_state.at[:, 2].set(initial_wave)
    forecast = jnp.zeros((1, 1, 10, longitude_count, 1), dtype=jnp.float32)
    forecast = forecast.at[:, :, 2].set(0.25 * initial_wave)

    restored = restore_initialized_anomaly_rms(
        forecast,
        initial_state,
        current_count=10,
        variable_indices=(2,),
    )

    np.testing.assert_allclose(restored[0, 0, 2], initial_wave, atol=1.0e-6)


def test_history_eddy_growth_memory_scales_selected_future_eddies():
    """Recent eddy growth should only scale selected future zonal anomalies."""
    initial_state = jnp.zeros((1, 4, 4, 2), dtype=jnp.float32)
    current_eddy = jnp.asarray(
        [[2.0, 2.0], [-2.0, -2.0], [2.0, 2.0], [-2.0, -2.0]],
        dtype=jnp.float32,
    )
    previous_eddy = 0.5 * current_eddy
    forecast_eddy = jnp.asarray(
        [[1.0, 1.0], [-1.0, -1.0], [1.0, 1.0], [-1.0, -1.0]],
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 1].set(current_eddy)
    initial_state = initial_state.at[:, 3].set(previous_eddy)
    forecast = jnp.zeros((2, 1, 4, 4, 2), dtype=jnp.float32)
    forecast = forecast.at[:, :, 0].set(7.0)
    forecast = forecast.at[:, :, 1].set(forecast_eddy)

    updated = apply_history_eddy_growth_memory(
        forecast,
        initial_state,
        (0, 4),
        21_600.0,
        current_count=2,
        variable_indices=(1,),
        growth_weight=0.2,
        memory_decay_days=2.0,
        max_scale=1.15,
        max_log_growth_per_step=0.05,
    )

    np.testing.assert_allclose(updated[0], forecast[0], atol=1.0e-6)
    np.testing.assert_allclose(updated[:, :, 0], forecast[:, :, 0], atol=1.0e-6)
    assert jnp.std(updated[1, :, 1]) > jnp.std(forecast[1, :, 1])
    np.testing.assert_allclose(
        jnp.mean(updated[:, :, 1], axis=-2),
        jnp.mean(forecast[:, :, 1], axis=-2),
        atol=1.0e-6,
    )


def test_scale_split_residual_correction_is_zero_for_smooth_state():
    """Scale-split residual should not alter a zonally smooth state."""
    initial_state = jnp.ones((1, 20, 16, 3), dtype=jnp.float32)

    correction = scale_split_residual_correction(
        initial_state,
        (0, 4),
        21_600.0,
        current_count=10,
        surface_indices=(1, 3, 4),
        lower_indices=(5, 8, 9),
        upper_indices=(2, 6, 7),
        surface_u_indices=(3,),
        surface_v_indices=(4,),
        surface_weights=(1.0,),
        lower_u_index=8,
        lower_v_index=9,
        upper_u_index=6,
        upper_v_index=7,
        wind_scale=0.0,
        max_wind_speed=55.0,
        reference_wave_number=4.0,
        damping_power=4.0,
        decay_days=5.0,
        residual_weight=0.75,
    )

    np.testing.assert_allclose(correction, 0.0, atol=1.0e-6)


def test_phase_blended_zonal_displacement_uses_recent_phase_motion():
    """Phase blending should mix steering displacement with observed wave motion."""
    longitude_count = 32
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    previous_wave = jnp.sin(longitude)[jnp.newaxis, :, jnp.newaxis]
    current_wave = jnp.roll(previous_wave, shift=1, axis=-2)
    previous_state = jnp.zeros((1, 2, longitude_count, 1), dtype=jnp.float32)
    current_state = previous_state.at[:, 1].set(current_wave)
    previous_state = previous_state.at[:, 1].set(previous_wave)
    wind_displacement = jnp.full((1, 1), 2.0, dtype=jnp.float32)

    blended = phase_blended_zonal_displacement(
        current_state,
        previous_state,
        wind_displacement,
        phase_reference_index=1,
        phase_blend=0.5,
        phase_bound=1.0,
    )

    np.testing.assert_allclose(blended, 1.5, atol=1.0e-5)


def test_cumulative_decayed_displacement_integrates_fading_steps():
    """Cumulative feature displacement should sum exponentially fading motion."""
    displacement = cumulative_decayed_displacement(
        (0, 1, 2),
        jnp.float32,
        displacement_decay_steps=2.0,
    )
    expected_decay = np.exp(-0.5)

    np.testing.assert_allclose(displacement[0], 0.0, atol=1.0e-6)
    np.testing.assert_allclose(displacement[1], 1.0, atol=1.0e-6)
    np.testing.assert_allclose(displacement[2], 1.0 + expected_decay, atol=1.0e-6)


def test_add_optical_flow_residual_restores_selected_weather_scale_wave():
    """Optical-flow residual should carry selected high-pass structure."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    weather_scale_wave = jnp.sin(6.0 * longitude)[:, jnp.newaxis]
    weather_scale_wave = jnp.broadcast_to(
        weather_scale_wave,
        (longitude_count, latitude_count),
    )
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 1].set(weather_scale_wave)
    initial_state = initial_state.at[:, 11].set(weather_scale_wave)
    forecast = jnp.zeros((1, 1, 20, longitude_count, latitude_count), dtype=jnp.float32)

    updated = add_optical_flow_residual(
        forecast,
        initial_state,
        (0,),
        21_600.0,
        current_count=10,
        variable_indices=(1,),
        flow_channel_indices=(1,),
        regularization=0.05,
        smoothing_passes=0,
        max_displacement_cells=1.0,
        flow_scale=0.0,
        displacement_decay_steps=8.0,
        reference_wave_number=1.0,
        damping_power=4.0,
        decay_days=100.0,
        residual_weight=1.0,
    )

    assert jnp.max(jnp.abs(updated[0, 0, 1])) > 0.9
    np.testing.assert_allclose(updated[:, :, 0], 0.0, atol=1.0e-6)
    np.testing.assert_allclose(updated[:, :, 2], 0.0, atol=1.0e-6)


def test_spectral_phase_residual_advances_recent_zonal_phase():
    """Spectral residual propagation should continue observed zonal phase motion."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    previous_wave = jnp.sin(4.0 * longitude)[:, jnp.newaxis]
    previous_wave = jnp.broadcast_to(previous_wave, (longitude_count, latitude_count))
    current_wave = jnp.roll(previous_wave, shift=1, axis=0)
    expected_next_wave = jnp.roll(current_wave, shift=1, axis=0)
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 2].set(current_wave)
    initial_state = initial_state.at[:, 12].set(previous_wave)

    correction = spectral_phase_residual_correction(
        initial_state,
        (0, 1),
        21_600.0,
        current_count=10,
        reference_wave_number=1.0,
        damping_power=4.0,
        decay_days=1.0e6,
        residual_weight=1.0,
    )

    np.testing.assert_allclose(correction[0, 0, 2], current_wave, atol=1.0e-5)
    np.testing.assert_allclose(correction[1, 0, 2], expected_next_wave, atol=1.0e-5)
    np.testing.assert_allclose(correction[:, :, 1], 0.0, atol=1.0e-6)


def test_zonal_phase_forecast_advances_full_field_phase():
    """Full-field zonal phase propagation should keep the current zonal mean."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    previous_wave = jnp.sin(4.0 * longitude)[:, jnp.newaxis]
    previous_wave = jnp.broadcast_to(previous_wave, (longitude_count, latitude_count))
    current_wave = jnp.roll(previous_wave, shift=1, axis=0)
    expected_next_wave = jnp.roll(current_wave, shift=1, axis=0)
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    current_field = 10.0 + current_wave
    previous_field = 7.0 + previous_wave
    initial_state = initial_state.at[:, 2].set(current_field)
    initial_state = initial_state.at[:, 12].set(previous_field)

    forecast = zonal_phase_forecast(
        initial_state,
        (0, 1),
        current_count=10,
        variable_indices=(2,),
    )

    np.testing.assert_allclose(forecast[0, 0, 0], current_field, atol=1.0e-5)
    np.testing.assert_allclose(
        forecast[1, 0, 0],
        10.0 + expected_next_wave,
        atol=1.0e-5,
    )


def test_add_zonal_phase_forecast_blends_selected_channel_only():
    """Zonal phase blending should leave unselected channels unchanged."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    previous_wave = jnp.sin(4.0 * longitude)[:, jnp.newaxis]
    previous_wave = jnp.broadcast_to(previous_wave, (longitude_count, latitude_count))
    current_wave = jnp.roll(previous_wave, shift=1, axis=0)
    expected_next_wave = jnp.roll(current_wave, shift=1, axis=0)
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 2].set(current_wave)
    initial_state = initial_state.at[:, 12].set(previous_wave)
    forecast = jnp.zeros((2, 1, 20, longitude_count, latitude_count), dtype=jnp.float32)

    updated = add_zonal_phase_forecast(
        forecast,
        initial_state,
        (0, 1),
        current_count=10,
        variable_indices=(2,),
        phase_weight=0.25,
    )

    np.testing.assert_allclose(updated[0, 0, 2], 0.25 * current_wave, atol=1.0e-5)
    np.testing.assert_allclose(
        updated[1, 0, 2],
        0.25 * expected_next_wave,
        atol=1.0e-5,
    )
    np.testing.assert_allclose(updated[:, :, 1], 0.0, atol=1.0e-6)


def test_phase_nudged_values_moves_phase_without_losing_amplitude():
    """Phase nudging should rotate waves while preserving forecast amplitude."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    forecast_wave = jnp.sin(4.0 * longitude)[:, jnp.newaxis]
    forecast_wave = jnp.broadcast_to(forecast_wave, (longitude_count, latitude_count))
    target_wave = jnp.roll(forecast_wave, shift=1, axis=0)
    forecast_values = forecast_wave[jnp.newaxis, jnp.newaxis, jnp.newaxis]
    target_values = target_wave[jnp.newaxis, jnp.newaxis, jnp.newaxis]

    nudged = phase_nudged_values(
        forecast_values,
        target_values,
        phase_weight=1.0,
    )

    np.testing.assert_allclose(nudged[0, 0, 0], target_wave, atol=1.0e-5)
    np.testing.assert_allclose(jnp.max(nudged), jnp.max(forecast_wave), atol=1.0e-5)


def test_add_zonal_phase_nudge_updates_selected_channel_only():
    """Zonal phase nudging should preserve unselected forecast channels."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    previous_wave = jnp.sin(4.0 * longitude)[:, jnp.newaxis]
    previous_wave = jnp.broadcast_to(previous_wave, (longitude_count, latitude_count))
    current_wave = jnp.roll(previous_wave, shift=1, axis=0)
    expected_next_wave = jnp.roll(current_wave, shift=1, axis=0)
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 1].set(current_wave)
    initial_state = initial_state.at[:, 11].set(previous_wave)
    forecast = jnp.zeros((1, 1, 20, longitude_count, latitude_count), dtype=jnp.float32)
    forecast = forecast.at[:, :, 1].set(current_wave)
    forecast = forecast.at[:, :, 2].set(3.0)

    updated = add_zonal_phase_nudge(
        forecast,
        initial_state,
        (1,),
        21_600.0,
        current_count=10,
        variable_indices=(1,),
        phase_weight=1.0,
        decay_days=1.0e12,
    )

    np.testing.assert_allclose(updated[0, 0, 1], expected_next_wave, atol=1.0e-5)
    np.testing.assert_allclose(updated[:, :, 2], 3.0, atol=1.0e-6)


def test_two_dimensional_phase_forecast_advances_coherent_phase():
    """2-D phase propagation should keep the current mean and advance waves."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    previous_wave = jnp.sin(4.0 * longitude)[:, jnp.newaxis]
    previous_wave = jnp.broadcast_to(previous_wave, (longitude_count, latitude_count))
    current_wave = jnp.roll(previous_wave, shift=1, axis=0)
    expected_next_wave = jnp.roll(current_wave, shift=1, axis=0)
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    current_field = 10.0 + current_wave
    previous_field = 7.0 + previous_wave
    initial_state = initial_state.at[:, 2].set(current_field)
    initial_state = initial_state.at[:, 12].set(previous_field)

    forecast = two_dimensional_phase_forecast(
        initial_state,
        (0, 1),
        current_count=10,
        variable_indices=(2,),
        max_zonal_wave_number=8.0,
        max_meridional_wave_number=2.0,
    )

    np.testing.assert_allclose(forecast[0, 0, 0], current_field, atol=1.0e-5)
    np.testing.assert_allclose(
        forecast[1, 0, 0],
        10.0 + expected_next_wave,
        atol=1.0e-5,
    )


def test_add_two_dimensional_phase_nudge_updates_selected_channel_only():
    """2-D phase nudging should preserve unselected forecast channels."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    previous_wave = jnp.sin(4.0 * longitude)[:, jnp.newaxis]
    previous_wave = jnp.broadcast_to(previous_wave, (longitude_count, latitude_count))
    current_wave = jnp.roll(previous_wave, shift=1, axis=0)
    expected_next_wave = jnp.roll(current_wave, shift=1, axis=0)
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 1].set(current_wave)
    initial_state = initial_state.at[:, 11].set(previous_wave)
    forecast = jnp.zeros((1, 1, 20, longitude_count, latitude_count), dtype=jnp.float32)
    forecast = forecast.at[:, :, 1].set(current_wave)
    forecast = forecast.at[:, :, 2].set(3.0)

    updated = add_two_dimensional_phase_nudge(
        forecast,
        initial_state,
        (1,),
        21_600.0,
        current_count=10,
        variable_indices=(1,),
        phase_weight=1.0,
        decay_days=1.0e12,
        max_zonal_wave_number=8.0,
        max_meridional_wave_number=2.0,
    )

    np.testing.assert_allclose(updated[0, 0, 1], expected_next_wave, atol=1.0e-5)
    np.testing.assert_allclose(updated[:, :, 2], 3.0, atol=1.0e-6)


def test_cap_increment_to_current_eddy_rms_bounds_anomaly_scale():
    """Vorticity increments should be capped by initialized eddy energy."""
    longitude_count = 16
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    current_wave = 2.0 * jnp.sin(longitude)[:, jnp.newaxis]
    increment_wave = 10.0 * jnp.sin(longitude)[:, jnp.newaxis]
    current_values = current_wave[jnp.newaxis]
    increment = jnp.broadcast_to(
        increment_wave,
        (2, 1, longitude_count, 1),
    )

    capped = cap_increment_to_current_eddy_rms(
        increment,
        current_values,
        max_fraction=0.25,
    )

    capped_rms = jnp.sqrt(jnp.mean(capped * capped, axis=(-2, -1)))
    current_rms = jnp.sqrt(jnp.mean(current_wave * current_wave))
    assert jnp.max(capped_rms) <= 0.25 * current_rms + 1.0e-6


def test_upper_absolute_vorticity_increment_is_zero_without_wind():
    """Barotropic vorticity increment should vanish without steering flow."""
    initial_state = jnp.zeros((1, 10, 8, 5), dtype=jnp.float32)

    increment = upper_absolute_vorticity_geopotential_increment(
        initial_state,
        (0, 1),
        21_600.0,
        current_count=10,
        upper_u_index=6,
        upper_v_index=7,
        wind_scale=1.0,
        max_wind_speed=70.0,
        coriolis_scale=1.0e-4,
        reference_latitude_radians=0.75,
    )

    np.testing.assert_allclose(increment, 0.0, atol=1.0e-5)


def test_add_upper_vorticity_phase_nudge_preserves_unselected_channels():
    """Upper-vorticity phase nudging should only update Z500."""
    longitude_count = 16
    latitude_count = 5
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    latitude = jnp.linspace(-1.0, 1.0, latitude_count)
    geopotential = (
        50_000.0
        + 500.0 * jnp.sin(longitude)[:, jnp.newaxis]
        + 100.0 * latitude[jnp.newaxis, :]
    )
    initial_state = jnp.zeros(
        (1, 10, longitude_count, latitude_count), dtype=jnp.float32
    )
    initial_state = initial_state.at[:, 2].set(geopotential)
    initial_state = initial_state.at[:, 6].set(20.0)
    initial_state = initial_state.at[:, 7].set(10.0)
    forecast = jnp.zeros((1, 1, 10, longitude_count, latitude_count), dtype=jnp.float32)
    forecast = forecast.at[:, :, 0].set(7.0)
    forecast = forecast.at[:, :, 2].set(geopotential)

    updated = add_upper_vorticity_phase_nudge(
        forecast,
        initial_state,
        (1,),
        21_600.0,
        current_count=10,
        geopotential_index=2,
        upper_u_index=6,
        upper_v_index=7,
        wind_scale=1.0,
        max_wind_speed=70.0,
        coriolis_scale=1.0e-4,
        reference_latitude_radians=0.75,
        max_increment_fraction=0.10,
        phase_weight=0.10,
        decay_days=20.0,
    )

    assert jnp.isfinite(updated).all()
    np.testing.assert_allclose(updated[:, :, 0], forecast[:, :, 0], atol=1.0e-6)


def test_add_barotropic_vorticity_phase_nudge_preserves_unselected_channels():
    """Barotropic-vorticity phase nudging should only update Z500."""
    longitude_count = 32
    latitude_count = 7
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    latitude = jnp.linspace(-1.0, 1.0, latitude_count)
    height_wave = 800.0 * jnp.sin(2.0 * longitude)[:, jnp.newaxis]
    height_wave = height_wave * jnp.cos(latitude)[jnp.newaxis, :]
    geopotential = 50_000.0 + height_wave
    initial_state = jnp.zeros(
        (1, 10, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 1].set(100_000.0)
    initial_state = initial_state.at[:, 2].set(geopotential)
    initial_state = initial_state.at[:, 5].set(280.0)
    forecast = jnp.zeros(
        (2, 1, 10, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    forecast = forecast.at[:, :, 0].set(7.0)
    forecast = forecast.at[:, :, 1].set(100_000.0)
    forecast = forecast.at[:, :, 2].set(geopotential)

    updated = add_barotropic_vorticity_phase_nudge(
        forecast,
        initial_state,
        (0, 4),
        21_600.0,
        current_count=10,
        geopotential_index=2,
        pressure_index=1,
        surface_temperature_index=0,
        surface_u_index=3,
        lower_temperature_index=5,
        flow_scale=0.10,
        max_wind_speed=100.0,
        vorticity_decay_days=30.0,
        target_anomaly_weight=1.0,
        coriolis_scale=1.0e-4,
        reference_latitude_radians=0.75,
        phase_weight=1.0,
        amplitude_weight=0.25,
        pressure_response_weight=0.25,
        wind_response_weight=0.25,
        wind_response_hours=2.0,
        wind_response_max_increment=5.0,
        wind_response_ramp_days=0.25,
        wind_response_decay_days=100.0,
        ramp_days=0.25,
        decay_days=100.0,
    )

    np.testing.assert_allclose(updated[0], forecast[0], atol=1.0e-6)
    np.testing.assert_allclose(updated[:, :, 0], forecast[:, :, 0], atol=1.0e-6)
    assert jnp.max(jnp.abs(updated[1, :, 1] - forecast[1, :, 1])) > 1.0e-4
    assert jnp.max(jnp.abs(updated[1, :, 2] - forecast[1, :, 2])) > 1.0e-4
    assert jnp.max(jnp.abs(updated[1, :, 3] - forecast[1, :, 3])) > 1.0e-4
    assert jnp.isfinite(updated).all()


def test_ramped_thermal_thickness_phase_nudge_waits_then_updates_height():
    """Thermal thickness phase nudging should ramp in after lead zero."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    previous_temperature_wave = jnp.sin(4.0 * longitude)[:, jnp.newaxis]
    previous_temperature_wave = jnp.broadcast_to(
        previous_temperature_wave,
        (longitude_count, latitude_count),
    )
    current_temperature_wave = jnp.roll(previous_temperature_wave, shift=1, axis=0)
    height_wave = 100.0 * jnp.sin(4.0 * longitude)[:, jnp.newaxis]
    height_wave = jnp.broadcast_to(height_wave, (longitude_count, latitude_count))
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 2].set(50_000.0 + height_wave)
    initial_state = initial_state.at[:, 5].set(280.0 + current_temperature_wave)
    initial_state = initial_state.at[:, 15].set(280.0 + previous_temperature_wave)
    forecast = jnp.zeros(
        (2, 1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    forecast = forecast.at[:, :, 0].set(7.0)
    forecast = forecast.at[:, :, 2].set(50_000.0 + height_wave)

    updated = add_ramped_thermal_thickness_phase_nudge(
        forecast,
        initial_state,
        (0, 4),
        21_600.0,
        current_count=10,
        temperature_index=5,
        height_index=2,
        phase_weight=0.15,
        ramp_days=5.0,
        decay_days=20.0,
        max_increment_fraction=0.10,
        max_zonal_wave_number=8.0,
        max_meridional_wave_number=2.0,
    )

    np.testing.assert_allclose(updated[0], forecast[0], atol=1.0e-6)
    np.testing.assert_allclose(updated[:, :, 0], forecast[:, :, 0], atol=1.0e-6)
    assert jnp.max(jnp.abs(updated[1, :, 2] - forecast[1, :, 2])) > 1.0e-3
    assert jnp.isfinite(updated).all()


def test_phase_propagated_tendency_advances_recent_tendency_phase():
    """Phase-propagated tendency should integrate coherent recent motion."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    previous_wave = jnp.sin(4.0 * longitude)[:, jnp.newaxis]
    previous_wave = jnp.broadcast_to(previous_wave, (longitude_count, latitude_count))
    current_wave = jnp.roll(previous_wave, shift=1, axis=0)
    current_tendency = current_wave - previous_wave
    expected_tendency = jnp.roll(current_tendency, shift=1, axis=0)
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 2].set(current_wave)
    initial_state = initial_state.at[:, 12].set(previous_wave)

    correction = phase_propagated_tendency_correction(
        initial_state,
        (0, 1),
        21_600.0,
        current_count=10,
        variable_indices=(2,),
        memory_decay_days=0.25,
        max_cumulative_steps=4.0,
        max_zonal_wave_number=12.0,
        max_meridional_wave_number=12.0,
    )

    np.testing.assert_allclose(correction[0, 0, 0], 0.0, atol=1.0e-6)
    np.testing.assert_allclose(correction[1, 0, 0], expected_tendency, atol=1.0e-5)


def test_add_phase_propagated_tendency_updates_selected_channels_only():
    """Phase-propagated tendency should not alter unselected forecast channels."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    wave = jnp.sin(4.0 * longitude)[:, jnp.newaxis]
    wave = jnp.broadcast_to(wave, (longitude_count, latitude_count))
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 1].set(wave)
    forecast = jnp.zeros((1, 1, 20, longitude_count, latitude_count), dtype=jnp.float32)
    forecast = forecast.at[:, :, 2].set(7.0)

    updated = add_phase_propagated_tendency(
        forecast,
        initial_state,
        (1,),
        21_600.0,
        current_count=10,
        variable_indices=(1,),
        tendency_weight=0.5,
        memory_decay_days=0.25,
        max_cumulative_steps=4.0,
        max_zonal_wave_number=12.0,
        max_meridional_wave_number=12.0,
    )

    assert jnp.max(jnp.abs(updated[0, 0, 1])) > 0.0
    np.testing.assert_allclose(updated[:, :, 2], 7.0, atol=1.0e-6)


def test_thermal_height_tendency_correction_uses_lower_warm_advection():
    """Thermal height tendency should respond to lower-level temperature advection."""
    longitude_count = 32
    latitude_count = 5
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    temperature_wave = jnp.sin(longitude)[:, jnp.newaxis]
    temperature_wave = jnp.broadcast_to(
        temperature_wave,
        (longitude_count, latitude_count),
    )
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 5].set(temperature_wave)
    initial_state = initial_state.at[:, 8].set(20.0)

    correction = thermal_height_tendency_correction(
        initial_state,
        (0, 4),
        21_600.0,
        current_count=10,
        temperature_index=5,
        u_index=8,
        v_index=9,
        reference_wave_number=18.0,
        damping_power=4.0,
        decay_days=3.0,
    )

    np.testing.assert_allclose(correction[0], 0.0, atol=1.0e-6)
    assert jnp.max(jnp.abs(correction[1])) > 0.0
    np.testing.assert_allclose(jnp.mean(correction[1], axis=-2), 0.0, atol=1.0e-5)


def test_baroclinic_eddy_activity_increases_with_vertical_shear():
    """Eady activity should be zero without shear and bounded with shear."""
    initial_state = jnp.zeros((1, 20, 8, 5), dtype=jnp.float32)
    no_shear = baroclinic_eddy_activity(
        initial_state,
        current_count=10,
        lower_u_index=8,
        lower_v_index=9,
        upper_u_index=6,
        upper_v_index=7,
    )
    sheared_state = initial_state.at[:, 6].set(40.0)
    sheared = baroclinic_eddy_activity(
        sheared_state,
        current_count=10,
        lower_u_index=8,
        lower_v_index=9,
        upper_u_index=6,
        upper_v_index=7,
    )

    np.testing.assert_allclose(no_shear, 0.0, atol=1.0e-6)
    assert jnp.max(sheared) > 0.0
    assert jnp.max(sheared) < 1.0


def test_baroclinic_residual_memory_factor_slows_decay_under_shear():
    """Baroclinic memory should increase future residual weight only with shear."""
    initial_state = jnp.zeros((1, 20, 8, 5), dtype=jnp.float32)
    sheared_state = initial_state.at[:, 6].set(40.0)
    no_shear = baroclinic_residual_memory_factor(
        initial_state,
        (0, 4),
        21_600.0,
        current_count=10,
        lower_u_index=8,
        lower_v_index=9,
        upper_u_index=6,
        upper_v_index=7,
        decay_days=12.0,
        memory_strength=1.0,
    )
    sheared = baroclinic_residual_memory_factor(
        sheared_state,
        (0, 4),
        21_600.0,
        current_count=10,
        lower_u_index=8,
        lower_v_index=9,
        upper_u_index=6,
        upper_v_index=7,
        decay_days=12.0,
        memory_strength=1.0,
    )

    np.testing.assert_allclose(no_shear, 1.0, atol=1.0e-6)
    np.testing.assert_allclose(sheared[0], 1.0, atol=1.0e-6)
    assert jnp.max(sheared[1]) > 1.0


def test_add_thermal_height_tendency_updates_only_height_channel():
    """Thermal height tendency should not directly alter other variables."""
    longitude_count = 32
    latitude_count = 5
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    temperature_wave = jnp.sin(longitude)[:, jnp.newaxis]
    temperature_wave = jnp.broadcast_to(
        temperature_wave,
        (longitude_count, latitude_count),
    )
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 5].set(temperature_wave)
    initial_state = initial_state.at[:, 8].set(20.0)
    forecast = jnp.zeros((1, 1, 20, longitude_count, latitude_count), dtype=jnp.float32)

    updated = add_thermal_height_tendency(
        forecast,
        initial_state,
        (4,),
        21_600.0,
        current_count=10,
        height_index=2,
        temperature_index=5,
        u_index=8,
        v_index=9,
        reference_wave_number=18.0,
        damping_power=4.0,
        decay_days=3.0,
        tendency_weight=1.0,
    )

    assert jnp.max(jnp.abs(updated[0, 0, 2])) > 0.0
    np.testing.assert_allclose(updated[:, :, 1], 0.0, atol=1.0e-6)
    np.testing.assert_allclose(updated[:, :, 3], 0.0, atol=1.0e-6)


def test_add_scale_split_residual_restores_selected_weather_scale_wave():
    """Scale split should carry selected high-pass structure without leakage."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    weather_scale_wave = jnp.sin(6.0 * longitude)[:, jnp.newaxis]
    weather_scale_wave = jnp.broadcast_to(
        weather_scale_wave,
        (longitude_count, latitude_count),
    )
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 1].set(weather_scale_wave)
    forecast = jnp.zeros((2, 1, 20, longitude_count, latitude_count), dtype=jnp.float32)

    updated = add_scale_split_residual(
        forecast,
        initial_state,
        (0, 4),
        21_600.0,
        current_count=10,
        variable_indices=(1,),
        surface_indices=(1, 3, 4),
        lower_indices=(5, 8, 9),
        upper_indices=(2, 6, 7),
        surface_u_indices=(3,),
        surface_v_indices=(4,),
        surface_weights=(1.0,),
        lower_u_index=8,
        lower_v_index=9,
        upper_u_index=6,
        upper_v_index=7,
        wind_scale=0.0,
        max_wind_speed=55.0,
        reference_wave_number=1.0,
        damping_power=4.0,
        decay_days=100.0,
        residual_weight=1.0,
    )

    assert jnp.max(jnp.abs(updated[0, 0, 1])) > 0.9
    np.testing.assert_allclose(updated[:, :, 0], 0.0, atol=1.0e-6)
    np.testing.assert_allclose(updated[:, :, 2], 0.0, atol=1.0e-6)


def test_highpass_tendency_residual_correction_ignores_smooth_tendency():
    """High-pass tendency correction should ignore spatially smooth changes."""
    initial_state = jnp.zeros((1, 20, 16, 3), dtype=jnp.float32)
    initial_state = initial_state.at[:, :10].set(2.0)

    correction = highpass_tendency_residual_correction(
        initial_state,
        (0, 4),
        21_600.0,
        current_count=10,
        variable_indices=(1, 2),
        surface_indices=(1, 3, 4),
        lower_indices=(5, 8, 9),
        upper_indices=(2, 6, 7),
        surface_u_indices=(3,),
        surface_v_indices=(4,),
        surface_weights=(1.0,),
        lower_u_index=8,
        lower_v_index=9,
        upper_u_index=6,
        upper_v_index=7,
        wind_scale=0.0,
        max_wind_speed=55.0,
        reference_wave_number=4.0,
        damping_power=4.0,
        decay_days=2.0,
        residual_weight=1.0,
    )

    np.testing.assert_allclose(correction, 0.0, atol=1.0e-6)


def test_add_highpass_tendency_residual_updates_selected_channels():
    """High-pass tendency residual should update only selected channels."""
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    tendency_wave = jnp.sin(6.0 * longitude)[:, jnp.newaxis]
    tendency_wave = jnp.broadcast_to(tendency_wave, (longitude_count, latitude_count))
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 1].set(tendency_wave)
    forecast = jnp.zeros((1, 1, 20, longitude_count, latitude_count), dtype=jnp.float32)

    updated = add_highpass_tendency_residual(
        forecast,
        initial_state,
        (0,),
        21_600.0,
        current_count=10,
        variable_indices=(1,),
        surface_indices=(1, 3, 4),
        lower_indices=(5, 8, 9),
        upper_indices=(2, 6, 7),
        surface_u_indices=(3,),
        surface_v_indices=(4,),
        surface_weights=(1.0,),
        lower_u_index=8,
        lower_v_index=9,
        upper_u_index=6,
        upper_v_index=7,
        wind_scale=0.0,
        max_wind_speed=55.0,
        reference_wave_number=1.0,
        damping_power=4.0,
        decay_days=2.0,
        residual_weight=1.0,
    )

    assert jnp.max(jnp.abs(updated[0, 0, 1])) > 0.9
    np.testing.assert_allclose(updated[:, :, 0], 0.0, atol=1.0e-6)
    np.testing.assert_allclose(updated[:, :, 2], 0.0, atol=1.0e-6)


def test_pressure_inertia_layered_balanced_zonal_advection_keeps_temperature_fixed_without_wind():
    """Zonally uniform temperature should persist without steering wind."""
    model = PressureInertiaLayeredBalancedZonalAdvectionDycoreModel(
        jit_forecast=False,
        zonal_wind_scale=0.0,
        surface_temperature_tendency_weight=0.0,
    )
    longitude_count = 8
    latitude_count = 5
    latitude_temperature = jnp.arange(latitude_count, dtype=jnp.float32)
    temperature = jnp.broadcast_to(
        latitude_temperature[jnp.newaxis, :],
        (longitude_count, latitude_count),
    )
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count), dtype=jnp.float32
    )
    initial_state = initial_state.at[:, 0].set(temperature)

    forecast = model.forecast(initial_state, (0, 1, 2), 21_600.0)

    assert forecast.shape == (3, 1, 20, 8, 5)
    expected_temperature = jnp.broadcast_to(
        initial_state[jnp.newaxis, :, 0],
        forecast[:, :, 0].shape,
    )
    np.testing.assert_allclose(forecast[:, :, 0], expected_temperature)


def test_pressure_inertia_layered_balanced_zonal_advection_adds_upper_tendency_after_filtering():
    """Upper inertia should survive scale-selective background filtering."""
    model = PressureInertiaLayeredBalancedZonalAdvectionDycoreModel(
        jit_forecast=False,
        zonal_wind_scale=0.0,
        tendency_decay_days=100.0,
        pressure_decay_days=100.0,
        scale_selective_reference_wave_number=1.0,
        meridional_scale_selective_reference_wave_number=1.0,
        horizontal_cross_scale_selective_reference_wave_number=1.0,
    )
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    upper_wave = jnp.sin(8.0 * longitude)[:, jnp.newaxis]
    upper_wave = jnp.broadcast_to(upper_wave, (longitude_count, latitude_count))
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 2].set(upper_wave)

    forecast = model.forecast(initial_state, (4,), 21_600.0)

    assert jnp.max(jnp.abs(forecast[0, 0, 2])) > 0.1
    assert jnp.isfinite(forecast).all()


def test_pressure_inertia_layered_balanced_zonal_advection_restores_z500_rms():
    """Default anomaly RMS restoration should include 500 hPa geopotential."""
    default_model = PressureInertiaLayeredBalancedZonalAdvectionDycoreModel(
        jit_forecast=False,
        zonal_wind_scale=0.0,
        scale_split_residual_indices=(),
        scale_split_phase_residual_indices=(),
        scale_split_baroclinic_memory_indices=(),
        scale_selective_reference_wave_number=1.0,
        meridional_scale_selective_reference_wave_number=1.0,
        horizontal_cross_scale_selective_reference_wave_number=1.0,
        zonal_phase_forecast_indices=(),
    )
    surface_only_model = PressureInertiaLayeredBalancedZonalAdvectionDycoreModel(
        jit_forecast=False,
        zonal_wind_scale=0.0,
        anomaly_rms_indices=(1, 3, 4),
        scale_split_residual_indices=(),
        scale_split_phase_residual_indices=(),
        scale_split_baroclinic_memory_indices=(),
        scale_selective_reference_wave_number=1.0,
        meridional_scale_selective_reference_wave_number=1.0,
        horizontal_cross_scale_selective_reference_wave_number=1.0,
        zonal_phase_forecast_indices=(),
    )
    longitude_count = 32
    latitude_count = 3
    longitude = jnp.linspace(0.0, 2.0 * jnp.pi, longitude_count, endpoint=False)
    upper_wave = jnp.sin(4.0 * longitude)[:, jnp.newaxis]
    upper_wave = jnp.broadcast_to(upper_wave, (longitude_count, latitude_count))
    initial_state = jnp.zeros(
        (1, 20, longitude_count, latitude_count),
        dtype=jnp.float32,
    )
    initial_state = initial_state.at[:, 2].set(upper_wave)
    initial_state = initial_state.at[:, 12].set(upper_wave)

    default_forecast = default_model.forecast(initial_state, (4,), 21_600.0)
    surface_only_forecast = surface_only_model.forecast(initial_state, (4,), 21_600.0)

    assert jnp.max(jnp.abs(default_forecast[0, 0, 2])) > (
        1.5 * jnp.max(jnp.abs(surface_only_forecast[0, 0, 2]))
    )
    assert jnp.isfinite(default_forecast).all()


def test_pressure_inertia_layered_balanced_zonal_advection_works_inside_jit():
    """Pressure-inertia model should remain valid inside JAX jit."""
    model = PressureInertiaLayeredBalancedZonalAdvectionDycoreModel()
    initial_state = jnp.arange(2 * 20 * 6 * 5, dtype=jnp.float32).reshape((2, 20, 6, 5))

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 21_600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 20, 6, 5)
    assert jnp.isfinite(forecast).all()


def test_pressure_inertia_layered_balanced_zonal_advection_reuses_callable():
    """Forecast callable should be cached per model instance."""
    model = PressureInertiaLayeredBalancedZonalAdvectionDycoreModel()

    assert model.forecast_function is model.forecast_function
