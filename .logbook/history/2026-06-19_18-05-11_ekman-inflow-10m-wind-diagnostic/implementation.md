# Implementation Record

## Identity

- Proposal slug: ekman-inflow-10m-wind-diagnostic
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_ekman_inflow_10m_wind
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
- Baseline commit: 54375ce2994827fcc2dfe09ce0df3924cbaa6c75
- Candidate commit: uncommitted worktree on 54375ce2994827fcc2dfe09ce0df3924cbaa6c75

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-19_18-05-11_ekman-inflow-10m-wind-diagnostic/implementation.md

## Implementation Summary

Added a default-false `use_ekman_inflow_10m_wind_diagnostic` selector to
`DinosaurPrimitiveEquationsDycoreModel` and registered a side-by-side candidate
factory extending the incumbent model name with `_ekman_inflow_10m_wind`.

When enabled, output packing first computes the accepted Richardson 10 m wind
diagnostic, then applies a bounded vector adjustment toward
`-grad(log_surface_pressure)` from the forecast trajectory. The adjustment uses
the existing spherical-harmonic `cos_lat_grad` helper, a Coriolis latitude taper
that is zero through 20 degrees and full by 35 degrees, a stable-Richardson
fraction range from 0.08 to 0.16, calm/invalid no-op masks, and a fixed final
speed envelope of 0.95 to 1.03 times the Richardson diagnostic speed.

The change is output-only: trajectory dynamics, DFI, filters, time integration,
primitive-equation tendencies, output variables, and the near-surface residual
correction path are unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Syntax/import compilation check. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "ekman_inflow or surface_layer_richardson_10m_wind or richardson_10m_wind_diagnostic_only_changes_raw_surface_wind" tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py` | fail, then pass | Initial failure was a test assertion over points already parallel/antiparallel to downhill flow; after narrowing to turnable points, 14 passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 122 passed. |
| `uv run pytest` | pass | 188 passed, 2 skipped. |
| `git diff --check` | pass | No whitespace errors. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_ekman_inflow_10m_wind` | not_run | Optional fast eval was not run during implementation. |

## Repair Attempts

- Failure observed: initial focused pytest failed in `test_ekman_inflow_10m_wind_diagnostic_turns_toward_lower_pressure`.
- Implementer-owned failure: yes, the test asserted strict alignment improvement at points already exactly parallel or antiparallel to the downhill direction.
- NaN/Inf forecast observed: no.
- Fix attempted: restricted the assertion to finite extratropical points whose initial alignment was not already near +/-1.
- Follow-up command and result: reran the same focused pytest command; 14 passed.

## Known Limitations

- Fast evaluation, iteration, validation, and golden protocols were not run.
- The diagnostic intentionally no-ops for calm winds, tiny/nonfinite pressure gradients, nonfinite winds, and near-equatorial points; exact parallel or antiparallel wind/gradient alignments also receive no perpendicular turn.
- Scientific score impact is unmeasured in this implementation pass.

## Rollback Notes

Revert this experiment by removing the new adapter selector, Ekman helper,
candidate factory/export, registry entry, focused tests, and this implementation
record. Do not alter unrelated logbook history or evaluation outputs.
