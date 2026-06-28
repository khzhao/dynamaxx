# Implementation Record

## Identity

- Proposal slug: `hydrostatic-work-gated-vertical-dse`
- Candidate model name: `dino_hsl2_mass_dse_wtg_vdse_hwg`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Candidate commit: not committed at implementation time

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

Added a side-by-side Dinosaur dycore model,
`dino_hsl2_mass_dse_wtg_vdse_hwg`, derived from the accepted
`dino_hsl2_mass_dse_wtg_vdse_ramp` incumbent.

The implementation adds an opt-in hydrostatic-work gate inside the accepted
pressure-ramped vertical-DSE increment path. When enabled, the gate decomposes
the pressure-guarded vertical-DSE temperature increment into a
pressure-thickness-weighted column mean and a column-neutral vertical residual.
It computes a bounded column-work ratio and smoothly damps only the column-mean
component when that ratio is large. The column-neutral residual is preserved.

The incumbent time ramp, low-mode pressure guard, `0.05 K` per-step cap, WTG
relaxation, mass-DSE horizontal transport, surface residuals, output packing,
forecast API, and fixed evaluation protocols were not changed. The incumbent
model has the new selector disabled by default, and gate-specific invalid
diagnostics fall back to the incumbent vertical-DSE branch.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `python -m compileall ...` | 0 | Implementer syntax check on changed source and test files. |
| `uv run pytest ... -k <focused hydrostatic-work/registry/smoke selection>` | 0 | Implementer focused test run: `16 passed`. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_hwg` | 0 | Candidate fast score `-0.34772607973591296`; diagnostics clean with zero issues and 120 records. |
| `uv run ruff check ...` | 1 then 0 | First run found import ordering; Implementer fixed ordering and reran successfully. |
| `git diff --check` | 0 | No whitespace errors. |
| `uv run pytest` | 0 | Full required test suite: `259 passed, 2 skipped in 303.81s`. |

## Repair Attempts

- Failure observed: `uv run ruff check ...` reported import ordering.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: reordered imports in the touched test/source files.
- Follow-up command and result: `uv run ruff check ...` exited `0`.

## Known Limitations

- The candidate fast primary score is substantially worse than the current
  incumbent-family fast scores despite clean diagnostics. The fixed protocol
  still requires iteration scoring before a terminal model-selection decision.
- Validation must remain unrun unless iteration promotes.

## Rollback Notes

If rejected, revert the seven source/test files using `candidate.diff` from this
history directory. Do not remove raw evaluation artifacts or unrelated
pre-existing untracked content such as `gifs/`.
