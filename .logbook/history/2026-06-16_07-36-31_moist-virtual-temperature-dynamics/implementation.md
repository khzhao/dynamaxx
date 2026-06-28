# Implementation Record

## Identity

- Proposal slug: moist-virtual-temperature-dynamics
- Candidate model name: dinosaur_moist
- Incumbent model name: dinosaur
- Baseline commit: 3f517232303e37bc947361cb29c214b13b249438
- Candidate commit: uncommitted implementation diff on baseline commit

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/test_registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py

## Implementation Summary

The implementation registered a side-by-side `dinosaur_moist` candidate so the incumbent `dinosaur` could remain unchanged for direct comparison. The candidate factory returned `DinosaurPrimitiveEquationsDycoreModel(name="dinosaur_moist", use_humidity_in_dynamics=True)`, enabling the adapter's existing moist primitive-equation branch only when a complete pressure-level specific-humidity stack was present.

Focused tests confirmed that `dinosaur` retained dry dynamics, `dinosaur_moist` enabled humidity feedbacks, and incomplete humidity inputs fell back to the dry equation path.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py` | 0 | 21 passed. |
| `uv run pytest` | 0 | 87 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_moist` | 0 | Process exited 0, but fixed diagnostics failed with `nonfinite_forecast`; primary score recorded as `-1.7976931348623157e+308` in `scores.json`. |
| `git diff --check` | 0 | No whitespace errors. |

## Repair Attempts

- Failure observed: fixed fast diagnostics reported `nonfinite_forecast` with value `4713420`.
- Implementer-owned failure: no bounded source fix was attempted because the candidate was the intended small registry/factory change and the nonfinite lower-pressure-level pattern was also observed in a one-start dry incumbent diagnostic.
- NaN/Inf forecast observed: yes.
- Fix attempted: none within this candidate scope.
- Follow-up command and result: Scorer verified the failed fast artifact and did not run iteration or validation.

## Known Limitations

- The candidate did not pass the required fast diagnostic gate, so iteration and validation were not run.
- The WeatherBench2 fast artifact contains finite metric rows but diagnostic failure is authoritative under the protocol.
- Any lower-level pressure interpolation or full-output diagnostic repair should be proposed as separate infrastructure or adapter work, not folded into this rejected model-selection candidate.

## Rollback Notes

Revert only the six implementation files listed above to remove the `dinosaur_moist` factory, registry entry, exports, and tests. Preserve `.logbook/history/2026-06-16_07-36-31_moist-virtual-temperature-dynamics/` and ignored raw evaluation artifacts under `outputs/eval/`.
