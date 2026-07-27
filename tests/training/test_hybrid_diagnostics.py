# Copyright 2026 dynamaxx

import numpy as np
import pytest

from dynamaxx.training.hybrid_diagnostics import stratified_initial_times


def test_stratified_initial_times_span_split_without_crossing_end():
    """Diagnostic starts must span the split and keep truth within it."""
    available_times = np.arange(
        np.datetime64("2019-01-01T00:00:00"),
        np.datetime64("2019-01-04T00:00:00"),
        np.timedelta64(6, "h"),
    )

    selected = stratified_initial_times(
        available_times,
        start="2019-01-01T00:00:00",
        end="2019-01-03T18:00:00",
        count=3,
        maximum_lead_hours=24,
    )

    np.testing.assert_array_equal(
        selected,
        np.asarray(
            [
                "2019-01-01T00:00:00",
                "2019-01-02T00:00:00",
                "2019-01-02T18:00:00",
            ],
            dtype="datetime64[ns]",
        ),
    )
    assert selected[-1] + np.timedelta64(24, "h") <= np.datetime64(
        "2019-01-03T18:00:00"
    )


def test_stratified_initial_times_rejects_oversized_sample():
    """Selection must reject a sample larger than the valid start pool."""
    available_times = np.asarray(
        ["2019-01-01T00:00:00", "2019-01-01T06:00:00"],
        dtype="datetime64[ns]",
    )

    with pytest.raises(ValueError, match="only 1 are available"):
        stratified_initial_times(
            available_times,
            start="2019-01-01T00:00:00",
            end="2019-01-01T06:00:00",
            count=2,
            maximum_lead_hours=6,
        )
