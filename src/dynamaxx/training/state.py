# Copyright 2026 dynamaxx

"""Optimizer construction and JAX training state for hybrid correction."""

from dataclasses import dataclass
from typing import Any

import jax
import jax.numpy as jnp
import optax

from dynamaxx.training.config import TrainingConfig
from dynamaxx.training.corrector import hidden_weight_decay_mask


@jax.tree_util.register_pytree_node_class
@dataclass(frozen=True)
class TrainingState:
    """Replicable numerical state required to resume an exact update stream."""

    step: jax.Array
    parameters: Any
    ema_parameters: Any
    optimizer_state: optax.OptState
    random_key: jax.Array

    def tree_flatten(self):
        """Return dynamic children for JAX transformations."""
        return (
            self.step,
            self.parameters,
            self.ema_parameters,
            self.optimizer_state,
            self.random_key,
        ), None

    @classmethod
    def tree_unflatten(cls, auxiliary_data, children):
        """Reconstruct a training state from JAX PyTree children."""
        del auxiliary_data
        return cls(*children)


def learning_rate_schedule(config: TrainingConfig) -> optax.Schedule:
    """Build the configured linear-warmup and cosine-decay schedule."""
    decay_steps = config.training_steps - config.warmup_steps
    cosine_schedule = optax.cosine_decay_schedule(
        init_value=config.learning_rate,
        decay_steps=max(decay_steps, 1),
        alpha=config.minimum_learning_rate_ratio,
    )
    if config.warmup_steps == 0:
        return cosine_schedule
    warmup_schedule = optax.linear_schedule(
        init_value=0.0,
        end_value=config.learning_rate,
        transition_steps=config.warmup_steps,
    )
    return optax.join_schedules(
        schedules=(warmup_schedule, cosine_schedule),
        boundaries=(config.warmup_steps,),
    )


def build_optimizer(
    parameters: Any,
    config: TrainingConfig,
) -> tuple[optax.GradientTransformation, optax.Schedule]:
    """Build clipped AdamW with decay restricted to hidden kernels."""
    schedule = learning_rate_schedule(config)
    transformations: list[optax.GradientTransformation] = [
        optax.clip_by_global_norm(config.gradient_clip_norm),
        optax.adamw(
            learning_rate=schedule,
            weight_decay=config.weight_decay,
            mask=hidden_weight_decay_mask(parameters),
        ),
    ]
    if config.decoder_only or config.freeze_corrector:
        frozen_corrector_mask = {
            "corrector": jax.tree_util.tree_map(
                lambda _: True, parameters["corrector"]
            ),
            "decoder": jax.tree_util.tree_map(lambda _: False, parameters["decoder"]),
        }
        transformations.append(optax.masked(optax.set_to_zero(), frozen_corrector_mask))
    optimizer = optax.chain(*transformations)
    return optimizer, schedule


def initialize_training_state(
    parameters: Any,
    optimizer: optax.GradientTransformation,
    *,
    random_key: jax.Array,
) -> TrainingState:
    """Create optimizer and EMA state from initialized neural parameters."""
    return TrainingState(
        step=jnp.asarray(0, dtype=jnp.int32),
        parameters=parameters,
        ema_parameters=parameters,
        optimizer_state=optimizer.init(parameters),
        random_key=random_key,
    )


def update_ema(ema_parameters: Any, parameters: Any, decay: float) -> Any:
    """Update an exponential moving average in FP32."""
    return jax.tree_util.tree_map(
        lambda average, value: (
            decay * average.astype(jnp.float32)
            + (1.0 - decay) * value.astype(jnp.float32)
        ),
        ema_parameters,
        parameters,
    )
