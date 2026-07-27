# Copyright 2026 dynamaxx

from dataclasses import dataclass

import jax
import numpy as np

from dynamaxx.hybrid.api import HybridState
from dynamaxx.training.initialization_cache import (
    InitializedStateCache,
    build_initialized_state_cache,
    default_initialized_state_cache_directory,
)
from dynamaxx.training.target_cache import (
    ModalTargetCache,
    build_modal_target_cache,
    default_modal_target_cache_directory,
)


class _MemoryStateSource:
    def read_state(self, time, *, channels):
        return self.read_state_times(
            [time],
            channels=channels,
            parallel_workers=1,
        )[0]

    def read_state_times(
        self,
        times,
        *,
        channels,
        parallel_workers,
    ):
        del parallel_workers
        values = np.asarray(times, dtype="datetime64[ns]").astype(np.int64)
        return np.broadcast_to(
            values[:, np.newaxis, np.newaxis, np.newaxis],
            (values.size, len(channels), 1, 1),
        ).astype(np.float32)


@dataclass(frozen=True)
class _InitializationModel:
    def initialize(self, weather_state, initial_time):
        del initial_time
        return HybridState(core=weather_state.values * 2.0)


def test_default_cache_directories_distinguish_timestamp_coverage(tmp_path):
    """Full-period caches must not collide with shorter pilot caches."""
    short_times = np.asarray(["2018-01-01"], dtype="datetime64[ns]")
    full_times = np.asarray(
        ["1979-01-01", "2018-01-01"],
        dtype="datetime64[ns]",
    )
    dataset_path = str(tmp_path / "dataset")

    assert default_initialized_state_cache_directory(
        dataset_path,
        "fingerprint",
        times=short_times,
    ) != default_initialized_state_cache_directory(
        dataset_path,
        "fingerprint",
        times=full_times,
    )
    assert default_modal_target_cache_directory(
        dataset_path,
        "fingerprint",
        times=short_times,
    ) != default_modal_target_cache_directory(
        dataset_path,
        "fingerprint",
        times=full_times,
    )


def test_initialized_state_cache_round_trip_preserves_requested_order(tmp_path):
    """Initialized states survive persistence and indexed reads."""
    times = np.asarray(
        [
            "2020-01-01T00",
            "2020-01-01T06",
            "2020-01-01T12",
        ],
        dtype="datetime64[ns]",
    )
    cache = build_initialized_state_cache(
        tmp_path / "cache",
        fingerprint="test-fingerprint",
        times=times,
        source=_MemoryStateSource(),
        model=_InitializationModel(),
        input_variables=("x",),
        devices=[jax.local_devices()[0]],
        parallel_workers=1,
        progress_every=1,
    )

    requested = times[[2, 0, 2]]
    states = cache.read(requested)
    expected = requested.astype(np.int64).astype(np.float32) * 2.0

    np.testing.assert_allclose(states.core[:, 0, 0, 0], expected)
    reopened = InitializedStateCache(
        tmp_path / "cache",
        expected_fingerprint="test-fingerprint",
        preload=False,
    )
    np.testing.assert_allclose(reopened.read(requested).core, states.core)


def test_modal_target_cache_round_trip_preserves_requested_order(tmp_path):
    """Modal targets survive persistence and indexed reads."""
    times = np.asarray(
        [
            "2020-01-01T00",
            "2020-01-01T06",
            "2020-01-01T12",
        ],
        dtype="datetime64[ns]",
    )
    cache = build_modal_target_cache(
        tmp_path / "modal-cache",
        fingerprint="modal-test-fingerprint",
        times=times,
        source=_MemoryStateSource(),
        to_modal=lambda values: values * 3.0,
        target_variables=("x",),
        devices=[jax.local_devices()[0]],
        parallel_workers=1,
        progress_every=1,
    )

    requested = times[[1, 0, 1]]
    expected = requested.astype(np.int64).astype(np.float32) * 3.0
    np.testing.assert_allclose(cache.read(requested)[:, 0, 0, 0], expected)
    reopened = ModalTargetCache(
        tmp_path / "modal-cache",
        expected_fingerprint="modal-test-fingerprint",
        preload=False,
    )
    np.testing.assert_allclose(reopened.read(requested), cache.read(requested))
