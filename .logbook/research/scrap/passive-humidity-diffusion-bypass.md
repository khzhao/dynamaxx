---
schema_version: 1
slug: passive-humidity-diffusion-bypass
title: Bypass Horizontal Diffusion for Passive Humidity Diagnostics
status: scrap
created_at: 2026-06-20T04:32:18Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/filtering.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Bypass Horizontal Diffusion for Passive Humidity Diagnostics

## Hypothesis

The incumbent keeps humidity out of prognostic dynamics, but still carries
specific humidity as a passive tracer and uses it in virtual-temperature
geopotential reconstruction. The generic horizontal diffusion filter applies to
the entire state tree, including passive tracers. That is useful for active
dynamical variables, but for passive diagnostic humidity it can smear sharp
moisture gradients and introduce an artificial virtual-temperature thickness
bias without any compensating latent heating or moisture dynamics.

Bypassing only the positive-time horizontal diffusion of passive humidity should
preserve more analyzed moisture structure for geopotential diagnostics while
leaving winds, temperature, pressure, DFI, residual memory, and fixed forecast
protocols unchanged.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_qdiff_bypass`.
Preserve every incumbent option except positive-time filtering of passive
humidity tracers.

For this candidate only:

- keep humidity passive: do not set `humidity_key`, do not add moist momentum,
  moist temperature tendencies, latent heating, saturation adjustment, or
  humidity-aware DFI;
- build the incumbent horizontal diffusion filter for vorticity, divergence,
  temperature, log_surface_pressure, and any active state leaves;
- when applying that filter in positive-time rollout, restore the
  `specific_humidity` tracer from the pre-filter state after all non-humidity
  leaves have been diffused;
- keep DFI on the incumbent filter path so time-reversed initialization remains
  unchanged and this proposal isolates positive-time diagnostic humidity drift;
- retain existing finite guards for humidity output and geopotential
  reconstruction; if humidity is absent, the candidate is exactly the
  incumbent;
- do not change pressure-level interpolation, scale-separated residual memory,
  10 m wind diagnostics, or output variable selection.

This is not a humidity mass fixer and not log-humidity transport. It tests
whether the existing diffusion of a diagnostic-only tracer is harmful.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/filtering.py` if a named selective
    filter helper is preferable to adapter-only composition
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the candidate named above.
- API changes:
  - None. Forecast input/output contract, target variables, lead times, splits,
    and metrics remain fixed.
- Tests to update:
  - Unit-test that positive-time diffusion changes wind/temperature leaves but
    restores the `specific_humidity` tracer exactly.
  - Verify the candidate is identical to the incumbent when no humidity channels
    are present.
  - Verify DFI filter construction remains the incumbent path.
  - Verify output humidity and geopotential diagnostics remain finite.
  - Verify the candidate factory preserves every incumbent option except the
    passive-humidity diffusion selector and model name.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at medium and long leads if over-diffused passive
    humidity is contaminating virtual-temperature thickness diagnostics.
  - `mean_sea_level_pressure` may improve indirectly through more consistent
    pressure-level diagnostic thickness, though the prognostic pressure state is
    unchanged.
- Expected neutral metrics:
  - `2m_temperature` and `10m_u_component_of_wind` should remain near incumbent
    because thermal dynamics, residual memory, and wind diagnostics are
    unchanged.
- Possible regressions:
  - Humidity diffusion may currently suppress noisy passive-tracer ringing that
    would otherwise degrade Z500 diagnostics.
  - If the fixed target set is weakly sensitive to passive humidity, the result
    may be clean but subthreshold like prior humidity bookkeeping ideas.

## Risks

- Numerical stability:
  - Low to moderate. Humidity stays passive and finite-guarded, but bypassing
    diffusion can preserve sharper tracer structures.
- Compute cost:
  - Negligible. It replaces one tracer leaf after the existing filter.
- Data leakage:
  - None. It uses only forecast-state humidity and fixed filter routing.
- Physical plausibility:
  - Moderate. Positive and conservative tracer transport is a known concern in
    atmospheric models, but bypassing diffusion is a minimal diagnostic test
    rather than a complete monotone transport scheme.
- Rollback complexity:
  - Low. Remove one selective-filter option, one factory/export, one registry
    entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_qdiff_bypass`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_qdiff_bypass --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_qdiff_bypass --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero iteration delta would show passive humidity diffusion is
    not a material remaining error source. A Z500 guardrail failure would show
    the incumbent diffusion is protecting diagnostics from tracer noise.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` carries
  `specific_humidity` in `state.tracers` even when humidity is not used in the
  prognostic equation, then uses it in `get_geopotential_on_sigma`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/filtering.py` applies
  horizontal diffusion through a tree-map filter that can act on tracer leaves.
- Dynamaxx history:
  `.logbook/history/2026-06-16_21-13-22_passive-humidity-positivity-limiter/decision.md`
  rejected after-the-fact clipping as clean but slightly negative, so this
  proposal avoids clipping and instead changes only filter routing.
- Dynamaxx research:
  `.logbook/research/staging/log-humidity-passive-tracer.md` changes the tracer
  representation. This proposal keeps specific humidity representation and
  tests only whether diffusion of a diagnostic passive tracer is harmful.
- Diamantakis, M., and Agusti-Panareda, A. 2017. A positive definite tracer mass
  fixer for high resolution weather and atmospheric composition forecasts.
  ECMWF Technical Memorandum 819.
  https://www.ecmwf.int/en/elibrary/80422-positive-definite-tracer-mass-fixer-high-resolution-weather-and-atmospheric
- Lauritzen, P. H., Skamarock, W. C., Prather, M. J., and Taylor, M. A. 2012.
  A standard test case suite for two-dimensional linear transport on the sphere.
  Geoscientific Model Development. https://doi.org/10.5194/gmd-5-887-2012
- GFDL. Idealized Models with Spectral Dynamics. The documentation notes
  conservation difficulties for tracers and dry air in spectral dynamics.
  https://www.gfdl.noaa.gov/idealized-models-with-spectral-dynamics/

## Researcher Notes

This is not a duplicate of rejected `passive-humidity-dfi-bypass`, which changed
DFI routing and was effectively neutral. This proposal leaves DFI unchanged and
targets positive-time horizontal diffusion of diagnostic humidity.

It is not a duplicate of staged `log-humidity-passive-tracer`, scrapped
`passive-humidity-global-mass-fixer`, or scrapped
`bounded-virtual-humidity-geopotential`: it does not change humidity variables,
apply mass rescaling, clip diagnostic humidity, or activate moist dynamics.
The idea should be considered lower priority if the Evaluator views prior
humidity evidence as too weak, but it is mechanically distinct and cheap.

## Evaluator Notes

### 2026-06-20T04:40:42Z

Decision: move to `scrap`.

Source inspection supports the mechanical premise: passive `specific_humidity`
is stored in `state.tracers`, the horizontal diffusion filter is tree-mapped
over matching modal leaves, and diagnostic geopotential uses the recovered
humidity when present. The proposal is therefore distinct from the rejected DFI
humidity bypass.

The local evidence still makes the cost-risk tradeoff unfavorable. The closest
humidity-only scored experiments were clean but score-irrelevant or negative:
the passive humidity positivity limiter moved iteration by only
`-0.0000019440828125105725`, and passive humidity DFI bypass moved by only
`-1.9179700339044814e-07`. Broader humidity feedback experiments were much
worse. This candidate again preserves or reroutes a passive tracer without a
new dynamical coupling, while the fixed target set has no humidity target and
can only benefit indirectly through Z500/MSLP diagnostics.

Bypassing positive-time diffusion could be more visible than the DFI-only
experiment, but the most likely effect is preserving passive-tracer ringing
that the incumbent diffusion currently damps. The staged
`log-humidity-passive-tracer` remains the better representative if the loop
later revisits humidity transport because it addresses positivity and
diagnostic bounds more directly. Do not consume a ready slot on this bypass
without read-only evidence that diffused passive humidity is materially
degrading evaluated geopotential diagnostics.
