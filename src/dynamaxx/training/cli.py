# Copyright 2026 dynamaxx

"""Command-line entry point for the first Dinosaur hybrid training stage."""

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import jax
import numpy as np

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.hybrid.dinosaur import (
    DinosaurNeuralCorrector,
    make_dinosaur_hybrid_core,
)
from dynamaxx.hybrid.model import PreparedHybridModel
from dynamaxx.training.checkpoints import latest_checkpoint, restore_checkpoint
from dynamaxx.training.config import (
    CURRICULUM_HORIZONS_HOURS,
    DEFAULT_TRAINING_OUTPUT_DIRECTORY,
    PRODUCTION_HIDDEN_SIZE,
    PRODUCTION_RESIDUAL_BLOCKS,
    TrainingConfig,
)
from dynamaxx.training.corrector import ColumnResidualMLP
from dynamaxx.training.data import (
    PrefetchingTrajectorySampler,
    WeatherBench2TrajectorySampler,
)
from dynamaxx.training.initialization_cache import (
    build_initialized_state_cache,
    default_initialized_state_cache_directory,
    initialized_state_cache_fingerprint,
)
from dynamaxx.training.logging import WandbMetricsLogger
from dynamaxx.training.losses import HybridForecastLoss
from dynamaxx.training.state import build_optimizer, initialize_training_state
from dynamaxx.training.statistics import (
    TrainingStatistics,
    estimate_training_statistics,
    load_training_statistics,
    save_training_statistics,
)
from dynamaxx.training.target_cache import (
    build_modal_target_cache,
    default_modal_target_cache_directory,
    modal_target_cache_fingerprint,
)
from dynamaxx.training.trainer import HybridTrainer
from dynamaxx.training.weatherbench_metrics import WeatherBenchValidationMetrics
from dynamaxx.utils.consts import WEATHERBENCH2_ERA5_1P5DEG_6H_PATH

logger = logging.getLogger("dynamaxx.training.cli")

_CONTINUATION_CONFIG_CHANGES = frozenset(
    {
        "gradient_accumulation_steps",
        "output_directory",
        "per_device_batch_size",
        "wandb_run_name",
    }
)


def _normalized_config_for_comparison(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize effective BPTT semantics across pre-window checkpoints."""
    normalized = dict(config)
    horizon_hours = int(normalized["horizon_hours"])
    configured_window = int(normalized.get("bptt_window_hours", horizon_hours))
    normalized["bptt_window_hours"] = min(horizon_hours, configured_window)
    return normalized


def _validate_continuation_config(
    checkpoint_metadata: dict[str, Any],
    config: TrainingConfig,
) -> None:
    """Require model, objective, optimizer, data, and schedule compatibility."""
    source_config = checkpoint_metadata.get("config")
    if not isinstance(source_config, dict):
        raise ValueError("continued checkpoint is missing its training configuration")
    source_config = _normalized_config_for_comparison(source_config)
    destination_config = _normalized_config_for_comparison(config.asdict())
    incompatible_keys = sorted(
        key
        for key in source_config.keys() | destination_config.keys()
        if key not in _CONTINUATION_CONFIG_CHANGES
        and source_config.get(key) != destination_config.get(key)
    )
    if incompatible_keys:
        joined_keys = ", ".join(incompatible_keys)
        raise ValueError(
            "continued training can only change execution/batch settings; "
            f"incompatible fields: {joined_keys}"
        )


def _parser() -> argparse.ArgumentParser:
    """Build the hybrid-training argument parser."""
    parser = argparse.ArgumentParser(
        description="Train one logarithmic-curriculum Dinosaur hybrid stage.",
    )
    parser.add_argument(
        "--dataset",
        default=WEATHERBENCH2_ERA5_1P5DEG_6H_PATH,
        help="Processed WeatherBench2 collection path.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_TRAINING_OUTPUT_DIRECTORY,
        help="Local checkpoint and statistics directory.",
    )
    parser.add_argument(
        "--horizon-hours",
        type=int,
        choices=CURRICULUM_HORIZONS_HOURS,
        default=6,
    )
    parser.add_argument("--steps", type=int, default=100_000)
    parser.add_argument(
        "--stop-at-step",
        type=int,
        default=None,
        help=(
            "Stop cleanly at this absolute step without changing the stored "
            "training schedule; useful for bounded, resumable production runs."
        ),
    )
    parser.add_argument("--warmup-steps", type=int, default=2_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--hidden-size",
        type=int,
        default=PRODUCTION_HIDDEN_SIZE,
        help="Column-network width; the default is the production 800-wide model.",
    )
    parser.add_argument(
        "--residual-blocks",
        type=int,
        default=PRODUCTION_RESIDUAL_BLOCKS,
        help="Residual blocks; the default gives about 20.69M learned parameters.",
    )
    parser.add_argument(
        "--correction-interval-seconds",
        type=float,
        default=1800.0,
        help="Seconds between neural-corrector evaluations.",
    )
    parser.add_argument(
        "--bptt-window-hours",
        type=int,
        default=24,
        help=(
            "Maximum temporal gradient window. Forward states remain continuous "
            "across stopped-gradient boundaries."
        ),
    )
    parser.add_argument("--statistics-samples", type=int, default=32)
    parser.add_argument("--checkpoint-every", type=int, default=500)
    parser.add_argument("--validate-every", type=int, default=500)
    parser.add_argument("--log-every", type=int, default=10)
    parser.add_argument("--validation-batches", type=int, default=8)
    parser.add_argument("--per-device-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=2)
    parser.add_argument(
        "--pack-gradient-accumulation",
        action="store_true",
        help=(
            "Execute accumulated microbatches together when their combined "
            "device-local batch fits; preserves configured batch semantics."
        ),
    )
    parser.add_argument(
        "--data-loader-workers",
        type=int,
        default=8,
        help="Concurrent host workers used for yearly Zarr reads and decompression.",
    )
    parser.add_argument(
        "--state-cache-workers",
        type=int,
        default=8,
        help="Devices concurrently constructing deterministic initial states.",
    )
    parser.add_argument(
        "--state-cache-directory",
        type=Path,
        default=None,
        help="Local initialized-state cache; defaults beside a local dataset.",
    )
    parser.add_argument(
        "--no-state-cache",
        action="store_true",
        help="Initialize every sampled state online instead of using the local cache.",
    )
    parser.add_argument(
        "--state-cache-only",
        action="store_true",
        help="Build/load deterministic training caches and exit before training.",
    )
    parser.add_argument(
        "--target-cache-directory",
        type=Path,
        default=None,
        help="Local modal-target cache; defaults beside a local dataset.",
    )
    parser.add_argument(
        "--no-target-cache",
        action="store_true",
        help="Read nodal targets and transform them inside every loss evaluation.",
    )
    parser.add_argument(
        "--no-prefetch",
        action="store_true",
        help="Disable the one-batch deterministic background prefetch queue.",
    )
    parser.add_argument(
        "--mmap-caches",
        action="store_true",
        help="Memory-map deterministic caches instead of preloading them into RAM.",
    )
    parser.add_argument(
        "--no-rollout-rematerialization",
        action="store_true",
        help="Retain correction-step residuals instead of recomputing them backward.",
    )
    parser.add_argument(
        "--rematerialization-policy",
        choices=("nothing", "dots", "dots-no-batch"),
        default="nothing",
        help="Residual-saving policy used inside rematerialized correction scans.",
    )
    parser.add_argument("--wandb-project", default=None)
    parser.add_argument("--wandb-run-name", default=None)
    parser.add_argument(
        "--no-wandb",
        action="store_true",
        help="Disable W&B scalar logging.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume the exact latest checkpoint in --output.",
    )
    parser.add_argument(
        "--initialize-from",
        type=Path,
        default=None,
        help="Start a new curriculum stage from a prior local checkpoint EMA.",
    )
    parser.add_argument(
        "--continue-from",
        type=Path,
        default=None,
        help=(
            "Continue full optimizer, EMA, RNG, and sampler state in a new output "
            "directory while changing only approved execution/batch settings."
        ),
    )
    parser.add_argument(
        "--statistics-only",
        action="store_true",
        help="Estimate/cache statistics and exit before training.",
    )
    return parser


def _sampler(
    source: WeatherBench2Source,
    *,
    start: str,
    end: str,
    lead_hours: tuple[int, ...],
    input_variables: tuple[str, ...],
    target_variables: tuple[str, ...],
    seed: int,
    parallel_workers: int = 1,
    initialized_state_cache: Any | None = None,
    modal_target_cache: Any | None = None,
) -> WeatherBench2TrajectorySampler:
    """Construct one deterministic chronological trajectory sampler."""
    return WeatherBench2TrajectorySampler(
        source,
        start=start,
        end=end,
        lead_hours=lead_hours,
        input_channels=input_variables,
        target_channels=target_variables,
        seed=seed,
        parallel_workers=parallel_workers,
        initialized_state_cache=initialized_state_cache,
        modal_target_cache=modal_target_cache,
    )


def _statistics(
    config: TrainingConfig,
    *,
    core: Any,
    source: WeatherBench2Source,
    input_variables: tuple[str, ...],
    target_variables: tuple[str, ...],
    parallel_workers: int,
) -> tuple[TrainingStatistics, Path]:
    """Load frozen training statistics or estimate them once locally."""
    statistics_path = config.checkpoint_directory / "training_statistics.npz"
    if statistics_path.exists():
        statistics = load_training_statistics(statistics_path)
    else:
        logger.info(
            "estimating statistics from %d training-split samples",
            config.statistics_samples,
        )
        statistics_sampler = _sampler(
            source,
            start=config.statistics_start,
            end=config.statistics_end,
            lead_hours=(6,),
            input_variables=input_variables,
            target_variables=target_variables,
            seed=config.seed + 2,
            parallel_workers=parallel_workers,
        )
        try:
            statistics = estimate_training_statistics(
                core,
                statistics_sampler,
                sample_count=config.statistics_samples,
            )
        finally:
            statistics_sampler.close()
        save_training_statistics(statistics_path, statistics)
    if statistics.input_variables != input_variables:
        raise ValueError("cached input-variable statistics do not match the dataset")
    if statistics.target_variables != target_variables:
        raise ValueError("cached target-variable statistics do not match the dycore")
    if statistics.input_mean.shape != (core.input_feature_count,):
        raise ValueError("cached input statistics do not match the hybrid features")
    return statistics, statistics_path


def _write_local_run_config(config: TrainingConfig) -> None:
    """Write a readable local copy of the exact run configuration."""
    config.checkpoint_directory.mkdir(parents=True, exist_ok=True)
    path = config.checkpoint_directory / "run_config.json"
    path.write_text(
        json.dumps(config.asdict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _build_config(arguments: argparse.Namespace) -> TrainingConfig:
    """Translate parsed arguments into the validated immutable configuration."""
    return TrainingConfig(
        dataset_path=arguments.dataset,
        output_directory=arguments.output,
        horizon_hours=arguments.horizon_hours,
        bptt_window_hours=arguments.bptt_window_hours,
        training_steps=arguments.steps,
        warmup_steps=arguments.warmup_steps,
        seed=arguments.seed,
        hidden_size=arguments.hidden_size,
        residual_blocks=arguments.residual_blocks,
        correction_interval_seconds=arguments.correction_interval_seconds,
        statistics_samples=arguments.statistics_samples,
        per_device_batch_size=arguments.per_device_batch_size,
        gradient_accumulation_steps=arguments.gradient_accumulation_steps,
        checkpoint_every_steps=arguments.checkpoint_every,
        validate_every_steps=arguments.validate_every,
        log_every_steps=arguments.log_every,
        validation_batches=arguments.validation_batches,
        wandb_project=arguments.wandb_project,
        wandb_run_name=arguments.wandb_run_name,
    )


def main(argv: list[str] | None = None) -> int:
    """Run one fully specified hybrid training stage."""
    arguments = _parser().parse_args(argv)
    checkpoint_modes = sum(
        (
            bool(arguments.resume),
            arguments.initialize_from is not None,
            arguments.continue_from is not None,
        )
    )
    if checkpoint_modes > 1:
        raise ValueError(
            "--resume, --initialize-from, and --continue-from are mutually exclusive"
        )
    if (
        arguments.state_cache_only
        and arguments.no_state_cache
        and arguments.no_target_cache
    ):
        raise ValueError("--state-cache-only requires at least one enabled cache")
    if arguments.data_loader_workers < 1:
        raise ValueError("--data-loader-workers must be positive")
    if arguments.state_cache_workers < 1:
        raise ValueError("--state-cache-workers must be positive")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    jax.config.update("jax_default_matmul_precision", "high")
    config = _build_config(arguments)
    _write_local_run_config(config)
    source = WeatherBench2Source(path=config.dataset_path)
    input_variables = source.state_channel_names(year=2018)
    longitude, latitude = source.spatial_coordinates(year=2018)
    core = make_dinosaur_hybrid_core(
        dycore_name=config.dycore_name,
        longitude=longitude,
        latitude=latitude,
        input_variables=input_variables,
        data_path=config.dataset_path,
    )
    target_variables = core.output_variables
    statistics, statistics_path = _statistics(
        config,
        core=core,
        source=source,
        input_variables=input_variables,
        target_variables=target_variables,
        parallel_workers=arguments.data_loader_workers,
    )
    if arguments.statistics_only:
        logger.info("statistics saved locally at %s", statistics_path)
        return 0

    network = ColumnResidualMLP(
        input_mean=statistics.input_mean,
        input_standard_deviation=statistics.input_standard_deviation,
        output_scale=core.conservative_output_scale,
        hidden_size=config.hidden_size,
        residual_blocks=config.residual_blocks,
    )
    corrector = DinosaurNeuralCorrector(network, layer_count=core.layer_count)
    model = PreparedHybridModel(
        core=core,
        corrector=corrector,
        correction_interval_seconds=config.correction_interval_seconds,
    )
    cache_times = source.available_times(
        config.train_start,
        config.validation_end,
    )
    initialized_state_cache = None
    if not arguments.no_state_cache:
        cache_fingerprint = initialized_state_cache_fingerprint(
            dataset_path=config.dataset_path,
            dycore_name=config.dycore_name,
            input_variables=input_variables,
            core_configuration=core.model,
        )
        cache_directory = (
            arguments.state_cache_directory
            if arguments.state_cache_directory is not None
            else default_initialized_state_cache_directory(
                config.dataset_path,
                cache_fingerprint,
            )
        )
        initialized_state_cache = build_initialized_state_cache(
            cache_directory,
            fingerprint=cache_fingerprint,
            times=cache_times,
            source=source,
            model=model,
            input_variables=input_variables,
            devices=list(jax.local_devices()),
            parallel_workers=arguments.state_cache_workers,
            preload=not (arguments.state_cache_only or arguments.mmap_caches),
        )
        logger.info(
            "loaded %.2f GiB initialized-state cache from %s",
            initialized_state_cache.byte_count / 2**30,
            cache_directory,
        )
    modal_target_cache = None
    if not arguments.no_target_cache:
        target_cache_fingerprint = modal_target_cache_fingerprint(
            dataset_path=config.dataset_path,
            target_variables=target_variables,
            core_configuration=core.model,
        )
        target_cache_directory = (
            arguments.target_cache_directory
            if arguments.target_cache_directory is not None
            else default_modal_target_cache_directory(
                config.dataset_path,
                target_cache_fingerprint,
            )
        )
        modal_target_cache = build_modal_target_cache(
            target_cache_directory,
            fingerprint=target_cache_fingerprint,
            times=cache_times,
            source=source,
            to_modal=core.coords.horizontal.to_modal,
            target_variables=target_variables,
            devices=list(jax.local_devices()),
            parallel_workers=arguments.data_loader_workers,
            preload=not (arguments.state_cache_only or arguments.mmap_caches),
        )
        logger.info(
            "loaded %.2f GiB modal-target cache from %s",
            modal_target_cache.byte_count / 2**30,
            target_cache_directory,
        )
    if arguments.state_cache_only:
        return 0
    parameters = network.initialize(jax.random.key(config.seed))
    parameter_count = sum(
        int(parameter.size) for parameter in jax.tree_util.tree_leaves(parameters)
    )
    logger.info(
        "initialized production corrector with %d trainable parameters (%.3fM)",
        parameter_count,
        parameter_count / 1.0e6,
    )
    optimizer, learning_rate = build_optimizer(parameters, config)
    training_state = initialize_training_state(
        parameters,
        optimizer,
        random_key=jax.random.key(config.seed + 1),
    )
    training_sampler = _sampler(
        source,
        start=config.train_start,
        end=config.train_end,
        lead_hours=config.lead_hours,
        input_variables=input_variables,
        target_variables=target_variables,
        seed=config.seed,
        parallel_workers=arguments.data_loader_workers,
        initialized_state_cache=initialized_state_cache,
        modal_target_cache=modal_target_cache,
    )
    validation_sampler = _sampler(
        source,
        start=config.validation_start,
        end=config.validation_end,
        lead_hours=config.lead_hours,
        input_variables=input_variables,
        target_variables=target_variables,
        seed=config.seed + 1,
        parallel_workers=arguments.data_loader_workers,
        initialized_state_cache=initialized_state_cache,
        modal_target_cache=modal_target_cache,
    )
    restored = None
    if arguments.resume:
        checkpoint_path = latest_checkpoint(config.checkpoint_directory)
        if checkpoint_path is None:
            raise FileNotFoundError(
                f"no local checkpoint found in {config.checkpoint_directory}"
            )
        restored = restore_checkpoint(checkpoint_path)
        checkpoint_config = restored.metadata.get("config")
        if not isinstance(checkpoint_config, dict) or (
            _normalized_config_for_comparison(checkpoint_config)
            != _normalized_config_for_comparison(config.asdict())
        ):
            raise ValueError(
                "exact resume requires the same configuration as the checkpoint"
            )
        training_state = restored.training_state
        training_sampler.load_state_dict(restored.sampler_state)
        validation_sampler.load_state_dict(restored.validation_sampler_state)
        logger.info("resumed local checkpoint %s", checkpoint_path)
    elif arguments.initialize_from is not None:
        restored = restore_checkpoint(arguments.initialize_from)
        training_state = initialize_training_state(
            restored.training_state.ema_parameters,
            optimizer,
            random_key=jax.random.key(config.seed + 1),
        )
        logger.info(
            "initialized new curriculum stage from EMA in %s",
            arguments.initialize_from,
        )
    elif arguments.continue_from is not None:
        restored = restore_checkpoint(arguments.continue_from)
        _validate_continuation_config(restored.metadata, config)
        training_state = restored.training_state
        training_sampler.load_state_dict(restored.sampler_state)
        validation_sampler.load_state_dict(restored.validation_sampler_state)
        logger.info(
            "continued full training state from %s",
            arguments.continue_from,
        )

    if not arguments.no_prefetch:
        training_sampler = PrefetchingTrajectorySampler(
            training_sampler,
            batch_size=(
                len(jax.local_devices())
                * config.per_device_batch_size
                * config.gradient_accumulation_steps
            ),
        )
        validation_sampler = PrefetchingTrajectorySampler(
            validation_sampler,
            batch_size=(
                len(jax.local_devices())
                * config.per_device_batch_size
                * config.gradient_accumulation_steps
            ),
        )

    loss = HybridForecastLoss(
        to_modal=core.coords.horizontal.to_modal,
        total_wavenumber=core.coords.horizontal.modal_mesh[1],
        modal_mask=core.coords.horizontal.mask,
        statistics=statistics.spectral,
        spectral_weight=config.spectral_loss_weight,
        bias_weight=config.bias_loss_weight,
        bias_axis_name="devices",
        full_resolution_hours=config.full_resolution_loss_hours,
        final_retained_fraction=config.final_retained_wavenumber_fraction,
        taper_width_fraction=config.spectral_taper_width_fraction,
    )
    devices = list(jax.local_devices())
    logger.info(
        "training horizon=%dh leads=%s bptt_window=%dh devices=%d "
        "global_update_batch=%d",
        config.horizon_hours,
        config.lead_hours,
        config.effective_bptt_window_hours,
        len(devices),
        len(devices)
        * config.per_device_batch_size
        * config.gradient_accumulation_steps,
    )
    trainer = HybridTrainer(
        model=model,
        loss=loss,
        optimizer=optimizer,
        learning_rate=learning_rate,
        config=config,
        devices=devices,
        rematerialize_rollout=not arguments.no_rollout_rematerialization,
        stop_at_step=arguments.stop_at_step,
        pack_accumulation=arguments.pack_gradient_accumulation,
        rematerialization_policy=arguments.rematerialization_policy,
        weatherbench_metrics=WeatherBenchValidationMetrics(
            to_nodal=core.coords.horizontal.to_nodal,
            area_weights=source.area_weights(year=2018),
            channel_names=target_variables,
        ),
    )
    try:
        with WandbMetricsLogger(
            project=config.wandb_project,
            run_name=config.wandb_run_name,
            local_directory=config.checkpoint_directory,
            run_id=(
                None
                if restored is None or not arguments.resume
                else restored.metadata.get("wandb_run_id")
            ),
            resume=arguments.resume,
            enabled=not arguments.no_wandb,
        ) as metrics_logger:
            metadata = {
                "config": config.asdict(),
                "parameter_count": parameter_count,
                "statistics": statistics,
                "wandb_run_id": metrics_logger.run_id,
                "initialized_from": (
                    None
                    if arguments.initialize_from is None
                    else str(arguments.initialize_from.expanduser().resolve())
                ),
                "continued_from": (
                    None
                    if arguments.continue_from is None
                    else str(arguments.continue_from.expanduser().resolve())
                ),
            }
            if restored is not None and arguments.resume:
                previous_best_loss = restored.metadata.get("best_validation_loss")
                if previous_best_loss is not None:
                    metadata["best_validation_loss"] = previous_best_loss
            final_state = trainer.run(
                training_state,
                training_sampler=training_sampler,
                validation_sampler=validation_sampler,
                metrics_logger=metrics_logger,
                checkpoint_metadata=metadata,
            )
    finally:
        training_sampler.close()
        validation_sampler.close()
    logger.info(
        "completed step %d; checkpoints remain local in %s",
        int(np.asarray(final_state.step)),
        config.checkpoint_directory,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
