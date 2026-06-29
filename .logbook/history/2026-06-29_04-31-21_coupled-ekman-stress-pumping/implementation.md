# Implementation Record

## Identity

- Proposal slug: `coupled-ekman-stress-pumping`
- Candidate model name: `dino_ri2m_ekman_coupled`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`
- Baseline commit: `7f4a314196fa4893939efa071bb686eda9f3669b`
- Candidate commit: not committed; candidate is pending full scoring.

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

Implemented one side-by-side Dinosaur adapter candidate derived from the accepted RI2m incumbent. The candidate adds a default-false `apply_coupled_ekman_surface_closure` selector and registers `dino_ri2m_ekman_coupled`.

The candidate adds a rollout-only lower-boundary step filter after the existing spectral and WTG filters. The filter diagnoses the lowest-layer wind and pressure, applies a weak bounded bulk-stress momentum increment over the lowest two sigma layers, removes the area-weighted zonal acceleration mean, derives a pressure tendency proxy from the same applied stress field with a smooth equatorial taper, removes the area-weighted log-pressure tendency mean, and enforces stress-tied caps. Temperature, tracers, WTG heating, pressure-ramped vertical-DSE, low-mode T2m memory, RI2m 2 m temperature diagnostics, output diagnostics, fixed metrics, splits, and target variables are unchanged directly.

The implementation adds finite fallback to the incumbent no-op path if any stress, pressure, transform, cap, or corrected-state diagnostic is invalid. A bounded repair changed the momentum update to add only modal wind increments to the existing vorticity/divergence state instead of reprojecting the full background wind field; this preserves the incumbent background flow and avoids transform round-trip drift. A conservative projection safety factor keeps realized component increments below the declared per-step wind cap after spherical-harmonic projection.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run python -m py_compile src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Compile check passed after bounded repair. |
| `git diff --check` | passed | No whitespace errors. |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | One file reformatted, then six files left unchanged on rerun. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | All checks passed after removing two unused variables. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'ekman_coupled' tests/dycore/models/dinosaur/test_dependency.py -k 'ekman_coupled or canonical' tests/dycore/test_registry.py -k 'ekman_coupled or lists_default'` | passed | `9 passed, 198 deselected in 10.33s`. |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_coupled` | passed | `primary_score=-0.16771830165614882`, `failed=false`, zero issues, artifacts `outputs/eval/fast_dino_ri2m_ekman_coupled.json/.csv`. |

## Repair Attempts

- Implementer subagent stalled after a partial patch; main agent continued the Implementer role.
- First focused pytest run failed because the synthetic high-wind cap test exposed spherical-harmonic projection drift when the filter reprojected the entire background wind field.
- Bounded repair: convert only the bounded wind increment to modal vorticity/divergence and add that modal increment to the incumbent state.
- Second focused pytest run failed by a small cap overshoot after final vector projection.
- Bounded repair: neutralize the projected zonal increment and apply a conservative internal projection safety factor so the realized projected increment remains below the declared physical cap.
- Lint then found two unused variables left after the modal-increment repair; they were removed.
- Follow-up focused tests, lint, compile, and fast evaluation passed.

## Known Limitations

- The closure is deliberately weak and uses fixed predeclared constants: no coefficient sweep or validation tuning was performed.
- The pressure-pumping proxy is reduced and diagnostic; it is not a full boundary-layer turbulence or Monin-Obukhov scheme.
- The filter uses a global projection safety factor to keep post-transform wind increments below the declared cap.
- Fast evaluation passed with a large positive sanity signal, but full pytest and iteration/validation gates have not yet been run.

## Rollback Notes

The exact candidate source/test patch was saved as `.logbook/history/2026-06-29_04-31-21_coupled-ekman-stress-pumping/candidate.diff`. If rejected, revert it with `git apply -R` against that patch and leave `.logbook/history`, `outputs/eval`, and the pre-existing untracked `gifs/` directory intact.
