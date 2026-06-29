# dynamaxx

Autoresearch for weather dycores.


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

## Citation

If you use Dynamaxx, please cite:

```bibtex
@misc{zhao2026dynamaxx,
  title        = {dynamaxx},
  author       = {Zhao, Kevin and Jiang, Justin and Wang, Zhaoran},
  year         = {2026},
  howpublished = {\url{https://github.com/khzhao/dynamaxx}},
  note         = {Autoresearch for weather dycores},
  version      = {0.1.0}
}
```

## Development

Common local checks:

```bash
uv run pytest
uv run ruff check src
uv run ruff format src
```
