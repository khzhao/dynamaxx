# Implementation Record

## Identity

- Proposal slug: skew-adjoint-vertical-momentum-advection
- Candidate model name: dino_ri2m_skewvadv
- Incumbent model name: dino_ri2m_ekman_coupled
- Baseline commit: c48695696fc0a05fd92c1020fd50a264c1cb5b59
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py
- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-30_01-05-36_skew-adjoint-vertical-momentum-advection/implementation.md

## Implementation Summary

Implemented the proposal as a side-by-side candidate derived from
`dino_ri2m_ekman_coupled`. Added
`sigma_coordinates.skew_adjoint_vertical_advection`, a zero-boundary interface
stencil satisfying the layer-mass skew identity on unequal sigma layers. Added
the default-false selector
`use_skew_adjoint_vertical_momentum_advection` and applied it only inside
`PrimitiveEquationsSigma.curl_and_div_tendencies` through the local
momentum-only vertical terms. Temperature vertical advection, tracer vertical
advection, pressure continuity, weak-HS, WTG, vertical-DSE, Ekman
stress-pumping, residual memory, and diagnostics use the same paths as the
incumbent.

The candidate computes incumbent centered momentum terms first. When the skew
momentum terms are nonfinite, both momentum components fall back exactly to the
incumbent centered terms for that call.

Registered and exported `dino_ri2m_skewvadv`.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py` | 0 | Syntax check before test runs. |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Reformatted two test files; unrelated source formatting noise was restored afterward. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "skew_vertical_advection or skew_adjoint_vertical_advection or centered_vertical_advection_does_not_satisfy or nonfinite_skew" tests/dycore/test_registry.py -k skew` | 0 | 6 passed, 181 deselected. |
| `uv run pytest tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 1 | First run failed because `tests/dycore/models/dinosaur/test_dependency.py::test_dinosaur_is_registered_as_canonical_dycore_model` lacked the new registry key. |
| `uv run pytest tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | 214 passed, 1 skipped after updating the duplicate dependency registry list. |
| `uv run pytest` | 0 | 280 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dino_ri2m_skewvadv` | 0 | Command completed but fixed diagnostics failed: `failed=True`, `issues=2`, `primary_score=-inf`, metrics at `outputs/eval/fast_dino_ri2m_skewvadv.json`. |

## Repair Attempts

- Failure observed: scoped test failure in duplicate registry-name expectation.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: added `dino_ri2m_skewvadv` to the dependency registry list.
- Follow-up command and result: `uv run pytest tests/dycore/models/dinosaur tests/dycore/test_registry.py` passed with 214 passed, 1 skipped.

- Failure observed: fast eval diagnostics reported `nonfinite_forecast` and `nonfinite_metric` for `dino_ri2m_skewvadv`.
- Implementer-owned failure: unclear; the local finite-guard behavior is covered by tests, and the failed run indicates the finite skew operator destabilizes the rollout before or by the first fixed 24 h output.
- NaN/Inf forecast observed: yes.
- Fix attempted: no code change. Adding damping, clipping, timestep gates, or fallback based on forecast growth would broaden the selected proposal beyond the specified nonfinite skew-tendency fallback.
- Follow-up command and result: not rerun after no code change.

## Known Limitations

- Limitation: the candidate passes local tests but fails the fixed fast sanity evaluation with nonfinite forecasts and nonfinite metrics. The implementation remains registered for scoring inspection, but the fast output is diagnostically failed.
- Limitation: finite guarding is scoped exactly to nonfinite skew momentum tendencies. It does not detect finite skew tendencies that later destabilize the forecast.

## Rollback Notes

Revert the listed source, test, registry, export, and implementation-log changes
from this experiment only. Leave the pre-existing untracked `gifs/` directory
untouched. The generated fast eval artifacts are
`outputs/eval/fast_dino_ri2m_skewvadv.json` and
`outputs/eval/fast_dino_ri2m_skewvadv.csv`.
