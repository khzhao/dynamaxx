# Implementation Record

## Identity

- Proposal slug: finite-volume-mass-dse-hsl-remap
- Candidate model name: dino_hsl2_mass_dse_fv_remap
- Incumbent model name: dino_hsl2_mass_dse
- Baseline commit: 2c70bb5b77370a074330c2b46954f74f20771f12
- Candidate commit: unavailable

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-24_15-20-39_finite-volume-mass-dse-hsl-remap/implementation.md

## Implementation Summary

Implemented one side-by-side candidate, `dino_hsl2_mass_dse_fv_remap`, derived
from `dino_hsl2_mass_dse`. The incumbent mass-DSE branch remains the fallback
and is unchanged unless the new `use_finite_volume_mass_dse_hsl_remap` selector
is true.

The candidate keeps the accepted transported quantity
`weighted_dse_anomaly = delta_p * dry_static_energy_anomaly`, the local guarded
division by `delta_p`, and the local division by `Cp`. It replaces only the
weighted mass-DSE scalar remap/tendency: the helper uses the incumbent bounded
HSL2 midpoint departure remap, then applies one constant correction per layer so
the global horizontal quadrature integral of the remapped weighted scalar
matches the pre-remap integral to roundoff. Invalid displacement, remap,
correction, pressure-thickness, or tendency diagnostics fall back to the
accepted mass-DSE bilinear tendency path.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Final lint pass. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "finite_volume or fv_remap or mass_dse"` | pass | 9 passed, 122 deselected. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 47 passed. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_fv_remap` | pass | failed=False, issues=0, records=120, primary_score=-0.263938; metrics: outputs/eval/fast_dino_hsl2_mass_dse_fv_remap.json. |

## Repair Attempts

- Failure observed: focused primitive tests initially failed for constant-field
  zero tendency and strict periodic tendency comparison.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: added exact constant-layer preservation inside the FV-remap
  correction; changed the periodicity test to compare remapped fields directly
  so float32 remap roundoff is not amplified by the synthetic `1e-3` step.
- Follow-up command and result: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "finite_volume or fv_remap or mass_dse"` passed.

## Known Limitations

- Limitation: This is the allowed narrow conservative finite-volume-style
  correction, not a full split conservative overlap-geometry remap. It preserves
  each layer's global quadrature integral after HSL2 remap, but it is not locally
  conservative at every cell face.
- Limitation: Candidate commit is unavailable because no commit was requested.

## Rollback Notes

Revert only the added selector, FV-remap helper, candidate factory/export,
registry entry, focused tests, and this implementation record. Leave unrelated
pre-existing files such as `gifs/` untouched.
