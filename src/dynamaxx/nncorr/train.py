# Copyright 2026 dynamaxx

"""Training skeleton: hand-rolled Adam, curriculum, checkpoints, etiquette.

This file intentionally does NOT run end-to-end until you finish exercises
1-6. It is the assembly diagram, with the boring parts (EMA, checkpoint
cadence, GPU etiquette) done and the parts you learn from left open.
"""

from __future__ import annotations

import dataclasses
import subprocess
from typing import Any

import jax
import numpy as np


@dataclasses.dataclass(frozen=True)
class TrainConfig:
    """Hyperparameters for one training run — freeze a copy per experiment."""

    seed: int = 0
    hidden_dims: tuple[int, ...] = (256, 256, 256)
    learning_rate: float = 1e-4
    warmup_steps: int = 200
    total_steps: int = 5000
    grad_clip_norm: float = 1.0
    ema_decay: float = 0.999
    # Curriculum: (train_step_threshold, target_count). Start with ONE 6 h
    # target; extend the horizon only after the short-rollout loss has
    # dropped, mirroring the NeuralGCM curriculum. Longer horizons change
    # the loss landscape (exposure to your own drift) — expect a loss jump
    # at each transition and do not panic.
    curriculum: tuple[tuple[int, int], ...] = ((0, 1), (1000, 4), (3000, 12))
    checkpoint_every: int = 500
    checkpoint_path: str = "nncorr_params.npz"


def adam_update(
    params: Any,
    grads: Any,
    moments: tuple[Any, Any],
    step: jax.Array,
    *,
    learning_rate: float,
    beta1: float = 0.9,
    beta2: float = 0.999,
    eps: float = 1e-8,
):
    """EXERCISE 6 — one Adam step over arbitrary pytrees.

    Return `(new_params, (new_m, new_v))` where every leaf follows

        m <- b1 m + (1 - b1) g
        v <- b2 v + (1 - b2) g^2
        m_hat = m / (1 - b1^t),  v_hat = v / (1 - b2^t)      (t = step + 1)
        p <- p - lr * m_hat / (sqrt(v_hat) + eps)

    Constraints that make this a JAX exercise rather than a formula copy:
      * one `jax.tree_util.tree_map` per moment/param update — no manual
        recursion, no flattening;
      * `step` is a TRACED int32 scalar (it lives inside jit): the bias
        corrections must be computed with jnp on the traced value, and
        nothing here may trigger a Python branch on it;
      * the whole update must be wrappable in `jax.jit` with `donate_
        argnums` on (params, moments) — think about why donation is safe
        here and what it saves at this parameter count (~0.5 MB — nothing;
        at 7 GB of optimizer state — everything).

    Acceptance test (matches a NumPy reference to 1e-6):
      uv run pytest tests/nncorr/test_exercises.py -k adam -m exercise
    """
    raise NotImplementedError("EXERCISE 6: see tutorial/05-training.md")


def clip_by_global_norm(grads: Any, max_norm: float) -> Any:
    """EXERCISE 6b — rescale grads so the GLOBAL l2 norm is <= max_norm.

    One tree_map for the squares, one `jnp.sqrt(sum(...))`, one tree_map to
    scale. No epsilon games: use `jnp.minimum(1.0, max_norm / norm)` and
    make the zero-gradient case well-defined.
    """
    raise NotImplementedError("EXERCISE 6b")


def ema_update(ema_params: Any, params: Any, decay: float) -> Any:
    """Exponential moving average of parameters (evaluate with these)."""
    return jax.tree_util.tree_map(
        lambda e, p: decay * e + (1.0 - decay) * p, ema_params, params
    )


def learning_rate_at(step: int, config: TrainConfig) -> float:
    """Linear warmup then cosine decay to zero — computed host-side.

    Host-side on purpose: the LR is a Python float fed in as a regular
    argument each step. If you instead branch on the step INSIDE jit,
    every distinct Python value would recompile; if you trace it, fine too
    — but then keep it a traced scalar throughout. Mixing the two styles
    is the classic recompilation bug (the optimization loop once lost an
    entire candidate to per-sample recompilation; see tutorial/05).
    """
    if step < config.warmup_steps:
        return config.learning_rate * (step + 1) / config.warmup_steps
    progress = (step - config.warmup_steps) / max(
        1, config.total_steps - config.warmup_steps
    )
    return float(config.learning_rate * 0.5 * (1.0 + np.cos(np.pi * progress)))


def targets_at(step: int, config: TrainConfig) -> int:
    """Current curriculum horizon (number of 6 h targets)."""
    count = config.curriculum[0][1]
    for threshold, value in config.curriculum:
        if step >= threshold:
            count = value
    return count


def assert_gpu_is_free() -> None:
    """Refuse to start if ANY process holds a GPU (loop etiquette).

    The optimization loop owns the four L4s during its eval phases and this
    box's standing rule is one process per GPU, never oversubscribed. Run
    real training only when `nvidia-smi` shows zero compute processes, or
    export JAX_PLATFORMS=cpu and accept toy scale.
    """
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        check=False,
    )
    busy = [line for line in result.stdout.splitlines() if line.strip()]
    assert not busy, (
        f"{len(busy)} compute process(es) hold GPUs — the optimization loop "
        "is likely mid-eval. Train later, or JAX_PLATFORMS=cpu for smoke "
        "tests."
    )


def main() -> None:  # pragma: no cover - assembled by the reader
    """Assembly diagram. Wire the pieces as exercises complete.

    TODO(you), in order:
      1. bundle = data.build_grid_bundle(); source = WeatherBench2Source()
      2. stats: normalize.pooled_channel_stats(source.path, range(1980,
         2014)) -> feature vectors via feature_stats_from_channels; static
         stack via features.static_features(+ load_static_surface_fields).
      3. params = mlp.init_mlp_params(key, spec.feature_dim, config.
         hidden_dims, spec.output_dim); moments = zeros_like pytrees.
      4. jit the update: loss+grad (rollout.rollout_loss via value_and_
         grad), clip, adam. Decide argnums/donation deliberately.
      5. loop: sample window (data.sample_training_window), encode t0
         (data.encode_analysis), decode targets to nodal SI dicts (
         corrector.decode_nodal_si after encoding each target — think
         about why encode-then-decode rather than raw pressure-level
         targets; tutorial/04 discusses), step, log, checkpoint via
         ckpt_lib.save_pytree, ema_update.
      6. curriculum via targets_at(); expect and log the loss jumps.

    Keep the first real run tiny: T21 (spectral_wavenumbers=21 in
    build_grid_bundle), one target, ~200 steps, CPU. You are debugging
    plumbing, not fitting the atmosphere.
    """
    raise NotImplementedError("wire this up as the exercises complete")


if __name__ == "__main__":
    main()
