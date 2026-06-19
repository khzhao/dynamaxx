# Copyright 2026 dynamaxx

"""Engine-enforced cache for deterministic evaluation metrics.

Evaluating a model on a fixed protocol is deterministic in four inputs: the
model (identified by its stable registry name), the evaluation case (target
variables, lead times, initialization times), the data path, and the evaluation
harness code that turns forecasts into metric values. When all four are
unchanged, re-running the evaluation reproduces the same metrics. The autonomous
optimization loop re-scores the unchanged incumbent on most cycles, so this
cache lets the engine serve the previously computed metrics instead of
recomputing them.

This is the code-level counterpart to the Scorer's documented reuse policy: it
holds regardless of how the Scorer is invoked, so caching no longer depends on
the agent's judgement. Pass ``--restart`` (``resume=False``) to bypass the cache
and force a fresh computation.

Identity assumptions:

- A registry model name is treated as a stable identity for forecast behavior.
  The protocol requires every candidate to be a side-by-side model with its own
  name, so a given name always maps to the same forecast code path. The cache
  key therefore does **not** include the dycore source tree -- doing so would
  invalidate every model's cache whenever any candidate additively registers
  itself, which is exactly the failure this layer exists to prevent. If a model
  is edited in place under an unchanged name, force a recompute with
  ``--restart``.
- The harness fingerprint covers the evaluation package source that determines
  metric values, so a change to metrics, scoring, runner, protocol, or
  diagnostics logic invalidates every cached result.
"""

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

_EVAL_PACKAGE_DIR = Path(__file__).resolve().parent
# This module only stores and serves results; it never changes metric values,
# so exclude it from the harness fingerprint to avoid self-referential churn.
_HARNESS_FINGERPRINT_EXCLUDE = frozenset({"metric_cache.py"})
_FIELD_SEPARATOR = "\x1f"


def eval_harness_fingerprint() -> str:
    """Return a content hash of the evaluation source that determines metrics."""
    digest = hashlib.sha256()
    for source_path in sorted(_EVAL_PACKAGE_DIR.glob("*.py")):
        if source_path.name in _HARNESS_FINGERPRINT_EXCLUDE:
            continue
        digest.update(source_path.name.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(source_path.read_bytes())
        digest.update(b"\x00")
    return digest.hexdigest()


def case_fingerprint(case: Any) -> str:
    """Return a stable hash of the evaluation case definition."""
    serialized = json.dumps(case.asdict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def result_cache_key(
    *,
    model_name: str,
    protocol: str,
    case_fingerprint: str,
    data_path: str,
    harness_fingerprint: str,
) -> str:
    """Return the cache key for one model, protocol, dataset, and harness."""
    payload = _FIELD_SEPARATOR.join(
        (model_name, protocol, case_fingerprint, data_path, harness_fingerprint)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def cache_dir(output_dir: str | Path) -> Path:
    """Return the directory holding cached metric artifacts."""
    return Path(output_dir) / "cache"


def _cache_paths(output_dir: str | Path, key: str) -> tuple[Path, Path]:
    base = cache_dir(output_dir)
    return base / f"{key}.json", base / f"{key}.csv"


def lookup(output_dir: str | Path, key: str) -> tuple[Path, Path] | None:
    """Return cached (json, csv) paths for a key, or None if absent."""
    json_path, csv_path = _cache_paths(output_dir, key)
    if json_path.exists() and csv_path.exists():
        return json_path, csv_path
    return None


def store(
    output_dir: str | Path,
    key: str,
    json_path: str | Path,
    csv_path: str | Path,
) -> None:
    """Copy freshly written metric artifacts into the cache under a key."""
    cached_json, cached_csv = _cache_paths(output_dir, key)
    cached_json.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(json_path, cached_json)
    shutil.copy2(csv_path, cached_csv)


def serve(
    cached: tuple[Path, Path],
    json_path: str | Path,
    csv_path: str | Path,
) -> float:
    """Copy cached artifacts to the output paths; return the primary score."""
    cached_json, cached_csv = cached
    output_json = Path(json_path)
    output_csv = Path(csv_path)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cached_json, output_json)
    shutil.copy2(cached_csv, output_csv)
    with output_json.open("r", encoding="utf-8") as cached_file:
        return float(json.load(cached_file)["primary_score"])
