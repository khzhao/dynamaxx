---
schema_version: 1
slug: barotropic-analysis-hs-equilibrium-offset
title: Project the Analysis-HS Equilibrium Offset onto Barotropic Thermal Modes
status: ready
created_at: 2026-06-20T22:43:21Z
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

# Project the Analysis-HS Equilibrium Offset onto Barotropic Thermal Modes

## Hypothesis

The accepted analysis-offset Held-Suarez equilibrium was the strongest recent
gain, but it keeps the full vertical structure of the initialized low-mode
temperature offset. Recent follow-ups show the offset itself is useful, while
weakening the relaxation rate is damaging and a simple lead decay is too weak.
A mass-weighted barotropic projection should retain the beneficial large-scale
analysis-conditioned equilibrium shift while removing vertical baroclinic
offset components that can perturb hydrostatic thickness, MSLP, and Z500.

## Mechanism

Add one side-by-side candidate, for example suffixing the incumbent with
`_barotropic_analysis_hs_eq`. Keep DFI, weak-HS rates, Strang Coriolis split,
theta tendency, theta recentering, off-centering, scale-separated residuals,
output variables, lead schedule, and fixed metrics unchanged.

For the candidate only, replace the accepted analysis-HS offset helper with a
vertical projection:

- compute the incumbent bounded low-horizontal-wavenumber temperature offset;
- form a sigma-layer-mass-weighted column mean offset at each horizontal grid
  point;
- re-expand that column mean through the vertical with a fixed broad lower- and
  mid-tropospheric taper, leaving the top few sigma layers weakly affected;
- preserve the existing horizontal low-mode mask and Kelvin cap after the
  vertical projection;
- fall back exactly to the incumbent accepted offset if the projection is
  nonfinite or shape-incompatible.

This keeps the stabilizing weak-HS relaxation rate untouched. It changes the
vertical structure of the accepted equilibrium target, not the relaxation
strength, time decay, DFI state, or forecast contract.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one factory and registry key for the side-by-side candidate only.
- API changes:
  - None.
- Tests to update:
  - Verify the projected offset has the same horizontal low-mode mask and cap as
    the incumbent accepted offset.
  - Verify finite fallback reproduces the incumbent offset.
  - Verify the candidate factory preserves every incumbent option except the new
    vertical projection selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500`, especially around the
    medium leads where accepted analysis-HS had small pressure regressions.
  - `2m_temperature` should retain most accepted analysis-HS benefit because
    the weak-HS rate and lower-column equilibrium anchoring remain.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, since momentum and the Richardson diagnostic are
    unchanged.
- Possible regressions:
  - Removing useful vertical offset structure can weaken the accepted gain.
  - A vertically smoothed thermal target can still alter baroclinic growth and
    pressure-gradient phase.

## Risks

- Numerical stability:
  - Low to moderate; the offset remains bounded but changes a thermal forcing
    target every step.
- Compute cost:
  - Negligible relative to the incumbent.
- Data leakage:
  - None; it uses only the same initial forecast state already used by the
    accepted analysis-HS candidate.
- Physical plausibility:
  - Moderate. Large-scale radiative-equilibrium offsets should be vertically
    coherent compared with noisy layerwise analysis increments.
- Rollback complexity:
  - Low.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A subthreshold or negative clean iteration delta would show that the
    accepted full-depth offset structure is already better than the barotropic
    projection. Any early MSLP/Z500 or T2m guardrail failure would show the
    projection disrupts balance.

## Citations

- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society. https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AECAAM%3E2.0.CO;2
- Jablonowski, C. and Williamson, D. L. 2011. The pros and cons of diffusion,
  filters and fixers in atmospheric general circulation models. In Numerical
  Techniques for Global Atmospheric Models, Springer.
- Dynamaxx history:
  `.logbook/history/2026-06-20_10-50-51_analysis-offset-held-suarez-equilibrium/decision.md`
  accepted the low-mode analysis-HS equilibrium offset.
- Dynamaxx history:
  `.logbook/history/2026-06-20_19-13-38_analysis-offset-relaxation-rate-mask/decision.md`
  rejected weakening the weak-HS rate, so this proposal preserves the rate.

## Researcher Notes

This is a near-family follow-up to the accepted analysis-HS mechanism, but the
mechanism is materially different from the rejected rate mask and lead taper:
it does not reduce damping and does not time-decay the offset. It tests whether
the accepted gain comes mainly from large-scale barotropic thermal anchoring,
while avoiding potentially harmful vertical baroclinic offset structure.

## Evaluator Notes

### 2026-06-20T22:47:09Z

Decision: move to `ready`; ranked first of the three triaged proposals.

This is the strongest next candidate because it stays closest to the only
recent large positive signal: the accepted analysis-offset Held-Suarez
equilibrium improved iteration by `+0.016990568302663656` and validation by
`+0.01745893975367474` with clean guardrails. The proposal preserves the weak-HS
relaxation rate, DFI path, Coriolis split, theta recentering, off-centering,
surface residuals, and output diagnostics, so it avoids the failure mode of the
analysis-offset rate mask, which weakened stabilizing thermal damping and
caused severe `2m_temperature` and MSLP guardrail regressions.

The follow-up evidence is cautionary but not disqualifying. Computing the same
offset from the DFI-balanced state was clean but slightly negative, and
lead-decaying the offset was clean but subthreshold at
`+0.0002465885628093467`; both imply that trivial reordering or tapering is not
enough. A vertical barotropic projection is a larger physical difference while
remaining low-surface-area and bounded. It directly tests whether the accepted
gain comes from large-scale column thermal anchoring while reducing potentially
harmful baroclinic equilibrium increments that could affect MSLP/Z500. If it is
subthreshold or harms mass-field guardrails, that should close this immediate
analysis-HS projection branch.
