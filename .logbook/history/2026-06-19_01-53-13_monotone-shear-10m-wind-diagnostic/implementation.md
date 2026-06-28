# Implementation Record

## Identity

- Proposal slug: monotone-shear-10m-wind-diagnostic
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_monotone_10m_wind
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter
- Baseline commit: c359ee1b016ccd92412585997a799a7c644a65c5
- Candidate commit: not available; Implementer did not commit changes
- Current HEAD observed during final checks: 8ead91209dfbd2abc3ffc31082653cf29aa962dd

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-19_01-53-13_monotone-shear-10m-wind-diagnostic/implementation.md

## Implementation Summary

Implemented a side-by-side Dinosaur candidate that preserves the incumbent theta-recenter dycore and adds only an opt-in monotone 10 m wind diagnostic selector. The candidate computes the existing Richardson 10 m wind diagnostic first, then applies a scalar speed limiter to that vector: stable and neutral lower columns are capped at `1.00 * lowest_speed`, while unstable lower columns are capped at `1.02 * lowest_speed`. The limiter preserves vector direction and falls back locally to the raw lowest-layer wind when required diagnostics or corrected winds are nonfinite.

The fixed forecast API, output variables, target variables, WeatherBench2 protocols, residual decay, theta recentering, thermodynamic tendency, initialization, and non-wind outputs were left unchanged. The incumbent factory and registered incumbent name are unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Syntax check passed after final repair. |
| `uv run python - <<'PY' ... create_dycore_model(candidate) ... PY` | 0 | Direct package export and registry creation sanity check passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 1 | First run failed in the dependency subprocess because the candidate package export was missing after local file drift. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | `110 passed` after restoring the export and candidate changes. |
| `uv run pytest` | 0 | `176 passed, 2 skipped`. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_monotone_10m_wind` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.7990725366440742`; metrics JSON written under `outputs/eval/`. |
| `git diff --check` | 0 | No whitespace errors. |

## Repair Attempts

- Failure observed: focused pytest first failed in `test_dinosaur_imports_without_external_dinosaur_package` with an `AttributeError` for `monotone_10m_wind_dinosaur_dycore_model`.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: restored the candidate package export and verified the adapter factory, registry entry, and tests were present after detecting local file drift.
- Follow-up command and result: focused pytest rerun passed with `110 passed`; full pytest passed with `176 passed, 2 skipped`; fast eval passed with clean diagnostics.

## Known Limitations

- The limiter is intentionally output-diagnostic only and is applied before the existing near-surface residual correction, preserving residual decay behavior as requested.
- The existing Richardson factor already satisfies the monotone envelope in many synthetic columns, so this candidate may produce small score movement if late 10 m wind error is dominated by residual or phase error rather than diagnostic speed overshoot.
- No iteration, validation, or golden evaluation was run by the Implementer.

## Rollback Notes

If the Orchestrator rejects this candidate, revert only the six implementation files listed above with `git restore -- src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`. The logbook record and raw `outputs/eval/fast_*monotone_10m_wind.*` artifacts should be retained unless the Orchestrator explicitly requests cleanup.
