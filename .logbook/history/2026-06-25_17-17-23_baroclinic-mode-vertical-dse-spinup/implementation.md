# Implementation Record

## Identity

- Proposal slug: baroclinic-mode-vertical-dse-spinup
- Candidate model name: dino_hsl2_mass_dse_wtg_vdse_bm
- Incumbent model name: dino_hsl2_mass_dse_wtg_vdse_ramp
- Baseline commit: ff40def55ac707e8915c840b856a0aaa3345b046
- Candidate commit: uncommitted candidate worktree

## Files Changed

- src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- src/dynamaxx/dycore/models/dinosaur/adapter.py
- src/dynamaxx/dycore/models/dinosaur/__init__.py
- src/dynamaxx/dycore/registry.py
- tests/dycore/models/dinosaur/test_dependency.py
- tests/dycore/models/dinosaur/test_primitive_equations.py
- tests/dycore/test_registry.py

## Implementation Summary

Registered `dino_hsl2_mass_dse_wtg_vdse_bm` side by side with the
pressure-ramped vertical-DSE incumbent. The candidate keeps the accepted
mass-DSE HSL transport, WTG relaxation, pressure-ramped vertical-DSE path, cap,
low-mode pressure guard, and finite fallback.

When the new selector is enabled, the raw vertical-DSE temperature increment is
split into a pressure-thickness-weighted external column component and a
zero-column-mean internal component. The external component keeps the incumbent
zero-through-24h, full-by-72h ramp. The internal component uses a fixed smooth
zero-through-12h, full-by-48h ramp before the shared pressure guard and
per-inner-step cap. Invalid split diagnostics fall back to the incumbent
pressure-ramped vertical-DSE tendency.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q ...` | 0 | Implementer syntax check over modified modules. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "vertical_dse or pressure_weighted_column_split or baroclinic_mode"` | 0 | `10 passed`. |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py -k "registry or registered or dycore_model_names or vertical_dse or dependency"` | 0 | `51 passed`. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py` | 0 | `141 passed`. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_bm` | 0 | Fast sanity passed with clean diagnostics; primary score `-0.23079739639076055`. |
| `git diff --check` | 0 | Implementer whitespace check passed. |
| `uv run pytest` | 0 | Orchestrator full test gate: `258 passed, 2 skipped in 277.83s`. |

## Repair Attempts

- Failure observed: none reported by Implementer after bounded implementation.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: not applicable.
- Follow-up command and result: all targeted checks, candidate fast, and full
  pytest passed.

## Known Limitations

- Candidate fast primary score was below the incumbent fast score, but fast is
  a sanity gate and diagnostics were clean. Fixed iteration and validation gates
  determine selection.
- The internal-mode ramp may still perturb hydrostatic thickness even with a
  zero pressure-weighted column mean, so MSLP guardrails need explicit review.

## Rollback Notes

If rejected, revert the source/test diff captured in `candidate.diff`, remove
the selected proposal from `.logbook/research/ready`, leave raw evaluation
outputs for reproducibility, and do not update `.logbook/leaderboard.json`.
