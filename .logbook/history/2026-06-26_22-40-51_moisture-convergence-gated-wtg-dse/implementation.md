# Implementation Record

## Identity

- Proposal slug: moisture-convergence-gated-wtg-dse
- Candidate model name: dino_hsl2_mass_dse_wtg_vdse_mfcgate
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

Added a side-by-side candidate, `dino_hsl2_mass_dse_wtg_vdse_mfcgate`, derived from the accepted `dino_hsl2_mass_dse_wtg_vdse_ramp` incumbent. The new selector `use_moisture_convergence_gated_wtg` leaves the incumbent path unchanged unless enabled.

When enabled, the existing tropical WTG mass-DSE relaxation keeps its vertical envelope, low-mode mask, per-step temperature cap, relaxation fraction, and heat-neutral layer correction. It only modulates the horizontal WTG support with a bounded lower-tropospheric moisture-convergence proxy based on nodal `specific_humidity * max(-divergence, 0)`. The multiplier is normalized over the existing tropical weights so mean WTG support is preserved in the tropics. Missing humidity, nonfinite humidity, nonfinite proxy values, or degenerate proxy/weight sums fall back to the incumbent fixed WTG support.

The candidate was exported and registered without changing the incumbent registry entry.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "mfc_gate or moisture_convergence_gated_wtg"` | 0 | 6 passed, run by Implementer. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 194 passed, run by Implementer. |
| `python -m compileall -q <touched paths>` | 0 | Run by Implementer. |
| `uv run ruff check <touched files>` | 0 | Run by Implementer. |
| `uv run ruff format --check <touched files>` | 0 | Run by Implementer. |
| `git diff --check` | 0 | Run by Implementer. |
| `uv run pytest` | 0 | 260 passed, 2 skipped in 305.04s. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_mfcgate` | 0 | failed=False, issues=0, records=120, primary_score=-0.22390463383670187. |

## Repair Attempts

- Failure observed: none from final checks
- Implementer-owned failure: no unresolved failure
- NaN/Inf forecast observed: no
- Fix attempted: Implementer applied formatting and removed one unnecessary finite-diagnostic check during self-review.
- Follow-up command and result: focused and broad local tests passed after implementation.

## Known Limitations

- Limitation: The gate uses passive specific humidity as a proxy for convective support. The mechanism is deliberately bounded and opt-in but may be noisy if humidity phase errors dominate.

## Rollback Notes

Reverse-apply `candidate.diff` from this history directory and remove the ready proposal for this slug. No fixed evaluation protocol files were changed.
