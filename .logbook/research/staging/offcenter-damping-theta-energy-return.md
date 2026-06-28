---
schema_version: 1
slug: offcenter-damping-theta-energy-return
title: Return Off-Centered Gravity-Wave Damping Loss as Theta Heating
status: staging
created_at: 2026-06-19T10:11:34Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
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

# Return Off-Centered Gravity-Wave Damping Loss as Theta Heating

## Hypothesis

The accepted off-centered SIL3 incumbent improved mass fields by adding
controlled damping to fast gravity-wave modes. That damping is numerically
useful, but it is also an energy sink. The accepted scoring notes show the main
remaining cost is modest late `2m_temperature`, while MSLP and Z500 improved
strongly. A small, conservative return of diagnosed off-centering energy loss to
dry theta-compatible heat may preserve the mass-field damping benefit while
reducing late lower-column cold drift.

This proposal does not weaken the accepted off-centering and does not tune its
epsilon. It keeps the dissipative fast-mode control and tests whether the
unreturned energy sink is part of the remaining thermal error.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_theta_energy_return`.
Preserve the incumbent initialization, DFI, weak-HS forcing, exact symmetric
Coriolis split, horizontal diffusion, theta tendency, theta layer-mean
recentering, stability-aware residual correction, Richardson 10 m wind
diagnostic, output variables, splits, lead times, metrics, and the accepted
off-centered positive-time solver.

For the candidate only, add an optional positive-time energy-return wrapper:

- build the usual off-centered SIL3 raw dynamics step and a centered SIL3 raw
  dynamics step with the same equation and time step;
- during positive-time rollout only, compute both raw next states before
  horizontal diffusion, theta recentering, and exact Coriolis post-filters;
- estimate dry column energy in the centered and off-centered raw next states
  using forecast surface pressure, sigma layer mass weights, wind kinetic energy,
  and dry thermal energy;
- define nonnegative damping loss as the centered-minus-off-centered dry energy
  difference, clipped to a fixed small per-step heating cap;
- distribute that loss as a local theta-compatible temperature increment over
  the layers where the damping loss is diagnosed, with finite fallback to zero
  heating;
- use the off-centered next state plus the bounded heating increment as the
  state passed to the incumbent filters and symmetric Coriolis split;
- leave DFI centered/off-centered behavior unchanged from the current incumbent
  so this proposal isolates positive-time energy accounting;
- leave log surface pressure, vorticity, divergence, tracers, output packing,
  and residual correction unchanged except through the local heat increment.

The centered step is used only as an energy diagnostic, not as a forecast-state
blend. The forecast state remains the accepted off-centered trajectory plus a
bounded heat return.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` if a reusable
    dual-step helper is cleaner than adapter-only wiring
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast input/output contract, target variables, lead times, and
    fixed evaluation protocols remain unchanged.
- Tests to update:
  - Unit-test dry energy diagnostics on synthetic states and verify zero loss
    produces zero heating.
  - Unit-test nonnegative clipping, per-step cap, finite fallback, and
    theta-compatible temperature conversion.
  - Verify the centered raw step is used only for energy diagnostics and that
    the forecast state keeps off-centered divergence/log-pressure behavior.
  - Verify DFI, weak-HS, theta recentering, Coriolis split, and residual
    correction flags match the incumbent.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at days 5 to 15 if the accepted off-centering introduced a
    small cumulative thermal energy sink.
  - `geopotential_500` may stay improved or improve slightly if thickness errors
    from over-damping are reduced without restoring fast gravity-wave noise.
- Expected neutral metrics:
  - `mean_sea_level_pressure` should retain most accepted off-centered gains
    because the gravity-wave damping itself is not removed.
  - `10m_u_component_of_wind` should be close to neutral unless lower-column
    heating changes stability enough to affect the accepted Richardson
    diagnostic.
- Possible regressions:
  - Heating can degrade MSLP/Z500 through thickness changes if the energy
    estimate includes physical balanced evolution rather than only numerical
    damping.
  - Running a centered diagnostic step increases cost and may expose JIT memory
    pressure.

## Risks

- Numerical stability:
  - Moderate. The heat increment is nonnegative, capped, and finite-guarded, but
    it changes the positive-time thermal state every inner step.
- Compute cost:
  - Moderate. The raw dynamics step is evaluated twice for the candidate, though
    output volume, lead count, resolution, and worker count are unchanged. The
    reported four idle L4 GPUs and `--workers 4` envelope should handle one
    such candidate, but runtime should be monitored.
- Data leakage:
  - None. The correction uses only two model-internal candidate states from the
    same forecast time step and fixed constants.
- Physical plausibility:
  - Moderate. Energy fixers and frictional-heating treatments are common in
    atmospheric modeling, but attributing centered/off-centered energy
    differences exactly to removable heat is an approximation.
- Rollback complexity:
  - Low to moderate. Remove one wrapper/helper, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_theta_energy_return`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_theta_energy_return --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no early or variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_theta_energy_return --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that off-centering's
    energy sink is not a material remaining thermal error source. Any MSLP or
    Z500 guardrail failure would show the heat return disrupts the balance that
    made off-centering successful.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
    implements the accepted off-centered SIL3 tableau as a row-sum-preserving
    shift of implicit weight toward current stages.
  - Dynamaxx history:
    `.logbook/history/2026-06-19_06-50-50_offcentered-semi-implicit-gravity-wave/scoring_notes.md`
    records large MSLP and Z500 improvements from off-centering and modest late
    `2m_temperature` regression.
  - Dynamaxx research:
    `.logbook/research/staging/theta-diffusion-dissipative-heating.md` and
    `.logbook/research/staging/surface-drag-theta-dissipation.md` cover
    diffusion and drag heating; this proposal instead targets energy loss from
    the accepted semi-implicit off-centering.
  - Becker, E. 2003. Frictional Heating in Global Climate Models. Monthly
    Weather Review.
    https://doi.org/10.1175/1520-0493(2003)131%3C0508:FHIGCM%3E2.0.CO;2
  - Thuburn, J. 2008. Some Conservation Issues for the Dynamical Cores of NWP
    and Climate Models. Journal of Computational Physics.
    https://doi.org/10.1016/j.jcp.2006.08.016
  - Simmons, A. J. and Temperton, C. 1997. Stability of a Two-Time-Level
    Semi-Implicit Integration Scheme for Gravity Wave Motion. Monthly Weather
    Review. https://doi.org/10.1175/1520-0493(1997)125%3C0600:SOATTL%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of staged horizontal-diffusion or surface-drag heating.
Those proposals return energy removed by explicit filters or physical drag. This
one is only meaningful after the accepted off-centered SIL3 incumbent, because
its diagnosed energy source is the difference between centered and off-centered
semi-implicit gravity-wave treatment.

It is also not an off-centering epsilon tune. The accepted damping remains
unchanged; the proposal adds an energy-accounting repair for the thermal cost
that appeared after the large mass-field gain. If selected, the Implementer
should keep the cap fixed before evaluation and avoid any iteration-driven
constant search.

## Evaluator Notes

### 2026-06-19T10:15:47Z

Decision: move to `staging`; ranked 3 of 3 new proposals.

This is scientifically defensible but too broad for the immediate next
experiment. It targets a real remaining signal from the accepted off-centered
run, namely modest late `2m_temperature` degradation after large mass-field
improvements, and it is distinct from staged diffusion- and drag-heating ideas
because the diagnosed source is the centered-minus-off-centered SIL3 energy
difference.

The risk and cost are materially higher than the centered-DFI split. The
candidate would run both centered and off-centered raw dynamics steps during
every positive-time inner step, then estimate dry column energy and inject
bounded theta-compatible heating into the prognostic state. That diagnostic can
confound physical balanced evolution with numerical damping loss, and even a
capped positive heat source can perturb thickness, MSLP, and Z500 enough to
spend the guardrail margin that made off-centering successful. Keep it staged
as a later fallback if narrower off-centering follow-ups fail cleanly or if
diagnostics continue to implicate a cumulative thermal energy sink.
