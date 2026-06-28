---
schema_version: 1
slug: compensated-vertical-integral-reductions
title: Compensated Vertical Integral Reductions
status: staging
created_at: 2026-06-26T11:07:00Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/jax_numpy_utils.py
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

# Compensated Vertical Integral Reductions

## Hypothesis

The current incumbent's largest remaining trajectory weakness is late
`mean_sea_level_pressure`, while the accepted vertical-DSE ramp already protects
short-lead guardrails. A remaining error source may be small accumulated
roundoff and cancellation in vertical cumulative reductions used for hydrostatic
geopotential, hybrid mass flux, and omega-alpha temperature work. Replacing only
selected layer-axis cumulative reductions with a compensated or pairwise
high-precision-in-accumulation helper should reduce slow mass/thickness drift
without changing the physical tendencies, forecast contract, or the accepted
vertical-DSE schedule.

## Mechanism

Add one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_ramp_vint_comp`.

For this candidate only:

- keep the incumbent mass-DSE HSL, WTG relaxation, pressure-ramped vertical-DSE
  increment, weak-HS forcing, residual correction, diffusion strength, Coriolis
  split, output variables, and evaluation protocols unchanged;
- add an opt-in vertical-reduction helper for short layer-axis prefix and
  reverse-prefix sums used in hydrostatic and pressure-work calculations;
- implement the helper as fixed-shape pairwise or triangular-matrix reductions
  using `jax.lax.Precision.HIGHEST`, with explicit finite fallback to the
  incumbent reduction when the candidate result is nonfinite;
- apply it only to the cancellation-prone reductions in hybrid mass flux,
  hydrostatic geopotential difference, omega-alpha temperature work, and
  temperature implicit weights; leave horizontal transforms, HSL interpolation,
  WTG masks, vertical-DSE ramp/cap logic, and output diagnostics unchanged;
- return all candidate tendencies in the incumbent dtype so this is not a
  global `jax_enable_x64` experiment and does not change public array types.

This is a numerical-operator accuracy test, not a new filter, pressure gate,
vertical-DSE retune, or output correction.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/jax_numpy_utils.py` if the helper is
    reusable; otherwise keep the helper local to `primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused primitive-equation and registry tests
- Registry changes:
  - Add one side-by-side model key such as
    `dino_hsl2_mass_dse_wtg_vdse_ramp_vint_comp`.
- API changes:
  - None. Forecast inputs, outputs, lead schedule, target variables, and fixed
    protocols remain unchanged.
- Tests to update:
  - Unit-test candidate reductions against incumbent reductions on smooth and
    alternating-sign synthetic columns.
  - Verify candidate and incumbent are identical when all selected reductions
    are constant-column or one-layer equivalent.
  - Verify nonfinite candidate reductions fall back to incumbent reductions.
  - Verify the candidate factory preserves every incumbent option except the
    vertical-integral selector and model name.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at days 4-15 if slow
    hydrostatic or mass-flux accumulation error is contributing to late drift.
  - Small downstream improvement in `2m_temperature` if lower-column pressure
    work becomes less biased.
- Expected neutral metrics:
  - Day-1 to day-3 fields should stay very close to the incumbent because no
    physical tendency strength, ramp, filter, or residual path changes.
  - `10m_u_component_of_wind` should be mostly neutral except through balanced
    mass-field feedback.
- Possible regressions:
  - If the incumbent's float32 reduction path is already within metric noise,
    the proposal will be clean but subthreshold.
  - Tiny phase changes in pressure work can still accumulate into MSLP or Z500
    regressions, so fixed guardrails remain important.

## Risks

- Numerical stability:
  - Low. The candidate changes reduction arithmetic and falls back on nonfinite
    results, but it touches core hydrostatic and mass-flux calculations.
- Compute cost:
  - Low to moderate. Layer counts are small, but extra pairwise/triangular
    reductions run at every inner step. The reported 48 CPUs, 171 GiB RAM, four
    L4 GPUs, and fixed `--workers 4` are sufficient for one side-by-side test.
- Data leakage:
  - None. The helper uses only current forecast state and fixed grid geometry.
- Physical plausibility:
  - Moderate to high. The physical equations are unchanged; the hypothesis is
    numerical fidelity in the reductions that discretize hydrostatic balance and
    mass continuity.
- Rollback complexity:
  - Low. Remove one helper or selector, one factory/export, one registry entry,
    and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_vint_comp`.
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_vint_comp --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached
    `dino_hsl2_mass_dse_wtg_vdse_ramp`, clean diagnostics, and no early
    day-1-to-day-5 or variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_vint_comp --workers 4`
    only after iteration promotion.
  - Support requires validation primary-score delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that vertical
    reduction roundoff is not a material remaining error source. Any early MSLP
    or Z500 guardrail failure would show the arithmetic change perturbs balance
    more than it helps.

## Citations

- Dynamaxx source:
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` uses vertical
  cumulative reductions in hybrid mass flux, hydrostatic geopotential, and
  omega-alpha temperature-work paths, while the accepted incumbent is registered
  as `dino_hsl2_mass_dse_wtg_vdse_ramp`.
- Dynamaxx history:
  `.logbook/history/2026-06-25_12-52-40_pressure-ramped-vertical-dse-wtg/decision.md`
  accepted the current incumbent with large iteration and validation gains and
  clean guardrails.
- Dynamaxx history:
  `.logbook/history/2026-06-26_00-40-18_hydrostatic-work-gated-vertical-dse/decision.md`
  rejected a physical hydrostatic-work gate with severe early `2m_temperature`
  and mass-field regressions; this proposal leaves that physics unchanged.
- Higham, N. J. 2002. *Accuracy and Stability of Numerical Algorithms*, second
  edition. SIAM. https://doi.org/10.1137/1.9780898718027
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  *Monthly Weather Review*. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Durran, D. R. 2010. *Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics*, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of the active pressure-work or omega-alpha proposals:
those alter the discrete physical coupling or add diagnostics around pressure
work, while this proposal changes only the arithmetic used to evaluate existing
vertical reductions. It is also not a vertical-DSE schedule, cap, or spatial
gate, which recent rejected histories show are high risk.

The accepted incumbent's RMSE guardrail movement against its predecessor was
near numerical noise despite a large primary-score gain, so a small numerical
operator change is plausible but should be treated as a low-amplitude test. The
proposal is intentionally decorrelated from the rejected surface-output and
surface-residual variants because it never touches `2m_temperature` or `10m`
diagnostic residual logic directly.

## Evaluator Notes

### 2026-06-26T11:09:59Z

Decision: move to `staging`; ranked 2 of 2 in this proposal triage.

This is scientifically legitimate but not the best next experiment. High-quality
summation is a standard numerical concern, and the targeted vertical reductions
feed real hydrostatic, mass-flux, omega-alpha, and implicit-temperature paths.
The proposal is also attractive in that it leaves physical tendency strengths,
the accepted WTG and vertical-DSE schedule, output variables, and evaluation
protocols unchanged.

Keep it staged because the expected score signal is likely small relative to
the fixed `+0.002` iteration gate. The current `jax_numpy_utils.cumsum` already
uses a fixed dot-product reduction for short axes with high precision settings,
the vertical layer count is small, and prior roundoff-scale cleanup ideas have
usually been neutral or subthreshold. This also partially overlaps with staged
`compensated-hydrostatic-dse-diagnostic`, but broadens the surface area from a
diagnostic scalar into several core operators. That broader touch path increases
implementation and balance risk without a clearer mechanism than the
mass-centered DSE anomaly proposal.

Caveats: if promoted later, the exact list of compensated reductions should be
fixed before scoring, the implementation should avoid global `float64`, preserve
public dtypes, handle sharding deterministically, and include finite fallback to
the incumbent path. It should be revisited only after stronger mass-DSE
consistency candidates fail cleanly or diagnostics show vertical reduction
roundoff large enough to plausibly affect MSLP/Z500.
