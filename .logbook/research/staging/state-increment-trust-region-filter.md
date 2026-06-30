---
schema_version: 1
slug: state-increment-trust-region-filter
title: Bounded State-Increment Trust-Region Filter
status: staging
created_at: 2026-06-30T05:34:31Z
author_role: Researcher
target_model: dino_ri2m_ekman_coupled
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

# Bounded State-Increment Trust-Region Filter

## Hypothesis

Recent history gives two useful constraints. The accepted Ekman closure shows
that small, capped post-step filters can move WeatherBench2 skill materially.
The failed `skew-adjoint-vertical-momentum-advection` run shows that an
unbounded core-momentum change can still produce nonfinite forecasts even when
local tendency fallbacks exist. A conservative post-step trust-region filter
should test the complementary idea: keep the incumbent equations intact, but
limit only rare, physically implausible single-step state increments before they
can seed nonlinear growth.

The hypothesis is that occasional outlier increments in wind, temperature, or
log surface pressure contribute to medium-lead phase and mass-field drift. A
fixed, generous, area-neutral limiter can damp those outliers without changing
normal resolved synoptic evolution.

## Mechanism

Register one side-by-side candidate such as `dino_ri2m_step_trust`, derived
from `ekman_coupled_dinosaur_dycore_model()`.

Add an opt-in final rollout step filter after the incumbent horizontal
diffusion, WTG, and coupled Ekman filters:

- compute `next_state - prev_state` after all incumbent filters have run;
- convert the momentum increment from vorticity/divergence to nodal `u/v`
  increment using the existing spherical-harmonic helper;
- apply generous fixed trust regions to the completed-step increments, for
  example max local wind-vector increment, max local temperature increment, and
  max log-surface-pressure increment per 900 s inner step;
- shrink only the excess part with a smooth bounded multiplier rather than hard
  replacing the state;
- preserve layerwise area means for temperature and global area mean for
  log-surface-pressure so the filter is not a mass or heat source;
- convert the limited wind increment back to vorticity/divergence and accept it
  only if the modal round trip is finite and does not increase global kinetic
  energy relative to the raw candidate step;
- include a breadth guard: if more than a small fixed fraction of grid points
  would be limited on any variable, no-op to the incumbent step, because broad
  clipping would indicate the caps are diagnosing normal dynamics rather than
  isolated outliers;
- leave tracers and `sim_time` unchanged except for normal incumbent evolution.

This is not a replacement vertical-advection operator, not another horizontal
diffusion-strength experiment, and not an exact mass-neutral Ekman projection.
It is a last-mile boundedness filter around completed state increments.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side key such as `dino_ri2m_step_trust`.
- API changes:
  - None. Forecast inputs, outputs, target variables, and fixed protocols
    remain unchanged.
- Tests to update:
  - Verify increments below the trust region reproduce incumbent output.
  - Verify local wind, temperature, and log-pressure outliers are reduced but
    finite and sign-preserving.
  - Verify temperature layer means and global log-pressure mean are preserved
    by the limiter.
  - Verify the kinetic-energy guard no-ops wind limiting when the round trip is
    nonfinite or energy-increasing.
  - Verify the breadth guard no-ops when a synthetic broad increment exceeds
    the cap over too much of the grid.
  - Verify candidate factory parity with `dino_ri2m_ekman_coupled` except for
    the trust-region selector and model name.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium and late leads if
    rare pressure or wind increment spikes seed balanced mass-field drift.
  - `10m_u_component_of_wind` if isolated wind-increment outliers are damped
    without weakening the accepted Ekman mean effect.
- Expected neutral metrics:
  - `2m_temperature` should be mostly neutral because the temperature limiter is
    generous, layer-mean preserving, and inactive on normal increments.
- Possible regressions:
  - If the incumbent's high-amplitude increments are physically necessary for
    synoptic development, the trust region can overdamp storms and reduce skill.
  - If the filter almost never activates, the score movement may be near
    roundoff and fail promotion cleanly.

## Risks

- Numerical stability:
  - Low to moderate. The operation is dissipative and finite-guarded, but it
    touches completed prognostic state increments each inner step.
- Compute cost:
  - Low to moderate. It adds two wind transform pairs and local reductions per
    step. The reported `--workers 4` resource envelope is sufficient for one
    candidate.
- Data leakage:
  - None. It uses only `prev_state`, `next_state`, fixed caps, fixed grid
    weights, and model constants.
- Physical plausibility:
  - Moderate. Trust-region limiters are numerical stabilization devices rather
    than a new physical parameterization, but the caps are stated in physical
    wind, temperature, and pressure units and preserve broad means.
- Rollback complexity:
  - Low. Remove one filter/helper branch, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_step_trust`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_step_trust --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached
    incumbent iteration primary `-0.16500618979404214`, clean diagnostics, and
    no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_step_trust --workers 4`
    only after iteration promotion.
  - Require validation delta at least `+0.001` against cached validation
    primary `-0.16591150807771451`.
- Outcome that would falsify the hypothesis:
  - Any fast nonfinite failure would falsify the safety argument. A clean
    negative or subthreshold iteration delta would show rare outlier increments
    are not a material remaining error source, or that limiting them removes
    useful dynamics. Early U10, MSLP, or Z500 guardrail failure would show the
    trust region is too intrusive.

## Citations

- Local positive evidence:
  `.logbook/history/2026-06-29_04-31-21_coupled-ekman-stress-pumping/decision.md`
  accepted a bounded post-step surface filter with clean diagnostics and large
  iteration/validation gains.
- Local negative evidence:
  `.logbook/history/2026-06-30_01-05-36_skew-adjoint-vertical-momentum-advection/decision.md`
  rejected an unbounded core vertical-momentum change after fast diagnostics
  reported nonfinite forecasts.
- Local negative evidence:
  `.logbook/history/2026-06-18_13-26-11_symmetric-horizontal-diffusion-split/decision.md`
  rejected changing diffusion placement, so this proposal is not a diffusion
  split or strength retune.
- Thuburn, J. 1996. "Multidimensional Flux-Limited Advection Schemes." Journal
  of Computational Physics. https://doi.org/10.1006/jcph.1996.0006
- Zalesak, S. T. 1979. "Fully Multidimensional Flux-Corrected Transport
  Algorithms for Fluids." Journal of Computational Physics.
  https://doi.org/10.1016/0021-9991(79)90051-2
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Jablonowski, C. and Williamson, D. L. 2006. "A Baroclinic Instability Test
  Case for Atmospheric Model Dynamical Cores." Quarterly Journal of the Royal
  Meteorological Society. https://doi.org/10.1256/qj.06.12

## Researcher Notes

This proposal is intentionally decorrelated from the Ekman spinup proposal:
it does not change the Ekman formula, activation time, mass projection,
roughness, depth, or thermal coupling. It also avoids the recent failed vertical
momentum family by leaving the primitive-equation tendency operator untouched.
Compared with staged divergence damping or pressure-only limiters, it is a
completed-step finite-increment guard with strict no-op and breadth guards,
designed to answer whether rare outlier increments remain a score-relevant
source of drift in the accepted incumbent.

## Evaluator Notes

### 2026-06-30T06:09:00Z

Decision: move to `staging`; plausible but not ready for the next
model-selection run.

The proposal has a coherent numerical-stability argument. Bounded/limited
transport methods are well established for controlling overshoots, and the
proposed finite guards, breadth no-op, mean preservation, and kinetic-energy
backstop are better motivated than the recently failed unbounded vertical
momentum experiment. It is also not an exact duplicate of the staged
`bounded-log-pressure-tendency-limiter` because it covers wind, temperature, and
log pressure after completed incumbent filters rather than only pressure
increments.

Keep it staged because the experiment is broad relative to the evidence. It
would touch completed prognostic increments for multiple state components every
inner step, add wind transform round trips, and introduce several fixed caps
without a diagnostic showing rare state-increment outliers are the remaining
limiting error source. Recent local history is cautionary: the skew-adjoint
vertical momentum candidate failed fast with nonfinite forecasts, while several
small pressure/Ekman refinements were stable but subthreshold. This trust-region
filter could easily be clean but near-neutral if it rarely activates, or
score-negative if it clips physically meaningful cyclogenesis, shear, or thermal
adjustment.

Promotion would require either evidence from read-only diagnostics that rare
single-step wind, temperature, or log-pressure increment tails are present in
the incumbent and correlate with MSLP/Z500/U10 errors, or exhaustion of narrower
ready ideas. If promoted later, narrow the first implementation to the minimum
state subset supported by diagnostics, fix all caps before scoring, and keep the
breadth/no-op and mean-preservation tests strict.
