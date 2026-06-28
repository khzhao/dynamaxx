# Implementation Record

## Identity

- Proposal slug: `land-ocean-lowmode-t2m-memory`
- Candidate model name: `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Candidate commit: `d1f132fafcad09bcc92cfeedbe3fc2be1b930770`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

Added a side-by-side Dinosaur candidate derived from the pressure-ramped vertical-DSE WTG incumbent. The candidate preserves the dynamics and forecast contract, then adds an output-side low-mode `2m_temperature` memory correction. The correction computes broad land and ocean means of the existing low-mode initial residual, ramps in after day 5, uses a long finite decay, caps the added correction to `1.5 K`, preserves lead zero exactly, and falls back to incumbent behavior for invalid land-sea masks or nonfinite diagnostics.

The candidate is exported through the Dinosaur package and registered as `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`. Focused tests cover factory parity, registration, late-only correction behavior, cap enforcement, non-T2m preservation, and invalid-mask fallback.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run python -m compileall -q src/dynamaxx tests` | passed | Syntax/import sanity check. |
| focused Dinosaur/registry pytest selection | passed | `14 passed, 177 deselected`. |
| `uv run ruff format ...` | passed | Reformatted touched Python files. |
| `uv run ruff check ...` | passed | No lint failures after formatting. |
| `git diff --check` | passed | No whitespace errors. |
| `uv run pytest` | passed | `257 passed, 2 skipped in 277.62s`. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem` | passed | Primary score `-0.21873176048319332`; diagnostics clean. |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem --workers 4` | passed | Primary score `-0.21638012219181893`; diagnostics clean. |
| `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem --workers 4` | passed | Primary score `-0.21606470816567627`; diagnostics clean. |

## Repair Attempts

- Failure observed: none after implementation.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: not required.
- Follow-up command and result: validation completed cleanly after iteration promotion.

## Known Limitations

- The improvement is output-side and targets only `2m_temperature`; it does not improve the prognostic trajectory directly.
- The correction is deliberately late-ramped and capped, so it leaves early T2m skill nearly unchanged.

## Rollback Notes

Reverting commit `d1f132fafcad09bcc92cfeedbe3fc2be1b930770` removes the factory, registry key, selector, low-mode memory correction helpers, and focused tests. The exact candidate patch is preserved in `candidate.diff`.
