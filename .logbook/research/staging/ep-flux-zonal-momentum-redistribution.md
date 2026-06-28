---
schema_version: 1
slug: ep-flux-zonal-momentum-redistribution
title: Redistribute Zonal-Mean Momentum with a Bounded EP-Flux Closure
status: staging
created_at: 2026-06-28T00:00:00Z
author_role: Researcher
target_model: dinosaur
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

## Hypothesis

The incumbent's accepted gains come from careful thermodynamic trajectory corrections, but medium-range wind, pressure, and height errors can still arise from under-resolved wave-mean-flow momentum exchange. A small Eliassen-Palm-flux-inspired zonal-mean momentum redistribution could improve jet placement and downstream pressure evolution while remaining decorrelated from recent `2m_temperature`, MSLP-offset, and vertical-advection failures.

## Mechanism

Add a side-by-side registered candidate, for example `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_epmom`, that enables a new `apply_ep_flux_zonal_momentum_redistribution` path on top of the incumbent configuration. The closure should only modify the zonal-mean rotational wind component, leaving thermodynamics, humidity, surface pressure, diagnostics, WTG relaxation, vertical-DSE increments, and final output conversions unchanged.

After each accepted dynamics step, reconstruct nodal horizontal wind and compute the zonal-mean zonal wind by sigma layer. Estimate a broad eddy-activity weight from resolved transient anomaly amplitude, such as zonal variance of vorticity or meridional wind in the free troposphere, with optional static-stability or latitude tapering. Apply a weak latitudinal flux convergence to the zonal-mean zonal wind:

- Only within a conservative free-tropospheric sigma band, such as approximately `0.2 <= sigma <= 0.8`.
- Tapered to zero near the equator, the poles, the surface layer, and the top layer.
- Formulated as a redistribution so that the area-weighted axial angular-momentum tendency is zero per affected layer, or at minimum zero globally after applying the increment.
- Capped per inner step, for example no more than `0.02 m s^-1` wind change before modal conversion.
- Projected back through the existing vorticity/divergence representation as a zonally symmetric rotational increment, with no added divergent wind.

The closure should be implemented as a small deterministic trajectory increment rather than a drag. It should move momentum meridionally where the resolved eddy-activity proxy is large, but preserve total angular momentum and avoid surface drag effects. The finite fallback should return the incumbent state if any diagnostic or modal projection produces non-finite values.

## Implementation Scope

- Add one boolean option and one factory in `src/dynamaxx/dycore/models/dinosaur/adapter.py`.
- Add a helper that builds a capped zonal-mean `u` increment, removes its angular-momentum-weighted mean, and projects it to the model's vorticity/divergence state.
- Register one side-by-side model key in `src/dynamaxx/dycore/registry.py`.
- Update exports if required by the existing dinosaur model module pattern.
- Add focused tests for zero correction on solid-body or uniform zonal flow, angular-momentum neutrality, cap enforcement, finite fallback, and registry availability.

## Expected Metric Movement

The main expected signal is modest improvement in medium-to-late `10m_wind_speed`, `geopotential`, and `mean_sea_level_pressure` through better jet latitude and waveguide evolution. `2m_temperature` should remain near-neutral because the closure does not touch near-surface thermodynamic diagnostics or boundary-layer temperature memory. A successful result should show broad non-failing diagnostics rather than a single-variable spike.

## Risks

The biggest risk is degrading realistic jet accelerations by imposing an overly diffusive or incorrectly signed momentum tendency. A second risk is angular-momentum drift if the spherical weighting is wrong. The proposal therefore requires a very small capped tendency, explicit angular-momentum neutrality, free-tropospheric-only application, and a side-by-side registry key so the incumbent remains untouched.

## Evaluation Plan

Run unchanged `fast` evaluation first, with diagnostic inspection for non-finite winds, pressure failures, and any sharp early `10m_wind_speed` degradation. If clean, run unchanged `iteration` with `--workers 4` and compare to cached incumbent score `-0.21299732605547173`. Only run unchanged `validation` if iteration shows a material positive delta and no sign of surface-wind-only overfitting. Do not change protocols, target variables, lead times, metrics, artifacts, or the single-trajectory forecast contract.

## Citations

- Eliassen, A. and E. Palm. 1961. "On the Transfer of Energy in Stationary Mountain Waves." Geofysiske Publikasjoner. Cited in Lindzen's wave-mean-flow review: https://link.springer.com/article/10.1007/BF02265242
- Andrews, D. G. and M. E. McIntyre. 1976. "Planetary Waves in Horizontal and Vertical Shear: The Generalized Eliassen-Palm Relation and the Mean Zonal Acceleration." Journal of the Atmospheric Sciences. https://journals.ametsoc.org/view/journals/atsc/33/11/1520-0469_1976_033_2031_pwihav_2_0_co_2.xml
- Edmon, H. J. Jr., B. J. Hoskins, and M. E. McIntyre. 1980. "Eliassen-Palm Cross Sections for the Troposphere." Journal of the Atmospheric Sciences. https://journals.ametsoc.org/view/journals/atsc/37/12/1520-0469_1980_037_2600_epcsft_2_0_co_2.xml
- NOAA Physical Sciences Laboratory EP-flux diagnostics page. https://psl.noaa.gov/data/epflux/
- NCAR Command Language EP-flux documentation. https://www.ncl.ucar.edu/Document/Functions/Contributed/epflux.shtml

## Researcher Notes

This is not a duplicate of nonorographic gravity-wave drag, surface stress, Leith viscosity, deformation-rate momentum damping, or angular-momentum fixers. Those ideas damp, diffuse, or restore momentum; this proposal conservatively redistributes only the zonal-mean rotational wind using an EP-flux-inspired wave-mean-flow proxy and explicitly removes the angular-momentum mean. It also does not overlap with the recent failed momentum-only semi-Lagrangian vertical advection because it introduces no vertical transport, no semi-Lagrangian departure search, and no new vertical Courant constraint. It is independent of the rejected MSLP offset and lower-tropospheric T2m diagnostic because it does not alter pressure reduction or near-surface temperature output.

## Evaluator Notes

### 2026-06-28T10:26:24Z

Decision: move to `staging`; rank 2 of 2 reviewed proposals.

The scientific family is credible, but this proposal is not ready for the next
implementation. The cited EP-flux literature and operational diagnostics support
EP-flux divergence as a wave-mean-flow diagnostic and as a source of zonal-mean
acceleration. NOAA/NCAR diagnostic documentation also emphasizes that EP-flux
components represent the relative importance of eddy heat and momentum fluxes,
and that divergence or acceleration is computed from those diagnosed fluxes.

The proposed closure does not yet specify a defensible approximation to those
flux terms. It uses a broad eddy-activity amplitude such as zonal variance of
vorticity or meridional wind, then applies an unspecified signed latitudinal
redistribution of zonal-mean `u`. That is too underdetermined for immediate
scoring: the sign, latitude structure, vertical coupling, angular-momentum
weighting, and projection back to vorticity/divergence could easily produce a
momentum damping or jet-shifting surrogate rather than an EP-flux closure.

Local evidence also argues for staging rather than ready. Recent
momentum-only semi-Lagrangian vertical advection failed iteration diagnostics
with nonfinite forecasts, and the research queue already contains several
staged momentum-closure ideas (`leith-nonlinear-eddy-viscosity`,
`deformation-rate-momentum-damping`, `nonorographic-gravity-wave-drag`,
`orographic-wave-drag-split`, and Richardson-gated momentum mixing). The
scrapped barotropic angular-momentum fixer is especially relevant negative
evidence: global or zonal-mean wind corrections need diagnostic proof that the
target conservation or wave-mean-flow error is actually material for the scored
variables.

Keep staged as a later candidate if a read-only diagnostic first shows coherent
EP-flux-divergence-like zonal acceleration errors, persistent jet-latitude drift,
or angular-momentum-neutral waveguide bias under the current incumbent. Before
promotion, the proposal should predeclare the proxy, sign convention, taper,
projection method, and exact angular-momentum invariant, and should include a
no-op test for symmetric eddy activity with no implied mean-flow acceleration.
