---
schema_version: 1
slug: sigma-tapered-horizontal-diffusion
title: Taper Horizontal Diffusion Away From the Lower Sigma Layers
status: staging
created_at: 2026-06-19T17:59:18Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Taper Horizontal Diffusion Away From the Lower Sigma Layers

## Hypothesis

The incumbent applies the same horizontal diffusion filter to all vertical
layers every inner step. After the accepted off-centered semi-implicit solver,
fast-mode stability is much improved, while the incumbent iteration and
validation artifacts still show substantial late negative bias in low-level
temperature and zonal wind. A vertically tapered diffusion filter that preserves
the standard damping aloft but weakens it in the lowest sigma layers may retain
needed high-wavenumber control while reducing excessive damping of the boundary
layer flow that feeds the 2 m and 10 m diagnostics.

## Mechanism

Preserve the incumbent primitive-equation tendencies, DFI route, weak
Held-Suarez forcing, exact Coriolis Strang split, Richardson 10 m diagnostic,
theta tendency, theta recentering, and SIL3 off-centering.

Add an opt-in horizontal diffusion step filter such as
`use_sigma_tapered_horizontal_diffusion`. The filter should use the same
spectral damping law and top-mode time scale as the incumbent, but multiply the
diffusion strength by a fixed sigma-layer taper:

- `1.0` through the upper and middle troposphere, for example sigma centers
  `<= 0.65`;
- smoothly decreasing from `1.0` to a lower bound such as `0.35` between sigma
  `0.65` and the lowest model layer;
- a conservative surface-log-pressure multiplier, for example `0.75`, to avoid
  fully removing mass-field smoothing;
- identical behavior in DFI and positive-time rollout because this is a filter
  shape change, not a DFI routing experiment.

The implementation can either extend `_horizontal_diffusion_step_filter` to
accept a layer multiplier or add a sibling helper that constructs a broadcastable
modal scaling for three-dimensional state leaves. It should keep the same filter
order and default tau calculation unless the Evaluator explicitly asks for a
separate sensitivity proposal.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/filtering.py` if a reusable scaling
    helper is cleaner than adapter-local code
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model name extending the incumbent with a
    `_sigma_tapered_diffusion` suffix.
- API changes:
  - None. The forecast contract, target variables, lead steps, and protocols are
    unchanged.
- Tests to update:
  - Verify the taper is finite, monotone toward the surface, bounded by the
    chosen lower/upper limits, and has shape compatible with modal 3D fields.
  - Verify the candidate factory preserves all incumbent options except the new
    diffusion selector.
  - Verify the filter is a no-op for leaves whose shape cannot safely broadcast
    the layer taper.
  - Add registry and non-JIT smoke tests.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` at medium and late leads if current uniform
    low-level diffusion contributes to the negative wind bias.
  - `2m_temperature` at medium and late leads if weaker lower-layer damping
    preserves near-surface thermal anomalies that the accepted residual cannot
    maintain indefinitely.
  - Primary score may improve without broad mass-field risk because upper-level
    and midlevel damping remain unchanged.
- Expected neutral metrics:
  - `geopotential_500` and `mean_sea_level_pressure` should remain close to the
    incumbent if the full aloft damping and partial log-pressure smoothing are
    retained.
- Possible regressions:
  - Early 10 m wind can regress if the lower-layer filter is too weak and
    small-scale spectral noise survives into the surface diagnostic.
  - Late mass fields can regress if log-surface-pressure smoothing is weakened
    too far.

## Risks

- Numerical stability:
  - Low to moderate. The proposal preserves the incumbent damping aloft and the
    accepted off-centered semi-implicit solver, but intentionally reduces one
    stabilizing filter near the surface.
- Compute cost:
  - Negligible. It changes filter coefficients, not trajectory count or model
    resolution.
- Data leakage:
  - None. The taper is fixed from sigma coordinates and uses no truth data.
- Physical plausibility:
  - Moderate. Boundary-layer wind and temperature errors often depend on
    unresolved turbulent exchange, and a uniform horizontal smoother is a crude
    substitute. A lower-level taper is a numerical experiment, not a complete
    PBL parameterization.
- Rollback complexity:
  - Low. Remove one option/helper, one factory/export, one registry entry, and
    tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early `10m_u_component_of_wind` guardrail failure, and
    neutral or improved late low-level metrics.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` and no mass-field
    or low-level wind guardrail failure.
- Outcome that would falsify the hypothesis:
  - A clean near-zero delta would show that uniform low-level horizontal
    diffusion is not a material remaining score bottleneck. Any early wind or
    MSLP guardrail failure would show the taper is too aggressive for the fixed
    evaluation.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` builds one
    horizontal diffusion filter for all layers through
    `_horizontal_diffusion_step_filter`.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/filtering.py` and
    `src/dynamaxx/dycore/models/dinosaur/time_integration.py` implement the
    spectral horizontal diffusion scaling used by the incumbent.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
    rejected a broad scale-selective diffusion change after early 10 m wind
    degradation, motivating a narrower lower-layer-preserving filter.
  - Dynamaxx history:
    `.logbook/history/2026-06-19_06-50-50_offcentered-semi-implicit-gravity-wave/decision.md`
    accepted off-centered SIL3 with large mass-field gains and clean guardrails,
    reducing the need to use horizontal diffusion as the main fast-mode control.
  - GFDL Spectral Dynamical Core documentation describes horizontal diffusion
    with Laplacian powers in global spectral primitive-equation models:
    https://www.gfdl.noaa.gov/wp-content/uploads/files/user_files/pjp/spectral_core.pdf
  - ECMWF IFS Documentation Part III documents spectral-transform dynamics in a
    global NWP model context:
    https://www.ecmwf.int/sites/default/files/elibrary/2023/81369-ifs-documentation-cy48r1-part-iii-dynamics-and-numerical-procedures.pdf
  - Rasp, S. et al. 2024. WeatherBench 2: A benchmark for the next generation of
    data-driven global weather models. Journal of Advances in Modeling Earth
    Systems. https://doi.org/10.1029/2023MS004019

## Researcher Notes

This is not a duplicate of staged `planetary-wave-preserving-horizontal-diffusion`.
That proposal changes the horizontal spectral response to preserve large-scale
planetary modes. This proposal keeps the horizontal spectral law and changes
only its vertical profile, with the specific intent of preserving lower-layer
wind and temperature anomalies.

It is also not a retry of rejected `scale-selective-hyperdiffusion`: the failed
candidate changed the global diffusion order/shape and degraded early 10 m
wind. This proposal preserves the accepted top-mode damping law aloft and only
weakens diffusion where the target diagnostics directly sample the model state.

## Evaluator Notes

### 2026-06-19T18:03:28Z

Decision: move to `staging`; ranked 2 of 3 fresh proposals.

The idea is distinct enough to preserve. It is narrower than prior broad
diffusion-order experiments because it leaves the high-wavenumber law and
aloft damping intact while testing whether uniform low-level smoothing is
hurting boundary-layer wind and temperature diagnostics. It is also distinct
from staged `planetary-wave-preserving-horizontal-diffusion`, which changes
horizontal spectral selectivity rather than vertical diffusion profile, and
from staged `pressure-gradient-product-dealiasing`, which filters one nonlinear
source term rather than the step filter.

Keep it out of `ready` because the diffusion family has poor local evidence:
`scale-selective-hyperdiffusion` regressed primary score by
`-0.05124210065383061` and failed the early 10 m wind guardrail, while
`symmetric-horizontal-diffusion-split` was clean but slightly negative. This
proposal also changes the prognostic trajectory and mass smoothing, so the
surface-diagnostic upside comes with MSLP/Z500 and early-wind risk that the
ready Ekman-inflow proposal avoids.

If promoted later, the taper should be fixed before evaluation and kept
conservative, with explicit tests for monotone layer weights, unchanged aloft
behavior, finite fallback for non-3D leaves, and no accidental change to the
accepted Richardson 10 m diagnostic path.
