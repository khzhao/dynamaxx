---
schema_version: 1
slug: mass-conserving-dry-static-stability-adjustment
title: Mass-Conserving Dry Static-Stability Adjustment
status: scrap
created_at: 2026-06-17T21:12:20Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Mass-Conserving Dry Static-Stability Adjustment

## Hypothesis

The incumbent is a dry primitive-equation rollout with weak thermal relaxation
but no explicit dry convective stability constraint. During multi-day free
integration, vertical advection and adiabatic tendencies can create locally
superadiabatic or weakly unstable temperature profiles that project onto
near-surface temperature, pressure thickness, and geopotential errors. A
conservative dry static-stability adjustment may reduce those unphysical
vertical structures without using humidity feedback, latent heating, direct
surface post-processing, new data, or metric-specific tuning.

## Mechanism

Add a side-by-side candidate with a post-step dry stability filter. The filter
converts `temperature_variation` and `log_surface_pressure` to nodal
temperature and sigma-level pressure, computes dry potential temperature, and
detects adjacent layers where potential temperature decreases with height
beyond a small numerical tolerance. For unstable adjacent pairs, replace the
pair with a mass-weighted neutral profile that preserves the pair's dry
enthalpy or mass-weighted temperature while making potential temperature
monotone. Convert the adjusted temperature back to modal
`temperature_variation`; leave vorticity, divergence, log surface pressure, and
humidity tracers unchanged.

The adjustment should be deterministic, local to each column, and implemented
as a model step filter composed with the existing step filters. It is not a
surface diagnostic correction and not a saturation or latent-heating scheme.
The intended physical analogue is dry convective adjustment: redistribution of
column heat to remove statically unstable dry layers.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` or a focused
    helper module if the filter is clearer outside the equation class
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
- Registry changes:
  - Add a factory such as
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_dry_static_adjust`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, and protocols
    stay fixed.
- Tests to update:
  - Verify the adjustment removes a synthetic adjacent-layer dry instability.
  - Verify a stable profile is unchanged.
  - Verify column mass-weighted temperature or dry enthalpy is conserved within
    floating-point tolerance for adjusted pairs.
  - Verify the registered candidate emits finite forecasts on existing
    fixtures.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` may improve if long-lead cold or unstable lower-column
    drift is partly caused by dry vertical structure errors.
  - `geopotential_500` may improve if temperature thickness errors are reduced
    without changing pressure diagnostics directly.
- Expected neutral metrics:
  - `mean_sea_level_pressure` should be less affected than in humidity-heating
    experiments because log surface pressure is not directly modified.
- Possible regressions:
  - `10m_u_component_of_wind` can regress through thermal-wind and pressure
    gradient changes, the same guardrail that rejected full-column thermal
    recentering.
  - If the incumbent rarely creates dry static instability, the proposal may be
    neutral while adding cost.

## Risks

- Numerical stability:
  - Medium. Static-stability adjustment should remove a source of instability,
    but discontinuous pairwise adjustment can introduce shocks in vertical
    temperature gradients if not implemented smoothly and conservatively.
- Compute cost:
  - Medium. It requires nodal transforms and column operations during stepping,
    but no new data, training, or large dependencies.
- Data leakage:
  - None. The adjustment uses only forecast state variables and fixed physical
    constants.
- Physical plausibility:
  - Medium. Dry convective adjustment is physically established, but real
    atmospheric convection is moist and nonlocal; this proposal deliberately
    uses only a dry conservative limiter to avoid the recently failed humidity
    feedback and saturation-heating families.
- Rollback complexity:
  - Low to medium. The candidate is side-by-side, but step-filter plumbing must
    be isolated so rollback is a factory/flag removal.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate> --workers 4`.
  - Require clean diagnostics, no fixed RMSE guardrail failures, and at least
    `+0.002` primary improvement.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate> --workers 4` only
    after iteration promotion.
  - Require clean diagnostics, no fixed RMSE guardrail failures, and at least
    `+0.001` validation primary improvement.
- Outcome that would falsify the hypothesis:
  - Early `10m_u_component_of_wind` guardrail failure, mass-field guardrail
    failure, or a clean negative primary-score delta would show that dry
    stability adjustment is either too intrusive or not a relevant incumbent
    error source.

## Citations

- Manabe, S. and Strickler, R. F. 1964. Thermal equilibrium of the atmosphere
  with a convective adjustment. Journal of the Atmospheric Sciences, 21,
  361-385.
  https://journals.ametsoc.org/view/journals/atsc/21/4/1520-0469_1964_021_0361_teotaw_2_0_co_2.xml
- Manabe, S. and Wetherald, R. T. 1967. Thermal equilibrium of the atmosphere
  with a given distribution of relative humidity. Journal of the Atmospheric
  Sciences, 24, 241-259.
  https://climate-dynamics.org/wp-content/uploads/2016/06/manabe67.pdf
- GFDL bibliography copy of Manabe and Strickler 1964.
  https://www.gfdl.noaa.gov/bibliography/related_files/sm6401.pdf
- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society, 75, 1825-1830.
  https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2

## Researcher Notes

This proposal is low confidence. It is deliberately not another humidity
proposal: it does not use moisture in dynamics, saturation adjustment, or
latent heating, all of which have strong recent negative evidence. It is also
not the rejected `layer-mean-thermal-recentering` family because it does not
freeze or recenter a global modal temperature mean; it only removes local dry
static instabilities while preserving column heat. The main risk is that the
fixed metrics may punish any thermodynamic intervention through early low-level
wind changes.

## Evaluator Notes

### 2026-06-17_21-15-13Z

Decision: `scrap`.

The dry-convective-adjustment analogy is scientifically recognizable, but the
proposal is a broad per-step thermodynamic intervention for this incumbent. It
requires repeated modal-to-nodal reconstruction, pressure/sigma thermodynamic
diagnostics, pairwise column adjustment, and conversion back into modal
temperature tendencies or state fields. That surface area is large relative to
the evidence that dry static instability is a material remaining error source
under the fixed WeatherBench2 metrics.

Recent decisions make the risk unfavorable. Full-column thermal recentering had
a primary-score signal but failed the early 10 m wind guardrail; the
low-level-sparing thermal limiter avoided that guardrail but lost the primary
benefit; saturation adjustment improved `2m_temperature` while degrading
pressure, height, and wind fields. This proposal again perturbs thermal
structure during rollout, with likely thermal-wind and pressure-gradient
side-effects, and adds discontinuous column operations that are harder to
reason about than the accepted initialization changes. It should not consume
the next implementation slot without new diagnostics showing frequent dry
static instability in the incumbent trajectory.
