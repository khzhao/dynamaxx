# Implementation: surface-layer-diagnostic-extrapolation

## Summary

Implemented `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_surface_diag` as a side-by-side Dinosaur adapter model. The candidate adds one output-only flag, `use_surface_layer_diagnostic_extrapolation`, that diagnoses only `2m_temperature` and `10m_u_component_of_wind` from the lowest two sigma layers before the existing near-surface residual correction is applied.

The diagnostic estimates lowest-layer heights with a dry isothermal hypsometric approximation using local surface pressure, sigma centers, lowest-layer temperature, `physics_specs.R`, and `physics_specs.g`. Extrapolated increments are bounded by the magnitude of the lowest-layer vertical difference. Pressure-level outputs, `geopotential_500`, MSLP, surface pressure, humidity, 10 m V wind, trajectory integration, DFI, weak Held-Suarez forcing, log-pressure initialization, layer-mean hydrostatic temperature initialization, vertical advection, T80 truncation, 900 s inner step, and fixed evaluation protocols are unchanged.

## Commits

- Baseline commit: `a7833574e9ade1a5271bd8cbef2fa1357465f5a8`
- Candidate commit: `not committed`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`
- `.logbook/history/2026-06-17_13-35-18_surface-layer-diagnostic-extrapolation/implementation.md`

## Tests And Commands

- `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
  - Exit status: `0`
  - Result: `All checks passed!`
- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
  - Exit status: `0`
  - Result: `63 passed in 57.07s`
- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_surface_diag`
  - Exit status: `0`
  - Result: `failed=False`, `issues=0`, `records=120`
  - Primary score: `-1.2277670451193914`
  - Metrics JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_surface_diag.json`
- `git diff --check`
  - Exit status: `0`

## Repair Attempts

- The first Ruff run failed due to import ordering in `tests/dycore/models/dinosaur/test_primitive_equations.py`.
- Reordered the new import and reran Ruff successfully.

## Known Limitations

- The height estimate is intentionally simple: dry, isothermal, and based on the lowest-layer temperature. It does not include roughness length, stability functions, land-surface state, or moist virtual temperature.
- The diagnostic is bounded and output-only, so it cannot correct dynamical low-level wind or thermal drift in the forecast trajectory.
- No iteration, validation, golden evaluation, leaderboard update, or commit was performed by the Implementer role.

## Rollback Notes

If rejected, revert only the source and test changes listed above. The candidate is isolated behind `use_surface_layer_diagnostic_extrapolation` and the registry key `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_surface_diag`; removing that factory, export, registry entry, helper usage, and focused tests restores the incumbent behavior. Raw fast artifacts under `outputs/eval/` were produced for sanity checking and should only be removed if the Orchestrator explicitly requests artifact cleanup.
