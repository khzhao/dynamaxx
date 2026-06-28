---
schema_version: 1
slug: strang-split-mass-dse-hsl
title: Strang-split layer-mass DSE HSL transport around the primitive-equation step
status: staging
created_at: 2026-06-24T08:38:37Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fixed_fast
  - fixed_iteration
  - fixed_validation
---

## Hypothesis

The accepted mass-DSE incumbent embeds the layer-mass-weighted HSL remap as an explicit thermodynamic tendency inside the primitive-equation tendency evaluation. That improved the score, but the remaining error may include time-placement error between the semi-Lagrangian horizontal transport operator and the semi-implicit primitive-equation update. A side-by-side candidate that applies the mass-DSE HSL remap as a symmetric half-step operator around the core primitive-equation step may improve phase and balance without changing the remap trajectory, the metric, or the forecast contract.

## Mechanism

Add a candidate such as `dino_mass_dse_split_hsl` derived from the incumbent.

The implementation should treat the accepted layer-mass DSE HSL update as an operator rather than only as a tendency:

1. Build a reusable helper that applies a signed fractional HSL update to `delta_p * s'`, where `s'` is the incumbent dry-static-energy anomaly and `delta_p` is sigma-layer pressure thickness.
2. Convert the transported scalar increment back to a bounded temperature increment using the incumbent safe-thickness division and `/ Cp` conversion.
3. For positive forecast steps, apply a half-step mass-DSE HSL update, run the core primitive-equation step, and then apply a second half-step update using refreshed diagnostics.
4. Keep the core equation otherwise incumbent-compatible, but avoid double-counting the embedded mass-DSE HSL tendency inside the core step.
5. Use finite checks and a fallback to the incumbent embedded-tendency step if either split half-step produces invalid diagnostics.

The first implementation should avoid changing the fixed DFI/evaluation protocol. If the existing integration path makes signed split steps during filtering ambiguous, the split operator can be limited to the positive forecast step while keeping DFI on the incumbent path.

## Implementation Scope

This is a side-by-side model wrapper plus a small primitive-equation helper extraction. It should not alter the incumbent registry entry, the weather-state contract, or the evaluation scripts.

Tests should cover that the split candidate is registered, zero or near-zero fractional step leaves the thermal state unchanged within tolerance, and the fallback path matches the incumbent when split diagnostics are invalid.

## Expected Metric Movement

Expected movement is a modest positive aggregate change if the accepted mass-DSE signal is currently limited by operator time placement. Improvements would likely appear in advective phase-sensitive fields such as `T850`, `Z500`, and medium-lead thermal structure while avoiding the large early `MSLP` shock associated with vertical-DSE transport.

The candidate could be neutral if the embedded-tendency time placement is already adequate or if the split/fallback overhead changes the effective thermodynamic damping too little to matter.

## Risks

The main risk is double-counting or under-counting the accepted mass-DSE transport if the core step is not cleanly separated from the split operator. Another risk is that the split update changes balance enough to trigger early `MSLP` guardrails. The implementation should be conservative, local, and easy to disable.

This proposal should not become a general nonlinear-advection subcycling experiment. Its purpose is specifically to test symmetric time placement of the already accepted mass-DSE horizontal transport operator.

## Evaluation Plan

Run fixed fast checks first, with attention to finite values and step reproducibility. Then run fixed iteration against `dino_hsl2_mass_dse`, inspecting aggregate movement plus early `MSLP` and `Z500` guardrails. Only run fixed validation if the iteration result improves without broad short-lead pressure degradation.

Keep all evaluation protocols unchanged.

## Citations

- Strang, G., 1968: On the construction and comparison of difference schemes. *SIAM Journal on Numerical Analysis*, 5, 506-517. https://doi.org/10.1137/0705041
- Staniforth, A., and J. Cote, 1991: Semi-Lagrangian integration schemes for atmospheric models: A review. *Monthly Weather Review*, 119, 2206-2223. https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- Durran, D. R., 2010: *Numerical Methods for Fluid Dynamics: With Applications to Geophysics*. Springer.
- Lauritzen, P. H., R. D. Nair, and P. A. Ullrich, 2010: A conservative semi-Lagrangian multi-tracer transport scheme (CSLAM) on the cubed-sphere grid. *Journal of Computational Physics*, 229, 1401-1424. https://doi.org/10.1016/j.jcp.2009.10.036

## Researcher Notes

This proposal is distinct from the recent rejected pressure-thickness product-rule correction, hydrostatic inversion, and unguarded vertical-DSE transport. It does not change the transported scalar algebra, does not invert the hydrostatic tendency operator, and does not introduce a vertical thermal transport term. It asks whether the accepted horizontal mass-DSE transport works better as a symmetric operator around the step.

It is also distinct from staged broader split-explicit or HSL-remap variants: those target general nonlinear advection, remap monotonicity, or trajectory refinement. This proposal targets only the time placement of the already accepted layer-mass DSE HSL mechanism and should be implemented as a side-by-side candidate model.

## Evaluator Notes

### 2026-06-24T09:35:00Z

Decision: move to `staging`; rank 2 of 3 new proposals.

This is a coherent follow-up, but not the next implementation target. The
proposal asks a real numerical question: whether the accepted mass-DSE HSL
thermal transport is limited by being embedded as an explicit tendency rather
than applied as a symmetric operator around the primitive-equation step.
Strang splitting is a reputable tool for operator-ordering error, and this
candidate is more targeted than the older staged split-explicit/advection
experiments.

Keep it staged because the implementation surface is materially larger than
the initialization proposal. Source inspection shows the mass-DSE path is
currently embedded inside `temperature_tendency_potential_temperature_form`;
making it a signed half-step state operator would require careful helper
extraction, double-count prevention, refreshed diagnostics after the core step,
and explicit DFI behavior. Prior timing and splitting history is also mixed to
negative: symmetric diffusion splitting was essentially neutral/slightly
negative, full time-step and startup subcycling variants degraded MSLP or
primary score, and broader solver swaps were risky even with clean diagnostics.

Recommendation: keep as the best staged operator-timing variant behind the
rank-1 initialization test and behind lower-surface-area mass-DSE tendency
diagnostics. If promoted later, require a zero-fraction no-op test, exact
incumbent fallback for invalid half steps, and a clear implementation plan for
positive-time rollout versus DFI before any fixed iteration run.
