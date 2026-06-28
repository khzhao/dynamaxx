# Implementation Record

## Identity

- Proposal slug: surface-layer-richardson-wind-diagnostic
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual
- Baseline commit: 5cdb5ba7bd929dc6f29eba14da306f1ce5f6eb81
- Candidate commit: 257f79d871482727b4256b624490122a84982c69

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-18_17-23-29_surface-layer-richardson-wind-diagnostic/implementation.md

## Implementation Summary

Implemented a side-by-side Dinosaur factory and registry entry for the candidate model. The incumbent factory remains unchanged. The new model preserves DFI, weak Held-Suarez relaxation, log-pressure initialization, hydrostatic layer initialization, exact Coriolis Strang splitting, and stability-aware near-surface residual decay, with one additional default-off option enabled: `use_surface_layer_richardson_10m_wind_diagnostic`.

The opt-in diagnostic changes only the raw `10m_u_component_of_wind` and `10m_v_component_of_wind` packing path inside `dinosaur_state_to_weather_state`. It computes lowest-two-layer potential temperature, lower-column bulk Richardson number, hypsometric layer separation, and a log-law-like neutral attenuation to 10 m. A bounded scalar factor in `[0.55, 1.05]` is applied equally to u and v, with no rotation. If required lower-column values are unavailable or nonfinite, the diagnostic falls back pointwise to the incumbent lowest-layer wind. The accepted residual correction still runs after diagnostic packing.

Focused tests cover candidate factory inheritance, registered model creation, import isolation, stable/neutral/unstable scalar ordering, nonfinite fallback, unchanged non-10 m wind diagnostics before residual correction, lead-zero u-wind residual exactness, and finite non-JIT forecast smoke behavior.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 87 passed in 71.24s |
| `uv run pytest` | 0 | 153 passed, 2 skipped in 79.87s |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind` | 0 | failed=False, issues=0, records=120, primary_score=-0.822515, metrics written to outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind.json |

## Repair Attempts

- Failure observed: none after implementation.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: not applicable.
- Follow-up command and result: not applicable.

## Known Limitations

- Limitation: The surface-layer height and stability correction are fixed diagnostic approximations without roughness, land/ocean, or learned coefficients; scoring must determine whether this bounded output-only transformation improves 10 m wind skill.
- Limitation: The accepted residual correction remains exactly as incumbent behavior and corrects only the channels it already corrected.

## Rollback Notes

To revert only this experiment, remove the Richardson diagnostic option/helper and candidate factory from `adapter.py`, remove its export from `src/dynamaxx/dycore/models/dinosaur/__init__.py`, remove the candidate registry wrapper and dictionary entry from `src/dynamaxx/dycore/registry.py`, and remove the associated focused tests and this implementation record. Do not alter incumbent factories, accepted residual decay code, evaluation protocols, or unrelated files.
