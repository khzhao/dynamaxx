---
schema_version: 1
slug: reversible-cloud-water-partition
title: Partition Supersaturated Humidity into Reversible Cloud Condensate
status: scrap
created_at: 2026-06-24T18:46:33Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Partition Supersaturated Humidity into Reversible Cloud Condensate

## Hypothesis

The incumbent carries humidity passively and uses humidity in pressure-level
geopotential output, but it does not represent condensate storage. The rejected
`bounded-saturation-adjustment` showed that irreversible supersaturation removal
with latent heating damaged mass, height, and wind skill. A narrower reversible
partition can test a different physical question: whether noisy passive water
vapor should be split into vapor plus cloud condensate for diagnostic virtual
temperature, while conserving total water and adding no latent heating,
precipitation, radiation, or active moist pressure-gradient dynamics.

## Mechanism

Add a side-by-side candidate such as `dino_hsl2_mass_dse_cloudpart`.

When specific humidity is present:

- initialize an internal cloud-condensate tracer to zero alongside the existing
  humidity tracer;
- after each positive-time step, compute sigma-layer pressure and temperature,
  a guarded saturation specific humidity, and total water
  `q_total = q_vapor + q_cloud`;
- partition total water reversibly:
  - `q_vapor_new = min(q_total, q_sat + q_supersat_tolerance)`;
  - `q_cloud_new = max(q_total - q_vapor_new, 0)`;
  - allow cloud condensate to evaporate automatically when the column becomes
    subsaturated because the same total-water partition is recomputed each step;
- conserve `q_vapor + q_cloud` pointwise before existing transport/filter
  effects; do not add `L_v / c_p` latent heating and do not remove water as
  precipitation;
- keep humidity and cloud condensate passive in the dynamics by leaving
  `use_humidity_in_dynamics=False`;
- pass the cloud condensate only to the existing virtual-temperature
  geopotential diagnostic path, where condensate loading reduces virtual
  temperature consistently with the existing `clouds` argument;
- keep forecast output variables unchanged; cloud condensate is internal and not
  scored or emitted;
- fall back to the incumbent humidity-only diagnostic when saturation,
  total-water, or cloud fields are nonfinite or out of broad physical bounds.

## Implementation Scope

- Expected files:
  - `adapter.py` for tracer initialization, forecast-output cloud diagnostic
    plumbing, and the positive-time partition filter.
  - `primitive_equations.py` only if a small shared saturation helper or cloud
    tracer key is cleaner there.
  - `__init__.py`, `registry.py`, and focused tests.
- Registry changes:
  - Add one side-by-side candidate, `dino_hsl2_mass_dse_cloudpart`.
- API changes:
  - None. No new required input or output variable, no protocol change, and no
    training.
- Tests to update:
  - Verify pointwise total-water conservation by the partition helper.
  - Verify zero cloud and subsaturated humidity reproduce incumbent diagnostics.
  - Verify supersaturation creates finite nonnegative cloud condensate without a
    temperature tendency.
  - Verify cloud condensate is not returned as a forecast output variable.
  - Verify dry/no-humidity input falls back exactly to the incumbent path.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` if humid or supersaturated regions currently create a
    virtual-temperature thickness bias in pressure-level interpolation.
  - `mean_sea_level_pressure` indirectly if cleaner geopotential/thickness
    output reduces mass-field diagnostic mismatch.
  - `2m_temperature` should be mostly neutral because no heat source is added.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because winds, surface residuals, Coriolis split,
    and momentum tendencies are unchanged.
  - Early pressure guardrails, because the dynamical pressure-gradient path
    remains dry.
- Possible regressions:
  - If passive humidity errors compensate geopotential output bias, condensate
    loading can worsen Z500.
  - If saturation estimates are poor on sigma levels, the partition can add
    noisy diagnostic structure even without latent heating.

## Risks

- Numerical stability:
  - Low for dynamics because the change is passive and diagnostic; moderate for
    output if saturation calculations are poorly guarded.
- Compute cost:
  - Low. The partition is local grid algebra plus existing tracer arrays.
- Data leakage:
  - None. The partition uses only forecast temperature, pressure, humidity, and
    fixed thermodynamic constants.
- Physical plausibility:
  - Moderate. Prognostic condensate and cloud fraction are standard in full
    NWP physics, but this is a deliberately minimal total-water partition with no
    precipitation or latent heating.
- Rollback complexity:
  - Low. Remove one internal tracer/filter, one diagnostic-plumbing branch, one
    factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_cloudpart`
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_cloudpart --workers 4`
  - Support requires primary-score delta at least `+0.002`, clean diagnostics,
    no early RMSE guardrail failure, and no variable-by-lead guardrail failure.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_cloudpart --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001`.
- Outcome that would falsify the hypothesis:
  - A clean neutral or negative iteration delta would show reversible condensate
    partitioning does not address the remaining benchmark error. Any Z500 or
    MSLP guardrail issue would show the cloud-loading diagnostic is noisier than
    the incumbent humidity-only output path.

## Citations

- Tiedtke, M. 1993. Representation of clouds in large-scale models. Monthly
  Weather Review, 121, 3040-3061.
  https://doi.org/10.1175/1520-0493(1993)121%3C3040:ROCILS%3E2.0.CO;2
- Wilson, D. R., Bushell, A. C., Kerr-Munslow, A. M., Price, J. D. and
  Morcrette, C. J. 2008. PC2: A prognostic cloud fraction and condensation
  scheme. I: Scheme description. Quarterly Journal of the Royal Meteorological
  Society, 134, 2093-2107. https://doi.org/10.1002/qj.333
- ECMWF OpenIFS physical-process documentation describes moist conserved
  variables and prognostic cloud variables in the IFS cloud scheme.
  https://confluence.ecmwf.int/display/OIFS/3.2%2BOpenIFS%3A%2BPhysical%2BProcesses
- Forbes, R. M., Tompkins, A. M. and Untch, A. 2011. A new prognostic bulk
  microphysics scheme for the IFS. ECMWF Technical Memorandum 649.
  https://www.ecmwf.int/sites/default/files/elibrary/2011/9441-new-prognostic-bulk-microphysics-scheme-ifs.pdf

## Researcher Notes

This is deliberately not a revival of `bounded-saturation-adjustment`: it adds no
latent heating, removes no water, and keeps total water reversible rather than
irreversibly condensing and warming the column. It is also not another active
humidity-dynamics proposal because moisture remains passive and does not enter
the momentum or pressure-gradient equations. It avoids the recent DSE and ocean
negative families by touching only an internal passive-water partition and the
existing geopotential diagnostic cloud-loading hook.

## Evaluator Notes

### 2026-06-24T18:51:46Z

Decision: move to `scrap`; rank 3 of 3 new proposals; ready now: no.

The literature supports prognostic cloud condensate in full NWP cloud schemes,
and source inspection confirms `get_geopotential_on_sigma` already accepts a
`clouds` argument that subtracts condensate loading from virtual temperature.
That makes the proposal technically feasible. The issue is local evidence and
scope, not scientific impossibility.

This is too close to the rejected saturation and humidity-diagnostic family for
another model-selection slot. `bounded-saturation-adjustment` already showed
that pointwise supersaturation handling can run cleanly yet regress primary
score by `-0.026391567842939834` and fail early `MSLP`, `Z500`, and wind
guardrails once latent heating is included. Removing the heating lowers the
dynamical risk, but it also leaves only an indirect cloud-loading change to
diagnostic geopotential. Other humidity-only or humidity-light histories are
weak: passive humidity positivity and DFI bypass were near-roundoff negative,
active moist virtual-temperature dynamics regressed strongly, and moist-static
energy HSL was effectively neutral.

The active staging queue already contains safer humidity mechanisms that are
better tied to known local evidence, especially passive-humidity transport and
virtual-temperature interpretation of the accepted analysis-HS offset. This
proposal would add a new internal tracer, saturation helper, partition filter,
and output plumbing without a scored cloud target, precipitation closure, cloud
fraction, or read-only evidence that supersaturated passive humidity is a
remaining `Z500`/`MSLP` bottleneck. Scrapping keeps the queue focused.
