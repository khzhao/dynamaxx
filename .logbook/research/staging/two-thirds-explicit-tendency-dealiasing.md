---
schema_version: 1
slug: two-thirds-explicit-tendency-dealiasing
title: Apply Two-Thirds Dealiasing to Explicit Primitive-Equation Tendencies
status: staging
created_at: 2026-06-18T07:23:54Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Apply Two-Thirds Dealiasing to Explicit Primitive-Equation Tendencies

## Hypothesis

The incumbent remains a spectral-transform primitive-equation model with
explicit nonlinear tendencies. A prior smooth exponential explicit-tendency
cleanup was stable and slightly positive but sub-threshold, so aliasing-like
numerical noise may be real but not sufficiently addressed by that smooth
filter.

An Orszag-style two-thirds modal cutoff applied only to explicit
primitive-equation tendencies is a stronger and more interpretable anti-aliasing
mechanism. It should remove quadratic high-wavenumber aliasing from nonlinear
tendencies while preserving the accepted Strang Coriolis split, state diffusion
filter, DFI, weak Held-Suarez forcing, initialization, outputs, and fixed
protocols.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_two_thirds_dealias`.
Preserve all incumbent options except a new explicit-tendency de-aliasing flag.

Implement a small equation wrapper around the base primitive equation before
weak Held-Suarez composition:

- call the incumbent primitive equation's `explicit_terms`;
- multiply modal tendency leaves with the horizontal modal shape by a fixed
  triangular/spherical total-wavenumber mask that keeps modes at or below
  `floor(2 * L / 3)` and zeros higher modes;
- leave nonmodal leaves, scalar leaves, `sim_time`, and unmatched tracer
  structures unchanged;
- preserve the primitive equation's existing `implicit_terms` and
  `implicit_inverse` exactly;
- compose the accepted weak Held-Suarez thermal forcing after this wrapper so
  the analytic large-scale forcing is not the object of the de-aliasing test;
- use the same wrapped equation in DFI and positive-time rollout.

This differs from changing horizontal diffusion strength: the state after a
step is not additionally damped. Only the explicit nonlinear tendencies passed
to the IMEX solver are de-aliased.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast input/output variables, lead times, metrics, and protocols
    stay fixed.
- Tests to update:
  - Unit-test the two-thirds mask for total-wavenumber cutoff behavior and
    preservation of low modes.
  - Unit-test the explicit-tendency wrapper on a synthetic state, verifying
    high modal tendencies are removed while implicit terms and inverse are
    identical to the wrapped equation.
  - Verify weak Held-Suarez composition still returns tracer-safe tendencies.
  - Verify the candidate factory preserves all Strang incumbent flags except
    the new de-aliasing flag.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind`, `geopotential_500`, and
    `mean_sea_level_pressure` at medium and long leads if aliased nonlinear
    tendency energy is feeding phase or amplitude drift.
  - Primary score may improve more than the prior smooth tendency filter because
    the two-thirds rule is a sharper aliasing-control mechanism.
- Expected neutral metrics:
  - Early `2m_temperature` should remain close to the incumbent because
    initialization, weak-HS forcing, and near-surface residual correction are
    unchanged.
- Possible regressions:
  - A sharp cutoff may remove useful resolved near-truncation tendencies and
    make the forecast too diffusive.
  - If the prior smooth filter's small positive signal exhausted the aliasing
    benefit, this stronger mask may be clean but still sub-threshold.

## Risks

- Numerical stability:
  - Low to moderate. The mask is stabilizing in form, but a sharp tendency
    cutoff can alter nonlinear phase and amplitude.
- Compute cost:
  - Low. The implementation is a modal mask multiplication on explicit
    tendencies and should fit the reported `--workers 4` resource policy.
- Data leakage:
  - None. The mask uses only grid geometry and no truth fields, fitted
    coefficients, validation artifacts, or golden data.
- Physical plausibility:
  - Moderate to high as a spectral numerical-method change. It is not a new
    physical parameterization and not a diffusion-strength sweep.
- Rollback complexity:
  - Low. Remove one wrapper/flag, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_two_thirds_dealias`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_two_thirds_dealias --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`
    against the Strang incumbent, clean diagnostics, no early day 1-5 RMSE
    guardrail failure, and no variable+lead guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_two_thirds_dealias --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that nonlinear
    aliasing is not a material remaining error source. A wind or Z500 guardrail
    failure would show that the sharp cutoff is too intrusive for this
    incumbent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  exposes IMEX stepping and equation composition; `adapter.py` currently builds
  the base primitive equation and weak-HS composed equation before stepping.
- History: `.logbook/history/2026-06-17_21-16-05_nonlinear-tendency-exponential-dealiasing/decision.md`
  rejected smooth explicit-tendency exponential filtering as clean but
  sub-threshold with iteration delta `+0.0007881219001772966`.
- Patterson, G. S. and Orszag, S. A. 1971. Spectral Calculations of Isotropic
  Turbulence: Efficient Removal of Aliasing Interactions. Physics of Fluids.
  https://doi.org/10.1063/1.1693365
- Canuto, C., Hussaini, M. Y., Quarteroni, A., and Zang, T. A. 2007. Spectral
  Methods: Evolution to Complex Geometries and Applications to Fluid Dynamics.
  Springer. https://doi.org/10.1007/978-3-540-30728-0
- Hou, T. Y. and Li, R. 2007. Computing nearly singular solutions using
  pseudo-spectral methods. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2007.04.014

## Researcher Notes

This is a deliberate retargeting of the anti-aliasing family to preserve the
accepted Strang incumbent. It is not a duplicate of the rejected smooth
exponential tendency filter: that result is used as weak positive evidence that
the mechanism is stable but too small. The new proposal uses a standard
two-thirds truncation rule, which is a distinct and stronger spectral aliasing
control.

It is also distinct from active staged `symmetric-horizontal-diffusion-split`
and `fourth-order-imex-rk-rollout`: it does not move the state diffusion
operator, change diffusion strength, alter the time integrator, or change the
inner step.

## Evaluator Notes

### 2026-06-18T07:28:25Z

Decision: move to `staging`; rank as a high fallback, not ready.

The proposal is feasible and scientifically distinct from the rejected smooth
exponential tendency filter. Source inspection confirms the adapter builds a
primitive-equation object with separable `explicit_terms`, while modal axes and
modal masks are available from the horizontal grid. A two-thirds total
wavenumber cutoff is therefore implementable as an explicit-tendency wrapper
without changing the implicit inverse, DFI span, forcing, initialization, or
forecast API.

Keep it staged because prior evidence suggests this family is stable but small.
The closest scored experiment, nonlinear-tendency exponential dealiasing, was
clean and improved all early target-variable means, but its iteration delta was
only `+0.0007881219001772966`, below promotion. A sharper two-thirds cutoff is
a materially stronger mechanism, but it also risks removing useful resolved
near-truncation tendencies and behaving like extra diffusion. It should not
displace the sigma-native hydrostatic initialization, which has stronger
accepted-history support.

### 2026-06-18T08:53:53Z

Decision: keep in `staging`, now ranked below the new skew-symmetric scalar
advection proposal within the anti-aliasing family.

The sigma-native hydrostatic candidate has since failed, so that specific item
no longer outranks this proposal. However, the new skew-symmetric scalar
advection proposal is the cleaner first anti-aliasing follow-up because it
changes a discrete product identity instead of sharply zeroing near-truncation
tendencies. Both remain below the ready residual-rotation candidate.

Keep this staged as a simple, source-local fallback. The closest scored
evidence remains the smooth tendency filter: clean and slightly positive but
only `+0.0007881219001772966`. A two-thirds cutoff is more interpretable and
stronger, but it may behave like extra diffusion and remove useful resolved
near-truncation tendencies, so it should not be the next implementation.

### 2026-06-18T10:25:42Z

Decision: keep in `staging`; current staged rank 5.

This remains a feasible, source-local anti-aliasing fallback and is distinct
from the rejected smooth exponential tendency filter. However, the best direct
evidence is still only a clean subthreshold gain of
`+0.0007881219001772966`, and a sharp two-thirds cutoff is more likely than the
skew-symmetric scalar-advection idea to remove useful near-truncation resolved
tendencies.

Keep it below the skew form and below the lower-surface initialization,
diagnostic, and operator-splitting candidates. It should be selected only if
future diagnostics or failed fallbacks make aliasing control the most plausible
remaining mechanism.

### 2026-06-18T11:49:28Z

Decision: keep in `staging`, staged fallback rank 5.

The ranking is unchanged within the anti-aliasing group. It remains simpler
than the new momentum-skew proposal but less attractive than scalar
skew-symmetry because a sharp two-thirds cutoff may remove useful resolved
near-truncation tendencies. Keep it as the direct, easy-to-implement spectral
fallback if structural scalar advection is not selected.

### 2026-06-18T13:22:44Z

Decision: keep in `staging`, staged fallback rank 5.

The two-thirds mask remains a feasible fallback, but the new evidence does not
justify promoting a sharper damping-like tendency cutoff. It stays below the
skew-symmetric scalar-advection proposal because that test is structural rather
than an explicit removal of high-mode tendencies, and it stays above broader
operator rewrites because it is source-local and easy to roll back.
