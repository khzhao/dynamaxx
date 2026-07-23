import jax.numpy as jnp
import numpy as np

from dynamaxx.eval.core import (
    WeatherState,
    WeatherVariable,
)
from dynamaxx.eval.protocols import (
    DEFAULT_LEAD_DAYS,
    PROTOCOL_FACTORIES,
    create_case,
    cycled_daily_initial_times,
    daily_initial_times,
    fast_case,
    fixed_case,
    golden_case,
    iteration_case,
    lead_days_to_steps,
    twice_daily_initial_times,
    validation_case,
    weatherbench2_case,
)


def test_weather_variable_channel_names_match_weatherbench_convention():
    assert WeatherVariable("2m_temperature").channel_name == "2m_temperature"
    assert WeatherVariable("geopotential", level=500).channel_name == (
        "geopotential_500"
    )


def test_lead_days_to_steps_uses_step_hours():
    assert lead_days_to_steps((1, 3, 15), step_hours=6) == (4, 12, 60)


def test_default_lead_days_are_daily_through_day_15():
    assert DEFAULT_LEAD_DAYS == tuple(range(1, 16))


def test_fixed_protocols_use_default_daily_leads():
    expected_steps = lead_days_to_steps(DEFAULT_LEAD_DAYS, step_hours=6)

    assert fast_case().lead_steps == expected_steps
    assert iteration_case().lead_steps == expected_steps
    assert validation_case().lead_steps == expected_steps
    assert golden_case().lead_steps == expected_steps
    assert weatherbench2_case().lead_steps == expected_steps


def test_fixed_protocols_match_iteration_validation_golden_split():
    iteration = iteration_case()
    validation = validation_case()
    golden = golden_case()

    assert iteration.initial_times.astype("datetime64[D]")[0] == np.datetime64(
        "2014-01-01"
    )
    assert iteration.initial_times.astype("datetime64[D]")[-1] == np.datetime64(
        "2018-12-31"
    )
    assert validation.initial_times.astype("datetime64[D]")[0] == np.datetime64(
        "2019-01-01"
    )
    assert validation.initial_times.astype("datetime64[D]")[-1] == np.datetime64(
        "2019-12-31"
    )
    assert golden.initial_times.astype("datetime64[D]")[0] == np.datetime64(
        "2020-01-01"
    )
    assert golden.initial_times.astype("datetime64[D]")[-1] == np.datetime64(
        "2020-12-31"
    )
    expected_hours = np.array([0, 6, 12, 18, 0, 6, 12, 18])
    np.testing.assert_array_equal(
        _initial_hours(iteration.initial_times[:8]),
        expected_hours,
    )
    np.testing.assert_array_equal(
        _initial_hours(validation.initial_times[:8]),
        expected_hours,
    )
    np.testing.assert_array_equal(
        _initial_hours(golden.initial_times[:8]),
        expected_hours,
    )


def test_protocol_registry_contains_only_fixed_eval_protocols():
    assert tuple(PROTOCOL_FACTORIES) == (
        "fast",
        "iteration",
        "validation",
        "golden",
        "weatherbench2",
    )
    assert create_case("validation").name == "validation"


def test_weatherbench2_protocol_matches_public_2020_initializations():
    case = weatherbench2_case()

    assert case.initial_times.size == 732
    assert case.initial_times[0] == np.datetime64("2020-01-01T00:00:00")
    assert case.initial_times[-1] == np.datetime64("2020-12-31T12:00:00")
    np.testing.assert_array_equal(
        _initial_hours(case.initial_times[:6]),
        np.array([0, 12, 0, 12, 0, 12]),
    )
    assert tuple(variable.channel_name for variable in case.target_variables) == (
        "2m_temperature",
        "mean_sea_level_pressure",
        "geopotential_500",
        "temperature_850",
        "specific_humidity_700",
        "u_component_of_wind_850",
        "v_component_of_wind_850",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
    )


def test_daily_initial_times_returns_inclusive_range():
    times = daily_initial_times("2020-01-01", "2020-01-03")

    np.testing.assert_array_equal(
        times,
        np.array(["2020-01-01", "2020-01-02", "2020-01-03"], dtype="datetime64[D]"),
    )


def test_cycled_daily_initial_times_uses_repeating_hour_cycle():
    times = cycled_daily_initial_times("2020-01-01", "2020-01-06")

    np.testing.assert_array_equal(
        times.astype("datetime64[D]"),
        np.array(
            [
                "2020-01-01",
                "2020-01-02",
                "2020-01-03",
                "2020-01-04",
                "2020-01-05",
                "2020-01-06",
            ],
            dtype="datetime64[D]",
        ),
    )
    np.testing.assert_array_equal(
        _initial_hours(times),
        np.array([0, 6, 12, 18, 0, 6]),
    )


def test_twice_daily_initial_times_uses_00_and_12_utc():
    times = twice_daily_initial_times("2020-01-01", "2020-01-03")

    np.testing.assert_array_equal(
        _initial_hours(times),
        np.array([0, 12, 0, 12, 0, 12]),
    )


def test_fixed_case_derives_valid_times():
    case = fixed_case(
        "tiny",
        ["2020-01-01T00:00:00"],
        lead_days=(0, 0.25, 0.5),
        target_variables=(WeatherVariable("2m_temperature"),),
    )

    assert case.lead_steps == (0, 1, 2)
    np.testing.assert_array_equal(
        case.valid_times,
        np.array(
            [
                [
                    "2020-01-01T00:00:00",
                    "2020-01-01T06:00:00",
                    "2020-01-01T12:00:00",
                ]
            ],
            dtype="datetime64[ns]",
        ),
    )


def _initial_hours(initial_times: np.ndarray) -> np.ndarray:
    dates = initial_times.astype("datetime64[D]").astype("datetime64[ns]")
    hours = (initial_times - dates) / np.timedelta64(1, "h")
    return hours.astype(np.int64)


def test_fixed_case_uses_target_variables_for_scoring():
    temperature = WeatherVariable("2m_temperature")
    case = fixed_case(
        "tiny",
        ["2020-01-01T00:00:00"],
        lead_days=(0.25,),
        target_variables=(temperature,),
    )

    assert case.target_channel_names == ("2m_temperature",)


def test_weather_state_selects_variables_on_named_axis():
    state = WeatherState(
        values=jnp.arange(2 * 3 * 4 * 5).reshape((2, 3, 4, 5)),
        variables=("temperature", "u", "v"),
    )

    selected = state.select(("v", "temperature"))

    assert selected.variables == ("v", "temperature")
    assert selected.values.shape == (2, 2, 4, 5)
    np.testing.assert_allclose(selected.values[:, 0], state.values[:, 2])
    np.testing.assert_allclose(selected.values[:, 1], state.values[:, 0])


def test_weather_state_reports_leading_and_spatial_shapes():
    state = WeatherState(
        values=jnp.zeros((4, 2, 3, 8, 6)),
        variables=("a", "b", "c"),
    )

    assert state.leading_shape == (4, 2)
    assert state.spatial_shape == (8, 6)
