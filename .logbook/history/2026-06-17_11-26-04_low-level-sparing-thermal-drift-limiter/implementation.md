# Implementation Record

## Identity

- Proposal slug: low-level-sparing-thermal-drift-limiter
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
- Baseline commit: a7833574e9ade1a5271bd8cbef2fa1357465f5a8
- Candidate commit: not committed

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`
- `.logbook/history/2026-06-17_11-26-04_low-level-sparing-thermal-drift-limiter/implementation.md`

## Implementation Summary

Registered a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter`.
The factory preserves the incumbent DFI, weak Held-Suarez relaxation,
near-surface residual correction, log-pressure initialization, layer-mean
hydrostatic temperature initialization, vertical advection, horizontal
diffusion, T80 truncation, 900 s inner step, output diagnostics, and forecast
contract.

The only candidate behavior change is a positive-time rollout step filter,
enabled by `apply_upper_thermal_drift_limiter`. After the existing IMEX step
and horizontal diffusion filters, the filter copies only selected layerwise
zero-wavenumber coefficients of `temperature_variation` from the previous state
into the next state. The fixed layer mask selects sigma centers `<= 0.55` and
leaves sigma centers `> 0.55` unchanged. The filter leaves nonzero temperature
modes, vorticity, divergence, `log_surface_pressure`, tracers, `sim_time`, and
output diagnostics unchanged except through subsequent forward dynamics. It is
not included in the `filters` sequence passed to
`digital_filter_initialization`, so DFI and backward initialization use the
incumbent filter path.

Focused tests cover the factory flags, exact sigma mask, modal zero-wavenumber
copy behavior, preservation of non-temperature and nonzero-mode state leaves,
DFI isolation, registry exposure, dependency/import exposure, and a small
non-JIT finite forecast smoke test for the candidate.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Reran after import-order repair; final output: `All checks passed!`. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | `64 passed in 59.14s`. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter` | passed | Exit 0. Output reported `failed=False`, `issues=0`, `records=120`, `primary_score=-1.12481`. Raw JSON primary score: `-1.1248138532182568`; metrics path: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_upper_thermal_limiter.json`. |
| `git diff --check` | passed | Exit 0 with no output. |

## Repair Attempts

- Failure observed: first ruff run reported unsorted imports in `tests/dycore/models/dinosaur/test_primitive_equations.py`.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: moved `_unit_factor` to ruff's expected import position.
- Follow-up command and result: reran the required ruff command; it passed.

## Known Limitations

- Full `iteration`, `validation`, and `golden` evaluations were not run by the
  Implementer. Per scope, only the requested fast sanity evaluation was run.
- Candidate source/test changes are uncommitted until the Orchestrator scores
  and decides the candidate.

## Rollback Notes

If the candidate is rejected, revert only the source and test changes listed in
this implementation record. Leave this history record and raw evaluation
artifacts available for audit unless the Orchestrator explicitly requests
cleanup.
