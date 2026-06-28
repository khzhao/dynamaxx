---
schema_version: 1
slug: dse-consistent-sigma-initialization
title: Dry-static-energy-consistent sigma initialization for the mass-DSE HSL incumbent
status: ready
created_at: 2026-06-24T08:38:37Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/registry.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - tests/dycore/
expected_eval_protocols:
  - fixed_fast
  - fixed_iteration
  - fixed_validation
---

## Hypothesis

The incumbent now advances the horizontal thermal transport as a layer-mass-weighted dry-static-energy anomaly, but its sigma initial condition is still produced through temperature interpolation after the hydrostatic layer-mean preprocessing step. A side-by-side model that initializes the sigma thermal state by projecting the analysis onto the same dry-static-energy anomaly used by the rollout should reduce initial thermal adjustment without changing the forecast contract.

This should be most useful at short leads, where the rejected vertical-DSE candidate showed that thermal-energy information is high-signal but dangerous when it excites pressure adjustment during the rollout.

## Mechanism

Add a candidate such as `dino_mass_dse_init` derived from `dino_hsl2_mass_dse`.

In `weather_state_to_dinosaur_state`, after the incumbent pressure-level hydrostatic/layer-mean temperature construction:

1. Build the pressure-level dry static energy scalar `s = Cp * T_hydro + Phi` using the analysis geopotential already available on pressure levels.
2. Remove a horizontal mean or level-wise reference consistent with `nodal_dry_static_energy_anomaly`, so the projection initializes the anomaly transported by the incumbent rather than a global offset.
3. Interpolate the dry-static-energy anomaly from pressure levels to sigma levels with the same log-pressure sigma mapping used by the incumbent initialization.
4. Use the incumbent interpolated sigma temperature as the first estimate, compute its sigma dry static energy with the existing hydrostatic geopotential diagnostic, and apply a bounded local correction `delta_T = (s_sigma_projected - s_sigma_current) / Cp`.
5. Recompute `temperature_variation` from the corrected sigma temperature. Keep winds, humidity, surface pressure, and output diagnostics unchanged.

The implementation should include finite checks and fall back to the incumbent initialization if the projected scalar or temperature correction is non-finite or exceeds a conservative physical cap. This is a one-time initialization projection, not a hydrostatic inversion of the tendency operator.

## Implementation Scope

This is a model-factory and adapter change only. Add an opt-in initialization flag to `DinosaurPrimitiveEquationsDycoreModel`, thread it through the incumbent-derived factory, and register the new side-by-side key in `registry.py`.

Expected tests should cover that the new factory is registered, the weather-state conversion preserves array shapes, and the fallback path reproduces incumbent initialization when the DSE projection is disabled or invalid.

## Expected Metric Movement

Expected aggregate movement is modestly positive relative to the incumbent, with the best chance of improvement in day-1 to day-5 `Z500`, `MSLP`, and near-surface temperature consistency. The proposal should not rely on a lead-specific metric patch; the physical target is reducing the initialization mismatch between the transported invariant and the starting sigma thermal state.

I would expect a smaller upside than the accepted DSE-HSL and layer-mass-weighted DSE-HSL changes, but a lower MSLP guardrail risk than unguarded vertical-DSE rollout transport because no new vertical tendency is applied during integration.

## Risks

The pressure-level geopotential and sigma hydrostatic geopotential diagnostics are not identical operators, so the projected scalar can introduce a small temperature shock if the correction is too aggressive. The bounded correction and finite fallback are important. If the incumbent initialization error is not a material source of the current residual, the candidate may be neutral.

This should not be implemented as a direct hydrostatic inversion of the prognostic tendency, because the rejected hydrostatic-inverted mass-DSE follow-up is strong negative evidence against that direction.

## Evaluation Plan

Run the standard fixed fast check first to catch shape and finite-value failures. If clean, run fixed iteration against `dino_hsl2_mass_dse` and inspect aggregate score plus the early `MSLP` and `Z500` guardrails. Only promote to fixed validation if iteration improves without a short-lead pressure or height regression.

Keep all evaluation protocols unchanged.

## Citations

- Simmons, A. J., and D. M. Burridge, 1981: An energy and angular-momentum conserving vertical finite-difference scheme and hybrid vertical coordinates. *Monthly Weather Review*, 109, 758-766. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Staniforth, A., and J. Cote, 1991: Semi-Lagrangian integration schemes for atmospheric models: A review. *Monthly Weather Review*, 119, 2206-2223. https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Durran, D. R., 2010: *Numerical Methods for Fluid Dynamics: With Applications to Geophysics*. Springer.
- Laprise, R., 1992: The Euler equations of motion with hydrostatic pressure as an independent variable. *Monthly Weather Review*, 120, 197-207. https://doi.org/10.1175/1520-0493(1992)120%3C0197:TEEOMW%3E2.0.CO;2

## Researcher Notes

This proposal follows the accepted DSE-HSL and mass-DSE-HSL path but moves the new idea to initialization rather than adding another rollout tendency. It is intentionally distinct from `pressure-thickness-corrected-mass-dse-hsl`, `hydrostatic-inverted-mass-dse-hsl`, and `vertical-dse-transport-mass-hsl`: it does not add a product-rule pressure-thickness correction, does not invert the hydrostatic tendency operator, and does not add unguarded vertical DSE transport.

I did not find an existing active proposal for DSE-consistent sigma initialization. Nearby staged initialization ideas focus on hydrostatic theta, shape-preserving log-pressure interpolation, or low-mode surface-pressure initialization, so this is a separate candidate tied directly to the incumbent's transported scalar.

## Evaluator Notes

### 2026-06-24T09:35:00Z

Decision: move to `ready`; rank 1 of 3 new proposals.

This is the best next experiment because it targets the current incumbent's
clearest unresolved consistency gap with the smallest behavioral surface. The
accepted DSE-HSL and layer-mass-weighted DSE-HSL history shows that dry-static-
energy horizontal transport is high-value. Recent pressure-thickness and
hydrostatic-inversion follow-ups show that adding more rollout coupling is
fragile, especially for early MSLP. This proposal avoids that failure mode by
changing only the initial sigma thermal state, not the positive-time tendency,
pressure continuity, or momentum equations.

The mechanism is also distinct from the active staged queue. Existing staged
mass-DSE ideas mostly project, limit, or time-center the incumbent tendency;
existing initialization ideas focus on interpolation shape, theta monotonicity,
or surface-pressure/hypsometric offsets. A bounded projection of the analysis
onto the same DSE anomaly transported by the incumbent is a more direct test of
initial scalar mismatch and is cheap to roll back.

Implementation guardrails matter: keep the incumbent layer-mean hydrostatic
temperature as the first estimate, compute only a bounded local temperature
correction from the projected DSE anomaly, require finite diagnostics, and fall
back exactly to `dino_hsl2_mass_dse` on invalid or overlarge corrections. This
should run before broader split-step or humidity-coupled variants. Promote to
validation only if fixed iteration improves and early MSLP/Z500 guardrails stay
clean.
