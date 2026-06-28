# Implementation Record

## Identity

- Proposal slug: sigma-native-hydrostatic-initialization
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sigma_hydro_init
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
- Baseline commit: 30a496b1f2ed8f894511404341c7774288bdb4c8
- Candidate commit: not created; implementation remains uncommitted in the working tree

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-18_07-30-18_sigma-native-hydrostatic-initialization/implementation.md

## Implementation Summary

Registered the side-by-side candidate
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sigma_hydro_init`
without changing the incumbent factory. The candidate preserves the Strang
Coriolis rollout, DFI settings, weak Held-Suarez forcing, log-pressure
pressure-to-sigma initialization, near-surface residual correction, output
diagnostics, sigma grid, and target-variable contract.

The adapter adds one initialization flag and a sigma-native hypsometric helper.
When geopotential is available, the existing incumbent pressure-level
hydrostatic layer-mean temperature path still produces the sigma-interpolated
fallback temperature. After the pressure-to-sigma remap, the new helper computes
adjacent sigma-center layer dry temperatures from interpolated geopotential
thickness and sigma-center pressure differences, applies bounded same-time
humidity when present, reconstructs sigma-center temperatures, enforces broad
150 K to 350 K physical bounds, and falls back pointwise to the incumbent sigma
temperature for invalid or nonfinite estimates. Vorticity, divergence,
`log_surface_pressure`, tracers, pressure-level diagnostics, and forecast output
variables are otherwise left unchanged.

Focused tests cover the analytic sigma-layer reconstruction, humidity bounding,
pointwise fallback for invalid estimates, missing-geopotential fallback,
non-temperature state preservation, candidate factory flags, registry coverage,
vendored import coverage, and a finite non-JIT smoke forecast.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `JAX_PLATFORMS=cpu uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'sigma_hydrostatic or falls_back_without_geopotential'` | 0 | New focused helper/candidate tests passed: 7 passed, 50 deselected. |
| `JAX_PLATFORMS=cpu uv run python -c "from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names; incumbent='dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang'; candidate='dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sigma_hydro_init'; names=dycore_model_names(); assert incumbent in names; assert candidate in names; assert create_dycore_model(incumbent).name == incumbent; assert create_dycore_model(candidate).name == candidate; print('registered', incumbent, candidate)"` | 0 | Required focused registration/import check passed for incumbent and candidate. |
| `JAX_PLATFORMS=cpu uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Required focused suite passed before formatting: 81 passed. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Lint passed before formatting. |
| `uv run ruff format --check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 1 | Formatting drift found in `adapter.py` and `test_primitive_equations.py`; repaired with `ruff format`. |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Reformatted 2 files, left 4 unchanged. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Final lint check passed. |
| `uv run ruff format --check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Final format check passed: 6 files already formatted. |
| `JAX_PLATFORMS=cpu uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Required focused suite rerun after formatting passed: 81 passed. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sigma_hydro_init` | 0 | Optional fast sanity completed with `failed=False`, `issues=0`, `records=120`, `primary_score=-1.10585`; metrics written to `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sigma_hydro_init.json` and `.csv`. |

## Repair Attempts

- Failure observed: `ruff format --check` reported formatting drift in `src/dynamaxx/dycore/models/dinosaur/adapter.py` and `tests/dycore/models/dinosaur/test_primitive_equations.py`.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: ran `uv run ruff format` on the changed Python files.
- Follow-up command and result: final `uv run ruff check`, final `uv run ruff format --check`, final required focused pytest suite, `git diff --check`, and optional fast sanity all passed.

## Known Limitations

- Limitation: This implementation only changes initialization. It does not tune rollout dynamics, DFI coefficients, output diagnostics, or evaluation protocols.
- Limitation: The optional fast sanity protocol was run, but iteration, validation, and golden protocols were not run by the Implementer role.
- Limitation: Candidate commit is unavailable because the Orchestrator did not request a commit.

## Rollback Notes

To revert only this experiment, remove the sigma-hydro initialization flag,
helper, factory, public export, registry entry, focused tests, and this
implementation record. If desired, also remove the optional fast sanity metrics
for this candidate from `outputs/eval/`. Do not touch incumbent factories,
leaderboard state, evaluation protocols, or unrelated output artifacts.
