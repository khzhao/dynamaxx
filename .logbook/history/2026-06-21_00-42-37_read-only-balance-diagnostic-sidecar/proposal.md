---
schema_version: 1
slug: read-only-balance-diagnostic-sidecar
title: Add a Read-Only Balance Diagnostic Sidecar
status: ready
created_at: 2026-06-21T00:38:35Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/eval/
  - tests/
expected_eval_protocols: []
---

# Add a Read-Only Balance Diagnostic Sidecar

## Hypothesis

Several plausible dycore mechanisms have been rejected or staged because there
is no inexpensive evidence that the incumbent actually suffers from the
targeted imbalance: vertical normal modes, barotropic angular momentum,
passive-humidity tails, dry static-stability defects, pressure/MSLP mismatch,
and output geopotential diagnostics all lack read-only incumbent diagnostics.
A sidecar that computes physical balance summaries without scoring them can
reduce proposal churn while preserving fixed WeatherBench2 metrics, splits,
lead times, and model-selection rules.

## Mechanism

This is an infrastructure proposal, not a model-selection candidate. It should
not change `DycoreModel.forecast`, target variables, metric calculations,
leaderboard acceptance, or any fixed protocol.

Add an optional diagnostic command or helper that can be run on a small set of
forecast batches and write artifacts outside the score path. Suggested
summaries:

- lead-zero and lead-1 residual spectra for `2m_temperature`,
  `10m_u_component_of_wind`, `mean_sea_level_pressure`, and `geopotential_500`;
- global and latitude-band mass drift from `log_surface_pressure`;
- layerwise dry static stability and frequency of negative potential-
  temperature gradients;
- passive-humidity min/max and virtual-temperature contribution to Z500;
- barotropic zonal-wind and angular-momentum proxies;
- divergence/vorticity spectra at early and medium leads.

The sidecar should use existing forecast inputs and outputs only. It must not
produce a tuned coefficient, alter selection gates, or introduce golden usage
for iterative selection.

## Implementation Scope

- Expected files:
  - Optional helper under `src/dynamaxx/eval/` or a dedicated diagnostic module.
  - Optional Dinosaur adapter utilities only if needed to expose read-only
    intermediate state summaries.
  - Tests for deterministic artifact schema and no-score-path integration.
- Registry changes:
  - None.
- API changes:
  - None for `DycoreModel.forecast`. If a CLI is added, it must be outside
    `fast`, `iteration`, `validation`, and `golden`.
- Tests to update:
  - Verify diagnostic artifacts are finite JSON/CSV summaries.
  - Verify running the sidecar does not create or modify leaderboard, history,
    score JSON, or fixed evaluation outputs.
  - Verify no code path changes metric records or target variables.

## Expected Metric Movement

- Expected improvements:
  - None directly. This is evidence infrastructure.
- Expected neutral metrics:
  - All fixed metrics are unchanged because no model-selection forecast is
    modified.
- Possible regressions:
  - None in scores if kept outside the fixed protocols. The risk is process
    misuse: treating diagnostic summaries as tuned validation feedback.

## Risks

- Numerical stability:
  - None for forecasts; diagnostics must tolerate nonfinite candidate fields and
    report them without crashing.
- Compute cost:
  - Low to moderate depending on selected batches. It should default to a small
    read-only sample and avoid `golden`.
- Data leakage:
  - Moderate process risk. The sidecar must not use validation or golden truth
    to choose coefficients. It should be used for qualitative mechanism
    triage, not parameter fitting.
- Physical plausibility:
  - High. The summaries are standard dynamical-core balance diagnostics.
- Rollback complexity:
  - Low if implemented as an isolated optional command.

## Evaluation Plan

- Fast gate:
  - Not applicable as a model-selection gate. Run unit tests and a tiny
    diagnostic smoke command on a development batch only.
- Iteration gate:
  - Do not run fixed `iteration` for this infrastructure proposal.
- Validation gate:
  - Do not run fixed `validation` for this infrastructure proposal.
- Outcome that would falsify the hypothesis:
  - If the sidecar cannot be kept out of score artifacts or encourages
    coefficient tuning against validation/golden data, it should be rejected.

## Citations

- Williamson, D. L. et al. 1992. A standard test set for numerical
  approximations to the shallow water equations in spherical geometry. Journal
  of Computational Physics. https://doi.org/10.1016/S0021-9991(05)80016-6
- Jablonowski, C. and Williamson, D. L. 2006. A baroclinic instability test
  case for atmospheric model dynamical cores. Quarterly Journal of the Royal
  Meteorological Society. https://doi.org/10.1256/qj.06.12
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian integration schemes for
  atmospheric models: A review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- ECMWF IFS Documentation Part III: Dynamics and Numerical Procedures describes
  hydrostatic, mass, vorticity-divergence, and semi-implicit balance concepts.
  https://www.ecmwf.int/en/publications/ifs-documentation
- Dynamaxx research scrap records for `vertical-normal-mode-gravity-wave-filter`,
  `barotropic-angular-momentum-fixer`, `bounded-virtual-humidity-geopotential`,
  and `free-tropospheric-pv-stability-floor` all cite missing read-only evidence
  as a reason not to spend model-selection evaluations.

## Researcher Notes

This is intentionally separate from model selection. It should not move the
incumbent, modify protocols, or create a new scored metric. Its value is to
make future Researcher proposals less speculative and to avoid repeated
near-duplicates in rejected terrain, humidity, gravity-wave, and broad damping
families.

## Evaluator Notes

### 2026-06-21T00:41:38Z

Decision: move to `ready`; ranked 1 of 3 triaged proposals.

This is the only proposal in this batch that should be ready now because it is
infrastructure, not a model-selection candidate. The proposal explicitly keeps
`DycoreModel.forecast`, target variables, metrics, leaderboard acceptance,
history, and fixed `fast`/`iteration`/`validation`/`golden` protocols
unchanged. That separation is essential: anything that changes evaluation
support or the forecast contract must remain infrastructure-only and cannot be
mixed with model selection.

The sidecar directly addresses repeated negative evidence in prior research.
Several scrapped or staged families cite missing read-only evidence before
another evaluation should be spent: terrain/orography and dynamic MSLP ideas
are risky without better balance diagnostics; humidity/geopotential proposals
lack evidence of harmful passive-tracer tails; vertical normal-mode,
barotropic angular-momentum, and PV/static-stability filters are too complex or
too speculative without read-only incumbent imbalance measurements. A
small-sample diagnostic artifact outside the score path can reduce proposal
churn without changing any fixed selection metric.

Implementation must remain tightly scoped. It should write only separate
diagnostic JSON/CSV artifacts, avoid validation and golden truth for tuning,
avoid producing tuned coefficients, and include tests proving it does not
create or modify leaderboard, history, score JSON, fixed evaluation outputs, or
target-variable definitions.
