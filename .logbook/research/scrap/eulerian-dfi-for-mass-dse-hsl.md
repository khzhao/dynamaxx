---
schema_version: 1
slug: eulerian-dfi-for-mass-dse-hsl
title: Eulerian DFI for Mass-DSE HSL Rollout
status: scrap
created_at: 2026-06-24T22:43:00Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Eulerian DFI for Mass-DSE HSL Rollout

## Hypothesis

Digital-filter initialization is meant to remove fast initialization noise by
filtering short forward and backward integrations. The current incumbent
rollout uses horizontal semi-Lagrangian thermal transport and the accepted
layer-mass DSE HSL branch. Those are useful in positive time, but the DFI
initializer is a time-symmetric filtering procedure and may not benefit from
running the same semi-Lagrangian/DSE transport path in both the forward and
time-reversed short integrations.

A side-by-side candidate that keeps the accepted HSL/DSE rollout unchanged but
uses the pre-HSL Eulerian theta-form thermal equation inside DFI can test whether
DFI should remain closer to the reversible primitive-equation core while the
forecast rollout uses the accepted semi-Lagrangian DSE transport.

## Mechanism

Register one side-by-side candidate such as `dino_mass_dse_euler_dfi` derived
from `dino_hsl2_mass_dse`.

For the candidate only:

- preserve the positive-time rollout exactly: HSL2 midpoint departure,
  layer-mass DSE HSL thermal transport, ocean sensible heat flux exclusion from
  DFI, weak-HS analysis equilibrium, theta mean recentering, off-centered SIL3,
  exact Coriolis Strang split, residual corrections, outputs, and protocols;
- when constructing `digital_filter_initialization`, build the DFI equation with
  `use_horizontal_semilagrangian_theta_transport=False`,
  `use_midpoint_semilagrangian_theta_departure=False`,
  `use_dry_static_energy_hsl_transport=False`, and
  `use_layer_mass_weighted_dse_hsl_transport=False`, while preserving the
  incumbent theta-form tendency, weak-HS equilibrium offset, horizontal
  diffusion filters, DFI window, and timestep;
- do not change the lead-zero output contract: the filtered initial state still
  feeds the accepted `dino_hsl2_mass_dse` rollout;
- if the Eulerian-DFI output state is nonfinite, fall back to incumbent DFI.

Do not retune the DFI time span, cutoff, off-centering, or diffusion strength.
This is a fixed DFI-equation routing experiment, not a DFI parameter sweep.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` only if a
    cleaner constructor selector is needed
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests in `tests/dycore/models/dinosaur/test_primitive_equations.py`
    and `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model alias, for example `dino_mass_dse_euler_dfi`.
- API changes:
  - None.
- Tests to update:
  - Verify the candidate preserves every incumbent rollout flag and differs only
    by the DFI-equation selector.
  - Monkeypatch or inspect the DFI constructor path to prove the DFI equation
    disables HSL/DSE flags while rollout keeps them enabled.
  - Verify the ocean sensible heat flux remains excluded from DFI as in the
    accepted incumbent.
  - Verify nonfinite Eulerian-DFI output falls back to incumbent DFI.
  - Verify registry construction and a finite smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - Day-1 to day-5 `mean_sea_level_pressure` and `geopotential_500` if the
    time-reversed HSL/DSE DFI path currently introduces small imbalance before
    the accepted rollout begins.
  - `2m_temperature` if lower-column spinup is smoother after a more reversible
    thermal DFI equation.
- Expected neutral metrics:
  - Medium and late leads should remain close because the positive-time rollout
    is still the accepted `dino_hsl2_mass_dse` path.
  - `10m_u_component_of_wind` should be mostly neutral except through initial
    pressure/thermal balance.
- Possible regressions:
  - HSL/DSE inside DFI may already be beneficial because it filters the same
    thermal variable used by the rollout.
  - Prior DFI-routing experiments were weak or negative, so expected signal is
    modest.

## Risks

- Numerical stability:
  - Low to moderate. Eulerian DFI uses existing equation paths, but changing the
    filtered initial state can perturb early pressure balance.
- Compute cost:
  - Low. DFI span, timestep, and forecast length are unchanged.
- Data leakage:
  - None. Uses no verification or future data.
- Physical plausibility:
  - Moderate. Digital filtering is intended for balanced initialization, while
    semi-Lagrangian transport is primarily a positive-time advection strategy.
- Rollback complexity:
  - Low. Remove one selector/helper, factory/export, registry key, and focused
    tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_mass_dse_euler_dfi`.
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_mass_dse_euler_dfi --workers 4`.
  - Compare against cached `dino_hsl2_mass_dse` artifacts when valid.
  - Require primary-score delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_mass_dse_euler_dfi --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show HSL/DSE equation
    routing inside DFI is not a material remaining error source. An early
    MSLP/Z500 guardrail failure would show that matching DFI to rollout is more
    important than using the more Eulerian reversible core.

## Citations

- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM Model Using a
  Digital Filter. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Huang, X.-Y. and Lynch, P. 1993. Diabatic Digital-Filtering Initialization:
  Application to the HIRLAM Model. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1993)121%3C0589:DDFIAT%3E2.0.CO;2
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Dynamaxx history:
  `.logbook/history/2026-06-22_12-07-18_horizontal-semilagrangian-theta-transport/decision.md`,
  `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`,
  and `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted the positive-time HSL/DSE rollout path. This proposal preserves that
  path and changes only DFI equation routing.

## Researcher Notes

This is not a repeat of `dse-consistent-sigma-initialization`: that candidate
changed the pressure-to-sigma thermal initial condition before DFI, while this
candidate keeps initialization unchanged and changes only the short DFI equation.
It is also not another timestep or DFI-window proposal; the DFI span, cutoff,
and `900 s` step are fixed.

## Evaluator Notes

### 2026-06-24T22:15:03Z

Decision: move to `scrap`; ranked 3 of 3 new proposals.

This is implementable, but it is unlikely to beat the current incumbent under
the fixed gates. The mechanism is another DFI equation-routing experiment:
preserve the accepted positive-time HSL/mass-DSE rollout, but disable HSL and
DSE inside the short forward/backward DFI integrations. Prior local evidence is
consistently weak for this family. Removing weak-HS from DFI was effectively
neutral, signed Coriolis routing in DFI was clean but subthreshold, centered
DFI with off-centered rollout was near-neutral, DFI theta recentering was
slightly negative, and partial DFI state merges were rejected. Active staged
DFI-only mass and divergence cleanup proposals are already held back pending
diagnostic evidence.

The proposal's physical claim is plausible in the abstract because DFI targets
balanced initialization, but the candidate would intentionally make the DFI
thermal equation less consistent with the now-accepted rollout variable. There
is no current diagnostic evidence that the HSL/mass-DSE DFI path is injecting a
score-relevant imbalance, and the proposal itself expects modest early-lead
effects. That is too weak for another implementation slot after several clean
but subthreshold DFI routing outcomes.

Recommendation: do not implement. Revive only if future read-only diagnostics
show that DFI with HSL/mass-DSE specifically creates a measurable early MSLP or
Z500 imbalance that is absent under the Eulerian theta equation.

Prior DFI-routing history is mixed to negative (`dry-dfi-weak-hs-split`,
`coriolis-split-dfi-initialization`, `centered-dfi-offcenter-rollout`, and
`dfi-theta-mean-recenter`), so this should not outrank stronger rollout
mechanisms. The reason to keep it in proposals is that none of those tested the
new current mismatch between a semi-Lagrangian mass-DSE rollout and a
time-symmetric DFI equation.
