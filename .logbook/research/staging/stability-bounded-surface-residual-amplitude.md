---
schema_version: 1
slug: stability-bounded-surface-residual-amplitude
title: Bound Surface Residual Amplitude by Lower-Column Stability
status: staging
created_at: 2026-06-21T02:42:06Z
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

# Bound Surface Residual Amplitude by Lower-Column Stability

## Hypothesis

The accepted scale-separated near-surface residual correction is a major part of
the incumbent, but recent attempts to modify its memory, decay, seasonality, and
relaxation rate caused either large `2m_temperature` regressions or subthreshold
clean results. This suggests that the decay schedule is already close to useful,
while occasional residual amplitudes may still be too aggressive in very stable
or weak-shear lower columns. A bounded amplitude limiter can reduce harmful
surface-memory injections without changing the accepted decay timescales,
spectral split, or analysis-HS equilibrium.

## Mechanism

Add an optional amplitude limiter inside the near-surface residual path. Before
splitting residuals into low and high horizontal scales, compute the same lower
column stability information already used by the incumbent's stability-aware
decay helper when pressure-level temperature and wind channels are available.
Then cap only the lead-zero residual that will be persisted:

- for `2m_temperature`, allow the full residual in neutral or weakly unstable
  columns, but smoothly cap stable weak-shear residuals to a bounded Kelvin
  scale
- for `10m_u_component_of_wind`, cap residual magnitude more strongly under
  stable weak-shear conditions where surface-layer decoupling makes lowest-model
  wind a poor proxy
- preserve residual sign and preserve lead-zero exactness by continuing to set
  requested lead-zero outputs to the initial state
- keep the incumbent high-mode and low-mode decay factors unchanged
- do not alter weak-HS rates, analysis-HS masks, spectral taper, or lead decay

Register a side-by-side candidate whose name appends
`_stable_residual_amp_bound` to the incumbent.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/`
- Registry changes:
  - Add one candidate factory and registry key.
- API changes:
  - None. Forecast contract, target variables, lead range, metrics, data split,
    and leaderboard semantics remain unchanged.
- Tests to update:
  - Unit-test that neutral columns are effectively no-op.
  - Unit-test that stable weak-shear columns cap residual amplitudes without
    changing sign.
  - Unit-test lead-zero exactness and finite fallback behavior.
  - Add registry/factory tests showing all incumbent flags are preserved except
    the new amplitude limiter.

## Expected Metric Movement

- Expected improvements:
  - Early `2m_temperature` if a small fraction of large stable-column residuals
    currently overcorrects surface memory.
  - Early and medium `10m_u_component_of_wind` if the accepted residual path
    occasionally carries too much low-level wind mismatch into stable regimes.
- Expected neutral metrics:
  - `mean_sea_level_pressure` and `geopotential_500` should be mostly neutral
    because this proposal does not touch dynamics, mass initialization, weak-HS
    forcing, or output interpolation.
- Possible regressions:
  - The accepted residual amplitude may already be optimal; capping it could
    undercorrect day-1 `2m_temperature`.
  - Long-lead surface residual behavior may change indirectly because low-mode
    residual memory persists to later leads.

## Risks

- Numerical stability:
  - Low. This is bounded output-side residual behavior after a finite trajectory.
- Compute cost:
  - Low. It reuses existing lower-column stability diagnostics and simple caps.
- Data leakage:
  - Low. Uses only same-time initial and forecast fields already available to
    the incumbent residual logic.
- Physical plausibility:
  - Moderate to high. Bulk Richardson and lower-column stability are standard
    controls for surface-layer coupling, but this is still an empirical
    residual limiter.
- Rollback complexity:
  - Low. The implementation can be isolated behind one boolean flag.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_name>`.
  - Require finite outputs and no diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_name> --workers 4`.
  - Support requires iteration primary delta at least `+0.002` against
    `-0.5150627015910243` with clean early and variable-lead RMSE guardrails.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_name> --workers 4`
    only if iteration promotes.
  - Require validation primary delta at least `+0.001` against
    `-0.5044433981077879`.
- Outcome that would falsify the hypothesis:
  - Any early `2m_temperature` guardrail failure, or a clean subthreshold result
    resembling `lead-decayed-analysis-hs-equilibrium` and
    `smooth-analysis-hs-spectral-taper`, would show that residual amplitude is
    not an actionable remaining error source.

## Citations

- Louis, J. F. 1979. "A parametric model of vertical eddy fluxes in the
  atmosphere." Boundary-Layer Meteorology, 17, 187-202.
  https://doi.org/10.1007/BF00117978
- Stull, R. B. 1988. "An Introduction to Boundary Layer Meteorology." Kluwer
  Academic Publishers. https://doi.org/10.1007/978-94-009-3027-8
- Mahrt, L. 1999. "Stratified Atmospheric Boundary Layers." Boundary-Layer
  Meteorology, 90, 375-396. https://doi.org/10.1023/A:1001765727956
- Holtslag, A. A. M., and Boville, B. A. 1993. "Local Versus Nonlocal
  Boundary-Layer Diffusion in a Global Climate Model." Journal of Climate, 6,
  1825-1842. https://doi.org/10.1175/1520-0442(1993)006<1825:LVNBLD>2.0.CO;2
- Source context: `src/dynamaxx/dycore/models/dinosaur/adapter.py` contains the
  incumbent scale-separated residual split and lower-column stability proxy.

## Researcher Notes

This deliberately avoids the recent failed residual-rate and residual-memory
families. It does not change residual decay hours, lead decay, seasonal gates,
analysis-HS equilibrium, or spectral taper. The mechanism is a bounded
amplitude safety valve for surface residuals in stable weak-shear columns,
which is different from `analysis-offset-relaxation-rate-mask`,
`lead-decayed-analysis-hs-equilibrium`, `barotropic-analysis-hs-equilibrium-offset`,
and `smooth-analysis-hs-spectral-taper`.

## Evaluator Notes

### 2026-06-21T02:45:40Z

Decision: move to `staging`; plausible but not the next model-selection run.

The proposal is narrower than the rejected residual-memory and residual-decay
experiments because it preserves the accepted decay schedule and targets only
stable weak-shear amplitude. The physical mechanism is coherent: lower-column
stability can modulate surface coupling, and a bounded amplitude cap is easier
to roll back than changing weak-HS rates or analysis-HS masks.

Keep it staged because the accepted scale-separated residual path is now a
fragile high-value part of the incumbent. Recent evidence shows that coarse
surface-residual changes can be strongly negative: seasonal/stability residual
decay regressed iteration by `-0.018957530153108526` with an early T2m guardrail
failure, broad residual-memory follow-ups were poor, and
`analysis-offset-relaxation-rate-mask` caused severe T2m/MSLP guardrail
failures. This proposal also relies on empirical amplitude caps, which raises
overfit and early `2m_temperature` risk. Reconsider after a read-only residual
amplitude distribution or if lower-risk initialization candidates are exhausted.
