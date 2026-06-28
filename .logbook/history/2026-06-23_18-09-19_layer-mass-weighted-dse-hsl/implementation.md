# Implementation Record

## Identity

- Proposal slug: layer-mass-weighted-dse-hsl
- Candidate model name: dino_hsl2_mass_dse
- Incumbent model name: dino_hsl2_theta_dse_hsl
- Baseline commit: a274541cc57f593b8e5796e1df8307e8820c2d6b
- Candidate commit: 2c70bb5b77370a074330c2b46954f74f20771f12

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/implementation.md

## Implementation Summary

Added the opt-in selector `use_layer_mass_weighted_dse_hsl_transport`, defaulting
to `False`, on the sigma primitive-equation path and adapter model. The accepted
DSE-HSL path remains unchanged when the selector is disabled.

For the new candidate, the sigma branch diagnoses nodal layer pressure thickness
as `self.coords.vertical.layer_thickness[:, None, None] * nodal_surface_pressure`.
It transports `delta_p * dry_static_energy_anomaly` through the accepted HSL
scalar helper, divides the resulting horizontal tendency by guarded local
`delta_p`, then converts to temperature tendency through `Cp`. Vertical theta
tendency, adiabatic tendency, log-surface-pressure tendency, momentum tendency,
tracers, outputs, and evaluation protocols are unchanged. Nonfinite or unsafe
mass-DSE diagnostics fall back to the incumbent DSE-HSL tendency.

Registered and exported the side-by-side candidate model
`dino_hsl2_mass_dse`, derived from
`dry_static_energy_hsl_transport_dinosaur_dycore_model()`.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Required lint selection passed. |
| `git diff --check` | pass | No whitespace or conflict-marker issues. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "hsl_theta or hsl2_theta or dse_hsl or layer_mass_dse" tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | 27 passed, 143 deselected. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse` | pass | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.263456`, metrics at `outputs/eval/fast_dino_hsl2_mass_dse.json`. |
| `uv run pytest` | pass | Orchestrator full test gate passed with 236 passed and 2 skipped. |

## Repair Attempts

- Failure observed: initial focused pytest run failed in `test_layer_mass_dse_uses_sigma_pressure_thickness_and_dse_anomaly`.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: corrected the test expectation to compare against the diagnosed nodal surface pressure `exp(to_nodal(log_surface_pressure))`, matching the implementation path after modal projection.
- Follow-up command and result: reran the focused pytest command; it passed with 27 passed and 143 deselected.

## Known Limitations

- Limitation: The implementation intentionally keeps log-surface-pressure transport on the incumbent path, so this is not a fully flux-form mass-continuity transport update.
- Limitation: The candidate keeps log-surface-pressure transport on the incumbent path, so future work could test a fully mass-flux-consistent pressure transport proposal separately.

## Rollback Notes

Remove the mass-DSE selector, pressure-thickness helper, weighted DSE branch,
adapter pass-through, factory/export, registry entry, and the mass-DSE focused
tests added for this experiment. Leave the incumbent DSE-HSL model and fixed
evaluation protocols unchanged.
