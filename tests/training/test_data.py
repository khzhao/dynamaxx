# Copyright 2026 dynamaxx

import threading

import numpy as np

from dynamaxx.training.data import (
    PrefetchingTrajectorySampler,
    WeatherBench2TrajectorySampler,
)


class _MemoryWeatherSource:
    def __init__(self):
        self.times = np.arange(
            np.datetime64("2020-01-01T00", "h"),
            np.datetime64("2020-01-04T00", "h"),
            np.timedelta64(6, "h"),
        ).astype("datetime64[ns]")
        self._lock = threading.Lock()
        self.read_count = 0

    def available_times(self, start, end):
        start = np.datetime64(start, "ns")
        end = np.datetime64(end, "ns")
        return self.times[(self.times >= start) & (self.times <= end)]

    def read_state_times(
        self,
        times,
        *,
        channels,
        parallel_workers,
    ):
        del parallel_workers
        times = np.asarray(times, dtype="datetime64[ns]")
        with self._lock:
            self.read_count += 1
        values = times.astype(np.int64).astype(np.float32)
        return np.broadcast_to(
            values[:, np.newaxis, np.newaxis, np.newaxis],
            (times.size, len(channels), 1, 1),
        ).copy()


def _sampler(source, seed):
    return WeatherBench2TrajectorySampler(
        source,
        start="2020-01-01T00",
        end="2020-01-03T18",
        lead_hours=(6,),
        input_channels=("x",),
        target_channels=("x",),
        seed=seed,
        parallel_workers=4,
    )


def test_prefetch_preserves_consumed_sampler_state_for_exact_resume():
    source = _MemoryWeatherSource()
    reference_sampler = _sampler(source, seed=7)
    expected_first = reference_sampler.sample(3)
    expected_second = reference_sampler.sample(3)
    reference_sampler.close()

    wrapped_sampler = _sampler(source, seed=7)
    prefetch = PrefetchingTrajectorySampler(wrapped_sampler, batch_size=3)
    actual_first = prefetch.sample(3)
    committed_state = prefetch.state_dict()

    resumed_sampler = _sampler(source, seed=0)
    resumed_sampler.load_state_dict(committed_state)
    resumed_second = resumed_sampler.sample(3)

    np.testing.assert_array_equal(
        actual_first.initial_times, expected_first.initial_times
    )
    np.testing.assert_array_equal(
        resumed_second.initial_times,
        expected_second.initial_times,
    )
    prefetch.close()
    resumed_sampler.close()
