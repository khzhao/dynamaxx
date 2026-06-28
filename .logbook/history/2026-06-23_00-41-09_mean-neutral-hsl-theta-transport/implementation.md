# Implementation Record

## Identity

- Proposal slug: mean-neutral-hsl-theta-transport
- Candidate model name: dino_hsl_mean
- Incumbent model name: dino_hsl2_theta
- Baseline commit: 72efada4e0afbd8e34e3184dbcef90cb91cc051c
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-23_00-41-09_mean-neutral-hsl-theta-transport/implementation.md

## Implementation Summary

Added a default-false
`use_mean_neutral_semilagrangian_theta_transport` selector to
`PrimitiveEquationsSigma`, the concrete primitive-equation constructors, the
Dinosaur adapter dataclass, and `_primitive_equation` plumbing. When enabled,
finite first-order and midpoint horizontal semi-Lagrangian dry-theta anomaly
candidate tendencies subtract the quadrature-weighted horizontal layer mean of
the remap increment before branch acceptance. A final finite tendency residual
is removed to keep the realized candidate tendency layer-mean neutral under
fp32 summation. If quadrature weights, weight sum, corrected remap diagnostics,
or corrected tendency diagnostics are invalid, that branch returns the accepted
uncorrected HSL theta tendency.

Added
`mean_neutral_semilagrangian_theta_transport_dinosaur_dycore_model()`, exported
it from the Dinosaur package, and registered `dino_hsl_mean` as a side-by-side
alias that starts from `dino_hsl2_theta` and changes only the new selector plus
name.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'hsl_mean'` | passed | 6 passed, 116 deselected. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | All checks passed. |
| `git diff --check` | passed | No whitespace errors. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'hsl_mean or hsl2_theta or hsl_theta' tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | 22 passed, 143 deselected. |
| `uv run dynamaxx-eval fast --model dino_hsl_mean` | not_run | Left final fixed scoring to Orchestrator/Scorer. |

## Repair Attempts

- Failure observed: initial `hsl_mean` pytest subset had two failures.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: removed a small fp32 residual in the corrected candidate
  tendency after remap recentering, and changed the invalid quadrature-weight
  test to monkeypatch the read-only grid property instead of assigning to it.
- Follow-up command and result:
  `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'hsl_mean'`
  passed with 6 passed, 116 deselected.

## Known Limitations

- No iteration, validation, golden, or fast evaluation protocol was run by the
  Implementer.
- The fallback covers invalid finite diagnostics. Static shape-incompatible
  quadrature weights would still fail before JAX execution, matching the
  repository's normal fixed-grid assumptions.

## Rollback Notes

Remove the new selector/helper/plumbing, the
`mean_neutral_semilagrangian_theta_transport_dinosaur_dycore_model()` factory,
the `dino_hsl_mean` registry/export entries, and the focused tests added for
factory parity, registry/dependency coverage, mean neutrality, zero wind,
invalid-weight fallback, non-theta tendencies, and non-JIT smoke forecasting.
