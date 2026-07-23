# Copyright 2026 dynamaxx

"""Persistent host cache for deterministic hybrid-model initial states."""

import hashlib
import json
import logging
import pickle
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import jax
import numpy as np

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.weather import WeatherState

logger = logging.getLogger("dynamaxx.training.initialization_cache")

_CACHE_FORMAT_VERSION = 1


def initialized_state_cache_fingerprint(
    *,
    dataset_path: str,
    dycore_name: str,
    input_variables: tuple[str, ...],
    core_configuration: Any,
) -> str:
    """Return a stable identifier for one deterministic initialization mapping."""
    payload = {
        "format_version": _CACHE_FORMAT_VERSION,
        "dataset_path": str(dataset_path),
        "dycore_name": str(dycore_name),
        "input_variables": list(map(str, input_variables)),
        "core_configuration": repr(core_configuration),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def default_initialized_state_cache_directory(
    dataset_path: str,
    fingerprint: str,
) -> Path:
    """Place large local caches beside a filesystem-backed source dataset."""
    if "://" in dataset_path:
        raise ValueError("remote datasets require an explicit --state-cache-directory")
    dataset = Path(dataset_path).expanduser().resolve()
    return (
        dataset.parent
        / "dynamaxx-training-cache"
        / "initialized-states"
        / fingerprint[:20]
    )


class InitializedStateCache:
    """Read a complete timestamp-indexed PyTree cache into host memory."""

    def __init__(
        self,
        directory: Path,
        *,
        expected_fingerprint: str | None = None,
        preload: bool = True,
    ):
        self.directory = Path(directory).expanduser().resolve()
        complete_path = self.directory / "complete.json"
        if not complete_path.exists():
            raise FileNotFoundError(
                f"incomplete initialized-state cache: {self.directory}"
            )
        metadata = json.loads((self.directory / "metadata.json").read_text())
        if metadata.get("format_version") != _CACHE_FORMAT_VERSION:
            raise ValueError("unsupported initialized-state cache format")
        if (
            expected_fingerprint is not None
            and metadata.get("fingerprint") != expected_fingerprint
        ):
            raise ValueError("initialized-state cache fingerprint mismatch")

        self.metadata = metadata
        self.times = np.asarray(
            np.load(self.directory / "times.npy", mmap_mode="r"),
            dtype="datetime64[ns]",
        )
        time_integers = self.times.astype(np.int64)
        self._time_to_index = {
            int(time_integer): index for index, time_integer in enumerate(time_integers)
        }
        with (self.directory / "tree.pkl").open("rb") as file:
            self._tree_definition = pickle.load(file)

        leaves = []
        for leaf_index in range(int(metadata["leaf_count"])):
            array = np.load(
                self.directory / f"leaf_{leaf_index:03d}.npy",
                mmap_mode="r",
            )
            leaves.append(np.array(array, copy=True) if preload else array)
        self._leaves = tuple(leaves)

    @property
    def byte_count(self) -> int:
        """Bytes occupied by all cached numeric state leaves."""
        return sum(int(leaf.nbytes) for leaf in self._leaves)

    def contains(self, times: np.ndarray) -> bool:
        """Return whether every requested timestamp exists in this cache."""
        requested = np.asarray(times, dtype="datetime64[ns]").astype(np.int64)
        return all(int(value) in self._time_to_index for value in requested)

    def read(self, times: np.ndarray) -> Any:
        """Return host arrays for initialized states in requested order."""
        requested = np.asarray(times, dtype="datetime64[ns]")
        if requested.ndim != 1 or requested.size == 0:
            raise ValueError("times must be a non-empty vector")
        try:
            indices = np.asarray(
                [
                    self._time_to_index[int(value)]
                    for value in requested.astype(np.int64)
                ],
                dtype=np.int64,
            )
        except KeyError as error:
            missing = np.datetime64(int(error.args[0]), "ns")
            raise KeyError(
                f"timestamp {missing} is absent from the state cache"
            ) from error
        selected_leaves = [np.asarray(leaf[indices]) for leaf in self._leaves]
        return jax.tree_util.tree_unflatten(self._tree_definition, selected_leaves)


def _host_state_leaves(state: Any) -> tuple[list[np.ndarray], Any]:
    leaves, tree_definition = jax.tree_util.tree_flatten(jax.device_get(state))
    host_leaves = [np.asarray(leaf) for leaf in leaves]
    if not host_leaves:
        raise ValueError("initialized state must contain numeric leaves")
    return host_leaves, tree_definition


def _initialize_on_device(
    *,
    model: Any,
    values: np.ndarray,
    variables: tuple[str, ...],
    initial_time: np.datetime64,
    device: jax.Device,
) -> tuple[list[np.ndarray], Any]:
    device_values = jax.device_put(values, device)
    state = model.initialize(
        WeatherState(values=device_values, variables=variables),
        initial_time,
    )
    return _host_state_leaves(state)


def _open_cache_arrays(
    directory: Path,
    metadata: dict[str, Any],
) -> tuple[list[np.memmap], np.memmap]:
    leaves = [
        np.lib.format.open_memmap(
            directory / f"leaf_{leaf_index:03d}.npy",
            mode="r+",
        )
        for leaf_index in range(int(metadata["leaf_count"]))
    ]
    completed = np.lib.format.open_memmap(
        directory / "completed.npy",
        mode="r+",
    )
    return leaves, completed


def build_initialized_state_cache(
    directory: Path,
    *,
    fingerprint: str,
    times: np.ndarray,
    source: WeatherBench2Source,
    model: Any,
    input_variables: tuple[str, ...],
    devices: list[jax.Device],
    parallel_workers: int,
    progress_every: int = 128,
    preload: bool = True,
) -> InitializedStateCache:
    """Build or resume a complete cache using concurrent device initialization."""
    directory = Path(directory).expanduser().resolve()
    times = np.unique(np.asarray(times, dtype="datetime64[ns]"))
    if times.ndim != 1 or times.size == 0:
        raise ValueError("times must be a non-empty vector")
    if not devices:
        raise ValueError("at least one initialization device is required")
    if parallel_workers < 1:
        raise ValueError("parallel_workers must be positive")

    complete_path = directory / "complete.json"
    if complete_path.exists():
        cache = InitializedStateCache(
            directory,
            expected_fingerprint=fingerprint,
            preload=preload,
        )
        if not cache.contains(times):
            raise ValueError("complete initialized-state cache lacks requested times")
        return cache

    directory.mkdir(parents=True, exist_ok=True)
    metadata_path = directory / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
        if metadata.get("fingerprint") != fingerprint:
            raise ValueError("incomplete initialized-state cache fingerprint mismatch")
        stored_times = np.asarray(
            np.load(directory / "times.npy"),
            dtype="datetime64[ns]",
        )
        if not np.array_equal(stored_times, times):
            raise ValueError("incomplete initialized-state cache timestamps changed")
        cache_leaves, completed = _open_cache_arrays(directory, metadata)
    else:
        np.save(directory / "times.npy", times.astype("datetime64[ns]"))
        first_values = source.read_state(
            times[0],
            channels=input_variables,
        )
        first_leaves, tree_definition = _initialize_on_device(
            model=model,
            values=first_values,
            variables=input_variables,
            initial_time=times[0],
            device=devices[0],
        )
        with (directory / "tree.pkl").open("wb") as file:
            pickle.dump(tree_definition, file, protocol=pickle.HIGHEST_PROTOCOL)
        metadata = {
            "format_version": _CACHE_FORMAT_VERSION,
            "fingerprint": fingerprint,
            "leaf_count": len(first_leaves),
            "state_count": int(times.size),
            "leaf_specs": [
                {"shape": list(leaf.shape), "dtype": leaf.dtype.str}
                for leaf in first_leaves
            ],
        }
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        cache_leaves = [
            np.lib.format.open_memmap(
                directory / f"leaf_{leaf_index:03d}.npy",
                mode="w+",
                dtype=leaf.dtype,
                shape=(times.size, *leaf.shape),
            )
            for leaf_index, leaf in enumerate(first_leaves)
        ]
        completed = np.lib.format.open_memmap(
            directory / "completed.npy",
            mode="w+",
            dtype=np.bool_,
            shape=(times.size,),
        )
        completed[:] = False
        for cache_leaf, first_leaf in zip(cache_leaves, first_leaves, strict=True):
            cache_leaf[0] = first_leaf
        completed[0] = True
        completed.flush()

    with (directory / "tree.pkl").open("rb") as file:
        expected_tree_definition = pickle.load(file)
    pending_indices = np.flatnonzero(~np.asarray(completed))
    if pending_indices.size:
        worker_count = min(parallel_workers, len(devices))
        start_time = time.monotonic()
        completed_before = int(np.sum(completed))
        logger.info(
            "building initialized-state cache %s (%d/%d already complete)",
            directory,
            completed_before,
            times.size,
        )
        with ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="state-initializer",
        ) as executor:
            for wave_start in range(0, pending_indices.size, worker_count):
                wave_indices = pending_indices[wave_start : wave_start + worker_count]
                wave_times = times[wave_indices]
                wave_values = source.read_state_times(
                    wave_times,
                    channels=input_variables,
                    parallel_workers=parallel_workers,
                )
                futures = [
                    executor.submit(
                        _initialize_on_device,
                        model=model,
                        values=wave_values[wave_offset],
                        variables=input_variables,
                        initial_time=wave_times[wave_offset],
                        device=devices[wave_offset % len(devices)],
                    )
                    for wave_offset in range(wave_indices.size)
                ]
                for cache_index, future in zip(wave_indices, futures, strict=True):
                    state_leaves, tree_definition = future.result()
                    if tree_definition != expected_tree_definition:
                        raise ValueError("initialized-state PyTree structure changed")
                    if len(state_leaves) != len(cache_leaves):
                        raise ValueError("initialized-state PyTree structure changed")
                    for cache_leaf, state_leaf in zip(
                        cache_leaves,
                        state_leaves,
                        strict=True,
                    ):
                        if cache_leaf.shape[1:] != state_leaf.shape:
                            raise ValueError("initialized-state leaf shape changed")
                        cache_leaf[cache_index] = state_leaf
                    completed[cache_index] = True

                completed_count = int(np.sum(completed))
                if (
                    completed_count == times.size
                    or completed_count // progress_every
                    > (completed_count - wave_indices.size) // progress_every
                ):
                    completed.flush()
                    elapsed = max(time.monotonic() - start_time, 1.0e-12)
                    built = completed_count - completed_before
                    logger.info(
                        "initialized-state cache %d/%d (%.2f states/s)",
                        completed_count,
                        times.size,
                        built / elapsed,
                    )

    for cache_leaf in cache_leaves:
        cache_leaf.flush()
    completed.flush()
    if not bool(np.all(completed)):
        raise RuntimeError("initialized-state cache build ended with missing rows")
    complete_path.write_text(
        json.dumps(
            {
                "format_version": _CACHE_FORMAT_VERSION,
                "fingerprint": fingerprint,
                "state_count": int(times.size),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    del cache_leaves, completed
    logger.info("initialized-state cache complete at %s", directory)
    return InitializedStateCache(
        directory,
        expected_fingerprint=fingerprint,
        preload=preload,
    )
