# Implementation Record

## Identity

- Proposal slug: wind-sparing-held-suarez-relaxation
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs
- Incumbent model name: dinosaur_dfi_surface_residual
- Baseline commit: 845de671268f42c6b44b0a60c287e043087364a1
- Candidate commit: 4756cc9a4b69c41eec60e2177fb03a73974f0e2d

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented a side-by-side Dinosaur candidate that preserves the accepted
digital-filter initialization and near-surface residual correction while adding
a weak, wind-sparing Held-Suarez thermal relaxation term. The forcing is
composed inside the existing primitive-equation trajectory before the stepper
and DFI setup. It uses fixed proposal coefficients, with `kf=0/day`,
`ka=1/160 days`, and `ks=1/16 days`, so velocity damping is disabled and the
change is limited to thermal relaxation.

The local Held-Suarez wrapper returns zero tendencies for vorticity,
divergence, log surface pressure, and all tracer leaves. This keeps the forcing
compatible with the repository forecast contract and avoids changing the fixed
evaluation protocol.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore` | pass | Syntax/import compilation completed. |
| `uv run ruff format ...` | pass | Formatting applied to changed Python files. |
| `uv run ruff check ...` | pass | Lint passed for changed Python files. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | pass | 37 passed. |
| `uv run pytest` | pass | 103 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs` | pass | Primary `-1.1909821759396455`; diagnostics clean. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs --workers 4` | pass | Primary `-1.2218408656785489`; diagnostics clean. |
| `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs --workers 4` | pass | Primary `-1.2103467803549615`; diagnostics clean. |
| `git diff --check` | pass | No whitespace errors before commit. |

## Repair Attempts

- Failure observed: none
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none
- Follow-up command and result: not applicable

## Known Limitations

- Limitation: The largest accepted RMSE regression is long-lead 10 m zonal wind
  at 360 hours, but it remains below the 10 percent guardrail on both iteration
  and validation.

## Rollback Notes

Revert commit `4756cc9a4b69c41eec60e2177fb03a73974f0e2d` to remove this
experiment's implementation changes. The ignored logbook and evaluation
artifacts can remain as historical records.
