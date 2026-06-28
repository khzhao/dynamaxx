---
schema_version: 1
slug: low-mode-preserving-dfi-initialization
title: Preserve Balanced Low Modes During Digital Filter Initialization
status: scrap
created_at: 2026-06-20T08:56:40Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
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

# Preserve Balanced Low Modes During Digital Filter Initialization

## Hypothesis

Balanced digital filter initialization was accepted early in the loop, but the
current DFI merge applies the filtered state to all spectral scales. The
rejected vorticity-preserving DFI merge showed that replacing only one state
component is too imbalanced. A low-mode-preserving DFI merge across the coupled
dynamic variables is a stronger balance argument: keep the raw analyzed
planetary/synoptic modes where the analysis is already slow and balanced, while
retaining DFI on medium and high modes that are more likely to contain
gravity-wave spinup.

If DFI is slightly damping useful large-scale temperature, wind, or mass
structure after the accepted hydrostatic/theta/offcenter changes, this should
improve early-to-medium `geopotential_500`, `mean_sea_level_pressure`, and
possibly `10m_u_component_of_wind` without reopening broad DFI-routing changes.

## Mechanism

Register a side-by-side model named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_low_mode_dfi`.

For this candidate only:

- build the raw initialized Dinosaur state exactly as the incumbent does;
- run the existing `time_integration.digital_filter_initialization` unchanged;
- after DFI, blend raw and filtered states with one smooth total-wavenumber mask:
  raw state for very low modes, filtered state for medium/high modes, and a
  fixed cosine transition between them;
- apply the same modal mask to `vorticity`, `divergence`,
  `temperature_variation`, and `log_surface_pressure`, so the coupled balanced
  low-mode state remains internally consistent;
- keep passive tracers on the incumbent DFI path for the first candidate, since
  humidity DFI and log-humidity variants have weak direct support and humidity
  is not a fixed target variable;
- preserve weak-HS forcing, exact Coriolis Strang split, positive-time
  offcentered SIL3, theta tendency, theta recentering, horizontal diffusion,
  pressure-level output interpolation, and scale-separated near-surface
  residual memory;
- fall back to the incumbent fully filtered state if the modal mask or blended
  state is nonfinite.

A conservative starting mask would preserve total wavenumber `n <= 6`, taper to
the DFI state by `n >= 12`, and use one fixed mask for all candidate runs.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one factory and one registry entry for the candidate model name above.
- API changes:
  - None. The forecast contract, target variables, lead times, metrics, and
    evaluation protocols remain fixed.
- Tests to update:
  - Unit-test the low-mode mask shape, bounds, and taper using the existing
    spherical-harmonic modal mesh.
  - Unit-test that low modes of the coupled dynamic leaves come from the raw
    state and high modes from the DFI state.
  - Verify tracers remain on the incumbent DFI path.
  - Verify nonfinite masks or blended leaves fall back to the fully filtered
    incumbent state.
  - Add factory, registry, and finite non-JIT smoke forecast tests.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 1 to 7 if DFI
    currently weakens balanced large-scale mass/thermal modes.
  - `10m_u_component_of_wind` if preserving low-mode rotational and divergent
    wind together avoids the imbalance that hurt the vorticity-only merge.
  - `2m_temperature` may be neutral to slightly positive because residual memory
    remains incumbent and only the large-scale initialized thermal state changes.
- Expected neutral metrics:
  - Long leads may approach incumbent behavior because the positive-time dycore,
    forcing, diffusion, offcentering, and residual decay are unchanged.
- Possible regressions:
  - Some low-frequency imbalance may genuinely live in low modes; preserving it
    can worsen early MSLP/Z500 or excite gravity-wave adjustment.
  - The mask cutoff may be too small to matter or too large to retain the
    accepted DFI benefit.

## Risks

- Numerical stability:
  - Moderate. The merge is balanced across dynamic leaves, but it still combines
    raw and filtered states after a nonlinear DFI trajectory.
- Compute cost:
  - Low. It adds one modal blend after the existing DFI initializer and does not
    increase rollout length or resolution.
- Data leakage:
  - None. It uses only the same-time initialized state and deterministic DFI
    output.
- Physical plausibility:
  - Moderate. DFI and normal-mode initialization aim to remove spurious fast
    modes while preserving balanced slow modes; this is an approximate spectral
    surrogate for that separation.
- Rollback complexity:
  - Low. Remove one adapter flag/helper, one factory/export, one registry entry,
    and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_low_mode_dfi`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_low_mode_dfi --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early day-1-through-day-5 RMSE guardrail failure, and no variable-by-lead
    RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_low_mode_dfi --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or subthreshold iteration delta would show that large-scale
    DFI movement is not a material remaining error. Any early MSLP/Z500
    guardrail failure would show that the preserved low modes contain important
    imbalance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` builds the
  raw primitive-equation state and applies DFI inside `_trajectory_function`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  implements Lanczos-window digital filter initialization.
- History: `.logbook/history/2026-06-16_09-54-58_balanced-digital-filter-initialization/decision.md`
  accepted full-state DFI, so this proposal preserves the mechanism and changes
  only the post-DFI scale merge.
- History: `.logbook/history/2026-06-18_00-44-09_vorticity-preserving-dfi-increment/decision.md`
  rejected preserving raw vorticity alone; this proposal responds by preserving
  low modes consistently across vorticity, divergence, temperature, and log
  surface pressure instead of merging one component.
- History: `.logbook/history/2026-06-19_10-17-34_centered-dfi-offcenter-rollout/decision.md`
  and `.logbook/history/2026-06-19_11-55-13_dfi-theta-mean-recenter/decision.md`
  show DFI routing/recentering changes were clean but subthreshold, so this
  proposal avoids changing the DFI solver, equation, or recentering filter.
- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM Model Using a
  Digital Filter. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Daley, R. 1981. Normal Mode Initialization. Reviews of Geophysics.
  https://doi.org/10.1029/RG019i003p00450
- Polavarapu, S., Ren, S., Clayton, A. M., Sankey, D., and Rochon, Y. 2004. On
  the Relationship between Incremental Analysis Updating and Incremental
  Digital Filtering. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2004)132%3C2495:OTRBIA%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of `vorticity-preserving-dfi-increment`: that candidate
mixed one raw component with filtered mass and thermal leaves and was rejected.
The new mechanism keeps the coupled low-mode dynamic state together and keeps
all medium/high modes on the accepted DFI path.

It is also distinct from active `balanced-low-mode-thermal-iau`, which adds a
positive-time thermal tendency from output residuals. This proposal does not add
heating, residuals, IAU increments, or forecast-time nudging; it only changes
the scale-selective merge of raw and DFI-initialized states before rollout.

## Evaluator Notes

### 2026-06-20T09:01:44Z

Decision: move to `scrap`; ranked 3 of 3 proposals in this triage batch.

This is more balanced than the rejected `vorticity-preserving-dfi-increment`,
but it is still a DFI post-merge experiment in a family with repeated weak or
negative evidence. Full-state DFI was accepted early, while later DFI changes
were not material: Coriolis-consistent DFI was only `+0.0008926584240389612`,
centered DFI with offcentered positive rollout was only
`+0.000005771767184858945`, DFI theta mean recentering was negative, and the
vorticity-only merge was negative despite clean guardrails. The current
proposal would reintroduce raw low-mode vorticity, divergence, temperature, and
log-surface-pressure content with an arbitrary total-wavenumber cutoff, so it
can preserve genuine low-frequency imbalance as easily as balanced signal.

The active queue already has more defensible low-mode analysis-insertion ideas,
especially staged `balanced-low-mode-thermal-iau`, which uses bounded
positive-time insertion rather than replacing part of the DFI output. Under the
fixed gates, this proposal is unlikely to produce a `+0.002` iteration gain
over the current incumbent and is not the best use of another DFI implementation
cycle. Scrap it rather than growing the staging queue with another nearby DFI
merge.
