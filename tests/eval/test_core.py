import jax.numpy as jnp
import numpy as np

from dynamaxx.eval.core import (
    DEFAULT_LEAD_DAYS,
    WeatherState,
    WeatherVariable,
    candidate_year_case,
    daily_initial_times,
    fast_case,
    fixed_case,
    lead_days_to_steps,
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


def test_fast_and_candidate_year_cases_use_default_daily_leads():
    expected_steps = lead_days_to_steps(DEFAULT_LEAD_DAYS, step_hours=6)

    assert fast_case().lead_steps == expected_steps
    assert candidate_year_case(2019).lead_steps == expected_steps


def test_daily_initial_times_returns_inclusive_range():
    times = daily_initial_times("2020-01-01", "2020-01-03")

    np.testing.assert_array_equal(
        times,
        np.array(["2020-01-01", "2020-01-02", "2020-01-03"], dtype="datetime64[D]"),
    )


def test_fixed_case_derives_valid_times():
    case = fixed_case(
        "tiny",
        ["2020-01-01T00:00:00"],
        lead_days=(0, 0.25, 0.5),
        prognostic_variables=(WeatherVariable("2m_temperature"),),
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


def test_fixed_case_separates_variable_groups():
    temperature = WeatherVariable("2m_temperature")
    wind = WeatherVariable("10m_u_component_of_wind")
    case = fixed_case(
        "tiny",
        ["2020-01-01T00:00:00"],
        lead_days=(0.25,),
        prognostic_variables=(temperature,),
        target_variables=(temperature,),
        forcing_variables=(wind,),
        static_variables=("latitude", "coriolis"),
    )

    assert case.prognostic_channel_names == ("2m_temperature",)
    assert case.target_channel_names == ("2m_temperature",)
    assert case.forcing_channel_names == ("10m_u_component_of_wind",)
    assert case.static_variables == ("latitude", "coriolis")


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
