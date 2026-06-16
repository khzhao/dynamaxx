# Agentic Dycore Optimization Protocol

This file defines the shared operating contract for all roles in the dycore
optimization loop. Each role must follow this protocol in addition to its own
role-specific instructions.

## Repository Constants

- Dycore models live in `src/dynamaxx/dycore/models/`.
- Model registration lives in `src/dynamaxx/dycore/registry.py`.
- The forecast model API lives in `src/dynamaxx/dycore/api.py`.
- Fixed evaluation protocols are run with `uv run dynamaxx-eval`.
- Evaluation outputs are written under `outputs/eval/`.
- The default incumbent model is recorded in `.logbook/leaderboard.json`.
- If `.logbook/leaderboard.json` does not exist, the incumbent is `dinosaur`
  when registered, otherwise `persistence`.
- Logbook artifact templates live in `roles/templates/`.

`leaderboard.json` must be a JSON object with at least these fields after the
first accepted candidate:

```json
{
  "incumbent_model_name": "dinosaur",
  "incumbent_commit": "git-commit-hash",
  "updated_at": "2026-06-16T00:00:00Z",
  "iteration_primary_score": 0.0,
  "validation_primary_score": 0.0,
  "history_path": ".logbook/history/2026-06-16_00-00-00_slug",
  "iteration_metrics_json": "outputs/eval/iteration_dinosaur.json",
  "iteration_metrics_csv": "outputs/eval/iteration_dinosaur.csv",
  "validation_metrics_json": "outputs/eval/validation_dinosaur.json",
  "validation_metrics_csv": "outputs/eval/validation_dinosaur.csv",
  "evaluation_fingerprint": {
    "data_path": "/home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative",
    "protocols": ["iteration", "validation"],
    "target_variables": [
      "2m_temperature",
      "mean_sea_level_pressure",
      "geopotential_500",
      "10m_u_component_of_wind"
    ],
    "lead_days": "1..15",
    "eval_code_commit": "git-commit-hash"
  }
}
```

The leaderboard is a pointer to the incumbent and its comparable baseline
artifacts. It is not the full experiment record; full records live under
`.logbook/history/`.

## Fixed Evaluation Commands

Use these commands unless the Orchestrator explicitly changes worker count after
checking machine resources:

```bash
uv run pytest
uv run dynamaxx-eval fast --model <model_name>
uv run dynamaxx-eval iteration --model <model_name> --workers <worker_count>
uv run dynamaxx-eval validation --model <model_name> --workers <worker_count>
```

The `golden` protocol is locked final reporting. Do not run it for iterative
model selection unless the Orchestrator explicitly requests a final report.

## Continuous Operation

The optimization loop is open-ended when the user asks for continuous
improvement. One iteration means exactly one selected proposal is implemented,
scored, accepted/rejected/revised, logged, and cleaned up.

After an iteration reaches a terminal decision, the Orchestrator starts the next
iteration immediately unless one of these stop conditions is true:

- the user pauses or stops the loop;
- required data, credentials, dependencies, or compute are unavailable;
- the worktree cannot be made safe without risking unrelated user work;
- fixed evaluation repeatedly fails for infrastructure reasons;
- disk, memory, GPU memory, or wall-clock limits would be exceeded;
- no ready or researchable ideas remain after a documented search;
- the same blocking condition occurs for three consecutive loop attempts.

Do not mark the overall continuous goal complete because one candidate finished.
The correct terminal state for an endless loop is either user-paused or
genuinely blocked with the blocking condition written in `.logbook/history` or
`.logbook/research`.

## Resource And Worker Policy

Before each implementation or scoring phase, the Orchestrator records:

- CPU count;
- available RAM;
- GPU count and available GPU memory per GPU, if GPUs are visible;
- free disk space for the repository and output directories;
- selected `--workers` value and rationale.

Use conservative defaults:

- use `--workers 1` when RAM or GPU capacity is unknown;
- do not exceed `--workers 2` below 64 GiB available RAM;
- do not exceed `--workers 4` below 128 GiB available RAM;
- do not exceed half of available CPU cores unless the user explicitly allows it;
- keep at least 50 GiB free disk space before starting iteration or validation;
- stop instead of deleting artifacts when disk cleanup would remove history
  needed for reproducibility.

Long evaluations must be supervised. If a command appears hung, repeatedly
exhausts memory, or produces no useful progress for the timeout selected by the
Orchestrator, stop the run, write a scoring anomaly, and return control to the
Orchestrator. Prefer reducing worker count before changing any evaluation code.

## Logbook Layout

The Orchestrator creates this layout before the first run:

```text
.logbook/
├── leaderboard.json
├── research/
│   ├── proposals/
│   ├── scrap/
│   ├── staging/
│   └── ready/
└── history/
```

Research files move through exactly one of these states:

- `proposals`: newly written ideas that have not been evaluated by the
  Evaluator.
- `staging`: promising ideas that are not the next implementation target.
- `ready`: implementable ideas approved by the Evaluator for Orchestrator
  selection.
- `scrap`: rejected ideas, including duplicates and ideas with unfavorable
  cost-risk tradeoffs.
- `history/<timestamp>_<slug>`: immutable record of an idea that was actually
  implemented and scored.

Use UTC timestamps in `YYYY-MM-DD_HH-MM-SS` format. History directory names use
`<timestamp>_<proposal-slug>`.

## Proposal Schema

Every proposal is a Markdown file with YAML front matter and these required
fields:

```yaml
---
schema_version: 1
slug: short-kebab-case-name
title: Human-readable title
status: proposals
created_at: 2026-06-16T00:00:00Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---
```

The body must contain these sections:

- `Hypothesis`: the physical or numerical reason the change should help.
- `Mechanism`: what changes in the dycore behavior.
- `Implementation Scope`: files, interfaces, and registry changes expected.
- `Expected Metric Movement`: which variables, leads, or diagnostics should
  improve or may regress.
- `Risks`: numerical stability, compute cost, data leakage, and physical
  plausibility risks.
- `Evaluation Plan`: exact protocols to run and what outcome would support the
  hypothesis.
- `Citations`: papers, docs, or code references used to justify the idea.

## Evaluation History Schema

Each implemented idea gets one immutable history directory:

```text
.logbook/history/2026-06-16_03-45-10_short-kebab-case-name/
├── proposal.md
├── implementation.md
├── scores.json
├── scoring_notes.md
├── decision.md
└── artifacts.json
```

`implementation.md` records:

- baseline commit hash and candidate commit hash, if available;
- files changed;
- model name evaluated;
- tests run and their pass/fail status;
- known limitations of the implementation.

`scores.json` records:

- model name;
- incumbent model name;
- commands run;
- paths to raw evaluation JSON and CSV files;
- fast, iteration, and validation primary scores when available;
- diagnostic issue counts and failure status;
- per-variable and per-lead regressions against the incumbent.

`scoring_notes.md` records:

- gate-status calculations produced by the Scorer;
- measurement anomalies, cache reuse, resource limits, or failed commands;
- lessons learned from the evaluation run that should influence future
  proposals or scoring setup.

`decision.md` records:

- `accepted`, `rejected`, or `needs_revision`;
- the exact score deltas that drove the decision;
- lessons learned for future research;
- cleanup or follow-up actions that were completed.

## Decision Authority

- Researcher proposes ideas only.
- Evaluator triages and ranks ideas only.
- Implementer changes code only for the one idea selected by the Orchestrator.
- Scorer measures and reports results only.
- Orchestrator owns resource checks, idea selection, final accept/reject
  decisions, commits, rollback requests, and logbook state transitions.

No role may change the fixed evaluation protocol inside the same experiment
being scored. Any change to metrics or protocols must be proposed, reviewed,
and accepted as a separate infrastructure change before it can affect model
selection.

## Subagent Operating Mode

The Orchestrator should prefer role-specific subagents when the active Codex
surface supports them. Each subagent must receive:

- `roles/PROTOCOL.md`;
- its role-specific file from `roles/`;
- the exact task, input paths, expected output paths, and stop condition;
- any resource, git-state, or file-ownership constraints discovered by the
  Orchestrator.

Subagents are workers, not decision owners. A subagent may recommend an action,
but authority stays with the role boundaries above.

Use subagents sequentially whenever their outputs modify shared state. In
particular:

- Researcher writes proposals before Evaluator triage begins.
- Evaluator finishes moving proposals before Implementer starts.
- Implementer finishes code changes and local tests before Scorer starts.
- Scorer finishes measurement before Orchestrator accepts, rejects, or requests
  revision.

Parallel subagents are allowed only for read-only investigation or for writing
to disjoint proposal files. Do not let multiple subagents edit source code,
registry files, `.logbook/leaderboard.json`, or the same history directory at
the same time.

If subagent tooling is unavailable, the Orchestrator must simulate the roles
sequentially in the main agent while still following each role file.

## Subagent Handoff Contracts

Researcher subagent prompt must include:

- incumbent model name and relevant source paths;
- `.logbook/history` and `.logbook/research` paths to inspect;
- maximum number of proposals;
- required output directory;
- instruction to use `roles/templates/proposal.md`;
- stop condition: proposals written and summarized, or no novel ideas found.

Evaluator subagent prompt must include:

- proposal, staging, ready, and scrap directories;
- incumbent model name and relevant source paths;
- instruction to verify scientific and implementation claims against reputable
  literature when claims are uncertain;
- instruction to update proposal `status` and append `Evaluator Notes`;
- stop condition: every reviewed proposal is in exactly one research state and
  ready ideas are ranked or capped.

Implementer subagent prompt must include:

- selected proposal path;
- candidate model name;
- edit-in-place versus new-model instruction;
- files and interfaces that are in scope;
- tests to run;
- stop condition: implementation and local tests completed, or a concrete
  blocker reported before broad edits.

Scorer subagent prompt must include:

- candidate and incumbent model names;
- history directory path;
- worker count and resource limits;
- compatible incumbent artifacts, if any;
- validation permission;
- stop condition: `scores.json` and `scoring_notes.md` written, or a scoring
  blocker recorded.

Every subagent must return a concise summary of files changed or written,
commands run, failures, and recommended next action.

## Model Naming And Incumbent Policy

In-place improvements keep the existing registered model name. New dycores use
a stable snake_case Python package name under `src/dynamaxx/dycore/models/` and
a matching registry key that is short, lowercase, and underscore-separated.

Experimental candidates that are not intended to become an immediately reusable
model should use an `experiment_<slug>` registry key. Accepted new dycores must
be renamed to a stable model name before the leaderboard is updated.

An accepted candidate becomes the incumbent by updating
`.logbook/leaderboard.json`. Do not create a `best/` folder unless the
repository later adds that convention explicitly.

## Validation Discipline

`iteration` is the scratchpad for model development. `validation` is a promotion
gate. Do not repeatedly revise a candidate against validation results.

Rules:

- run validation only after the candidate passes the iteration gate;
- run validation at most once per candidate implementation state;
- if validation fails, reject the candidate or move the idea back to `staging`
  with lessons learned;
- a revised implementation must first pass a new iteration gate before any new
  validation run;
- never inspect `golden` during iterative selection.

## Acceptance Gates

The primary score is the `primary_score` field written by this repository's
evaluation result. It is currently the mean candidate skill against persistence
across reported records.

Candidate and incumbent scores are comparable only when they use the same
protocol, data path, target variables, lead times, and evaluation code. If the
candidate edits the incumbent model in place, compatible incumbent metrics must
be captured before implementation or loaded from immutable history before any
acceptance decision is made.

The fixed gates are intentionally conservative:

1. Unit tests must pass.
2. `fast` must complete without forecast or metric diagnostic failure.
3. `iteration` must improve over the incumbent before validation is run.
4. `validation` must improve over the incumbent before a candidate replaces the
   incumbent.
5. `golden` is never used to choose between iterative candidates.

Default promotion from `iteration` to `validation` requires all of:

- candidate diagnostics are not failed;
- candidate primary score is at least `0.002` higher than the incumbent
  iteration primary score;
- no target variable has mean RMSE regression greater than `2%` over leads
  1-5 days;
- no target variable and lead has RMSE regression greater than `10%` unless the
  Orchestrator records a domain-specific exception before validation.

Default acceptance on `validation` requires all of:

- candidate diagnostics are not failed;
- candidate primary score is at least `0.001` higher than the incumbent
  validation primary score;
- no target variable has mean RMSE regression greater than `2%` over leads
  1-5 days;
- physical plausibility diagnostics and qualitative notes do not identify an
  obvious nonphysical failure mode such as unstable fields, nonfinite values, or
  severe oversmoothing.

The Orchestrator may tighten thresholds for high-risk changes. Loosening a gate
requires a written rationale in `decision.md`.

## Rollback And Clean State

Only one idea may be implemented at a time. Before implementation, the
Orchestrator records the baseline git status and baseline commit hash. If the
worktree is dirty before the experiment starts, the Orchestrator must either
stop or explicitly record which pre-existing files are user-owned and must not
be touched.

Rejected candidates must leave the repository clean:

- candidate code changes are reverted;
- generated evaluation outputs may remain only under `outputs/eval/`;
- immutable history remains under `.logbook/history/`;
- research files are moved out of `.logbook/research/ready`;
- `git status --short` contains no unexpected files.

Do not use destructive git commands that could discard unrelated user work.
