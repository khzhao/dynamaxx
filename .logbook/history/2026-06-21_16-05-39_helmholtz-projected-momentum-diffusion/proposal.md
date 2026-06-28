---
schema_version: 1
slug: helmholtz-projected-momentum-diffusion
title: Diffuse Reconstructed Vector Wind Instead of Separate Modal Components
status: ready
created_at: 2026-06-21T16:02:00Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Diffuse Reconstructed Vector Wind Instead of Separate Modal Components

## Hypothesis

The incumbent applies the standard modal horizontal diffusion filter as a tree
operation over vorticity, divergence, temperature, log surface pressure, and
tracers. That is cheap and stable, but independent scalar damping of vorticity
and divergence can change the phase relationship of the reconstructed vector
wind near sharp baroclinic features. A momentum-space diffusion filter that
reconstructs wind, damps the vector field isotropically in spectral space, and
then converts back to vorticity/divergence may reduce grid-scale kinetic-energy
noise while preserving balanced large-scale rotational flow.

## Mechanism

Add an opt-in positive-time filter after the incumbent dynamical step and before
the symmetric Coriolis half-step. The filter should reconstruct nodal wind from
modal vorticity/divergence with the existing spherical-harmonic helpers, transform
the two vector components to modal space, apply the same high-wavenumber
diffusion scale to both components, convert the damped vector wind back to
vorticity/divergence, and leave temperature, log surface pressure, tracers, DFI,
weak-HS forcing, theta recentering, residual memory, and output diagnostics
unchanged.

The first candidate should keep the incumbent scalar horizontal diffusion for
temperature, log pressure, and tracers, but replace only the momentum part with
the Helmholtz-projected vector form. It should use the incumbent diffusion order
and timescale, finite fallback to the unfiltered state, and a side-by-side model
suffix such as `_helmholtz_momentum_diffusion`.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side incumbent-derived model with suffix `_helmholtz_momentum_diffusion`.
- API changes:
  - None. Forecast inputs, outputs, leads, variables, splits, and metrics remain fixed.
- Tests to update:
  - Verify the candidate factory preserves every incumbent option except the new momentum-diffusion selector.
  - Unit-test zero-wind and finite random-wind filter behavior on a small grid.
  - Verify non-momentum state leaves are unchanged by the new filter.
  - Verify nonfinite vector-filter diagnostics fall back to the incumbent vorticity/divergence state.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium leads if small-scale wind noise aliases into the accepted Richardson diagnostic.
  - `mean_sea_level_pressure` and `geopotential_500` if cleaner momentum diffusion reduces noisy divergence and pressure adjustment.
- Expected neutral metrics:
  - `2m_temperature` should be mostly neutral because thermal forcing and near-surface residuals are unchanged.
- Possible regressions:
  - Reconstructing and redamping wind components can over-damp balanced jets or perturb vorticity/divergence consistency enough to hurt MSLP.

## Risks

- Numerical stability:
  - Low to moderate. It is dissipative and finite-guarded, but it changes prognostic momentum every inner step.
- Compute cost:
  - Moderate. It adds wind reconstruction and extra transforms per step, but fits the reported 48 CPU / 172 GiB / 4-worker envelope.
- Data leakage:
  - None. The filter uses only the current forecast state and fixed grid operators.
- Physical plausibility:
  - Moderate to high. Momentum diffusion is standard, and vector-isotropic damping is a cleaner physical target than unrelated scalar damping.
- Rollback complexity:
  - Low. Remove one filter flag/helper, one factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires candidate-minus-incumbent primary delta at least `+0.002`, clean diagnostics, and no fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta, or an early wind/MSLP guardrail failure, would show the incumbent scalar modal filter is already the better compromise.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` composes `_horizontal_diffusion_step_filter` into the incumbent rollout filters.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py` implements `horizontal_diffusion_step_filter` through `filtering.horizontal_diffusion_filter`.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/spherical_harmonic.py` provides `vor_div_to_uv_nodal` and `uv_nodal_to_vor_div_modal`.
  - History: `.logbook/history/2026-06-18_13-26-11_symmetric-horizontal-diffusion-split/decision.md` and staged diffusion proposals show diffusion remains a plausible but sensitive family; this proposal changes only momentum representation, not diffusion strength tuning.
  - Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications to Geophysics, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0
  - Gottlieb, D. and Shu, C.-W. 1997. On the Gibbs phenomenon and its resolution. SIAM Review. https://doi.org/10.1137/S0036144596301390

## Researcher Notes

This is not another surface diagnostic, screen-temperature nudge, startup-only
fix, or off-centering change. It is distinct from staged
`vorticity-sparing-horizontal-diffusion` and
`planetary-wave-preserving-horizontal-diffusion`: those change which modal
momentum components are damped, while this proposal changes the variable in
which momentum diffusion is applied. It is also distinct from
`dissipative-heating-from-horizontal-diffusion` because it adds no thermal
energy return.

## Evaluator Notes

### 2026-06-21T16:04:40Z

Decision: move to `ready`; ranked 1 of 3 current proposals.

This is implementable now and is the strongest current proposal to leave for
Orchestrator selection. Source inspection confirms the required wind projection
surface already exists: `spherical_harmonic.vor_div_to_uv_nodal` and
`uv_nodal_to_vor_div_modal` are used by the incumbent exact Coriolis rotation
filter, and the horizontal diffusion filter is a localized step-filter path.
That makes a side-by-side momentum-only filter feasible without changing the
forecast API, fixed protocols, target variables, splits, output diagnostics,
DFI contract, weak-HS forcing, theta recentering, or residual memory.

The main negative evidence is the weak diffusion family history:
`symmetric-horizontal-diffusion-split` was clean but slightly negative, and
active staged diffusion variants already cover vorticity-sparing,
planetary-wave-preserving, sigma-tapered, and heating-return mechanisms. This
proposal remains distinct enough for `ready` because it does not tune diffusion
strength, placement, or low-mode masking; it tests whether damping the
reconstructed vector wind and projecting back to vorticity/divergence preserves
momentum consistency better than independent scalar modal damping. It also
avoids the recently poor surface-diagnostic, startup-only, lower-temperature,
and pressure-anchor directions.

Implementation should be conservative: keep the incumbent diffusion order and
timescale, change only vorticity/divergence through the vector projection,
leave all non-momentum leaves incumbent-equivalent, and fall back to the
unfiltered incumbent momentum state on nonfinite projection diagnostics. The
expected effect may be small, so promotion should require the fixed iteration
delta and guardrails exactly as written.
