---
schema_version: 1
slug: upper-sigma-rayleigh-sponge
title: Add a Top-Confined Sigma Rayleigh Sponge
status: scrap
created_at: 2026-06-17T07:56:48Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
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

# Add a Top-Confined Sigma Rayleigh Sponge

## Hypothesis

The current incumbent still develops negative long-lead skill in all fixed
target variables even after successful initialization and weak thermal
relaxation improvements. Prior damping-style candidates give important negative
evidence: scale-selective hyperdiffusion damaged low-level wind, divergence
damping was too weak or misdirected, full-grid spectral truncation was rejected,
and a 600 s time-step change did not help. Those failures do not rule out a
physically localized model-top sponge, because a sponge targets upper-boundary
wave reflection and top-layer temperature/divergence noise rather than applying
additional damping throughout the troposphere.

A top-confined Rayleigh sponge should reduce spurious vertically propagating
gravity-wave energy and upper-level imbalance without touching the lower sigma
levels that feed `2m_temperature` and `10m_u_component_of_wind` directly.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_top_sponge`.
Preserve the incumbent initialization, DFI, weak Held-Suarez thermal relaxation,
near-surface residual correction, output interpolation, vertical advection,
horizontal diffusion settings, inner step, spectral truncation, and public API.

Add an optional step filter after the existing IMEX step and horizontal
diffusion filter. The filter applies only to the upper sigma layers, for
example with a smooth vertical weight that is one at the top layer, tapers to
zero by about `sigma = 0.20`, and is exactly zero below that. Apply a fixed,
single-strength Rayleigh relaxation over the inner step to damp upper-layer
`divergence`, `vorticity`, and `temperature_variation` toward zero anomaly
relative to the incumbent reference state. Do not damp `log_surface_pressure`,
passive humidity, near-surface diagnostic outputs, or any output residual.

Use one predetermined strength, such as a top-layer e-folding time of 48 hours,
to avoid validation-guided tuning. The Evaluator can scrap or stage if that
fixed strength is judged too arbitrary, but the proposal should not become a
parameter sweep inside model selection.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_top_sponge`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, and metrics
    remain unchanged.
- Tests to update:
  - Unit-test the sponge weight profile: positive only in upper sigma levels,
    exactly zero below the selected cutoff, finite, and monotone toward the
    model top.
  - Unit-test that the filter damps `vorticity`, `divergence`, and
    `temperature_variation` in weighted upper levels while leaving
    `log_surface_pressure` and tracers unchanged.
  - Verify the candidate factory preserves all incumbent flags and changes only
    the top-sponge option.
  - Verify registry construction and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium and long leads if
    upper-level wave reflection or thermal noise is contaminating column
    thickness and mass evolution.
  - `10m_u_component_of_wind` may improve at long leads if less upper-level
    imbalance projects onto barotropic wind error.
  - Primary score may improve without spending much early near-surface guardrail
    margin because the sponge is zero in lower sigma layers.
- Expected neutral metrics:
  - Day-1 `2m_temperature` and `10m_u_component_of_wind` should remain close to
    the incumbent if the sponge is genuinely top-confined and weak.
- Possible regressions:
  - Excess upper-level damping could weaken real baroclinic development,
    degrading Z500 or MSLP despite clean diagnostics.
  - Damping vorticity and temperature anomalies could interact with the accepted
    weak Held-Suarez thermal relaxation in a way that reduces useful synoptic
    amplitude.

## Risks

- Numerical stability:
  - Low to moderate. A multiplicative damping filter is stabilizing in form, but
    it changes prognostic upper-level dynamics every inner step.
- Compute cost:
  - Low. The filter is a small modal-array update and should fit the reported
    `--workers 4` resource budget.
- Data leakage:
  - Low. It uses no future truth, validation statistics, or target-specific
    corrections.
- Physical plausibility:
  - Moderate. Sponge layers are standard upper-boundary devices, but this
    implementation is a simplified sigma-level filter rather than a full
    vertical-velocity absorbing layer.
- Rollback complexity:
  - Low. The change can be isolated behind one adapter flag and one side-by-side
    factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_top_sponge`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_top_sponge --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`,
    clean diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_top_sponge --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative iteration delta would show that the model-top noise
    mechanism is not relevant for this incumbent. Any early `10m_u_component_of_wind`
    or `geopotential_500` guardrail failure would show that even top-confined
    damping harms balanced forecast evolution.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` constructs
  the current stepper with `time_integration.step_with_filters`, making a
  side-by-side additional filter implementable without API changes.
- History:
  `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
  rejected broad hyperdiffusion after early `10m_u_component_of_wind`
  regression, motivating a top-confined rather than global damping mechanism.
- History:
  `.logbook/history/2026-06-16_19-57-46_divergence-selective-gravity-wave-damping/decision.md`
  rejected weak divergence damping with a negative iteration delta, so this
  proposal damps a different, vertically localized upper-boundary mechanism.
- History:
  `.logbook/history/2026-06-16_18-41-23_six-hundred-second-inner-step/decision.md`
  rejected a simple time-step convergence candidate, arguing against spending
  another iteration on generic stability changes.
- Klemp, J. B., Dudhia, J., and Hassiotis, A. D. 2008. An Upper Gravity-Wave
  Absorbing Layer for NWP Applications. Monthly Weather Review.
  https://doi.org/10.1175/2008MWR2596.1
- Klemp, J. B. and Lilly, D. K. 1978. Numerical Simulation of Hydrostatic
  Mountain Waves. Journal of the Atmospheric Sciences.
- ECMWF IFS Documentation, Part III: Dynamics and Numerical Procedures,
  section on model-top sponge diffusion. https://www.ecmwf.int/en/elibrary
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications
  to Geophysics, second edition. Springer.

## Researcher Notes

This is not a repeat of rejected hyperdiffusion, divergence damping, full-grid
spectral truncation, or the 600 s inner-step candidate. Those ideas changed
global horizontal damping, one dynamical variable, spectral resolution, or time
discretization. This proposal is vertically localized, lower-boundary-sparing,
and aimed at upper-boundary wave reflection.

It is decorrelated from the staged semi-Lagrangian vertical-transport proposal:
the semi-Lagrangian idea changes vertical transport throughout the column every
step, while this proposal leaves vertical advection unchanged and only damps
selected prognostic anomalies in the top sigma layers. The risk remains real
because prior numerics changes have mostly failed; the narrow sponge scope is
the reason to keep it scientifically plausible rather than a broad damping
retry.

## Evaluator Notes

2026-06-17T08:00:01Z - Move to `scrap`; rank 5 of 5 active ideas.

The proposal is physically recognizable but not strong enough for this
incumbent queue. Literature and operational documentation support model-top
absorbing layers in general, including Rayleigh or diffusion-based sponges, but
the cited mechanisms do not directly justify this specific adapter change:
Klemp-Dudhia-Hassiotis targets vertical-velocity damping in split-explicit NWP,
while ECMWF IFS documentation describes vertically dependent diffusion near the
model top. This proposal would instead relax Dinosaur sigma-level vorticity,
divergence, and temperature anomalies toward zero after every IMEX/filter step.
That is a broader prognostic damping perturbation than the supporting evidence
establishes, and the fixed 48-hour top-layer strength is arbitrary without a
diagnostic showing upper-boundary reflection is the dominant remaining error.

Repository history is also unfavorable for another damping/numerics iteration.
Scale-selective hyperdiffusion regressed iteration primary by
`-0.05124210065383061` and failed the early `10m_u_component_of_wind` mean RMSE
guardrail by `+3.64645557771629%`. Divergence-selective damping was stable and
guardrail-clean but still lost `-0.00020461043258523937` primary. The 600 s
inner-step candidate lost `-0.0002549284092885351`, pressure-aware sigma grid
lost `-0.10322710509965427`, and vertical-advection suppression failed fast
with nonfinite metrics from lead hour 264. Those results do not disprove every
possible top sponge, but they do make this candidate a poor next use of a full
iteration when initialization-only proposals remain.

Scrapping is not a final claim that model-top damping can never help. It means
this proposal lacks enough local diagnostic evidence and implementation
specificity to outweigh the negative damping history. A future sponge idea
would need a measured upper-layer imbalance or reflection diagnostic, a tighter
mapping to the supported literature, and a design that protects Z500/MSLP and
low-level wind guardrails before it returns to staging.
