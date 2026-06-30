# Implementation Record

## Identity

- Proposal slug: ekman-balanced-spinup-ramp
- Candidate model name: dino_ri2m_ekman_spinup
- Incumbent model name: dino_ri2m_ekman_coupled
- Baseline commit: 6fabde16f8cd8e5e55f67c6cc31fc63795c59617
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-30_05-41-41_ekman-balanced-spinup-ramp/implementation.md

## Implementation Summary

Added a default-false `apply_ekman_positive_time_spinup_ramp` selector to the
Dinosaur adapter and registered the side-by-side `dino_ri2m_ekman_spinup`
factory. The incumbent Ekman coupled filter still computes the accepted stress,
drag, depth, vertical/equatorial taper, wind caps, pressure cap, area-neutral
pressure projection, finite fallback, wind projection, and safety checks before
any candidate-only change.

For the candidate selector only, the filter computes a smooth scalar from
`State.sim_time`: 0.35 at forecast time zero, smoothstep to 1.0 by 24 forecast
hours, and 1.0 thereafter. Missing, nonfinite, or negative `sim_time` returns
1.0 so the filter falls back to full-strength incumbent behavior. The scalar is
applied after the incumbent caps/projections to the already capped nodal wind
increments, modal wind increments, and log-pressure increment. The forecast
initialization path now requests `sim_time` when either the existing vertical-DSE
ramp or this new Ekman spinup selector needs it.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Syntax/import smoke for changed Python files. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "ekman_spinup or ekman_positive_time_spinup" tests/dycore/test_registry.py -k "ekman_spinup or lists_default"` | 1 then 0 | Initial run found all-one fallback roundoff; rerun passed 9 selected tests. |
| `uv run pytest tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | 217 passed, 1 skipped. |
| `uv run pytest` | 0 | 283 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_spinup` | 0 | failed=False, issues=0, records=120, primary_score=-0.16944, metrics written to outputs/eval/fast_dino_ri2m_ekman_spinup.json. |

## Repair Attempts

- Failure observed: Focused tests showed the spinup path with missing, invalid,
  negative, or 24h `sim_time` did not exactly match the incumbent.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: Removed a redundant modal recomputation after applying an
  all-one ramp factor. The implementation now scales the already computed modal
  vorticity/divergence increments directly, preserving exact incumbent behavior
  when the factor is 1.0 while still scaling capped nodal diagnostics and
  pressure increments.
- Follow-up command and result: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "ekman_spinup or ekman_positive_time_spinup" tests/dycore/test_registry.py -k "ekman_spinup or lists_default"` exited 0 with 9 passed.

## Known Limitations

- Limitation: No iteration, validation, golden, incumbent, metric, split,
  target-variable, lead-range, or WeatherBench2 evaluation-code changes were
  made or run. The fast sanity score is only a finite/diagnostic gate for the
  candidate implementation, not a promotion decision.

## Rollback Notes

Revert this experiment by removing the `apply_ekman_positive_time_spinup_ramp`
field, the `_ekman_positive_time_spinup_ramp` helper, the candidate-only scaling
branch in `_ekman_coupled_surface_step_filter`, the
`ekman_spinup_dinosaur_dycore_model` factory/export, the
`dino_ri2m_ekman_spinup` registry factory/key, the focused spinup tests, and
this implementation record. Leave unrelated files and pre-existing untracked
`gifs/` untouched.
