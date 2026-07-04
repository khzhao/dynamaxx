# Implementation Record

## Candidate

- Proposal slug: `terrain-work-form-drag-heating`
- Candidate model: `dino_ri2m_ekman_depth_orolift_lwind_twork_drag`
- Incumbent model: `dino_ri2m_ekman_depth_orolift_lwind`
- Baseline HEAD: `6c53d6d519dc1e092f5197558ebc099aeacfd31b`
- Candidate commit: `8f0b4f529d29d372341e136bd11cbe2f21542bc2`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Summary

Added a default-off selector, `apply_terrain_work_form_drag_heating`, and
registered `dino_ri2m_ekman_depth_orolift_lwind_twork_drag` as a side-by-side
candidate extending the accepted depth-weighted orographic-lift incumbent.

The implementation adds a positive-time post-step filter that reuses the
incumbent terrain-lift path: smoothed terrain, terrain gradient, equatorial
taper, lower-column weighted wind, and terrain-work proxy. Where terrain-work
and slope diagnostics are active, the filter applies a conservative anti-flow
lower-column momentum decrement, projects it back through the
vorticity/divergence path, and returns a small capped, layerwise area-neutral
heat increment from the diagnosed kinetic-energy loss.

The filter preserves `log_surface_pressure`, tracers, `sim_time`, forecast
inputs/outputs, fixed evaluation protocols, and the accepted Ekman/orographic
selectors. Invalid terrain, wind, projection, or heating diagnostics fall back
to the incumbent next state.

## Tests And Checks

- `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py`: passed; no files changed.
- `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py`: passed.
- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`: passed, `237 passed in 291.48s`.
- `uv run pytest`: passed, `303 passed, 2 skipped in 301.34s`.
- `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag`: passed, `failed=false`, issues `0`, records `120`, primary score `-0.12743232368039709`.

## Saved Patch

- `.logbook/history/2026-07-04_04-57-16_terrain-work-form-drag-heating/candidate.diff`

## Known Limitations

- No incumbent, iteration, validation, or golden evaluation was run during
  implementation.
- The form-drag strength uses fixed conservative caps rather than a diagnosed
  subgrid orographic standard deviation or Froude-number blocking depth. This
  keeps the experiment within the selected proposal and avoids new static-data
  infrastructure.
- The Implementer subagent was closed after writing the source/test patch but
  before completing artifacts; the main Orchestrator completed formatting,
  tests, fast sanity evaluation, and history records.
- Pre-existing untracked `gifs/` remains untouched.
