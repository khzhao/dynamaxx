# Implementation

- Proposal: `.logbook/research/ready/coriolis-centered-hsl-theta-departure.md`
- Baseline commit: `72efada4e0afbd8e34e3184dbcef90cb91cc051c`
- Candidate commit: not committed
- Candidate model: `dino_hsl_corcen`
- Incumbent model: `dino_hsl2_theta`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`
- `.logbook/history/2026-06-23_06-13-46_coriolis-centered-hsl-theta-departure/implementation.md`

## Implementation Notes

Added `use_coriolis_centered_semilagrangian_theta_departure`, defaulting to
false, and registered `dino_hsl_corcen` as a side-by-side model derived from
`dino_hsl2_theta`. The selector rotates only the diagnostic `cos_lat_u` winds
used by horizontal semi-Lagrangian theta departure geometry by the local
half-step Coriolis angle `0.5 * f * dt`. Prognostic state, non-theta tendencies,
vertical theta transport, pressure work, remap order, output variables, lead
protocols, and incumbent model behavior are unchanged.

The Coriolis-centered path retains the accepted first-order and midpoint HSL
theta machinery. If rotated winds or the selected rotated HSL departure path
are not finite, it falls back to the incumbent full-wind HSL2 path.

## Tests Run

- PASS: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'corcen or coriolis or hsl2_theta or hsl_theta' tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
- PASS: `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
- PASS: `git diff --check`
- PASS: `uv run pytest` (`229 passed, 2 skipped`)

## Repair Attempts

- Corrected the internal HSL theta transport refactor so the tuple-returning
  helper is private and the public method preserves the original array-returning
  interface.

## Limitations

- Did not run full `uv run pytest` or WeatherBench evaluation; those are
  reserved for Orchestrator/Scorer unless separately requested.
- The fallback is finite-diagnostic based. It does not tune or adapt the
  Coriolis-centering strength from forecast skill.
