# Implementation Record

## Identity

- Proposal slug: pressure-thickness-corrected-mass-dse-hsl
- Candidate model name: dino_mass_dse_fluxcorr
- Incumbent model name: dino_hsl2_mass_dse
- Baseline commit: 2c70bb5b77370a074330c2b46954f74f20771f12
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-23_22-01-24_pressure-thickness-corrected-mass-dse-hsl/implementation.md

## Implementation Summary

Registered side-by-side model `dino_mass_dse_fluxcorr` from
`dino_hsl2_mass_dse`. The new primitive-equation selector preserves the
incumbent mass-DSE HSL path, then computes a matching HSL tendency for
`delta_p`. The candidate forms the corrected horizontal DSE tendency as
`(d(delta_p * s_prime) / dt - s_prime * d(delta_p) / dt) / safe_delta_p`,
converts that horizontal term through `1 / Cp`, and keeps the incumbent
vertical theta and adiabatic terms.

The corrected branch falls back to the exact incumbent mass-DSE tendency when
the correction selector is disabled, when incumbent theta/DSE/mass diagnostics
are invalid, when the pressure-thickness tendency or corrected tendencies are
nonfinite, or when any diagnosed layer pressure thickness is nonpositive.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | All checks passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k "dse or hsl or mass or fluxcorr or registry"` | pass | 55 passed, 122 deselected. |
| `git diff --check` | pass | No whitespace errors. |
| `uv run dynamaxx-eval fast --model dino_mass_dse_fluxcorr` | pass | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.268084`, metrics at `outputs/eval/fast_dino_mass_dse_fluxcorr.json`. |
| `uv run pytest` | pass | Orchestrator full test gate passed with 243 passed and 2 skipped. |

## Repair Attempts

- Failure observed: initial manual patch context did not match the current mass-DSE return block.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: split the source edit into smaller exact-context patches.
- Follow-up command and result: subsequent ruff, focused pytest, `git diff --check`, and fast eval all passed.

## Known Limitations

- The candidate adds one extra scalar HSL remap per thermal tendency evaluation, so runtime is slightly higher than `dino_hsl2_mass_dse`.
- Fast and full pytest gates passed locally. Iteration and validation scoring remain for the Scorer/Orchestrator workflow.
- The prognostic log-surface-pressure equation is unchanged by design; this only corrects the thermal horizontal DSE tendency.

## Rollback Notes

Revert the added primitive-equation selector and corrected branch, remove the
adapter factory/export and registry key, and remove the focused tests that
mention `dino_mass_dse_fluxcorr` or
`use_pressure_thickness_corrected_mass_dse_hsl_transport`. Do not touch
unrelated history, evaluation outputs, or `.logbook/leaderboard.json`.
