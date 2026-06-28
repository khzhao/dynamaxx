---
schema_version: 1
slug: convective-momentum-column-mixing
title: Bounded Convective Momentum Column Mixing
status: scrap
created_at: 2026-06-28T13:50:38Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Bounded Convective Momentum Column Mixing

## Hypothesis

The incumbent contains thermal WTG and DSE machinery for tropical adjustment,
but it does not represent convective momentum transport. In deep convection,
unresolved updrafts and downdrafts redistribute horizontal momentum vertically,
altering vertical shear, low-level winds, and downstream balanced height fields.
A bounded, mass-conserving column momentum mixer activated only by a convective
proxy can improve `10m_u_component_of_wind` and possibly MSLP/Z500 without
adding latent heating, changing target variables, or using the failed
momentum-only semi-Lagrangian vertical-advection mechanism.

## Mechanism

Add one side-by-side candidate, for example `dino_ri2m_cmt`, derived from the
current incumbent.

For this candidate only:

- preserve the incumbent HSL mass-DSE transport, WTG thermal relaxation,
  pressure-ramped vertical-DSE increment, T2m memory, RI2m diagnostic, weak-HS
  forcing, DFI, ocean heat flux, and output contract;
- after each positive-time dynamics step, reconstruct nodal horizontal wind
  from vorticity and divergence;
- compute a convective proxy from low-level convergence, lower-tropospheric
  relative humidity, and conditional-instability or moist-static-energy
  contrast; if humidity is unavailable or invalid, the mixer is an exact no-op;
- apply a smooth tropical-to-subtropical latitude taper and activate only where
  the proxy exceeds a fixed threshold;
- mix wind anomalies vertically toward a column mass-weighted mean over a fixed
  lower-to-mid-tropospheric layer, conserving column mass-weighted horizontal
  momentum at each grid point;
- cap the per-step wind increment and suppress the filter when static stability,
  pressure thickness, wind, or transformed modal fields are nonfinite;
- write only the momentum increment back to vorticity/divergence, leaving
  temperature, `log_surface_pressure`, tracers, final T2m formulas, MSLP
  diagnostics, and pressure-level interpolation unchanged;
- exclude the filter from time-reversed DFI so initialization remains on the
  accepted balanced path.

This is a parameterized convective vertical momentum redistribution, not a
semi-Lagrangian vertical advection scheme and not boundary-layer drag.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` only if shared
    pressure-thickness or humidity-diagnostic helpers are needed
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one short side-by-side model key, such as `dino_ri2m_cmt`.
- API changes:
  - None. Forecast inputs, output variables, lead times, metrics, and protocols
    remain unchanged.
- Tests to update:
  - Verify missing humidity, zero convergence, and inactive latitude weights
    reproduce the incumbent exactly.
  - Verify the vertical mixing conserves column mass-weighted `u` and `v`.
  - Verify only vorticity/divergence change after wind reconstruction and that
    temperature, `log_surface_pressure`, and tracers remain unchanged.
  - Verify per-step wind caps and finite fallback.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium leads if unresolved convective momentum
    redistribution is a remaining source of low-level wind error.
  - `mean_sea_level_pressure` and `geopotential_500` at days 5-15 if improved
    tropical and subtropical momentum structure reduces balanced phase drift.
- Expected neutral metrics:
  - `2m_temperature`, because the proposal does not change final T2m blending,
    lower-boundary heat fluxes, or thermal tendencies.
  - Day 1-3 fields, because the filter is capped, positive-time only, and
    activated only by the convective proxy.
- Possible regressions:
  - Momentum mixing can weaken real vertical shear and degrade Rossby-wave
    propagation or storm-track phase.
  - The dry dycore's passive humidity and convergence may be an imperfect
    convective proxy, making the activation noisy.

## Risks

- Numerical stability:
  - Moderate. The operation is damping and column-conservative, but it edits
    prognostic momentum every active positive-time step.
- Compute cost:
  - Low to moderate. It adds wind reconstruction, local column reductions, and
    one wind-to-vorticity/divergence conversion per inner step; this should be
    practical for `--workers 4`.
- Data leakage:
  - None. The proxy uses only forecast state, fixed masks, fixed thresholds, and
    initialization-time inputs already available to the incumbent.
- Physical plausibility:
  - Moderate. Convective momentum transport is a real parameterized process in
    NWP, but this proposal is a reduced deterministic mixer without an explicit
    convective mass-flux closure.
- Rollback complexity:
  - Low to moderate. Remove one selector/filter, optional helper functions, one
    factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_cmt`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_cmt --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached
    `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`, clean diagnostics, no early
    day-1-through-day-5 RMSE guardrail failure, and no variable-lead guardrail
    failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_cmt --workers 4`
    only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A fast or iteration nonfinite failure would show the wind reconstruction or
    proxy is too risky. A clean near-zero or negative iteration delta would show
    convective momentum redistribution is not a material remaining score
    source. Any early wind, MSLP, or Z500 guardrail failure would show the
    mixer disrupts balanced flow.

## Citations

- Dynamaxx history:
  `.logbook/history/2026-06-28_06-42-52_momentum-only-sl-vertical-advection/decision.md`
  rejected a momentum-only semi-Lagrangian vertical-advection candidate after
  152 nonfinite forecast issues, so this proposal avoids semi-Lagrangian
  vertical transport and uses capped column mixing with finite fallback.
- Dynamaxx history:
  `.logbook/history/2026-06-26_22-40-51_moisture-convergence-gated-wtg-dse/decision.md`
  is negative evidence for another moisture-convergence-gated thermal WTG
  change; this proposal uses convective diagnostics only for momentum mixing.
- Gregory, D., Kershaw, R., and Inness, P. M. 1997. "Parametrization of momentum
  transports by convection. II: Tests in single-column and general circulation
  models." Quarterly Journal of the Royal Meteorological Society.
  https://doi.org/10.1002/qj.49712354103
- Moncrieff, M. W. and Klinker, E. 1997. "Organized convective systems in the
  tropical western Pacific as a process in general circulation models."
  Quarterly Journal of the Royal Meteorological Society.
  https://doi.org/10.1002/qj.49712354010
- Kuang, Z. 2015. "A strategy for representing the effects of convective
  momentum transport in multiscale models." Journal of Advances in Modeling
  Earth Systems. https://doi.org/10.1002/2014MS000417
- ECMWF Technical Memorandum, "The parametrization of convective momentum
  transports in the ECMWF model: Evaluation using cloud resolving model data",
  documents CMT testing in an operational-model context.
  https://www.ecmwf.int/sites/default/files/elibrary/1996/9644-parametrization-convective-momentum-transports-ecmwf-model-evaluation-using-cloud-resolving.pdf

## Researcher Notes

This is not a duplicate of the failed `momentum-only-sl-vertical-advection`
candidate: it does not compute departure points, does not advect momentum with
`sigma_dot_full`, excludes DFI, conserves column momentum locally, and caps each
increment. It is not a boundary-layer Richardson or Rayleigh drag proposal,
because it redistributes momentum vertically in convective columns rather than
removing low-level momentum. It is also not the staged EP-flux zonal momentum
redistribution idea, which remains under-specified in sign and proxy; this uses
a local convective proxy and should be evaluated independently.

It explicitly avoids recent negative evidence: it does not retune the weak
Eady heat-flux filter, does not touch MSLP/surface-pressure ratios, does not
blend final-output T2m, and does not add another WTG thermal gate.

## Evaluator Notes

### 2026-06-28T13:53:42Z

Decision: move to `scrap`; ranked 2 of 2 fresh proposals.

Convective momentum transport is a real NWP/GCM parameterization family:
Gregory, Kershaw, and Inness 1997 and later CMT-in-multiscale-model work
support the scientific premise that deep convection can vertically redistribute
horizontal momentum.
That literature does not make this reduced operator ready in the current
Dynamaxx queue. The proposed activation depends on passive humidity,
low-level convergence, and conditional-instability proxies in a dry dycore with
no explicit convective mass-flux or precipitation closure, then writes a new
prognostic momentum increment back through vorticity/divergence transforms after
each positive-time step.

Local evidence argues against spending the next fixed evaluation slot on this
version. A momentum-only semi-Lagrangian vertical-advection candidate recently
failed iteration with 152 nonfinite forecast issues, and a
moisture-convergence-gated WTG/DSE change was clean but essentially neutral.
More importantly, the research queue already contains staged and better
controlled momentum-redistribution ideas, especially
`richardson-column-momentum-mixing` and `richardson-momentum-mixing`, plus the
staged EP-flux zonal-momentum proposal pending diagnostic evidence. This
proposal overlaps that family while adding a noisier convective proxy and a
larger implementation/test surface.

Scrap rather than stage to avoid carrying another column-momentum mixer until
diagnostics first show that convective-region vertical shear, not generic
boundary-layer shear or jet/wave momentum exchange, is a material incumbent
error. The front-matter `target_model` was normalized to the protocol schema
value `dinosaur`; if this idea is revived later, it should return as a narrower
diagnostic-driven CMT proposal with a predeclared proxy, layer range, momentum
invariant, and no overlap with the staged Richardson-column mixer.
