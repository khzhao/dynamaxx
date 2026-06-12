from dynamaxx.dycore.forecast import SpectralDycoreForecastModel
from dynamaxx.dycore.grid import SphericalGrid
from dynamaxx.dycore.simulation import SpectralDycore


def test_spectral_dycore_forecast_reuses_simulate_callable():
    grid = SphericalGrid(
        total_wavenumbers=4,
        longitude_nodes=12,
        latitude_nodes=6,
    )
    model = SpectralDycoreForecastModel(SpectralDycore(grid))

    assert model.simulate_forecast is model.simulate_forecast
