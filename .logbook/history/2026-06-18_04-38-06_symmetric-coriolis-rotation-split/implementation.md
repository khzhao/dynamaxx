# Implementation Record

## Identity

- Proposal slug: symmetric-coriolis-rotation-split
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_split
- Baseline commit: 56bda6beec7f67abc2e42cc130ec7295cf29d32a
- Candidate commit: not committed; working tree based on 56bda6beec7f67abc2e42cc130ec7295cf29d32a

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-18_04-38-06_symmetric-coriolis-rotation-split/implementation.md

## Implementation Summary

Registered a side-by-side Strang split candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang`.
The candidate preserves the accepted Coriolis split settings and adds
`apply_symmetric_exact_coriolis_rotation_split=True`.

The rollout equation uses `angular_velocity=0.0`, builds the same SIL3
non-Coriolis step with the existing horizontal diffusion filter, then wraps that
step as exact half Coriolis rotation, non-Coriolis step, exact half Coriolis
rotation. The existing Lie split incumbent still appends the full exact rotation
as a post-step filter. DFI remains on the normal-rotation primitive equation and
normal horizontal diffusion filter for split modes.

Focused tests cover factory option preservation, registry/export availability,
finite non-JIT smoke forecasting, exact half-rotation composition, non-wind
state preservation, and the Strang rollout versus unsplit DFI setup.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `JAX_PLATFORMS=cpu uv run python -c "from dynamaxx.dycore.registry import create_dycore_model; ..."` | 0 | Focused incumbent and candidate registration/import check passed before formatting. |
| `JAX_PLATFORMS=cpu uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 73 passed in 36.11s before formatting. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | All checks passed before formatting. |
| `uv run ruff format --check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 1 | Four files needed formatting. |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Four files reformatted. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | All checks passed after formatting. |
| `uv run ruff format --check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Six files already formatted. |
| `JAX_PLATFORMS=cpu uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 73 passed in 36.03s after formatting. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-1.09659`; wrote fast JSON/CSV under `outputs/eval/`. |
| `JAX_PLATFORMS=cpu uv run python -c "from dynamaxx.dycore.registry import create_dycore_model; ..."` | 0 | Final incumbent and candidate registration/import check passed after formatting and fast sanity. |

## Repair Attempts

- Failure observed: `ruff format --check` reported four files would be reformatted.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: ran `uv run ruff format` on the four reported files.
- Follow-up command and result: reran `ruff check`, `ruff format --check`, and the focused pytest command; all passed.

## Known Limitations

- Limitation: only focused tests and the `fast` implementation sanity were run; iteration, validation, and golden protocols were not run by this Implementer pass.
- Limitation: the candidate is uncommitted, so there is no candidate commit hash yet.
- Limitation: the added symmetric split performs one extra wind transform/projection pair per inner step relative to the accepted Lie split; no performance benchmark was run beyond fast sanity.

## Rollback Notes

To revert only this experiment, remove the symmetric split field, helper, and
factory from `adapter.py`; remove the package export and registry factory/name;
remove the focused Strang tests and expected registry names; and remove this
implementation record if the history entry itself is being discarded. The fast
sanity artifacts are
`outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json`
and
`outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv`
if output cleanup is explicitly requested.
