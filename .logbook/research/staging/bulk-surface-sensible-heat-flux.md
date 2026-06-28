---
schema_version: 1
slug: bulk-surface-sensible-heat-flux
title: Flow-Dependent Bulk Surface Sensible Heat Flux Lower Boundary
status: staging
created_at: 2026-06-22T02:00:27Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/held_suarez.py
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

# Flow-Dependent Bulk Surface Sensible Heat Flux Lower Boundary

## Hypothesis

The model's only near-surface thermodynamic process is the Held-Suarez Newtonian
relaxation toward an analytic equilibrium temperature `Teq` at a fixed rate
(`ks = 1/4 day` at the surface), now offset toward analysis. That relaxation is
flow-independent and pulls the air toward an idealized profile, not toward the
actual surface it sits over. Physically, near-surface air temperature is set by
the **turbulent sensible heat exchange with the underlying surface**, whose
strength scales with surface wind speed and stability. The real lower boundary
is close to persistent on forecast timescales -- ocean skin temperature barely
moves over 1-15 days, and land has a slowly varying mean. Replacing the crude
fixed-rate near-surface relaxation with a **flow-dependent bulk sensible heat
flux toward a persisted observed surface temperature** should let the lowest
layers track the real surface (especially over ocean, where the persisted
surface anchor is excellent), reducing the dominant `2m_temperature` error
through the prognostic state rather than an output diagnostic.

## Mechanism

Register a side-by-side candidate named `..._landsea_surface_bulk_shf`. Preserve
every incumbent setting; add one new explicit forcing term applied only to the
lowest sigma layer(s).

- At initialization, capture a persisted surface anchor temperature `T_sfc` from
  the initial state (the initial lowest-model-layer temperature, or initial
  `2m_temperature` if exposed as input), held fixed through the forecast. This
  is the slowly varying surface the air exchanges heat with.
- Each step, add a bulk sensible heat flux tendency to the lowest-layer
  temperature: `dT/dt += C_h * |V_1| * (T_sfc - T_1) / depth`, where `|V_1|` is
  the lowest-layer wind speed (flow dependence), `C_h` a bounded transfer
  coefficient, and the effect confined to the lowest one or two layers with a
  bounded magnitude.
- Optionally make `C_h` weakly stability-dependent (smaller under stable
  stratification) reusing the existing bulk-Richardson diagnostic; keep it
  bounded with a floor and ceiling.
- This **augments**, rather than removes, the incumbent HS relaxation, so the
  candidate is a bounded additive forcing; set the flux coefficient small enough
  that the surface relaxation remains the dominant control and fall back to the
  incumbent if the flux is nonfinite.
- Do not change winds, pressure, geopotential, the spectral dynamics, or the
  output diagnostics; the flux acts on the prognostic temperature only and its
  effect reaches `2m_temperature` through the (unchanged) diagnostic mapping.
- Apply identically in DFI and positive-time rollout.

This is a new **physical process** (surface turbulent heat exchange), distinct
from: the analytic HS Newtonian relaxation (fixed rate toward `Teq`, no surface
coupling, no flow dependence); the accepted `analysis-offset-held-suarez-equilibrium`
and `land-sea-contrast-surface-temperature` (which shift the equilibrium / blend
the output diagnostic); the scrapped `near-surface-stability-heat-mixing` (interior
air-column vertical diffusion, no external surface source); and the staged
boundary-layer drag ideas (`exponential-boundary-layer-rayleigh-drag`,
`geostrophic-sparing-boundary-layer-drag`), which act on momentum, not heat.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/held_suarez.py` (or a small companion
    forcing) for the bulk-flux explicit tendency;
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py` to capture and thread the
    persisted surface anchor and compose the forcing;
  - `__init__.py`, `registry.py`, and tests under `tests/dycore/`.
- Registry changes: add only the side-by-side candidate named above.
- API changes: none to `DycoreModel.forecast`, variables, leads, splits, metrics,
  or gates; the persisted surface anchor is derived from the existing initial
  state.
- Tests to update:
  - flux drives the lowest-layer temperature toward `T_sfc` and vanishes when
    `T_1 == T_sfc`;
  - flux scales with wind speed and respects its bounds and stability factor;
  - upper layers and all non-temperature fields are unchanged;
  - nonfinite fallback reproduces the incumbent;
  - registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements: `2m_temperature` at days 1-10, strongest over ocean
  (persisted surface anchor is near-exact) and complementary to the accepted
  land-sea correction over land.
- Expected neutral metrics: `geopotential_500`, `mean_sea_level_pressure`,
  `10m_u_component_of_wind` (momentum untouched; mass field responds only weakly
  through the small lowest-layer thermal change).
- Possible regressions: over land in strong diurnal regimes a persisted surface
  anchor can be biased; the bounded coefficient and retained HS relaxation limit
  this. Excessive `C_h` could over-couple and add lowest-layer noise.

## Risks

- Numerical stability: moderate. A wind-dependent relaxation is stiff under high
  winds; the bounded coefficient, lowest-layer confinement, and explicit-with-bound
  treatment (or reuse of the forcing partition) keep it controlled; finite
  fallback guards failures.
- Compute cost: low. One elementwise lowest-layer tendency per step; no change to
  resolution, leads, output volume, or workers.
- Data leakage: none. Uses the model's own initial state and forecast winds with
  fixed coefficients; no verification-time data.
- Physical plausibility: high. Bulk-aerodynamic surface sensible heat flux is the
  standard surface-layer heat-exchange closure.
- Rollback complexity: low. Remove one forcing term, the anchor capture, one
  factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate: `uv run pytest`; `uv run dynamaxx-eval fast --model ..._bulk_shf`;
  finite forecasts, zero diagnostic issues.
- Iteration gate: `uv run dynamaxx-eval iteration --model ..._bulk_shf --workers 4`;
  support is primary-score delta at least `+0.002`, clean diagnostics, no
  early-lead or variable-by-lead RMSE guardrail failure.
- Validation gate: `uv run dynamaxx-eval validation --model ..._bulk_shf --workers 4`
  only after iteration promotion; require validation delta at least `+0.001`.
- Falsification: a clean near-zero or negative iteration delta would show the HS
  relaxation rate, not the lack of surface coupling, governs near-surface
  temperature error, or that the persisted surface anchor is not better than the
  analysis-offset equilibrium the air already relaxes toward.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/held_suarez.py`
    `explicit_terms` applies only Newtonian thermal relaxation and Rayleigh drag;
    no surface heat flux exists.
  - Dynamaxx history:
    `.logbook/history/2026-06-20_10-50-51_analysis-offset-held-suarez-equilibrium`
    and `.logbook/history/2026-06-21_23-32-41_land-sea-contrast-surface-temperature`
    improved `2m_temperature` by shifting/blending the equilibrium and diagnostic;
    this attacks the same error through a prognostic surface flux instead.
  - Monin, A. S. and Obukhov, A. M. 1954. Basic laws of turbulent mixing in the
    surface layer of the atmosphere. Tr. Geofiz. Inst. Akad. Nauk SSSR.
  - Louis, J. F. 1979. A parametric model of vertical eddy fluxes in the
    atmosphere. Boundary-Layer Meteorology.
    https://doi.org/10.1007/BF00117978
  - Garratt, J. R. 1992. The Atmospheric Boundary Layer. Cambridge University
    Press (bulk aerodynamic surface flux formulation).

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-22. Chosen to
be orthogonal to the recent output-diagnostic wins and to the staged dynamics
ideas: it adds a near-surface physical *process* the dycore lacks entirely, per
RESEARCHER.md's preference for changes to physical processes over hyperparameter
tuning. Negative-evidence check: the scrapped `near-surface-stability-heat-mixing`
was rejected on implementation cost, not physics; this proposal is deliberately
lighter (one bounded lowest-layer flux term, no implicit column solve or
conservation machinery) to stay within the low-surface envelope the Evaluator has
favored. Paired with `exponential-integrator-newtonian-relaxation`, which is a
numerical (not process) change, to give the loop two decorrelated levers.

## Evaluator Notes

### 2026-06-22T03:17:44Z

Decision: move to `staging`, ranked behind
`exponential-integrator-newtonian-relaxation`.

The physical premise is credible but not the best next implementation target.
Bulk-aerodynamic and stability-aware lower-boundary heat exchange is supported
by standard surface-layer literature: Louis 1979 presents stability-dependent
vertical eddy fluxes of heat, momentum, and water vapor in forecast models
(`https://doi.org/10.1007/BF00117978`), and Monin-Obukhov-style surface-layer
closures are an established basis for sensible-heat exchange. The proposal is
also distinct from the recent accepted `land-sea-contrast-surface-temperature`
experiment because it changes the prognostic lower-layer thermal state rather
than only the output residual diagnostic.

Keep it out of `ready` for this pass. The current incumbent just gained a large
validation improvement from a bounded land-sea `2m_temperature` diagnostic, and
the most recent rejected experiment showed that nearby residual-memory
extensions can be clean but score-negative. This proposal introduces a new
forecast-time heat source tied to a persisted initial "surface" anchor. In the
available model state that anchor is likely an initial lowest-layer or screen
temperature proxy rather than a true skin/surface temperature, so the mechanism
risks becoming a prognostic residual-memory/nudging variant with extra
hydrostatic and MSLP coupling. It is lighter than the scrapped
`near-surface-stability-heat-mixing` proposal, but still spends more mass-field
guardrail margin than a local numerical treatment of the already accepted
Held-Suarez forcing.

Stage for later if the exact-relaxation candidate fails cleanly or if diagnostics
show the remaining `2m_temperature` deficit requires a prognostic lower-boundary
thermal process. A future promotion should pin down the anchor source, bounds,
and coefficient before implementation, and should not change forecast contracts
or fixed evaluation protocols.
