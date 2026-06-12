import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.forecast import SpectralDycoreForecastModel
from dynamaxx.dycore.grid import SphericalGrid
from dynamaxx.dycore.simulation import SpectralDycore


def _test_grid() -> SphericalGrid:
    return SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )


def test_spectral_dycore_forecast_returns_requested_leads():
    grid = _test_grid()
    model = SpectralDycoreForecastModel(SpectralDycore(grid), jit_forecast=False)
    initial_state = jnp.zeros((2, 1, *grid.nodal_shape))

    forecast = model.forecast(
        initial_state,
        (1, 3),
        600.0,
    )

    assert forecast.shape == (2, 2, 1, *grid.nodal_shape)
    np.testing.assert_allclose(forecast, 0.0)


def test_spectral_dycore_forecast_reuses_simulate_callable():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    model = SpectralDycoreForecastModel(SpectralDycore(grid))

    assert model.simulate_forecast is model.simulate_forecast
