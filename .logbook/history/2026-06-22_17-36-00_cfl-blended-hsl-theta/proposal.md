---
schema_version: 1
slug: cfl-blended-hsl-theta
title: CFL-Weighted Blend for Horizontal Semi-Lagrangian Theta
status: ready
created_at: 2026-06-22T17:30:10Z
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

# CFL-Weighted Blend for Horizontal Semi-Lagrangian Theta

## Hypothesis

The current incumbent `dino_hsl2_theta` at commit
`72efada4e0afbd8e34e3184dbcef90cb91cc051c` proves that horizontal
semi-Lagrangian transport of dry-theta anomaly is a high-signal change. The
accepted implementation now uses a midpoint departure estimate, but it still
replaces the Eulerian spectral theta tendency wherever the bounded
semi-Lagrangian diagnostics are finite.

The semi-Lagrangian replacement should be most valuable where resolved
horizontal displacement is a meaningful fraction of the grid spacing. In weak
flow or very small local displacement, the bilinear remap can add interpolation
diffusion while the incumbent spectral advective tendency is already accurate.
A fixed local CFL-weighted blend should retain the accepted HSL phase benefit in
fast advective regions while sparing slow regions from unnecessary remap
diffusion.

## Mechanism

Add one side-by-side candidate with short alias `dino_hsl_cflblend` targeting
`dino_hsl2_theta`.

For the candidate only:

- preserve the full `dino_hsl2_theta` model path: DFI, weak-HS analysis
  equilibrium, symmetric Coriolis split, theta tendency, theta mean recentering,
  semi-implicit off-centering, scale-separated residuals, land-sea surface
  residual, ocean bulk sensible heat flux, midpoint theta departure, output
  variables, lead schedule, and evaluation protocols;
- keep the existing midpoint semi-Lagrangian theta tendency and incumbent
  Eulerian spectral theta tendency available inside
  `horizontal_semilagrangian_theta_transport`;
- compute a local nondimensional displacement weight from the already capped
  longitude and latitude departure distances divided by their existing maximum
  allowed distances;
- blend pointwise between the incumbent Eulerian theta tendency and the accepted
  midpoint HSL theta tendency using that fixed displacement weight, so zero or
  tiny displacement tends toward the Eulerian tendency and near-cap displacement
  tends toward the accepted HSL tendency;
- keep the current finite diagnostics and wind-present guards, falling back to
  exactly the accepted `dino_hsl2_theta` fallback path if the blend weights,
  displacements, remapped theta, or blended tendency are nonfinite;
- do not change vertical theta transport, pressure-work terms, momentum,
  pressure continuity, passive humidity, filters, residual corrections, or
  forecast output packing.

This is not another midpoint or departure-geometry tweak. The accepted
departure estimate remains the HSL candidate tendency; the new question is
whether local displacement should control how strongly that candidate replaces
the spectral theta tendency.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one registered side-by-side model named `dino_hsl_cflblend`.
- API changes:
  - None. `DycoreModel.forecast`, accepted input variables, emitted variables,
    lead times, metrics, and WeatherBench2 splits stay unchanged.
- Tests to update:
  - Verify `dino_hsl_cflblend` preserves all `dino_hsl2_theta` flags except the
    new CFL-blend selector and model name.
  - Unit-test zero displacement gives the incumbent Eulerian theta tendency.
  - Unit-test near-cap displacement gives the accepted midpoint HSL tendency to
    tolerance.
  - Unit-test blend weights are bounded in `[0, 1]`, finite at polar rows, and
    shape-compatible with layerwise theta fields.
  - Verify nonfinite blend diagnostics fall back to the accepted
    `dino_hsl2_theta` tendency/fallback chain.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium and late leads if
    slow-region HSL remap diffusion is slightly degrading accepted thermal
    phase.
  - `2m_temperature` after residual memory decay if lower-column weak-flow
    thermal structures benefit from retaining the spectral tendency.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to `dino_hsl2_theta` because
    momentum, Coriolis splitting, the Richardson diagnostic, and residual
    memory are unchanged.
- Possible regressions:
  - The globally applied accepted HSL remap may be providing useful numerical
    smoothing even in slow flow.
  - A pointwise blend can create a new spatially varying numerical diffusion
    pattern that is less balanced than the accepted all-or-nothing HSL
    replacement.

## Risks

- Numerical stability:
  - Low to moderate. The candidate adds a convex blend between two already
    finite-guarded theta tendencies, but it touches thermodynamic transport
    every inner step.
- Compute cost:
  - Low. It reuses existing HSL displacements and tendencies, adding only local
    algebra and one registered model.
- Data leakage:
  - None. It uses only current forecast state, fixed grid geometry, and existing
    displacement caps.
- Physical plausibility:
  - Moderate to high. Semi-Lagrangian remap benefits depend on trajectory
    displacement relative to grid spacing; retaining a spectral tendency in
    near-zero-displacement regions is numerically plausible.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl_cflblend`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl_cflblend --workers <worker_count>`.
  - Support requires primary-score improvement against cached `dino_hsl2_theta`
    artifacts, clean diagnostics, and no fixed early-lead or variable-lead RMSE
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl_cflblend --workers <worker_count>`
    only after iteration promotion.
  - Require validation support under the unchanged acceptance gates.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show the accepted
    all-valid HSL replacement is already the better bias-variance tradeoff. Any
    early Z500, MSLP, or wind guardrail failure would show the spatially varying
    blend disrupts accepted balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  implements the current `dino_hsl2_theta` bounded midpoint HSL theta transport
  hook, including displacement caps and finite fallback.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` wires the
  accepted `dino_hsl2_theta` path without changing the forecast contract.
- Dynamaxx history:
  `.logbook/history/2026-06-22_12-07-18_horizontal-semilagrangian-theta-transport/decision.md`
  accepted `dino_hsl_theta` with iteration delta `+0.1070074439676863` and
  validation delta `+0.10295803136629866`.
- Dynamaxx history:
  `.logbook/history/2026-06-22_14-43-00_midpoint-semilagrangian-theta-departure/decision.md`
  accepted `dino_hsl2_theta` with iteration delta `+0.0071755259598786925` and
  validation delta `+0.007196436070573853`.
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: a review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Lauritzen, P. H., Ullrich, P. A., and Nair, R. D. 2011. Atmospheric
  transport schemes: desirable properties and a semi-Lagrangian view on
  finite-volume discretizations. In Numerical Techniques for Global Atmospheric
  Models. https://doi.org/10.1007/978-3-642-11640-7_8
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This proposal explicitly targets `dino_hsl2_theta` and is not a duplicate of
the accepted HSL sequence: accepted `dino_hsl_theta` introduced the HSL theta
replacement, and accepted `dino_hsl2_theta` improved the departure estimate.
This proposal leaves both mechanisms intact and tests a bounded displacement
weight between the accepted HSL tendency and the pre-HSL Eulerian theta
tendency.

It is also distinct from staged `skew-symmetric-horizontal-scalar-advection`,
which changes the scalar product identity, and staged `mass-flux-theta-transport`,
which changes the conservative form of theta transport. It avoids recent
rejected or staged lower-boundary reservoirs, SST/sea-ice anchors,
lead-dependent smoothing, convective adjustment, passive-humidity HSL, and any
forecast-contract or evaluation-protocol change.

## Evaluator Notes

### 2026-06-22T17:34:01Z

Decision: move to `ready`; rank 1 of 2 current proposals and the single
recommended next implementation target.

This is the strongest immediate follow-up to the current incumbent
`dino_hsl2_theta` at `72efada4e0afbd8e34e3184dbcef90cb91cc051c`. The two most
recent accepted candidates establish that horizontal dry-theta HSL transport is
high signal, first with a large validation gain and then with a smaller but
clean midpoint-departure gain. This proposal tests a narrow remaining numerical
question inside the same accepted hook: whether near-zero horizontal
displacement should keep the spectral Eulerian theta tendency instead of paying
semi-Lagrangian interpolation diffusion everywhere.

The implementation surface is small and compatible with fixed evaluation gates:
one side-by-side alias, one primitive-equation selector/helper, existing
displacement caps, existing finite fallback, and focused tests. It is not a
duplicate of staged scalar-product or flux-form theta transport because it does
not change the advection identity or conservative mass coupling. It is also not
the lead-dependent smoothing/calibration idea; the blend weight is diagnosed
from current-step displacement geometry and must be fixed before scoring, with
no validation tuning or protocol change.

Main risk: this is still a blend and can quietly remove useful HSL smoothing in
slow-flow regions, producing a near-zero or negative score. The risk is
acceptable for the next iteration because the hypothesis is directly tied to
the accepted HSL mechanism, uses no new data, and should fail cleanly under the
iteration gate and RMSE guardrails if the accepted all-valid HSL replacement is
already the better tradeoff.
