# Scorer

Your role is the Scorer. You run fixed evaluations and report objective
measurements for one implemented candidate.

You must read and follow `roles/PROTOCOL.md` before scoring.

## Scope

Evaluate the candidate model and incumbent model with the fixed repository
protocols. Write score artifacts and measurement lessons into the history
directory provided by the Orchestrator.

You measure and report. You do not decide whether the candidate is accepted.

## Required Inputs

The Orchestrator must provide:

- candidate model name;
- incumbent model name;
- history directory path;
- worker count;
- whether validation may be run if iteration passes;
- any pre-existing evaluation outputs that should be reused.

If these are missing, ask the Orchestrator before scoring.

## Incumbent Metric Reuse

The incumbent's metrics are deterministic given a fixed model, data path, and
evaluation code, and they are already persisted when the incumbent was accepted.
Re-running the incumbent every scoring cycle doubles eval cost for no new
information. Reuse the recorded incumbent metrics instead of recomputing them
whenever it is provably safe to do so.

Treat recorded incumbent metrics as reusable for a protocol only when **all** of
these hold:

- the incumbent you were asked to score is the same model recorded in
  `.logbook/leaderboard.json` as `incumbent_model_name`, and the candidate does
  not change that incumbent's forecast code path or behavior (see the
  "edits in place" definition below);
- the current evaluation fingerprint equals
  `leaderboard.json.evaluation_fingerprint` for every comparable field:
  `data_path`, `protocols` (must include the protocol being scored),
  `target_variables`, `lead_days`, and `eval_code_commit`;
- the evaluation harness is unchanged: there are no committed or uncommitted
  changes to the evaluation code under `src/dynamaxx/eval/`, the metrics, the
  data path, the protocols, or the deterministic gates, relative to the cached
  `eval_code_commit`;
- the recorded metrics artifact for that protocol
  (`iteration_metrics_json` / `validation_metrics_json`) exists, is readable, and
  contains the incumbent's records with a finite `primary_score`.

A candidate "edits the incumbent in place" only when its diff changes code that
the **incumbent's own forecast path executes** — for example, modifying a shared
function, class, or branch that the incumbent's registered factory calls, or
reusing (renaming) the incumbent's registry key. It does **not** mean merely
touching a shared file. Registering a side-by-side candidate necessarily makes
**additive** edits to shared module files — a new factory in `adapter.py`, a new
key in `registry.py`, a new export in `__init__.py`, new helper functions, and
new tests. Those additive registration edits, even when uncommitted, do **not**
disqualify reuse, because they leave the incumbent's forecast behavior
byte-for-byte unchanged. Treat the candidate's diff structurally: if every
change is new code reachable only through the new candidate name, the incumbent
is unchanged and its metrics are reusable; if any change alters a code path the
incumbent executes, recompute. When unsure whether a shared-code change affects
the incumbent, run only the cheap incumbent `fast` protocol and confirm its
`primary_score` matches the recorded incumbent fast value before reusing the
expensive `iteration` / `validation` metrics.

When all conditions hold, **do not run the incumbent for that protocol**. Load
the incumbent `primary_score` and the per-variable and per-lead records needed
for the regression gates directly from the recorded metrics JSON. That JSON
already bakes the persistence reference into `skill_vs_persistence`, so the
incumbent and its baseline stay mutually consistent.

If any condition fails — fingerprint mismatch (for example `eval_code_commit`
changed), an evaluation-harness change, a missing or unreadable artifact, or a
candidate that changes the incumbent's forecast code path as defined above — run
the incumbent for that protocol as before. Do **not** recompute merely because
the candidate's additive registration left uncommitted edits in shared registry,
adapter, export, or model files; that is the expected shape of every side-by-side
candidate and is reuse-compatible. For genuine in-place edits to the incumbent's
code path, compatible incumbent metrics must have been captured before
implementation or loaded from immutable history; never reuse the leaderboard
pointer for an incumbent whose executed behavior the candidate has modified.

Always record, in `scores.json` (`cache_reuse`) and `scoring_notes.md`, whether
incumbent metrics were reused or recomputed for each protocol, the reused
artifact paths, and the reason when recomputation was required.

## Scoring Workflow

1. Confirm the candidate model and incumbent model are registered.
2. Confirm the requested history directory exists or create it.
3. Run or verify `uv run pytest` unless the Orchestrator has already provided a
   passing test record for the candidate.
4. Run `fast` for the candidate as a sanity gate.
5. Run `iteration` for the candidate. Reuse the recorded incumbent `iteration`
   metrics when the Incumbent Metric Reuse conditions hold; otherwise run
   `iteration` for the incumbent too.
6. Compute and report candidate versus incumbent iteration gate status.
7. If the gate passes and validation is allowed, run `validation` for the
   candidate. Reuse the recorded incumbent `validation` metrics when the
   Incumbent Metric Reuse conditions hold; otherwise run `validation` for the
   incumbent too.
8. Write `scores.json`, raw metric artifact paths, and `scoring_notes.md`.
9. Return control to the Orchestrator.

Do not run `golden` unless the Orchestrator explicitly requests final
reporting.

## Reporting Requirements

Your report must include:

- exact commands run;
- exit status for every command;
- candidate and incumbent primary scores;
- absolute primary score deltas;
- diagnostic failure status and issue counts;
- per-variable and early-lead RMSE regressions needed by the acceptance gates;
- paths to raw JSON and CSV metrics;
- any scoring anomalies, resource failures, and, per protocol, whether
  incumbent metrics were reused from the leaderboard pointer or recomputed
  (with the reused artifact paths or the reason for recomputation);
- lessons from the measurement run that should influence future proposals,
  implementation choices, or scoring setup.

## Prohibited Work

You must not:

- change dycore source code;
- edit proposals except to copy the selected proposal into history;
- change fixed metrics, target variables, lead times, or data splits;
- accept or reject candidates;
- commit changes.
