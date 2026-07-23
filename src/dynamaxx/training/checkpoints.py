# Copyright 2026 dynamaxx

"""Atomic local-only checkpoints for hybrid training."""

import json
import os
import pickle
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jax

from dynamaxx.training.state import TrainingState

_LATEST_MANIFEST = "latest.json"
_BEST_MANIFEST = "best.json"


@dataclass(frozen=True)
class RestoredCheckpoint:
    """Numerical and host-side state restored from one local checkpoint."""

    training_state: TrainingState
    sampler_state: dict[str, Any]
    validation_sampler_state: dict[str, Any]
    metadata: dict[str, Any]


def _atomic_write_bytes(path: Path, contents: bytes) -> None:
    """Write and fsync a file before atomically replacing its destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(contents)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def save_checkpoint(
    directory: Path,
    training_state: TrainingState,
    *,
    sampler_state: dict[str, Any],
    validation_sampler_state: dict[str, Any],
    metadata: dict[str, Any],
) -> Path:
    """Save one complete checkpoint locally without contacting W&B."""
    directory = Path(directory).expanduser().resolve()
    host_state = jax.device_get(training_state)
    step = int(host_state.step)
    checkpoint_name = f"step_{step:09d}.pkl"
    checkpoint_path = directory / checkpoint_name
    payload = {
        "format_version": 1,
        "training_state": host_state,
        "sampler_state": sampler_state,
        "validation_sampler_state": validation_sampler_state,
        "metadata": metadata,
    }
    _atomic_write_bytes(
        checkpoint_path,
        pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL),
    )
    manifest = {
        "format_version": 1,
        "checkpoint": checkpoint_name,
        "step": step,
    }
    _atomic_write_bytes(
        directory / _LATEST_MANIFEST,
        json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8"),
    )
    return checkpoint_path


def latest_checkpoint(directory: Path) -> Path | None:
    """Return the checkpoint named by the local latest manifest."""
    directory = Path(directory).expanduser().resolve()
    manifest_path = directory / _LATEST_MANIFEST
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checkpoint_path = directory / str(manifest["checkpoint"])
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"latest checkpoint does not exist: {checkpoint_path}")
    return checkpoint_path


def mark_best_checkpoint(checkpoint_path: Path, *, validation_loss: float) -> None:
    """Point the local best manifest at a selected checkpoint."""
    checkpoint_path = Path(checkpoint_path).expanduser().resolve()
    if not checkpoint_path.is_file():
        raise FileNotFoundError(checkpoint_path)
    manifest = {
        "format_version": 1,
        "checkpoint": checkpoint_path.name,
        "validation_loss": float(validation_loss),
    }
    _atomic_write_bytes(
        checkpoint_path.parent / _BEST_MANIFEST,
        json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8"),
    )


def restore_checkpoint(path: Path) -> RestoredCheckpoint:
    """Restore a trusted local checkpoint produced by this module."""
    path = Path(path).expanduser().resolve()
    with path.open("rb") as checkpoint_file:
        payload = pickle.load(checkpoint_file)
    if payload.get("format_version") != 1:
        raise ValueError("unsupported checkpoint format version")
    return RestoredCheckpoint(
        training_state=payload["training_state"],
        sampler_state=payload["sampler_state"],
        validation_sampler_state=payload["validation_sampler_state"],
        metadata=payload["metadata"],
    )
