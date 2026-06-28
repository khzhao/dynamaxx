---
schema_version: 1
slug: eady-limited-baroclinic-heat-flux
title: Add an Eady-Limited Baroclinic Heat-Flux Closure
status: ready
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

The incumbent `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m` has benefited from trajectory-level thermodynamic corrections, but recent direct `2m_temperature` output blends and persistent MSLP offsets were either harmful or neutral. A more physical path is to address a likely missing midlatitude process inside the rollout: unresolved baroclinic eddy heat transport. A weak, capped heat-flux closure keyed to local Eady growth should reduce broad free-tropospheric thermal-gradient errors without changing fixed evaluation protocols, target variables, lead times, or the single-trajectory forecast contract.

## Mechanism

Add a side-by-side registered candidate, for example `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_eady_hfx`, that enables a new `apply_eady_limited_baroclinic_heat_flux` path on top of the incumbent configuration. The closure should operate only on the prognostic thermodynamic state, preferably dry static energy or potential temperature anomaly, after the existing mass-DSE HSL and accepted WTG/vertical-DSE increments have been formed.

At each inner step, diagnose a broad-scale Eady-growth proxy from free-tropospheric static stability, Coriolis magnitude, and vertical shear. Use that proxy to define a small downgradient horizontal heat-flux tendency on low-to-medium spherical-harmonic modes in the extratropics. The update should be:

- Mass and dry-static-energy neutral in the layer/global mean by removing the area-weighted mean correction from each affected sigma layer.
- Limited to a conservative free-tropospheric sigma band, such as approximately `0.25 <= sigma <= 0.85`, leaving the boundary layer and model top untouched.
- Smoothly tapered away from the equator where the Eady proxy is ill-conditioned.
- Capped per inner step, for example no more than `0.02` to `0.05 K` equivalent thermal change, with a finite-value fallback to the unmodified incumbent state.
- Applied to the trajectory only, not as a final diagnostic adjustment to `2m_temperature`, MSLP, geopotential, or winds.

Implementation can reuse the existing nodal/modal conversion and latitude weights already needed by the dinosaur adapter. The simplest implementation is a post-tendency thermal filter: reconstruct the next-step thermodynamic field, compute the capped closure increment in nodal space, remove the area-weighted layer mean, convert the increment back to modal representation, and add it before the next model step. The candidate should preserve the incumbent model as a separate registry key and should include tests for registry availability, zero correction under horizontally uniform temperature, mean-neutrality, finite fallback, and cap enforcement.

## Implementation Scope

- Add one boolean option and one factory in `src/dynamaxx/dycore/models/dinosaur/adapter.py`.
- Add the closure helper either in the adapter or in `primitive_equations.py`, depending on where existing spectral helper access is cleanest.
- Register one new side-by-side model key in `src/dynamaxx/dycore/registry.py`.
- Update the dinosaur package exports if local patterns require explicit exports.
- Add focused unit tests for the new closure invariants and registry entry.

## Expected Metric Movement

Expected improvement is most plausible in medium-to-late `geopotential`, `mean_sea_level_pressure`, and possibly `2m_temperature` through corrected thermal-gradient evolution rather than through final-output patching. `10m_wind_speed` should be near-neutral unless better storm-track placement changes surface gradients. The closure should be rejected quickly if `fast` shows non-finite behavior, early explosive thermal drift, or broad degradation of non-temperature variables.

## Risks

The main risk is double-counting already resolved baroclinic eddies, which could over-diffuse storm tracks and degrade `geopotential`. The second risk is numerical noise from shear/static-stability diagnostics near the model top, the equator, or weakly stratified columns. Those risks are addressed by broad-mode filtering, sigma tapers, Eady-proxy floors, small per-step caps, and a finite fallback to the incumbent update.

## Evaluation Plan

Run the normal `fast` protocol first and compare against the incumbent commit `3992244f20b2a938fdd96f8904f3749f5505670d`. If diagnostics are clean and the score is not a clear regression, run the unchanged `iteration` protocol with `--workers 4`. Promote to unchanged `validation` only if the iteration result is materially positive and does not show isolated improvement from a single fragile variable. Keep cached incumbent artifacts unchanged and compare against the cached incumbent iteration score `-0.21299732605547173` and validation score `-0.21274255459898536`.

## Citations

- Eady, E. T. 1949. "Long Waves and Cyclone Waves." Tellus. https://onlinelibrary.wiley.com/doi/10.1111/j.2153-3490.1949.tb01265.x
- Stone, P. H. 1978. "Baroclinic Adjustment." Journal of the Atmospheric Sciences. NASA NTRS summary and DOI record: https://ntrs.nasa.gov/citations/19780052267
- Held, I. M. and V. D. Larichev. 1996. "A Scaling Theory for Horizontally Homogeneous, Baroclinically Unstable Flow on a Beta Plane." Journal of the Atmospheric Sciences. https://journals.ametsoc.org/view/journals/atsc/53/7/1520-0469_1996_053_0946_astfhh_2_0_co_2.xml
- NCAR Command Language documentation for the maximum Eady growth-rate diagnostic. https://www.ncl.ucar.edu/Document/Functions/Contributed/eady_growth_rate.shtml

## Researcher Notes

This is not a duplicate of the rejected lower-tropospheric airmass `2m_temperature` diagnostic because it does not postprocess `2m_temperature` or blend with near-surface air mass. It is not the neutral persistent MSLP offset because it does not touch MSLP reduction. It avoids the failed momentum-only semi-Lagrangian vertical-advection family entirely. It also differs from active diffusion, Leith, deformation-damping, and QG-frontogenesis ideas: the proposed increment is a bounded thermodynamic heat-flux closure tied to Eady baroclinicity and constrained by layer/global thermal neutrality, not a momentum viscosity, spectral smoother, pressure-gradient correction, WTG retune, or vertical transport scheme.

## Evaluator Notes

### 2026-06-28T10:26:24Z

Decision: move to `ready`; rank 1 of 2 reviewed proposals.

Recommended candidate model name:
`dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_eady_hfx`.

The proposal is the strongest next experiment because it introduces a bounded
trajectory-level thermodynamic closure through an already familiar scalar
step-filter pattern. It is side-by-side with the current incumbent, leaves
fixed protocols and cached incumbent artifacts untouched, and targets multiple
scored channels (`geopotential_500`, `mean_sea_level_pressure`, and possibly
`2m_temperature`) without another final-output diagnostic or MSLP offset.

Literature support is adequate for a single implementation attempt. NCAR's Eady
growth-rate diagnostic documents the standard dependence on static stability,
Coriolis magnitude, and vertical shear, and explicitly treats it as a
midlatitude baroclinic-instability measure while cautioning against equatorial
use. Stone's baroclinic-adjustment record supports enhanced eddy heat flux as a
negative feedback on excessive meridional temperature gradients. Those sources
support the proposal's extratropical taper, Eady-proxy gating, small caps, and
mean-neutral heat increment. They do not prove the closure will improve this
incumbent, so the implementation should keep the amplitude conservative and
predeclared.

Local history is cautionary but not disqualifying. The rejected
baroclinic-theta-variance guard was stable and essentially neutral, and the
baroclinic-mode vertical-DSE spinup degraded early `2m_temperature`; however,
this proposal is neither variance preservation nor an early vertical-DSE timing
change. It instead adds a small low-to-medium-mode free-tropospheric heat-flux
tendency after the accepted HSL/WTG/vertical-DSE path. The existing adapter has
rollout-only thermal filters with latitude/sigma masks, low-mode transforms,
caps, area-mean removal, and finite fallback, keeping the implementation surface
practical under `--workers 4`.

Implementation guardrails: keep the closure out of final diagnostics, preserve
the incumbent registry key, exclude the equator and boundary layer, remove
layer means after clipping, use an exact finite fallback to the incumbent next
state, and reject quickly if `fast` shows nonfinite fields or broad Z500/MSLP
oversmoothing.
