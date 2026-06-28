# Implementation Record

## Identity

- Proposal slug: `narrow-core-tropical-wtg-envelope`
- Candidate model name: `dino_hsl2_mass_dse_wtg_vdse_ramp_wtg_narrow`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Candidate commit: not committed; candidate rejected at iteration gate.

## Files Changed

- Path: `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- Path: `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- Path: `src/dynamaxx/dycore/registry.py`
- Path: `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Path: `tests/dycore/models/dinosaur/test_dependency.py`
- Path: `tests/dycore/test_registry.py`

## Implementation Summary

Added an opt-in selector `use_narrow_tropical_wtg_latitude_envelope` and a
side-by-side factory/registry alias
`dino_hsl2_mass_dse_wtg_vdse_ramp_wtg_narrow`. The WTG filter received
configurable latitude-envelope bounds, preserving the incumbent default of full
strength inside `12` degrees and zero by `27` degrees. The candidate used full
strength inside `8` degrees and zero by `22` degrees while preserving the
incumbent WTG sigma envelope, low-mode spectral mask, relaxation timescale,
increment cap, vertical-DSE ramp, forecast contract, and fixed evaluation
protocols.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run python -m compileall -q <touched Python files>` | 0 | Passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'narrow_core_tropical_wtg or tropical_wtg_narrow_latitude_envelope or pressure_ramped_vertical_dse_factory or tropical_wtg_mass_dse_filter'` | 0 | `6 passed, 134 deselected in 42.71s`. |
| `uv run pytest tests/dycore/test_registry.py -k 'narrow_core_tropical_wtg or vertical_dse or dycore_model_names' tests/dycore/models/dinosaur/test_dependency.py -k 'narrow_core_tropical_wtg or vertical_dse or dycore_model_names'` | 0 | `4 passed, 47 deselected in 1.98s`. |
| `uv run ruff format --check <touched Python files>` | 0 | Initially required formatting; passed after `uv run ruff format`. |
| `uv run ruff check <touched Python files>` | 0 | All checks passed. |
| `git diff --check` | 0 | Passed. |
| `uv run pytest <focused post-format selection>` | 0 | `12 passed, 179 deselected in 70.03s`. |
| `uv run pytest` | 0 | `257 passed, 2 skipped in 304.20s`. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_wtg_narrow` | 0 | Candidate fast completed with `failed=false`, issues `0`, records `120`, primary `-0.2244004137048363`. |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_wtg_narrow --workers 4` | 0 | Candidate iteration completed with `failed=false`, issues `0`, records `120`, primary `-0.2203902442291438`. |
| `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_wtg_narrow --workers 4` | not_run | Iteration delta was negative, so validation was skipped. |

## Repair Attempts

- Failure observed: `ruff format --check` reported three files needing
  formatting.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: ran `uv run ruff format` on touched source/test files.
- Follow-up command and result: format check, ruff check, diff check, focused
  tests, full pytest, fast, and iteration all passed.

## Known Limitations

- The candidate degraded iteration primary score relative to the cached
  incumbent.

## Rollback Notes

Revert the implementation diff captured in `candidate.diff`; preserve this
history directory and raw evaluation artifacts.
