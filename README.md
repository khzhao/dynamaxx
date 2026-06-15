# dynamaxx

Persistence dycore utilities and fixed WeatherBench2 evaluation tools.

## Quickstart

Install dependencies and run the local test suite:

```bash
uv sync
uv run pytest
```

Run the quick fixed WeatherBench2 protocol:

```bash
uv run dynamaxx-eval fast
```

The command writes metrics to `outputs/eval/` as JSON and CSV. It uses the
processed 1.5-degree, 6-hourly ERA5 collection:

```text
s3://weathermaxx-data/weatherbench2/datasets/v1/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative/
```

Run the fixed iteration, validation, or golden protocols:

```bash
uv run dynamaxx-eval iteration
uv run dynamaxx-eval validation
uv run dynamaxx-eval golden
```

Real S3 integration tests are opt-in:

```bash
DYNAMAXX_RUN_S3_TESTS=1 uv run pytest -m "integration and s3"
```
