# Implementation Record

## Identity

- Proposal slug: cfl-blended-hsl-theta
- Candidate model name: dino_hsl_cflblend
- Incumbent model name: dino_hsl2_theta
- Baseline commit: 72efada4e0afbd8e34e3184dbcef90cb91cc051c
- Candidate commit: uncommitted worktree

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`
- `.logbook/history/2026-06-22_17-36-00_cfl-blended-hsl-theta/implementation.md`

## Implementation Summary

Added the side-by-side `dino_hsl_cflblend` candidate on top of the accepted
`dino_hsl2_theta` path. The new selector
`use_cfl_blended_semilagrangian_theta_transport` is false by default and true
only for the new factory/registry alias.

Inside horizontal dry-theta anomaly HSL transport, the candidate computes a
local blend weight from the already capped midpoint longitude and latitude
displacements:

- `weight = sqrt(max(abs(longitude_displacement) / longitude_cap,
  abs(latitude_displacement) / latitude_cap))`, clipped to `[0, 1]`;
- weight `0` selects the incumbent Eulerian theta horizontal tendency;
- capped displacement selects the accepted midpoint HSL theta tendency.

If the midpoint HSL diagnostics, weights, or blended tendency are nonfinite, the
code falls back to the accepted `dino_hsl2_theta` fallback chain. No vertical
theta transport, pressure-work terms, momentum, pressure continuity, passive
humidity, filters, residual corrections, or output packing were changed.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | All checks passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "cflblend or hsl2_theta_factory_preserves_hsl_theta_except_midpoint_selector or hsl2_theta_midpoint_displacement_is_finite_and_bounded or hsl2_theta_nonfinite_midpoint_wind_falls_back_to_first_order or hsl2_theta_non_jit_forecast_smoke_is_finite" tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | 11 passed, 153 deselected. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | 42 passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "hsl or cflblend"` | passed | 18 passed, 104 deselected. |
| `uv run pytest` | passed | 230 passed, 2 skipped in 185.03s. |
| `uv run dynamaxx-eval fast --model dino_hsl_cflblend` | failed before repair | Primary score was the negative sentinel for nonfinite metrics; diagnostics reported nonfinite forecast and nonfinite metric records. |

## Orchestrator Repair Notes

- Initial fast gate produced nonfinite forecasts and metrics. This was treated
  as an implementation/numerical-stability issue within the selected proposal
  scope.
- Repair: changed the local displacement blend from linear CFL weight to a
  concave square-root CFL weight. Zero displacement still selects the Eulerian
  theta tendency, capped displacement still selects the accepted midpoint HSL
  tendency, and small nonzero displacements retain more of the accepted stable
  HSL path.
- Post-repair `uv run ruff check ...`: passed.
- Post-repair `git diff --check`: passed.
- Post-repair `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "hsl or cflblend" tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`: 21 passed, 143 deselected in 55.10s.
- Post-repair `uv run pytest`: 230 passed, 2 skipped in 185.94s.
- Post-repair `uv run dynamaxx-eval fast --model dino_hsl_cflblend`: failed.
  Diagnostics again reported nonfinite forecast and nonfinite metric records.
  No iteration or validation gate was run.

## Repair Attempts

- Failure observed: none during focused checks
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: not applicable
- Follow-up command and result: not applicable

## Known Limitations

- Fixed WeatherBench2 fast, iteration, and validation gates were not run.
- The scientific score impact is unknown until the Scorer runs the fixed eval
  protocols.

## Rollback Notes

Rollback for a rejected candidate should remove the CFL selector/helper and
blend branch from `primitive_equations.py`, remove the adapter factory and
registry alias, remove the package export, and remove the focused tests and this
implementation record. Do not alter unrelated history or evaluation artifacts.
