# Scoring Notes

## Gate Status

- Fast gate: Passed by verified/reused post-repair artifacts at `outputs/eval/fast_dinosaur.json` and `outputs/eval/fast_dinosaur.csv`. Primary score was `-1.2882176100657747`, diagnostics failed was `false`, issue count was `0`, and record count was `120`.
- Iteration promotion gate: Passed for infrastructure repair. `uv run dynamaxx-eval iteration --model dinosaur --workers 4` exited `0`; diagnostics failed was `false`, issue count was `0`, record count was `120`, and primary score was `-1.3251884351511753`.
- Validation acceptance gate: Not applied as a model-selection threshold because candidate and incumbent are the same canonical repaired `dinosaur` model. Validation was run to establish the finite baseline; `uv run dynamaxx-eval validation --model dinosaur --workers 4` exited `0`, diagnostics failed was `false`, issue count was `0`, record count was `120`, and primary score was `-1.3128324262513928`.

## Commands Run

- `uv run python -c "from dynamaxx.dycore.registry import dycore_model_names, create_dycore_model; names=dycore_model_names(); print(names); model=create_dycore_model('dinosaur'); print(model.name)"` exited `0`; output confirmed `('persistence', 'dinosaur')` and model name `dinosaur`.
- `jq '{protocol, model_name, primary_score, diagnostics, records: (.records | length? // .record_count // null), started_at, finished_at, config, evaluation_fingerprint}' outputs/eval/fast_dinosaur.json` exited `0`; verified reusable fast JSON.
- `uv run dynamaxx-eval iteration --model dinosaur --workers 4` exited `0`; runner reported `chunks=229 cached=0 pending=229` at start and `failed=False issues=0 records=120 primary_score=-1.32519` at completion.
- `uv run dynamaxx-eval validation --model dinosaur --workers 4` exited `0`; runner reported `chunks=46 cached=0 pending=46` at start and `failed=False issues=0 records=120 primary_score=-1.31283` at completion.
- Artifact JSON/CSV consistency and finite-metric check exited `0`; confirmed fast, iteration, and validation JSON/CSV artifacts each had `120` records and zero nonfinite metric cells:

```bash
uv run python - <<'PY'
import csv
import json
import math
from pathlib import Path

for stem in ["fast_dinosaur", "iteration_dinosaur", "validation_dinosaur"]:
    json_path = Path("outputs/eval") / f"{stem}.json"
    csv_path = Path("outputs/eval") / f"{stem}.csv"
    data = json.loads(json_path.read_text())
    issue_count = len(data["diagnostics"]["issues"])
    nonfinite_cells = 0
    with csv_path.open(newline="") as file_handle:
        rows = list(csv.DictReader(file_handle))
    for row in rows:
        for column in ("rmse", "mae", "bias", "skill_vs_persistence"):
            value = float(row[column])
            if not math.isfinite(value):
                nonfinite_cells += 1
    print(f"{stem}: model={data['model_name']} primary_score={data['primary_score']} failed={data['diagnostics']['failed']} issues={issue_count} json_records={len(data['records'])} csv_records={len(rows)} nonfinite_metric_cells={nonfinite_cells}")
PY
```

## Raw Artifacts

- Fast JSON: `outputs/eval/fast_dinosaur.json`
- Fast CSV: `outputs/eval/fast_dinosaur.csv`
- Iteration JSON: `outputs/eval/iteration_dinosaur.json`
- Iteration CSV: `outputs/eval/iteration_dinosaur.csv`
- Validation JSON: `outputs/eval/validation_dinosaur.json`
- Validation CSV: `outputs/eval/validation_dinosaur.csv`
- Iteration run directory: `outputs/eval/runs/iteration_dinosaur`
- Validation run directory: `outputs/eval/runs/validation_dinosaur`

## Measurement Lessons

- The repaired canonical `dinosaur` model now produces finite scored metric artifacts under fast, iteration, and validation diagnostics without changing the fixed evaluation protocols.
- Because this is an infrastructure repair, candidate and incumbent fields in `scores.json` intentionally point to the same post-repair canonical artifacts; the recorded `0.0` deltas are bookkeeping only and should not be interpreted as model-selection evidence.
- The post-repair validation artifact is suitable as the finite baseline for future model-selection experiments, subject to Orchestrator acceptance of the infrastructure repair.

## Anomalies

- Cache reuse: Reused existing post-repair fast artifacts only. Iteration and validation had no stale run directories beforehand and both started with `cached=0`.
- Resource limits: No resource limits or worker failures were observed with `--workers 4`.
- Failed or restarted commands: None.
- Nonfinite or unstable outputs: None observed. The final artifact check found zero nonfinite `rmse`, `mae`, `bias`, or `skill_vs_persistence` cells in fast, iteration, and validation CSV outputs.

## Recommendation To Orchestrator

Treat this as a measured finite infrastructure baseline for canonical `dinosaur`, not a model-selection promotion. Recommended next action is for Orchestrator to decide whether to accept the infrastructure repair, then update the repair decision record and future comparable baseline pointers if accepted.
