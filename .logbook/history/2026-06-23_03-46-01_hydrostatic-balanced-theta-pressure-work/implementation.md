# Implementation

## Model Identity

- Candidate model: `dino_hsl2_theta_pw`
- Incumbent model: `dino_hsl2_theta`
- Baseline commit: `72efada4e0afbd8e34e3184dbcef90cb91cc051c`
- Candidate commit: not committed

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`
- `.logbook/history/2026-06-23_03-46-01_hydrostatic-balanced-theta-pressure-work/implementation.md`

## Implementation Notes

- Added the default-false selector `use_hydrostatic_theta_pressure_work` to
  `PrimitiveEquationsSigma`, the concrete primitive-equation constructors, the
  Dinosaur adapter dataclass, and `_primitive_equation`.
- Registered/exported the side-by-side factory
  `hydrostatic_theta_pressure_work_dinosaur_dycore_model()` as
  `dino_hsl2_theta_pw`.
- The new factory starts from
  `midpoint_semilagrangian_theta_departure_dinosaur_dycore_model()` and changes
  only `name` and `use_hydrostatic_theta_pressure_work`.
- In the potential-temperature tendency branch, the accepted theta transport
  path is unchanged. When the new selector is enabled, only the additive
  pressure-work term is replaced.
- The candidate pressure-work diagnostic uses
  `dlog(p)/dt = dlog(ps)/dt + sigma_dot_center / sigma_center`, with
  `sigma_dot_center` formed by averaging adjacent full-level sigma-dot values
  after padding zero top and bottom boundary values.
- Guarding preserves existing behavior: invalid shared theta/pressure
  diagnostics fall back to the prior temperature-form tendency, while invalid
  pressure-work-only diagnostics fall back to the incumbent theta-form tendency.

## Tests And Sanity Commands

- `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
  - Status: passed
- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'pressure_work or hsl2_theta or hsl_theta' tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
  - Status: passed, `22 passed, 143 deselected`
- `git diff --check`
  - Status: passed
- `uv run pytest`
  - Status: passed, `231 passed, 2 skipped`

## Repair Attempts

- Ruff reported import ordering issues in the Dinosaur package export and
  primitive-equation test imports. The import order was corrected and ruff then
  passed.

## Limitations

- Did not run `uv run dynamaxx-eval fast`; the required focused checks passed,
  and scoring is left to the Orchestrator/Scorer.
- Did not run or modify golden, iteration, validation, WeatherBench2 metrics,
  splits, lead times, target variables, output variables, worker policy, or
  forecast contract.
- Did not implement selective HSL curvature fallback, omega-alpha energy
  coupling, bounded pressure-work cap, full-state theta, Charney-Phillips
  vertical transport, or any second idea.
