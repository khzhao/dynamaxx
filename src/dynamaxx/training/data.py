# Copyright 2026 dynamaxx

"""Chronological WeatherBench2 trajectory sampling for recurrent training."""

import copy
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Protocol

import jax
import numpy as np

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.weather import WeatherState


@dataclass(frozen=True)
class HostWeatherState:
    """Named weather values retained in host memory until explicit sharding."""

    values: np.ndarray
    variables: tuple[str, ...]

    def __post_init__(self):
        values = np.asarray(self.values)
        variables = tuple(map(str, self.variables))
        if values.ndim < 3 or values.shape[-3] != len(variables):
            raise ValueError("weather values and variables have incompatible shapes")
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "variables", variables)

    @property
    def leading_shape(self) -> tuple[int, ...]:
        """Axes before variable, longitude, and latitude."""
        return tuple(self.values.shape[:-3])


class InitializedStateReader(Protocol):
    """Local cache interface consumed by the trajectory sampler."""

    def read(self, times: np.ndarray) -> Any:
        """Return initialized hybrid states in the requested timestamp order."""


class ModalTargetReader(Protocol):
    """Local modal-truth cache interface consumed by the sampler."""

    def read(self, times: np.ndarray) -> np.ndarray:
        """Return modal target arrays in the requested timestamp order."""


@dataclass(frozen=True)
class SampledTrajectory:
    """One host-side batch of truth starts and logarithmic lead targets."""

    initial_times: np.ndarray
    initial_state: HostWeatherState | WeatherState | None
    targets: HostWeatherState | WeatherState
    lead_hours: tuple[int, ...]
    initialized_states: Any | None = None
    targets_are_modal: bool = False

    def __post_init__(self):
        initial_times = np.asarray(self.initial_times, dtype="datetime64[ns]")
        lead_hours = tuple(int(value) for value in self.lead_hours)
        if initial_times.ndim != 1 or initial_times.size == 0:
            raise ValueError("initial_times must be a non-empty vector")
        if not lead_hours or any(value <= 0 for value in lead_hours):
            raise ValueError("lead_hours must contain positive values")
        if tuple(sorted(set(lead_hours))) != lead_hours:
            raise ValueError("lead_hours must be unique and increasing")
        if (self.initial_state is None) == (self.initialized_states is None):
            raise ValueError(
                "exactly one of initial_state and initialized_states must be present"
            )
        if self.initial_state is not None and self.initial_state.leading_shape != (
            initial_times.size,
        ):
            raise ValueError("initial_state must have one leading batch axis")
        if self.initialized_states is not None:
            leading_sizes = {
                int(np.shape(leaf)[0])
                for leaf in jax.tree_util.tree_leaves(self.initialized_states)
                if np.ndim(leaf) >= 1
            }
            if leading_sizes != {initial_times.size}:
                raise ValueError("initialized_states must have one leading batch axis")
        if self.targets.leading_shape != (initial_times.size, len(lead_hours)):
            raise ValueError("targets must have leading (batch, lead) axes")
        object.__setattr__(self, "initial_times", initial_times)
        object.__setattr__(self, "lead_hours", lead_hours)
        object.__setattr__(self, "targets_are_modal", bool(self.targets_are_modal))


class WeatherBench2TrajectorySampler:
    """Uniformly sample split-contained recurrent forecast trajectories."""

    def __init__(
        self,
        source: WeatherBench2Source,
        *,
        start: Any,
        end: Any,
        lead_hours: tuple[int, ...],
        input_channels: tuple[str, ...],
        target_channels: tuple[str, ...],
        seed: int,
        parallel_workers: int = 1,
        initialized_state_cache: InitializedStateReader | None = None,
        modal_target_cache: ModalTargetReader | None = None,
    ):
        self.source = source
        self.start = np.datetime64(start, "ns")
        self.end = np.datetime64(end, "ns")
        self.lead_hours = tuple(int(value) for value in lead_hours)
        self.input_channels = tuple(map(str, input_channels))
        self.target_channels = tuple(map(str, target_channels))
        if isinstance(parallel_workers, bool) or not isinstance(parallel_workers, int):
            raise TypeError("parallel_workers must be an integer")
        if parallel_workers < 1:
            raise ValueError("parallel_workers must be positive")
        self.parallel_workers = parallel_workers
        self.initialized_state_cache = initialized_state_cache
        self.modal_target_cache = modal_target_cache
        if not self.lead_hours or any(value <= 0 for value in self.lead_hours):
            raise ValueError("lead_hours must contain positive values")
        if tuple(sorted(set(self.lead_hours))) != self.lead_hours:
            raise ValueError("lead_hours must be unique and increasing")
        if not self.input_channels or not self.target_channels:
            raise ValueError("input_channels and target_channels must not be empty")

        all_times = source.available_times(self.start, self.end)
        latest_initial_time = self.end - np.timedelta64(max(self.lead_hours), "h")
        valid_initial_times = all_times[all_times <= latest_initial_time]
        if valid_initial_times.size == 0:
            raise ValueError("the split contains no complete training trajectory")
        target_offsets = np.asarray(self.lead_hours, dtype="timedelta64[h]")
        candidate_targets = (
            valid_initial_times[:, np.newaxis] + target_offsets[np.newaxis, :]
        )
        all_times_ns = all_times.astype("datetime64[ns]").astype(np.int64)
        target_times_ns = candidate_targets.astype("datetime64[ns]").astype(np.int64)
        complete_mask = np.all(np.isin(target_times_ns, all_times_ns), axis=1)
        self._initial_times = valid_initial_times[complete_mask]
        if self._initial_times.size == 0:
            raise ValueError("no candidate has every requested target timestamp")
        self._random = np.random.default_rng(seed)
        self._request_executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="trajectory-read",
        )

    @property
    def candidate_count(self) -> int:
        """Number of complete truth-start windows in the split."""
        return int(self._initial_times.size)

    @property
    def candidate_times(self) -> np.ndarray:
        """Immutable complete truth-start timestamps."""
        candidate_times = self._initial_times.view()
        candidate_times.setflags(write=False)
        return candidate_times

    def sample(self, batch_size: int) -> SampledTrajectory:
        """Read a random batch and all active logarithmic targets."""
        if isinstance(batch_size, bool) or not isinstance(batch_size, int):
            raise TypeError("batch_size must be an integer")
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        indices = self._random.integers(
            0,
            self._initial_times.size,
            size=batch_size,
        )
        initial_times = self._initial_times[indices]
        target_times = (
            initial_times[:, np.newaxis]
            + np.asarray(
                self.lead_hours,
                dtype="timedelta64[h]",
            )[np.newaxis, :]
        )
        flat_target_times = target_times.reshape(-1)
        if self.modal_target_cache is None and self.initialized_state_cache is None:
            request_workers = max(1, self.parallel_workers // 2)
            initial_future = self._request_executor.submit(
                self.source.read_state_times,
                initial_times,
                channels=self.input_channels,
                parallel_workers=request_workers,
            )
            target_future = self._request_executor.submit(
                self.source.read_state_times,
                flat_target_times,
                channels=self.target_channels,
                parallel_workers=request_workers,
            )
            initial_values = initial_future.result()
            initialized_states = None
        elif self.modal_target_cache is None:
            target_future = self._request_executor.submit(
                self.source.read_state_times,
                flat_target_times,
                channels=self.target_channels,
                parallel_workers=self.parallel_workers,
            )
            initial_values = None
            initialized_states = self.initialized_state_cache.read(initial_times)
        else:
            target_future = None
            if self.initialized_state_cache is None:
                initial_values = self.source.read_state_times(
                    initial_times,
                    channels=self.input_channels,
                    parallel_workers=self.parallel_workers,
                )
                initialized_states = None
            else:
                initial_values = None
                initialized_states = self.initialized_state_cache.read(initial_times)
        flat_target_values = (
            self.modal_target_cache.read(flat_target_times)
            if self.modal_target_cache is not None
            else target_future.result()
        )
        target_values = flat_target_values.reshape(
            batch_size,
            len(self.lead_hours),
            *flat_target_values.shape[1:],
        )
        return SampledTrajectory(
            initial_times=initial_times,
            initial_state=(
                None
                if initial_values is None
                else HostWeatherState(
                    values=initial_values,
                    variables=self.input_channels,
                )
            ),
            initialized_states=initialized_states,
            targets=HostWeatherState(
                values=target_values,
                variables=self.target_channels,
            ),
            lead_hours=self.lead_hours,
            targets_are_modal=self.modal_target_cache is not None,
        )

    def state_dict(self) -> dict[str, Any]:
        """Return the exact NumPy sampler state for local checkpointing."""
        return dict(copy.deepcopy(self._random.bit_generator.state))

    def load_state_dict(self, state: dict[str, Any]) -> None:
        """Restore an exact NumPy sampler state."""
        self._random.bit_generator.state = copy.deepcopy(state)

    def close(self) -> None:
        """Release loader threads after all submitted reads have completed."""
        self._request_executor.shutdown(wait=True, cancel_futures=True)


class PrefetchingTrajectorySampler:
    """Overlap one deterministic trajectory read with accelerator execution."""

    def __init__(self, sampler: WeatherBench2TrajectorySampler, *, batch_size: int):
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        self.sampler = sampler
        self.batch_size = int(batch_size)
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="trajectory-prefetch",
        )
        self._future: Future[tuple[SampledTrajectory, dict[str, Any]]] | None = None
        self._committed_state = sampler.state_dict()

    @property
    def candidate_count(self) -> int:
        """Wrapped sampler's candidate count."""
        return self.sampler.candidate_count

    def _load_next(self) -> tuple[SampledTrajectory, dict[str, Any]]:
        sampled = self.sampler.sample(self.batch_size)
        return sampled, self.sampler.state_dict()

    def _submit_next(self) -> None:
        self._future = self._executor.submit(self._load_next)

    def sample(self, batch_size: int) -> SampledTrajectory:
        """Return the next ordered batch and immediately prefetch its successor."""
        if int(batch_size) != self.batch_size:
            raise ValueError("prefetch batch size must remain constant")
        if self._future is None:
            self._submit_next()
        assert self._future is not None
        sampled, state_after_sample = self._future.result()
        self._committed_state = state_after_sample
        self._submit_next()
        return sampled

    def state_dict(self) -> dict[str, Any]:
        """Return RNG state after the last consumed, not prefetched, batch."""
        return copy.deepcopy(self._committed_state)

    def close(self) -> None:
        """Cancel unused prefetch work and close all loader threads."""
        if self._future is not None:
            self._future.cancel()
        self._executor.shutdown(wait=True, cancel_futures=True)
        self.sampler.close()


def stack_initialized_states(states: list[Any]) -> Any:
    """Stack independently initialized recurrent states on a batch axis."""
    if not states:
        raise ValueError("states must not be empty")
    return jax.tree_util.tree_map(lambda *leaves: np.stack(leaves), *states)
