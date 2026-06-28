---
schema_version: 1
slug: passive-humidity-global-mass-fixer
title: Conserve Passive Humidity Mass During Rollout
status: scrap
created_at: 2026-06-18T14:33:12Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
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

# Conserve Passive Humidity Mass During Rollout

## Hypothesis

The incumbent is dynamically dry, but it still advects `specific_humidity` as a
passive tracer and uses that tracer in the virtual-temperature geopotential
diagnostic. Spectral passive-tracer transport and repeated horizontal diffusion
can introduce small global water-mass drift even when humidity is not active in
the momentum or thermodynamic equations. A conservative passive-humidity fixer
may reduce spurious virtual-temperature thickness drift, especially for
`geopotential_500`, without adding moist dynamics, saturation adjustment, latent
heating, or target-specific output corrections.

## Mechanism

Register a side-by-side candidate named
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_q_mass_fixer`.
Preserve the accepted DFI, near-surface residuals, weak Held-Suarez thermal
forcing, log-pressure and hydrostatic layer initialization, symmetric exact
Coriolis split, horizontal diffusion settings, pressure-level outputs, and fixed
forecast API.

Add an optional positive-time step filter that runs after the incumbent
diffusion/Coriolis step:

- if the trajectory carries no `specific_humidity` tracer, return the incumbent
  state unchanged;
- convert previous and candidate next humidity tracers plus next
  `log_surface_pressure` to nodal values;
- compute a dry-air-mass proxy proportional to
  `area_weight * sigma_thickness * surface_pressure` for each layer and grid
  point;
- preserve the previous step's global mass-weighted humidity integral by a
  single multiplicative correction applied to the next humidity field;
- optionally fill only negative humidity holes with a bounded, mass-conserving
  redistribution before the multiplicative correction;
- transform only humidity back to modal tracer space;
- leave vorticity, divergence, temperature variation, log surface pressure,
  `sim_time`, near-surface residuals, DFI filters, and all emitted channel names
  unchanged.

The first implementation should apply the fixer only during forward rollout, not
inside time-reversed DFI. This tests conservation of a passive diagnostic tracer
rather than another DFI bookkeeping change.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast inputs, outputs, leads, variables, metrics, and protocols stay
    fixed.
- Tests to update:
  - Unit-test that the fixer exactly preserves a synthetic mass-weighted humidity
    integral while changing no non-humidity state leaves.
  - Verify zero or absent humidity is a deterministic no-op.
  - Verify the candidate factory preserves every incumbent flag except the new
    passive-humidity mass fixer.
  - Verify the DFI filter path remains the incumbent path.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at medium and long leads if passive humidity drift is
    perturbing virtual-temperature thickness in the output diagnostic.
  - `2m_temperature` may improve weakly through more stable lower-column
    humidity diagnostics when near-surface residuals decay.
- Expected neutral metrics:
  - `mean_sea_level_pressure` and `10m_u_component_of_wind` should be close to
    neutral because humidity remains passive and prognostic dry dynamics are
    unchanged.
- Possible regressions:
  - If virtual-temperature humidity errors partly compensate dry temperature
    errors, conserving humidity mass can worsen Z500.
  - A global correction may be too blunt if humidity drift is spatially localized
    or dominated by vertical interpolation rather than rollout transport.

## Risks

- Numerical stability:
  - Low to moderate. The correction is multiplicative and bounded, but humidity
    enters geopotential output and therefore can move scored Z500.
- Compute cost:
  - Low. It adds one tracer nodal transform and a few global reductions per inner
    step when humidity exists.
- Data leakage:
  - None. The fixer uses only previous and next forecast states plus fixed grid
    weights.
- Physical plausibility:
  - Moderate to high for passive tracer bookkeeping. It is not a moist physics
    parameterization and should be interpreted as a conservative transport
    repair.
- Rollback complexity:
  - Low. Remove one filter option, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_q_mass_fixer`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_q_mass_fixer --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`, clean
    diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and no
    variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_q_mass_fixer --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show passive humidity
    mass drift is not a material remaining error source. Any Z500 guardrail
    failure would show the humidity correction disrupts a compensating diagnostic
    balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` carries
  `specific_humidity` as a tracer when pressure-level humidity exists, while the
  incumbent keeps `use_humidity_in_dynamics=False`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` passes
  humidity into `primitive_equations.get_geopotential_on_sigma`, so passive
  humidity can affect pressure-level geopotential diagnostics even in dry
  dynamics.
- History: `.logbook/history/2026-06-17_12-29-40_passive-humidity-dfi-bypass/decision.md`
  found passive-humidity DFI bypass effectively neutral; this proposal instead
  targets forward tracer conservation after DFI.
- History: `.logbook/history/2026-06-17_19-31-12_bounded-saturation-adjustment/decision.md`
  rejected saturation adjustment with iteration delta `-0.026391567842939834`;
  this proposal adds no latent heating and does not alter temperature tendencies.
- Diamantakis, M. and Flemming, J. 2014. Global mass fixer algorithms for
  conservative tracer transport in the ECMWF model. Geoscientific Model
  Development. https://gmd.copernicus.org/articles/7/965/2014/
- Williamson, D. L. and Rasch, P. J. 1994. Water vapor transport in the NCAR
  CCM2. Tellus A. https://onlinelibrary.wiley.com/doi/10.1034/j.1600-0870.1994.00004.x
- ECMWF IFS Documentation CY49R1, Part III: Dynamics and Numerical Procedures,
  documents tracer mass-fixer algorithms in operational semi-Lagrangian
  transport. https://www.ecmwf.int/sites/default/files/elibrary/112024/81625-ifs-documentation-cy49r1-part-iii-dynamics-and-numerical-procedures.pdf

## Researcher Notes

This is not a duplicate of rejected moist-dynamics or saturation-adjustment
candidates. It does not feed humidity back into momentum, pressure-gradient, or
temperature tendencies. It is also not a duplicate of the scrapped
`bounded-virtual-humidity-geopotential` diagnostic guard: that proposal clipped
humidity only at output time, while this one preserves a transport invariant for
the passive tracer itself.

It is intentionally different from recent pressure-continuity and wind residual
failures. The correction touches only one passive tracer leaf and tests whether
humidity conservation has enough diagnostic leverage on Z500 to matter under
the current dry incumbent.

## Evaluator Notes

### 2026-06-18T14:37:31Z

Decision: move to `scrap`.

The mechanism is implementable and not a literal duplicate of passive-humidity
DFI bypass, saturation adjustment, or the bounded virtual-humidity diagnostic.
However, the evidence is too weak for another humidity-only experiment. Passive
humidity positivity limiting and DFI bypass both moved the iteration score only
at near-roundoff scale, while moist feedback and saturation-adjustment variants
were strongly negative. The proposal adds per-step global reductions and a
multiplicative tracer correction without read-only evidence that global
humidity-mass drift is contaminating `geopotential_500` enough to clear the
fixed `+0.002` iteration gate.

Rank it below the staged hypsometric Z diagnostic because hypsometric
integration directly targets the scored hydrostatic pressure-level diagnostic.
This proposal instead assumes a passive-tracer conservation error that has not
shown measurable leverage in prior humidity tests and could remove compensating
virtual-temperature structure.
