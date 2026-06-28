# Implementation Record

## Identity

- Proposal slug: momentum-only-sl-vertical-advection
- Candidate model name: dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_momslva
- Incumbent model name: dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m
- Baseline commit: 3992244f20b2a938fdd96f8904f3749f5505670d
- Candidate commit: not committed

## Files Changed

- Path: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- Path: `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- Path: `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- Path: `src/dynamaxx/dycore/registry.py`
- Path: `tests/dycore/models/dinosaur/test_primitive_equations.py`
- Path: `tests/dycore/models/dinosaur/test_dependency.py`
- Path: `tests/dycore/test_registry.py`

## Implementation Summary

The candidate added a guarded momentum-only semi-Lagrangian vertical-advection option to the Dinosaur primitive-equation path. The default option remained disabled, preserving incumbent behavior by default.

When enabled, `PrimitiveEquationsSigma.curl_and_div_tendencies` replaced only the vertical-advection contribution for horizontal wind components. The implementation computed incumbent `sigma_dot_u` and `sigma_dot_v`, then attempted a bounded sigma-column departure remap for `u` and `v` using the model step, `sigma_dot_full`, vertical-center coordinates, and a center-spacing CFL cap. Scalar, thermal, mass, humidity, WTG, T2m diagnostics, output contract, and fixed evaluation protocols were left unchanged.

The adapter and registry exposed the candidate as `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_momslva`, preserving the incumbent factory settings and enabling only `use_momentum_only_semi_lagrangian_vertical_advection`.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'momentum_slva or bulk_richardson_2m_temperature_factory or default_dinosaur_configuration' tests/dycore/models/dinosaur/test_dependency.py -k 'momentum_sl or registered' tests/dycore/test_registry.py -k 'momentum_sl or bulk_richardson'` | 0 | 14 passed, 191 deselected after the interpolation-direction fix. |
| `uv run python -m compileall src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py` | 0 | Compile check passed. |
| `uv run ruff format --check src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/primitive_equations.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Touched files already formatted after formatting the touched files. |
| `uv run ruff check` | 0 | Lint passed. |
| `git diff --check` | 0 | Whitespace check passed. |
| Tiny non-jit smoke forecast for candidate output variables | 0 | Shape `(2, 1, 4, 4, 3)` and finite outputs. |
| `uv run pytest` | 0 | 271 passed, 2 skipped in 282.01s. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_momslva` | 0 | Clean diagnostics, 120 records, primary score `-0.5760627913044538`. |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_momslva --workers 4` | 0 | Fixed iteration eval completed with failed diagnostics, 153 issues, primary score sentinel `-1.7976931348623157e+308`. |

## Repair Attempts

- Failure observed: the fixed iteration eval produced non-finite forecasts and a failed diagnostic status.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: yes
- Fix attempted: before full scoring, the helper interpolation direction was corrected from `_vertical_interp(sigma_centers, departure_sigma, wind)` to `_vertical_interp(departure_sigma, sigma_centers, wind)` after a focused linear-profile test exposed the direction error.
- Follow-up command and result: focused tests, compile, ruff checks, full pytest, and fast eval passed after the repair; the full iteration gate still failed with non-finite forecasts.

## Known Limitations

- The guarded local helper passed unit and smoke checks but was not stable over the full fixed iteration split.
- The implementation added formatting changes in `primitive_equations.py` because the touched file had pre-existing format drift; these changes were reverted with the rest of the rejected candidate.

## Rollback Notes

Revert only the seven candidate source/test files:

```bash
git restore -- \
  src/dynamaxx/dycore/models/dinosaur/__init__.py \
  src/dynamaxx/dycore/models/dinosaur/adapter.py \
  src/dynamaxx/dycore/models/dinosaur/primitive_equations.py \
  src/dynamaxx/dycore/registry.py \
  tests/dycore/models/dinosaur/test_dependency.py \
  tests/dycore/models/dinosaur/test_primitive_equations.py \
  tests/dycore/test_registry.py
```
