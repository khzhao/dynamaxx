# Implementation Record

## Identity

- Proposal slug: `boundary-layer-sheltered-vertical-dse`
- Candidate model name: `dino_hsl2_mass_dse_wtg_vdse_pblcap`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Candidate commit: not committed; rejected candidates are not committed.

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

Implemented one side-by-side opt-in candidate derived from the incumbent pressure-ramped vertical-DSE dycore. The candidate adds a fixed sigma envelope that leaves upper layers at full vertical-DSE increment strength, smoothly tapers through the lower troposphere, and floors the lowest-layer increment at `0.35`. The envelope multiplies only the accepted pressure-ramped vertical-DSE increment before modal conversion, while preserving the incumbent time ramp, low-mode pressure guard, per-step Kelvin cap, WTG relaxation, forecast contract, and fixed evaluation protocols.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | `0` | Syntax check passed before and after formatting. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'boundary_layer_sheltered_vertical_dse or pressure_ramped_vertical_dse' tests/dycore/models/dinosaur/test_dependency.py -k 'boundary_layer_sheltered_vertical_dse or pressure_ramped_vertical_dse or canonical_dycore_model or imports_without_external' tests/dycore/test_registry.py -k 'boundary_layer_sheltered_vertical_dse or pressure_ramped_vertical_dse or lists_default'` | `0` | `15 passed, 177 deselected`. |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | `0` | `4 files reformatted, 3 files left unchanged`. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | `0` | All checks passed. |
| `git diff --check` | `0` | No whitespace errors. |
| `uv run pytest` | `0` | `258 passed, 2 skipped in 301.73s`. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_pblcap` | `0` | Candidate fast score `-0.22864775066430187`, failed `False`, issues `0`. |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_pblcap --workers 4` | `0` | Candidate iteration score `-0.2252107539770965`, failed `False`, issues `0`. |
| `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_pblcap --workers 4` | not_run | Iteration delta was negative and below the fixed `+0.002` promotion threshold. |

## Repair Attempts

- Failure observed: none in tests, lint, fast, or iteration.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: no repair needed after formatting.
- Follow-up command and result: full pytest and fixed fast/iteration evaluation passed without diagnostics.

## Known Limitations

- The implementation was rejected by fixed scoring and then reverted.
- Validation was intentionally not run because iteration did not promote.

## Rollback Notes

Revert the candidate source/test changes by applying the inverse of `candidate.diff`, then remove the ready research proposal from `.logbook/research/ready`. Preserve raw evaluation outputs under `outputs/eval/` and immutable history under this directory.
