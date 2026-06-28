# Implementation Record

## Identity

- Proposal slug: tropical-wtg-mass-dse-relaxation
- Candidate model name: dino_hsl2_mass_dse_wtg
- Incumbent model name: dino_hsl2_mass_dse
- Baseline commit: 2c70bb5b77370a074330c2b46954f74f20771f12
- Candidate commit: uncommitted working tree

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-25_01-45-51_tropical-wtg-mass-dse-relaxation/implementation.md

## Implementation Summary

Implemented one side-by-side candidate, `dino_hsl2_mass_dse_wtg`, derived from
`layer_mass_weighted_dse_hsl_transport_dinosaur_dycore_model()` with only the
model name and `apply_tropical_wtg_mass_dse_relaxation` selector changed.

The selector adds a positive-time rollout filter in `adapter.py` after incumbent
rollout filters and before theta recentering. The filter diagnoses next-state
dry static energy anomaly and sigma-layer pressure thickness through existing
primitive-equation dry hydrostatic helpers, applies fixed tropical latitude,
free-tropospheric sigma, and low-mode masks, relaxes masked mass-DSE anomalies
toward the tropical area-weighted layer mean on a fixed 5-day timescale, caps
the thermal increment at 0.25 K per inner step, and applies only a temperature
variation increment. The increment is mask-supported layer neutral, and unsafe
pressure, DSE, mask, increment, or corrected-temperature diagnostics fall back
to the incoming next state.

DFI filters are built before adding the WTG and theta-recenter rollout-only
filters, so time-reversed initialization remains incumbent-compatible.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Reran after repairs; all checks passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "wtg or mass_dse"` | pass | 8 passed, 122 deselected. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 47 passed. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg` | pass | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.259781`, metrics at `outputs/eval/fast_dino_hsl2_mass_dse_wtg.json`. |

## Repair Attempts

- Failure observed: initial ruff check found a stale `bad_next_state` variable in a new WTG fallback assertion.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: changed the assertion to compare against `next_state`.
- Follow-up command and result: required ruff command passed.

- Failure observed: first focused pytest run had two WTG test failures. The polar no-op assertion was too strict for a modal state reconstructed from a localized nodal mask, and the DFI filter-list test did not call the lazily built analysis-offset trajectory.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: bounded the polar leakage assertion to 1% of the fixed step cap and invoked the returned trajectory on a synthetic state to trigger lazy trajectory construction.
- Follow-up command and result: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "wtg or mass_dse"` passed.

## Known Limitations

- The WTG increment is represented in the model's modal state, so a localized tropical mask can leave tiny nodal leakage outside the latitude mask after spectral projection. The implementation keeps the induced increment exactly zero on fully masked sigma layers and tests polar leakage at less than 1% of the fixed step cap.
- Only fast was run by the Implementer. Iteration and validation scoring remain for the Scorer/Orchestrator.

## Rollback Notes

Revert the edits to the files listed above for this experiment only. Do not
touch unrelated worktree content such as the pre-existing untracked `gifs/`
directory or any evaluation outputs unless the Orchestrator explicitly requests
cleanup.
