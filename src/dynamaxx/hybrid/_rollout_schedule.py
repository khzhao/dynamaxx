# Copyright 2026 dynamaxx

"""Static scheduling for observed rollouts and truncated backpropagation."""

from dataclasses import dataclass

import numpy as np


def normalize_durations(durations_seconds: tuple[float, ...]) -> tuple[float, ...]:
    """Validate an increasing sequence of positive physical durations."""
    durations = tuple(float(value) for value in durations_seconds)
    if not durations:
        raise ValueError("durations_seconds must not be empty")
    if any(not np.isfinite(value) or value <= 0.0 for value in durations):
        raise ValueError("durations_seconds must be positive and finite")
    if tuple(sorted(set(durations))) != durations:
        raise ValueError("durations_seconds must be unique and increasing")
    return durations


def correction_steps(duration_seconds: float, step_seconds: float) -> int:
    """Convert an exact physical duration to neural-correction steps."""
    step_count = int(round(duration_seconds / step_seconds))
    if step_count < 1 or not np.isclose(
        duration_seconds,
        step_count * step_seconds,
    ):
        raise ValueError("durations_seconds must fall on neural-correction boundaries")
    return step_count


@dataclass(frozen=True)
class RolloutSchedule:
    """Precomputed events for observations and bounded-BPTT boundaries."""

    durations_seconds: tuple[float, ...]
    event_durations_seconds: tuple[float, ...]
    observation_durations: frozenset[float]
    gradient_boundaries: frozenset[float]
    correction_step_seconds: float
    gradient_window_seconds: float | None
    uniform_suffix_start: float
    uniform_suffix_steps: int

    @classmethod
    def build(
        cls,
        *,
        durations_seconds: tuple[float, ...],
        correction_step_seconds: float,
        gradient_window_seconds: float | None,
    ) -> "RolloutSchedule":
        """Build and validate a static rollout schedule."""
        durations = normalize_durations(durations_seconds)
        maximum_duration = durations[-1]
        boundaries: tuple[float, ...] = ()

        if gradient_window_seconds is not None:
            gradient_window_seconds = float(gradient_window_seconds)
            if (
                not np.isfinite(gradient_window_seconds)
                or gradient_window_seconds <= 0.0
            ):
                raise ValueError(
                    "maximum_gradient_duration_seconds must be positive and finite"
                )
            try:
                correction_steps(
                    gradient_window_seconds,
                    correction_step_seconds,
                )
            except ValueError as error:
                raise ValueError(
                    "maximum_gradient_duration_seconds must fall on a "
                    "neural-correction boundary"
                ) from error
            boundaries = tuple(
                boundary_index * gradient_window_seconds
                for boundary_index in range(
                    1,
                    int(np.ceil(maximum_duration / gradient_window_seconds)),
                )
                if boundary_index * gradient_window_seconds < maximum_duration
            )

        uniform_suffix_start = maximum_duration
        uniform_suffix_steps = 0
        if gradient_window_seconds is not None:
            duration_in_windows = maximum_duration / gradient_window_seconds
            suffix_leads_are_aligned = all(
                duration <= gradient_window_seconds
                or np.isclose(
                    duration / gradient_window_seconds,
                    round(duration / gradient_window_seconds),
                )
                for duration in durations
            )
            if (
                duration_in_windows > 1.0
                and np.isclose(duration_in_windows, round(duration_in_windows))
                and suffix_leads_are_aligned
            ):
                uniform_suffix_start = gradient_window_seconds
                uniform_suffix_steps = int(round(duration_in_windows)) - 1

        return cls(
            durations_seconds=durations,
            event_durations_seconds=tuple(sorted(set(durations).union(boundaries))),
            observation_durations=frozenset(durations),
            gradient_boundaries=frozenset(boundaries),
            correction_step_seconds=float(correction_step_seconds),
            gradient_window_seconds=gradient_window_seconds,
            uniform_suffix_start=uniform_suffix_start,
            uniform_suffix_steps=uniform_suffix_steps,
        )

    @property
    def prefix_events(self) -> tuple[float, ...]:
        """Events handled before a possible uniform scan suffix."""
        return tuple(
            duration
            for duration in self.event_durations_seconds
            if duration <= self.uniform_suffix_start
        )

    @property
    def remaining_events(self) -> tuple[float, ...]:
        """Events handled when the suffix cannot use one uniform scan."""
        return tuple(
            duration
            for duration in self.event_durations_seconds
            if duration > self.uniform_suffix_start
        )

    @property
    def uniform_window_steps(self) -> int:
        """Correction steps in one uniform bounded-BPTT window."""
        assert self.gradient_window_seconds is not None
        return correction_steps(
            self.gradient_window_seconds,
            self.correction_step_seconds,
        )

    @property
    def requested_suffix_indices(self) -> np.ndarray:
        """Indices selecting requested observations from the uniform suffix."""
        assert self.gradient_window_seconds is not None
        return np.asarray(
            [
                round(duration / self.gradient_window_seconds) - 2
                for duration in self.durations_seconds
                if duration > self.gradient_window_seconds
            ],
            dtype=np.int32,
        )

    def segment_steps(self, start_seconds: float, end_seconds: float) -> int:
        """Return correction steps between two scheduled events."""
        return correction_steps(
            end_seconds - start_seconds,
            self.correction_step_seconds,
        )
