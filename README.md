# dynamaxx

A fixed evaluation framework to optimize weather dycores.

## Quickstart

Dynamaxx uses Python 3.11+ and `uv`.

```bash
uv sync
uv run pytest
```

## Goal that I used to jumpstart Codex/Claude Code

Due to some speed issues, I asked Codex to not run the "baseline" again and again after each change. This resulted in a change in the "protocol" but should be harmless for the result interpretation. 

```
Continuously improve the dycore by running the agentic optimization loop in roles/PROTOCOL.md and roles/ORCHESTRATOR.md, using Researcher, Evaluator, Implementer, and Scorer roles/subagents where available.

Operational constraints include:

- Keep producing research ideas continuously. Do not stop after one candidate.
- Implement exactly one ready proposal per iteration.
- Do not change fixed evaluation protocols during model-selection experiments.
- Do not use golden for iterative selection.
- Always compare candidate to incumbent.
- Reuse cached incumbent scores from .logbook/leaderboard.json when valid; do not rerun incumbent just because candidate code is dirty.
- Latest accepted commit is the best incumbent baseline.
- Accepted candidates update leaderboard and are committed with the full working protocol body.
- Rejected candidates get complete history artifacts, do not update leaderboard, and source changes are reverted.
- Leave tracked worktree clean before starting the next iteration.
- Report candidate slug, decision, score deltas, changed files, cleanup status, and next action after each iteration.
```

## Data

Default evaluations expect the processed ERA5 WeatherBench2 collection at:

The path is configured in `src/dynamaxx/utils/consts.py`.

Real WeatherBench2 integration tests are opt-in:

```bash
DYNAMAXX_RUN_WEATHERBENCH2_TESTS=1 uv run pytest -m "integration and weatherbench2"
```

## Evaluation

Fixed evaluation protocols:

- `fast`: quick real-data development gate. Intended not for selection but just to see if the new dycore blows up or has NaN/Inf. 
- `iteration`: multi-year candidate-development score
- `validation`: held-out model-selection score
- `golden`: locked period that has not been touched

Longer protocols can run in parallel chunks and resume by default:

```bash
uv run dynamaxx-eval iteration --model dinosaur --workers 2
uv run dynamaxx-eval validation --model dinosaur --workers 2
```

Use `--restart` to discard compatible cached chunks for a run.

## Models

Registered models live in `src/dynamaxx/dycore/registry.py`. List them with:

```bash
uv run python -c "from dynamaxx.dycore.registry import dycore_model_names; print('\n'.join(dycore_model_names()))"
```

## Hybrid training

The production frozen-Dinosaur neural-corrector pipeline is described in
[`docs/neural-corrector-first-training-pipeline.md`](docs/neural-corrector-first-training-pipeline.md).
The production default is a 20.69M-parameter, 800-wide learned-physics
corrector with eight residual blocks. Run one static curriculum stage with:

```bash
uv run dynamaxx-train-hybrid \
  --hidden-size 800 \
  --residual-blocks 8 \
  --horizon-hours 6 \
  --output /mnt/data/dynamaxx-training-cache/checkpoints/hybrid-production-20m/6h
```

Checkpoints and training statistics remain in the local output directory. W&B
is used only for scalar training and validation statistics; the trainer does
not create or upload W&B artifacts. Deterministic initialized-state and modal-
target performance caches remain local beside a filesystem-backed dataset and
are reused across compatible curriculum stages.

Run the horizon-weighted 6-hour through 15-day curriculum within the bounded
production compute plan with:

```bash
uv run dynamaxx-train-hybrid-curriculum \
  --output-root /mnt/data/dynamaxx-training-cache/checkpoints/hybrid-production-20m \
  --reference-6h-steps 20000 \
  --bptt-window-hours 24 \
  --wandb-project dynamaxx
```

The stage maxima are 20,000, 10,000, 5,000, 2,500, 1,250, 625, and 334
updates. BPTT is exact through the 24-hour stage; longer numerical rollouts stay
continuous while the recurrent state is detached every 24 hours. Existing
local stages resume automatically, and W&B still receives scalars only.
Validation scalars include WeatherBench2-compatible global RMSE and bias for
headline forecast channels in physical units.

## Development

Common local checks:

```bash
uv run pytest
uv run ruff check src
uv run ruff format src
```
