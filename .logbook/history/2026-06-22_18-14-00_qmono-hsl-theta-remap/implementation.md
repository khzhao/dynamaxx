# Implementation Record

## Identity

- Proposal slug: qmono-hsl-theta-remap
- Candidate model name: dino_hsl_qmono
- Incumbent model name: dino_hsl2_theta
- Baseline commit: 72efada4e0afbd8e34e3184dbcef90cb91cc051c
- Candidate commit: not committed before scoring

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented a side-by-side `dino_hsl_qmono` candidate derived from
`dino_hsl2_theta`. The candidate preserves the accepted midpoint horizontal
semi-Lagrangian theta departure path and changes only the theta-anomaly scalar
remap hook. The new remap forms a tensor-product, PCHIP-style monotone cubic
candidate in longitude and latitude, bounds candidate values by the local 4x4
stencil extrema, and falls back to the accepted bilinear remap for boundary
rows, invalid stencils, or nonfinite diagnostics.

The adapter, package export, and registry gained one opt-in
`use_quasi_monotone_theta_remap` selector and one registered alias,
`dino_hsl_qmono`. Momentum remapping, midpoint departure winds, vertical theta
transport, pressure work, forcing, output variables, lead schedule, and fixed
evaluation protocols were left unchanged.

Focused tests cover factory parity with `dino_hsl2_theta`, registry export,
constant and linear remap behavior, local-stencil boundedness, zero-wind parity,
nonfinite qmono fallback to bilinear HSL2, unchanged non-theta explicit
tendencies, and a small finite non-JIT forecast smoke path.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | all checks passed |
| `git diff --check` | 0 | no whitespace errors |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'qmono or hsl' tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 23 passed, 143 deselected in 73.98s |
| `uv run pytest` | 0 | 232 passed, 2 skipped in 206.00s |
| `uv run dynamaxx-eval fast --model dino_hsl_qmono` | not_run | next scorer gate |

## Repair Attempts

- Failure observed: none during local verification
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none needed after resuming implementation
- Follow-up command and result: not applicable

## Known Limitations

- The qmono candidate is intentionally limited to theta-anomaly remapping. It
  does not regularize departure winds or change vertical coherence across
  layers.
- The qmono path falls back to bilinear remapping at latitude boundary rows,
  so any benefit is expected from interior theta-gradient transport.

## Rollback Notes

Reverse `.logbook/history/2026-06-22_18-14-00_qmono-hsl-theta-remap/candidate.diff`
from the repository root to remove only this experiment's source and test
changes if the candidate is rejected.
