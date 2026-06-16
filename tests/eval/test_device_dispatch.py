# Copyright 2026 dynamaxx

import os

from dynamaxx.eval.device_dispatch import (
    WORKER_CUDA_DEVICE_ENV_VAR,
    WORKER_SLOT_ENV_VAR,
    initialize_eval_worker,
    plan_eval_worker_devices,
)


class _SlotQueue:
    def __init__(self, *slots: int):
        self.slots = list(slots)

    def get(self) -> int:
        return self.slots.pop(0)


def test_plan_eval_worker_devices_caps_workers_to_visible_cuda_devices():
    """Workers should not oversubscribe the visible CUDA device list."""
    dispatch = plan_eval_worker_devices(
        5,
        env={"CUDA_VISIBLE_DEVICES": "2,5"},
        gpu_count=2,
        cpu_count=16,
    )

    assert dispatch.mode == "gpu"
    assert dispatch.requested_worker_count == 5
    assert dispatch.effective_worker_count == 2
    assert dispatch.available_gpu_count == 2
    assert dispatch.worker_cuda_devices == ("2", "5")
    assert not dispatch.force_cpu


def test_plan_eval_worker_devices_uses_default_cuda_ordinals():
    """Workers should use local CUDA ordinals when visibility is unrestricted."""
    dispatch = plan_eval_worker_devices(4, env={}, gpu_count=3, cpu_count=16)

    assert dispatch.mode == "gpu"
    assert dispatch.requested_worker_count == 4
    assert dispatch.effective_worker_count == 3
    assert dispatch.available_gpu_count == 3
    assert dispatch.worker_cuda_devices == ("0", "1", "2")


def test_plan_eval_worker_devices_respects_cpu_platform_request():
    """An explicit JAX CPU platform request should disable GPU assignment."""
    dispatch = plan_eval_worker_devices(
        3,
        env={"JAX_PLATFORMS": "cpu"},
        gpu_count=4,
        cpu_count=2,
    )

    assert dispatch.mode == "cpu"
    assert dispatch.requested_worker_count == 3
    assert dispatch.effective_worker_count == 2
    assert dispatch.available_cpu_count == 2
    assert dispatch.worker_cuda_devices == (None, None)
    assert dispatch.force_cpu


def test_plan_eval_worker_devices_uses_cpu_without_gpus():
    """Workers should fall back to CPU mode when no GPU backend is available."""
    dispatch = plan_eval_worker_devices(5, env={}, gpu_count=0, cpu_count=3)

    assert dispatch.mode == "cpu"
    assert dispatch.requested_worker_count == 5
    assert dispatch.effective_worker_count == 3
    assert dispatch.available_cpu_count == 3
    assert dispatch.worker_cuda_devices == (None, None, None)
    assert dispatch.force_cpu


def test_initialize_eval_worker_sets_assigned_cuda_device(monkeypatch):
    """The worker initializer should expose only its assigned CUDA device."""
    monkeypatch.delenv("JAX_PLATFORMS", raising=False)
    monkeypatch.delenv("JAX_PLATFORM_NAME", raising=False)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0,1")

    initialize_eval_worker(_SlotQueue(1), ("2", "5"), force_cpu=False)

    assert os.environ[WORKER_SLOT_ENV_VAR] == "1"
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "5"
    assert os.environ[WORKER_CUDA_DEVICE_ENV_VAR] == "5"
    assert "JAX_PLATFORMS" not in os.environ
    assert "JAX_PLATFORM_NAME" not in os.environ


def test_initialize_eval_worker_forces_cpu(monkeypatch):
    """CPU workers should hide CUDA devices and force the JAX CPU backend."""
    monkeypatch.setenv("JAX_PLATFORMS", "cuda,cpu")
    monkeypatch.setenv("JAX_PLATFORM_NAME", "gpu")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0,1")

    initialize_eval_worker(_SlotQueue(0), (None, None), force_cpu=True)

    assert os.environ[WORKER_SLOT_ENV_VAR] == "0"
    assert os.environ["JAX_PLATFORMS"] == "cpu"
    assert os.environ["JAX_PLATFORM_NAME"] == "cpu"
    assert os.environ["CUDA_VISIBLE_DEVICES"] == ""
    assert os.environ[WORKER_CUDA_DEVICE_ENV_VAR] == ""
