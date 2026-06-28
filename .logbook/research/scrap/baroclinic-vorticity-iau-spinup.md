---
schema_version: 1
slug: baroclinic-vorticity-iau-spinup
title: Apply a Low-Mode Baroclinic Vorticity IAU During Early Spinup
status: scrap
created_at: 2026-06-21T00:30:15Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Apply a Low-Mode Baroclinic Vorticity IAU During Early Spinup

## Hypothesis

The accepted DFI removes initialization imbalance, but a prior abrupt
vorticity-preserving DFI merge was slightly harmful. That negative result argues
against replacing the filtered initial vorticity with the raw analysis
vorticity. It does not rule out a much narrower incremental analysis update:
slowly reintroducing only the low-wavenumber baroclinic part of the raw-minus-DFI
vorticity increment over the first few forecast hours.

Gradual IAU can reduce spinup shocks relative to an instantaneous state merge.
Restricting the increment to low-mode baroclinic vorticity avoids the rejected
barotropic analysis-HS projection branch, leaves divergence/mass/thermal fields
on the accepted DFI-balanced path, and targets medium-lead wind and Z500 phase
errors without changing fixed evaluation protocols.

## Mechanism

Add a side-by-side candidate with a suffix such as `_baroclinic_vort_iau`.
Preserve the full incumbent trajectory setup and add one opt-in early-rollout
tendency.

For the candidate only:

- compute both the raw initialized Dinosaur state and the accepted DFI-filtered
  initial state using the incumbent conversion path;
- form the vorticity increment `raw_vorticity - dfi_vorticity`;
- remove the barotropic vertical mean of that increment so only vertical shear
  structure is retained;
- project the remaining increment onto a fixed low total-wavenumber taper, for
  example full weight through wavenumber 8 and cosine taper to zero by
  wavenumber 15;
- add the tapered increment as an IAU tendency spread over the first `6 h` or
  `12 h` of positive-time rollout with a fixed smooth window whose integral is
  one;
- leave divergence, temperature variation, log-surface-pressure, tracers,
  weak-HS forcing, Coriolis splitting, residual correction, and output packing
  unchanged;
- do not apply the IAU during DFI itself, and no-op if raw or DFI states are
  nonfinite.

This is not a partial DFI state merge. The accepted DFI state remains the
initial condition; the raw analysis increment enters only as a small,
low-mode, time-distributed vorticity tendency.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory extending the incumbent name with
    `_baroclinic_vort_iau`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, metrics, and
    splits remain unchanged.
- Tests to update:
  - Verify the IAU window integrates to one and is zero after the configured
    spinup interval.
  - Unit-test barotropic vertical-mean removal and low-wavenumber tapering.
  - Verify only vorticity tendencies are changed by the selector.
  - Verify nonfinite increment fallback leaves the incumbent path unchanged.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` and `geopotential_500` at medium leads if DFI
    removes useful balanced baroclinic rotational structure during spinup.
  - Primary score can improve without perturbing the accepted surface residual
    or analysis-HS thermal mechanism.
- Expected neutral metrics:
  - `2m_temperature` and `mean_sea_level_pressure` should be mostly neutral
    because mass and thermal leaves are not directly incremented.
- Possible regressions:
  - Reintroducing raw vorticity, even gradually, can create imbalance with
    divergence and pressure fields.
  - If the accepted full DFI state is already optimal, the IAU will add phase
    error or noise.

## Risks

- Numerical stability:
  - Moderate. Vorticity-only tendencies can unbalance the flow, though low-mode
    tapering and smooth IAU reduce this risk.
- Compute cost:
  - Low to moderate. It reuses raw and DFI initial states and adds one modal
    vorticity tendency during early steps.
- Data leakage:
  - None. The increment uses only the same-time initial analysis and the
    accepted DFI-filtered state.
- Physical plausibility:
  - Moderate to high. IAU is a standard way to introduce analysis increments
    gradually, but this dycore-specific low-mode vorticity increment is a
    simplified balance assumption.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta would show that useful
    rotational analysis structure is not being lost by accepted DFI. Any early
    wind, Z500, or MSLP guardrail failure would show the vorticity-only IAU is
    not sufficiently balanced.

## Citations

- Bloom, S. C., Takacs, L. L., da Silva, A. M., and Ledvina, D. 1996. Data
  assimilation using incremental analysis updates. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1996)124%3C1256:DAUIAU%3E2.0.CO;2
- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM model using a
  digital filter. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Polavarapu, S., Tanguay, M., and Fillion, L. 2000. Four-dimensional
  variational data assimilation with digital filter initialization. Monthly
  Weather Review.
  https://doi.org/10.1175/1520-0493(2000)128%3C2491:FDVDAW%3E2.0.CO;2
- Dynamaxx history:
  `.logbook/history/2026-06-18_00-44-09_vorticity-preserving-dfi-increment/decision.md`
  rejected an abrupt partial vorticity merge; this proposal differs by keeping
  the DFI initial state and applying only a low-mode, baroclinic, gradual IAU.
- Dynamaxx history:
  `.logbook/history/2026-06-20_22-48-00_barotropic-analysis-hs-equilibrium-offset/decision.md`
  rejected a barotropic analysis-HS projection, so this proposal explicitly
  removes the barotropic vertical-mean increment and targets rotational spinup
  rather than thermal equilibrium.

## Researcher Notes

This is a DFI follow-up, but it is not an immediate analysis-HS timing/rate
variant and not another partial-state merge. The material difference is the
time-distributed IAU with low-mode and baroclinic restrictions; the proposal
should be scrapped if the Evaluator judges that the prior vorticity-merge
negative result is already decisive.

## Evaluator Notes

### 2026-06-21T00:35:34Z

Decision: move to `scrap`.

The low-mode, baroclinic, time-distributed IAU is safer than the rejected
abrupt `vorticity-preserving-dfi-increment`, and IAU itself is a reputable
gradual-insertion mechanism. However, this loop's evidence is already strongly
cautionary for exactly the component being reintroduced. The vorticity-preserving
DFI increment was clean but negative, showing that raw analysis vorticity did
not recover enough useful wind skill even without a guardrail failure. The
current proposal still injects raw-minus-DFI vorticity into the prognostic
trajectory while leaving mass, divergence, and thermal fields on the DFI path,
so the core balance risk remains.

It is also dominated by existing research states. Scrapped
`low-mode-preserving-dfi-initialization` was rejected even though it preserved
coupled low modes across dynamic leaves, and staged `balanced-low-mode-thermal-iau`
is a cleaner IAU representative because it targets thermal thickness/Z500
without reintroducing raw vorticity. Recent immediate analysis-HS follow-ups
also warn against nearby tweaks after a strong accepted result: rate masking
failed severely, lead decay was clean but subthreshold, and barotropic
projection was clean but slightly negative. Under the fixed gates, this
vorticity-only IAU is unlikely to clear `+0.002` without early wind or mass
balance risk.
