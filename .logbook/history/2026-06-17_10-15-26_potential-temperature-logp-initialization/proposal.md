---
schema_version: 1
slug: potential-temperature-logp-initialization
title: Initialize Temperature Through Log-Pressure Potential Temperature
status: ready
created_at: 2026-06-17T10:10:34Z
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

# Initialize Temperature Through Log-Pressure Potential Temperature

## Hypothesis

The current incumbent's strongest accepted gains came from making the initial
sigma-coordinate thermodynamic column more hydrostatically consistent before
DFI. It now estimates dry temperature from geopotential thickness, then remaps
temperature itself from pressure levels to sigma levels in log pressure.

For dry adiabatic primitive-equation dynamics, potential temperature is the more
natural thermodynamic coordinate than temperature because it removes the
background compressional dependence on pressure. Interpolating the accepted
hydrostatic dry-temperature estimate as potential temperature, then converting
back to temperature at the target sigma pressure, should preserve vertical
static-stability structure with less spurious warming or cooling across thick
pressure intervals. The mechanism is narrower than the rejected conservative
pressure-thickness remap because it changes only the thermodynamic variable
used for initialization interpolation; winds, humidity, surface pressure,
vertical grid, DFI, weak Held-Suarez relaxation, and output packing are
unchanged.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init`.
Preserve the incumbent DFI, near-surface residual correction, weak thermal
Held-Suarez relaxation, log-pressure initialization for non-temperature fields,
layer-mean hydrostatic temperature estimate, finite sigma-to-pressure output
packing, vertical advection, spectral truncation, inner step, and public API.

During `weather_state_to_dinosaur_state`, after the incumbent layer-mean
hydrostatic temperature estimate and before pressure-to-sigma interpolation:

- compute source pressure-level dry potential temperature
  `theta = temperature * (p0 / p) ** kappa` using the Dinosaur dry-air `kappa`
  constant and a fixed `p0 = 1000 hPa`;
- interpolate `theta` from pressure levels to sigma centers in log pressure
  using the same interpolation helper and target pressure
  `sigma_center * surface_pressure_hpa` as the incumbent;
- convert the interpolated result back to target dry temperature with
  `temperature = theta * (target_pressure / p0) ** kappa`;
- leave wind and passive humidity initialization on the incumbent log-pressure
  interpolation path.

Use finite fallback to the incumbent temperature interpolation wherever target
pressure is nonpositive, source values are nonfinite, or the reconstructed
temperature is nonphysical.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_vertical_interpolation.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init`.
- API changes:
  - None. `ForecastInput`, `WeatherState`, emitted variables, lead times, and
    fixed metrics remain unchanged.
- Tests to update:
  - Unit-test a helper that interpolates temperature through potential
    temperature on a simple analytic column and matches direct temperature
    interpolation when pressure is constant.
  - Unit-test finite fallback for nonpositive target pressure and nonphysical
    reconstructed temperature.
  - Verify the candidate factory preserves all incumbent flags and changes only
    the thermodynamic initialization option.
  - Verify registry construction and a finite no-JIT smoke forecast if existing
    Dinosaur fixtures make this cheap.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if reduced
    thermodynamic interpolation noise improves column thickness and phase.
  - `2m_temperature` may improve after the accepted residual decays if lower-
    tropospheric static stability is initialized more consistently.
  - Primary score should improve modestly if the accepted hydrostatic layer
    initialization still leaves removable thermodynamic remap error.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because wind
    initialization, vertical advection, DFI, and drag-free weak-HS settings are
    unchanged.
- Possible regressions:
  - Potential-temperature interpolation can sharpen or flatten temperature
    gradients differently from direct temperature interpolation and may worsen
    short-lead `2m_temperature` or mass-field RMSE.
  - If the current hydrostatic layer-mean temperature estimate already removes
    most thermodynamic remap error, the primary delta may be below promotion.

## Risks

- Numerical stability:
  - Low to moderate. The change is initialization-only and bounded by finite
    fallback, but it directly changes the initialized temperature column used by
    DFI and subsequent dynamics.
- Compute cost:
  - Low. It adds a few elementwise exponent/log operations and one temperature
    interpolation during initialization only.
- Data leakage:
  - Low. The candidate uses only same-time pressure, temperature, geopotential,
    humidity already used by the incumbent, and fixed dry-air constants.
- Physical plausibility:
  - Moderate to high. Potential temperature is conserved for dry adiabatic
    displacement and is a standard thermodynamic state variable; this is aligned
    with a dry primitive-equation rollout.
- Rollback complexity:
  - Low. The behavior can be isolated behind one adapter flag and one
    side-by-side factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`,
    clean diagnostics, no fixed RMSE guardrail failure, and no early
    `10m_u_component_of_wind` guardrail movement.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_theta_init --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean but sub-threshold or negative iteration delta would show that
    thermodynamic interpolation variable choice is not a material remaining
    error source. Any early `2m_temperature`, `geopotential_500`, or MSLP
    guardrail failure would show that direct temperature interpolation is safer
    for this incumbent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` applies the
  accepted layer-mean hydrostatic temperature initialization, then remaps
  temperature to sigma levels through the current log-pressure path.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/scales.py` defines the
  dry-air `KAPPA = 2 / 7`, and `units.py` exposes `physics_specs.kappa` for
  primitive-equation thermodynamics.
- History: `.logbook/history/2026-06-17_06-42-58_hydrostatic-layer-mean-temperature-init/decision.md`
  accepted the current layer-mean hydrostatic initialization with iteration
  delta `+0.004688970185515728` and validation delta `+0.005305927605172567`.
- History: `.logbook/history/2026-06-17_08-03-52_conservative-pressure-thickness-init-remap/decision.md`
  rejected broad conservative remapping with iteration delta
  `-0.006775878375613553`, motivating a temperature-only variable transform
  rather than another all-field remap.
- NOAA/AOML preliminary notes on potential temperature describe potential
  temperature as unchanged for dry adiabatic motion:
  https://www.aoml.noaa.gov/ftp/hrd/annane/prelim_notes/Potential_Temperature.pdf
- Wallace, J. M. and Hobbs, P. V. 2006. Atmospheric Science: An Introductory
  Survey, second edition, describes potential temperature and dry static
  stability as standard atmospheric thermodynamic diagnostics.
- Rasp, S. et al. 2023. WeatherBench 2: A benchmark for the next generation of
  data-driven global weather models. https://arxiv.org/abs/2308.15560

## Researcher Notes

This is not another hydrostatic derivative variant: it does not change the
accepted layer-mean hypsometric temperature estimator. It changes only the
thermodynamic variable used while moving that estimate from pressure levels to
sigma levels.

It is also not the rejected conservative pressure-thickness remap, the staged
bounded edge extrapolation, or the rejected log-pressure output interpolation.
The conservative remap reinterpreted all pressure-level fields as layer averages
and moved winds and mass-field phase unfavorably. This proposal keeps the
incumbent point-sample interpretation, affects only initialized temperature, and
leaves the output path untouched.

## Evaluator Notes

2026-06-17T10:13:20Z - Move to `ready`; rank 1 of 5 active ideas.

This is the best next dycore iteration. The mechanism is narrow, physically
grounded, and aligned with the strongest accepted incumbent lineage: DFI
improved iteration by `+0.004385840377088002`, near-surface residual diagnostics
by `+0.0353889745054945`, weak thermal Held-Suarez relaxation by
`+0.06357275459004397`, log-pressure initialization by
`+0.006318821843572353`, hydrostatic-thickness initialization by
`+0.0668578150568`, and layer-mean hydrostatic initialization by
`+0.004688970185515728`. The current idea preserves those accepted mechanisms
and changes only the thermodynamic variable used for pressure-level to sigma
temperature initialization.

Relevant negative history also favors this as the safest remaining
initialization follow-up. Conservative pressure-thickness remapping was stable
but regressed iteration primary by `-0.006775878375613553`, so broad all-field
remaps should be avoided. Layer-mean thermal recentering improved primary score
but failed the early `10m_u_component_of_wind` guardrail by just over 2%, so
thermal changes need to be bounded and initialization-local. This proposal is
more localized than either failed path: winds, humidity, surface pressure,
output packing, DFI, weak-HS forcing, vertical transport, and residual
diagnostics stay on the incumbent path.

Source inspection confirms feasibility without a new dependency or API change.
The adapter already applies the accepted layer-mean hydrostatic temperature
estimate before calling the log-pressure pressure-to-sigma interpolation helper,
and the dry-air `kappa` constant is available through the existing Dinosaur
physics path. The implementation should remain side-by-side, with finite
fallback to the incumbent temperature interpolation for invalid pressure or
nonphysical reconstructed temperature. Promote this single ready proposal and
keep all guardrails unchanged.
