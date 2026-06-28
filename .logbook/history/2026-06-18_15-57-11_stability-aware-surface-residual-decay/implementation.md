# Implementation Record

## Identity

- Proposal slug: stability-aware-surface-residual-decay
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
- Baseline commit: 30a496b1f2ed8f894511404341c7774288bdb4c8
- Candidate commit: 5cdb5ba7bd929dc6f29eba14da306f1ce5f6eb81

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-18_15-57-11_stability-aware-surface-residual-decay/implementation.md

## Implementation Summary

Registered a side-by-side candidate that preserves the incumbent DFI, weak-HS relaxation, log-pressure initialization, hydrostatic layer initialization, symmetric exact-Coriolis split, forecast API, lead structure, and output variables.

The only enabled behavior change is a default-off stability-aware near-surface residual decay option. The existing residual channels, `2m_temperature` and `10m_u_component_of_wind`, still use the lead-zero model-minus-analysis residual and still force lead zero to exactly match the analyzed near-surface channels when present.

When pressure-level lower-column output is available, the decay uses the lowest two common temperature/u-wind pressure levels and optional v-wind shear to compute a bounded potential-temperature stability score. Stable weak-shear columns retain residuals longer, unstable or strongly mixed columns decay faster, and neutral columns use the incumbent 48 hour baseline. The resulting local timescale is clipped to fixed predeclared bounds of 18 to 72 hours. If lower-column output is unavailable, the helper falls back to a deterministic near-surface residual decoupling proxy using only the lead-zero raw forecast and initial residual information already available in the correction path.

Pressure-level variables, mean sea level pressure, geopotential, and all uncorrected channels remain unchanged by the correction helper.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 80 passed in 66.35s before the logbook write; rerun after final formatting also passed, 80 passed in 65.99s. |
| `uv run pytest` | 0 | 146 passed, 2 skipped in 73.47s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-1.07491`; metrics written to `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual.json`. |

## Repair Attempts

- Failure observed: none.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none required.
- Follow-up command and result: not applicable.

## Known Limitations

- Limitation: The primary stability proxy depends on the lowest two emitted pressure levels, which are coarse substitutes for a true surface-layer Richardson number because the adapter does not expose skin temperature, roughness, turbulent fluxes, or model-level boundary-layer diagnostics in the output correction path.
- Limitation: When a caller requests only near-surface output channels, the fallback proxy cannot diagnose true vertical stability and instead uses bounded lead-zero residual decoupling information.

## Rollback Notes

Remove the stability-aware residual option and helper functions from `src/dynamaxx/dycore/models/dinosaur/adapter.py`, remove the side-by-side factory export from `src/dynamaxx/dycore/models/dinosaur/__init__.py`, remove the registry factory and model-name entry from `src/dynamaxx/dycore/registry.py`, and delete the focused tests added for the candidate in the three touched test files. Do not change the incumbent Strang factory or any fixed evaluation protocol.
