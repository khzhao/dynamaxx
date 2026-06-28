# Implementation Record

## Identity

- Proposal slug: pressure-ramped-vertical-dse-wtg
- Candidate model name: dino_hsl2_mass_dse_wtg_vdse_ramp
- Incumbent model name: dino_hsl2_mass_dse_wtg
- Baseline commit: d8561caebb78ca096263d8c412217570ff2d1f46
- Candidate commit: ff40def55ac707e8915c840b856a0aaa3345b046

## Files Changed

- src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- src/dynamaxx/dycore/models/dinosaur/adapter.py
- src/dynamaxx/dycore/models/dinosaur/__init__.py
- src/dynamaxx/dycore/registry.py
- tests/dycore/models/dinosaur/test_dependency.py
- tests/dycore/models/dinosaur/test_primitive_equations.py
- tests/dycore/test_registry.py

## Implementation Summary

Registered `dino_hsl2_mass_dse_wtg_vdse_ramp` side by side with the WTG
incumbent. The candidate preserves the accepted mass-DSE HSL transport and
rollout WTG filter, then opts into a guarded vertical-DSE thermal increment in
the potential-temperature tendency path.

The increment is computed as the DSE vertical thermal tendency minus the
accepted theta-derived vertical thermal tendency. It is multiplied by a fixed
smooth forecast-time ramp that is zero through 24 forecast hours and reaches
full strength at 72 forecast hours. During spinup the broad layerwise low-mode
component is removed, the final increment is capped to a fixed per-inner-step
temperature tendency, and nonfinite or invalid diagnostics fall back to the
incumbent WTG tendency.

Candidate-specific `sim_time` initialization was added without changing the
external forecast contract. The incumbent keeps `sim_time=None` and the new
selector disabled.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -q -k "pressure_ramped_vertical_dse or initializes_sim_time or tropical_wtg_factory" tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | `10 passed, 176 deselected in 45.04s`. |
| `uv run pytest` | 0 | `252 passed, 2 skipped in 275.58s`. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp` | not_run | Reserved for Scorer. |

## Repair Attempts

- Failure observed: initial targeted test used `(250, 750)` hPa pressure levels
  with a structured fixture containing `(100, 500, 900)` hPa channels.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: changed the focused `sim_time` initialization test to use the
  fixture's actual pressure levels.
- Follow-up command and result: targeted test command passed with
  `10 passed, 176 deselected`.

## Known Limitations

- The candidate intentionally delays vertical-DSE influence until after day 1,
  so it may lose much of the prior unrestricted vertical-DSE aggregate gain.
- The fixed broad-mode spinup guard and cap are conservative protocol constants,
  not validation-tuned parameters.

## Rollback Notes

If rejected, revert the source/test diff captured in `candidate.diff`, remove
the ready proposal copy from `.logbook/research/ready`, leave raw evaluation
outputs for reproducibility, and do not update `.logbook/leaderboard.json`.
