---
schema_version: 1
slug: coriolis-rotated-surface-wind-residual
title: Rotate Near-Surface Wind Residuals With Local Inertial Phase
status: ready
created_at: 2026-06-18T08:47:58Z
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

# Rotate Near-Surface Wind Residuals With Local Inertial Phase

## Hypothesis

The accepted near-surface residual correction adds the lead-zero model-minus-
analysis residual back to `2m_temperature`, `10m_u_component_of_wind`, and
`10m_v_component_of_wind` as fixed grid-component anomalies with a 48 hour
decay. The accepted exact-Coriolis Lie and Strang rollout improvements show
that resolved wind phase under planetary rotation matters for the fixed
protocol.

If part of the remaining 10 m wind error is an unresolved near-surface
ageostrophic component, the residual vector should rotate approximately with
the local inertial frequency as it decays. Rotating the accepted near-surface
wind residual vector should improve `10m_u_component_of_wind` without changing
the prognostic trajectory, weak-HS forcing, DFI, initialization, diffusion,
time stepping, output variables, or fixed evaluation protocol.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual`.
Preserve the accepted Strang incumbent exactly, except for the diagnostic
near-surface wind residual update.

Modify the optional near-surface residual path:

- leave the `2m_temperature` residual correction exactly on the incumbent
  scalar decay path;
- when both 10 m wind components are available in the initial analysis and
  output variables, compute the lead-zero residual vector
  `(u_analysis - u_raw_lead0, v_analysis - v_raw_lead0)`;
- for each requested lead, rotate that residual vector by the local inertial
  angle `f * lead_seconds`, with `f = 2 * Omega * sin(latitude)` and the same
  rotation sign convention as the accepted exact-Coriolis step filter;
- multiply the rotated residual by the existing fixed 48 hour exponential
  decay and add it to the raw 10 m wind forecast;
- keep lead zero exactly equal to the analysis;
- if either 10 m wind component is absent, fall back to the incumbent scalar
  residual behavior for the present component.

This is output-diagnostic physics for the accepted residual, not a new decay
timescale and not a forecast-contract change.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Inputs, outputs, variable names, lead times, and protocols remain
    fixed.
- Tests to update:
  - Verify the candidate factory preserves all Strang incumbent flags and only
    changes the near-surface wind residual mode.
  - Unit-test zero lead exactly reproduces analyzed 10 m wind components.
  - Unit-test an equatorial column has no inertial residual rotation.
  - Unit-test northern and southern hemisphere residual rotations have opposite
    signs under the accepted Coriolis convention.
  - Verify fallback to incumbent scalar residual behavior when only one wind
    component is available.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at day 2 and later if fixed-component residuals
    are currently phase-wrong as the accepted residual decays.
  - Primary score may improve without spending mass-field guardrail margin
    because the prognostic vorticity, divergence, temperature, and pressure
    trajectory are unchanged.
- Expected neutral metrics:
  - `2m_temperature`, `geopotential_500`, and `mean_sea_level_pressure` should
    be effectively unchanged aside from any shared output packing roundoff.
- Possible regressions:
  - If the accepted fixed-component residual is empirically compensating a
    stationary surface bias rather than an inertial residual, rotation will hurt
    `10m_u_component_of_wind`.
  - The fixed target only scores 10 m zonal wind, so rotating residual into the
    meridional component can reduce scored zonal correction at some latitudes
    and leads.

## Risks

- Numerical stability:
  - Low. The mechanism is output-only and has finite fallbacks.
- Compute cost:
  - Low. It adds one latitude-dependent sine/cosine rotation over requested
    output leads and fits the reported `--workers 4` evaluation budget.
- Data leakage:
  - Low. It uses only the same lead-zero analysis residual already used by the
    accepted residual correction plus deterministic latitude and lead time.
    There is no validation feedback, learned climatology, or truth use beyond
    the initial condition.
- Physical plausibility:
  - Moderate. Inertial rotation is a first-order model for ageostrophic wind
    residuals, but the real boundary layer also has friction, surface coupling,
    and diurnal forcing that this simple diagnostic does not represent.
- Rollback complexity:
  - Low. Remove one adapter option, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day 1-5 RMSE guardrail failure, and no variable+lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, especially with a 10 m zonal
    wind regression, would show that the accepted residual is better treated as
    a fixed component bias under this evaluation. Any movement in mass or Z500
    metrics should be treated as an implementation bug because the trajectory
    is intended to be unchanged.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  `_apply_near_surface_residual_correction` and the accepted exact-Coriolis
  rotation filter used by the Strang incumbent.
- History: `.logbook/history/2026-06-16_14-27-30_near-surface-anomaly-diagnostics/decision.md`
  accepted decaying near-surface diagnostic residuals with validation delta
  `+0.03575996912567381`.
- History: `.logbook/history/2026-06-18_04-38-06_symmetric-coriolis-rotation-split/decision.md`
  accepted the Strang exact-Coriolis rollout split with iteration delta
  `+0.003720976790028363`, motivating a wind-phase-aware residual diagnostic.
- History: `.logbook/history/2026-06-17_13-35-18_surface-layer-diagnostic-extrapolation/decision.md`
  rejected a broader surface-layer diagnostic extrapolation, so this proposal
  changes only the already accepted residual vector geometry.
- Blackadar, A. K. 1957. Boundary Layer Wind Maxima and Their Significance for
  the Growth of Nocturnal Inversions. Bulletin of the American Meteorological
  Society. https://doi.org/10.1175/1520-0477-38.5.283
- Van de Wiel, B. J. H., Moene, A. F., Steeneveld, G. J., Baas, P., Bosveld,
  F. C., and Holtslag, A. A. M. 2010. A Conceptual View on Inertial
  Oscillations and Nocturnal Low-Level Jets. Journal of the Atmospheric
  Sciences. https://doi.org/10.1175/2010JAS3289.1
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.
  https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not a duplicate of the accepted Strang Coriolis rollout: the forecast
trajectory remains the incumbent trajectory, and only the output residual vector
is rotated. It is also not another DFI-only consistency proposal and does not
change DFI, initialization, or the Coriolis operator inside the dycore.

This deliberately avoids the rejected broader surface diagnostic family. It
does not extrapolate 2 m temperature or 10 m wind from sigma-layer shear, does
not touch MSLP or Z500, and does not add new residual channels. The main risk is
that the idea is output-facing and may be judged too narrow or too close to the
accepted residual correction; if selected, guardrail review should focus on
whether 10 m zonal wind improves without any unintended mass-field movement.

## Evaluator Notes

### 2026-06-18T08:53:53Z

Decision: move to `ready`; rank 1 for the next Orchestrator selection pass.

This is the best current candidate because it is a tightly scoped side-by-side
test on top of the accepted Strang incumbent. The accepted near-surface
residual produced a large validation gain (`+0.03575996912567381`) without
moving mass fields, and the accepted Lie and Strang Coriolis split experiments
showed that wind phase under planetary rotation still matters. The latest
DFI-Coriolis rejection was only a sub-threshold initialization-consistency test;
it does not falsify an output-only residual-vector geometry change.

Source inspection confirms the accepted residual correction is localized in
`_apply_near_surface_residual_correction`, while the exact Coriolis rotation
sign convention is already encoded in `_exact_coriolis_rotation_step_filter`.
This makes implementation and rollback low cost. A literature spot-check
supports the general inertial-oscillation mechanism for residual-layer and
low-level jet winds, but the proposal remains an approximation because the
boundary layer includes friction, surface coupling, and non-inertial forcing.

The main risks are metric and implementation risks. The fixed target scores
only `10m_u_component_of_wind`, so rotating residual energy into the meridional
component may reduce the currently helpful zonal residual if the incumbent
residual is mostly a stationary bias. The current output request may not include
`10m_v_component_of_wind`, so an implementation must either compute the hidden
raw 10 m meridional diagnostic safely or fall back to the incumbent scalar
residual when the vector is unavailable. Guardrails should require
near-roundoff movement for `2m_temperature`, `geopotential_500`, and
`mean_sea_level_pressure`; any mass-field movement would indicate an
implementation bug.
