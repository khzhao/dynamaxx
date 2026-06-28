# Implementation Record

## Identity

- Proposal slug: `nocturnal-cloud-longwave-blanket`
- Candidate model name: `dino_ri2m_cloud_lw`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`
- Baseline commit: `3992244f20b2a938fdd96f8904f3749f5505670d`
- Candidate commit: not committed

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

Added a side-by-side candidate, `dino_ri2m_cloud_lw`, derived from the current
RI2m incumbent. The candidate adds an opt-in
`apply_nocturnal_cloud_longwave_blanket` selector that appends a rollout-only
lower-boundary thermal step filter.

The filter uses normalized solar radiation to weight local nighttime, returns an
exact no-op when humidity is absent or invalid, computes a bounded low-cloud
proxy from lower-layer relative humidity and static stability, and applies only
positive capped warming to the lowest two sigma layers. It changes only
`temperature_variation`; vorticity, divergence, `log_surface_pressure`, tracers,
MSLP reduction, pressure-level interpolation, and final diagnostic formulas are
unchanged. Nonfinite diagnostics or corrected fields fall back to the
unmodified next state.

No changes were made to fixed evaluation protocols, metrics, target variables,
lead times, or incumbent cache artifacts.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff format ...` | 0 | Touched files formatted, per Implementer report. |
| `uv run ruff check ...` | 1 | Initial import-order failure in `test_primitive_equations.py`. |
| `uv run ruff check --fix ... && uv run ruff check ...` | 0 | Import ordering repaired, lint passed. |
| Focused pytest selection for cloud-LW tests | 0 | 18 passed, per Implementer report. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 55 passed, per Implementer report. |
| `uv run dynamaxx-eval fast --model dino_ri2m_cloud_lw` | 0 | Clean diagnostics, 120 records, primary score `-0.21716838342731634`. |
| `git diff --check` | 0 | Whitespace check passed. |

## Repair Attempts

- Failure observed: ruff import ordering only.
- Implementer-owned failure: yes, local lint ordering.
- Fix attempted: `ruff check --fix` on touched files, followed by a clean lint run.
- NaN/Inf forecast observed: no.

## Known Limitations

- The radiation reference datetime is taken from `forecast_input.initial_times[0]`
  when constructing the trajectory function, matching the current batch-level
  trajectory construction. This is side-by-side candidate behavior only.
- Full `uv run pytest` and fixed `iteration` scoring are deferred to the Scorer.
