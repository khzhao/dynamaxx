---
schema_version: 1
slug: hydrostatic-theta-monotone-initialization
title: Limit Hydrostatic Initialization to Monotone Potential Temperature
status: staging
created_at: 2026-06-18T14:33:12Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
expected_code_paths:
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

# Limit Hydrostatic Initialization to Monotone Potential Temperature

## Hypothesis

The accepted hydrostatic layer-mean initialization improved the incumbent, but
it estimates temperature from finite pressure-level geopotential thicknesses.
Layer-thickness differencing can introduce small local static-instability or
over-sharpened thermal structures when pressure levels are coarse or noisy. A
one-time monotone-potential-temperature limiter applied only to the initialized
hydrostatic temperature profile may reduce spinup from unphysical vertical
thermal structure while avoiding the broad rollout intervention that made dry
static-stability adjustment unattractive.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_theta_init`.
Preserve all incumbent rollout physics and numerics after initialization.

Add an opt-in preprocessing step inside `weather_state_to_dinosaur_state`, after
the accepted layer-mean hydrostatic temperature estimate is computed on pressure
levels and before pressure-to-sigma interpolation:

- compute dry potential temperature from the hydrostatic temperature and
  pressure-level centers;
- scan each vertical column for adjacent pairs where potential temperature
  decreases upward beyond a small fixed tolerance;
- minimally mix only unstable adjacent pairs to a neutral potential-temperature
  value while preserving pair-mean dry temperature in pressure-log thickness
  weights;
- cap the absolute temperature change per pressure level, for example at 2 K, so
  this remains an initialization limiter rather than a new thermal analysis;
- leave analyzed winds, surface pressure, humidity tracers, geopotential input,
  DFI span, weak-HS forcing, Coriolis split, horizontal diffusion, and output
  diagnostics unchanged;
- fall back to the incumbent hydrostatic temperature if the limiter would produce
  nonfinite values.

The candidate should not add a post-step stability filter. It only guards the
hydrostatic temperature estimate used to initialize the accepted sigma state.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast input/output contracts, target variables, lead times, and
    protocols stay fixed.
- Tests to update:
  - Unit-test that a stable hydrostatic column is unchanged.
  - Unit-test that a synthetic unstable adjacent pair is neutralized within the
    fixed temperature-change cap.
  - Verify humidity, winds, surface pressure, and output variable routing are
    unchanged by the option.
  - Verify the candidate factory preserves every Strang incumbent flag except
    the new initialization limiter.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - Day-1 to day-5 `geopotential_500` and MSLP if residual thermal imbalance in
    the initialized column still contributes to spinup after DFI.
  - `2m_temperature` may improve modestly if low-level hydrostatic temperature
    spikes are clipped before sigma interpolation.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be less exposed than in wind
    initialization experiments because winds and Coriolis treatment are
    unchanged.
  - Long leads should remain close to the incumbent if the limiter only removes
    rare local initialization outliers.
- Possible regressions:
  - The accepted hydrostatic layer-mean temperature estimate may already be
    optimal for aggregate score, and limiting it can remove useful analyzed
    stratification.
  - Thermal changes can still perturb pressure gradients after DFI and indirectly
    move winds.

## Risks

- Numerical stability:
  - Low to moderate. The limiter removes static instability but must be capped to
    avoid discontinuous thermal-profile edits.
- Compute cost:
  - Low. It is a one-time column operation during initialization, not an inner
    step filter.
- Data leakage:
  - None. It uses only same-time initial analysis fields and fixed physical
    constants.
- Physical plausibility:
  - Moderate. Dry static stability is physically meaningful, but real lower-
    tropospheric adjustment is moist and turbulent; this candidate deliberately
    limits only the hydrostatic preprocessing artifact.
- Rollback complexity:
  - Low. Remove one initialization option/helper, one factory/export, one
    registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_theta_init`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_theta_init --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_theta_init --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative iteration delta would show that the accepted hydrostatic
    layer-mean initialization should not be constrained this way. Any early Z500,
    MSLP, or wind guardrail failure would show that even capped initialization
    thermal edits disrupt balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  `_layer_mean_hydrostatic_temperature_from_geopotential_thickness` before
  pressure-to-sigma interpolation in the accepted initialization path.
- History: `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init/decision.md`
  accepted the layer-mean hydrostatic initialization with iteration delta
  `+0.004688970185515728`; this proposal preserves that mechanism and only
  guards local static-stability outliers.
- History: `.logbook/history/2026-06-18_07-30-18_sigma-native-hydrostatic-initialization/decision.md`
  rejected sigma-native hydrostatic initialization with iteration delta
  `-0.008345744027537627`; this proposal does not change to sigma-native
  reconstruction.
- Research scrap: `.logbook/research/scrap/mass-conserving-dry-static-stability-adjustment.md`
  rejected a post-step dry stability filter as too broad; this proposal is
  initialization-only and leaves the rollout untouched.
- Manabe, S. and Strickler, R. F. 1964. Thermal equilibrium of the atmosphere
  with a convective adjustment. Journal of the Atmospheric Sciences.
  https://journals.ametsoc.org/view/journals/atsc/21/4/1520-0469_1964_021_0361_teotaw_2_0_co_2.xml
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0
- Wallace, J. M. and Hobbs, P. V. 2006. Atmospheric Science: An Introductory
  Survey, second edition, discusses potential temperature and dry static
  stability. https://doi.org/10.1016/C2009-0-00034-8

## Researcher Notes

This is not a duplicate of the scrapped dry static-stability adjustment because
it does not run after each forecast step, does not repeatedly alter thermal
structure, and does not add a discontinuous rollout filter. It is also not a
duplicate of rejected `sigma-native-hydrostatic-initialization`, because it keeps
the accepted pressure-level layer-mean hydrostatic construction and only applies
a capped monotone-theta guard before the existing log-pressure sigma remap.

The proposal uses recent negative evidence directly: broad thermodynamic rollout
edits and sigma-native reconstruction were harmful, so this candidate narrows
the intervention to rare initialization outliers while preserving all accepted
Strang-Coriolis dynamics.

## Evaluator Notes

### 2026-06-18T14:37:31Z

Decision: move to `staging`, not `ready`.

The proposal is physically recognizable and narrower than the scrapped
post-step dry static-stability adjustment. It preserves the accepted
pressure-level layer-mean hydrostatic initialization and applies only a
one-time, capped potential-temperature monotonicity guard before the existing
sigma remap. That makes it a plausible later initialization experiment rather
than a duplicate of the rejected sigma-native hydrostatic reconstruction.

Keep it staged because recent evidence argues against spending the next run on
another thermal initialization edit. Sigma-native hydrostatic initialization
regressed by `-0.008345744027537627`, variable-selective pressure
initialization regressed by `-0.005133070800804607`, and thermal-profile edits
have repeatedly risked short-lead Z500, MSLP, or wind balance. The cap and
pairwise mixing rules also introduce tunable choices without diagnostics
showing frequent unstable hydrostatic-initialization columns. It ranks behind
the ready hypsometric Z diagnostic, which changes only one scored output
diagnostic and leaves the initialized state and rollout untouched.
