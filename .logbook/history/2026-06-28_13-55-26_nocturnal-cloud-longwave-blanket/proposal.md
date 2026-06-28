---
schema_version: 1
slug: nocturnal-cloud-longwave-blanket
title: Nocturnal Low-Cloud Longwave Blanket Forcing
status: ready
created_at: 2026-06-28T13:50:38Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/radiation.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Nocturnal Low-Cloud Longwave Blanket Forcing

## Hypothesis

The accepted incumbent improved `2m_temperature` with broad land/ocean memory
and a bounded Richardson 2 m diagnostic, but its cached iteration metrics still
show a growing cold `2m_temperature` bias after the first few days. A missing
low-cloud downward-longwave effect is a plausible lower-boundary physics gap:
clouds reduce nocturnal radiative cooling of the surface layer, especially in
humid and stable boundary layers. A bounded nighttime-only longwave-blanket
tendency can warm the lowest model layer where cloud likelihood is high without
using a final-output T2m blend or perturbing the accepted vertical-DSE, WTG, or
MSLP diagnostic paths.

## Mechanism

Add one side-by-side candidate, for example `dino_ri2m_cloud_lw`, derived from
the current incumbent.

For this candidate only:

- keep the incumbent HSL mass-DSE transport, tropical WTG relaxation,
  pressure-ramped vertical-DSE increment, low-mode T2m memory, Richardson 2 m
  diagnostic, weak-HS forcing, ocean heat flux, DFI, and output contract
  unchanged;
- use existing forecast time, longitude, latitude, and `radiation.py` utilities
  to diagnose local solar angle and apply the new tendency only when normalized
  local shortwave flux is near zero;
- derive a bounded low-cloud proxy from forecast-state lower-tropospheric
  relative humidity and a stable or inversion-like lowest-column temperature
  structure; if humidity is absent or invalid, the candidate is an exact no-op;
- apply a positive, capped temperature tendency only to the lowest one or two
  sigma layers, proportional to cloud proxy and nighttime weight, with a fixed
  cap such as `0.20 K day^-1`;
- subtract no global mean and do not cool daytime columns in the first test,
  because the incumbent's local evidence is cold T2m drift rather than warm
  drift;
- leave vorticity, divergence, `log_surface_pressure`, humidity tracer
  transport, pressure-level interpolation, MSLP reduction, and final T2m
  diagnostic formulas unchanged;
- fall back exactly to the incumbent if the cloud proxy, nighttime weight,
  layer pressure, tendency, or post-step state is nonfinite.

This is a lower-boundary radiative forcing, not a final-output screen
temperature correction and not a humidity pressure-gradient mechanism.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/radiation.py` only if a small reusable
    nighttime-weight helper is needed
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add exactly one short side-by-side model key, such as
    `dino_ri2m_cloud_lw`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, metrics, and
    fixed evaluation protocols remain unchanged.
- Tests to update:
  - Verify daytime and missing-humidity cases reproduce the incumbent exactly.
  - Verify the cloud proxy is bounded, finite, and increases with lower-level
    relative humidity under a stable lower-column profile.
  - Verify the tendency changes only `temperature_variation` in the lowest
    layers and obeys the fixed per-day cap.
  - Verify nonfinite diagnostics fall back to the incumbent path.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` from days 3-15 if missing nocturnal cloud greenhouse effect
    contributes to the incumbent's cold lower-boundary drift.
  - Small secondary `geopotential_500` improvement if lower-column thickness
    bias is reduced without mass-field shocks.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because no momentum tendency or 10 m wind
    diagnostic changes.
  - `mean_sea_level_pressure`, because the tendency is low-level, capped, and
    does not alter surface-pressure tendency or MSLP reduction formulas.
- Possible regressions:
  - If the cold T2m error is dominated by advection or land/ocean residual
    decay rather than radiative cooling, the added warming will be neutral or
    wrong-signed.
  - A crude cloud proxy can warm humid advective regimes where cloud radiative
    forcing should instead be weak.

## Risks

- Numerical stability:
  - Low to moderate. The forcing is positive and capped, but it affects the
    thermodynamic state every nighttime step.
- Compute cost:
  - Low. It adds local humidity, stability, and solar-angle algebra; no extra
    forecast trajectories or evaluation workers are required.
- Data leakage:
  - None. It uses only forecast state, initialization time, grid geometry, and
    fixed constants.
- Physical plausibility:
  - Moderate. Downward longwave cloud forcing is real, but this is a minimal
    diagnostic cloud proxy rather than a full cloud-radiation scheme.
- Rollback complexity:
  - Low. Remove one selector/helper, one factory/export, one registry entry, and
    focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_ri2m_cloud_lw`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_ri2m_cloud_lw --workers 4`.
  - Support requires primary-score delta at least `+0.002` against cached
    `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`, clean diagnostics, no early
    day-1-through-day-5 RMSE guardrail failure, and no variable-lead guardrail
    failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_ri2m_cloud_lw --workers 4`
    only after iteration promotion.
  - Require validation primary-score delta at least `+0.001` with clean
    guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show that nocturnal
    low-cloud longwave warming is not a material remaining score source. Any
    early T2m, MSLP, or Z500 guardrail failure would show the proxy is too
    intrusive.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/radiation.py` already
  provides orbital-time and top-of-atmosphere solar-radiation utilities that can
  gate a nighttime-only tendency.
- Dynamaxx history:
  `.logbook/history/2026-06-27_23-08-54_bulk-richardson-2m-temperature-diagnostic/decision.md`
  accepted the current RI2m incumbent with clean diagnostics and a validation
  delta of `+0.0033221535666909108`.
- Dynamaxx history:
  `.logbook/history/2026-06-28_02-44-14_lower-tropospheric-airmass-t2m-diagnostic/decision.md`
  rejected a final-output T2m air-mass blend with a `-0.03976967819222538`
  iteration delta, so this proposal changes lower-boundary physics instead of
  blending final T2m output.
- Slingo, J. M. 1987. "The development and verification of a cloud prediction
  scheme for the ECMWF model." Quarterly Journal of the Royal Meteorological
  Society. https://doi.org/10.1002/qj.49711347710
- ECMWF Technical Memorandum, "The parametrization of cloud cover", summarizes
  relative-humidity cloud-cover parameterizations and cites Slingo-style cloud
  schemes. https://www.ecmwf.int/sites/default/files/elibrary/2005/16958-parametrization-cloud-cover.pdf
- Costa, S. M. S. et al. 2015. "Modeling atmospheric longwave radiation at the
  surface during overcast skies." Journal of Geophysical Research: Atmospheres.
  https://doi.org/10.1002/2014JD022310

## Researcher Notes

This is not a duplicate of the staged `clear-sky-longwave-relaxation`, which is
a dry temperature-anomaly damping proxy with no humidity or clouds. It is also
not the scrapped `humidity-weighted-radiative-temperature-relaxation`, which
coupled all-time temperature tendencies to humidity anomalies with arbitrary
sign and layer-mean removal. This proposal is local-time gated, low-cloud
gated, one-signed nocturnal warming aimed at the accepted incumbent's cold T2m
drift.

It explicitly avoids recent negative evidence: it does not retune the
Eady-limited baroclinic heat-flux filter, does not use persistent MSLP ratios,
does not blend final-output T2m, does not change vertical transport, and does
not touch the staged EP-flux momentum idea.

## Evaluator Notes

### 2026-06-28T13:53:42Z

Decision: move to `ready`; ranked 1 of 2 fresh proposals. Recommended next
candidate model name: `dino_ri2m_cloud_lw`.

The local score artifacts support the proposal's premise strongly enough for one
implementation slot: the current incumbent has a growing negative
`2m_temperature` bias in the cached iteration CSV, from about `-0.019 K` at
72 h to about `-0.465 K` at 360 h. That is not proof that missing nocturnal
cloud longwave forcing is the cause, but it is a concrete target for a
low-level, bounded warming process. This is preferable to another final-output
T2m blend after the lower-tropospheric air-mass diagnostic regressed iteration
by `-0.03976967819222538`.

Literature checks support the broad physical ingredients. Slingo 1987 supports
diagnosing cloud fraction from large-scale model variables including humidity;
Costa et al. 2015 and broader cloud-radiation literature support the premise
that overcast and low-cloud conditions increase downward longwave radiation at
the surface, with cloud-base height and water-vapor profiles controlling the
effect. Those sources do not validate this exact passive-humidity, stability,
and nighttime proxy, so the implementation must stay tightly bounded and should
avoid coefficient sweeps.

Promote this over the convective-momentum proposal because the implementation
surface is smaller, it leaves momentum, pressure reduction, vertical transport,
and final-output diagnostics unchanged, and it addresses a measured incumbent
error channel. Guardrails for implementation: keep missing/invalid humidity as
an exact no-op; restrict the tendency to the lowest one or two layers; preserve
the fixed evaluation protocols and cached incumbent comparison; require unit
tests for daytime no-op, tendency cap, finite fallback, and unchanged
non-temperature fields. The front-matter `target_model` was normalized to the
protocol schema value `dinosaur`; the body still correctly states that the
candidate should derive from the current incumbent configuration.
