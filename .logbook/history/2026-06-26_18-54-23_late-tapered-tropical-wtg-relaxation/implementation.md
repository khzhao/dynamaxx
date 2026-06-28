# Implementation Record

## Identity

- Proposal slug: late-tapered-tropical-wtg-relaxation
- Candidate model name: dino_hsl2_mass_dse_wtg_vdse_wtg_taper
- Incumbent model name: dino_hsl2_mass_dse_wtg_vdse_ramp
- Baseline commit: ff40def55ac707e8915c840b856a0aaa3345b046
- Candidate commit: uncommitted working tree based on ff40def55ac707e8915c840b856a0aaa3345b046

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Added an opt-in late-lead taper for the incumbent tropical WTG mass-DSE relaxation. The new selector `apply_late_tropical_wtg_taper` leaves the incumbent filter exactly unchanged unless enabled by the candidate factory.

For `dino_hsl2_mass_dse_wtg_vdse_wtg_taper`, the existing WTG relaxation fraction remains at full strength through 120 forecast hours, then uses a smoothstep schedule to reach 70 percent strength by 240 forecast hours and stays there afterward. Missing, nonfinite, or negative `sim_time` falls back to a multiplier of 1.0 so the filter matches incumbent behavior. The WTG latitude envelope, sigma envelope, low-mode mask, temperature cap, and mass-neutral heat offset are unchanged.

The candidate is registered side by side with the incumbent as `dino_hsl2_mass_dse_wtg_vdse_wtg_taper`.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | Completed before full gate. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | No lint issues. |
| `uv run ruff format --check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Six files already formatted. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run pytest` | 0 | 261 passed, 2 skipped in 305.08s. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_wtg_taper` | 0 | failed=False, issues=0, records=120, primary_score=-0.22392494621838646. |

## Repair Attempts

- Failure observed: none
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none
- Follow-up command and result: none

## Known Limitations

- Limitation: The taper constants are a single fixed hypothesis, not a sweep. The fixed evaluation protocol is unchanged.

## Rollback Notes

Reverse-apply `candidate.diff` from this history directory and remove the ready proposal for this slug. No fixed evaluation protocol files were changed.
