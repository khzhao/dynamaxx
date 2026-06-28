---
schema_version: 1
slug: deformation-rate-momentum-damping
title: Add a Bounded Deformation-Rate Momentum Damping Split
status: staging
created_at: 2026-06-21T19:46:17Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add a Bounded Deformation-Rate Momentum Damping Split

## Hypothesis

The incumbent uses fixed spectral horizontal diffusion for all states. Recent
history shows that changing the vector projection of that fixed filter was
effectively neutral, and broad diffusion-strength/order changes have been
risky. A more physical missing closure may be deformation-rate damping: apply
extra momentum damping only where the resolved wind field has strong horizontal
strain, leaving weakly deformed planetary flow and thermal/mass fields on the
incumbent path.

This should target fronts and jet-exit shear zones that can create noisy wind
and pressure tendencies without retuning the globally applied diffusion curve.

## Mechanism

Register a side-by-side candidate suffix such as
`_deformation_damping`. Preserve the accepted DFI, weak-HS analysis-equilibrium
offset, Strang Coriolis split, theta tendency/recentering, offcentering, fixed
horizontal diffusion, Richardson 10 m wind diagnostic, and scale-separated
surface residual correction.

For positive-time rollout only, append a guarded step filter after the incumbent
horizontal diffusion and before the symmetric Coriolis half-step:

- diagnose nodal wind from vorticity/divergence;
- compute horizontal deformation magnitude from the symmetric strain tensor
  using existing spherical derivative operators and conservative polar guards;
- build a smooth damping coefficient that is zero below a fixed strain
  threshold and capped at a small fraction of local wind per 900 s step;
- damp only the ageostrophic/high-strain wind increment by converting the
  damped nodal wind back to vorticity/divergence;
- leave temperature, log surface pressure, tracers, weak-HS forcing, DFI, output
  interpolation, and near-surface residuals unchanged;
- fall back to the incumbent next state if any diagnosed field or reconstructed
  momentum state is nonfinite.

This is a local physical closure rather than a change to the spectral diffusion
law. The first implementation should use fixed, predeclared caps and no
validation tuning.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the incumbent plus
    deformation-rate damping.
- API changes:
  - None. Forecast inputs, outputs, lead times, metrics, and splits stay fixed.
- Tests to update:
  - Verify zero strain is exactly no-op.
  - Verify finite fallback on nonfinite strain or wind.
  - Verify the damping cap cannot reverse wind direction in one step.
  - Verify only vorticity/divergence leaves change.
  - Add registry coverage for the side-by-side model.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium and late leads if excessive resolved
    shear noise contributes to wind RMSE.
  - `mean_sea_level_pressure` and `geopotential_500` if noisy momentum
    deformation feeds pressure adjustment.
- Expected neutral metrics:
  - `2m_temperature` should remain close because thermal forcing and residual
    diagnostics are unchanged.
- Possible regressions:
  - Overdamping jet-exit regions can worsen synoptic phase and long-lead wind.
  - Any low-level damping may interact with the accepted Richardson 10 m wind
    diagnostic.

## Risks

- Numerical stability:
  - Moderate. The filter is capped and finite-guarded, but it reconstructs
    momentum from nodal winds every step.
- Compute cost:
  - Low to moderate. Extra wind transforms and derivative diagnostics are small
    relative to the rollout at the reported 48 CPU, 173 GiB RAM budget.
- Data leakage:
  - None. It uses only the forecast state and fixed constants.
- Physical plausibility:
  - Moderate to high. Deformation-dependent eddy viscosity is a standard closure
    idea, but this is a simple deterministic spectral-grid surrogate.
- Rollback complexity:
  - Low. Remove one flag/helper/factory/registry entry and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite diagnostics and zero issue count.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no fixed RMSE guardrail failure.
- Validation gate:
  - Run validation with `--workers 4` only after iteration promotion and require
    at least `+0.001` validation primary delta.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show strain-localized
    damping is not a material remaining error source. An early wind guardrail
    failure would show the damping is too intrusive.

## Citations

- Repository code: `src/dynamaxx/dycore/models/dinosaur/adapter.py:301`
  builds the incumbent fixed horizontal diffusion filter list, and
  `src/dynamaxx/dycore/models/dinosaur/adapter.py:350` applies filters around
  the accepted positive-time step.
- Repository code: `src/dynamaxx/dycore/models/dinosaur/adapter.py:1020`
  reconstructs nodal winds from vorticity/divergence for output, showing the
  required transform path already exists in the adapter.
- Repository history:
  `.logbook/history/2026-06-21_16-05-39_helmholtz-projected-momentum-diffusion/decision.md:24`
  found vector-projected fixed momentum diffusion effectively neutral, so this
  proposal changes the physical trigger rather than only the projection.
- Repository history:
  `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
  rejected broad diffusion-order changes after early wind degradation.
- Smagorinsky, J. 1963. General circulation experiments with the primitive
  equations. Monthly Weather Review.
- Lilly, D. K. 1967. The representation of small-scale turbulence in numerical
  simulation experiments. IBM Scientific Computing Symposium on Environmental
  Sciences.

## Researcher Notes

This is not a duplicate of staged `leith-nonlinear-eddy-viscosity`: Leith-style
viscosity keys off vorticity gradients/enstrophy-cascade structure, while this
proposal keys off the symmetric deformation tensor and damps momentum only in
strong strain. It is also not the rejected Helmholtz-projected diffusion, which
kept the incumbent diffusion coefficient and only changed vector projection.
The proposal deliberately avoids pressure-level output reconstruction, ensemble
outputs, metric changes, training, or evaluation-protocol changes.

## Evaluator Notes

### 2026-06-21T19:51:53Z

Decision: move to `staging`.

The proposal is scientifically plausible and distinct from the recently
rejected Helmholtz-projected momentum diffusion: it keys the extra damping to
resolved symmetric strain instead of only changing the vector projection of the
incumbent diffusion. It is also forecast-contract compliant, bounded, and
testable as a side-by-side candidate.

Do not promote it to `ready` for the next run. The active staging queue already
contains `leith-nonlinear-eddy-viscosity`, multiple boundary-layer momentum
closures, and Richardson-gated lower-layer momentum mixing. This proposal sits
in the same broad momentum-damping family and would require additional
wind-to-vorticity/divergence reconstruction every positive-time step. Recent
local evidence is also weak for momentum-filter changes: Helmholtz-projected
momentum diffusion was clean but effectively neutral, and broader diffusion
experiments have been risky. Keep it staged as a more targeted strain-triggered
alternative if the stronger Leith or boundary-layer hypotheses are exhausted or
if diagnostics specifically implicate high-strain wind noise.
