# Implementation Record

## Identity

- Proposal slug: sst-sea-ice-ocean-flux-anchor
- Candidate model name: dino_obulk_sstice
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf
- Baseline commit: 329dd5758204b7e77f1abb258b1dab9ee5d9b2c8
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-22_07-54-50_sst-sea-ice-ocean-flux-anchor/implementation.md

## Implementation Summary

Added the opt-in `use_sst_sea_ice_ocean_bulk_shf_selector` flag on the Dinosaur adapter and registered the required short alias `dino_obulk_sstice`. The new factory is a `replace(...)` of the accepted ocean bulk sensible heat-flux incumbent, changing only the model name and the SST/sea-ice selector flag.

For the selector path, the adapter validates lead-zero `sea_surface_temperature` and `sea_ice_cover` from the current initialization only. When both fields are present, finite, shape-aligned, and physically valid, SST replaces the incumbent ocean thermal anchor in Dinosaur latitude order and sea ice multiplies the accepted ocean weight by `1 - sea_ice_cover`. If either selector field is missing or invalid, the adapter uses the accepted incumbent anchor and accepted ocean weighting. The accepted land mask, transfer coefficient, wind dependence, DFI exclusion, residual corrections, output contract, and step cap remain unchanged.

Added an optional SST-air departure bound in the ocean SHF forcing. It is only enabled for the validated SST/sea-ice selector trajectory, before the existing single-step cap, so incumbent and fallback trajectories keep the accepted forcing math.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "ocean_bulk_shf or sst_sea_ice" tests/dycore/test_registry.py -k "dino_obulk_sstice or sst_sea_ice_ocean_bulk"` | pass | Selected only 2 tests because the second `-k` expression overrode the first. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py -k "ocean_bulk_shf or sst_sea_ice or dino_obulk_sstice"` | pass | 13 passed, 117 deselected. |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | pass | 2 files reformatted; unrelated wrapping churn was manually removed afterward. |
| `git diff --check` | pass | No whitespace errors. |
| `uv run pytest tests/dycore/models/dinosaur tests/dycore/test_registry.py` | pass | Final run: 150 passed, 1 skipped in 137.07s. The skipped test is the WeatherBench2 integration test gated by `DYNAMAXX_RUN_WEATHERBENCH2_TESTS`. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | pass | Orchestrator rerun after import-order cleanup. |
| `uv run pytest` | pass | Orchestrator full gate: 216 passed, 2 skipped in 142.99s. |
| `uv run dynamaxx-eval fast --model dino_obulk_sstice` | not_run | Scoring gates were intentionally not run by Implementer. |
| `uv run dynamaxx-eval golden --model dino_obulk_sstice` | not_run | Golden is prohibited for this implementation phase. |

## Repair Attempts

- Failure observed: none in implementation-owned tests.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: after `ruff format`, manually removed unrelated formatting churn from pre-existing adapter and test code to keep the diff scoped to the selected proposal.
- Follow-up command and result: final `uv run pytest tests/dycore/models/dinosaur tests/dycore/test_registry.py` passed with 150 passed and 1 skipped.
- Orchestrator cleanup: adjusted import ordering in `tests/dycore/models/dinosaur/test_primitive_equations.py` after Ruff flagged the expanded import block; Ruff and full pytest passed afterward.

## Known Limitations

- Limitation: the selector requires both SST and sea-ice cover to validate before changing the accepted anchor or ocean weighting; otherwise it deliberately falls back to the accepted incumbent boundary exactly.
- Limitation: no WeatherBench2 fast, iteration, validation, or golden scoring was run by Implementer.
- Limitation: the SST and sea-ice fields are persisted lead-zero lower-boundary fields; no coupled ocean or evolving sea-ice model is introduced.

## Rollback Notes

Revert the `use_sst_sea_ice_ocean_bulk_shf_selector` adapter flag, SST/sea-ice boundary helpers, optional departure-bound plumbing, short alias factory/export/registry entry, focused tests, and this implementation record. Leave fixed evaluation protocols, leaderboard state, and unrelated history untouched.
