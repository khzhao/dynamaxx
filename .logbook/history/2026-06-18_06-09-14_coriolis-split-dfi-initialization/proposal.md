---
schema_version: 1
slug: coriolis-split-dfi-initialization
title: Use the Accepted Coriolis Split Inside Digital Filter Initialization
status: ready
created_at: 2026-06-18T06:01:43Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use the Accepted Coriolis Split Inside Digital Filter Initialization

## Hypothesis

The accepted incumbent uses a symmetric exact Coriolis rotation during the
positive-time rollout, but its digital filter initialization still uses the
original primitive-equation Coriolis term. That means the initialized state is
balanced by one fast-wave operator and then forecast with a different
operator-split Coriolis treatment.

Using the same exact Coriolis split family inside DFI should reduce a remaining
initialization/rollout mismatch without changing the forecast API, the Strang
positive-time rollout, weak Held-Suarez forcing, hydrostatic initialization, or
output diagnostics.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_dfi_coriolis`.
Preserve every incumbent option, including the accepted symmetric exact
Coriolis rollout split.

Add a DFI-specific step builder that mirrors the accepted rollout operator:

- build the DFI primitive equation with `angular_velocity=0.0`, so the Coriolis
  tendency is not also applied inside the explicit primitive-equation step;
- apply an exact Coriolis rotation with the correct sign after each forward DFI
  substep and the opposite sign after each backward DFI substep;
- keep the existing DFI time span, cutoff period, inner step, weak-HS forcing,
  spectral diffusion, and Lanczos weights unchanged;
- apply this split only when both DFI and the accepted Coriolis Strang option
  are enabled, leaving all older registered models unchanged.

This proposal changes the balance operator used to construct the initial
filtered state, not the scored forecast protocol.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` if a small
    signed-step DFI helper is cleaner than adapter-local code
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. `DycoreModel.forecast(ForecastInput) -> WeatherState` remains
    unchanged.
- Tests to update:
  - Verify the candidate preserves all incumbent flags and adds only the
    DFI-Coriolis split option.
  - Unit-test that signed exact rotation uses opposite signs for forward and
    backward DFI legs.
  - Verify the older Strang incumbent keeps the current DFI path.
  - Add a finite non-JIT smoke forecast and registry coverage.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at short and medium leads
    if remaining mass-field error is partly DFI balance noise from a Coriolis
    operator mismatch.
  - `10m_u_component_of_wind` if near-inertial phase error is still present
    after the accepted rollout-only Strang split.
- Expected neutral metrics:
  - `2m_temperature` should be close to neutral because weak-HS forcing,
    hydrostatic initialization, and near-surface residuals are unchanged.
- Possible regressions:
  - The signed DFI split may reduce the beneficial smoothing from the current
    fully coupled DFI equation.
  - If the accepted Strang gain was purely positive-rollout phase error, DFI
    matching may be too small to clear the iteration threshold.

## Risks

- Numerical stability:
  - Moderate. The forecast rollout remains accepted, but DFI is reversible only
    if forward and backward signed rotations are implemented consistently.
- Compute cost:
  - Low. The same DFI window and step count are used, with extra wind
    modal-nodal transforms during DFI only.
- Data leakage:
  - None. The candidate uses no future targets, fitted coefficients, validation
    artifacts, or changed metrics.
- Physical plausibility:
  - High. The accepted history shows exact Coriolis treatment matters, and DFI
    is intended to initialize the model actually used for the forecast.
- Rollback complexity:
  - Low to moderate. Remove one option, one factory/export, one registry entry,
    and focused DFI tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_dfi_coriolis`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_dfi_coriolis --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    the Strang incumbent, clean diagnostics, and no fixed RMSE guardrail
    failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_dfi_coriolis --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the current
    DFI/rollout operator mismatch is not a material remaining error source.
    Any fast nonfinite result would indicate an incorrect reversible split.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` uses the
  accepted symmetric exact Coriolis split for the positive rollout, while DFI
  falls back to a full-physics equation when a Coriolis split is enabled.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  implements Lanczos digital filter initialization with forward and backward
  model integrations.
- History: `.logbook/history/2026-06-18_03-03-20_exact-coriolis-rotation-split/decision.md`
  and `.logbook/history/2026-06-18_04-38-06_symmetric-coriolis-rotation-split/decision.md`
  accepted exact and symmetric Coriolis rollout splits with validation gains.
- History: `.logbook/history/2026-06-18_00-44-09_vorticity-preserving-dfi-increment/decision.md`
  rejected a DFI increment edit, so this proposal changes the DFI model
  operator rather than post-filtering vorticity increments.
- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM Model Using a
  Digital Filter. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Strang, G. 1968. On the Construction and Comparison of Difference Schemes.
  SIAM Journal on Numerical Analysis. https://doi.org/10.1137/0705041
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of the accepted Coriolis proposals because those changed
only the positive-time rollout ordering. It is also not a duplicate of the
rejected vorticity-preserving DFI increment: this proposal does not mask or
preserve a subset of DFI increments, and it does not remove rotational balance
from DFI. It retargets the DFI integration operator so it remains consistent
with the accepted Strang incumbent.

## Evaluator Notes

### 2026-06-18T06:07:51Z

Decision: move to `ready`; rank 1 of active ideas.

Source inspection confirms the mechanism is real. The accepted Strang incumbent
sets `angular_velocity=0.0` for the positive rollout when an exact Coriolis
split is enabled, but `adapter._trajectory_function` deliberately rebuilds the
DFI equation with the original `physics_specs` and original diffusion filter.
That means the current initialized state is filtered under a different Coriolis
operator than the one used by the scored rollout.

This is the best next implementation because it is a narrow consistency test on
top of two accepted Coriolis rollout changes. It is not a duplicate of rejected
DFI partial-state ideas: dry DFI, passive-humidity bypass, and
vorticity-preserving DFI merges were clean but neutral or negative because they
changed which state components DFI filtered. This proposal instead uses DFI to
initialize the same split dynamics that the forecast now uses.

Important implementation risk: the backward DFI leg must apply the exact
Coriolis rotation with the opposite signed time step. A same-sign rotation in
both legs would break the reversible balance argument and could create an
artificial inertial phase bias. Keep the incumbent Strang rollout unchanged and
add focused tests proving older split models keep the unsplit DFI path.
