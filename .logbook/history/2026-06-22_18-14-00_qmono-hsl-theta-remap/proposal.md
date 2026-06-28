---
schema_version: 1
slug: qmono-hsl-theta-remap
title: Quasi-Monotone Remap for Horizontal Semi-Lagrangian Theta
status: ready
created_at: 2026-06-22T18:07:59Z
author_role: Researcher
target_model: dino_hsl2_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# Quasi-Monotone Remap for Horizontal Semi-Lagrangian Theta

## Hypothesis

The incumbent `dino_hsl2_theta` at commit
`72efada4e0afbd8e34e3184dbcef90cb91cc051c` improved the accepted horizontal
semi-Lagrangian dry-theta anomaly transport by using a midpoint departure
estimate. The current scalar remap is still bilinear. Bilinear interpolation is
robust, but it is also diffusive for smooth thermal gradients and fronts,
especially when applied every inner step over 15 forecast days.

A bounded quasi-monotone remap for the theta anomaly should keep the accepted
departure geometry and finite fallback while reducing interpolation diffusion.
The expected gain is sharper lower- and mid-tropospheric thermal phase, which
can project onto `geopotential_500`, `mean_sea_level_pressure`, and late
`2m_temperature` without changing momentum, pressure continuity, forcing,
surface residuals, or the fixed evaluation protocol.

## Mechanism

Add one side-by-side candidate with short alias `dino_hsl_qmono`.

For the candidate only:

- preserve the full `dino_hsl2_theta` stack: DFI, weak-HS analysis equilibrium,
  symmetric Coriolis split, theta tendency, theta mean recentering, SIL3
  off-centering, scale-separated near-surface residuals, land-sea surface
  residual, ocean bulk sensible heat flux, midpoint theta departure, output
  variables, lead schedule, and evaluation protocols;
- replace only the theta-anomaly scalar remap used by
  `horizontal_semilagrangian_theta_transport`;
- use a tensor-product monotone cubic Hermite or limited PCHIP-style remap in
  longitude and latitude, with periodic longitude handling and latitude
  boundary clipping matching the incumbent bilinear remap;
- bound every remapped value by the local stencil extrema before forming the
  theta tendency, so the candidate cannot introduce new theta extrema;
- keep the current bilinear remap as the exact fallback for nonfinite slopes,
  shape mismatch, boundary degeneracy, or nonfinite remapped theta;
- leave the existing midpoint departure displacement, CFL caps, zero-wind
  guard, first-order fallback, vertical theta transport, pressure-work term,
  momentum equations, log-pressure tendency, filters, and output packing
  unchanged.

This is not another local Eulerian/HSL blend. The accepted midpoint HSL
tendency remains the selected transport path; this proposal changes only the
interpolation order and boundedness of the theta remap used at the accepted
departure point.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one side-by-side model registered as `dino_hsl_qmono`.
- API changes:
  - None. `DycoreModel.forecast`, emitted variables, lead times, metrics,
    target variables, and WeatherBench2 splits remain fixed.
- Tests to update:
  - Verify constant and linear theta fields reproduce the bilinear remap to
    tolerance under valid midpoint departures.
  - Verify a synthetic sharp front remains bounded by local stencil extrema.
  - Verify the zero-wind path reproduces the incumbent theta tendency.
  - Verify nonfinite slope or remap diagnostics fall back to the accepted
    bilinear `dino_hsl2_theta` path.
  - Verify non-theta tendencies and all incumbent factory flags are unchanged.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 3 to 10 if repeated
    bilinear theta remapping is damping synoptic thermal gradients.
  - `2m_temperature` after near-surface residual memory decays, if lower-column
    theta fronts retain sharper phase.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because prognostic momentum, Coriolis splitting,
    and Richardson 10 m wind diagnosis are unchanged.
- Possible regressions:
  - The accepted bilinear remap may be providing useful diffusion. Reducing it
    could increase small-scale thermal variance and hurt early Z500/MSLP
    guardrails.
  - A higher-order remap costs more transforms/indexing work and can be brittle
    near polar rows unless the local-extrema limiter and bilinear fallback are
    strict.

## Risks

- Numerical stability:
  - Moderate. The change touches theta transport every inner step, but the
    candidate is bounded and falls back exactly to the accepted bilinear path.
- Compute cost:
  - Low to moderate. It adds local stencil and slope calculations for theta
    remapping only; grid size, lead count, and evaluation protocols are fixed.
- Data leakage:
  - None. It uses only current forecast state and fixed grid geometry.
- Physical plausibility:
  - High. Shape-preserving semi-Lagrangian interpolation is a standard way to
    reduce remap diffusion without allowing new extrema.
- Rollback complexity:
  - Low. Remove one remap helper/selector, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl_qmono`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl_qmono --workers <worker_count>`.
  - Support requires clean diagnostics, no fixed RMSE guardrail failure, and a
    primary-score improvement against cached `dino_hsl2_theta` artifacts.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl_qmono --workers <worker_count>`
    only after iteration promotion.
  - Support requires validation improvement with clean diagnostics under the
    unchanged gates.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show bilinear remap
    diffusion is not a material remaining error source. Any early Z500/MSLP
    guardrail failure would show the reduced remap diffusion disrupts the
    accepted thermodynamic balance.

## Citations

- Local evidence:
  - `.logbook/history/2026-06-22_12-07-18_horizontal-semilagrangian-theta-transport/decision.md`
    accepted `dino_hsl_theta` with iteration delta `+0.1070074439676863` and
    validation delta `+0.10295803136629866`.
  - `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`
    accepted `dino_hsl2_theta` with iteration delta `+0.0071755259598786925`
    and validation delta `+0.007196436070573853`.
  - `.logbook/history/2026-06-22_17-36-00_cfl-blended-hsl-theta/decision.md`
    rejected a pointwise Eulerian/HSL blend after nonfinite fast forecasts, so
    this proposal avoids blending and keeps an exact incumbent fallback.
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` implements
    `_horizontal_semilagrangian_remap_layer` as the localized bilinear remap
    hook for accepted theta HSL transport.
- Literature:
  - Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
    atmospheric models: a review. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
  - Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. Atmospheric
    transport schemes: desirable properties and a semi-Lagrangian view on
    finite-volume discretizations. In Numerical Techniques for Global
    Atmospheric Models. https://doi.org/10.1007/978-3-642-11640-7_8
  - Fritsch, F. N. and Carlson, R. E. 1980. Monotone piecewise cubic
    interpolation. SIAM Journal on Numerical Analysis.
    https://doi.org/10.1137/0717021

## Researcher Notes

This proposal explicitly targets `dino_hsl2_theta` and is distinct from the
accepted HSL sequence. It does not introduce HSL theta transport, change the
midpoint departure estimate, or blend HSL with the pre-HSL Eulerian tendency.
It keeps the accepted path and changes only the bounded interpolation used to
sample theta at the accepted departure point.

It is also distinct from staged `vertical-coherent-hsl-theta`, which changes
departure coherence across layers; staged `horizontal-semilagrangian-passive-
humidity`, which transports humidity; staged `mass-flux-theta-transport`, which
changes the conservative form; and staged `lead-dependent-spectral-smoothing`,
which is calibration/RMSE-facing. It avoids lower-boundary reservoirs, SST/sea-
ice anchors, snow/soil memory, and convective adjustment.

## Evaluator Notes

### 2026-06-22T18:10:43Z

Decision: move to `ready`; rank 1 of 2 current proposals; recommended as the
single next implementation target.

This is the strongest next HSL-theta follow-up because it stays on the accepted
`dino_hsl2_theta` trajectory geometry and changes only the scalar theta-anomaly
remap at the already localized `_horizontal_semilagrangian_remap_layer` hook.
Recent history strongly favors the theta HSL path: `dino_hsl_theta` produced a
large accepted iteration/validation gain, and the midpoint departure follow-up
added another clean gain. By contrast, recent lower-boundary and q/physics
families have been weaker, so the best current signal is still horizontal
theta transport.

The proposal is not a duplicate of staged `vertical-coherent-hsl-theta`, which
regularizes departure winds, or of `mass-flux-theta-transport`, which changes
the transport form. It is also distinct from scrapped quasi-monotone pressure
output interpolation: that was a diagnostic vertical output remap with broad
guardrail risk, while this is a prognostic horizontal theta remap inside the
accepted thermodynamic transport path. The monotone semi-Lagrangian and
PCHIP-style citation set supports the numerical mechanism.

The numerical risk is real because the remap is evaluated every inner step and
reduced bilinear diffusion could expose small-scale thermal variance. However,
it does not repeat the rejected `cfl-blended-hsl-theta` failure mode: there is
no pointwise Eulerian/HSL tendency blend, no new CFL weighting of tendencies,
and the proposal requires a bounded local-extrema limiter plus exact bilinear
fallback for invalid remap diagnostics. Implementation should keep the
fallback conservative and run the fixed gates unchanged: pytest, fast,
iteration, then validation only after promotion.
