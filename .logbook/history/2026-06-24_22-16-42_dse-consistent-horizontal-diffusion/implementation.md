# Implementation Record

## Identity

- Proposal slug: dse-consistent-horizontal-diffusion
- Candidate model name: dino_mass_dse_diff
- Incumbent model name: dino_hsl2_mass_dse
- Baseline commit: 2c70bb5b77370a074330c2b46954f74f20771f12
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-24_22-16-42_dse-consistent-horizontal-diffusion/implementation.md

## Implementation Summary

Registered `dino_mass_dse_diff` as a side-by-side factory derived from
`layer_mass_weighted_dse_hsl_transport_dinosaur_dycore_model()` with only the
model name and `use_dse_consistent_horizontal_diffusion=True` changed.

The opt-in rollout filter first computes the incumbent horizontal diffusion
state for all leaves. For the thermal leaf only, it diagnoses the next-state
dry static energy anomaly through the existing dry hydrostatic
`PrimitiveEquations.nodal_dry_static_energy_anomaly` path, applies the same
horizontal diffusion modal scaling to that DSE anomaly, recenters the original
and filtered DSE anomalies to preserve layerwise mean neutrality, converts the
filtered DSE change to `dT = dDSE / Cp`, and applies that increment to
`temperature_variation`. If DSE diagnostics, modal transforms, increments, or
the corrected thermal state are nonfinite or shape-incompatible, the filter
uses incumbent temperature diffusion. Non-thermal leaves come directly from the
incumbent diffusion path.

DFI filters are explicitly rebuilt without the DSE-consistent selector, so the
rollout-only custom filter is not routed into DFI.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | `All checks passed!` |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "dse_diff or horizontal_diffusion or mass_dse"` | passed | 9 passed, 122 deselected |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | 47 passed |
| `uv run dynamaxx-eval fast --model dino_mass_dse_diff` | passed | failed=False, issues=0, records=120, primary_score=-0.263411, metrics=outputs/eval/fast_dino_mass_dse_diff.json |

## Repair Attempts

- Failure observed: constant-DSE unit test saw a tiny zero-mode thermal drift.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: recentered the original diagnosed DSE anomaly with the same
  layer-mean helper used for the filtered anomaly before differencing.
- Follow-up command and result: focused primitive-equation pytest passed.

- Failure observed: DFI setup test did not build the deferred trajectory, then
  assumed only one rollout filter while the incumbent chain also includes theta
  mean recentering.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: invoked the deferred trajectory function and asserted the DSE
  diffusion is the first rollout filter while DFI retains incumbent diffusion.
- Follow-up command and result: focused primitive-equation pytest passed.

## Known Limitations

- The DSE-consistent diffusion helper adds extra spherical harmonic transforms
  and dry hydrostatic diagnostics during positive-time rollout.
- The DSE diagnostic is dry by proposal design; moisture-coupled diffusion was
  not added.
- No iteration or validation protocols were run by the Implementer.

## Rollback Notes

Revert the selector, custom filter helper, candidate factory/export, registry
entry, focused tests, and this implementation record. Do not remove unrelated
worktree files such as the pre-existing untracked `gifs/` directory.
