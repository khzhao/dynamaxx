# Implementation Record

## Identity

- Proposal slug: `bounded-moist-virtual-temperature-dynamics`
- Candidate model name:
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist`
- Incumbent model name:
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`
- Baseline commit: `a7833574e9ade1a5271bd8cbef2fa1357465f5a8`
- Candidate commit: not committed at scoring handoff

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

The implementation adds a side-by-side bounded-moist candidate that preserves
the incumbent DFI, near-surface residual correction, weak Held-Suarez
relaxation, log-pressure initialization, hydrostatic layer-mean temperature
initialization, spectral truncation, inner step, and output path. The candidate
only enables moist virtual-temperature dynamics and bounded humidity handling.

The adapter now supports `bound_humidity_for_dynamics`. When the flag is enabled
for a humid forecast state, initialized `specific_humidity` is clipped to
`[0, 1]` before it is converted to the Dinosaur modal tracer, and a post-step
filter bounds the named humidity tracer after each inner step. The filter
leaves vorticity, divergence, temperature variation, log surface pressure,
non-humidity tracers, and `sim_time` unchanged.

`PrimitiveEquationsSigma` now uses bounded humidity values when bounded moist
dynamics are requested. This includes virtual-temperature adjustment, moist
temperature-tendency denominators, and humidity-gradient correction terms. When
the bounded flag is disabled, the existing humidity behavior is unchanged.

The candidate is registered as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist`.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | `65 passed in 57.89s` |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Touched-file lint passed. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_moist` | 0 | `failed=False`, `issues=0`, primary score `-1.1788189813240295` |

## Repair Attempts

- Failure observed: manual review found that initial implementation bounded
  nodal humidity but humidity-gradient correction terms still read raw modal
  humidity.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: added a modal dynamics accessor that projects bounded nodal
  humidity back to modal space when `bound_humidity_for_dynamics` is enabled,
  and routed humidity-gradient correction terms through it.
- Follow-up command and result: focused tests, lint, and fast sanity all passed.

## Known Limitations

- The candidate activates moist virtual-temperature dynamics without
  condensation, precipitation, radiation, or moisture sources/sinks.
- The humidity bound is physical but not mass-conservative for the humidity
  tracer.
- Validation and golden were not run by the Implementer.

## Rollback Notes

If rejected, revert only the seven files listed above. Preserve this history
directory and raw evaluation artifacts as the immutable experiment record.
