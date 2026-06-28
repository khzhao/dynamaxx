---
schema_version: 1
slug: geostrophic-sparing-boundary-layer-drag
title: Add Weak Geostrophic-Sparing Boundary-Layer Drag
status: staging
created_at: 2026-06-19T17:59:18Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Add Weak Geostrophic-Sparing Boundary-Layer Drag

## Hypothesis

The incumbent has weak thermal Held-Suarez relaxation but no active lower-boundary
momentum sink: `DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY` is zero and the accepted
10 m wind improvement is output-diagnostic only. A full Rayleigh drag risks
over-damping balanced large-scale flow, but a weak lower-layer drag that damps
only the diagnosed ageostrophic component should remove unresolved
boundary-layer momentum error while preserving the geostrophic pressure-wind
balance that controls MSLP and Z500.

## Mechanism

Preserve the incumbent initialization, DFI, weak thermal relaxation, horizontal
diffusion, exact Coriolis Strang split, theta tendency, theta recentering,
semi-implicit off-centering, Richardson 10 m diagnostic, output variables, and
fixed evaluation protocol.

Add an opt-in positive-time step filter such as
`apply_geostrophic_sparing_boundary_layer_drag`. The filter should operate only
after the main dynamics step, not inside DFI initialization, unless the
Implementer finds that reusing the ordinary filter list is necessary for code
simplicity and records that choice.

For each positive-time inner step:

- convert modal vorticity/divergence to nodal wind;
- estimate a lower-layer geostrophic wind from the current log-surface-pressure
  gradient and layer temperature scale, with a strict no-op taper where
  `abs(f)` is below a fixed tropical threshold;
- cap diagnosed geostrophic speed to a broad physical range, for example
  `0..80 m s^-1`, and fall back to the raw wind wherever diagnostics are
  nonfinite;
- damp only the ageostrophic wind `wind - geostrophic_wind` in lower sigma
  layers, with a fixed taper from full strength at the lowest layer to zero by
  about sigma `0.70`;
- use exact exponential damping with a weak lowest-layer timescale, for example
  `3..5` days, so the first implementation is a conservative source term rather
  than a high-complexity PBL solver;
- convert the adjusted wind back to modal vorticity/divergence while leaving
  temperature, log-surface-pressure, and passive tracers unchanged.

No heating return is included in the first candidate. That keeps the experiment
decorrelated from staged dissipative-heating proposals and makes wind/mass
movement easier to interpret.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model name extending the incumbent with an
    `_geostrophic_sparing_bl_drag` suffix.
- API changes:
  - None. The forecast contract remains unchanged.
- Tests to update:
  - Unit-test that the filter leaves temperature, log surface pressure, and
    tracers unchanged.
  - Verify no-op behavior near the equator, with nonfinite pressure-gradient
    diagnostics, and when geostrophic speed caps are exceeded.
  - Verify the lower-layer taper damps `wind - wind_geostrophic` but leaves a
    wind exactly equal to the bounded geostrophic estimate unchanged.
  - Add registry and non-JIT smoke tests.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` from day 2 onward if unresolved lower-boundary
    drag is part of the remaining low-level wind bias.
  - `mean_sea_level_pressure` may improve modestly if damping ageostrophic
    near-surface convergence reduces spurious pressure tendencies without
    weakening geostrophic flow.
- Expected neutral metrics:
  - `geopotential_500` should be nearly neutral because the source is confined
    to low sigma layers and avoids direct thermal or pressure changes.
  - `2m_temperature` should move less than wind because no drag heating is
    returned in the first candidate.
- Possible regressions:
  - Early 10 m wind can regress if the approximate geostrophic estimate is poor.
  - MSLP can regress if damping ageostrophic wind suppresses real cyclone
    development or frontal convergence.

## Risks

- Numerical stability:
  - Low to moderate. Exact exponential damping is stable, but wind-to-vorticity
    conversion and pressure-gradient diagnostics must be guarded carefully.
- Compute cost:
  - Small. It adds one wind transform pair and a few nodal operations per inner
    step, still practical under the fixed `--workers 4` evaluation.
- Data leakage:
  - None. The filter uses only the candidate trajectory state and fixed physical
    constants.
- Physical plausibility:
  - Moderate. Boundary-layer drag is physically expected, but this is a reduced
    ageostrophic drag, not a full turbulent closure with roughness, heat flux,
    or vertical diffusion.
- Rollback complexity:
  - Low to moderate. The filter is isolated behind one adapter flag and one
    registry entry.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early `10m_u_component_of_wind` or MSLP guardrail failure,
    and wind improvement that is not offset by mass-field degradation.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` and the same
    guardrail cleanliness.
- Outcome that would falsify the hypothesis:
  - A negative wind or MSLP movement would show that the current low-level wind
    errors are better handled diagnostically than through even weak prognostic
    drag. A clean near-zero delta would suggest full boundary-layer drag is not
    worth pursuing without additional thermodynamic coupling.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` sets
    `DEFAULT_WEAK_HELD_SUAREZ_KF_PER_DAY = 0.0`, so the accepted weak
    Held-Suarez path does not currently add lower-layer momentum friction.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_16-27-03_wind-sparing-held-suarez-relaxation/decision.md`
    accepted weak thermal relaxation while keeping wind drag off, motivating a
    separate conservative momentum-only experiment.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_17-23-29_surface-layer-richardson-wind-diagnostic/decision.md`
    shows low-level wind remains a high-leverage target when changes are
    tightly bounded.
  - ECMWF OpenIFS physical-process documentation lists surface exchange and
    turbulent mixing as subgrid parameterizations in global models:
    https://confluence.ecmwf.int/display/OIFS/3.2%2BOpenIFS%3A%2BPhysical%2BProcesses
  - ECMWF IFS Documentation Part IV, Physical Processes, documents boundary-layer
    turbulent diffusion and 10 m wind/friction-velocity diagnostics:
    https://www.ecmwf.int/sites/default/files/2023-06/Part-IV-Physical-Processes.pdf
  - Beljaars, A. C. M. and Holtslag, A. A. M. 1991. Flux parameterization over
    land surfaces for atmospheric models. Journal of Applied Meteorology.
    https://journals.ametsoc.org/view/journals/apme/30/3/1520-0450_1991_030_0327_fpolsf_2_0_co_2.xml
  - Rasp, S. et al. 2024. WeatherBench 2: A benchmark for the next generation of
    data-driven global weather models. Journal of Advances in Modeling Earth
    Systems. https://doi.org/10.1029/2023MS004019

## Researcher Notes

This is not a duplicate of staged `exponential-boundary-layer-rayleigh-drag`.
That idea damps the full low-level wind. This proposal explicitly preserves the
bounded geostrophic component and damps only the ageostrophic residual, which is
the mechanism intended to protect MSLP and Z500.

It is also not a duplicate of staged `surface-drag-theta-dissipation` or
`offcenter-damping-theta-energy-return`; this first candidate intentionally does
not return dissipated kinetic energy as heat. If the wind-only experiment
promotes but introduces thermal drift, an energy-return follow-up would be a
separate proposal.

## Evaluator Notes

### 2026-06-19T18:03:28Z

Decision: move to `staging`; ranked 3 of 3 fresh proposals.

The mechanism is physically motivated and improves on staged
`exponential-boundary-layer-rayleigh-drag` by attempting to spare the balanced
geostrophic component rather than damping the full low-level wind. It is not a
duplicate of that staged Rayleigh-drag idea, and it could teach whether the
remaining low-level wind error is ageostrophic and prognostic rather than a
diagnostic representativeness problem.

Do not promote it to `ready` now. It changes prognostic vorticity/divergence
every positive-time inner step, requires approximate geostrophic reconstruction
from the surface-pressure gradient, and can perturb the pressure-wind balance
that the accepted off-centered SIL3 incumbent just improved. The recent
theta-consistent implicit-gravity rejection shows that finite balance-related
operator changes can still cause large MSLP and wind guardrail failures, and
the current rubric specifically penalizes prognostic drag likely to disturb
MSLP/Z500.

This should remain behind bounded output diagnostics and more isolated
numerical tests. If promoted later, the no-op tropical taper, speed cap,
ageostrophic-only damping identity test, and unchanged temperature/log-pressure
guarantees need strong unit coverage, and the first implementation should use
a single conservative timescale rather than any sweep.
