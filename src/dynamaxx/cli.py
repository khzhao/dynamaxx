# Copyright 2026 dynamaxx

import argparse
import logging
from collections.abc import Sequence
from functools import partial
from pathlib import Path

from dynamaxx.utils.consts import WEATHERBENCH2_ERA5_1P5DEG_6H_PATH

logger = logging.getLogger("dynamaxx.cli")
OUTPUT_DIR = Path("outputs/eval")
PROTOCOL_NAMES = ("fast", "iteration", "validation", "golden", "weatherbench2")


def main(argv: Sequence[str] | None = None) -> int:
    """Run a fixed WeatherBench2 evaluation protocol."""
    args = _parser().parse_args(argv)
    _configure_logging()
    return run_protocol(
        args.protocol,
        model_name=args.model,
        hybrid_checkpoint=args.hybrid_checkpoint,
        use_hybrid_ema=not args.raw_hybrid_parameters,
        worker_count=args.workers,
        resume=not args.restart,
        output_directory=args.output_directory,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dynamaxx-eval",
        description="Run a fixed WeatherBench2 evaluation protocol.",
    )
    parser.add_argument(
        "protocol",
        choices=PROTOCOL_NAMES,
        help="fixed evaluation protocol",
    )
    model_group = parser.add_mutually_exclusive_group()
    model_group.add_argument("--model", default="persistence")
    model_group.add_argument(
        "--hybrid-checkpoint",
        type=Path,
        help="local hybrid checkpoint to evaluate with its EMA parameters",
    )
    parser.add_argument(
        "--raw-hybrid-parameters",
        action="store_true",
        help="evaluate raw rather than EMA parameters from a hybrid checkpoint",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="parallel chunk workers; use 1 for serial evaluation",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="discard existing parallel chunk results before running",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=OUTPUT_DIR,
        help="directory for metrics and resumable chunk results",
    )
    return parser


def _configure_logging() -> None:
    package_logger = logging.getLogger("dynamaxx")
    if not package_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        package_logger.addHandler(handler)
    package_logger.setLevel(logging.INFO)
    package_logger.propagate = False


def run_protocol(
    protocol: str,
    *,
    model_name: str,
    hybrid_checkpoint: Path | None = None,
    use_hybrid_ema: bool = True,
    worker_count: int = 1,
    resume: bool = True,
    output_directory: Path = OUTPUT_DIR,
) -> int:
    """Run one fixed WeatherBench2 protocol."""
    from dynamaxx.data.weatherbench2 import WeatherBench2Source
    from dynamaxx.dycore.registry import create_dycore_model
    from dynamaxx.eval.protocols import chunk_initial_count, create_case
    from dynamaxx.eval.runner import (
        evaluate_case,
        evaluate_case_parallel,
        write_metric_csv,
        write_metric_json,
    )
    from dynamaxx.hybrid.checkpoint import (
        hybrid_checkpoint_model_name,
        load_hybrid_checkpoint,
    )

    assert worker_count >= 1
    case = create_case(protocol)
    if hybrid_checkpoint is None:
        model_factory = partial(create_dycore_model, model_name)
    else:
        hybrid_checkpoint = hybrid_checkpoint.expanduser().resolve()
        if not hybrid_checkpoint.is_file():
            raise FileNotFoundError(hybrid_checkpoint)
        model_name = hybrid_checkpoint_model_name(
            hybrid_checkpoint,
            use_ema=use_hybrid_ema,
        )
        model_factory = partial(
            load_hybrid_checkpoint,
            hybrid_checkpoint,
            use_ema=use_hybrid_ema,
        )
    logger.info("Model: %s", model_name)

    logger.info("Data: WeatherBench2")

    logger.info(
        "Forecast: %s starts=%d lead_days=1..15 chunk=%d workers=%d",
        case.name,
        case.initial_times.size,
        chunk_initial_count(protocol),
        worker_count,
    )
    if worker_count == 1:
        model = model_factory()
        source = WeatherBench2Source(path=WEATHERBENCH2_ERA5_1P5DEG_6H_PATH)
        result = evaluate_case(
            model,
            source,
            case,
            chunk_initial_count=chunk_initial_count(protocol),
        )
    else:
        result = evaluate_case_parallel(
            model_factory,
            model_name,
            WEATHERBENCH2_ERA5_1P5DEG_6H_PATH,
            case,
            chunk_initial_count=chunk_initial_count(protocol),
            worker_count=worker_count,
            run_dir=output_directory / "runs" / f"{case.name}_{model_name}",
            resume=resume,
        )

    logger.info("Metrics: writing")
    output_path = output_directory
    stem = f"{result.case.name}_{result.model_name}"
    write_metric_json(result, output_path / f"{stem}.json")
    write_metric_csv(result, output_path / f"{stem}.csv")
    _log_summary(result, output_path)
    return 0


def _log_summary(result, output_dir: Path) -> None:
    output_stem = f"{result.case.name}_{result.model_name}"
    logger.info(
        "Result: case=%s model=%s failed=%s issues=%d records=%d primary_score=%.6g metrics=%s",
        result.case.name,
        result.model_name,
        result.diagnostics.failed,
        len(result.diagnostics.issues),
        len(result.records),
        result.primary_score,
        output_dir / f"{output_stem}.json",
    )


if __name__ == "__main__":
    raise SystemExit(main())
