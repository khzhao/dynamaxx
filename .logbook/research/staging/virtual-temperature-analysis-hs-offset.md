---
schema_version: 1
slug: virtual-temperature-analysis-hs-offset
title: Compute the Analysis-HS Offset From Virtual-Temperature Anomalies
status: staging
created_at: 2026-06-20T20:51:54Z
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

# Compute the Analysis-HS Offset From Virtual-Temperature Anomalies

## Hypothesis

The accepted analysis-offset Held-Suarez equilibrium compares dry analyzed
temperature to a dry idealized equilibrium. Prior history shows that fully
activating moist dynamics and adding latent heating are harmful, but also that
humidity is useful in geopotential reconstruction. A narrower use of humidity
is to remove the virtual-temperature part of the initial low-mode thermal
offset before it becomes a persistent dry relaxation target.

If the accepted offset is partly treating moist tropical thickness as a dry
temperature anomaly, a virtual-temperature-aware offset should preserve the
successful large-scale analysis anchoring while reducing humidity-correlated
Z500 and MSLP drift. The rollout remains dynamically dry and passive humidity
does not feed pressure gradients or heating.

## Mechanism

Register a side-by-side candidate with a suffix such as
`_analysis_hs_eq_virtual_t`. Preserve the incumbent trajectory, DFI,
weak-HS rates, Coriolis Strang split, theta tendency, theta recentering,
off-centering, residual memory, pressure-level outputs, and forecast contract.

For this candidate only:

- when computing the accepted analysis-HS equilibrium offset, convert the
  initialized sigma humidity tracer to nodal space if it is present;
- clip diagnostic humidity to a fixed physical range such as `[0, 0.04]` kg/kg
  and use it only inside the offset calculation;
- form a virtual-temperature anomaly
  `T_virtual = T * (1 + (R_v/R_d - 1) * q)` and compare that field to the
  standard Held-Suarez equilibrium;
- convert the retained low-mode virtual-temperature offset back to a dry
  temperature-equilibrium offset by dividing by the same bounded virtual
  factor, so the forcing still acts on dry temperature;
- retain the incumbent low-mode spectral mask and Kelvin cap after conversion;
- fall back exactly to the incumbent dry offset when humidity is absent,
  shape-incompatible, or nonfinite.

This is not moist dynamics, humidity-weighted radiative relaxation, saturation
adjustment, or a geopotential output change. Humidity is used once, at
initialization, to interpret the already accepted low-mode equilibrium offset.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate factory and registry entry only.
- API changes:
  - None. The candidate consumes only humidity channels already available to
    the incumbent adapter.
- Tests to update:
  - Verify absent humidity gives bytewise or tolerance-equivalent incumbent
    offset behavior.
  - Verify humidity is clipped and used only in the offset helper, not in
    primitive-equation dynamics.
  - Verify the final dry offset keeps the incumbent low-mode mask and Kelvin
    cap.
  - Verify nonfinite humidity falls back to the incumbent dry offset.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` in humid low latitudes and medium leads if dry offset
    anchoring currently misattributes moist thickness to dry warming.
  - `mean_sea_level_pressure` through improved low-mode thermal thickness
    consistency.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be close to incumbent because momentum
    tendencies and the Richardson diagnostic are unchanged.
  - `2m_temperature` should be protected by the same offset cap and accepted
    near-surface residual memory.
- Possible regressions:
  - If the dry analysis offset is already the empirically correct relaxation
    target, removing the humidity contribution can weaken useful tropical
    temperature anchoring.
  - Passive humidity may be noisy after initialization, so the implementation
    must use only the initialized field and fixed finite bounds.

## Risks

- Numerical stability:
  - Low. This changes a bounded equilibrium offset, not the active moist
    pressure-gradient dynamics that previously regressed.
- Compute cost:
  - Negligible. It adds one nodal humidity conversion while building the
    per-initial-condition offset.
- Data leakage:
  - None. It uses same-time initial humidity already present in the input.
- Physical plausibility:
  - Moderate to good. Virtual temperature is the standard dry-air-equivalent
    thermodynamic variable for hydrostatic thickness, but mapping it back into
    a dry Held-Suarez relaxation target is approximate.
- Rollback complexity:
  - Low. Remove one adapter flag/helper path, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_name> --workers 4`.
  - Support requires primary delta at least `+0.002`, clean diagnostics, no
    early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_name> --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same
    guardrails.
- Outcome that would falsify the hypothesis:
  - A negative or subthreshold iteration delta with Z500 or MSLP regression
    would show that virtual-temperature interpretation is not a useful
    successor to the accepted dry analysis offset.

## Citations

- Held, I. M. and Suarez, M. J. 1994. A proposal for the intercomparison of the
  dynamical cores of atmospheric general circulation models. Bulletin of the
  American Meteorological Society. https://doi.org/10.1175/1520-0477(1994)075%3C1825:APFTIO%3E2.0.CO;2
- Emanuel, K. A. 1994. Atmospheric Convection. Oxford University Press.
- Wallace, J. M. and Hobbs, P. V. 2006. Atmospheric Science: An Introductory
  Survey, 2nd edition. Academic Press.
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AECAAM%3E2.0.CO;2

## Researcher Notes

This deliberately avoids the rejected moist-dynamics, bounded saturation, and
humidity-radiative-relaxation mechanisms. The only new humidity role is
diagnostic interpretation of the accepted initial low-mode HS equilibrium
offset.

## Evaluator Notes

### 2026-06-20T20:56:31Z

Decision: move to `staging`; ranked second of the three new proposals.

The proposal is scientifically plausible and narrower than the rejected moist
dynamics family: humidity is used once to interpret the initial low-mode
analysis-HS offset, not to feed active pressure gradients, latent heating, or a
new output diagnostic. The dry-geopotential diagnostic rejection is useful
positive context for keeping humidity in diagnostic thickness calculations, so
virtual-temperature reasoning is not inherently invalid here.

Do not promote it ahead of the lead-decay offset. Local evidence around
humidity is mixed to negative for model-selection changes: active moist
virtual-temperature dynamics regressed iteration skill strongly, bounded moist
dynamics was clean but very negative, and previous humidity-relaxation or moist
feedback ideas are weak. The accepted dry analysis-HS offset is already a
strong incumbent; converting part of that offset through bounded humidity could
remove empirically useful tropical thermal anchoring. Keep staged as a later,
low-surface-area analysis-HS variant only after the simpler offset-memory
hypothesis is scored.
