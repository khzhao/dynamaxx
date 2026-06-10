import jax.numpy as jnp

from dynamaxx.eval.diagnostics import (
    ForecastDiagnostics,
    ForecastIssue,
    diagnose_forecast,
    diagnose_metric_records,
)
from dynamaxx.eval.metrics import MetricRecord


def test_forecast_diagnostics_failed_only_for_errors():
    diagnostics = ForecastDiagnostics(
        issues=(
            ForecastIssue(
                severity="warning",
                code="large_value",
                message="Forecast values are unusually large.",
                value=12.0,
            ),
        ),
    )

    assert not diagnostics.failed
    assert diagnostics.asdict() == {
        "failed": False,
        "issues": [
            {
                "severity": "warning",
                "code": "large_value",
                "message": "Forecast values are unusually large.",
                "value": 12.0,
            },
        ],
    }


def test_diagnose_forecast_accepts_finite_values():
    diagnostics = diagnose_forecast(jnp.ones((2, 3)))

    assert not diagnostics.failed
    assert diagnostics.issues == ()


def test_diagnose_forecast_rejects_nonfinite_values():
    diagnostics = diagnose_forecast(jnp.asarray([1.0, jnp.nan, jnp.inf]))

    assert diagnostics.failed
    assert len(diagnostics.issues) == 1
    issue = diagnostics.issues[0]
    assert issue.severity == "error"
    assert issue.code == "nonfinite_forecast"
    assert issue.value == 2


def test_diagnose_metric_records_rejects_nonfinite_scores():
    diagnostics = diagnose_metric_records(
        (
            MetricRecord(
                model_name="candidate",
                variable="temperature",
                channel_name="2m_temperature",
                lead_hours=6,
                rmse=float("inf"),
                mae=1.0,
                bias=float("nan"),
                skill_vs_persistence=None,
            ),
        ),
    )

    assert diagnostics.failed
    assert diagnostics.issues[0].code == "nonfinite_metric"
    assert diagnostics.issues[0].value == 2
