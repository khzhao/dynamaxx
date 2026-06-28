# Implementation Record

## Identity

- Proposal slug: mass-conserving-logp-spectral-smoother
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
- Baseline commit: c359ee1b016ccd92412585997a799a7c644a65c5
- Candidate commit: not available; implementation is uncommitted on HEAD 8ead91209dfbd2abc3ffc31082653cf29aa962dd

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-19_03-32-34_mass-conserving-logp-spectral-smoother/implementation.md

## Implementation Summary

Registered the side-by-side log-surface-pressure spectral smoother candidate while preserving the incumbent factory and behavior unchanged. The new rollout-only filter applies a fixed total-wavenumber taper to `log_surface_pressure`: modes with `n <= 10` are unchanged by the taper, modes transition smoothly through `10 < n < 20`, and modes with `n >= 20` are fully damped before mass correction. The filter converts the smoothed log pressure to nodal surface pressure, applies one scalar log-pressure offset so the area-weighted mean surface pressure matches the pre-filter state, caps local surface-pressure changes to `0.25%`, converts back to modal form, and falls back to the incumbent next state if any finite, positivity, modal-conversion, or reconstructed-cap check fails.

The filter is appended only to positive-time rollout filters after theta layer-mean recentering. Digital-filter initialization keeps the incumbent DFI filter set and does not receive the pressure smoother. Vorticity, divergence, temperature variation, tracers, and `sim_time` are copied from the incumbent next state.

Tests cover the modal taper, mass preservation when the cap is inactive, local cap enforcement, nonfinite fallback, preservation of non-pressure state fields, DFI exclusion, registry exposure, package export, and a finite non-JIT smoke forecast.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Two files reformatted; four unchanged. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | `112 passed` in 93.20s. |
| `uv run pytest` | 0 | `178 passed, 2 skipped` in 100.09s. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.7989254063123296`; metrics at `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother.json`. |

## Repair Attempts

- Failure observed: none.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: not applicable.
- Follow-up command and result: not applicable.

## Known Limitations

- Limitation: The scalar mass offset exactly preserves area-weighted surface-pressure mass before local capping. If the local `0.25%` cap activates, final mass may differ slightly because the proposal requires the cap after mass correction.
- Limitation: A final reconstructed-pressure cap check can reject the smoothed modal state and fall back to the incumbent next state when modal projection would violate the local cap.
- Limitation: Iteration, validation, and golden protocols were intentionally not run by the Implementer role.

## Rollback Notes

If rejected, revert only the six tracked implementation files listed above. The ignored fast-eval output under `outputs/eval/` and this logbook record can remain as experiment history unless the Orchestrator explicitly requests cleanup.
