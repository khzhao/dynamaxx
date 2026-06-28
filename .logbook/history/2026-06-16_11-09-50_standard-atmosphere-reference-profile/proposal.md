---
schema_version: 1
slug: standard-atmosphere-reference-profile
title: Use a Standard-Atmosphere Reference Temperature Profile
status: ready
created_at: 2026-06-16T10:52:48Z
author_role: Researcher
target_model: dinosaur_dfi
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Use a Standard-Atmosphere Reference Temperature Profile

## Hypothesis

The incumbent `dinosaur_dfi` decomposes temperature into a constant 250 K
reference state plus a prognostic temperature variation on every sigma layer.
The semi-implicit primitive-equation split uses that reference temperature in
gravity-wave, hydrostatic, pressure-divergence, and temperature-coupling terms.
A constant 250 K profile is convenient but not representative of either the
lower troposphere or the stratosphere, so it leaves large vertical-mean
temperature residuals for the explicit terms and for DFI to handle.

A fixed standard-atmosphere vertical reference profile should improve numerical
balance and linearization accuracy without adding forcing, target-specific
diagnostics, or data-fitted parameters. Because total physical temperature is
still reconstructed as `reference_temperature + temperature_variation`, the
proposal changes the implicit-explicit partition and initialization balance, not
the forecast API or the initialized physical field.

## Mechanism

Add an adapter option that builds a one-dimensional reference-temperature vector
from a dry standard atmosphere instead of filling every layer with 250 K. The
side-by-side candidate should keep DFI enabled and use a model name such as
`dinosaur_dfi_ref_profile`.

The candidate mechanism should:

- Define a deterministic helper that maps each sigma-layer center to a reference
  pressure using `p = sigma_center * 1000 hPa`.
- Compute a dry standard-atmosphere temperature at that pressure by interpolating
  a small pressure-temperature table in log pressure, based on the 1976 U.S.
  Standard Atmosphere. Clamp the result to a physically conservative range, such
  as 200 K to 300 K, to avoid extreme upper-level values on the 1 hPa level.
- Use this vector anywhere the adapter currently uses `_reference_temperature`,
  including conversion into `temperature_variation`, primitive-equation
  construction, DFI, and output reconstruction.
- Keep the canonical `dinosaur` and incumbent `dinosaur_dfi` factories unchanged.
  Register only a side-by-side candidate so the Orchestrator can compare against
  the accepted incumbent.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add a side-by-side `dinosaur_dfi_ref_profile` factory that enables DFI and
    the standard-atmosphere reference profile.
- API changes:
  - None. `forecast(ForecastInput) -> WeatherState` remains unchanged.
- Tests to update:
  - Add a helper test showing the standard profile has one finite value per
    layer, is warmer near the surface than aloft, and stays within the clamp.
  - Add a no-JIT forecast test confirming the candidate preserves output shape,
    requested variables, and finite values.
  - Add a conversion round-trip test showing lead-zero physical temperature is
    unchanged when the reference profile changes and `temperature_variation` is
    adjusted consistently.
  - Add registry tests confirming `dinosaur_dfi_ref_profile` is available and
    has `apply_digital_filter_initialization=True`.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at early and medium leads if
    the more realistic implicit reference state reduces hydrostatic and gravity
    wave splitting error.
  - Primary score may improve through the same broad-balance channel that made
    DFI useful, but without adding another time filter.
- Expected neutral metrics:
  - `2m_temperature` may be neutral because the proposal does not add radiation,
    surface exchange, or near-surface diagnostic correction.
  - Late leads may remain dominated by missing physics and dry-model drift.
- Possible regressions:
  - `10m_u_component_of_wind` could regress if the changed mass-wind balance
    alters low-level divergence during spin-up.
  - If the constant 250 K profile happened to be a better numerical compromise
    for the low-resolution sigma grid, the standard profile could worsen the
    primary score despite being physically more realistic.

## Risks

- Numerical stability:
  - Low to moderate. Dinosaur already supports nonconstant reference
    temperatures and includes the extra vertical-advection term for `T_ref`, but
    the changed implicit matrix and DFI path must pass the fast gate.
- Compute cost:
  - Negligible. The reference vector is one length-per-layer array and does not
    increase trajectory length, spectral truncation, or output size.
- Data leakage:
  - Low. The proposed profile is analytic and fixed, with no fitting to
    iteration, validation, or future truth.
- Physical plausibility:
  - Good as a dry numerical reference state. It is not a full climatology and
    should not be described as adding missing diabatic physics.
- Rollback complexity:
  - Low. The change can be isolated behind one adapter option and one candidate
    factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_ref_profile`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_ref_profile --workers 4`.
  - Support for the hypothesis is a primary-score improvement over
    `dinosaur_dfi`, preferably with neutral or improved early-lead
    `mean_sea_level_pressure` and `geopotential_500` and no early 10 m wind
    guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_ref_profile --workers 4`
    only after iteration promotion.
  - Validation should preserve the same balance-driven direction rather than
    depending on one lead or one target variable.
- Outcome that would falsify the hypothesis:
  - A clean iteration run with worse primary score, no mass-field improvement, or
    an early `10m_u_component_of_wind` regression above the fixed gate would
    show that the reference profile is not useful for this incumbent.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` currently
  creates a constant 250 K reference vector through `_reference_temperature` and
  uses it for state conversion, equation construction, DFI, and output packing.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  uses `reference_temperature` in the sigma-coordinate implicit matrix,
  hydrostatic geopotential terms, and nonconstant-`T_ref` vertical temperature
  tendencies.
- Simmons, A. J., Hoskins, B. J., and Burridge, D. M. 1978. Stability of the
  semi-implicit method of time integration. Monthly Weather Review.
  https://journals.ametsoc.org/view/journals/mwre/106/3/1520-0493_1978_106_0405_sotsim_2_0_co_2.pdf
- Robert, A. 1981. A stable numerical integration scheme for the primitive
  meteorological equations. Atmosphere-Ocean.
  https://www.tandfonline.com/doi/abs/10.1080/07055900.1981.9649098
- U.S. Standard Atmosphere, 1976. NASA Technical Reports Server record.
  https://ntrs.nasa.gov/citations/19770009539
- Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications to
  Geophysics, second edition. Springer.

## Researcher Notes

This is not a duplicate of accepted `balanced-digital-filter-initialization`: DFI
adds a short initialization integration, while this proposal changes the
semi-implicit reference state used during both initialization and the main
trajectory. It is not another diffusion or filtering proposal, and it does not
touch the rejected hyperdiffusion mechanism.

It is also distinct from staged `held-suarez-relaxation-forcing`: no Newtonian
relaxation, Rayleigh drag, or persistent physical forcing is added. The proposal
is a numerical split/balance experiment. It is deliberately lower surface-area
than enabling moist virtual-temperature dynamics, which previously failed the
fast diagnostic gate, and it does not change the fixed evaluation protocol.

## Evaluator Notes

2026-06-16T10:58:43Z - Move to `ready`.

This is the best implementable next idea against incumbent `dinosaur_dfi` at
commit `cfdc344723cee1f267b892ddd924fc5d07b89f2d`. Source inspection confirms
the adapter builds a constant 250 K reference vector and threads it through
pressure-to-sigma conversion, primitive-equation construction, DFI, and output
reconstruction. The primitive-equation code also already accepts a length-layer
`reference_temperature` vector and includes nonconstant-reference-temperature
vertical tendency terms, so the implementation surface is small and mostly
isolated behind one adapter option plus one side-by-side registry factory.

The scientific support is adequate. The NASA U.S. Standard Atmosphere record is
a reputable fixed source for a dry pressure-temperature reference profile, and
ECMWF IFS documentation uses a reference temperature in semi-implicit pressure
gradient and surface-pressure/orography splitting terms. The proposal should be
framed as a numerical linearization and balance experiment, not as added
radiation, surface exchange, or learned climatology.

Rank this above terrain, Held-Suarez, and near-surface diagnostics for the next
candidate. It preserves DFI, does not touch forecast inputs, avoids static-data
plumbing, has negligible runtime cost, and plausibly affects both MSLP and Z500
through the same balance pathway that made DFI useful. The main risk is that the
existing constant 250 K value is a better low-resolution compromise than a
standard-atmosphere profile, so this must remain a side-by-side candidate such
as `dinosaur_dfi_ref_profile` and must not tune the profile against iteration or
validation outputs.
