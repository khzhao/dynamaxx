# Implementation Record

## Identity

- Proposal slug: dse-consistent-sigma-initialization
- Candidate model name: dino_mass_dse_init
- Incumbent model name: dino_hsl2_mass_dse
- Baseline commit: 2c70bb5b77370a074330c2b46954f74f20771f12
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-24_08-43-43_dse-consistent-sigma-initialization/implementation.md

## Implementation Summary

Registered `dino_mass_dse_init` as a side-by-side model derived from
`layer_mass_weighted_dse_hsl_transport_dinosaur_dycore_model()`.

Added the opt-in adapter flag `use_dse_consistent_sigma_initialization`. When
enabled and pressure-level geopotential is available, `weather_state_to_dinosaur_state`
first performs the incumbent pressure-level hydrostatic/layer-mean temperature
construction, then builds pressure-level dry-static-energy anomaly
`Cp * T + Phi` with the same layer-wise horizontal quadrature-mean removal used
by the rollout DSE diagnostic. It projects that anomaly to sigma with the same
pressure-to-sigma mapping selected for initialization, computes the current dry
sigma DSE anomaly from the existing hydrostatic geopotential diagnostic, and
applies bounded local `delta_T = (s_projected - s_current) / Cp` to sigma
temperature before recomputing `temperature_variation`.

The correction falls back exactly to incumbent sigma temperature when
pressure-level geopotential is missing, static shapes are incompatible, projected
or corrected fields are nonfinite, or any local correction exceeds the fixed
8 K cap. Winds, humidity, surface pressure, output diagnostics, rollout
equations, pressure/log-pressure tendency, momentum, HSL trajectory, forcing,
and fixed protocols are unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Passed after import-order repair. |
| `git diff --check` | pass | No whitespace errors. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "dse or initialization"` | pass | 31 passed, 98 deselected. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 47 passed. |
| `uv run dynamaxx-eval fast --model dino_mass_dse_init` | pass | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.26308`, metrics at `outputs/eval/fast_dino_mass_dse_init.json`. |
| `uv run pytest` | pass | Orchestrator full test gate passed with 242 passed and 2 skipped. |

## Repair Attempts

- Failure observed: Ruff import-order errors in `src/dynamaxx/dycore/models/dinosaur/__init__.py` and `tests/dycore/models/dinosaur/test_primitive_equations.py`.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: Reordered the new factory import next to the existing DSE transport import.
- Follow-up command and result: Required ruff command passed.

## Known Limitations

- The initialization correction is accepted or rejected as a whole-state scalar
  guard, so one nonfinite or over-cap local correction falls back to the full
  incumbent initialization for that initialized state.
- Local checks, fast sanity evaluation, and full pytest passed; iteration and
  validation were not run by the Implementer.
- `.logbook/leaderboard.json` was not updated and no commit was made.

## Rollback Notes

Revert the source, test, and implementation-log changes listed above. Leave the
unrelated untracked `gifs/` directory and generated evaluation outputs untouched
unless the Orchestrator explicitly requests cleanup.
