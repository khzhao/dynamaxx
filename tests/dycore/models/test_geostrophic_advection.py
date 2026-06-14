import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.models.geostrophic_advection import (
    GeostrophicAdvectionDycoreModel,
    cell_laplacian,
    geostrophic_wind,
    latitude_gradient,
    semi_lagrangian_advect,
)


def test_latitude_gradient_is_zero_for_constant_field():
    values = jnp.ones((2, 4, 5), dtype=jnp.float32)

    gradient = latitude_gradient(values)

    np.testing.assert_allclose(gradient, jnp.zeros_like(values), atol=1e-7)


def test_cell_laplacian_is_zero_for_constant_field():
    values = jnp.ones((2, 3, 4, 5), dtype=jnp.float32)

    laplacian = cell_laplacian(values)

    np.testing.assert_allclose(laplacian, jnp.zeros_like(values), atol=1e-7)


def test_zero_wind_advection_preserves_state():
    state = jnp.arange(3 * 4 * 5, dtype=jnp.float32).reshape((1, 3, 4, 5))
    wind = jnp.zeros((1, 4, 5), dtype=jnp.float32)

    advected = semi_lagrangian_advect(state, wind, wind, jnp.asarray(21_600.0))

    np.testing.assert_allclose(advected, state, atol=1e-6)


def test_geostrophic_wind_is_zero_for_constant_geopotential():
    state = jnp.ones((2, 3, 4, 5), dtype=jnp.float32)

    u_wind, v_wind = geostrophic_wind(
        state,
        geopotential_index=2,
        flow_scale=1.0,
        max_wind_speed=60.0,
    )

    np.testing.assert_allclose(u_wind, jnp.zeros_like(u_wind), atol=1e-7)
    np.testing.assert_allclose(v_wind, jnp.zeros_like(v_wind), atol=1e-7)


def test_geostrophic_advection_forecast_has_expected_shape_and_finite_values():
    model = GeostrophicAdvectionDycoreModel(jit_forecast=False)
    initial_state = jnp.arange(2 * 3 * 6 * 5, dtype=jnp.float32).reshape(
        (2, 3, 6, 5)
    )

    forecast = model.forecast(initial_state, (0, 1, 3), 21_600.0)

    assert forecast.shape == (3, 2, 3, 6, 5)
    np.testing.assert_allclose(forecast[0], initial_state)
    assert jnp.isfinite(forecast).all()


def test_geostrophic_advection_forecast_works_inside_jit():
    model = GeostrophicAdvectionDycoreModel()
    initial_state = jnp.arange(2 * 3 * 6 * 5, dtype=jnp.float32).reshape(
        (2, 3, 6, 5)
    )

    forecast = jax.jit(
        lambda state: model.forecast(state, (1, 2), 21_600.0),
    )(initial_state)

    assert forecast.shape == (2, 2, 3, 6, 5)
    assert jnp.isfinite(forecast).all()


def test_geostrophic_advection_reuses_forecast_callable():
    model = GeostrophicAdvectionDycoreModel()

    assert model.forecast_function is model.forecast_function
