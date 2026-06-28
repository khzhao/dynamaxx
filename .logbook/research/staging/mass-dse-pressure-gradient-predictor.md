---
schema_version: 1
slug: mass-dse-pressure-gradient-predictor
title: Time-Center the Pressure Gradient with a Mass-DSE Thermal Predictor
status: staging
created_at: 2026-06-24T05:12:55Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
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

# Time-Center the Pressure Gradient with a Mass-DSE Thermal Predictor

## Hypothesis

The accepted mass-DSE branch improves thermodynamic transport, but the explicit
momentum pressure-gradient product in `curl_and_div_tendencies` still uses the
start-of-step temperature anomaly. This can leave the pressure-gradient force
slightly out of phase with the improved half-step thermal transport, especially
for baroclinic waves where thermal gradients and pressure gradients should
co-evolve.

A bounded half-step temperature predictor derived from the accepted mass-DSE
horizontal thermal tendency should time-center the explicit pressure-gradient
product without changing the thermodynamic update itself. This tests a
momentum/thermal coupling, not another DSE conversion, pressure-thickness
correction, or hydrostatic inversion.

## Mechanism

Register a side-by-side candidate such as `dino_mass_dse_pgf_pred` derived from
`dino_hsl2_mass_dse`.

For the candidate only:

- preserve the accepted mass-DSE HSL thermal tendency and selected modal
  temperature tendency;
- diagnose only the horizontal mass-DSE temperature tendency already computed
  before adding vertical theta transport and adiabatic pressure work;
- form a pressure-gradient predictor
  `T_pg = T_start + 0.5 * dt * dT_dt_horizontal_mass_dse`, with a fixed finite
  per-step temperature-increment cap used only as a safety guard;
- use `T_pg - T_ref` in the `R T' grad(log ps)` pressure-gradient product inside
  `curl_and_div_tendencies`;
- leave absolute-vorticity fluxes, vertical momentum advection, kinetic energy,
  log-surface-pressure tendency, thermal tendency, tracers, forcing, filters,
  outputs, and protocols unchanged;
- fall back exactly to the incumbent pressure-gradient product if the predictor
  or capped increment is nonfinite.

This is a local time-centering experiment for the explicit pressure-gradient
term. It does not add any pressure-thickness tendency, does not solve
`(Cp I + G)`, and does not alter the accepted DSE-HSL trajectory.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
- Registry changes:
  - Add one side-by-side factory and registry key for `dino_mass_dse_pgf_pred`.
- API changes:
  - None.
- Tests to update:
  - Verify disabled selector leaves incumbent pressure-gradient tendencies
    unchanged.
  - Verify zero mass-DSE horizontal predictor leaves the pressure-gradient
    product unchanged.
  - Verify finite synthetic predictors change only the pressure-gradient
    product and not scalar transport, log pressure, or kinetic energy helpers.
  - Verify nonfinite predictors fall back to incumbent behavior.
  - Verify candidate registration and unchanged forecast output variables.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 2-10 if pressure
    gradients are lagging the accepted mass-DSE thermal transport.
  - `10m_u_component_of_wind` if better balanced pressure gradients improve
    low-level wind phase without changing the surface diagnostic formula.
- Expected neutral metrics:
  - `2m_temperature` should remain close to incumbent because the thermal update
    and near-surface residual paths are unchanged.
- Possible regressions:
  - The explicit pressure-gradient product may already be empirically balanced
    with the start-of-step temperature.
  - Time-centering only one momentum term can create divergence/thermal
    mismatch and hurt early MSLP or Z500.

## Risks

- Numerical stability:
  - Moderate. The change touches vorticity/divergence tendencies that feed the
    semi-implicit step, so fast diagnostics and early pressure guardrails are
    critical.
- Compute cost:
  - Low to moderate. The predictor reuses mass-DSE diagnostics but may require
    a small refactor so the horizontal mass-DSE tendency is available before
    momentum tendencies are formed.
- Data leakage:
  - None. The predictor uses only current-step forecast tendencies.
- Physical plausibility:
  - Moderate to high. Time-centering nonlinear source terms is standard in
    semi-implicit atmospheric schemes, but this is a partial local predictor.
- Rollback complexity:
  - Moderate. Remove one selector, predictor plumbing, factory/export, registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_mass_dse_pgf_pred`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_mass_dse_pgf_pred --workers 4`
  - Support requires primary delta at least `+0.002` against cached
    `dino_hsl2_mass_dse`, clean diagnostics, and no fixed RMSE guardrail
    failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_mass_dse_pgf_pred --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta would show that the
    incumbent pressure-gradient timing is not a material remaining error source.
    Any early MSLP, Z500, or wind guardrail failure would show the predictor is
    less balanced than the incumbent product.

## Citations

- Dynamaxx source: `PrimitiveEquationsSigma.curl_and_div_tendencies` in
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` forms the
  explicit `R T' grad(log ps)` pressure-gradient product.
- Dynamaxx source: `temperature_tendency_potential_temperature_form` in the
  same file contains the accepted mass-DSE horizontal thermal tendency that the
  predictor would reuse.
- Dynamaxx history:
  `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted mass-DSE transport and provides the current incumbent.
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Durran, D. R. 2010. *Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics*, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2

## Researcher Notes

This proposal is decorrelated from the latest failed mass-DSE follow-ups. It
does not apply the rejected pressure-thickness product rule and does not invert
mass-DSE tendencies through the hydrostatic operator. It also differs from
staged `pressure-gradient-product-dealiasing`, which damps high-wavenumber
pressure-gradient products; this candidate leaves spectral content intact and
changes only the temperature time level used by the explicit product.

The prior `hydrostatic-inverted-mass-dse-hsl` MSLP guardrail failure is a
warning that pressure/mass balance is fragile. The reason this remains a
separate researchable idea is that it alters the momentum pressure-gradient
timing, not the thermal DSE-to-temperature conversion or pressure thickness.

## Evaluator Notes

### 2026-06-24T05:16:50Z

Decision: move to `staging`; rank 2 of 3 new proposals.

This is a coherent and potentially useful follow-up because it targets a
different coupling than the latest rejected mass-DSE variants: the explicit
`R T' grad(log ps)` pressure-gradient product, not pressure-thickness
correction or hydrostatic inversion. Time-centering a nonlinear source with a
bounded half-step mass-DSE thermal predictor has a plausible path to improving
Z500/MSLP phase and possibly low-level wind without changing the thermal
trajectory itself.

Keep it staged rather than ready because pressure-gradient edits are a higher
risk surface than a local thermal-scalar substitution. Source inspection shows
`curl_and_div_tendencies` currently forms momentum tendencies before the
mass-DSE temperature branch returns its horizontal diagnostic, so the proposal
requires extra plumbing or duplicated diagnostics. Partial time-centering of
one momentum product can also introduce pressure/divergence mismatch, and the
latest hydrostatic-inverted mass-DSE run already showed early MSLP fragility.
Existing staged `pressure-gradient-product-dealiasing` is a related pressure
product experiment; this predictor is distinct and probably stronger, but not
enough to crowd the single ready slot.

Ranked recommendation: hold as the best staged pressure-gradient follow-up
behind `vertical-dse-transport-mass-hsl`. Promote only after the thermal-scalar
consistency test fails cleanly or diagnostics point specifically to
momentum/thermal phase lag. If promoted, fix the per-step predictor cap before
scoring and require exact incumbent fallback for nonfinite predictor fields.
