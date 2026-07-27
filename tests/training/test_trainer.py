# Copyright 2026 dynamaxx

from dataclasses import dataclass

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from dynamaxx.hybrid.model import PreparedHybridModel
from dynamaxx.training.config import TrainingConfig
from dynamaxx.training.data import SampledTrajectory
from dynamaxx.training.losses import HybridForecastLoss, SpectralLossStatistics
from dynamaxx.training.state import build_optimizer, initialize_training_state
from dynamaxx.training.trainer import HybridTrainer, _raise_for_rejected_update
from dynamaxx.weather import WeatherState


@dataclass(frozen=True)
class _TrainingCore:
    inner_step_seconds: float = 900.0

    def initialize(self, weather_state, initial_time):
        del initial_time
        return weather_state.values

    def corrector_inputs(self, state):
        return state[0, 0, 0]

    def to_native_tendency(self, state, nodal_tendency):
        del state
        return nodal_tendency

    def advance_one_inner_step(self, state, additive_tendency):
        return state + additive_tendency

    def decode(self, state):
        return WeatherState(values=state, variables=("x",))


def _corrector(parameters, inputs):
    del inputs
    return parameters["output"]["kernel"][0]


def _decoder(parameters, inputs, raw_observation):
    del inputs
    return raw_observation.with_values(raw_observation.values + parameters["offset"])


def test_decoder_only_update_freezes_corrector_and_skips_rollout():
    """Interface calibration updates only the decoder from lead-zero truth."""
    config = TrainingConfig(
        horizon_hours=24,
        decoder_only=True,
        training_steps=2,
        warmup_steps=0,
        per_device_batch_size=1,
        gradient_accumulation_steps=1,
    )

    def rollout_must_not_run(parameters, inputs):
        del parameters, inputs
        raise AssertionError("decoder-only training must not call the corrector")

    model = PreparedHybridModel(
        core=_TrainingCore(),
        corrector=rollout_must_not_run,
        decoder=_decoder,
    )
    loss = HybridForecastLoss(
        to_modal=lambda values: values,
        total_wavenumber=jnp.zeros((1, 1), dtype=jnp.int32),
        modal_mask=jnp.ones((1, 1)),
        statistics=SpectralLossStatistics(
            coefficient_variance=jnp.ones((1, 1)),
            climatological_power=jnp.ones((1, 1)),
            channel_weights=jnp.ones((1,)),
        ),
        bias_axis_name="devices",
    )
    parameters = {
        "corrector": {"unchanged": jnp.asarray(3.0)},
        "decoder": {"offset": jnp.asarray(0.0)},
    }
    optimizer, learning_rate = build_optimizer(parameters, config)
    state = initialize_training_state(
        parameters,
        optimizer,
        random_key=jax.random.key(0),
    )
    trainer = HybridTrainer(
        model=model,
        loss=loss,
        optimizer=optimizer,
        learning_rate=learning_rate,
        config=config,
        devices=[jax.local_devices()[0]],
    )
    sampled = SampledTrajectory(
        initial_times=np.asarray(["2018-01-01"], dtype="datetime64[ns]"),
        initial_state=WeatherState(
            values=jnp.zeros((1, 1, 1, 1)),
            variables=("x",),
        ),
        targets=WeatherState(
            values=jnp.ones((1, 1, 1, 1, 1)),
            variables=("x",),
        ),
        lead_hours=(0,),
    )
    replicated_state = jax.tree_util.tree_map(
        lambda value: jnp.stack([jnp.asarray(value)]),
        state,
    )

    updated_state, metrics = trainer._update(
        replicated_state,
        trainer.prepare(sampled),
    )

    assert float(updated_state.parameters["corrector"]["unchanged"][0]) == 3.0
    assert float(updated_state.parameters["decoder"]["offset"][0]) != 0.0
    assert float(metrics["correction/rms"][0]) == 0.0


def test_compiled_training_update_backpropagates_through_six_hour_rollout():
    """A compiled update differentiates through every correction step."""
    config = TrainingConfig(
        training_steps=2,
        warmup_steps=0,
        per_device_batch_size=1,
        gradient_accumulation_steps=1,
        decoder_hidden_size=0,
    )
    model = PreparedHybridModel(core=_TrainingCore(), corrector=_corrector)
    loss = HybridForecastLoss(
        to_modal=lambda values: values,
        total_wavenumber=jnp.zeros((1, 1), dtype=jnp.int32),
        modal_mask=jnp.ones((1, 1)),
        statistics=SpectralLossStatistics(
            coefficient_variance=jnp.ones((1, 1)),
            climatological_power=jnp.ones((1, 1)),
            channel_weights=jnp.ones((1,)),
        ),
        bias_axis_name="devices",
    )
    parameters = {
        "output": {
            "kernel": jnp.asarray([0.0]),
            "bias": jnp.asarray([0.0]),
        }
    }
    optimizer, learning_rate = build_optimizer(parameters, config)
    state = initialize_training_state(
        parameters,
        optimizer,
        random_key=jax.random.key(0),
    )
    device = jax.local_devices()[0]
    trainer = HybridTrainer(
        model=model,
        loss=loss,
        optimizer=optimizer,
        learning_rate=learning_rate,
        config=config,
        devices=[device],
    )
    sampled = SampledTrajectory(
        initial_times=np.asarray(["2018-01-01"], dtype="datetime64[ns]"),
        initial_state=WeatherState(
            values=jnp.zeros((1, 1, 1, 1)),
            variables=("x",),
        ),
        targets=WeatherState(
            values=jnp.ones((1, 1, 1, 1, 1)),
            variables=("x",),
        ),
        lead_hours=(6,),
    )
    batch = trainer.prepare(sampled)
    replicated_state = jax.tree_util.tree_map(
        lambda value: jnp.stack([jnp.asarray(value)]),
        state,
    )

    updated_state, metrics = trainer._update(replicated_state, batch)
    updated_kernel = updated_state.parameters["output"]["kernel"][0, 0]

    assert int(updated_state.step[0]) == 1
    assert float(jnp.abs(updated_kernel)) > 0.0
    assert bool(jnp.isfinite(metrics["loss"][0]))
    assert float(metrics["update/applied"][0]) == 1.0
    assert float(metrics["correction/rms"][0]) == 0.0


def test_frozen_corrector_update_trains_decoder_at_six_hours():
    """A decoder-only rollout preserves corrector weights and advances the core."""
    config = TrainingConfig(
        training_steps=2,
        warmup_steps=0,
        per_device_batch_size=1,
        gradient_accumulation_steps=1,
        freeze_corrector=True,
        interface_loss_weight=0.0,
    )
    model = PreparedHybridModel(
        core=_TrainingCore(),
        corrector=_corrector,
        decoder=_decoder,
    )
    loss = HybridForecastLoss(
        to_modal=lambda values: values,
        total_wavenumber=jnp.zeros((1, 1), dtype=jnp.int32),
        modal_mask=jnp.ones((1, 1)),
        statistics=SpectralLossStatistics(
            coefficient_variance=jnp.ones((1, 1)),
            climatological_power=jnp.ones((1, 1)),
            channel_weights=jnp.ones((1,)),
        ),
        bias_axis_name="devices",
    )
    parameters = {
        "corrector": {
            "output": {
                "kernel": jnp.asarray([0.0]),
                "bias": jnp.asarray([0.0]),
            }
        },
        "decoder": {"offset": jnp.asarray(0.0)},
    }
    optimizer, learning_rate = build_optimizer(parameters, config)
    state = initialize_training_state(
        parameters,
        optimizer,
        random_key=jax.random.key(0),
    )
    trainer = HybridTrainer(
        model=model,
        loss=loss,
        optimizer=optimizer,
        learning_rate=learning_rate,
        config=config,
        devices=[jax.local_devices()[0]],
    )
    sampled = SampledTrajectory(
        initial_times=np.asarray(["2018-01-01"], dtype="datetime64[ns]"),
        initial_state=WeatherState(
            values=jnp.zeros((1, 1, 1, 1)),
            variables=("x",),
        ),
        targets=WeatherState(
            values=jnp.asarray([0.0, 1.0]).reshape(1, 2, 1, 1, 1),
            variables=("x",),
        ),
        lead_hours=(0, 6),
    )
    replicated_state = jax.tree_util.tree_map(
        lambda value: jnp.stack([jnp.asarray(value)]),
        state,
    )

    updated_state, metrics = trainer._update(
        replicated_state,
        trainer.prepare(sampled),
    )

    assert float(updated_state.parameters["corrector"]["output"]["kernel"][0, 0]) == 0.0
    assert float(updated_state.parameters["decoder"]["offset"][0]) != 0.0
    assert bool(jnp.isfinite(metrics["loss"][0]))


def test_rejected_nonfinite_update_stops_training():
    """A guarded no-op update cannot masquerade as training progress."""
    replicated_metrics = {
        "update/applied": jnp.asarray([0.0]),
        "loss": jnp.asarray([jnp.nan]),
        "gradient/global_norm": jnp.asarray([jnp.nan]),
        "forecast/nonfinite_fraction": jnp.asarray([0.125]),
        "correction/rms": jnp.asarray([2.0]),
        "correction/max_abs": jnp.asarray([4.0]),
    }

    with pytest.raises(FloatingPointError, match="non-finite optimizer update"):
        _raise_for_rejected_update(replicated_metrics, step=1)


def test_packed_accumulation_matches_sequential_microbatches():
    """Packing changes execution shape without changing the optimizer update."""
    config = TrainingConfig(
        training_steps=2,
        warmup_steps=0,
        per_device_batch_size=1,
        gradient_accumulation_steps=2,
        log_every_steps=1,
        decoder_hidden_size=0,
    )
    model = PreparedHybridModel(core=_TrainingCore(), corrector=_corrector)
    loss = HybridForecastLoss(
        to_modal=lambda values: values,
        total_wavenumber=jnp.zeros((1, 1), dtype=jnp.int32),
        modal_mask=jnp.ones((1, 1)),
        statistics=SpectralLossStatistics(
            coefficient_variance=jnp.ones((1, 1)),
            climatological_power=jnp.ones((1, 1)),
            channel_weights=jnp.ones((1,)),
        ),
        bias_axis_name="devices",
    )
    parameters = {
        "output": {
            "kernel": jnp.asarray([0.0]),
            "bias": jnp.asarray([0.0]),
        }
    }
    optimizer, learning_rate = build_optimizer(parameters, config)
    initial_state = initialize_training_state(
        parameters,
        optimizer,
        random_key=jax.random.key(0),
    )
    device = jax.local_devices()[0]
    sequential_trainer = HybridTrainer(
        model=model,
        loss=loss,
        optimizer=optimizer,
        learning_rate=learning_rate,
        config=config,
        devices=[device],
    )
    packed_trainer = HybridTrainer(
        model=model,
        loss=loss,
        optimizer=optimizer,
        learning_rate=learning_rate,
        config=config,
        devices=[device],
        pack_accumulation=True,
    )
    sampled = SampledTrajectory(
        initial_times=np.asarray(
            ["2018-01-01T00", "2018-01-01T06"],
            dtype="datetime64[ns]",
        ),
        initial_state=WeatherState(
            values=jnp.zeros((2, 1, 1, 1)),
            variables=("x",),
        ),
        targets=WeatherState(
            values=jnp.asarray([1.0, 3.0]).reshape(2, 1, 1, 1, 1),
            variables=("x",),
        ),
        lead_hours=(6,),
    )

    def replicate_state():
        return jax.tree_util.tree_map(
            lambda value: jnp.stack([jnp.asarray(value)]),
            initial_state,
        )

    sequential_state, sequential_metrics = sequential_trainer._update(
        replicate_state(),
        sequential_trainer.prepare(sampled),
    )
    packed_state, packed_metrics = packed_trainer._update(
        replicate_state(),
        packed_trainer.prepare(sampled),
    )

    assert sequential_trainer.prepare(sampled).targets.shape[:3] == (1, 2, 1)
    assert packed_trainer.prepare(sampled).targets.shape[:3] == (1, 1, 2)
    for sequential_leaf, packed_leaf in zip(
        jax.tree_util.tree_leaves(sequential_state),
        jax.tree_util.tree_leaves(packed_state),
        strict=True,
    ):
        if jax.dtypes.issubdtype(sequential_leaf.dtype, jax.dtypes.prng_key):
            np.testing.assert_array_equal(
                jax.random.key_data(sequential_leaf),
                jax.random.key_data(packed_leaf),
            )
        else:
            np.testing.assert_allclose(
                sequential_leaf,
                packed_leaf,
                rtol=1e-6,
                atol=1e-7,
            )
    for metric_name in sequential_metrics:
        np.testing.assert_allclose(
            sequential_metrics[metric_name],
            packed_metrics[metric_name],
            rtol=1e-6,
            atol=1e-7,
        )
