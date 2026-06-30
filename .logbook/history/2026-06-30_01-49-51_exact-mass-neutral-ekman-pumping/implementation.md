# Implementation Record

## Identity

- Proposal slug: exact-mass-neutral-ekman-pumping
- Candidate model name: dino_ri2m_ekman_massfix
- Incumbent model name: dino_ri2m_ekman_coupled
- Baseline commit: 9ba646bcbcd98bb982356052a17c0d9bb0f60ca2
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py
- Path: .logbook/history/2026-06-30_01-49-51_exact-mass-neutral-ekman-pumping/implementation.md

## Implementation Summary

Added the default-false `use_surface_mass_neutral_ekman_pumping` selector to the
Dinosaur dycore adapter and threaded it only into `_ekman_coupled_surface_step_filter`.
The incumbent stress formula, drag coefficient, fixed depth, lower-layer taper,
equatorial pumping taper, wind caps, pressure cap, finite fallback, wind
projection, and post-pressure modal/nodal projection-scale safety check remain
unchanged.

Added `_bounded_surface_mass_neutral_logp_increment`, which solves one scalar
offset by monotone bisection for a capped log-pressure increment satisfying the
area-weighted surface-pressure conservation condition under `exp(delta)`. The
helper returns the incumbent `_bounded_area_neutral_field` projection when
surface pressure is nonpositive or nonfinite, the bracket is invalid, or the
candidate increment is nonfinite.

Registered the side-by-side candidate `dino_ri2m_ekman_massfix` from the coupled
Ekman incumbent with only the new selector enabled. Added focused helper,
filter, factory, registry, dependency, and non-JIT smoke forecast tests.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur tests/dycore/test_registry.py` | failed | Initial run: 1 helper mass-conservation assertion was tighter than float32 precision by about one ULP. |
| `uv run pytest tests/dycore/models/dinosaur tests/dycore/test_registry.py` | passed | 216 passed, 1 skipped in 306.67s. |
| `uv run pytest` | passed | 282 passed, 2 skipped in 316.51s. |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_massfix` | passed | failed=False, issues=0, records=120, primary_score=-0.167726, metrics=outputs/eval/fast_dino_ri2m_ekman_massfix.json. |

## Repair Attempts

- Failure observed: direct helper test required `rtol=1.0e-7`; float32 mass sums differed by `4.7683716e-07` on a mass of `4.442`.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: relaxed the focused test tolerance to `rtol=2.0e-7`, keeping the implementation unchanged.
- Follow-up command and result: `uv run pytest tests/dycore/models/dinosaur tests/dycore/test_registry.py` passed.

## Known Limitations

- The helper is evaluated in the existing JAX float32 path, so direct synthetic mass-conservation assertions use float32-appropriate tolerance.
- Iteration, validation, golden, and incumbent evaluations were not run, per Implementer instructions.

## Rollback Notes

Remove the new selector, helper, candidate factory/export, registry key, and the
focused tests listed above. Leave unrelated work and the pre-existing untracked
`gifs/` directory untouched.
