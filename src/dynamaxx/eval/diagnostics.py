# Copyright 2026 dynamaxx

from dataclasses import dataclass
from math import isfinite
from typing import Any, Literal

import jax
import jax.numpy as jnp

IssueSeverity = Literal["error", "warning"]


@dataclass(frozen=True)
class ForecastIssue:
    """One official diagnostic issue found during evaluation."""

    severity: IssueSeverity
    code: str
    message: str
    value: int | float | str | None = None

    def __post_init__(self):
        assert self.severity in ("error", "warning")
        assert self.code
        assert self.message

    def asdict(self) -> dict[str, Any]:
        """Return a JSON-serializable issue description."""
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "value": self.value,
        }


@dataclass(frozen=True)
class ForecastDiagnostics:
    """Official model-agnostic diagnostics for one forecast."""

    issues: tuple[ForecastIssue, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "issues", tuple(self.issues))

    @property
    def failed(self) -> bool:
        """Return whether any diagnostic issue rejects the forecast."""
        return any(issue.severity == "error" for issue in self.issues)

    def asdict(self) -> dict[str, Any]:
        """Return a JSON-serializable diagnostics summary."""
        return {
            "failed": self.failed,
            "issues": [issue.asdict() for issue in self.issues],
        }


def diagnose_forecast(values: jax.Array) -> ForecastDiagnostics:
    """Return official diagnostics for forecast values."""
    values = jnp.asarray(values)
    finite_count = int(jnp.sum(jnp.isfinite(values)))
    total_count = values.size
    nonfinite_count = total_count - finite_count
    if nonfinite_count == 0:
        return ForecastDiagnostics()

    return ForecastDiagnostics(
        issues=(
            ForecastIssue(
                severity="error",
                code="nonfinite_forecast",
                message="Forecast contains NaN or Inf values.",
                value=nonfinite_count,
            ),
        ),
    )


def diagnose_metric_records(records: tuple[Any, ...]) -> ForecastDiagnostics:
    """Return official diagnostics for serialized metric values."""
    nonfinite_count = 0
    for record in records:
        values = (
            record.rmse,
            record.mae,
            record.bias,
            record.skill_vs_persistence,
        )
        nonfinite_count += sum(
            value is not None and not isfinite(value) for value in values
        )

    if nonfinite_count == 0:
        return ForecastDiagnostics()

    return ForecastDiagnostics(
        issues=(
            ForecastIssue(
                severity="error",
                code="nonfinite_metric",
                message="Metric records contain NaN or Inf values.",
                value=nonfinite_count,
            ),
        ),
    )
