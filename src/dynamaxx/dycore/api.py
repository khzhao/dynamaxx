# Copyright 2026 dynamaxx

from collections.abc import Sequence
from typing import Protocol

import jax


class DycoreModel(Protocol):
    """Minimal forecast API implemented by dycore models."""

    @property
    def name(self) -> str:
        """Stable model name used in metric outputs."""

    def forecast(
        self,
        initial_state: jax.Array,
        lead_steps: Sequence[int],
        step_seconds: float,
    ) -> jax.Array:
        """Return forecast values shaped as (lead, init, variable, lon, lat)."""
