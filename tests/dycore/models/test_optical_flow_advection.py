import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.optical_flow_advection import (
    OpticalFlowAdvectionDycoreModel,
    advect_with_cell_displacement,
    estimate_optical_flow_cells,
    split_history_state,
)


def test_split_history_state_returns_current_and_previous_channels():
    current = jnp.ones((2, 3, 4, 5), dtype=jnp.float32)
    previous = jnp.zeros((2, 3, 4, 5), dtype=jnp.float32)
    state = jnp.concatenate([current, previous], axis=1)

    split_current, split_previous = split_history_state(state, current_count=3)

    np.testing.assert_allclose(split_current, current)
    np.testing.assert_allclose(split_previous, previous)


def test_advect_with_cell_displacement_preserves_state_for_zero_displacement():
    state = jnp.arange(2 * 3 * 7 * 5, dtype=jnp.float32).reshape((2, 3, 7, 5))
    displacement_x = jnp.zeros((2, 7, 5), dtype=jnp.float32)
    displacement_y = jnp.zeros((2, 7, 5), dtype=jnp.float32)

    advected = advect_with_cell_displacement(state, displacement_x, displacement_y)

    np.testing.assert_allclose(advected, state)


def test_estimate_optical_flow_detects_eastward_feature_shift():
    longitude_count = 48
    latitude_count = 31
    longitude = jnp.arange(longitude_count, dtype=jnp.float32)[:, jnp.newaxis]
    latitude = jnp.arange(latitude_count, dtype=jnp.float32)[jnp.newaxis, :]
    wave = (
        jnp.sin(2.0 * jnp.pi * longitude / longitude_count)
        + 0.4 * jnp.cos(3.0 * jnp.pi * latitude / (latitude_count - 1))
        + 0.3
        * jnp.sin(
            2.0 * jnp.pi * longitude / longitude_count
            + 2.0 * jnp.pi * latitude / (latitude_count - 1)
        )
    )
    previous = jnp.stack([wave, wave * wave], axis=0)[jnp.newaxis]
    current = jnp.roll(previous, shift=1, axis=-2)

    displacement_x, displacement_y = estimate_optical_flow_cells(
        current,
        previous,
        channel_indices=(0, 1),
        regularization=0.02,
        smoothing_passes=2,
        max_displacement_cells=2.0,
        flow_scale=1.0,
    )

    assert jnp.mean(displacement_x) > 0.2
    assert jnp.abs(jnp.mean(displacement_y)) < 0.2
    assert jnp.isfinite(displacement_x).all()
    assert jnp.isfinite(displacement_y).all()


def test_optical_flow_advection_forecast_works_inside_jit():
    model = OpticalFlowAdvectionDycoreModel()
    current = jnp.arange(2 * 10 * 6 * 5, dtype=jnp.float32).reshape((2, 10, 6, 5))
    previous = current - 1.0
    initial_state = jnp.concatenate([current, previous], axis=1)

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 21_600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 20, 6, 5)
    assert jnp.isfinite(forecast).all()


def test_optical_flow_advection_reuses_forecast_callable():
    model = OpticalFlowAdvectionDycoreModel()

    assert model.forecast_function is model.forecast_function
