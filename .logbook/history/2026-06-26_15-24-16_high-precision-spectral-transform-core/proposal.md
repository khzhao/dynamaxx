---
schema_version: 1
slug: high-precision-spectral-transform-core
title: High-Precision Spectral Transform Core
status: ready
created_at: 2026-06-26T00:00:00Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py
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

# High-Precision Spectral Transform Core

## Hypothesis

The incumbent is a spectral-transform primitive-equation model whose pressure-gradient, kinetic-energy, vorticity/divergence, horizontal advection, and output interpolation paths repeatedly move fields between modal and nodal space. Small transform roundoff and cancellation errors can accumulate into medium-lead phase and thickness drift even when the physical tendencies are unchanged. Using higher-precision contraction settings for selected spherical-harmonic transforms may reduce residual `mean_sea_level_pressure` and `geopotential_500` drift without touching the accepted mass-DSE, WTG, or pressure-ramped vertical-DSE mechanisms.

## Mechanism

Add one side-by-side candidate, for example `dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec`.

For this candidate only:

- keep the incumbent physics, DFI, weak-HS forcing, residual memory, Richardson 10 m wind diagnostic, ocean heat flux, mass-DSE HSL, WTG filter, vertical-DSE ramp, diffusion coefficients, and output contract unchanged;
- add an opt-in transform precision selector used by `spherical_harmonic.Grid.to_modal`, `to_nodal`, and derivative transforms through the existing `_transform_einsum` path;
- use `jax.lax.Precision.HIGHEST` for the selected transform contractions while preserving public dtypes and array shapes;
- leave vertical cumulative reductions unchanged, so this is not the staged compensated vertical-integral proposal;
- include a finite fallback or construction-time default that reproduces the incumbent transform precision when the selector is disabled.

This is a numerical fidelity experiment. It changes arithmetic precision in the repeated spectral transforms, not physical tendency strengths or diagnostics.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one model key such as `dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec`.
- API changes:
  - None. Forecast inputs, output variables, lead schedule, and fixed protocols remain unchanged.
- Tests to update:
  - Verify the new factory preserves every incumbent flag except the precision selector and model name.
  - Unit-test that the high-precision transform path preserves shapes, dtypes, masks, and finite values.
  - Verify disabling the selector reproduces the incumbent transform path.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at days 4-15 if transform roundoff contributes to pressure-gradient or thickness drift.
  - Small secondary improvement in `10m_u_component_of_wind` through cleaner vorticity/divergence transforms.
- Expected neutral metrics:
  - Day-1 fields and `2m_temperature` should be close to incumbent because no heating, surface residual, WTG, or vertical-DSE strength changes.
- Possible regressions:
  - The incumbent may already be precision-insensitive at this resolution, making the result clean but subthreshold.
  - Slightly different transform arithmetic can change phase enough to regress MSLP or Z500 despite being more accurate locally.

## Risks

- Numerical stability:
  - Low. The equations and filters are unchanged, but core transforms affect many tendencies.
- Compute cost:
  - Moderate. Higher-precision contractions can slow every inner step, but the reported 48 CPUs, 171 GiB RAM, four L4 GPUs, and fixed `--workers 4` envelope are adequate for one candidate.
- Data leakage:
  - None. The selector uses only model arithmetic settings.
- Physical plausibility:
  - High as a numerical-method test; it does not add fitted physics.
- Rollback complexity:
  - Low. Remove one selector, one factory/export, one registry entry, and tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec`.
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached `dino_hsl2_mass_dse_wtg_vdse_ramp`, clean diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec --workers 4` only after iteration promotion.
  - Support requires validation delta at least `+0.001` with clean guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show transform precision is not a material remaining error source. Any early MSLP or Z500 guardrail failure would show the arithmetic change perturbs balance more than it helps.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py` implements modal/nodal transforms through `_transform_einsum`, and `adapter.py` repeatedly uses these transforms during rollout and output packing.
- Dynamaxx history: `.logbook/history/2026-06-25_12-52-40_pressure-ramped-vertical-dse-wtg/decision.md` accepted the incumbent with large gains and clean guardrails, so this proposal preserves that physical path.
- Dynamaxx research: `.logbook/research/staging/compensated-vertical-integral-reductions.md` targets vertical cumulative reductions; this proposal targets horizontal spectral transform contractions instead.
- Higham, N. J. 2002. *Accuracy and Stability of Numerical Algorithms*, second edition. SIAM. https://doi.org/10.1137/1.9780898718027
- Canuto, C., Hussaini, M. Y., Quarteroni, A., and Zang, T. A. 2007. *Spectral Methods: Evolution to Complex Geometries and Applications to Fluid Dynamics*. Springer. https://doi.org/10.1007/978-3-540-30728-0
- Williamson, D. L. 2007. The evolution of dynamical cores for global atmospheric models. *Journal of the Meteorological Society of Japan*. https://doi.org/10.2151/jmsj.85B.241

## Researcher Notes

This is not a duplicate of the staged `compensated-vertical-integral-reductions`: that idea changes layer-axis cumulative sums in hydrostatic and omega-alpha paths, while this one changes horizontal spherical-harmonic contraction precision. It is also not a mass-DSE scalar-centering proposal, which local evidence showed was safe but subthreshold.

The proposal is decorrelated from recent failures: it does not touch vertical-DSE timing, caps, hydrostatic-work gates, surface wind diagnostics, or coupled surface residual decay. The main weakness is expected signal size; like other numerical cleanup ideas, it may be clean but too small for the `+0.002` iteration gate.

## Evaluator Notes

### 2026-06-26T15:05:45Z

Decision: move to `ready`; ranked 1 of 2 in this triage.

This is the stronger next experiment because it is implementation-ready and
source-local. Source inspection shows `FastSphericalHarmonics` already exposes a
`transform_precision` selector, with the current fast transform path passing
that value through `_transform_einsum`; the incumbent default is
`"tensorfloat32"`. A side-by-side model can therefore set the transform path to
highest precision without changing the forecast API, lead schedule, accepted
mass-DSE/WTG/vertical-DSE mechanisms, post-step filters, or fixed evaluation
protocols.

The expected score signal may be small. The recent
`mass-centered-dse-anomaly-hsl` experiment was clean but improved only
`+0.000026881174071430314`, far below the fixed `+0.002` iteration promotion
gate, so small numerical cleanup ideas need unusually low implementation risk.
This proposal meets that bar better than the SIL3 stage-filtering proposal: it
changes contraction precision rather than adding a new within-step state
regularization path.

Implementation constraints for the Implementer: keep this as one side-by-side
registered model, preserve public dtypes and shapes, avoid global `float64` or
evaluation-policy changes, and use the leaderboard incumbent cache unless the
Scorer finds a concrete invalidation under `roles/PROTOCOL.md`. Validation
should run only after the fixed iteration promotion gate passes.
