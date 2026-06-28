# Implementation Record

## Identity

- Proposal slug: `bulk-richardson-2m-temperature-diagnostic`
- Candidate model name: `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`
- Baseline commit: `d1f132fafcad09bcc92cfeedbe3fc2be1b930770`
- Candidate commit: `3992244f20b2a938fdd96f8904f3749f5505670d`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

Added a side-by-side Dinosaur candidate derived from `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`. The candidate preserves the accepted HSL, WTG, vertical-DSE ramp, and land/ocean low-mode T2m memory paths, then changes only the raw packed `2m_temperature` diagnostic before residual correction.

The diagnostic uses the lowest two sigma-layer temperatures, local sigma pressures, lower-column wind shear, and a bounded bulk-Richardson-style stability limiter to extrapolate a screen-level potential temperature. The final raw diagnostic is capped to `+/-1.5 K` from the incumbent lowest-layer temperature and falls back to the incumbent raw temperature for invalid or nonfinite columns. Non-T2m fields and the forecast trajectory remain unchanged.

The candidate is exported through the Dinosaur package and registered as `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`. Focused tests cover factory parity, stable/neutral/unstable behavior, cap enforcement, invalid fallback, raw non-T2m invariance, and lead-zero residual exactness.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Final focused run reported `199 passed`. |
| `uv run python -m compileall -q src/dynamaxx tests` | passed | Syntax/import sanity check. |
| `uv run ruff format ...` | passed | Reformatted touched Python files. |
| `uv run ruff check ...` | passed | No lint failures. |
| `git diff --check` | passed | No whitespace errors. |
| `uv run pytest` | passed | `265 passed, 2 skipped in 282.23s`. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m` | passed | Primary score `-0.21716702092934806`; diagnostics clean. |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m --workers 4` | passed | Primary score `-0.21299732605547173`; diagnostics clean. |
| `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m --workers 4` | passed | Primary score `-0.21274255459898536`; diagnostics clean. |

## Repair Attempts

- Failure observed: none after implementation.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: not required.
- Follow-up command and result: full tests, fast, iteration, and validation completed cleanly.

## Known Limitations

- The improvement is output-side and targets only the raw screen-temperature diagnostic; it does not change the prognostic trajectory.
- The diagnostic is a bounded surface-layer surrogate, not a full Monin-Obukhov or land-surface model.

## Rollback Notes

Reverting commit `3992244f20b2a938fdd96f8904f3749f5505670d` removes the selector, raw T2m diagnostic helper, factory/export, registry key, and focused tests. The exact candidate patch is preserved in `candidate.diff`.
