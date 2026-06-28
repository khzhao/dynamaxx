---
schema_version: 1
slug: absolute-vorticity-hsl-momentum
title: Transport Absolute Vorticity with the Accepted HSL2 Departure
status: staging
created_at: 2026-06-23T18:04:37Z
author_role: Researcher
target_model: dino_hsl2_theta_dse_hsl
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Transport Absolute Vorticity with the Accepted HSL2 Departure

## Hypothesis

The accepted thermodynamic DSE-HSL change improved broad skill without changing
momentum advection. A remaining error source may be phase drift in rotational
flow: the primitive-equation vorticity tendency still uses the existing local
Eulerian product of absolute vorticity and wind. Prior absolute-vorticity flux
dealiasing was clean but effectively neutral, which suggests a small product
filter is too weak. A materially different test is to transport absolute
vorticity itself along the already accepted HSL2 departure path.

If rotational structures are slightly displaced relative to the improved DSE
thermal field, a bounded HSL absolute-vorticity tendency could improve
`10m_u_component_of_wind`, MSLP gradients, and downstream Z500 phase without
touching pressure-work, terrain, or HSL trajectory geometry.

## Mechanism

Register a side-by-side model such as `dino_hsl2_theta_dse_vort_hsl` that
inherits all incumbent behavior.

For the candidate only:

- compute nodal absolute vorticity `eta = zeta + f` from the diagnostic state;
- remove a layerwise area mean before remap so the candidate does not inject a
  spurious global vorticity offset;
- use the existing accepted HSL2 midpoint departure helper to remap `eta'`;
- convert `(eta'_departure - eta') / dt` to a modal vorticity tendency and blend
  it only into the rotational part of `curl_and_div_tendencies`;
- leave divergence, kinetic-energy, pressure-gradient, thermal, tracer, weak-HS,
  and output-diagnostic paths unchanged;
- finite-fallback exactly to the incumbent momentum tendency if the HSL
  vorticity diagnostics are invalid.

This is intentionally not a new departure-point experiment. The trajectory is
the accepted HSL2 midpoint estimate already used by the incumbent thermal
transport.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests in `tests/dycore/models/dinosaur/test_primitive_equations.py`
    and `tests/dycore/test_registry.py`
- Registry changes:
  - Add a side-by-side model factory for the candidate.
- API changes:
  - None.
- Tests to update:
  - Verify incumbent vorticity/divergence tendencies are bitwise unchanged when
    the option is disabled.
  - Verify zero-wind states fall back or produce zero HSL vorticity tendency.
  - Verify the area-mean absolute-vorticity anomaly is not changed by the helper.
  - Verify non-rotational tendencies are unchanged by the option.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at early and medium leads if rotational phase
    error is a remaining momentum error after DSE-HSL.
  - `mean_sea_level_pressure` and `geopotential_500` if improved rotational
    phase keeps synoptic pressure systems better aligned.
- Expected neutral metrics:
  - `2m_temperature` should be mostly neutral because thermal DSE-HSL and
    surface residuals remain incumbent.
- Possible regressions:
  - Divergence/rotational imbalance can hurt MSLP and Z500 quickly, especially
    at 24-120 h.
  - Semi-Lagrangian interpolation may overdamp small-scale vorticity even with
    an area-mean anomaly guard.

## Risks

- Numerical stability:
  - Moderate to high. Momentum tendencies are sensitive, and the candidate
    changes the rotational tendency every inner step.
- Compute cost:
  - Moderate. It adds HSL remaps for one scalar per layer; no new evaluations or
    external data are required.
- Data leakage:
  - None.
- Physical plausibility:
  - Plausible as a material-vorticity transport test, but incomplete because
    divergence and pressure-gradient tendencies remain Eulerian.
- Rollback complexity:
  - Low to moderate. Remove one option, helper, factory/export, registry entry,
    and tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_theta_dse_vort_hsl`
  - Require clean diagnostics before iteration.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_theta_dse_vort_hsl --workers 4`
  - Support requires primary delta at least `+0.002`, zero diagnostic issues,
    and no fixed guardrail failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_theta_dse_vort_hsl --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A negative primary delta or short-lead `10m_u_component_of_wind`, MSLP, or
    Z500 guardrail regression would show that the incumbent Eulerian rotational
    tendency is better balanced than this partial HSL momentum treatment.

## Citations

- Dynamaxx source: `PrimitiveEquationsSigma.curl_and_div_tendencies` in
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` computes the
  existing absolute-vorticity/wind contribution to vorticity and divergence.
- Dynamaxx history:
  `.logbook/history/2026-06-20_05-39-53_absolute-vorticity-flux-dealiasing/decision.md`
  found narrow product dealiasing clean but subthreshold, motivating a stronger
  mechanism than a local taper.
- Dynamaxx history:
  `.logbook/history/2026-06-23_06-13-46_coriolis-centered-hsl-theta-departure/decision.md`
  rejected changing the HSL departure geometry, so this proposal reuses the
  accepted departure unchanged.
- Arakawa, A. and Lamb, V. R. 1981. A Potential Enstrophy and Energy
  Conserving Scheme for the Shallow Water Equations. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0018:APEAEC%3E2.0.CO;2
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Thuburn, J. 2008. Some Conservation Issues for the Dynamical Cores of NWP
  and Climate Models. Journal of Computational Physics, 227, 3715-3730.
  https://doi.org/10.1016/j.jcp.2006.08.016

## Researcher Notes

This proposal is decorrelated from the accepted DSE-HSL thermal scalar: it
targets rotational momentum phase rather than thermodynamic thickness. It is
not another HSL theta trajectory variant, not qmono/Picard/Coriolis-centered
departure work, and not a contract-changing ensemble. It also differs from the
rejected absolute-vorticity flux dealiasing candidate, which only filtered a
local product and did not materially change transport.

## Evaluator Notes

### 2026-06-23T18:45:00Z

Decision: move to `staging`; ranked 3 of 3 current proposals.

The idea is plausible enough to preserve because it targets a different
remaining error source than the accepted DSE-HSL thermal transport. Reusing the
accepted HSL2 departure and keeping the forecast contract fixed are positives,
and the prior absolute-vorticity flux-dealiasing run was clean rather than
unstable. This proposal is also materially stronger than that rejected local
product filter, so it is not a simple duplicate.

Keep staged rather than ready because the risk-to-benefit ratio is weaker than
the thermal DSE follow-up. Replacing part of the rotational tendency with a
semi-Lagrangian absolute-vorticity tendency changes momentum balance every
inner step while leaving divergence, pressure-gradient, and mass tendencies on
the incumbent path. That partial momentum treatment could quickly damage
short-lead MSLP, Z500, or 10 m wind guardrails. Recent nearby evidence also
raises the bar: absolute-vorticity dealiasing was subthreshold, and
Coriolis-centered/HSL trajectory variants were effectively neutral.

If this is revisited after lower-risk thermal candidates are exhausted, the
implementation should remain side-by-side, use the incumbent momentum tendency
as an exact finite fallback, prove non-rotational tendencies are unchanged, and
watch early 10 m wind, MSLP, and Z500 guardrails before spending validation
compute.
