# dynamaxx

Autoresearch for weather dycores.

Correspondence: Kevin Zhao <kzhao16@gmail.com>

## Quickstart

Dynamaxx uses Python 3.11+ and `uv`.

```bash
uv sync
uv run pytest
```

## Goal that I used to jumpstart Codex/Claude Code

Due to some speed issues, I asked Codex to not run the "baseline" again and again after each change. This resulted in a change in the "protocol" but should be harmless for the result interpretation. 

```
/goal Continuously improve the dycore in this repository by running the agentic optimization loop defined in roles/PROTOCOL.md and roles/ORCHESTRATOR.md.

Use role-specific subagents for Researcher, Evaluator, Implementer, and Scorer when the active Codex surface supports them. If subagents are unavailable, simulate those roles sequentially in the main agent while still following each role file.

Run repeated iterations. For each iteration: inspect resources and git state; initialize or update .logbook; identify the incumbent model; generate a small set of Researcher proposals using roles/templates/proposal.md; have the Evaluator triage and rank them; select exactly one ready idea; implement only that idea; run required tests and fixed evaluation gates using the configured local WeatherBench2 path; compare candidate against incumbent using roles/PROTOCOL.md acceptance thresholds; accept, reject, or request a bounded revision; write complete history artifacts using roles/templates; update leaderboard only for accepted candidates; revert rejected implementation changes; and leave the repository clean before
starting the next iteration.

Do not change fixed evaluation protocols during model-selection experiments. Do not use golden for iterative selection. Do not run multiple implementation ideas at once. Do not stop after one completed candidate; continue until paused by the user or genuinely blocked by a protocol stop condition. After each iteration, report candidate slug, decision, score deltas, changed files, cleanup status, and next action. If a proposed model class changes the forecast contract, such as an ensemble dycore that returns multiple trajectories, treat evaluation support as a separate infrastructure proposal first. The agent may propose adapters or additional metrics, but must not remove existing metrics, splits, or deterministic evaluation gates. Only after the evaluation infrastructure is reviewed, logged, and accepted may model-selection experiments use the expanded protocol.
```

## Data

Default evaluations expect the processed ERA5 WeatherBench2 dataset. See `scripts/packed_state_zarr.py` on how to create it. It just packs together the original WeatherBench2 dataset from Google. The original dataset is a bit fragmented.

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
