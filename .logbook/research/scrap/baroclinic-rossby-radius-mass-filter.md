---
schema_version: 1
slug: baroclinic-rossby-radius-mass-filter
title: Apply a Baroclinic Rossby-Radius Filter to Mass and Thermal Modes
status: scrap
created_at: 2026-06-21T21:34:31Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Apply a Baroclinic Rossby-Radius Filter to Mass and Thermal Modes

## Hypothesis

The incumbent already uses scalar modal diffusion, exact Coriolis splitting, and
off-centered semi-implicit damping. Recent momentum-diffusion and vorticity
dealiasing refinements were effectively neutral, so another broad wind filter
is unlikely to help. Remaining MSLP and Z500 error may instead come from
unbalanced small-scale mass and thermal modes whose natural balanced length
scale depends on static stability and latitude.

A weak, opt-in post-step filter that damps only temperature and surface-pressure
modes shorter than a conservative baroclinic Rossby-radius proxy can suppress
unbalanced mass noise while sparing planetary wind/vorticity structure and
leaving near-surface residual outputs unchanged.

## Mechanism

Register a side-by-side candidate extending the incumbent name with
`_rossby_mass_filter`. Preserve the incumbent DFI, weak-HS analysis equilibrium,
theta tendency, theta recentering, off-centered SIL3, Coriolis split, standard
horizontal diffusion, scale-separated residuals, Richardson 10 m wind
diagnostic, and output contract.

For this candidate only:

- after the normal step filters, compute a fixed latitude-dependent spectral
  attenuation mask from the horizontal total wavenumber and a conservative
  first-baroclinic Rossby-radius proxy;
- use a simple bounded proxy based on sigma-layer static stability from the
  current thermal state and Coriolis magnitude, with caps near the equator and
  poles so the mask remains finite and smooth;
- apply the mask only to `temperature_variation` and `log_surface_pressure`;
- leave `vorticity`, `divergence`, humidity/tracers, Coriolis rotation,
  weak-HS forcing, and residual output corrections unchanged;
- make the attenuation weak enough to be a safety filter, not a replacement for
  the incumbent horizontal diffusion;
- fall back to the incumbent state if static-stability diagnostics, masks, or
  filtered leaves are nonfinite.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/filtering.py` if a reusable modal mask
    helper is cleaner than adapter-local code
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side candidate with suffix `_rossby_mass_filter`.
- API changes:
  - None. Forecast variables, shapes, lead times, metrics, and fixed protocols
    remain unchanged.
- Tests to update:
  - Unit-test mask bounds at equator, midlatitudes, and polar rows.
  - Verify vorticity, divergence, tracers, and `sim_time` are unchanged by the
    filter.
  - Verify low total wavenumbers are preserved and high mass/thermal modes are
    weakly damped.
  - Verify finite fallback and factory/registry coverage.
  - Add a non-JIT finite smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` if short-scale mass/thermal
    imbalance remains after the accepted off-centered rollout.
  - `2m_temperature` may improve slightly if lower-column thermal noise is
    reduced before the accepted residual correction.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because
    vorticity/divergence and the 10 m wind diagnostic are untouched.
- Possible regressions:
  - The incumbent scalar diffusion may already be optimal; extra thermal/mass
    damping can oversmooth fronts and worsen Z500/MSLP phase.
  - Static-stability proxies can be noisy, so masks must be capped and smooth.

## Risks

- Numerical stability:
  - Low to moderate. The filter is damping-only and bounded, but it touches
    prognostic mass and thermal leaves each step.
- Compute cost:
  - Low to moderate. It adds mask diagnostics and modal multiplications but no
    extra rollout steps or resolution.
- Data leakage:
  - None. It uses only forecast state and fixed physical constants.
- Physical plausibility:
  - Moderate. Rossby deformation radius separates balanced large-scale flow from
    smaller-scale inertia-gravity adjustment, but this is a simple spectral
    proxy rather than a normal-mode decomposition.
- Rollback complexity:
  - Low. Remove one filter option/helper, one factory/export, one registry
    entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached
    incumbent metrics, clean diagnostics, and no fixed RMSE guardrail failures.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that residual
    mass/thermal imbalance is not improved by this filter. Any early MSLP or
    Z500 guardrail failure would show the damping is too intrusive.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` builds the
    incumbent step filters and leaves `temperature_variation` and
    `log_surface_pressure` coupled to output MSLP/Z500 diagnostics.
  - Dynamaxx history:
    `.logbook/history/2026-06-21_16-05-39_helmholtz-projected-momentum-diffusion/decision.md`
    rejected a momentum diffusion refinement as effectively neutral, motivating
    a different mass/thermal-only filter.
  - Dynamaxx history:
    `.logbook/history/2026-06-20_05-39-53_absolute-vorticity-flux-dealiasing/decision.md`
    found narrow vorticity product dealiasing subthreshold, so this proposal
    avoids another vorticity/momentum-only change.
  - Gill, A. E. 1982. Atmosphere-Ocean Dynamics. Academic Press. Describes
    Rossby deformation radius and balanced large-scale dynamics.
  - Vallis, G. K. 2017. Atmospheric and Oceanic Fluid Dynamics, second edition.
    Cambridge University Press. Discusses deformation radius and balanced
    geophysical flow.
  - Jablonowski, C. and Williamson, D. L. 2006. A Baroclinic Instability Test
    Case for Atmospheric Model Dynamical Cores. Quarterly Journal of the Royal
    Meteorological Society. https://doi.org/10.1256/qj.06.12

## Researcher Notes

This is decorrelated from recent near-no-op analysis-HS source variants and from
momentum-only diffusion. It is also not a vertical normal-mode filter: it does
not compute eigenmodes or alter the forecast contract. The implementation
should be held to a high bar because staged diffusion proposals already exist;
the distinct mechanism is that only mass and thermal modes are damped and the
cutoff is tied to a conservative baroclinic length-scale proxy rather than a
fixed total-wavenumber taper.

## Evaluator Notes

### 2026-06-21T21:38:13Z

Moved to `scrap`. The physical motivation is recognizable, but this is still a
broad rollout filter on prognostic mass and thermal fields, with a tunable proxy
cutoff and overlap with many staged diffusion, dealiasing, and mass-filter
ideas. Recent fixed-gate evidence from Helmholtz-projected momentum diffusion
and absolute-vorticity flux dealiasing showed clean but subthreshold movement,
and this proposal adds higher guardrail risk to MSLP/Z500 without a clear path
to the required `+0.002` iteration gain. Rank 3 of 3.
