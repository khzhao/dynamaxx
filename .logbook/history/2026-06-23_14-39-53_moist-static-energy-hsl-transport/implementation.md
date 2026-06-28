# Implementation Record

## Identity

- Proposal slug: moist-static-energy-hsl-transport
- Candidate model name: dino_hsl2_mse_hsl
- Incumbent model name: dino_hsl2_theta_dse_hsl
- Baseline commit: a274541cc57f593b8e5796e1df8307e8820c2d6b
- Candidate commit: uncommitted worktree

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-23_14-39-53_moist-static-energy-hsl-transport/implementation.md

## Implementation Summary

Implemented `dino_hsl2_mse_hsl` as a side-by-side opt-in candidate derived from
`dry_static_energy_hsl_transport_dinosaur_dycore_model()`. The new
`use_moist_static_energy_hsl_transport` selector defaults to `False` and is
enabled only by the new factory.

The sigma primitive-equation path now has a `nodal_moist_static_energy_anomaly`
helper that computes layer-mean-removed `Cp T + Phi + L_v q` using
`scales.LATENT_HEAT_OF_VAPORIZATION` nondimensionalized through
`physics_specs.nondimensionalize(...)`. When enabled and specific humidity is
available through existing tracer plumbing, the temperature tendency branch
transports MSE with the accepted HSL helper, transports humidity with the same
finite scalar-transport path, and converts horizontal MSE tendency back to
temperature as `(dmse_dt - L_v * dq_dt) / Cp`. The MSE branch reads the humidity
tracer directly and does not require `humidity_key`, so this candidate does not
enable broader primitive-equation moisture dynamics. Vertical theta tendency
and adiabatic pressure-work terms remain aligned with the accepted DSE-HSL path.

If humidity is absent or any MSE, humidity, conversion, or resulting tendency
diagnostic is nonfinite, the branch returns the accepted DSE-HSL tendency.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | All checks passed. |
| `git diff --check` | pass | No whitespace errors. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "mse_hsl or dse_hsl or hsl2_theta" tests/dycore/models/dinosaur/test_dependency.py -k "mse_hsl or dse_hsl or registry" tests/dycore/test_registry.py -k "mse_hsl or dse_hsl or lists_default"` | pass | 17 passed, 156 deselected. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mse_hsl` | pass | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.267648`, metrics at `outputs/eval/fast_dino_hsl2_mse_hsl.json`. |

## Repair Attempts

- Failure observed: focused pytest initially expected three HSL scalar captures in the MSE test.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: corrected the test expectation to include the existing theta-HSL transport call before DSE, MSE, and humidity captures.
- Follow-up command and result: focused pytest command above passed with 17 tests passing.
- Failure observed in Orchestrator review: MSE tracer access was initially tied to `humidity_key`, which would make the side-by-side candidate fall back to DSE-HSL because the incumbent keeps `use_humidity_in_dynamics=False`.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: decoupled MSE tracer access from `humidity_key` by reading the existing `specific_humidity` tracer directly and updated tests to exercise the branch with `humidity_key=None`.
- Follow-up command and result: Orchestrator reran `uv run ruff check ...`, `git diff --check`, and the focused pytest command; all passed. The focused pytest command passed with 17 tests passing and 156 deselected.
- Full test gate: Orchestrator ran `uv run pytest`; it passed with 239 tests passing and 2 skipped.

## Known Limitations

- Limitation: The MSE branch is guarded by finite-diagnostic fallback only; no evaluation-result tuning or empirical tendency cap was added.
- Limitation: Fast eval was run only as an implementation sanity check. Scorer still owns fixed iteration and validation gates.

## Rollback Notes

Revert the new MSE selector, helper, candidate factory/export/registry alias,
focused tests, and this implementation record. Leave unrelated logbook history
and generated eval outputs untouched unless the Orchestrator explicitly asks for
cleanup.
