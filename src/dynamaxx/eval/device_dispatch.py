# Copyright 2026 dynamaxx

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

DeviceDispatchMode = Literal["cpu", "gpu"]

WORKER_SLOT_ENV_VAR = "DYNAMAXX_EVAL_WORKER_SLOT"
WORKER_CUDA_DEVICE_ENV_VAR = "DYNAMAXX_EVAL_CUDA_DEVICE"


@dataclass(frozen=True)
class EvalDeviceDispatch:
    """Device assignment plan for parallel evaluation workers."""

    mode: DeviceDispatchMode
    requested_worker_count: int
    effective_worker_count: int
    worker_cuda_devices: tuple[str | None, ...]
    available_gpu_count: int
    available_cpu_count: int
    reason: str

    @property
    def force_cpu(self) -> bool:
        """Return whether workers should force JAX onto the CPU backend."""
        return self.mode == "cpu"

    def asdict(self) -> dict[str, Any]:
        """Return a JSON-serializable device dispatch record."""
        return {
            "mode": self.mode,
            "requested_worker_count": self.requested_worker_count,
            "effective_worker_count": self.effective_worker_count,
            "available_gpu_count": self.available_gpu_count,
            "available_cpu_count": self.available_cpu_count,
            "worker_cuda_devices": list(self.worker_cuda_devices),
            "reason": self.reason,
        }


def plan_eval_worker_devices(
    worker_count: int,
    *,
    env: Mapping[str, str] | None = None,
    gpu_count: int | None = None,
    cpu_count: int | None = None,
) -> EvalDeviceDispatch:
    """Return a CPU or GPU device plan capped by available execution devices."""
    assert worker_count >= 1
    environment = os.environ if env is None else env
    available_cpu_count = _available_cpu_count(cpu_count)
    if _jax_cpu_requested(environment):
        effective_worker_count = min(worker_count, available_cpu_count)
        return EvalDeviceDispatch(
            mode="cpu",
            requested_worker_count=worker_count,
            effective_worker_count=effective_worker_count,
            worker_cuda_devices=(None,) * effective_worker_count,
            available_gpu_count=0,
            available_cpu_count=available_cpu_count,
            reason="JAX CPU platform requested",
        )

    detected_gpu_count = (
        _detect_jax_gpu_count() if gpu_count is None else max(0, int(gpu_count))
    )
    cuda_devices = _visible_cuda_devices(environment, detected_gpu_count)
    if not cuda_devices:
        effective_worker_count = min(worker_count, available_cpu_count)
        return EvalDeviceDispatch(
            mode="cpu",
            requested_worker_count=worker_count,
            effective_worker_count=effective_worker_count,
            worker_cuda_devices=(None,) * effective_worker_count,
            available_gpu_count=0,
            available_cpu_count=available_cpu_count,
            reason="no JAX GPU backend available",
        )

    effective_worker_count = min(worker_count, len(cuda_devices))
    worker_cuda_devices = cuda_devices[:effective_worker_count]
    return EvalDeviceDispatch(
        mode="gpu",
        requested_worker_count=worker_count,
        effective_worker_count=effective_worker_count,
        worker_cuda_devices=worker_cuda_devices,
        available_gpu_count=len(cuda_devices),
        available_cpu_count=available_cpu_count,
        reason="one worker per visible CUDA device",
    )


def initialize_eval_worker(
    worker_slot_queue: Any,
    worker_cuda_devices: Sequence[str | None],
    force_cpu: bool,
) -> None:
    """Configure a spawned eval worker before JAX-backed modules are imported."""
    worker_slot = int(worker_slot_queue.get())
    os.environ[WORKER_SLOT_ENV_VAR] = str(worker_slot)

    cuda_device = None
    if worker_cuda_devices:
        cuda_device = worker_cuda_devices[worker_slot % len(worker_cuda_devices)]

    if force_cpu or cuda_device is None:
        os.environ["JAX_PLATFORMS"] = "cpu"
        os.environ["JAX_PLATFORM_NAME"] = "cpu"
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ[WORKER_CUDA_DEVICE_ENV_VAR] = ""
        return

    os.environ["CUDA_VISIBLE_DEVICES"] = str(cuda_device)
    os.environ[WORKER_CUDA_DEVICE_ENV_VAR] = str(cuda_device)


def _jax_cpu_requested(env: Mapping[str, str]) -> bool:
    platform_name = env.get("JAX_PLATFORM_NAME", "").strip().lower()
    if platform_name == "cpu":
        return True

    platform_values = [
        value.strip().lower()
        for value in env.get("JAX_PLATFORMS", "").split(",")
        if value.strip()
    ]
    return bool(platform_values) and platform_values[0] == "cpu"


def _detect_jax_gpu_count() -> int:
    try:
        import jax

        return len(jax.devices("gpu"))
    except Exception:
        return 0


def _available_cpu_count(cpu_count: int | None) -> int:
    detected_cpu_count = _detect_cpu_count() if cpu_count is None else int(cpu_count)
    if detected_cpu_count is None or detected_cpu_count < 1:
        return 1
    return detected_cpu_count


def _detect_cpu_count() -> int | None:
    try:
        return len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        return os.cpu_count()


def _visible_cuda_devices(
    env: Mapping[str, str],
    detected_gpu_count: int,
) -> tuple[str, ...]:
    if detected_gpu_count <= 0:
        return ()

    cuda_visible_devices = env.get("CUDA_VISIBLE_DEVICES")
    if cuda_visible_devices is None:
        return tuple(str(device_index) for device_index in range(detected_gpu_count))

    stripped_devices = cuda_visible_devices.strip()
    if stripped_devices.lower() in {"", "-1", "none", "void"}:
        return ()

    requested_devices = tuple(
        device.strip()
        for device in stripped_devices.split(",")
        if device.strip()
    )
    return requested_devices[:detected_gpu_count]
