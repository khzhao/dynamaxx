---
schema_version: 1
slug: compensated-hydrostatic-dse-diagnostic
title: Compensated Hydrostatic DSE Diagnostic
status: staging
created_at: 2026-06-24T22:43:00Z
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

# Compensated Hydrostatic DSE Diagnostic

## Hypothesis

The accepted `dino_hsl2_mass_dse` branch computes a dry-static-energy anomaly
from `c_p T + Phi`, subtracts an area-weighted layer mean, multiplies by local
layer mass, remaps that scalar horizontally, and converts the result back to a
temperature tendency. This is now a high-leverage thermodynamic path, but the
diagnostic contains two numerically sensitive reductions: the hydrostatic
vertical integration for `Phi` and the horizontal quadrature mean subtraction
used to form the DSE anomaly.

A candidate that uses compensated or pairwise reductions only for this
diagnostic should reduce roundoff-amplified layer-mean and column-thickness
noise without changing the accepted transported scalar, HSL geometry, pressure
thickness, or any forcing.

## Mechanism

Register a side-by-side candidate such as `dino_mass_dse_comp_dse` derived from
`dino_hsl2_mass_dse`.

For the candidate only:

- keep the accepted HSL2 midpoint departure, layer-mass DSE scalar, bilinear HSL
  remap, pressure-thickness division, vertical theta tendency, adiabatic term,
  weak-HS forcing, ocean sensible heat flux, residuals, and output contract;
- add an opt-in DSE diagnostic path in `PrimitiveEquationsSigma` that computes
  dry hydrostatic geopotential and layer DSE means with a fixed compensated or
  pairwise summation order over sigma levels and horizontal quadrature nodes;
- use the compensated values only inside `nodal_dry_static_energy_anomaly` for
  the mass-DSE HSL branch;
- fall back exactly to the incumbent DSE anomaly if any compensated reduction,
  layer mean, or resulting DSE anomaly is nonfinite.

Do not enable JAX `float64` globally and do not change the public forecast API.
If the implementer can use a stable pairwise reduction more cleanly than a
Kahan-style compensation under JAX transformations, prefer the simpler
deterministic pairwise implementation.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests in `tests/dycore/models/dinosaur/test_primitive_equations.py`
    and `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model alias, for example `dino_mass_dse_comp_dse`.
- API changes:
  - None. Forecast inputs, outputs, lead times, metrics, and data splits remain
    fixed.
- Tests to update:
  - Verify the candidate preserves all `dino_hsl2_mass_dse` flags except the
    compensated diagnostic selector and model name.
  - Verify the compensated DSE anomaly keeps zero horizontal layer mean on a
    synthetic finite state.
  - Verify nonfinite compensated diagnostics fall back to incumbent DSE anomaly.
  - Verify registry construction and a finite no-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - Small but broad improvements in `geopotential_500` and
    `mean_sea_level_pressure` if DSE anomaly roundoff currently feeds the
    accepted thermal tendency.
  - Possible medium-lead `2m_temperature` improvement from less noisy lower-layer
    DSE tendency.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be nearly neutral except through secondary
    pressure-gradient feedback.
- Possible regressions:
  - The current reduction order may accidentally compensate other truncation
    errors.
  - The measured effect may be near numerical noise because the incumbent already
    uses high-precision einsums in several operators.

## Risks

- Numerical stability:
  - Low. The change is guarded and local to a diagnostic scalar.
- Compute cost:
  - Low to moderate. It adds a few reductions per thermal tendency call and no
    new remaps or trajectories.
- Data leakage:
  - None. Uses only forecast state and fixed grid weights.
- Physical plausibility:
  - Moderate. This is a numerical consistency refinement, not a new physical
    process.
- Rollback complexity:
  - Low. Remove one selector/helper, factory/export, registry key, and focused
    tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_mass_dse_comp_dse`.
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_mass_dse_comp_dse --workers 4`.
  - Compare against cached `dino_hsl2_mass_dse` artifacts when valid.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_mass_dse_comp_dse --workers 4`
    only after iteration promotion.
  - Require validation delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show DSE diagnostic
    roundoff is not a material remaining error source. Any MSLP/Z500 guardrail
    regression would show the incumbent reduction order is part of the accepted
    balance.

## Citations

- Higham, N. J. 1993. The Accuracy of Floating Point Summation. SIAM Journal on
  Scientific Computing. https://doi.org/10.1137/0914050
- Goldberg, D. 1991. What Every Computer Scientist Should Know About
  Floating-Point Arithmetic. ACM Computing Surveys.
  https://doi.org/10.1145/103162.103163
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Dynamaxx history:
  `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted the layer-mass DSE HSL incumbent. The recent
  `finite-volume-mass-dse-hsl-remap` rejection argues against changing the remap
  itself; this proposal changes only diagnostic reduction arithmetic.

## Researcher Notes

This is not a duplicate of `finite-volume-mass-dse-hsl-remap`, because it does
not alter source-cell quadrature, remap conservation, or pressure-thickness
division. It is also not `dse-consistent-sigma-initialization`, because it does
not change pressure-to-sigma initialization. It differs from
`simmons-burridge-sigma-geopotential-operator`, which targets the sigma
pressure-gradient/geopotential operator broadly; this proposal is narrower and
only changes the DSE diagnostic used by the accepted mass-DSE HSL tendency.

## Evaluator Notes

### 2026-06-24T22:15:03Z

Decision: move to `staging`; ranked 2 of 3 new proposals.

The proposal is feasible and intentionally narrow. It preserves the accepted
mass-DSE HSL scalar, trajectory, pressure-thickness division, forcing, and
output contract while testing whether reduction arithmetic in the DSE anomaly
is a remaining source of balance noise. That makes it distinct from the recent
finite-volume mass-DSE remap rejection and from broader hydrostatic or
pressure-gradient operator proposals.

Keep it staged rather than ready because the expected signal is probably below
the fixed `+0.002` iteration promotion threshold. The incumbent reduction path
already uses JAX/XLA reductions, the recent conservative-remap correction was
guardrail-clean but slightly negative, and many roundoff-scale cleanups in the
history produced negligible or subthreshold score movement. A custom
compensated or pairwise reduction under JAX transformations may also add
implementation complexity without changing the physical forecast path enough
to matter.

Recommendation: reconsider after the stronger DSE-consistent diffusion test or
if a diagnostic artifact shows layer-mean DSE anomaly drift large enough to
affect MSLP or Z500. If promoted later, keep the change diagnostic-local and
fall back exactly to the incumbent anomaly on any nonfinite or shape mismatch.
