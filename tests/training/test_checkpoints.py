import json

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.training.checkpoints import (
    latest_checkpoint,
    mark_best_checkpoint,
    restore_checkpoint,
    save_checkpoint,
)
from dynamaxx.training.config import TrainingConfig
from dynamaxx.training.state import (
    build_optimizer,
    initialize_training_state,
)


def test_local_checkpoint_round_trip_preserves_all_resume_state(tmp_path):
    parameters = {
        "input": {"kernel": jnp.asarray([1.0]), "bias": jnp.asarray([0.0])},
        "output": {"kernel": jnp.asarray([0.0]), "bias": jnp.asarray([0.0])},
    }
    config = TrainingConfig(training_steps=2, warmup_steps=0)
    optimizer, _ = build_optimizer(parameters, config)
    training_state = initialize_training_state(
        parameters,
        optimizer,
        random_key=jax.random.key(7),
    )

    checkpoint_path = save_checkpoint(
        tmp_path,
        training_state,
        sampler_state={"position": 3},
        validation_sampler_state={"position": 4},
        metadata={"horizon_hours": 6},
    )
    restored = restore_checkpoint(checkpoint_path)
    mark_best_checkpoint(checkpoint_path, validation_loss=0.25)

    assert latest_checkpoint(tmp_path) == checkpoint_path
    assert restored.sampler_state == {"position": 3}
    assert restored.validation_sampler_state == {"position": 4}
    assert restored.metadata == {"horizon_hours": 6}
    np.testing.assert_array_equal(
        jax.random.key_data(restored.training_state.random_key),
        jax.random.key_data(jax.random.key(7)),
    )
    np.testing.assert_allclose(
        restored.training_state.parameters["input"]["kernel"],
        1.0,
    )
    best_manifest = json.loads((tmp_path / "best.json").read_text())
    assert best_manifest["checkpoint"] == checkpoint_path.name
    assert best_manifest["validation_loss"] == 0.25
