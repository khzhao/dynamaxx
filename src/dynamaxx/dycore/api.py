# Copyright 2026 dynamaxx

from typing import Protocol

from dynamaxx.weather import ForecastInput, WeatherState


class DycoreModel(Protocol):
    """Minimal forecast API implemented by dycore models."""

    @property
    def name(self) -> str:
        """Stable model name used in metric outputs."""

    def forecast(
        self,
        forecast_input: ForecastInput,
    ) -> WeatherState:
        """Return a named forecast shaped as (lead, init, variable, lon, lat)."""
