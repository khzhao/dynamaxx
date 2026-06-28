# Implementation Record

## Identity

- Proposal slug: `late-lead-vertical-dse-cap-release`
- Candidate model name: `dino_hsl2_mass_dse_wtg_vdse_latecap`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Candidate commit: not committed at implementation time

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

Added a side-by-side Dinosaur dycore model,
`dino_hsl2_mass_dse_wtg_vdse_latecap`, derived from the accepted
`dino_hsl2_mass_dse_wtg_vdse_ramp` incumbent.

The new selector leaves the accepted pressure-ramped vertical-DSE tendency path
unchanged except for the per-inner-step temperature increment limiter. When the
selector is enabled, the cap remains `0.05 K` through 120 forecast hours,
smoothly releases to `0.08 K` by 192 forecast hours, and stays bounded at
`0.08 K` afterward. Invalid schedule inputs fall back to the incumbent `0.05 K`
cap, and invalid step size or diagnostics still return the incumbent tendency.

The incumbent model's default behavior remains disabled for the new selector.
WTG relaxation, mass-DSE horizontal transport, pressure ramping, low-mode guard,
surface residuals, output packing, target variables, and evaluation protocols
were not changed.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Implementer syntax check. |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Implementer formatting check. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Implementer lint check. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k 'late_cap or pressure_ramped_vertical_dse or vertical_dse_non_jit or registry_lists_default_dycore_models'` | 0 | Implementer focused test run: `19 passed`. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_latecap` | 0 | Candidate fast score `-0.22415855014566696`; diagnostics clean with zero issues and 120 records. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py::test_dinosaur_is_registered_as_canonical_dycore_model` | 0 | Orchestrator repair verification after adding the new registry key to the canonical tuple test. |
| `uv run pytest` | 0 | Full required test suite: `262 passed, 2 skipped in 304.46s`. |

## Repair Attempts

- Failure observed: first full `uv run pytest` failed
  `tests/dycore/models/dinosaur/test_dependency.py::test_dinosaur_is_registered_as_canonical_dycore_model`
  because the new registered model key was missing from that test's expected
  tuple.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: added `dino_hsl2_mass_dse_wtg_vdse_latecap` to the canonical
  dycore model tuple in `tests/dycore/models/dinosaur/test_dependency.py`.
- Follow-up command and result:
  `uv run pytest tests/dycore/models/dinosaur/test_dependency.py::test_dinosaur_is_registered_as_canonical_dycore_model`
  exited `0`; full `uv run pytest` then exited `0`.

## Known Limitations

- Fast scoring is only a sanity gate; iteration scoring is required for
  promotion and validation scoring is required for acceptance.
- The proposal's exact early no-op claim still needs verification against
  iteration artifacts, because the implementation changes the forecast
  trajectory only after the fixed 120 h schedule boundary.

## Rollback Notes

If rejected, revert the seven source/test files using
`candidate.diff` from this history directory. Do not remove raw evaluation
artifacts or unrelated pre-existing untracked content such as `gifs/`.
