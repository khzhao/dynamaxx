---
schema_version: 1
slug: balanced-pv-thermal-consistency-filter
title: Balanced PV Thermal Consistency Filter
status: staging
created_at: 2026-06-26T03:50:40Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
expected_eval_protocols:
  - leaderboard standard iteration evaluation with 4 workers against the valid incumbent cache
  - standard validation rerun only if the iteration score improves and guardrails pass
---

## Hypothesis

The incumbent has already recovered a large score gain from pressure-ramped vertical dry-static-energy transport, but the rejected follow-ups show that changing the vertical-DSE timing, cap, or hydrostatic-work gate is a high-risk path, especially for early 2 m temperature. A bounded free-tropospheric dry-PV consistency filter should instead protect the balanced baroclinic structure that controls 500 hPa height, MSLP, and low-level winds while leaving the boundary layer and vertical-DSE schedule effectively unchanged.

This proposal targets a different failure mode from the recent vertical-DSE experiments: spurious free-tropospheric thermal increments that are dynamically inconsistent with the model's vorticity and static-stability evolution. It should reduce balanced height-pressure drift without injecting or removing near-surface heat.

## Mechanism

Add an opt-in step filter after the existing dynamics and filters for a new model variant such as `dino_hsl2_mass_dse_wtg_vdse_ramp_pvtherm`. For each outer step, diagnose a dry Ertel-PV proxy in sigma pressure coordinates:

`q_dry ~= (absolute_vorticity) * d(theta) / dp`

using the previous and candidate next states. Then isolate the low-horizontal-mode, free-tropospheric part of the thermodynamic increment, for example over a smooth sigma mask centered on roughly 0.25-0.80 and tapering to zero below the lower troposphere. Where that increment would produce a sharp, sign-inconsistent low-mode PV tendency, multiplicatively taper only the responsible low-mode potential-temperature increment. Preserve layer means, keep the correction column-neutral in dry-static-energy units, and cap the per-step temperature change well below the accepted vertical-DSE cap.

The filter should not change vorticity, divergence, log surface pressure, tracers, the vertical-DSE ramp, or the WTG relaxation. Boundary-layer sigma levels should be excluded so that the mechanism directly avoids the early T2m damage seen in the failed vertical-DSE spinup and hydrostatic-work-gated runs.

## Implementation Scope

- Add a boolean configuration field to the Dinosaur adapter for the new PV-thermal consistency filter, defaulting to false.
- Implement a finite, vectorized helper in `primitive_equations.py` that accepts previous and candidate next prognostic states plus coordinates, then returns a corrected candidate next state.
- Reuse existing spectral truncation or modal-filter utilities where available so the filter acts only on broad balanced structures rather than gridscale noise.
- Register a single new factory name derived from the incumbent, leaving existing factories and outputs untouched.
- Add focused tests for no-op behavior with vertically uniform theta, preservation of boundary-layer temperature increments, finite output under weak static stability, and strict disablement when the flag is false.

## Expected Metric Movement

Expected movement is modest but decorrelated from the accepted vertical-DSE gain: small improvement in `geopotential_500`, `mean_sea_level_pressure`, and `10m_u_component_of_wind`, with neutral to slightly positive `2m_temperature` because the filter avoids the lower boundary layer. A plausible iteration-score gain is +0.002 to +0.012 if the current incumbent's late-lead balanced drift is partly caused by thermally inconsistent free-tropospheric increments.

## Risks

- A dry PV proxy ignores humidity and frictional diabatic sources, so an overly aggressive limiter could suppress real baroclinic growth.
- If the low-mode projection is too broad, it may damp useful accepted HSL and vertical-DSE thermal transport.
- If the sigma mask leaks into the boundary layer, it could repeat the recent early T2m guardrail failures.
- The implementation needs conservative finite-value fallbacks around weak static stability and polar grid geometry.

## Evaluation Plan

Use the existing standard leaderboard protocol and the valid incumbent cache. Run the new variant against `dino_hsl2_mass_dse_wtg_vdse_ramp` with 4 workers. Reject immediately if any early day-1-through-day-5 guardrail regresses materially, with special scrutiny on `2m_temperature`. If iteration improves, run the standard validation comparison and inspect per-lead `geopotential_500`, `mean_sea_level_pressure`, and `10m_u_component_of_wind` to confirm the gain is broad rather than a single-lead artifact.

## Citations

- Local accepted baseline: `.logbook/history/2026-06-25_12-52-40_pressure-ramped-vertical-dse-wtg`, which accepted `dino_hsl2_mass_dse_wtg_vdse_ramp` with a +0.03880190339341674 iteration-score delta and clean diagnostics.
- Local rejection evidence: `.logbook/history/2026-06-25_17-17-23_baroclinic-mode-vertical-dse-spinup`, `.logbook/history/2026-06-25_21-06-21_late-lead-vertical-dse-cap-release`, and `.logbook/history/2026-06-26_00-40-18_hydrostatic-work-gated-vertical-dse`, which argue against more vertical-DSE timing, cap, or hydrostatic-work variants.
- Hoskins, B. J., McIntyre, M. E., and Robertson, A. W. (1985). "On the use and significance of isentropic potential vorticity maps." Quarterly Journal of the Royal Meteorological Society. https://doi.org/10.1002/qj.49711147002
- Haynes, P. H. and McIntyre, M. E. (1987). "On the evolution of vorticity and potential vorticity in the presence of diabatic heating and frictional or other forces." Journal of the Atmospheric Sciences. https://doi.org/10.1175/1520-0469(1987)044%3C0828:OTEOVA%3E2.0.CO;2
- Jablonowski, C. and Williamson, D. L. (2006). "A baroclinic instability test case for atmospheric model dynamical cores." Quarterly Journal of the Royal Meteorological Society. https://doi.org/10.1256/qj.06.12

This is not a duplicate of the prior PV and balance ideas because it does not apply a PV stability floor, vorticity-gradient filter, Rossby-wave-source correction, thermal-wind initialization, vertical-DSE cap, vertical-DSE timing change, or hydrostatic-work gate. It is a narrow post-step thermal-increment consistency limiter, excludes the boundary layer by design, and specifically addresses the recent evidence that direct lower-column thermal changes damage early T2m.

## Evaluator Notes

### 2026-06-26T03:55:51Z

Decision: move to `staging`; ranked 2 of 2 reviewed proposals.

The proposal is scientifically coherent and implementable as a side-by-side
step-filter variant: the adapter already supports rollout filters, and the
incumbent has reusable sigma-pressure, theta, vorticity, and low-mode masking
utilities. It also targets more than one scored channel and deliberately avoids
the boundary layer, so it should not be discarded as a duplicate of the
rejected vertical-DSE timing, cap, or hydrostatic-work experiments.

Stage rather than ready because it is still a positive-time prognostic thermal
filter with several under-specified constants and decisions: the PV-tendency
sign test, weak-static-stability fallback, low-mode taper strength,
column-neutral DSE redistribution, and per-step cap all need to be fixed before
scoring. Local evidence is cautionary: the baroclinic-mode vertical-DSE spinup
failed early `2m_temperature`, the hydrostatic-work gate failed all early
guardrails with severe T2m damage, and the scrapped free-tropospheric PV
stability-floor idea was rejected for a similar dry-PV-filter risk profile
without read-only diagnostics. Promote only after a diagnostic sidecar shows
frequent incumbent low-mode free-tropospheric PV/thermal inconsistency and
after the exact thresholds are predeclared.
