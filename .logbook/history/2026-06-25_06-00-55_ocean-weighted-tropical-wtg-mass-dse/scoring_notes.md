# Scoring Notes

## Scope

- Role: Scorer
- Proposal slug: `ocean-weighted-tropical-wtg-mass-dse`
- Candidate model: `dino_hsl2_mass_dse_wtg_ocean`
- Incumbent model: `dino_hsl2_mass_dse_wtg`
- History directory: `.logbook/history/2026-06-25_06-00-55_ocean-weighted-tropical-wtg-mass-dse`
- Worker count: 4
- Validation: skipped because iteration failed the promotion gate
- Golden protocol: not run

## Protocol Inputs

Read and followed `roles/PROTOCOL.md`, `roles/SCORER.md`, and `roles/ORCHESTRATOR.md`. The history directory already existed. Candidate and incumbent registration were confirmed through `dycore_model_names()` and `create_dycore_model()`.

The Orchestrator-provided full test gate was recorded rather than rerun: `uv run pytest` exit 0, `249 passed, 2 skipped in 272.47s`.

## Commands

| Command | Exit status | Notes |
| --- | ---: | --- |
| `uv run pytest` | 0 | Recorded from Orchestrator; not rerun by Scorer. |
| `uv run python - <<'PY' ... create_dycore_model, dycore_model_names ... PY` | 0 | Confirmed both models are registered and constructible. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_ocean` | 0 | Candidate fast sanity gate completed cleanly. |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_ocean --workers 4` | 0 | Candidate iteration evaluation completed cleanly. |

Validation command not run: iteration primary delta was `-0.000840153561011`, below the required `+0.002` promotion threshold. Golden was not run.

## Fast Gate

- Candidate artifact: `outputs/eval/fast_dino_hsl2_mass_dse_wtg_ocean.json` and `outputs/eval/fast_dino_hsl2_mass_dse_wtg_ocean.csv`
- Candidate primary score: `-0.260677801431530`
- Diagnostics: `failed=False`, `issues=0`, `records=120`
- Gate status: passed

## Incumbent Cache Reuse

Reused leaderboard incumbent metrics for iteration. No incumbent rerun was performed.

Validation checks:

- Requested incumbent equals `.logbook/leaderboard.json.incumbent_model_name`: yes
- Leaderboard incumbent commit: `d8561caebb78ca096263d8c412217570ff2d1f46`
- Leaderboard eval code commit: `d8561caebb78ca096263d8c412217570ff2d1f46`
- Current `HEAD`: `d8561caebb78ca096263d8c412217570ff2d1f46`
- Dirty tracked paths: `src/dynamaxx/dycore/models/dinosaur/__init__.py, src/dynamaxx/dycore/models/dinosaur/adapter.py, src/dynamaxx/dycore/registry.py, tests/dycore/models/dinosaur/test_dependency.py, tests/dycore/models/dinosaur/test_primitive_equations.py, tests/dycore/test_registry.py`
- Dirty paths are candidate dycore/registry/tests and do not invalidate the accepted incumbent cache under `roles/SCORER.md`.
- Fingerprint data path: `/home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative`
- Fingerprint protocols include `iteration` and `validation`; target variables and lead days match the requested protocol.
- Reused iteration artifact: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg.json` / `outputs/eval/iteration_dino_hsl2_mass_dse_wtg.csv`
- Validation incumbent cache was checked as available and valid but not used because validation was skipped: `outputs/eval/validation_dino_hsl2_mass_dse_wtg.json` / `outputs/eval/validation_dino_hsl2_mass_dse_wtg.csv`

## Iteration Results

- Candidate artifact: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_ocean.json` / `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_ocean.csv`
- Incumbent artifact: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg.json` / `outputs/eval/iteration_dino_hsl2_mass_dse_wtg.csv`
- Candidate primary score: `-0.259352508499267`
- Incumbent primary score: `-0.258512354938256`
- Primary delta: `-0.000840153561011`
- Required promotion delta: `+0.002`
- Diagnostics: `failed=False`, `issues=0`, `records=120`
- Promotion gate status: failed primary delta
- Early-lead mean RMSE guardrail: passed, worst relative change `0.122777%` versus `2%` limit
- Single variable-lead RMSE guardrail: passed, worst relative change `0.435032%` versus `10%` limit

Early-lead mean RMSE changes over leads 1-5 days:

| Variable | Candidate mean RMSE | Incumbent mean RMSE | Absolute change | Relative change |
| --- | ---: | ---: | ---: | ---: |
| `10m_u_component_of_wind` | 4.35636291415 | 4.35102085978 | 0.00534205436925 | 0.122777% |
| `2m_temperature` | 4.71996157963 | 4.71925706834 | 0.000704511290438 | 0.014928% |
| `geopotential_500` | 603.174198864 | 603.077786911 | 0.0964119533728 | 0.015987% |
| `mean_sea_level_pressure` | 781.197527913 | 780.7695161 | 0.428011813275 | 0.054819% |

Worst single variable-lead RMSE regression: `10m_u_component_of_wind` at `360` h, candidate RMSE `5.66512579514` vs incumbent `5.64058742838`, relative change `0.435032%`.

Best single variable-lead RMSE improvement: `mean_sea_level_pressure` at `24` h, relative change `-0.005009%`.

## Validation

Validation was allowed only if iteration passed the protocol promotion gates. Since the iteration primary delta was below `+0.002`, validation was not run and no candidate validation artifact was produced.

## Diagnostics And Anomalies

- Candidate fast and iteration reported `failed=False` and `issues=0`.
- Iteration made steady chunk progress but was slow, completing 229 parallel chunks before writing metrics.
- No incumbent command was run; the incumbent comparison came from the valid leaderboard cache.
- No golden protocol was run.
- The Scorer did not modify dycore source, tests, roles, protocols, leaderboard, research queue state, or commits.

## Measurement Lessons

- Ocean-weighted tropical WTG mass-DSE worsened the iteration primary score by `-0.000840` despite clean diagnostics and small RMSE guardrail movements.
- Early-lead RMSE moved slightly worse for all four target variables; the largest early relative regression was `0.122777%` in `10m_u_component_of_wind`.
- The worst single-lead regression was also wind at day 15, still far below the guardrail; the failed primary gate, not stability or guardrails, is the blocking measurement.
