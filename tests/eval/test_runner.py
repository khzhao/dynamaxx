from dataclasses import dataclass

import jax.numpy as jnp
import numpy as np
import xarray as xr

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.dycore.forecast import SpectralDycoreForecastModel
from dynamaxx.dycore.grid import SphericalGrid
from dynamaxx.dycore.simulation import SpectralDycore
from dynamaxx.eval.batch import build_weatherbench2_batch
from dynamaxx.eval.core import (
    ForecastInput,
    WeatherState,
    WeatherVariable,
    fixed_case,
)
from dynamaxx.eval.runner import (
    evaluate_batch,
    write_metric_csv,
    write_metric_json,
)


def _write_constant_forecast_dataset(path):
    time = np.array(
        [
            "2020-01-01T00:00:00",
            "2020-01-01T06:00:00",
            "2020-01-01T12:00:00",
        ],
        dtype="datetime64",
    )
    channel = np.array(
        [
            "2m_temperature",
            "mean_sea_level_pressure",
            "10m_u_component_of_wind",
        ]
    )
    longitude = np.array([0.0, 90.0, 180.0, 270.0])
    latitude = np.array([90.0, 0.0, -90.0])
    values = np.zeros((time.size, channel.size, longitude.size, latitude.size))
    values[:, 0] = np.array([10.0, 12.0, 14.0])[:, np.newaxis, np.newaxis]
    values[:, 1] = np.array([100.0, 98.0, 96.0])[:, np.newaxis, np.newaxis]
    values[:, 2] = np.array([1.0, 2.0, 3.0])[:, np.newaxis, np.newaxis]

    dataset = xr.Dataset(
        {
            "state": (
                ("time", "channel", "longitude", "latitude"),
                values,
            ),
        },
        coords={
            "time": time,
            "channel": channel,
            "longitude": longitude,
            "latitude": latitude,
        },
    )
    dataset.to_zarr(path, mode="w")


@dataclass(frozen=True)
class InputAwarePersistenceModel:
    name: str = "input_aware_persistence"

    def forecast(self, forecast_input: ForecastInput) -> WeatherState:
        assert forecast_input.forcing is not None
        assert forecast_input.forcing.variables == ("10m_u_component_of_wind",)
        assert forecast_input.forcing.values.shape == (2, 1, 1, 4, 3)
        assert set(forecast_input.static) == {
            "latitude",
            "coriolis",
            "area_weights",
        }
        assert forecast_input.static["latitude"].shape == (3,)
        assert forecast_input.static["coriolis"].shape == (3,)
        assert forecast_input.static["area_weights"].shape == (4, 3)
        target_shape = (
            len(forecast_input.lead_steps),
            *forecast_input.initial_state.values.shape,
        )
        return forecast_input.initial_state.with_values(
            jnp.broadcast_to(
                forecast_input.initial_state.values[jnp.newaxis],
                target_shape,
            )
        )


@dataclass(frozen=True)
class NonFiniteForecastModel:
    name: str = "nonfinite_forecast"

    def forecast(self, forecast_input: ForecastInput) -> WeatherState:
        target_shape = (
            len(forecast_input.lead_steps),
            *forecast_input.initial_state.values.shape,
        )
        return forecast_input.initial_state.with_values(
            jnp.full(target_shape, jnp.inf),
        )


def _record_by_key(result):
    return {
        (record.model_name, record.channel_name, record.lead_hours): record
        for record in result.records
    }


def test_evaluate_batch_scores_candidate_and_baselines(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_constant_forecast_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    grid = SphericalGrid(
        total_wavenumbers=2,
        longitude_nodes=4,
        latitude_nodes=3,
        latitude_spacing="equiangular_with_poles",
    )
    model = SpectralDycoreForecastModel(
        SpectralDycore(grid),
        name="candidate",
        jit_forecast=False,
    )
    variables = (
        WeatherVariable("2m_temperature"),
        WeatherVariable("mean_sea_level_pressure"),
    )
    case = fixed_case(
        "unit",
        ["2020-01-01T00:00:00"],
        lead_days=(0.25, 0.5),
        prognostic_variables=variables,
        target_variables=variables,
    )

    batch = build_weatherbench2_batch(source, case)

    result = evaluate_batch(model, batch)

    records = _record_by_key(result)
    t2m_lead_6 = records[("candidate", "2m_temperature", 6)]
    t2m_lead_12 = records[("candidate", "2m_temperature", 12)]

    np.testing.assert_allclose(t2m_lead_6.rmse, 2.0, atol=2e-5)
    np.testing.assert_allclose(t2m_lead_6.bias, -2.0, atol=2e-5)
    np.testing.assert_allclose(t2m_lead_6.skill_vs_persistence, 0.0, atol=2e-5)
    np.testing.assert_allclose(t2m_lead_12.rmse, 4.0, atol=2e-5)
    assert len(result.records) == 8
    assert not result.diagnostics.failed
    assert result.diagnostics.issues == ()
    np.testing.assert_allclose(result.primary_score, 0.0, atol=2e-5)


def test_evaluate_batch_passes_forcing_and_static_variables(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_constant_forecast_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    temperature = WeatherVariable("2m_temperature")
    wind = WeatherVariable("10m_u_component_of_wind")
    case = fixed_case(
        "unit",
        ["2020-01-01T00:00:00"],
        lead_days=(0.25, 0.5),
        prognostic_variables=(temperature,),
        target_variables=(temperature,),
        forcing_variables=(wind,),
        static_variables=("latitude", "coriolis", "area_weights"),
    )

    batch = build_weatherbench2_batch(source, case)

    result = evaluate_batch(InputAwarePersistenceModel(), batch)

    records = _record_by_key(result)
    assert records[("input_aware_persistence", "2m_temperature", 6)].rmse == 2.0
    assert not result.diagnostics.failed
    assert result.case.name == "unit"


def test_evaluate_batch_flags_unstable_forecasts(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_constant_forecast_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    variables = (WeatherVariable("2m_temperature"),)
    case = fixed_case(
        "unit",
        ["2020-01-01T00:00:00"],
        lead_days=(0.25,),
        prognostic_variables=variables,
        target_variables=variables,
    )

    batch = build_weatherbench2_batch(source, case)

    result = evaluate_batch(NonFiniteForecastModel(), batch)

    assert result.diagnostics.failed
    assert result.diagnostics.issues[0].code == "nonfinite_forecast"
    assert np.isneginf(result.primary_score)


def test_evaluation_result_writes_json_and_csv(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_constant_forecast_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    grid = SphericalGrid(
        total_wavenumbers=2,
        longitude_nodes=4,
        latitude_nodes=3,
        latitude_spacing="equiangular_with_poles",
    )
    model = SpectralDycoreForecastModel(
        SpectralDycore(grid),
        jit_forecast=False,
    )
    variables = (WeatherVariable("2m_temperature"),)
    case = fixed_case(
        "unit",
        ["2020-01-01T00:00:00"],
        lead_days=(0.25,),
        prognostic_variables=variables,
        target_variables=variables,
    )
    batch = build_weatherbench2_batch(source, case)
    result = evaluate_batch(model, batch)
    json_path = tmp_path / "metrics.json"
    csv_path = tmp_path / "metrics.csv"

    write_metric_json(result, json_path)
    write_metric_csv(result, csv_path)

    json_text = json_path.read_text()
    assert '"diagnostics"' in json_text
    assert '"primary_score"' in json_text
    assert "model_name,variable,channel_name,lead_hours" in csv_path.read_text()
