# Implementation Record

## Identity

- Proposal slug: `eady-limited-baroclinic-heat-flux`
- Candidate model name: `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_eady_hfx`
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

Added a side-by-side Dinosaur candidate,
`dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_eady_hfx`, derived from the
current RI2m incumbent. The candidate adds an opt-in
`apply_eady_limited_baroclinic_heat_flux` selector that appends a rollout-only
thermal step filter after the accepted WTG and vertical-DSE thermal filters.

The filter diagnoses an extratropical Eady-style proxy from vertical wind shear,
potential-temperature vertical difference, and Coriolis magnitude. It applies a
small capped low-mode thermal increment in a free-tropospheric sigma band, then
removes the area-weighted layer mean and rescales to the predeclared per-step
temperature cap. The finite fallback returns the unmodified next state when any
diagnostic or corrected field is nonfinite.

The implementation does not add final-output postprocessing for `2m_temperature`,
`mean_sea_level_pressure`, `geopotential_500`, or winds. The incumbent registry
key and fixed evaluation protocols are unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| Focused pytest for new Eady-HFX tests | 0 | 7 passed, per Implementer report. |
| Nearby factory, registry, and filter pytest selection | 0 | 78 passed, per Implementer report. |
| `uv run python -m compileall src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py` | 0 | Compile check passed, per Implementer report. |
| `uv run ruff check ...` | 0 | Lint passed, per Implementer report. |
| `uv run ruff format ...` | 0 | Formatting passed, per Implementer report. |
| `git diff --check -- ...` | 0 | Whitespace check passed, per Implementer report. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_eady_hfx` | 0 | Clean diagnostics, 120 records, primary score `-0.21702676229647105`. |

## Repair Attempts

- Failure observed: none during implementation checks.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none needed.

## Known Limitations

- Full `uv run pytest` and fixed `iteration` scoring are deferred to the Scorer.
- The closure is deliberately conservative and may produce a weak or neutral
  metric signal if the current incumbent already captures the broad baroclinic
  thermal-gradient behavior measured by the fixed split.
