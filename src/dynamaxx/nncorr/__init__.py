# Copyright 2026 dynamaxx

"""NeuralGCM-style neural corrector tutorial package.

Start with `tutorial/00-overview.md` at the repository root of this
worktree. Nothing in here is imported by the production dycore or the
optimization loop; the package exists on the `kzhao--nncorr-tutorial`
branch only.
"""

from dynamaxx.nncorr import (
    checkpoint,
    corrector,
    data,
    features,
    mlp,
    normalize,
    rollout,
    train,
)

__all__ = [
    "checkpoint",
    "corrector",
    "data",
    "features",
    "mlp",
    "normalize",
    "rollout",
    "train",
]
