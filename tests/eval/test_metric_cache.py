import json
import sys
import types

import numpy as np

from dynamaxx import cli
from dynamaxx.eval import metric_cache


class _FakeCase:
    """Minimal stand-in for EvalCase with the attributes run_protocol reads."""

    def __init__(self, name="fast", payload=None):
        self.name = name
        self.initial_times = np.array(["2019-01-01T00:00:00"], dtype="datetime64[ns]")
        self._payload = payload or {"name": name, "lead_days": [1, 2, 3]}

    def asdict(self):
        return dict(self._payload)


def _write_metrics(json_path, csv_path, *, primary_score, marker):
    json_path.write_text(
        json.dumps({"primary_score": primary_score, "marker": marker}),
        encoding="utf-8",
    )
    csv_path.write_text(f"marker\n{marker}\n", encoding="utf-8")


# --- pure cache-key / fingerprint behavior -------------------------------


def test_eval_harness_fingerprint_is_stable_hex():
    first = metric_cache.eval_harness_fingerprint()
    second = metric_cache.eval_harness_fingerprint()
    assert first == second
    assert len(first) == 64
    int(first, 16)  # valid hex


def test_case_fingerprint_changes_with_case_definition():
    a = metric_cache.case_fingerprint(_FakeCase(payload={"lead_days": [1, 2]}))
    b = metric_cache.case_fingerprint(_FakeCase(payload={"lead_days": [1, 2, 3]}))
    same = metric_cache.case_fingerprint(_FakeCase(payload={"lead_days": [1, 2]}))
    assert a != b
    assert a == same


def test_result_cache_key_is_sensitive_to_every_field():
    base = dict(
        model_name="m",
        protocol="iteration",
        case_fingerprint="c",
        data_path="/data",
        harness_fingerprint="h",
    )
    key = metric_cache.result_cache_key(**base)
    assert metric_cache.result_cache_key(**base) == key  # deterministic
    for field in base:
        changed = dict(base)
        changed[field] = base[field] + "x"
        assert metric_cache.result_cache_key(**changed) != key


# --- store / lookup / serve round trip -----------------------------------


def test_lookup_returns_none_when_absent(tmp_path):
    assert metric_cache.lookup(tmp_path, "deadbeef") is None


def test_store_then_lookup_and_serve_roundtrip(tmp_path):
    src_json = tmp_path / "src.json"
    src_csv = tmp_path / "src.csv"
    _write_metrics(src_json, src_csv, primary_score=-0.5, marker="cached")

    metric_cache.store(tmp_path, "key1", src_json, src_csv)
    found = metric_cache.lookup(tmp_path, "key1")
    assert found is not None

    out_json = tmp_path / "out" / "result.json"
    out_csv = tmp_path / "out" / "result.csv"
    primary = metric_cache.serve(found, out_json, out_csv)

    assert primary == -0.5
    assert json.loads(out_json.read_text())["marker"] == "cached"
    assert "cached" in out_csv.read_text()


# --- run_protocol engine enforcement -------------------------------------


def _key_for(case, protocol):
    return metric_cache.result_cache_key(
        model_name="incumbent_model",
        protocol=protocol,
        case_fingerprint=metric_cache.case_fingerprint(case),
        data_path=str(cli.WEATHERBENCH2_ERA5_1P5DEG_6H_PATH),
        harness_fingerprint=metric_cache.eval_harness_fingerprint(),
    )


def test_run_protocol_serves_from_cache_without_recompute(tmp_path, monkeypatch):
    case = _FakeCase(name="iteration")
    monkeypatch.setattr(cli, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr("dynamaxx.eval.protocols.create_case", lambda protocol: case)

    # Pre-populate the cache with a sentinel a real computation could never emit.
    cache_json = (
        metric_cache.cache_dir(tmp_path) / f"{_key_for(case, 'iteration')}.json"
    )
    cache_csv = cache_json.with_suffix(".csv")
    cache_json.parent.mkdir(parents=True, exist_ok=True)
    _write_metrics(cache_json, cache_csv, primary_score=-0.111, marker="from-cache")

    # Booby-trap the compute path: if reached, importing runner returns a module
    # whose evaluate functions raise.
    boom = types.ModuleType("dynamaxx.eval.runner")

    def _raise(*args, **kwargs):
        raise AssertionError("recomputed despite a cache hit")

    boom.evaluate_case = _raise
    boom.evaluate_case_parallel = _raise
    boom.write_metric_json = _raise
    boom.write_metric_csv = _raise
    monkeypatch.setitem(sys.modules, "dynamaxx.eval.runner", boom)

    exit_code = cli.run_protocol(
        "iteration", model_name="incumbent_model", worker_count=4, resume=True
    )

    assert exit_code == 0
    served = json.loads((tmp_path / "iteration_incumbent_model.json").read_text())
    assert served["marker"] == "from-cache"


def test_run_protocol_restart_bypasses_cache_and_restores_it(tmp_path, monkeypatch):
    case = _FakeCase(name="iteration")
    monkeypatch.setattr(cli, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr("dynamaxx.eval.protocols.create_case", lambda protocol: case)
    monkeypatch.setattr(
        "dynamaxx.eval.protocols.chunk_initial_count", lambda protocol: 1
    )
    monkeypatch.setattr(cli, "_log_summary", lambda result, output_dir: None)

    key = _key_for(case, "iteration")
    cache_json = metric_cache.cache_dir(tmp_path) / f"{key}.json"
    cache_csv = cache_json.with_suffix(".csv")
    cache_json.parent.mkdir(parents=True, exist_ok=True)
    _write_metrics(cache_json, cache_csv, primary_score=-0.999, marker="stale")

    # Fake the deferred compute dependencies so no JAX/data is needed.
    registry = types.ModuleType("dynamaxx.dycore.registry")
    registry.create_dycore_model = lambda name: object()
    data = types.ModuleType("dynamaxx.data.weatherbench2")
    data.WeatherBench2Source = lambda path: object()
    runner = types.ModuleType("dynamaxx.eval.runner")
    runner.evaluate_case = lambda *a, **k: types.SimpleNamespace()
    runner.evaluate_case_parallel = lambda *a, **k: types.SimpleNamespace()

    def _fresh_json(result, path):
        _write_metrics(
            path, path.with_suffix(".csv"), primary_score=-0.222, marker="fresh"
        )

    runner.write_metric_json = _fresh_json
    runner.write_metric_csv = lambda result, path: None
    monkeypatch.setitem(sys.modules, "dynamaxx.dycore.registry", registry)
    monkeypatch.setitem(sys.modules, "dynamaxx.data.weatherbench2", data)
    monkeypatch.setitem(sys.modules, "dynamaxx.eval.runner", runner)

    exit_code = cli.run_protocol(
        "iteration", model_name="incumbent_model", worker_count=1, resume=False
    )

    assert exit_code == 0
    # --restart ignored the stale cache and used the freshly computed result.
    out = json.loads((tmp_path / "iteration_incumbent_model.json").read_text())
    assert out["marker"] == "fresh"
    # And the fresh result replaced the stale cache entry for next time.
    assert json.loads(cache_json.read_text())["marker"] == "fresh"
