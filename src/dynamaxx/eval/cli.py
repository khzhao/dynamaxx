# Copyright 2026 dynamaxx

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from dynamaxx.utils.consts import WEATHERBENCH2_ERA5_1P5DEG_6H_PATH

logger = logging.getLogger("dynamaxx.eval.cli")
OUTPUT_DIR = Path("outputs/eval")
PROTOCOL_NAMES = ("fast", "train", "validation", "test")


def main(argv: Sequence[str] | None = None) -> int:
    """Run a fixed WeatherBench2 evaluation protocol."""
    args = _parser().parse_args(argv)
    _configure_logging()
    return run_protocol(args.protocol, model_name=args.model)


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
    parser.add_argument("--model", default="spectral_dycore")
    return parser


def _configure_logging() -> None:
    package_logger = logging.getLogger("dynamaxx")
    if not package_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        package_logger.addHandler(handler)
    package_logger.setLevel(logging.INFO)
    package_logger.propagate = False


def run_protocol(protocol: str, *, model_name: str) -> int:
    """Run one fixed WeatherBench2 protocol."""
    from dynamaxx.data.weatherbench2 import WeatherBench2Source
    from dynamaxx.dycore.registry import create_dycore_model
    from dynamaxx.eval.protocols import chunk_initial_count, create_case
    from dynamaxx.eval.runner import evaluate_case, write_metric_csv, write_metric_json

    case = create_case(protocol)
    logger.info("Model: %s", model_name)
    model = create_dycore_model(model_name)

    logger.info("Data: WeatherBench2")
    source = WeatherBench2Source(path=WEATHERBENCH2_ERA5_1P5DEG_6H_PATH)

    logger.info(
        "Forecast: %s starts=%d lead_days=1..15 chunk=%d",
        case.name,
        case.initial_times.size,
        chunk_initial_count(protocol),
    )
    result = evaluate_case(
        model,
        source,
        case,
        chunk_initial_count=chunk_initial_count(protocol),
    )

    logger.info("Metrics: writing")
    output_path = OUTPUT_DIR
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
