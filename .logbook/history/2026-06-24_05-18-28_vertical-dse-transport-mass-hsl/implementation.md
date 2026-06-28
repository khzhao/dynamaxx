# Implementation Record

## Identity

- Proposal slug: vertical-dse-transport-mass-hsl
- Candidate model name: dino_mass_dse_vdse
- Incumbent model name: dino_hsl2_mass_dse
- Baseline commit: 2c70bb5b77370a074330c2b46954f74f20771f12
- Candidate commit: not committed; working tree remains on baseline commit 2c70bb5b77370a074330c2b46954f74f20771f12

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Registered the side-by-side candidate `dino_mass_dse_vdse` from the incumbent
`dino_hsl2_mass_dse` path. The new selector
`use_dse_vertical_thermal_transport` is forwarded from the adapter into the
Dinosaur primitive equation and enabled only by the new candidate factory.

Inside the existing layer-mass-weighted DSE-HSL thermal branch, the incumbent
mass-DSE tendency is computed first and kept as the exact fallback. When the new
selector and vertical advection are both enabled, the candidate computes the
existing nodal dry-static-energy anomaly, applies the existing
`sigma_dot_full` vertical tendency operator to that anomaly, converts the
result through `1 / Cp`, and substitutes that nodal vertical thermal term in the
mass-DSE modal temperature tendency. The incumbent adiabatic tendency,
pressure/log-pressure tendency, momentum tendencies, pressure-thickness
handling, horizontal mass-DSE conversion, HSL trajectory, forcing, and output
packing remain unchanged.

The candidate falls back to the pre-existing mass-DSE result when incumbent
mass-DSE diagnostics are invalid or when the DSE vertical-transport diagnostics
DSE anomaly, `sigma_dot_full`, converted vertical temperature tendency, or
selected modal temperature tendency are nonfinite. If
`include_vertical_advection` is false, the selector returns the incumbent
mass-DSE tendency without computing the DSE vertical term.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Passed before and after the pytest repair. |
| `git diff --check` | pass | No whitespace errors. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k "vertical_dse or layer_mass_dse or dse_hsl or registry"` | pass | 43 passed, 135 deselected. |
| `uv run dynamaxx-eval fast --model dino_mass_dse_vdse` | pass | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.201778`, metrics at `outputs/eval/fast_dino_mass_dse_vdse.json`. |
| `uv run pytest` | pass | Orchestrator full test gate passed with 244 passed and 2 skipped. |

## Repair Attempts

- Failure observed: initial focused pytest failed in `test_vertical_dse_uses_dse_vertical_tendency_converted_by_cp`.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: corrected the test expectation to compare against the incumbent branch's theta vertical transport converted through potential-temperature pressure scaling, instead of the raw temperature-form vertical tendency.
- Follow-up command and result: reran `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k "vertical_dse or layer_mass_dse or dse_hsl or registry"`; passed with 43 passed and 135 deselected.

## Known Limitations

- Limitation: local checks, fast sanity evaluation, and full pytest passed; iteration and validation scoring were not run by the Implementer.
- Limitation: the fast primary score is recorded for traceability only. The Scorer and Orchestrator own comparison against the incumbent and any accept/reject decision.

## Rollback Notes

Revert this experiment by removing the `use_dse_vertical_thermal_transport`
selector and DSE vertical branch from
`src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`, removing the
adapter field/factory/export and `dino_mass_dse_vdse` registry entry, and
removing the focused vertical-DSE tests added in the three test files. Leave
unrelated `gifs/` and any evaluation outputs untouched unless the Orchestrator
explicitly asks otherwise.
