# Implementation Record

## Identity

- Proposal slug: mass-centered-dse-anomaly-hsl
- Candidate model name: dino_hsl2_mass_dse_wtg_vdse_ramp_masscenter
- Incumbent model name: dino_hsl2_mass_dse_wtg_vdse_ramp
- Baseline commit: ff40def55ac707e8915c840b856a0aaa3345b046
- Candidate commit: not committed before scoring

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented a side-by-side registered candidate,
`dino_hsl2_mass_dse_wtg_vdse_ramp_masscenter`, derived from the accepted
pressure-ramped vertical-DSE WTG incumbent. The candidate adds the opt-in
selector `use_mass_centered_dse_hsl_anomaly`.

Only inside the selected layer-mass-weighted horizontal DSE HSL branch, the
candidate forms the transported scalar as
`layer_pressure_thickness * (dry_static_energy - mass_centered_reference)`,
implemented equivalently by subtracting the pressure-thickness-and-area-weighted
mean from the existing layerwise area-centered DSE anomaly before multiplying
by layer pressure thickness. The existing incumbent mass-DSE HSL tendency is
computed first and is retained as the exact fallback if the mass-centered
weights, centered scalar, remap outputs, divided layer tendency, or converted
temperature tendency are nonfinite.

The unweighted DSE path and the accepted pressure-ramped vertical-DSE increment
continue to receive the original `nodal_dry_static_energy_anomaly`; the
candidate does not change WTG, vertical-DSE timing/caps, pressure work, residual
correction, output variables, forecast contract, metrics, splits, or protocols.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | ---: | --- |
| `python -m compileall ...` | 0 | Implementer syntax check over changed modules/tests. |
| `uv run ruff format --check ...` | 0 | Passed after applying formatter during implementation. |
| `uv run ruff check ...` | 0 | Lint clean. |
| targeted new tests | 0 | 8 passed in 50.86s. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Focused suite passed: 195 passed in 299.69s. |
| `uv run pytest` | 0 | Full suite passed: 261 passed, 2 skipped in 309.87s. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_masscenter` | 0 | Fast artifact verified: primary score -0.2237799449232893, diagnostics failed false, issue count 0, 120 metric rows. |
| `uv run python - <<'PY' ... registry.dycore_model_names/create_dycore_model ... PY` | 0 | Orchestrator verified candidate and incumbent registration/construction. |
| `git diff --check` | 0 | Orchestrator verified no whitespace errors. |

## Repair Attempts

- Failure observed: two new focused tests initially used full nondimensional DSE/pressure magnitudes with overly strict absolute tolerances.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: rewrote those tests to use small synthetic scalar fields while preserving the intended zero layer-mass-integral and uniform-pressure-equivalence checks.
- Follow-up command and result: targeted tests, focused suite, full pytest, fast eval, registry check, and diff check all passed.

## Known Limitations

- No iteration or validation evaluation had been run before this record.
- The candidate tests the scalar reference only inside the mass-DSE HSL branch; it does not address pressure-thickness tendency coupling, finite-volume remap replacement, or vertical-DSE scheduling.
- Fast score was slightly worse than the incumbent neighborhood, but fast is a sanity gate only. Fixed iteration scoring decides promotion.

## Rollback Notes

If rejected, apply the reverse of `candidate.diff` from this history directory
to revert only the source/test changes from this experiment. Preserve raw
evaluation outputs and this immutable history directory. The pre-existing
untracked `gifs/` directory is unrelated and must not be removed.
