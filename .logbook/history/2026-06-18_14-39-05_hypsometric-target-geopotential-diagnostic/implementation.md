# Implementation Record

## Identity

- Proposal slug: hypsometric-target-geopotential-diagnostic
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_hypsometric_z
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
- Baseline commit: 30a496b1f2ed8f894511404341c7774288bdb4c8
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-18_14-39-05_hypsometric-target-geopotential-diagnostic/implementation.md

## Implementation Summary

Implemented a default-off hypsometric geopotential output option on the Dinosaur adapter and registered the side-by-side Strang candidate
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_hypsometric_z`.

The incumbent rollout dynamics, DFI, weak Held-Suarez forcing, pressure-to-sigma initialization, near-surface residual correction, symmetric exact-Coriolis split, and non-geopotential output paths remain unchanged. When the new option is enabled, pressure-level geopotential is recomputed from sigma-center geopotential, pressure geometry, and bounded virtual temperature using the local hypsometric increment. Out-of-range targets and columns with nonfinite sigma pressure, geopotential, or virtual temperature fall back to the incumbent finite sigma-to-pressure interpolation result.

Focused tests cover the analytic isothermal hypsometric relation, fallback behavior, virtual-temperature bounds, output-path isolation to pressure-level geopotential, candidate factory flags, registry exposure, import dependency behavior, and a finite non-JIT smoke forecast.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 1 | Initial run: 80 passed, 1 failed. Fallback test exposed that nonfinite geopotential elsewhere in a column was not considered column-unusable. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 81 passed in 70.44s. |
| `uv run pytest` | 0 | 147 passed, 2 skipped in 77.96s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_hypsometric_z` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-1.0961`; metrics written to `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_hypsometric_z.json`. |

## Repair Attempts

- Failure observed: focused fallback test failed because the helper used the nearer finite bracket geopotential even though another sigma geopotential value in the column was nonfinite.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: tightened hypsometric usability checks so any nonfinite sigma geopotential or virtual temperature marks the column unusable for this diagnostic and falls back to the incumbent interpolation result.
- Follow-up command and result: focused pytest command exited 0 with 81 passed.

## Known Limitations

- Limitation: no iteration or validation evaluation was run by the Implementer role; those remain for Scorer.
- Limitation: the hypsometric diagnostic falls back conservatively for an entire column if any sigma-level geopotential or virtual temperature is nonfinite, even if an individual target could have used finite neighboring values.

## Rollback Notes

Remove `use_hypsometric_geopotential_output`, the hypsometric geopotential helper functions/constants, the `hypsometric_geopotential_output_dinosaur_dycore_model` factory/export, the registry wrapper and entry for the candidate model, and the focused tests added for this proposal. Leave the incumbent Strang model and all fixed evaluation protocols unchanged.
