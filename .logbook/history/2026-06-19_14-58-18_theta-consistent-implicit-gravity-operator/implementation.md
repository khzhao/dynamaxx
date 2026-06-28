# Implementation: theta-consistent implicit gravity operator

## Commits

- Baseline commit: `54375ce2994827fcc2dfe09ce0df3924cbaa6c75`
- Candidate commit: uncommitted worktree at current HEAD `54375ce2994827fcc2dfe09ce0df3924cbaa6c75`

## Candidate

- Candidate slug: `theta-consistent-implicit-gravity-operator`
- Candidate model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_theta_implicit`
- Incumbent model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`
- `.logbook/history/2026-06-19_14-58-18_theta-consistent-implicit-gravity-operator/implementation.md`

## Implementation Summary

- Added `implicit_thermodynamic_variable`, defaulting to the incumbent temperature-form semi-implicit operator.
- Added an opt-in potential-temperature implicit thermal/gravity operator for sigma coordinates. It builds a fixed reference Exner profile from sigma centers, forms reference theta, uses the theta vertical-transport weights with the dry compressional term removed, and scales the resulting theta tendency back to `temperature_variation` storage.
- Used the same selected thermal weights in `implicit_terms`, `_get_implicit_term_matrix_sigma`, and the blockwise inverse path.
- Kept finite fallbacks to the incumbent temperature-form weights for invalid reference Exner/theta weights, and guarded the theta inverse matrix with a finite inverse check.
- Registered the side-by-side candidate factory while preserving all incumbent DFI, weak-HS, initialization, Coriolis split, theta explicit tendency, theta mean recentering, SIL3 off-centering, filtering, output, and forecast behavior.

## Tests And Checks

- PASS: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
  - Result: `118 passed in 98.90s`
- PASS: `uv run pytest`
  - Result: `184 passed, 2 skipped in 106.19s`
- PASS: `git diff --check`

## Repair Attempts

- No repair loop was needed after the first focused run; focused tests and full tests passed.

## Known Limitations

- Fast eval was not run; iteration, validation, and golden were not run.
- The finite matrix-inverse guard falls back to the temperature-form inverse if the theta matrix is invalid. The representative unit and non-JIT smoke forecast cases stayed finite.
- No committed candidate hash exists because this implementation was left uncommitted as requested.
