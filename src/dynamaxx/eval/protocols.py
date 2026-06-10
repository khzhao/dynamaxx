# Copyright 2026 dynamaxx

from collections.abc import Callable

import numpy as np

from dynamaxx.eval.core import EvalCase, WeatherVariable
from dynamaxx.utils.consts import HOURS_PER_DAY

DEFAULT_VARIABLES = (
    WeatherVariable("2m_temperature", title="2 m temperature", unit="K"),
    WeatherVariable(
        "mean_sea_level_pressure",
        title="Mean sea level pressure",
        unit="Pa",
    ),
    WeatherVariable(
        "geopotential",
        level=500,
        title="500 hPa geopotential",
        unit="m2 s-2",
    ),
    WeatherVariable(
        "10m_u_component_of_wind",
        title="10 m zonal wind",
        unit="m s-1",
    ),
)
DEFAULT_LEAD_DAYS = tuple(range(1, 16))
DEFAULT_STEP_HOURS = 6
FAST_INITIAL_TIMES = (
    "2019-01-01T00:00:00",
    "2019-01-15T00:00:00",
    "2019-02-01T00:00:00",
    "2019-03-01T00:00:00",
    "2019-04-01T00:00:00",
    "2019-05-01T00:00:00",
    "2019-06-01T00:00:00",
    "2019-07-01T00:00:00",
    "2019-08-01T00:00:00",
    "2019-09-01T00:00:00",
    "2019-10-01T00:00:00",
    "2019-11-01T00:00:00",
    "2019-12-01T00:00:00",
    "2019-12-15T00:00:00",
)
PROTOCOL_CHUNK_INITIAL_TIMES = {
    "fast": len(FAST_INITIAL_TIMES),
    "train": 8,
    "validation": 8,
    "test": 8,
}

ProtocolFactory = Callable[[], EvalCase]


def lead_days_to_steps(
    lead_days: tuple[int | float, ...],
    *,
    step_hours: int,
) -> tuple[int, ...]:
    """Convert lead times in days to integer model steps."""
    steps_per_day = HOURS_PER_DAY / step_hours
    lead_steps = tuple(int(round(lead_day * steps_per_day)) for lead_day in lead_days)
    assert all(
        np.isclose(lead_step, lead_day * steps_per_day)
        for lead_step, lead_day in zip(lead_steps, lead_days, strict=True)
    )
    return lead_steps


def daily_initial_times(start_date: str, end_date: str) -> np.ndarray:
    """Return daily initialization times in an inclusive date range."""
    start = np.datetime64(start_date, "D")
    end = np.datetime64(end_date, "D")
    assert start <= end
    day_count = int((end - start) / np.timedelta64(1, "D")) + 1
    return start + np.arange(day_count).astype("timedelta64[D]")


def fixed_case(
    name: str,
    initial_times: np.ndarray | list[str] | tuple[str, ...],
    *,
    lead_days: tuple[int | float, ...] = DEFAULT_LEAD_DAYS,
    step_hours: int = DEFAULT_STEP_HOURS,
    prognostic_variables: tuple[WeatherVariable, ...] = DEFAULT_VARIABLES,
    target_variables: tuple[WeatherVariable, ...] | None = None,
    forcing_variables: tuple[WeatherVariable, ...] = (),
    static_variables: tuple[str, ...] = (),
) -> EvalCase:
    """Create one model-agnostic benchmark case."""
    return EvalCase(
        name=name,
        initial_times=np.asarray(initial_times, dtype="datetime64[ns]"),
        lead_steps=lead_days_to_steps(lead_days, step_hours=step_hours),
        step_hours=step_hours,
        prognostic_variables=prognostic_variables,
        target_variables=target_variables or prognostic_variables,
        forcing_variables=forcing_variables,
        static_variables=static_variables,
    )


def fast_case() -> EvalCase:
    """Return the quick real-data protocol used during development."""
    return fixed_case("fast", FAST_INITIAL_TIMES)


def train_case() -> EvalCase:
    """Return the multi-year tuning protocol for dycore development."""
    return fixed_case("train", daily_initial_times("2010-01-01", "2018-12-31"))


def validation_case() -> EvalCase:
    """Return the held-out model-selection protocol."""
    return fixed_case("validation", daily_initial_times("2019-01-01", "2019-12-31"))


def test_case() -> EvalCase:
    """Return the locked out-of-sample reporting protocol."""
    return fixed_case("test", daily_initial_times("2020-01-01", "2020-12-31"))


PROTOCOL_FACTORIES: dict[str, ProtocolFactory] = {
    "fast": fast_case,
    "train": train_case,
    "validation": validation_case,
    "test": test_case,
}


def protocol_names() -> tuple[str, ...]:
    """Return supported fixed evaluation protocols."""
    return tuple(PROTOCOL_FACTORIES)


def create_case(protocol: str) -> EvalCase:
    """Create a fixed evaluation case by protocol name."""
    assert protocol in PROTOCOL_FACTORIES, f"unknown eval protocol {protocol}"
    return PROTOCOL_FACTORIES[protocol]()


def chunk_initial_count(protocol: str) -> int:
    """Return the number of initialization times evaluated per chunk."""
    assert protocol in PROTOCOL_CHUNK_INITIAL_TIMES
    return PROTOCOL_CHUNK_INITIAL_TIMES[protocol]
