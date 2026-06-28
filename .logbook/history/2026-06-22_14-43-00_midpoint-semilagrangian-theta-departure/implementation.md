# Implementation Record

## Candidate

- Proposal: `midpoint-semilagrangian-theta-departure`
- Candidate model: `dino_hsl2_theta`
- Baseline commit: `34d20a0afd7133cba41c595072b5c14c8e42a88f`
- Candidate commit: not committed before scoring

## Changed Files

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Design Notes

The candidate adds a side-by-side midpoint departure selector on top of the
accepted `dino_hsl_theta` model. The default first-order horizontal
semi-Lagrangian theta transport remains unchanged and continues to serve as the
fallback path.

When `use_midpoint_semilagrangian_theta_departure` is enabled, the dycore first
computes a bounded half-step backward displacement from the arrival-grid
horizontal wind, remaps the nodal horizontal wind components to that midpoint,
then computes the full-step theta departure displacement from the midpoint
wind. The same CFL cap, finite checks, and incumbent fallback policy used by
the accepted HSL theta transport are preserved. The midpoint path applies only
to the horizontal dry-theta anomaly transport contribution; momentum, log
surface pressure, vertical theta transport, DFI, weak-HS forcing, residuals,
and ocean bulk sensible heat flux remain inherited from `dino_hsl_theta`.

The new registry alias is `dino_hsl2_theta`, with the forecast contract,
emitted variables, fixed metrics, and evaluation protocols unchanged.

## Tests And Checks

- `python -m compileall -q ...`: passed in Implementer subagent.
- `uv run ruff format ...`: completed in Implementer subagent.
- `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`: passed.
- `git diff --check`: passed.
- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`: `157 passed in 163.16s`.
- `uv run pytest`: `223 passed, 2 skipped in 172.28s`.

## Known Limitations

The midpoint wind remap adds interpolation work in every positive-time theta
transport step. It is intentionally guarded by first-order HSL fallback rather
than tuning constants or changing evaluation behavior. Fixed WeatherBench2 fast,
iteration, and validation scoring are recorded separately by the Scorer.
