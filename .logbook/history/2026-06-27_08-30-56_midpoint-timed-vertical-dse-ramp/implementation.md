# Implementation Record

## Identity

- Proposal slug: `midpoint-timed-vertical-dse-ramp`
- Candidate model name: `dino_hsl2_mass_dse_wtg_vdse_ramp_midtime`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Candidate commit: not committed; candidate rejected at iteration gate.

## Files Changed

- Path: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- Path: `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- Path: `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- Path: `src/dynamaxx/dycore/registry.py`
- Path: `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Path: `tests/dycore/models/dinosaur/test_dependency.py`
- Path: `tests/dycore/test_registry.py`

## Implementation Summary

Added an opt-in selector
`use_midpoint_pressure_ramped_vertical_dse_timing`. When enabled, the
pressure-ramped vertical-DSE increment samples the accepted smooth ramp at
`state.sim_time + 0.5 * horizontal_semilagrangian_theta_transport_step`; when
disabled, the incumbent start-of-step behavior is preserved. Added the
side-by-side factory and registry alias
`dino_hsl2_mass_dse_wtg_vdse_ramp_midtime`.

The implementation preserved the existing vertical-DSE increment, low-mode
pressure guard, per-step temperature cap, WTG filter, residual corrections,
forecast contract, and fixed evaluation protocols.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run python -m compileall -q <touched Python files>` | 0 | Passed before formatting. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'midpoint_timed_vertical_dse_ramp or pressure_ramped_vertical_dse_midpoint_timing or pressure_ramped_vertical_dse_factory or pressure_ramped_vertical_dse_weight_endpoints or pressure_ramped_vertical_dse_non_jit'` | 0 | `6 passed, 134 deselected in 65.62s`. |
| `uv run pytest tests/dycore/test_registry.py -k 'vertical_dse or dycore_model_names' tests/dycore/models/dinosaur/test_dependency.py -k 'vertical_dse or dycore_model_names'` | 0 | `4 passed, 47 deselected in 1.98s`. |
| `uv run ruff format --check <touched Python files>` | 0 | Initially required formatting; passed after `uv run ruff format`. |
| `uv run ruff check <touched Python files>` | 0 | All checks passed. |
| `git diff --check` | 0 | Passed. |
| `uv run pytest <focused post-format selection>` | 0 | `13 passed, 178 deselected in 70.41s`. |
| `uv run pytest` | 0 | `257 passed, 2 skipped in 304.93s`. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_midtime` | 0 | Candidate fast completed with `failed=false`, issues `0`, records `120`, primary `-0.22376081825519012`. |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_midtime --workers 4` | 0 | Candidate iteration completed with `failed=false`, issues `0`, records `120`, primary `-0.2196613024621508`. |
| `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_midtime --workers 4` | not_run | Iteration delta was below the fixed `+0.002` promotion threshold. |

## Repair Attempts

- Failure observed: `ruff format --check` reported four files needing
  formatting.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: ran `uv run ruff format` on touched source/test files.
- Follow-up command and result: format check, ruff check, diff check, focused
  tests, full pytest, fast, and iteration all passed.

## Known Limitations

- The candidate produced only a tiny iteration improvement and did not promote
  to validation.

## Rollback Notes

Revert the implementation diff captured in `candidate.diff`; preserve this
history directory, raw evaluation artifacts, and the staged alternate proposal.
