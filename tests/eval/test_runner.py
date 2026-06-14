from dataclasses import dataclass

import jax.numpy as jnp
import numpy as np
import xarray as xr

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.dycore.models.persistence import PersistenceDycoreModel
from dynamaxx.eval.batch import build_weatherbench2_batch
from dynamaxx.eval.core import (
    WeatherVariable,
)
from dynamaxx.eval.protocols import fixed_case
from dynamaxx.eval.runner import (
    case_chunks,
    evaluate_batch,
    evaluate_case,
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

    def forecast(self, initial_state, lead_steps, step_seconds):
        del step_seconds
        initial_values = initial_state.values
        target_shape = (
            len(lead_steps),
            *initial_values.shape,
        )
        forecast_values = jnp.broadcast_to(initial_values[jnp.newaxis], target_shape)
        return initial_state.with_values(forecast_values)


@dataclass(frozen=True)
class TemperatureSelectingPersistenceModel:
    name: str = "temperature_selecting_persistence"

    def forecast(self, initial_state, lead_steps, step_seconds):
        del step_seconds
        assert initial_state.variables == (
            "2m_temperature",
            "mean_sea_level_pressure",
            "10m_u_component_of_wind",
        )
        selected_state = initial_state.select(("2m_temperature",))
        target_shape = (
            len(lead_steps),
            *selected_state.values.shape,
        )
        forecast_values = jnp.broadcast_to(
            selected_state.values[jnp.newaxis],
            target_shape,
        )
        return selected_state.with_values(forecast_values)


@dataclass(frozen=True)
class NonFiniteDycoreModel:
    name: str = "nonfinite_forecast"

    def forecast(self, initial_state, lead_steps, step_seconds):
        del step_seconds
        initial_values = initial_state.values
        target_shape = (
            len(lead_steps),
            *initial_values.shape,
        )
        return initial_state.with_values(jnp.full(target_shape, jnp.inf))


def _record_by_key(result):
    return {
        (record.model_name, record.channel_name, record.lead_hours): record
        for record in result.records
    }


def test_evaluate_batch_scores_candidate_and_persistence(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_constant_forecast_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    model = PersistenceDycoreModel(
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
        target_variables=variables,
    )

    batch = build_weatherbench2_batch(source, case)

    assert batch.forecast_input.initial_state.variables == (
        "2m_temperature",
        "mean_sea_level_pressure",
        "10m_u_component_of_wind",
    )

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


def test_evaluate_case_chunks_match_single_batch_result(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_constant_forecast_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    model = InputAwarePersistenceModel()
    temperature = WeatherVariable("2m_temperature")
    case = fixed_case(
        "unit",
        ["2020-01-01T00:00:00", "2020-01-01T00:00:00"],
        lead_days=(0.25, 0.5),
        target_variables=(temperature,),
    )

    single_batch_result = evaluate_batch(
        model,
        build_weatherbench2_batch(source, case),
    )
    chunked_result = evaluate_case(
        model,
        source,
        case,
        chunk_initial_count=1,
    )

    assert [record.asdict() for record in chunked_result.records] == [
        record.asdict() for record in single_batch_result.records
    ]
    np.testing.assert_allclose(
        chunked_result.primary_score,
        single_batch_result.primary_score,
    )


def test_case_chunks_preserve_case_contract():
    variables = (WeatherVariable("2m_temperature"),)
    case = fixed_case(
        "unit",
        [
            "2020-01-01T00:00:00",
            "2020-01-02T00:00:00",
            "2020-01-03T00:00:00",
        ],
        lead_days=(1,),
        target_variables=variables,
    )

    chunks = case_chunks(case, 2)

    assert [chunk.initial_times.size for chunk in chunks] == [2, 1]
    assert all(chunk.name == "unit" for chunk in chunks)
    assert all(chunk.lead_steps == case.lead_steps for chunk in chunks)


def test_evaluate_batch_passes_full_initial_state(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_constant_forecast_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    temperature = WeatherVariable("2m_temperature")
    case = fixed_case(
        "unit",
        ["2020-01-01T00:00:00"],
        lead_days=(0.25, 0.5),
        target_variables=(temperature,),
    )

    batch = build_weatherbench2_batch(source, case)

    forecast_input = batch.forecast_input
    assert forecast_input.initial_state.variables == (
        "2m_temperature",
        "mean_sea_level_pressure",
        "10m_u_component_of_wind",
    )
    assert forecast_input.initial_state.values.shape == (
        case.initial_times.size,
        3,
        4,
        3,
    )

    result = evaluate_batch(InputAwarePersistenceModel(), batch)

    records = _record_by_key(result)
    assert records[("input_aware_persistence", "2m_temperature", 6)].rmse == 2.0
    assert not result.diagnostics.failed
    assert result.case.name == "unit"


def test_evaluate_batch_allows_model_to_select_forecast_variables(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_constant_forecast_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    temperature = WeatherVariable("2m_temperature")
    case = fixed_case(
        "unit",
        ["2020-01-01T00:00:00"],
        lead_days=(0.25, 0.5),
        target_variables=(temperature,),
    )
    batch = build_weatherbench2_batch(source, case)

    result = evaluate_batch(TemperatureSelectingPersistenceModel(), batch)

    records = _record_by_key(result)
    assert (
        "temperature_selecting_persistence",
        "2m_temperature",
        6,
    ) in records
    assert not result.diagnostics.failed


def test_evaluate_batch_flags_unstable_forecasts(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_constant_forecast_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    variables = (WeatherVariable("2m_temperature"),)
    case = fixed_case(
        "unit",
        ["2020-01-01T00:00:00"],
        lead_days=(0.25,),
        target_variables=variables,
    )

    batch = build_weatherbench2_batch(source, case)

    result = evaluate_batch(NonFiniteDycoreModel(), batch)

    assert result.diagnostics.failed
    assert result.diagnostics.issues[0].code == "nonfinite_forecast"
    assert np.isneginf(result.primary_score)


def test_evaluation_result_writes_json_and_csv(tmp_path):
    store_path = tmp_path / "weatherbench2.zarr"
    _write_constant_forecast_dataset(store_path)
    source = WeatherBench2Source(path=str(store_path))
    model = PersistenceDycoreModel(
        jit_forecast=False,
    )
    variables = (WeatherVariable("2m_temperature"),)
    case = fixed_case(
        "unit",
        ["2020-01-01T00:00:00"],
        lead_days=(0.25,),
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
