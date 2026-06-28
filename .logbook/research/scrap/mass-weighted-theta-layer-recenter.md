---
schema_version: 1
slug: mass-weighted-theta-layer-recenter
title: Mass-Weighted Theta Layer Recenter
status: scrap
created_at: 2026-06-27T01:48:57Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Mass-Weighted Theta Layer Recenter

## Hypothesis

The accepted theta layer-mean recentering filter preserves an area-weighted
layer mean of dry potential temperature. The current incumbent also uses
layer-mass-weighted DSE horizontal transport and a pressure-ramped vertical-DSE
increment. In that setting, preserving an area-weighted theta mean can leave a
small mass-weighted dry entropy/heat-content drift when surface pressure varies.
A side-by-side recentering filter that preserves the pressure-thickness weighted
layer mean theta should better match the current mass-DSE formulation and reduce
large-scale pressure/thickness drift without changing the forecast API.

## Mechanism

Register a side-by-side candidate named
`dino_hsl2_mass_dse_wtg_vdse_ramp_mwtheta`. Preserve every incumbent setting
except the weighting used by `_theta_layer_mean_recenter_step_filter`.

For the candidate:

- compute layer pressure thickness from each state's sigma pressure field;
- use `quadrature_weights * layer_pressure_thickness` to compute previous and
  next layer-mean theta;
- compute the same uniform per-layer temperature increment as the incumbent
  recentering filter, but target the mass-weighted theta mean;
- fall back to the incumbent area-weighted recentering if pressure thickness,
  pressure, theta, or weights are nonfinite or degenerate;
- keep the filter rollout-only, and keep DFI, WTG, vertical-DSE ramping,
  residual corrections, target variables, lead times, and scoring unchanged.

This is not another vertical-DSE amplitude or cap experiment. It changes the
global thermal invariant used by the already accepted recentering filter.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only `dino_hsl2_mass_dse_wtg_vdse_ramp_mwtheta`.
- API changes:
  - None.
- Tests to update:
  - Area-weighted and mass-weighted paths match when surface pressure is
    horizontally uniform.
  - Candidate preserves the pressure-thickness weighted layer mean theta.
  - Candidate falls back to incumbent area-weighted behavior for nonfinite or
    degenerate pressure thickness.
  - Factory, registry, and finite non-JIT smoke coverage.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` through improved
    hydrostatic/mass consistency.
  - Possible small `2m_temperature` gains if lower-layer heat-content drift is
    reduced.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because the mechanism does not directly change
    the wind diagnostic.
- Possible regressions:
  - The accepted area-weighted theta recentering may be a better numerical
    stabilizer than the mass-weighted invariant, especially over steep pressure
    gradients.
  - A uniform layer correction still changes temperature broadly, so even a
    physically better invariant can hurt early T2m if the pressure field is
    biased.

## Risks

- Numerical stability:
  - Low to moderate. The correction is uniform per layer and finite-guarded, but
    it changes a globally applied thermal filter.
- Compute cost:
  - Low. It adds pressure-thickness reductions to an existing filter.
- Data leakage:
  - None.
- Physical plausibility:
  - High. Mass-weighted layer means are the natural finite-volume invariant in
    pressure/sigma coordinates.
- Rollback complexity:
  - Low.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_mwtheta`
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_mwtheta --workers 4`
  - Support requires primary delta at least `+0.002` with clean diagnostics and
    fixed RMSE guardrails.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_mwtheta --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show that the accepted
    area-weighted recentering is already the better practical invariant for
    this forecast model.

## Citations

- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review, 109, 758-766.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Arakawa, A. and Lamb, V. R. 1977. Computational design of the basic dynamical
  processes of the UCLA general circulation model. Methods in Computational
  Physics, 17, 173-265.
  https://doi.org/10.1016/B978-0-12-460817-7.50009-4
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

The accepted incumbent now combines theta recentering with later mass-DSE and
WTG mechanisms. This proposal asks whether the older recentering invariant
should be updated to the same pressure-thickness weighting convention, without
changing vertical-DSE strength, WTG support, or fixed evaluation protocols.

## Evaluator Notes

### 2026-06-27T01:52:04Z

Decision: move to `scrap`.

This is a direct mechanism duplicate of
`.logbook/history/2026-06-21_06-24-25_mass-weighted-theta-recentering`, which
replaced the accepted area-weighted theta recentering moment with a
surface-pressure/mass-weighted layer-theta moment. That candidate passed tests
and diagnostics but scored `-0.5155611533781376` versus incumbent
`-0.5150627015910243`, an iteration delta of `-0.0004984517871132743`, and
the decision record concluded that the accepted area-weighted recentering was
empirically better.

The current incumbent has since added mass-DSE, WTG, and ramped vertical-DSE
mechanisms, but the proposed invariant replacement is the same evaluated
operation. Recent mass-consistency refinements also provide weak or negative
evidence: `mass-centered-dse-anomaly-hsl` was safe but only
`+0.000026881174071430314`, far below promotion, and multiple vertical-DSE
refinements after the accepted ramp were negative. Repeating the rejected
theta-moment replacement is therefore not a good use of a fixed iteration run.
