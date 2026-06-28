---
schema_version: 1
slug: column-neutral-weak-hs-heating-split
title: Split Weak Held-Suarez Heating into Column-Neutral Compensation
status: staging
created_at: 2026-06-20T02:44:49Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/held_suarez.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Split Weak Held-Suarez Heating into Column-Neutral Compensation

## Hypothesis

The accepted weak Held-Suarez relaxation is important for `2m_temperature`
skill, and a prior mass-neutral/global-mean variant failed because it removed
too much useful thermal forcing. However, the incumbent still shows growing
MSLP and Z500 errors with lead. A weak thermal relaxation that adds or removes a
net dry-static-energy tendency in each column can improve screen temperature
while also creating column-thickness drift that later appears in mass-field
targets.

Preserving the accepted lower-column Held-Suarez tendency but compensating its
column-integrated dry thermal tendency aloft should keep the surface-temperature
benefit while reducing artificial column-thickness drift. This is a forcing
structure change, not a time-discretization tweak or a removal of the accepted
global thermal source.

## Mechanism

Register a side-by-side candidate extending the incumbent with a suffix such as
`column_neutral_weak_hs`. Preserve DFI, log-pressure and hydrostatic
initialization, exact Coriolis Strang split, theta tendency, theta mean
recentering, off-centered SIL3, Richardson 10 m wind diagnostic, scale-separated
surface residual memory, target variables, lead times, and fixed protocols.

For the candidate only, replace the weak Held-Suarez thermal forcing wrapper
with a column-neutral split:

- compute the incumbent weak Held-Suarez nodal temperature tendency exactly as
  today;
- define fixed lower-column layers, for example sigma centers greater than
  `0.70`, whose tendency is preserved unchanged because prior history shows the
  weak-HS surface thermal signal is valuable;
- compute the pressure- or sigma-thickness-weighted column integral of the
  preserved lower-column tendency plus the free-atmosphere tendency;
- subtract a compensating tendency only over free-atmosphere layers above the
  lower-column cutoff, weighted smoothly by layer thickness and capped per layer
  to avoid creating unrealistic upper-level heating;
- preserve the existing zero tendencies for vorticity, divergence,
  `log_surface_pressure`, and tracers;
- fall back to the incumbent weak-HS tendency wherever weights, compensation, or
  corrected tendency are nonfinite.

The fixed compensation should be local to each column, not a global layer-mean
subtraction. It should be disabled during no-HS models and should preserve the
incumbent weak-HS constants unless the Evaluator separately approves a different
candidate.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/held_suarez.py` if a reusable forcing
    subclass is cleaner than adapter-local code
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the column-neutral weak-HS candidate.
- API changes:
  - None. The public forecast contract and evaluation protocols remain fixed.
- Tests to update:
  - Unit-test that lower-column weak-HS tendencies are unchanged.
  - Unit-test that the weighted column-integral temperature tendency is near
    zero after compensation for finite synthetic columns.
  - Verify vorticity, divergence, `log_surface_pressure`, tracers, and
    `sim_time` tendencies remain zero in the forcing wrapper.
  - Verify compensation caps and finite fallback.
  - Verify the candidate factory preserves every incumbent option except the
    weak-HS forcing selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium and long leads if
    part of the remaining drift is artificial column heating or cooling from the
    weak-HS source.
  - `2m_temperature` should retain much of the accepted weak-HS benefit because
    the lower-column tendency is preserved and the accepted residual correction
    remains active.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be close to incumbent unless mass-field
    phase changes feed back into low-level winds.
  - Day-1 fields should move little because compensation is weak and capped.
- Possible regressions:
  - Free-atmosphere compensation can worsen Z500 if the incumbent's column
    heating was empirically correcting a thickness bias.
  - Removing column-integrated heating can reduce the accepted long-lead
    `2m_temperature` improvement if the surface benefit depends on whole-column
    thermal adjustment.

## Risks

- Numerical stability:
  - Low to moderate. The forcing remains thermal-only but changes vertical
    heating structure every step.
- Compute cost:
  - Low. It adds local vertical reductions and algebra to an existing forcing.
- Data leakage:
  - None. The compensation uses only the current forecast state, fixed sigma
    geometry, and fixed constants.
- Physical plausibility:
  - Moderate. Column energy compensation is a pragmatic dycore bias-control
    device; it is less physical than a real radiation or boundary-layer scheme
    but more constrained than unconserved Newtonian relaxation.
- Rollback complexity:
  - Low. Remove one forcing option/subclass, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta would show that column-net
    weak-HS heating is not the remaining mass-field error source. Any early
    `2m_temperature` guardrail failure would show the compensation removes too
    much of the accepted surface thermal benefit.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-16_16-27-03_wind-sparing-held-suarez-relaxation/decision.md`
  accepted weak Held-Suarez relaxation with a large iteration improvement.
- Dynamaxx history:
  `.logbook/history/2026-06-17_23-29-54_mass-neutral-weak-hs-forcing/decision.md`
  rejected removing the accepted global-mean weak-HS thermal source after
  `2m_temperature` guardrail failures, so this proposal preserves lower-column
  forcing and compensates only aloft.
- Dynamaxx history:
  `.logbook/history/2026-06-18_01-58-44_exact-weak-hs-thermal-split/decision.md`
  found exact time integration of weak-HS forcing neutral, motivating a change
  to vertical forcing structure rather than source time discretization.
- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP and
  climate models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016
- CESM Held-Suarez documentation summarizes the simple relaxation and lower
  boundary drag setup used for dry dynamical-core experiments.
  https://www.cesm.ucar.edu/models/simple/held-suarez

## Researcher Notes

This is not a duplicate of `mass-neutral-weak-hs-forcing`: that candidate
removed a global-mean weak-HS thermal source and damaged `2m_temperature`.
This proposal preserves the lower-column tendency and compensates locally aloft
to reduce column-thickness drift. It is also distinct from
`theta-consistent-held-suarez-forcing` and `exact-weak-hs-thermal-split`, which
changed thermodynamic variable consistency or time integration rather than the
vertical distribution of net column heating.

## Evaluator Notes

### 2026-06-20T02:48:14Z

Decision: move to `staging`; plausible but not the best next experiment.

This is sufficiently distinct from the rejected `mass-neutral-weak-hs-forcing`
to preserve. That failed candidate removed the accepted layerwise global-mean
weak-HS thermal source and produced a large negative iteration delta with
`2m_temperature` guardrail failures. The fresh proposal keeps the lower-column
weak-HS tendency and compensates only aloft within each column, so it tests a
different and more constrained vertical-distribution hypothesis rather than a
repeat of global source removal. It also targets a real remaining concern:
column-integrated thermal forcing can influence thickness, Z500, and MSLP.

Keep it staged because it is materially riskier and less isolated than the
ready residual-decay proposal. Weak-HS source details have mixed local evidence:
the original weak-HS relaxation was strongly accepted, exact source time
integration was clean but far below threshold, and removing the accepted
thermal mean damaged 2 m temperature. This proposal changes the positive-time
thermal forcing structure every step and could spend near-surface temperature
margin or disrupt hydrostatic thickness if the accepted column heating is
empirically correcting a bias. If promoted later, the implementation should use
fixed lower-column cutoffs and compensation caps, preserve lower-column weak-HS
tendencies exactly, and unit-test the weighted column integral and finite
fallback against the incumbent forcing.
