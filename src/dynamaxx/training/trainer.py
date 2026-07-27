# Copyright 2026 dynamaxx

"""Eight-device recurrent BPTT trainer for prepared hybrid models."""

import logging
import time
from dataclasses import dataclass
from typing import Any, Protocol

import jax
import jax.numpy as jnp
import numpy as np
import optax

from dynamaxx.hybrid.rollout import rollout_at_durations_with_tendency_statistics
from dynamaxx.training.checkpoints import mark_best_checkpoint, save_checkpoint
from dynamaxx.training.config import TrainingConfig
from dynamaxx.training.data import SampledTrajectory
from dynamaxx.training.logging import WandbMetricsLogger
from dynamaxx.training.losses import HybridForecastLoss
from dynamaxx.training.state import TrainingState, update_ema
from dynamaxx.training.weatherbench_metrics import WeatherBenchValidationMetrics
from dynamaxx.weather import WeatherState

logger = logging.getLogger("dynamaxx.training")
_PMAP_AXIS_NAME = "devices"
_REMATERIALIZATION_POLICIES = {
    "nothing": jax.checkpoint_policies.nothing_saveable,
    "dots": jax.checkpoint_policies.dots_saveable,
    "dots-no-batch": jax.checkpoint_policies.dots_with_no_batch_dims_saveable,
}


class TrajectorySampler(Protocol):
    """Sampler interface shared by direct and prefetched implementations."""

    def sample(self, batch_size: int) -> SampledTrajectory:
        """Return one training trajectory batch."""

    def state_dict(self) -> dict[str, Any]:
        """Return exact state after the last consumed batch."""


@jax.tree_util.register_pytree_node_class
@dataclass(frozen=True)
class PreparedTrainingBatch:
    """Initialized recurrent states and targets sharded for one update."""

    initial_states: Any
    targets: jax.Array
    targets_are_modal: bool = False

    def tree_flatten(self):
        """Return dynamic children for JAX transformations."""
        return (self.initial_states, self.targets), bool(self.targets_are_modal)

    @classmethod
    def tree_unflatten(cls, auxiliary_data, children):
        """Reconstruct a prepared batch from JAX PyTree children."""
        return cls(*children, targets_are_modal=bool(auxiliary_data))


def _stack_states(states: list[Any]) -> Any:
    """Stack initialized states in host memory before one sharded transfer."""
    if not states:
        raise ValueError("states must not be empty")
    host_states = [jax.device_get(state) for state in states]
    return jax.tree_util.tree_map(
        lambda *leaves: np.stack([np.asarray(leaf) for leaf in leaves]),
        *host_states,
    )


def prepare_training_batch(
    model: Any,
    sampled: SampledTrajectory,
    *,
    devices: list[jax.Device],
    accumulation_steps: int,
    per_device_batch_size: int,
    pack_accumulation: bool = False,
) -> PreparedTrainingBatch:
    """Encode truth starts once and arrange accumulation/device/local axes."""
    device_count = len(devices)
    if device_count == 0:
        raise ValueError("devices must not be empty")
    expected_batch_size = device_count * accumulation_steps * per_device_batch_size
    if sampled.initial_times.size != expected_batch_size:
        raise ValueError(
            f"sample contains {sampled.initial_times.size} examples; "
            f"expected {expected_batch_size}"
        )
    if sampled.initialized_states is not None:
        stacked_states = jax.tree_util.tree_map(
            np.asarray,
            sampled.initialized_states,
        )
    else:
        assert sampled.initial_state is not None
        initialized_states = []
        for example_index, initial_time in enumerate(sampled.initial_times):
            weather_state = WeatherState(
                values=sampled.initial_state.values[example_index],
                variables=sampled.initial_state.variables,
            )
            initialized_states.append(model.initialize(weather_state, initial_time))
        stacked_states = _stack_states(initialized_states)

    def arrange_device_axes(values: Any) -> np.ndarray:
        host_values = np.asarray(values).reshape(
            accumulation_steps,
            device_count,
            per_device_batch_size,
            *np.shape(values)[1:],
        )
        device_values = np.swapaxes(host_values, 0, 1)
        if not pack_accumulation:
            return device_values
        return device_values.reshape(
            device_count,
            1,
            accumulation_steps * per_device_batch_size,
            *np.shape(values)[1:],
        )

    mesh = jax.sharding.Mesh(
        np.asarray(devices, dtype=object),
        ("devices",),
    )
    batch_sharding = jax.sharding.NamedSharding(
        mesh,
        jax.sharding.PartitionSpec("devices"),
    )

    def shard(values: Any) -> jax.Array:
        arranged = arrange_device_axes(values)
        return jax.device_put(arranged, batch_sharding)

    return PreparedTrainingBatch(
        initial_states=jax.tree_util.tree_map(
            shard,
            stacked_states,
        ),
        targets=shard(sampled.targets.values),
        targets_are_modal=sampled.targets_are_modal,
    )


def _tree_all_finite(tree: Any) -> jax.Array:
    """Return whether every numeric leaf is finite."""
    finite_leaves = [
        jnp.all(jnp.isfinite(leaf)) for leaf in jax.tree_util.tree_leaves(tree)
    ]
    return jnp.all(jnp.stack(finite_leaves)) if finite_leaves else jnp.asarray(True)


def _replicate(tree: Any, devices: list[jax.Device]) -> Any:
    """Replicate a host PyTree with the sharding returned by the pmap update."""
    mesh = jax.sharding.Mesh(
        np.asarray(devices, dtype=object),
        ("devices",),
    )
    sharding = jax.sharding.NamedSharding(
        mesh,
        jax.sharding.PartitionSpec("devices"),
    )

    def replicate_leaf(value: Any) -> jax.Array:
        is_prng_key = jax.dtypes.issubdtype(value.dtype, jax.dtypes.prng_key)
        host_value = np.asarray(
            jax.device_get(jax.random.key_data(value) if is_prng_key else value)
        )
        replicated = np.broadcast_to(
            host_value,
            (len(devices), *host_value.shape),
        )
        sharded = jax.device_put(replicated, sharding)
        return jax.random.wrap_key_data(sharded) if is_prng_key else sharded

    return jax.tree_util.tree_map(
        replicate_leaf,
        tree,
    )


def _first_replica(tree: Any) -> Any:
    """Copy the first replica of a PyTree to the host."""
    return jax.device_get(jax.tree_util.tree_map(lambda value: value[0], tree))


def _raise_for_rejected_update(
    replicated_metrics: dict[str, jax.Array],
    *,
    step: int,
) -> None:
    """Stop training when the numerical guard rejects an optimizer update."""
    update_applied = float(jax.device_get(replicated_metrics["update/applied"][0]))
    if update_applied == 1.0:
        return
    metrics = {
        name: float(value) for name, value in _first_replica(replicated_metrics).items()
    }
    raise FloatingPointError(
        "non-finite optimizer update rejected at "
        f"step {step}: loss={metrics['loss']}, "
        f"gradient_norm={metrics['gradient/global_norm']}, "
        "forecast_nonfinite_fraction="
        f"{metrics['forecast/nonfinite_fraction']}, "
        f"correction_rms={metrics['correction/rms']}, "
        f"correction_max_abs={metrics['correction/max_abs']}"
    )


class HybridTrainer:
    """Compile and execute one static logarithmic curriculum stage."""

    def __init__(
        self,
        *,
        model: Any,
        loss: HybridForecastLoss,
        optimizer: optax.GradientTransformation,
        learning_rate: optax.Schedule,
        config: TrainingConfig,
        devices: list[jax.Device] | None = None,
        rematerialize_rollout: bool = True,
        pack_accumulation: bool = False,
        rematerialization_policy: str = "nothing",
        weatherbench_metrics: WeatherBenchValidationMetrics | None = None,
    ):
        self.model = model
        self.loss = loss
        self.optimizer = optimizer
        self.learning_rate = learning_rate
        self.config = config
        self.devices = list(jax.local_devices() if devices is None else devices)
        self.rematerialize_rollout = bool(rematerialize_rollout)
        self.pack_accumulation = bool(pack_accumulation)
        self.weatherbench_metrics = weatherbench_metrics
        try:
            self.rematerialization_policy = _REMATERIALIZATION_POLICIES[
                rematerialization_policy
            ]
        except KeyError as error:
            choices = ", ".join(sorted(_REMATERIALIZATION_POLICIES))
            raise ValueError(
                f"rematerialization_policy must be one of: {choices}"
            ) from error
        self.execution_accumulation_steps = (
            1 if self.pack_accumulation else config.gradient_accumulation_steps
        )
        if not self.devices:
            raise RuntimeError("training requires at least one local JAX device")
        if loss.bias_axis_name != _PMAP_AXIS_NAME:
            raise ValueError(
                f"loss.bias_axis_name must be {_PMAP_AXIS_NAME!r} for training"
            )
        self._update = jax.pmap(
            self._device_update,
            axis_name=_PMAP_AXIS_NAME,
            devices=self.devices,
            donate_argnums=(0,),
        )
        self._validate = jax.pmap(
            self._device_validation,
            axis_name=_PMAP_AXIS_NAME,
            devices=self.devices,
        )

    @property
    def global_update_batch_size(self) -> int:
        """Examples contributing to one accumulated optimizer update."""
        return (
            len(self.devices)
            * self.config.per_device_batch_size
            * self.config.gradient_accumulation_steps
        )

    def _forecast_one(
        self,
        parameters: Any,
        initial_state: Any,
        collect_tendency_statistics: bool | jax.Array,
    ) -> tuple[jax.Array, dict[str, jax.Array]]:
        if self.config.decoder_only:
            initial_forecast = self.model.observe(parameters, initial_state)
            zero = jnp.asarray(0.0, dtype=jnp.float32)
            return initial_forecast.values[jnp.newaxis], {
                "correction/rms": zero,
                "correction/max_abs": zero,
            }
        rollout_parameters = parameters
        if self.config.freeze_corrector:
            rollout_parameters = {
                "corrector": jax.tree_util.tree_map(
                    jax.lax.stop_gradient,
                    parameters["corrector"],
                ),
                "decoder": parameters["decoder"],
            }
        _, positive_forecasts, tendency_statistics = (
            rollout_at_durations_with_tendency_statistics(
                self.model,
                rollout_parameters,
                initial_state,
                durations_seconds=tuple(
                    float(lead_hours * 3600) for lead_hours in self.config.lead_hours
                ),
                rematerialize=self.rematerialize_rollout,
                rematerialization_policy=self.rematerialization_policy,
                collect_tendency_statistics=collect_tendency_statistics,
                maximum_gradient_duration_seconds=(
                    float(self.config.effective_bptt_window_hours) * 3600.0
                ),
            )
        )
        if self.config.uses_interface_decoder:
            initial_forecast = self.model.observe(parameters, initial_state)
            forecast_values = jnp.concatenate(
                (
                    initial_forecast.values[jnp.newaxis],
                    positive_forecasts.values,
                ),
                axis=0,
            )
        else:
            forecast_values = positive_forecasts.values
        return forecast_values, tendency_statistics

    def _microbatch_loss(
        self,
        parameters: Any,
        initial_states: Any,
        targets: jax.Array,
        targets_are_modal: bool,
        collect_tendency_statistics: bool | jax.Array,
        include_weatherbench_metrics: bool = False,
    ) -> tuple[jax.Array, dict[str, jax.Array]]:
        forecasts, tendency_statistics = jax.vmap(
            self._forecast_one,
            in_axes=(None, 0, None),
        )(
            parameters,
            initial_states,
            collect_tendency_statistics,
        )
        losses, metrics = jax.vmap(
            lambda forecast, target: self.loss(
                forecast,
                target,
                self.config.loss_lead_hours,
                targets_are_modal=targets_are_modal,
                lead_weights=self.config.lead_loss_weights,
            )
        )(forecasts, targets)
        mean_metrics = jax.tree_util.tree_map(jnp.mean, metrics)
        mean_metrics.update(jax.tree_util.tree_map(jnp.mean, tendency_statistics))
        mean_metrics["forecast/nonfinite_fraction"] = jax.lax.cond(
            jnp.asarray(collect_tendency_statistics),
            lambda _: 1.0 - jnp.mean(jnp.isfinite(forecasts)),
            lambda _: jnp.asarray(0.0, dtype=jnp.float32),
            operand=None,
        )
        if include_weatherbench_metrics and self.weatherbench_metrics is not None:
            mean_metrics.update(
                self.weatherbench_metrics.score(
                    forecasts,
                    targets,
                    targets_are_modal=targets_are_modal,
                    lead_hours=self.config.loss_lead_hours,
                )
            )
        return jnp.mean(losses), mean_metrics

    def _device_update(
        self,
        training_state: TrainingState,
        batch: PreparedTrainingBatch,
    ) -> tuple[TrainingState, dict[str, jax.Array]]:
        next_step = training_state.step + 1
        collect_tendency_statistics = (next_step == 1) | (
            next_step % self.config.log_every_steps == 0
        )
        accumulated_gradients = jax.tree_util.tree_map(
            jnp.zeros_like,
            training_state.parameters,
        )
        accumulated_metrics: dict[str, jax.Array] | None = None
        for accumulation_index in range(self.execution_accumulation_steps):
            initial_states = jax.tree_util.tree_map(
                lambda value: value[accumulation_index],
                batch.initial_states,
            )
            targets = batch.targets[accumulation_index]
            (_, microbatch_metrics), gradients = jax.value_and_grad(
                self._microbatch_loss,
                has_aux=True,
            )(
                training_state.parameters,
                initial_states,
                targets,
                batch.targets_are_modal,
                collect_tendency_statistics,
            )
            gradients = jax.lax.pmean(gradients, axis_name=_PMAP_AXIS_NAME)
            microbatch_metrics = jax.lax.pmean(
                microbatch_metrics,
                axis_name=_PMAP_AXIS_NAME,
            )
            accumulated_gradients = jax.tree_util.tree_map(
                jnp.add,
                accumulated_gradients,
                gradients,
            )
            if accumulated_metrics is None:
                accumulated_metrics = microbatch_metrics
            else:
                accumulated_metrics = jax.tree_util.tree_map(
                    jnp.add,
                    accumulated_metrics,
                    microbatch_metrics,
                )
        divisor = float(self.execution_accumulation_steps)
        accumulated_gradients = jax.tree_util.tree_map(
            lambda value: value / divisor,
            accumulated_gradients,
        )
        assert accumulated_metrics is not None
        accumulated_metrics = jax.tree_util.tree_map(
            lambda value: value / divisor,
            accumulated_metrics,
        )
        updates, candidate_optimizer_state = self.optimizer.update(
            accumulated_gradients,
            training_state.optimizer_state,
            training_state.parameters,
        )
        candidate_parameters = optax.apply_updates(
            training_state.parameters,
            updates,
        )
        finite_update = (
            _tree_all_finite(accumulated_gradients)
            & _tree_all_finite(candidate_parameters)
            & _tree_all_finite(accumulated_metrics)
        )
        finite_update = jax.lax.pmin(
            finite_update.astype(jnp.int32),
            axis_name=_PMAP_AXIS_NAME,
        ).astype(jnp.bool_)
        candidate_ema = update_ema(
            training_state.ema_parameters,
            candidate_parameters,
            self.config.ema_decay,
        )
        next_parameters = jax.tree_util.tree_map(
            lambda candidate, previous: jnp.where(
                finite_update,
                candidate,
                previous,
            ),
            candidate_parameters,
            training_state.parameters,
        )
        next_ema = jax.tree_util.tree_map(
            lambda candidate, previous: jnp.where(
                finite_update,
                candidate,
                previous,
            ),
            candidate_ema,
            training_state.ema_parameters,
        )
        next_optimizer_state = jax.tree_util.tree_map(
            lambda candidate, previous: jnp.where(
                finite_update,
                candidate,
                previous,
            ),
            candidate_optimizer_state,
            training_state.optimizer_state,
        )
        next_random_key, _ = jax.random.split(training_state.random_key)
        next_state = TrainingState(
            step=training_state.step + 1,
            parameters=next_parameters,
            ema_parameters=next_ema,
            optimizer_state=next_optimizer_state,
            random_key=next_random_key,
        )
        accumulated_metrics.update(
            {
                "gradient/global_norm": optax.tree.norm(accumulated_gradients),
                "parameter/global_norm": optax.tree.norm(next_parameters),
                "update/global_norm": optax.tree.norm(updates),
                "update/applied": finite_update.astype(jnp.float32),
                "learning_rate": self.learning_rate(training_state.step),
            }
        )
        return next_state, accumulated_metrics

    def _device_validation(
        self,
        training_state: TrainingState,
        batch: PreparedTrainingBatch,
    ) -> dict[str, jax.Array]:
        accumulated_metrics: dict[str, jax.Array] | None = None
        for accumulation_index in range(self.execution_accumulation_steps):
            initial_states = jax.tree_util.tree_map(
                lambda value: value[accumulation_index],
                batch.initial_states,
            )
            targets = batch.targets[accumulation_index]
            _, metrics = self._microbatch_loss(
                training_state.ema_parameters,
                initial_states,
                targets,
                batch.targets_are_modal,
                True,
                include_weatherbench_metrics=True,
            )
            metrics = jax.lax.pmean(metrics, axis_name=_PMAP_AXIS_NAME)
            accumulated_metrics = (
                metrics
                if accumulated_metrics is None
                else jax.tree_util.tree_map(
                    jnp.add,
                    accumulated_metrics,
                    metrics,
                )
            )
        assert accumulated_metrics is not None
        divisor = float(self.execution_accumulation_steps)
        return {
            f"validation/{name}": value / divisor
            for name, value in accumulated_metrics.items()
        }

    def prepare(self, sampled: SampledTrajectory) -> PreparedTrainingBatch:
        """Encode and shard one host-side sample for this trainer."""
        return prepare_training_batch(
            self.model,
            sampled,
            devices=self.devices,
            accumulation_steps=self.config.gradient_accumulation_steps,
            per_device_batch_size=self.config.per_device_batch_size,
            pack_accumulation=self.pack_accumulation,
        )

    def _validation_metrics(
        self,
        replicated_state: TrainingState,
        sampler: TrajectorySampler,
    ) -> dict[str, float]:
        totals: dict[str, float] = {}
        for _ in range(self.config.validation_batches):
            sampled = sampler.sample(self.global_update_batch_size)
            metrics = _first_replica(
                self._validate(replicated_state, self.prepare(sampled))
            )
            for name, value in metrics.items():
                totals[name] = totals.get(name, 0.0) + float(value)
        averaged_metrics = {
            name: value / self.config.validation_batches
            for name, value in totals.items()
        }
        mse_prefix = "validation/weatherbench2/mse/"
        for name in tuple(averaged_metrics):
            if not name.startswith(mse_prefix):
                continue
            suffix = name[len(mse_prefix) :]
            mse = averaged_metrics.pop(name)
            averaged_metrics[f"validation/weatherbench2/rmse/{suffix}"] = float(
                np.sqrt(max(mse, 0.0))
            )
        return averaged_metrics

    def run(
        self,
        training_state: TrainingState,
        *,
        training_sampler: TrajectorySampler,
        validation_sampler: TrajectorySampler,
        metrics_logger: WandbMetricsLogger,
        checkpoint_metadata: dict[str, Any],
    ) -> TrainingState:
        """Run the configured stage, logging scalars and checkpointing locally."""
        replicated_state = _replicate(training_state, self.devices)
        start_step = int(training_state.step)
        trainable_parameter_count = sum(
            int(parameter.size)
            for parameter in jax.tree_util.tree_leaves(training_state.parameters)
        )
        metrics_logger.log(
            {"model/trainable_parameters": float(trainable_parameter_count)},
            step=start_step,
        )
        mutable_checkpoint_metadata = dict(checkpoint_metadata)
        best_validation_loss = float(
            mutable_checkpoint_metadata.get("best_validation_loss", np.inf)
        )
        last_log_step = start_step
        last_log_time = time.monotonic()
        accumulated_sample_wait_seconds = 0.0
        accumulated_prepare_seconds = 0.0
        accumulated_update_seconds = 0.0
        for _ in range(start_step, self.config.training_steps):
            sample_start = time.monotonic()
            sampled = training_sampler.sample(self.global_update_batch_size)
            prepare_start = time.monotonic()
            batch = self.prepare(sampled)
            update_start = time.monotonic()
            replicated_state, replicated_metrics = self._update(
                replicated_state,
                batch,
            )
            step = int(jax.device_get(replicated_state.step[0]))
            _raise_for_rejected_update(replicated_metrics, step=step)
            update_end = time.monotonic()
            accumulated_sample_wait_seconds += prepare_start - sample_start
            accumulated_prepare_seconds += update_start - prepare_start
            accumulated_update_seconds += update_end - update_start
            should_log = step == 1 or step % self.config.log_every_steps == 0
            if should_log:
                metrics = {
                    name: float(value)
                    for name, value in _first_replica(replicated_metrics).items()
                }
                current_time = time.monotonic()
                elapsed = max(current_time - last_log_time, 1.0e-12)
                metrics["throughput/examples_per_second"] = (
                    self.global_update_batch_size * (step - last_log_step) / elapsed
                )
                metrics["curriculum/horizon_hours"] = float(self.config.horizon_hours)
                update_count = max(step - last_log_step, 1)
                metrics["throughput/sample_wait_seconds_per_update"] = (
                    accumulated_sample_wait_seconds / update_count
                )
                metrics["throughput/prepare_seconds_per_update"] = (
                    accumulated_prepare_seconds / update_count
                )
                metrics["throughput/update_seconds_per_update"] = (
                    accumulated_update_seconds / update_count
                )
                metrics_logger.log(metrics, step=step)
                logger.info(
                    "step=%d loss=%.6g grad_norm=%.6g examples/s=%.3f "
                    "sample_wait=%.3fs prepare=%.3fs update=%.3fs",
                    step,
                    metrics["loss"],
                    metrics["gradient/global_norm"],
                    metrics["throughput/examples_per_second"],
                    metrics["throughput/sample_wait_seconds_per_update"],
                    metrics["throughput/prepare_seconds_per_update"],
                    metrics["throughput/update_seconds_per_update"],
                )
                last_log_time = current_time
                last_log_step = step
                accumulated_sample_wait_seconds = 0.0
                accumulated_prepare_seconds = 0.0
                accumulated_update_seconds = 0.0
            needs_host_state = (
                step % self.config.validate_every_steps == 0
                or step % self.config.checkpoint_every_steps == 0
            )
            host_state = _first_replica(replicated_state) if needs_host_state else None
            if step % self.config.checkpoint_every_steps == 0:
                assert host_state is not None
                save_checkpoint(
                    self.config.checkpoint_directory,
                    host_state,
                    sampler_state=training_sampler.state_dict(),
                    validation_sampler_state=validation_sampler.state_dict(),
                    metadata=mutable_checkpoint_metadata,
                )
            if step % self.config.validate_every_steps == 0:
                validation_metrics = self._validation_metrics(
                    replicated_state,
                    validation_sampler,
                )
                metrics_logger.log(validation_metrics, step=step)
                logger.info(
                    "step=%d validation_loss=%.6g",
                    step,
                    validation_metrics["validation/loss"],
                )
                validation_loss = validation_metrics["validation/loss"]
                if np.isfinite(validation_loss) and (
                    validation_loss < best_validation_loss
                ):
                    best_validation_loss = validation_loss
                    mutable_checkpoint_metadata["best_validation_loss"] = (
                        best_validation_loss
                    )
                    assert host_state is not None
                    selected_path = save_checkpoint(
                        self.config.checkpoint_directory,
                        host_state,
                        sampler_state=training_sampler.state_dict(),
                        validation_sampler_state=(validation_sampler.state_dict()),
                        metadata=mutable_checkpoint_metadata,
                    )
                    mark_best_checkpoint(
                        selected_path,
                        validation_loss=best_validation_loss,
                    )
        final_state = _first_replica(replicated_state)
        save_checkpoint(
            self.config.checkpoint_directory,
            final_state,
            sampler_state=training_sampler.state_dict(),
            validation_sampler_state=validation_sampler.state_dict(),
            metadata=mutable_checkpoint_metadata,
        )
        return final_state
