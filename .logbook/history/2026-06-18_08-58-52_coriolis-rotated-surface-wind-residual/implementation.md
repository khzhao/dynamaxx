# Implementation Record

## Identity

- Proposal slug: coriolis-rotated-surface-wind-residual
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
- Baseline commit: 30a496b1f2ed8f894511404341c7774288bdb4c8
- Candidate commit: not committed; implementation remains in the working tree

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-18_08-58-52_coriolis-rotated-surface-wind-residual/implementation.md

## Implementation Summary

Implemented a side-by-side Dinosaur candidate that preserves the accepted Strang
incumbent flags and enables one new diagnostic residual option:
`rotate_near_surface_wind_residual_by_inertial_phase`.

The incumbent residual path remains scalar for `2m_temperature` and, unless the
new flag is enabled with both 10 m wind components available, scalar for
`10m_u_component_of_wind`. With the new flag enabled, the lead-zero 10 m wind
residual vector is rotated by `f * lead_seconds`, using
`f = 2 * Omega * sin(latitude)` and the accepted exact-Coriolis sign convention:
`u_rot = u*cos + v*sin`, `v_rot = v*cos - u*sin`. The rotated residual is
multiplied by the existing 48 hour exponential decay. Lead zero is explicitly
set to the input analysis winds.

When public outputs request 10 m U but not 10 m V and the initial state includes
both 10 m wind components, the adapter appends hidden raw 10 m V internally for
the residual rotation, then projects the corrected state back to exactly the
original requested output variables before returning.

Orchestrator review added one guardrail: hidden 10 m V expansion is active only
when near-surface residual correction itself is enabled, so manually setting the
rotation flag without residual correction cannot change the public output
contract.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Formatted changed Python files. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 82 passed in 66.77s on the Implementer run. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 83 passed in 67.99s after Orchestrator review fix. |
| `uv run python -c "from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names; name='dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual'; model=create_dycore_model(name); assert name in dycore_model_names(); assert model.name == name; assert model.rotate_near_surface_wind_residual_by_inertial_phase; print(model.name)"` | 0 | Candidate imports and registry creation succeed. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual` | 0 | Final run completed with `failed=False`, `issues=0`, `records=120`, `primary_score=-1.10056`; metrics written to `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual.json`. |

## Repair Attempts

- Failure observed: Orchestrator review found an edge case where setting the
  rotation flag while disabling residual correction could request hidden V
  internally without projecting it out.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: gated hidden V expansion on both residual correction and
  residual rotation being enabled; added a focused contract test.
- Follow-up command and result: focused pytest passed with 83 tests, candidate
  registration check passed, and `git diff --check` passed.

## Known Limitations

- Limitation: Only the requested focused tests and fast evaluation sanity check
  were run by the Implementer; iteration and validation scoring remain for the
  Scorer/Orchestrator.
- Limitation: Hidden 10 m V is computed only for the proposed fixed-output case
  where public outputs include 10 m U, exclude 10 m V, and the initial state
  supplies both 10 m wind components. If V is unavailable, U follows the
  incumbent scalar residual behavior.

## Rollback Notes

Remove the new residual flag and inertial helper/output-expansion logic from
`adapter.py`, remove the candidate factory/export/registry entry, and remove the
focused tests added for this experiment. Do not alter fixed evaluation protocol
files or unrelated history artifacts.
