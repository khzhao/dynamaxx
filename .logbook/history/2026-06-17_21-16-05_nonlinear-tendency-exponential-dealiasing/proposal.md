---
schema_version: 1
slug: nonlinear-tendency-exponential-dealiasing
title: Nonlinear Tendency Exponential Dealiasing
status: ready
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

# Nonlinear Tendency Exponential Dealiasing

## Hypothesis

The current sigma-coordinate primitive-equation solver evaluates nonlinear
advection, vorticity flux, kinetic-energy, and pressure-gradient products in
nodal space before transforming tendencies back to modal space. Those
pseudo-spectral products can alias unresolved high-wavenumber energy back into
retained modes. A high-order exponential filter applied to the explicit
nonlinear tendencies, rather than to the prognostic state, may reduce aliasing
noise while preserving the accepted low-wavenumber trajectory, DFI setup, weak
Held-Suarez relaxation, and near-surface residual correction.

## Mechanism

Add a side-by-side candidate that wraps the primitive-equation explicit tendency
with an exponential modal filter. The filter should use the existing
`filtering.exponential_filter` machinery with a conservative cutoff near the
traditional two-thirds retained spectral range, high order, and attenuation
large enough to damp only the top modal tail. It should be applied to the
returned `primitive_equations.State` from `explicit_terms`, not as a step filter
on the full state. The zero mode and low total wavenumbers should remain
unchanged.

This differs from the rejected hyperdiffusion, divergence damping, and T120
truncation attempts because it is an anti-aliasing operation on the nonlinear
right-hand side. It does not raise resolution, does not shorten the time step,
and does not continually diffuse the full prognostic state.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/filtering.py` if a helper is useful
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
- Registry changes:
  - Add a factory such as
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_tendency_dealias`.
- API changes:
  - None. The deterministic forecast API, input variables, output variables,
    lead times, and WeatherBench2 protocols stay unchanged.
- Tests to update:
  - Verify the candidate is registered and produces finite forecasts on the
    existing test fixtures.
  - Verify the tendency filter preserves state shapes and leaves scalar fields
    with incompatible shapes untouched through the existing filter helper.
  - Verify a constant modal field is unchanged.

## Expected Metric Movement

- Expected improvements:
  - Long-lead `geopotential_500` and `mean_sea_level_pressure` may improve if
    nonlinear aliasing is feeding balanced mass-field drift.
  - `10m_u_component_of_wind` may improve modestly if high-wavenumber vorticity
    or divergence noise aliases into retained low-level flow.
- Expected neutral metrics:
  - Early `2m_temperature` should remain close to the incumbent because the
    accepted near-surface residual and weak thermal relaxation are unchanged.
- Possible regressions:
  - Any modal filtering can behave like numerical damping, so early wind skill
    may regress as in prior damping-family failures.
  - The aggregate primary score may be insensitive if aliasing is not a
    material remaining error source for this resolution.

## Risks

- Numerical stability:
  - Low to medium. The operation is dissipative in the top modal tail, but
    excessive attenuation or a too-low cutoff could overdamp balanced waves.
- Compute cost:
  - Low. This adds a modal tree-map scaling to explicit tendencies and should be
    much cheaper than an extra dynamics step or a new interpolation path.
- Data leakage:
  - None. No target data, metrics, split information, or validation feedback is
    used.
- Physical plausibility:
  - Medium. Anti-aliasing is numerically justified, but a global spectral tail
    filter is not a physical subgrid closure.
- Rollback complexity:
  - Low. It is a side-by-side registered candidate with localized flags and a
    factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate> --workers 4`.
  - Require clean diagnostics, no fixed RMSE guardrail failures, and at least
    `+0.002` primary improvement over the incumbent.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate> --workers 4` only
    if iteration promotes.
  - Require clean diagnostics, no fixed RMSE guardrail failures, and at least
    `+0.001` validation primary improvement.
- Outcome that would falsify the hypothesis:
  - A clean but neutral or negative iteration result, or an early `10m_u` RMSE
    guardrail failure, would indicate aliasing control is not the remaining
    high-value mechanism.

## Citations

- Hou, T. Y. and Li, R. 2007. Computing nearly singular solutions using
  pseudo-spectral methods. Journal of Computational Physics, 226, 379-397.
  https://www.math.umd.edu/~tadmor/references/files/Hou%20%26%20Li%20filter%20vs%202-3%20rule.pdf
- Gottlieb, D. and Shu, C.-W. 1997. On the Gibbs phenomenon and its resolution.
  SIAM Review, 39, 644-668.
  https://doi.org/10.1137/S0036144596301390
- Margairaz, F., Giometto, M. G., Parlange, M. B., and Calaf, M. 2018.
  Comparison of dealiasing schemes in large-eddy simulation of neutrally
  stratified atmospheric flows. Geoscientific Model Development, 11, 4069-4084.
  https://gmd.copernicus.org/articles/11/4069/2018/
- Dynamaxx source reference: `src/dynamaxx/dycore/models/dinosaur/filtering.py`
  already includes an exponential modal filter and cites spectral-filtering
  literature.

## Researcher Notes

Prior `scale-selective-hyperdiffusion`,
`divergence-selective-gravity-wave-damping`, `six-hundred-second-inner-step`,
and `full-grid-spectral-truncation` decisions are negative evidence for broad
damping or resolution changes. This proposal is still low confidence because
it belongs to the numerical-stability neighborhood, but it is not an exact
duplicate: the proposed filter is applied to nonlinear explicit tendencies to
reduce pseudo-spectral aliasing, not to the full model state as a forecast-time
diffusion operator.

## Evaluator Notes

### 2026-06-17_21-15-13Z

Decision: `ready`.

This is the strongest current proposal despite low confidence. It has the
smallest implementation surface among the three current ideas: the codebase
already has `filtering.exponential_filter`, and the proposed change can be
registered side by side by wrapping the primitive-equation explicit tendency
rather than altering initialization, output remapping, target variables,
evaluation protocols, or the full prognostic state after every step.

The main negative evidence is the prior damping family:
scale-selective hyperdiffusion hurt early `10m_u_component_of_wind`,
divergence-selective damping was slightly negative, and full-grid truncation
failed fast. This proposal is still distinct enough to test because it targets
the nonlinear right-hand side where pseudo-spectral products are formed, not
the accepted low-wavenumber state trajectory directly. Keep the cutoff
conservative, preserve zero and low total wavenumbers, and evaluate only under
the fixed fast, iteration, and validation gates. Ready is kept to this single
candidate because the alternatives either touch wind balance directly or
perform broader thermodynamic adjustment with poorer recent evidence.
