# Implementation Record

## Identity

- Proposal slug: `recenter-before-wtg-filter-order`
- Candidate model name: `dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Candidate commit: uncommitted working tree based on
  `ff40def55ac707e8915c840b856a0aaa3345b046`

## Files Changed

- Path: `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- Path: `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- Path: `src/dynamaxx/dycore/registry.py`
- Path: `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Path: `tests/dycore/models/dinosaur/test_dependency.py`
- Path: `tests/dycore/test_registry.py`

## Implementation Summary

Added a side-by-side candidate,
`dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg`, derived from the accepted
`dino_hsl2_mass_dse_wtg_vdse_ramp` incumbent. The new opt-in selector
`apply_theta_recenter_before_tropical_wtg` changes only the positive-time
rollout order when both theta layer-mean recentering and tropical WTG mass-DSE
relaxation are enabled.

The incumbent remains unchanged: rollout filters append WTG before theta
recentering. The candidate appends theta recentering before WTG. DFI filters are
still built before these rollout-only filters are appended, so DFI remains
unchanged and excludes both WTG and theta recentering as before.

The implementation adds factory/export/registry coverage for the candidate and
focused tests for factory parity, registry creation, incumbent filter order,
candidate filter order, DFI exclusion, and a finite non-JIT smoke forecast.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "precentered_wtg or trajectory_function_applies_precentered_wtg_rollout_order or trajectory_function_keeps_incumbent_wtg_before_theta_recenter or trajectory_function_applies_tropical_wtg_to_rollout_only" tests/dycore/models/dinosaur/test_dependency.py -k "precentered_wtg or pressure_ramped_vertical_dse_wtg" tests/dycore/test_registry.py -k "precentered_wtg or pressure_ramped_vertical_dse"` | 0 | 13 passed, 179 deselected in 94.85s after formatting. |
| `python -m compileall -q <touched Python files>` | 0 | Passed after formatting. |
| `uv run ruff check <touched Python files>` | 0 | Passed. |
| `uv run ruff format --check <touched Python files>` | 0 | Passed after applying `uv run ruff format` to three touched files. |
| `git diff --check` | 0 | Passed. |
| `uv run pytest` | 0 | 258 passed, 2 skipped in 347.65s. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg` | not_run | To be run by Orchestrator/Scorer after this implementation record. |

## Repair Attempts

- Failure observed: `uv run ruff format --check` initially reported that
  `adapter.py`, `registry.py`, and `test_primitive_equations.py` needed
  formatting.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: ran `uv run ruff format` on the three reported files.
- Follow-up command and result: focused tests, compileall, ruff check, ruff
  format check, `git diff --check`, and full `uv run pytest` all passed.

## Known Limitations

- Limitation: This is a numerical splitting/order experiment. If the two
  rollout filters effectively commute under the current step size and caps, the
  metric movement may be near numerical noise.

## Rollback Notes

Reverse-apply `candidate.diff` from this history directory and remove the ready
proposal for this slug if the candidate is rejected. No fixed evaluation
protocol files were changed.
