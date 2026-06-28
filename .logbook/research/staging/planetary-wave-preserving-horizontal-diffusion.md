---
schema_version: 1
slug: planetary-wave-preserving-horizontal-diffusion
title: Preserve Planetary Waves in Horizontal Diffusion
status: staging
created_at: 2026-06-18T18:48:00Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind
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

# Preserve Planetary Waves in Horizontal Diffusion

## Hypothesis

The incumbent uses a spectral horizontal diffusion filter every inner step. Its
high-wavenumber damping is necessary for stability, but even weak repeated
damping of the lowest resolved planetary and synoptic modes can accumulate over
15 forecast days and reduce large-scale amplitude in `geopotential_500` and
`mean_sea_level_pressure`. A filter that exactly preserves low total
wavenumbers while keeping the incumbent high-wavenumber damping unchanged may
improve medium-range mass-field skill without changing surface residuals,
10 m wind diagnostics, Coriolis splitting, initialization, or fixed protocols.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_planetary_diffusion`.
Preserve the incumbent equation, DFI, weak-HS forcing, hydrostatic/log-pressure
initialization, symmetric Coriolis split, stability-aware near-surface residual
correction, Richardson 10 m wind diagnostic, diffusion order, and top-end
diffusion timescale.

Replace only the rollout and DFI horizontal diffusion filter with an opt-in
masked spectral filter:

- compute total spherical-harmonic wavenumber from `coords.horizontal.modal_axes`;
- set diffusion scale to zero for very low modes, for example total wavenumber
  `n <= 8`;
- smoothly ramp from zero to the incumbent diffusion scale over a transition
  band, for example `8 < n < 16`;
- preserve the exact incumbent scaling for higher modes, including the same
  order and highest-wavenumber e-folding time;
- apply the mask consistently to vorticity, divergence, temperature variation,
  `log_surface_pressure`, and any tracers only through the same tree-map
  behavior as the incumbent filter;
- do not add diffusion, change time step, change spectral truncation, alter
  output interpolation, or tune per variable after seeing scores.

This is not a hyperdiffusion-strength sweep. It protects the lowest
large-scale modes from cumulative numerical damping while retaining the
incumbent grid-scale stabilization.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/filtering.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast inputs, outputs, lead times, target variables, and protocols
    remain unchanged.
- Tests to update:
  - Unit-test the modal mask: exactly zero diffusion for protected low modes,
    smooth finite ramp in transition modes, and incumbent-equivalent scaling for
    high modes.
  - Verify zero transition width is not allowed and invalid cutoffs raise clear
    errors.
  - Verify the candidate factory preserves all incumbent flags except the
    diffusion-filter selector.
  - Verify a synthetic modal state preserves protected coefficients and damps
    high-wavenumber coefficients.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at days 5 to 15 if
    low-wavenumber amplitude loss is a remaining large-scale error source.
  - Primary score may improve without spending the near-surface guardrail margin
    because surface diagnostics and 10 m wind output are unchanged.
- Expected neutral metrics:
  - Early day-1 fields should remain close to incumbent because the initial
    state, DFI span, and high-wavenumber stabilization remain in place.
  - `2m_temperature` and `10m_u_component_of_wind` should be mostly neutral
    except through downstream large-scale phase changes.
- Possible regressions:
  - The incumbent low-mode damping may be suppressing real large-scale error
    growth; preserving those modes could worsen synoptic phase or pressure
    amplitude.
  - Prior diffusion-shape experiments have negative evidence, so the expected
    signal may be small or unfavorable.

## Risks

- Numerical stability:
  - Low to moderate. High-wavenumber damping remains unchanged, but low-mode
    variance may grow more freely over long leads.
- Compute cost:
  - Low. The mask is precomputed from modal axes and reused inside the existing
    filter path.
- Data leakage:
  - None. The filter uses only fixed spectral geometry and fixed constants.
- Physical plausibility:
  - Moderate. Scale-selective diffusion is standard in spectral atmospheric
    models, and preserving large scales while damping small scales is the
    intended numerical role; the exact cutoff is still a modeling choice.
- Rollback complexity:
  - Low. Remove one filter option, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_planetary_diffusion`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_planetary_diffusion --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_planetary_diffusion --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show that cumulative
    planetary-wave damping is not a material remaining error source. Any early
    10 m wind, Z500, or MSLP guardrail failure would show the low-mode
    preservation destabilizes the accepted large-scale balance.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` builds the
    incumbent horizontal diffusion filter through `_horizontal_diffusion_step_filter`.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/filtering.py`
    implements spectral filters from modal total wavenumber.
  - Dynamaxx history:
    `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
    rejected changing diffusion order after iteration delta
    `-0.05124210065383061` and early 10 m wind degradation; this proposal keeps
    high-wavenumber damping unchanged and only removes low-mode damping.
  - Dynamaxx history:
    `.logbook/history/2026-06-18_13-26-11_symmetric-horizontal-diffusion-split/decision.md`
    found diffusion half-step ordering neutral/slightly negative; this proposal
    changes spectral selectivity rather than split order.
  - Roeckner et al. 2003, "The atmospheric general circulation model ECHAM5:
    Part I", documents spectral horizontal diffusion, scale selectivity, and
    expressing damping through highest-wavenumber e-folding time.
    https://pure.mpg.de/rest/items/item_995269_7/component/file_3192562/content
  - Jablonowski, C. and Williamson, D. L. 2011. The pros and cons of diffusion,
    filters and fixers in atmospheric general circulation models. In Numerical
    Techniques for Global Atmospheric Models. Springer.
    https://doi.org/10.1007/978-3-642-11640-7_13
  - Gelb, A. and Gleeson, J. P. 2001. Spectral viscosity for shallow water
    equations in spherical geometry. Monthly Weather Review.
    https://doi.org/10.1175/1520-0493(2001)129%3C2346:SVFSWE%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of rejected `scale-selective-hyperdiffusion`, which
changed the diffusion order and therefore the full damping curve. The present
proposal preserves the incumbent high-wavenumber e-folding behavior and only
protects the lowest total wavenumbers from cumulative damping.

It is also distinct from active staged `dissipative-heating-from-horizontal-diffusion`,
which keeps the incumbent diffusion and changes thermodynamic energy accounting,
and from `two-thirds-explicit-tendency-dealiasing`, which filters nonlinear
tendencies rather than the step filter. The prior diffusion history is negative
and should be treated as a serious risk, but the mechanism tests a different
failure mode: long-lead large-scale amplitude loss rather than underdamped
grid-scale noise or split-order error.

## Evaluator Notes

### 2026-06-18T18:47:01Z

Decision: move to `staging`, low-priority fallback.

The proposal is implementable and scientifically distinct enough to preserve:
scale-selective filters are standard in spectral atmospheric models, and this
candidate preserves the incumbent high-wavenumber damping while protecting only
the lowest total wavenumbers. It is not a duplicate of rejected
`scale-selective-hyperdiffusion`, which changed the full damping curve/order,
or rejected `symmetric-horizontal-diffusion-split`, which changed filter
placement rather than spectral selectivity.

Do not promote it now. The direct family evidence is unfavorable:
scale-selective hyperdiffusion regressed strongly, diffusion ordering was
neutral/slightly negative, and prior diffusion order/strength variants have not
shown useful primary-score movement. Removing low-mode damping could preserve
real planetary-wave amplitude, but it could also preserve large-scale forecast
error growth and degrade MSLP/Z500 phase. Keep staged only as a later,
well-isolated mass-field amplitude test after stronger thermodynamic and
transient-spinup candidates are scored.
