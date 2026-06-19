# Copyright 2026 dynamaxx

import argparse
import logging
from collections.abc import Sequence
from functools import partial
from pathlib import Path

from dynamaxx.utils.consts import WEATHERBENCH2_ERA5_1P5DEG_6H_PATH

logger = logging.getLogger("dynamaxx.cli")
OUTPUT_DIR = Path("outputs/eval")
PROTOCOL_NAMES = ("fast", "iteration", "validation", "golden")


def main(argv: Sequence[str] | None = None) -> int:
    """Run a fixed WeatherBench2 evaluation protocol."""
    args = _parser().parse_args(argv)
    _configure_logging()
    return run_protocol(
        args.protocol,
        model_name=args.model,
        worker_count=args.workers,
        resume=not args.restart,
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
    parser.add_argument("--model", default="persistence")
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
    worker_count: int = 1,
    resume: bool = True,
) -> int:
    """Run one fixed WeatherBench2 protocol."""
    # Lightweight imports needed to compute the cache key; the heavy forecast
    # and data dependencies are deferred until a cache miss so served results
    # avoid importing the model registry and JAX entirely.
    from dynamaxx.eval import metric_cache
    from dynamaxx.eval.protocols import chunk_initial_count, create_case

    assert worker_count >= 1
    case = create_case(protocol)
    logger.info("Model: %s", model_name)

    logger.info("Data: WeatherBench2")

    output_path = OUTPUT_DIR
    stem = f"{case.name}_{model_name}"
    output_json = output_path / f"{stem}.json"
    output_csv = output_path / f"{stem}.csv"
    cache_key = metric_cache.result_cache_key(
        model_name=model_name,
        protocol=protocol,
        case_fingerprint=metric_cache.case_fingerprint(case),
        data_path=str(WEATHERBENCH2_ERA5_1P5DEG_6H_PATH),
        harness_fingerprint=metric_cache.eval_harness_fingerprint(),
    )
    if resume:
        cached = metric_cache.lookup(output_path, cache_key)
        if cached is not None:
            primary_score = metric_cache.serve(cached, output_json, output_csv)
            logger.info(
                "Result: case=%s model=%s served from engine cache key=%s "
                "primary_score=%.6g metrics=%s",
                case.name,
                model_name,
                cache_key[:12],
                primary_score,
                output_json,
            )
            return 0

    from dynamaxx.data.weatherbench2 import WeatherBench2Source
    from dynamaxx.dycore.registry import create_dycore_model
    from dynamaxx.eval.runner import (
        evaluate_case,
        evaluate_case_parallel,
        write_metric_csv,
        write_metric_json,
    )

    logger.info(
        "Forecast: %s starts=%d lead_days=1..15 chunk=%d workers=%d",
        case.name,
        case.initial_times.size,
        chunk_initial_count(protocol),
        worker_count,
    )
    if worker_count == 1:
        model = create_dycore_model(model_name)
        source = WeatherBench2Source(path=WEATHERBENCH2_ERA5_1P5DEG_6H_PATH)
        result = evaluate_case(
            model,
            source,
            case,
            chunk_initial_count=chunk_initial_count(protocol),
        )
    else:
        result = evaluate_case_parallel(
            partial(create_dycore_model, model_name),
            model_name,
            WEATHERBENCH2_ERA5_1P5DEG_6H_PATH,
            case,
            chunk_initial_count=chunk_initial_count(protocol),
            worker_count=worker_count,
            run_dir=OUTPUT_DIR / "runs" / f"{case.name}_{model_name}",
            resume=resume,
        )

    logger.info("Metrics: writing")
    write_metric_json(result, output_json)
    write_metric_csv(result, output_csv)
    metric_cache.store(output_path, cache_key, output_json, output_csv)
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
