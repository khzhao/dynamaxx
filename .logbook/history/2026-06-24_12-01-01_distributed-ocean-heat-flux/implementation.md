# Implementation Record

## Identity

- Proposal slug: distributed-ocean-heat-flux
- Candidate model name: dino_hsl2_mass_dse_ocean_flux_taper
- Incumbent model name: dino_hsl2_mass_dse
- Baseline commit: 2c70bb5b77370a074330c2b46954f74f20771f12
- Candidate commit: unavailable

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-24_12-01-01_distributed-ocean-heat-flux/implementation.md

## Implementation Summary

Implemented one side-by-side candidate,
`dino_hsl2_mass_dse_ocean_flux_taper`, derived from
`dino_hsl2_mass_dse`. The accepted ocean bulk sensible heat-flux law, ocean
mask, temperature anchor, exchange coefficient, exchange-depth cap, per-step
heat cap, DFI behavior, weak-HS forcing, HSL/DSE transport, residuals, outputs,
and forecast API remain unchanged.

The new candidate opts into `use_distributed_ocean_bulk_sensible_heat_flux_taper`.
When enabled, the already capped signed lowest-layer ocean heat tendency is
redistributed over fixed nonnegative lower-sigma taper weights for layers with
sigma centers at or above 0.75. The distribution is normalized by sigma-layer
pressure thickness so the pressure-weighted column temperature tendency matches
the incumbent lowest-layer-only column increment. If taper weights, pressure
thickness, normalization, or distributed tendencies are nonfinite or unusable,
the forcing falls back to the incumbent lowest-layer-only tendency.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Import-order issue repaired, then passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "ocean_bulk or ocean_flux_taper or mass_dse"` | passed | 15 passed, 116 deselected. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | 47 passed. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_ocean_flux_taper` | passed | failed=False, issues=0, records=120, primary_score=-0.282013, metrics=outputs/eval/fast_dino_hsl2_mass_dse_ocean_flux_taper.json. |

## Repair Attempts

- Failure observed: Ruff reported unsorted imports in `tests/dycore/models/dinosaur/test_primitive_equations.py`.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: reordered the new `_ocean_bulk_*` import to match project import sorting.
- Follow-up command and result: reran the requested Ruff command; passed.

## Known Limitations

- Limitation: The taper is fixed and not stability-, wind-, or PBL-depth-aware.
- Limitation: Only the fast protocol was run locally; iteration and validation scoring are left for the Scorer.
- Limitation: No candidate commit exists because the Implementer was instructed not to commit.

## Rollback Notes

Revert only this experiment by removing the taper selector, taper helper,
`ocean_flux_taper_dinosaur_dycore_model()` factory/export, registry key
`dino_hsl2_mass_dse_ocean_flux_taper`, the focused taper tests, and this
implementation record. Do not remove unrelated untracked files such as `gifs/`.
