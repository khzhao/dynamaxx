---
schema_version: 1
slug: polar-vector-wind-initialization-taper
title: Regularize Polar Vector Wind Initialization
status: ready
created_at: 2026-06-17T11:20:21Z
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

# Regularize Polar Vector Wind Initialization

## Hypothesis

The WeatherBench2 grid used by the fixed local evaluation includes pole
latitudes, and the Dinosaur adapter supports `equiangular_with_poles` grids by
replacing exact-pole cosine factors with the smallest interior cosine. That
keeps the spherical harmonic transforms finite, but the input horizontal wind
components are still local east/north components at coordinate singularities.
At an exact pole, longitude-dependent vector components are not a smooth scalar
field for a spectral transform.

An initialization-only polar wind taper should reduce spurious high-wavenumber
vorticity/divergence injected by singular pole-row vector components without
changing pressure, temperature, humidity, DFI, weak Held-Suarez forcing,
near-surface residuals, or the output contract. The mechanism is aimed at the
incumbent's persistent `10m_u_component_of_wind` weakness, but it is
decorrelated from damping, timestep, pressure-remap, humidity, and residual
families.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_polar_wind_taper`.
Preserve all incumbent behavior except a guarded preprocessing step for
pressure-level `u_component_of_wind` and `v_component_of_wind` during
`weather_state_to_dinosaur_state`.

Before converting nodal winds to modal vorticity and divergence:

- detect exact polar latitude rows after conversion into Dinosaur latitude
  order;
- replace only those exact pole rows in the pressure-level `u` and `v` wind
  stacks with a fixed, longitude-independent regular value, preferably zero, or
  another Evaluator-approved value chosen before implementation;
- leave all non-pole latitude rows unchanged;
- do not change temperature, surface pressure, humidity, geopotential,
  pressure-level output interpolation, near-surface residuals, DFI weights,
  weak-HS forcing, or any fixed evaluation protocol.

The first candidate should be exact-pole-only. It should not smooth broad polar
caps or tune latitude widths against evaluation metrics. If exact-pole rows
prove too weak to matter, that result is useful negative evidence without
spending another iteration on a polar-width sweep.

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
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_polar_wind_taper`.
- API changes:
  - None. Forecast inputs, outputs, channel names, lead times, target variables,
    and metrics remain unchanged.
- Tests to update:
  - Unit-test the polar-row helper on north-up and south-up latitude ordering:
    exact pole rows are replaced, interior rows are unchanged, and no
    non-finite values are introduced.
  - Unit-test that the helper acts only on `u` and `v` wind stacks, not
    temperature, surface pressure, passive humidity, or geopotential arrays.
  - Verify the candidate factory preserves every incumbent flag except the new
    polar-wind taper option.
  - Add registry coverage and a non-JIT finite smoke forecast for the candidate
    on a grid with pole latitudes.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at short and medium leads if polar-row vector
    singularities seed spectral wind noise that survives DFI.
  - `geopotential_500` and `mean_sea_level_pressure` may improve slightly if
    cleaner initialized vorticity/divergence reduces balanced mass-field noise.
- Expected neutral metrics:
  - `2m_temperature` should be nearly neutral because the proposal does not
    directly change temperature initialization or output diagnostics.
  - Most non-polar flow features should remain close to the incumbent because
    only exact pole rows are changed before the spectral transform.
- Possible regressions:
  - If the pole rows carry meaningful analyzed large-scale circulation
    information under the dataset's vector convention, replacing them may
    slightly degrade global wind or mass evolution.
  - If evaluation area weights make exact poles negligible and spectral ringing
    from those rows is already controlled by DFI, score movement may be too
    small to pass promotion.

## Risks

- Numerical stability:
  - Low. The operation removes singular vector input at two latitude rows and
    does not add divisions, feedback, or longer trajectories.
- Compute cost:
  - Negligible relative to the incumbent. It is one small preprocessing update
    per initialized state.
- Data leakage:
  - Low. It uses only grid geometry and same-time input winds, with no target
    residuals, validation statistics, future truth, or golden data.
- Physical plausibility:
  - Moderate. Exact-pole east/north wind components are coordinate-singular, so
    regularizing them before a global spectral transform is defensible. The
    risk is that zeroing is a simple convention rather than a full vector-basis
    reconstruction.
- Rollback complexity:
  - Low. The change can be isolated behind one adapter flag and one side-by-side
    factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_polar_wind_taper`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_polar_wind_taper --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`,
    clean diagnostics, no fixed RMSE guardrail failure, and improvement or
    neutrality in early `10m_u_component_of_wind`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_polar_wind_taper --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same fixed
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero iteration delta would show exact-pole vector
    regularization is too small to matter. Any early wind or mass-field
    guardrail failure would show the raw polar wind convention is more useful
    than the regularized initialization.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/coordinates.py` detects
  `equiangular_with_poles` grids and replaces exact-pole cosine factors through
  `_with_safe_polar_cosine`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` converts
  pressure-level nodal `u` and `v` wind stacks to modal vorticity/divergence
  with `spherical_harmonic.uv_nodal_to_vor_div_modal`.
- History: `.logbook/history/2026-06-17_03-22-44_helmholtz-wind-initialization/decision.md`
  rejected a broad wind-initialization change with a large negative primary
  delta, motivating an exact-pole-only wind preprocessing proposal rather than
  another global wind decomposition.
- History: `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
  rejected broad damping after an early `10m_u_component_of_wind` guardrail
  failure, motivating a coordinate-local initialization fix instead of more
  spectral damping.
- Williamson, D. L., Drake, J. B., Hack, J. J., Jakob, R., and Swarztrauber,
  P. N. 1992. A standard test set for numerical approximations to the shallow
  water equations in spherical geometry. Journal of Computational Physics,
  102, 211-224. https://doi.org/10.1016/S0021-9991(05)80016-6
- Staniforth, A. and Thuburn, J. 2012. Horizontal grids for global weather and
  climate prediction models: a review. Quarterly Journal of the Royal
  Meteorological Society, 138, 1-26. https://doi.org/10.1002/qj.958

## Researcher Notes

This proposal is not a duplicate of `helmholtz-wind-initialization`; that
candidate changed the full wind initialization through a global balanced
decomposition and regressed badly. This proposal changes only the coordinate-
singular exact pole rows before the incumbent's existing `uv` to
vorticity/divergence transform.

It is also not a damping, diffusion, timestep, T120, vertical transport,
thermal, pressure-remap, humidity, surface residual, or terrain idea. The
expected effect may be small, but it is cheap, reversible, and probes an
unexplored source of wind noise in a grid that explicitly includes pole
latitudes.

## Evaluator Notes

2026-06-17T11:23:24Z - Move to `staging`; rank 4 of 6 active ideas.

This is feasible and scientifically plausible but not strong enough for the
next ready slot. Source inspection supports the mechanism: local grid metadata
does accept `equiangular_with_poles` grids and already guards exact-pole cosine
factors, while the adapter converts initialized nodal `u` and `v` fields to
modal vorticity/divergence with `spherical_harmonic.uv_nodal_to_vor_div_modal`.
The cited literature supports the general concern that spherical-pole
coordinates require care, and exact-pole east/north vector components are a
reasonable initialization-local regularization target.

The proposal is staged because the expected effect size is likely small under
the fixed global metrics. It changes only two exact latitude rows before the
spectral transform, and the accepted incumbent already passes diagnostics.
Recent wind-initialization history also argues for caution: the broad
`helmholtz-wind-initialization` candidate was diagnostic-clean but regressed
primary score badly, while hyperdiffusion and other broad wind/noise controls
failed guardrails or primary score. This exact-pole-only version is much more
bounded than those failures, but it should not displace the higher-signal
thermal limiter or the passive humidity DFI fallback.

If promoted later, keep the implementation exact-pole-only, side-by-side, and
initialization-only. Use a fixed zero value at exact pole rows rather than a
tunable polar-cap smoother; leave all non-pole rows and all non-wind variables
unchanged; and require tests for both latitude orderings plus a pole-grid
finite smoke forecast.

2026-06-17T13:33:51Z - Keep in `staging`; rank 2 of 4 active ideas.

This remains a plausible bounded wind-initialization idea, but it should stay
behind the surface-layer diagnostic. It is much narrower than the scrapped
barotropic angular-momentum fixer because it changes only exact pole rows
during initialization and leaves the forward rollout untouched. That locality
matters after the negative broad wind/numerics history.

The expected global metric effect is still likely small because only two
latitude rows are changed and DFI may already suppress any pole-row spectral
noise. If promoted later, keep the previous constraints unchanged: exact pole
rows only, initialization-only, no polar cap width tuning, fixed zero value at
the pole rows, and no changes to non-pole rows or non-wind fields.

2026-06-17T14:41:49Z - Move to `ready`; rank 1 of 3 active ideas.

Fresh triage after the surface-layer diagnostic extrapolation rejection leaves
this as the only bounded, physically plausible, low-surface-area candidate
worth a next iteration slot. The latest surface diagnostic failure strongly
penalizes output-contract and near-surface post-processing changes: the
candidate was diagnostic-clean yet regressed primary score by
`-0.10115079559414197`, with early `10m_u_component_of_wind` up
`+9.833722%` and `2m_temperature` up `+5.789438%`. This proposal avoids that
family entirely: it changes only exact-pole pressure-level wind rows before the
incumbent initialization transform, leaves all output diagnostics unchanged,
and should not perturb mass or thermal diagnostics directly.

It is also materially narrower than rejected broad wind or numerics attempts.
`helmholtz-wind-initialization` showed global wind-control-variable changes can
destroy mass-field balance, while this proposal touches only the coordinate
singular pole rows on an `equiangular_with_poles` grid. The expected signal may
be small under area-weighted global metrics, but a clean near-zero result would
be useful negative evidence and the implementation can be isolated behind one
side-by-side adapter flag. Promotion constraints remain strict: exact pole rows
only, initialization-only, fixed zero replacement, no polar-cap smoothing or
width tuning, no non-wind changes, no output-path changes, and no evaluation
protocol changes.
