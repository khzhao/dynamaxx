# Copyright 2026 dynamaxx

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from dynamaxx.utils.consts import WEATHERBENCH2_ERA5_1P5DEG_6H_PATH

logger = logging.getLogger("dynamaxx.eval.cli")


def main(argv: Sequence[str] | None = None) -> int:
    """Run a fixed WeatherBench2 evaluation protocol."""
    args = _parser().parse_args(argv)
    _configure_logging()
    match args.protocol:
        case "smoke":
            return run_smoke(
                dataset=args.dataset,
                output_dir=args.output_dir,
                model_name=args.model,
            )
        case "fast":
            return run_fast(
                dataset=args.dataset,
                output_dir=args.output_dir,
                model_name=args.model,
            )
        case "candidate-year":
            return run_candidate_year(
                year=args.year,
                dataset=args.dataset,
                output_dir=args.output_dir,
                model_name=args.model,
            )

    raise AssertionError(f"unknown protocol {args.protocol}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dynamaxx-eval",
        description="Run a fixed WeatherBench2 evaluation protocol.",
    )
    subparsers = parser.add_subparsers(
        dest="protocol",
        title="protocols",
        required=True,
    )

    smoke_parser = subparsers.add_parser("smoke", help="small fixed protocol")
    _add_io_arguments(smoke_parser)

    fast_parser = subparsers.add_parser("fast", help="seasonal fixed protocol")
    _add_io_arguments(fast_parser)

    candidate_parser = subparsers.add_parser(
        "candidate-year",
        help="daily starts for a year",
    )
    candidate_parser.add_argument("year", type=int)
    _add_io_arguments(candidate_parser)
    return parser


def _add_io_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dataset", default=WEATHERBENCH2_ERA5_1P5DEG_6H_PATH)
    parser.add_argument("--output-dir", default="outputs/eval")
    parser.add_argument("--model", default="spectral_dycore")


def _configure_logging() -> None:
    package_logger = logging.getLogger("dynamaxx")
    if not package_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        package_logger.addHandler(handler)
    package_logger.setLevel(logging.INFO)
    package_logger.propagate = False


def run_smoke(
    *,
    dataset: str = WEATHERBENCH2_ERA5_1P5DEG_6H_PATH,
    output_dir: str | Path = "outputs/eval",
    model_name: str = "spectral_dycore",
) -> int:
    """Run the fixed smoke protocol."""
    from dynamaxx.eval.core import smoke_case

    return _run_case(
        smoke_case(),
        dataset=dataset,
        output_dir=output_dir,
        model_name=model_name,
    )


def run_fast(
    *,
    dataset: str = WEATHERBENCH2_ERA5_1P5DEG_6H_PATH,
    output_dir: str | Path = "outputs/eval",
    model_name: str = "spectral_dycore",
) -> int:
    """Run the fixed fast protocol."""
    from dynamaxx.eval.core import fast_case

    return _run_case(
        fast_case(),
        dataset=dataset,
        output_dir=output_dir,
        model_name=model_name,
    )


def run_candidate_year(
    year: int,
    *,
    dataset: str = WEATHERBENCH2_ERA5_1P5DEG_6H_PATH,
    output_dir: str | Path = "outputs/eval",
    model_name: str = "spectral_dycore",
) -> int:
    """Run the fixed candidate-year protocol."""
    from dynamaxx.eval.core import candidate_year_case

    return _run_case(
        candidate_year_case(year),
        dataset=dataset,
        output_dir=output_dir,
        model_name=model_name,
    )


def _run_case(
    case,
    *,
    dataset: str,
    output_dir: str | Path,
    model_name: str,
) -> int:
    from dynamaxx.data.weatherbench2 import WeatherBench2Source
    from dynamaxx.eval.batch import build_weatherbench2_batch
    from dynamaxx.eval.runner import evaluate_batch, write_metric_csv, write_metric_json
    from dynamaxx.registry import create_forecast_model

    logger.info("Model: %s", model_name)
    model = create_forecast_model(model_name)

    logger.info("Data: WeatherBench2")
    batch = build_weatherbench2_batch(
        WeatherBench2Source(path=dataset),
        case,
    )

    logger.info("Forecast: running")
    result = evaluate_batch(model, batch)

    logger.info("Metrics: writing")
    output_path = Path(output_dir)
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
