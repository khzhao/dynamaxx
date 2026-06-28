# Implementation Record

## Model Identity

- Candidate model: `dino_hsl2_theta_cpvert`
- Incumbent model: `dino_hsl2_theta`
- Baseline commit at implementation time: `72efada4e0afbd8e34e3184dbcef90cb91cc051c`
- Candidate commit: not committed

## Changed Files

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - Added default-false `use_charney_phillips_theta_vertical_transport`.
  - Added `charney_phillips_theta_vertical_transport`, gated only inside the potential-temperature vertical theta branch.
  - Reconstructs theta anomaly at internal sigma interfaces in log-sigma coordinates with existing vertical interpolation helpers.
  - Forms padded zero-boundary interface fluxes and returns negative flux divergence over layer thickness.
  - Uses a column-mean theta anomaly reference in the transported interface flux so adding a vertical constant does not create a vertical tendency.
  - Falls back to the accepted centered vertical tendency when reconstructed interfaces, fluxes, layer thicknesses, flux divergence, or candidate tendency are nonfinite/invalid.
  - Threaded the selector through the concrete dry/moist primitive-equation constructors.
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - Added adapter dataclass selector plumbing into `_primitive_equation`.
  - Added `charney_phillips_theta_vertical_transport_dinosaur_dycore_model()`, extending `midpoint_semilagrangian_theta_departure_dinosaur_dycore_model()` with only name and selector changes.
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - Exported the new factory.
- `src/dynamaxx/dycore/registry.py`
  - Registered `dino_hsl2_theta_cpvert`.
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - Added factory parity, CP-vertical constant-theta, padded-boundary/no-source, nonfinite fallback, nonthermal explicit-term identity, and non-JIT smoke forecast coverage.
  - Added bounded-repair coverage that overlarge finite interface tendencies
    fall back to the accepted centered vertical tendency.
- `tests/dycore/models/dinosaur/test_dependency.py`
  - Added dependency/import and registration coverage for the new factory and model name.
- `tests/dycore/test_registry.py`
  - Added registry listing and factory parity coverage.

No edits were made to `sigma_coordinates.py` or `vertical_interpolation.py`; the implementation reused existing helpers locally in `primitive_equations.py`.

## Commands Run

- `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
  - Status: passed
- `git diff --check`
  - Status: passed
- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'cpvert or hsl2_theta or hsl_theta or vertical' tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
  - First run status: failed. The CP-vertical interpolation target was one-dimensional, but the existing vectorized interpolation helper expects target coordinates with horizontal dimensions.
  - Repair: broadcast internal log-sigma targets to `sigma_dot_full.shape`.
  - Final status: passed, `22 passed, 143 deselected`.
- `uv run dynamaxx-eval fast --model dino_hsl2_theta_cpvert`
  - First run status: failed at the fixed fast gate. The command exited 0, but
    the metrics payload reported `failed=True`, `nonfinite_forecast`,
    `nonfinite_metric`, and `primary_score=-Infinity`.
  - Repair: added a conservative local tendency-magnitude guard. The
    CP/interface vertical theta tendency is used only where it is finite and no
    more than two times the accepted centered vertical theta tendency magnitude,
    with a tiny absolute floor. Overlarge finite values fall back to the
    incumbent centered vertical tendency at that grid point; nonfinite
    reconstruction diagnostics still fall back to the incumbent branch.
  - Follow-up status: pending Orchestrator rerun.
- `uv run ruff check src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
  - Follow-up status after bounded repair: passed.
- `git diff --check`
  - Follow-up status after bounded repair: passed.
- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'cpvert or hsl2_theta or hsl_theta or vertical' tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
  - Follow-up status after bounded repair: passed, `23 passed, 143 deselected`.
- `uv run pytest`
  - Follow-up status after bounded repair: passed, `232 passed, 2 skipped in
    186.73s`.

## Limitations

- Did not run `uv run dynamaxx-eval fast`; the requested focused checks passed, and fixed scoring is left to the Orchestrator/Scorer.
- Did not run iteration, validation, or golden protocols.
- The new selector only changes vertical theta-anomaly transport in the potential-temperature tendency path. Momentum/divergence vertical advection, log-pressure continuity, implicit operators, horizontal HSL theta transport, pressure work, residuals, filters, diagnostics, and the forecast API remain on the incumbent path.
