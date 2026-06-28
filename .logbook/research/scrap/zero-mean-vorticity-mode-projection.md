---
schema_version: 1
slug: zero-mean-vorticity-mode-projection
title: Project Out Spurious Global-Mean Vorticity Modes
status: scrap
created_at: 2026-06-17T23:24:07Z
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

# Project Out Spurious Global-Mean Vorticity Modes

## Hypothesis

For any globally smooth horizontal wind on the sphere, the area integral of
relative vorticity should vanish by Stokes' theorem. The incumbent uses
vorticity-divergence spectral variables and repeatedly converts between nodal
and modal representations during initialization, DFI, filtering, and output.
If a tiny nonphysical total-wavenumber-zero vorticity component is introduced
or amplified, it is an invariant-violating rotational mode with no physical
counterpart in the wind field.

A narrow projection of only the global-mean vorticity mode should improve or
neutralize wind evolution without broad wind reprojection, angular-momentum
fixing, pressure anchoring, or direct output correction. Confidence is low
because the effect may be roundoff-scale, but the correction is highly local
and tests a clean state invariant that has not been tried.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_zero_mean_vort`.
Preserve all incumbent initialization, forcing, DFI, filters, vertical
advection, near-surface residuals, output interpolation, target variables, and
fixed protocols.

Add an optional state projection after the accepted initialization and after
each positive-time step filter. The projection should identify the spherical
harmonic coefficient corresponding to total wavenumber zero in
`state.vorticity` and set it to exactly zero for every sigma layer. It must
leave all nonzero vorticity modes, all divergence modes, temperature,
`log_surface_pressure`, tracers, and `sim_time` unchanged. If the local modal
layout does not include a vorticity zero mode, the helper should be a
deterministic no-op and the proposal should be scrapped by the Evaluator or
Implementer before scoring.

The projection should not be applied as a broad Helmholtz wind remap and should
not compute truth-based wind residuals. It is a pure modal invariant cleanup.

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
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_zero_mean_vort`.
- API changes:
  - None. Forecast inputs, outputs, leads, target variables, and protocols stay
    fixed.
- Tests to update:
  - Unit-test the modal mask against `coords.horizontal.modal_axes` so only
    total-wavenumber-zero vorticity coefficients are selected.
  - Unit-test the projection on a synthetic `primitive_equations.State` with a
    nonzero vorticity mean and verify every other field is unchanged.
  - Verify the candidate factory preserves all incumbent flags and inserts the
    projection without changing DFI span, forcing, step size, or output logic.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` if a spurious rotational mean component is
    contributing to residual wind drift.
  - Small neutral-to-positive movement in `geopotential_500` and MSLP if cleaner
    rotational balance reduces downstream mass-field adjustment.
- Expected neutral metrics:
  - `2m_temperature` should be nearly unchanged because thermal fields and
    near-surface residuals are untouched.
  - Day-1 metrics should remain close to incumbent unless initialization itself
    contains a measurable invariant violation.
- Possible regressions:
  - If the modal coefficient has a numerical role in the transform library,
    zeroing it could introduce a tiny but systematic wind imbalance.
  - The score movement may be indistinguishable from numerical noise.

## Risks

- Numerical stability:
  - Low. The projection removes only one modal degree of freedom per layer, but
    the modal indexing must be verified carefully.
- Compute cost:
  - Negligible. The operation is a masked modal assignment and fits the fixed
    `--workers 4` budget.
- Data leakage:
  - Low. The projection uses only the forecast state and fixed modal geometry.
- Physical plausibility:
  - Moderate to high as an invariant cleanup; low confidence as a material
    WeatherBench2 score improvement.
- Rollback complexity:
  - Low. It is one flag, one helper, one side-by-side factory, and tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_zero_mean_vort`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_zero_mean_vort --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, and no fixed RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_zero_mean_vort --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A no-op implementation path, a clean near-zero iteration delta, or any wind
    or mass-field guardrail failure would show this invariant projection is not
    useful for the current incumbent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` converts
  pressure-level winds to modal vorticity/divergence during initialization and
  builds step filters through `time_integration.step_with_filters`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py`
  exposes modal axes and wind/vorticity transform helpers needed to identify
  and test the total-wavenumber-zero mode.
- History: `.logbook/history/2026-06-17_03-22-44_helmholtz-wind-initialization/decision.md`
  rejected broad wind initialization, motivating a one-coefficient invariant
  projection instead of a wind-field reprojection.
- History: `.logbook/history/2026-06-17_22-19-32_continuity-balanced-divergence-init/decision.md`
  rejected a broader divergence initialization correction with iteration delta
  `-0.001312899911693144`, so this proposal avoids modifying divergence.
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP and
  climate models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016
- Arakawa, A. and Lamb, V. R. 1977. Computational design of the basic dynamical
  processes of the UCLA general circulation model. Methods in Computational
  Physics, 17, 173-265.
  https://doi.org/10.1016/B978-0-12-460817-7.50009-4
- Williamson, D. L. 2007. The Evolution of Dynamical Cores for Global
  Atmospheric Models. Journal of the Meteorological Society of Japan.
  https://doi.org/10.2151/jmsj.85B.241

## Researcher Notes

This is not a duplicate of `barotropic-angular-momentum-fixer`, which was
scrapped as a broad global wind correction that rewrites vorticity/divergence
after wind transforms. This proposal edits only an invariant-violating
vorticity zero mode and does not impose angular momentum, mean wind, or
barotropic velocity constraints.

It is also distinct from Helmholtz wind initialization, polar wind tapering,
continuity-balanced divergence initialization, pressure anchoring, broad
damping, and output residual corrections. Confidence is low because the
measured effect may be zero, but the idea is fresh, concrete, cheap, and tests
a modal invariant rather than another metric-facing field.

## Evaluator Notes

### 2026-06-17T23:27:52Z

Decision: move to `scrap`.

The invariant is physically valid, but source inspection makes this a poor
candidate for fixed-gate evaluation. The modal layout does include a total
wavenumber zero slot, yet vorticity is initialized through
`spherical_harmonic.uv_nodal_to_vor_div_modal`, which constructs vorticity with
`curl_cos_lat`, and forecast vorticity tendencies are likewise curl-derived in
`PrimitiveEquationsSigma.curl_and_div_tendencies`. The l=0 rotational scalar is
therefore either already derivative-null by construction or only a roundoff
artifact. In wind reconstruction, `Grid.inverse_laplacian` explicitly zeros the
singular l=0 inverse, so this coefficient is also not a meaningful recovered
wind degree of freedom.

Given that the likely implementation is a no-op or roundoff cleanup, it should
not consume an iteration. The prior Helmholtz wind initialization failure
(`-0.34423230670441374`) and the recent divergence initialization rejection
(`-0.001312899911693144`) further argue against spending evaluation budget on
another wind-control-variable cleanup without evidence of a measurable
nonzero mode.
