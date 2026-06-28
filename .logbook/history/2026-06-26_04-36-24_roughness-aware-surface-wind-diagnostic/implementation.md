# Implementation Record

## Identity

- Proposal slug: roughness-aware-surface-wind-diagnostic
- Candidate model name: dino_hsl2_mass_dse_wtg_vdse_z0_10m
- Incumbent model name: dino_hsl2_mass_dse_wtg_vdse_ramp
- Baseline commit: ff40def55ac707e8915c840b856a0aaa3345b046
- Candidate commit: not committed before scoring

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented a side-by-side candidate model,
`dino_hsl2_mass_dse_wtg_vdse_z0_10m`, derived from the accepted
pressure-ramped vertical-DSE WTG incumbent. The candidate adds an opt-in
adapter flag for roughness-aware 10 m wind diagnostics, loads the existing
land-sea static field only when needed, converts it to Dinosaur latitude order,
and derives a bounded neutral log-law roughness transfer adjustment. The
adjustment multiplies the existing Richardson surface-layer 10 m wind factor
before the pre-existing final wind-factor clip.

The implementation is diagnostic-only: it does not alter the prognostic
trajectory, vertical-DSE path, WTG relaxation, pressure diagnostics, temperature
diagnostics, residual corrections, or fixed evaluation protocol. If the static
land-sea field is absent, malformed, non-finite, or outside the expected shape,
the roughness adjustment remains unset and the wind diagnostic follows the
incumbent path.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | ---: | --- |
| `python -m compileall -q src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur tests/dycore/test_registry.py` | 0 | Implementer pre-scoring syntax check. |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Implementer formatting pass. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Implementer lint pass. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Focused candidate coverage; final focused run reported 51 passed. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_z0_10m` | 0 | Pre-scoring fast artifact verified: primary score -0.22400258588040814, diagnostics failed false, issue count 0, 120 metric rows. |
| `uv run python - <<'PY' ... registry.dycore_model_names/create_dycore_model ... PY` | 0 | Candidate and incumbent both registered and construct to expected model names. |
| `uv run pytest` | 0 | Full suite passed: 263 passed, 2 skipped in 455.51s. |

## Repair Attempts

- Failure observed: focused roughness tests initially exposed two test issues during implementation.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: repaired the focused tests within the selected proposal scope without broadening the model change.
- Follow-up command and result: focused Dinosaur dependency/registry tests passed; full `uv run pytest` passed with 263 passed, 2 skipped.

## Known Limitations

- The current roughness proxy uses the available land-sea fraction as the only static surface input. Vegetation, lake, and sea-ice roughness refinements were intentionally left out to keep this candidate small and to avoid introducing new data dependencies.
- The roughness transfer adjustment is finally bounded by both its own clip and the incumbent surface-layer wind-factor clip, so part of the roughness signal can saturate where the incumbent diagnostic already reaches its wind-factor bounds.
- Because this is output-side only, aggregate score movement is expected to be narrow and concentrated in `10m_u_component_of_wind`.

## Rollback Notes

If rejected, apply the reverse of `candidate.diff` from this history directory
to revert only the implementation/test changes from this experiment. Preserve
raw evaluation outputs and the immutable history record. The pre-existing
untracked `gifs/` directory is unrelated and must not be removed.
