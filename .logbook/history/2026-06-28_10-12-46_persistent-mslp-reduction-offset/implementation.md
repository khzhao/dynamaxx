# Implementation Record

## Identity

- Proposal slug: persistent-mslp-reduction-offset
- Candidate model name: dino_ri2m_mslp_offset
- Incumbent model name: dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m
- Baseline commit: 3992244f20b2a938fdd96f8904f3749f5505670d
- Candidate commit: not committed

## Files Changed

- Path: `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- Path: `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- Path: `src/dynamaxx/dycore/registry.py`
- Path: `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Path: `tests/dycore/models/dinosaur/test_dependency.py`
- Path: `tests/dycore/test_registry.py`

## Implementation Summary

Added a side-by-side candidate `dino_ri2m_mslp_offset` derived from the current RI2m incumbent. The candidate introduced an opt-in `use_persistent_mslp_reduction_offset` selector that computes a same-time initial factor `mean_sea_level_pressure / surface_pressure`, clips it to `[0.75, 1.35]`, falls back to `1.0` on missing or nonfinite inputs, and applies it only to emitted `mean_sea_level_pressure` at requested leads.

The implementation left the forecast trajectory, `surface_pressure`, pressure-level fields, `geopotential_500`, `2m_temperature`, `10m_u_component_of_wind`, and fixed evaluation protocols unchanged. Factory/export/registry coverage was added for the candidate, plus focused helper and output-isolation tests.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'persistent_mslp or bulk_richardson_2m_temperature_factory or dinosaur_state_to_weather_state_matches_direct_diagnostics' tests/dycore/models/dinosaur/test_dependency.py -k 'persistent_mslp or bulk_richardson_2m_temperature_is_registered or canonical' tests/dycore/test_registry.py -k 'persistent_mslp or bulk_richardson'` | 0 | 15 passed, 191 deselected. |
| `uv run python -m compileall src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py` | 0 | Compile check passed. |
| `uv run ruff check` | 0 | Lint passed. |
| `uv run ruff format --check src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Touched files already formatted. |
| `git diff --check` | 0 | Whitespace check passed. |
| `uv run pytest` | 0 | 272 passed, 2 skipped in 283.74s. |
| `uv run dynamaxx-eval fast --model dino_ri2m_mslp_offset` | 0 | Clean diagnostics, 120 records, primary score `-0.21716794171320913`. |
| `uv run dynamaxx-eval iteration --model dino_ri2m_mslp_offset --workers 4` | 0 | Clean diagnostics, 120 records, primary score `-0.21299743637019536`. |

## Repair Attempts

- Failure observed: no implementation failure; fixed gates ran cleanly.
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none after focused verification.
- Follow-up command and result: not applicable.

## Known Limitations

- The candidate produced only numerical-noise-scale metric changes, indicating the fixed WeatherBench2 initial fields likely do not contain a useful persistent MSLP/surface-pressure ratio signal for this incumbent.

## Rollback Notes

Revert only the six candidate source/test files:

```bash
git restore -- \
  src/dynamaxx/dycore/models/dinosaur/__init__.py \
  src/dynamaxx/dycore/models/dinosaur/adapter.py \
  src/dynamaxx/dycore/registry.py \
  tests/dycore/models/dinosaur/test_dependency.py \
  tests/dycore/models/dinosaur/test_primitive_equations.py \
  tests/dycore/test_registry.py
```
