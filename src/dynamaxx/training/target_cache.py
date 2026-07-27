# Copyright 2026 dynamaxx

"""Persistent cache for fixed modal forecast targets."""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

import jax
import numpy as np

from dynamaxx.data.weatherbench2 import WeatherBench2Source

logger = logging.getLogger("dynamaxx.training.target_cache")

_CACHE_FORMAT_VERSION = 1


def modal_target_cache_fingerprint(
    *,
    dataset_path: str,
    target_variables: tuple[str, ...],
    core_configuration: Any,
) -> str:
    """Return a stable identifier for one truth-to-modal transformation."""
    payload = {
        "format_version": _CACHE_FORMAT_VERSION,
        "dataset_path": str(dataset_path),
        "target_variables": list(map(str, target_variables)),
        "core_configuration": repr(core_configuration),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def default_modal_target_cache_directory(
    dataset_path: str,
    fingerprint: str,
    *,
    times: np.ndarray | None = None,
) -> Path:
    """Place large modal-target caches beside a local source dataset."""
    if "://" in dataset_path:
        raise ValueError("remote datasets require an explicit --target-cache-directory")
    dataset = Path(dataset_path).expanduser().resolve()
    cache_label = fingerprint[:20]
    if times is not None:
        normalized_times = np.unique(np.asarray(times, dtype="datetime64[ns]"))
        time_digest = hashlib.sha256(normalized_times.astype(np.int64).tobytes())
        cache_label = f"{fingerprint[:12]}-{time_digest.hexdigest()[:8]}"
    return dataset.parent / "dynamaxx-training-cache" / "modal-targets" / cache_label


class ModalTargetCache:
    """Read timestamp-indexed modal truth into host memory."""

    def __init__(
        self,
        directory: Path,
        *,
        expected_fingerprint: str | None = None,
        preload: bool = True,
    ):
        self.directory = Path(directory).expanduser().resolve()
        if not (self.directory / "complete.json").exists():
            raise FileNotFoundError(f"incomplete modal-target cache: {self.directory}")
        metadata = json.loads((self.directory / "metadata.json").read_text())
        if metadata.get("format_version") != _CACHE_FORMAT_VERSION:
            raise ValueError("unsupported modal-target cache format")
        if (
            expected_fingerprint is not None
            and metadata.get("fingerprint") != expected_fingerprint
        ):
            raise ValueError("modal-target cache fingerprint mismatch")
        self.metadata = metadata
        self.times = np.asarray(
            np.load(self.directory / "times.npy", mmap_mode="r"),
            dtype="datetime64[ns]",
        )
        self._time_to_index = {
            int(value): index for index, value in enumerate(self.times.astype(np.int64))
        }
        modal_targets = np.load(
            self.directory / "modal_targets.npy",
            mmap_mode="r",
        )
        self._modal_targets = (
            np.array(modal_targets, copy=True) if preload else modal_targets
        )

    @property
    def byte_count(self) -> int:
        """Bytes occupied by cached modal truth."""
        return int(self._modal_targets.nbytes)

    def contains(self, times: np.ndarray) -> bool:
        """Return whether every requested timestamp exists in this cache."""
        requested = np.asarray(times, dtype="datetime64[ns]").astype(np.int64)
        return all(int(value) in self._time_to_index for value in requested)

    def read(self, times: np.ndarray) -> np.ndarray:
        """Return modal targets in requested timestamp order."""
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
                f"timestamp {missing} is absent from the modal-target cache"
            ) from error
        return np.asarray(self._modal_targets[indices])


def _batch_sharding(devices: list[jax.Device]) -> jax.sharding.NamedSharding:
    mesh = jax.sharding.Mesh(
        np.asarray(devices, dtype=object),
        ("devices",),
    )
    return jax.sharding.NamedSharding(
        mesh,
        jax.sharding.PartitionSpec("devices"),
    )


def build_modal_target_cache(
    directory: Path,
    *,
    fingerprint: str,
    times: np.ndarray,
    source: WeatherBench2Source,
    to_modal: Any,
    target_variables: tuple[str, ...],
    devices: list[jax.Device],
    parallel_workers: int,
    progress_every: int = 256,
    preload: bool = True,
) -> ModalTargetCache:
    """Build or resume modal truth with one data-parallel transform per wave."""
    directory = Path(directory).expanduser().resolve()
    times = np.unique(np.asarray(times, dtype="datetime64[ns]"))
    if times.ndim != 1 or times.size == 0:
        raise ValueError("times must be a non-empty vector")
    if not devices:
        raise ValueError("at least one transform device is required")
    if parallel_workers < 1:
        raise ValueError("parallel_workers must be positive")

    complete_path = directory / "complete.json"
    if complete_path.exists():
        cache = ModalTargetCache(
            directory,
            expected_fingerprint=fingerprint,
            preload=preload,
        )
        if not cache.contains(times):
            raise ValueError("complete modal-target cache lacks requested times")
        return cache

    directory.mkdir(parents=True, exist_ok=True)
    metadata_path = directory / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
        if metadata.get("fingerprint") != fingerprint:
            raise ValueError("incomplete modal-target cache fingerprint mismatch")
        stored_times = np.asarray(
            np.load(directory / "times.npy"),
            dtype="datetime64[ns]",
        )
        if not np.array_equal(stored_times, times):
            raise ValueError("incomplete modal-target cache timestamps changed")
        modal_path = directory / "modal_targets.npy"
        modal_targets = (
            np.lib.format.open_memmap(modal_path, mode="r+")
            if modal_path.exists()
            else None
        )
        completed = np.lib.format.open_memmap(
            directory / "completed.npy",
            mode="r+",
        )
    else:
        np.save(directory / "times.npy", times)
        metadata: dict[str, Any] = {
            "format_version": _CACHE_FORMAT_VERSION,
            "fingerprint": fingerprint,
            "state_count": int(times.size),
        }
        metadata_path.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        modal_targets = None
        completed = np.lib.format.open_memmap(
            directory / "completed.npy",
            mode="w+",
            dtype=np.bool_,
            shape=(times.size,),
        )
        completed[:] = False
        completed.flush()

    device_count = len(devices)
    sharding = _batch_sharding(devices)
    transform = jax.pmap(to_modal, devices=devices)
    pending_indices = np.flatnonzero(~np.asarray(completed))
    completed_before = int(np.sum(completed))
    start_time = time.monotonic()
    logger.info(
        "building modal-target cache %s (%d/%d already complete)",
        directory,
        completed_before,
        times.size,
    )
    for wave_start in range(0, pending_indices.size, device_count):
        wave_indices = pending_indices[wave_start : wave_start + device_count]
        wave_times = times[wave_indices]
        wave_values = source.read_state_times(
            wave_times,
            channels=target_variables,
            parallel_workers=parallel_workers,
        )
        if wave_indices.size < device_count:
            padding = np.repeat(
                wave_values[-1:],
                device_count - wave_indices.size,
                axis=0,
            )
            wave_values = np.concatenate((wave_values, padding), axis=0)
        device_values = jax.device_put(wave_values, sharding)
        wave_modal = np.asarray(jax.device_get(transform(device_values)))

        if modal_targets is None:
            modal_targets = np.lib.format.open_memmap(
                directory / "modal_targets.npy",
                mode="w+",
                dtype=wave_modal.dtype,
                shape=(times.size, *wave_modal.shape[1:]),
            )
            metadata["modal_shape"] = list(wave_modal.shape[1:])
            metadata["modal_dtype"] = wave_modal.dtype.str
            metadata_path.write_text(
                json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        modal_targets[wave_indices] = wave_modal[: wave_indices.size]
        completed[wave_indices] = True

        completed_count = int(np.sum(completed))
        if (
            completed_count == times.size
            or completed_count // progress_every
            > (completed_count - wave_indices.size) // progress_every
        ):
            modal_targets.flush()
            completed.flush()
            elapsed = max(time.monotonic() - start_time, 1.0e-12)
            built = completed_count - completed_before
            logger.info(
                "modal-target cache %d/%d (%.2f targets/s)",
                completed_count,
                times.size,
                built / elapsed,
            )

    if modal_targets is None:
        raise RuntimeError("modal-target cache did not produce any values")
    modal_targets.flush()
    completed.flush()
    if not bool(np.all(completed)):
        raise RuntimeError("modal-target cache build ended with missing rows")
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
    del modal_targets, completed
    logger.info("modal-target cache complete at %s", directory)
    return ModalTargetCache(
        directory,
        expected_fingerprint=fingerprint,
        preload=preload,
    )
