# Implementation Record

## Identity

- Proposal slug: hydrostatic-inverted-mass-dse-hsl
- Candidate model name: dino_mass_dse_hydroinv
- Incumbent model name: dino_hsl2_mass_dse
- Baseline commit: 2c70bb5b77370a074330c2b46954f74f20771f12
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-24_01-58-03_hydrostatic-inverted-mass-dse-hsl/implementation.md

## Implementation Summary

Registered side-by-side model `dino_mass_dse_hydroinv`, derived from
`dino_hsl2_mass_dse`.

The candidate keeps the accepted mass-DSE HSL transported scalar and trajectory,
then converts `layer_mass_dse_dt_horizontal_nodal` to horizontal temperature
tendency by solving `(Cp * I + G_sigma) dT_dt = layer_mass_dse_dt_horizontal_nodal`
with the existing sigma-coordinate hydrostatic geopotential weight matrix from
`get_geopotential_weights_sigma`.

The incumbent vertical theta tendency and adiabatic tendency are added unchanged.
If the hydrostatic operator, solved tendency, pressure-thickness diagnostics, or
selected modal tendency are nonfinite, the candidate returns the accepted
`dino_hsl2_mass_dse` tendency path.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "hydrostatic_inverted_mass_dse or layer_mass_dse or dse_hsl"` | pass | 13 passed, 116 deselected. Preliminary focused primitive-equation check. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | pass | Exact requested ruff command; all checks passed. |
| `git diff --check` | pass | No whitespace errors. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k "hydrostatic_inverted_mass_dse or layer_mass_dse or dse_hsl or registry or dinosaur_imports_without_external_dinosaur_package or dinosaur_is_registered_as_canonical_dycore_model"` | pass | 43 passed, 133 deselected. Covers changed primitive-equation, dependency/import, and registry tests. |
| `uv run dynamaxx-eval fast --model dino_mass_dse_hydroinv` | pass | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.297131`; metrics at `outputs/eval/fast_dino_mass_dse_hydroinv.json`. |
| `uv run pytest` | pass | Orchestrator full test gate passed with 242 passed and 2 skipped. |

## Repair Attempts

- Failure observed: none from required commands.
- Implementer-owned failure: no command failure. During pre-check diff inspection,
  the initial local patch still had the old mass-DSE `return` instead of a named
  accepted fallback value, which would have made the hydrostatic branch
  unreachable.
- NaN/Inf forecast observed: no.
- Fix attempted: replaced the incumbent mass-DSE `return jnp.where(...)` with
  `accepted_mass_dse_temperature_tendency = jnp.where(...)`, then used that value
  for both incumbent behavior and hydrostatic fallback.
- Follow-up command and result: focused primitive-equation pytest passed; exact
  required ruff, diff check, focused pytest, and fast eval all passed.

## Known Limitations

- Fast and full pytest gates passed locally. Iteration, validation, and golden
  protocols were not run by the Implementer.
- The fast primary score is recorded only as a sanity result; acceptance remains
  the Scorer/Orchestrator decision under the fixed evaluation protocol.
- The hydrostatic inversion performs a small dense vertical solve when the
  candidate selector is enabled; no inverse is cached.

## Rollback Notes

Remove the `use_hydrostatic_inverted_mass_dse_hsl_transport` selector, the
hydrostatic conversion helper and branch, the
`hydrostatic_inverted_mass_dse_hsl_transport_dinosaur_dycore_model` factory and
export, the `dino_mass_dse_hydroinv` registry entry, and the focused tests added
for this candidate. Leave unrelated files and the untracked `gifs/` directory
untouched.
