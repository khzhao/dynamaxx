---
schema_version: 1
slug: one-step-anticipated-pv-flux
title: One-Step Anticipated Potential-Vorticity Flux
status: ready
created_at: 2026-07-12T02:38:19Z
author_role: Researcher
target_model: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori_rskin
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
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

# One-Step Anticipated Potential-Vorticity Flux

## Hypothesis

The incumbent retains fixed horizontal diffusion, while recent rotational
follow-ups either filtered a product or capped a diagnostic after enstrophy had
already accumulated. Absolute-vorticity product dealiasing was stable but only
gained `+0.00017069712459116815`, and the Rhines-band barotropic enstrophy cap
was effectively neutral at `+1.431142083452297e-07`. Those results do not test
the anticipated potential-vorticity method (APVM): a vector-invariant momentum
closure that evaluates the rotational flux with a one-step anticipated PV and
is constructed to dissipate potential enstrophy without doing nodal kinetic-
energy work.

Using a sigma-layer mass proxy gives the current primitive-equation state a
natural multilayer APVM form. Selectively removing grid-scale PV variance at
the flux, rather than damping vorticity after the step, may preserve resolved
cyclone amplitude while reducing medium- and late-lead phase contamination in
wind, pressure, and height.

## Mechanism

Register one side-by-side descendant, suggested key `dino_rskin_apv`, and add
one positive-time-only option to the dry sigma primitive equation.

For each sigma layer and explicit tendency evaluation:

- diagnose nodal layer mass `m_k = p_s * delta_sigma_k` from forecast surface
  pressure and the fixed sigma thickness;
- diagnose a shallow-water layer-PV proxy
  `q_k = (zeta_k + f) / m_k`, using the physical Coriolis parameter even though
  the incumbent applies the base Coriolis acceleration through its exact
  symmetric split;
- use the existing nodal wind and spherical gradient operators to form the
  horizontal material derivative `u_k dot grad(q_k)`;
- set the anticipated value to
  `q_star_k = q_k - dt * u_k dot grad(q_k)`, with `dt` exactly the incumbent
  `900 s` inner step;
- add only the APVM correction
  `m_k * (q_star_k - q_k) * k_cross_u_k` to the existing vector-invariant
  rotational momentum flux before the existing curl and divergence operators;
- retain the incumbent final tendency clipping and every vertical-advection,
  pressure-gradient, kinetic-energy, thermodynamic, continuity, tracer, and
  post-step-filter path.

The added nodal acceleration is perpendicular to the same-layer nodal wind, so
its pointwise kinetic-energy work is zero before spectral transformation. The
closure can still dissipate layer-PV variance through the anticipated flux.
Modal truncation and the incumbent filters mean this is a work-neutral closure,
not a claim of exact full-model energy conservation.

The experiment is frozen as follows: one-step anticipation only; no free APVM
coefficient, scale-dependent alpha, spectral cutoff, latitude or terrain mask,
PV-gradient threshold, amplitude cap, theta compensation, or post-score
variant. It is disabled during DFI. Any nonpositive mass, invalid shape, or
nonfinite PV, gradient, flux, or transformed tendency selects the exact
incumbent tendency for that evaluation.

The accepted zero-mean radiative land-skin ramp, cap, absorbed fraction,
emissivity, heat capacity, mask, observer, initialization, and private carry
are unchanged. No `vertical_velocity` channel is read and no omega tendency,
window, sign, interpolation, envelope, ordering, or amplitude is introduced.

## Implementation Scope

- Expected files:
  - `primitive_equations.py` for a default-false APVM option, the layer-mass PV
    diagnostic, and the additive vector-invariant flux correction.
  - `adapter.py` for positive-time equation routing, the physical Coriolis
    field, and one incumbent-derived factory.
  - Dinosaur exports, registry, and focused tests.
- Registry changes:
  - Add exactly one side-by-side key, suggested `dino_rskin_apv`.
- API changes:
  - None. Forecast inputs, returned variables, deterministic trajectory count,
    lead schedule, target variables, and metric protocol remain unchanged.
- Tests to update:
  - Selector-off and DFI paths are exactly incumbent.
  - Constant layer PV and zero wind produce an exact zero correction.
  - The nodal dot product of wind and APVM acceleration is zero to numerical
    tolerance for a finite synthetic state.
  - A resolved PV gradient produces the expected one-step anticipation sign,
    while surface pressure and sigma thickness enter the PV denominator.
  - Vorticity and divergence receive only the curl/divergence of the additive
    flux; temperature, log pressure, tracers, and private land-skin carry are
    not edited directly.
  - Nonpositive mass and all nonfinite diagnostics fall back to the exact
    incumbent tendency.
  - Factory, registry, dependency, JIT, and finite smoke tests preserve every
    incumbent option except the APVM selector and name.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` mainly at days 4-15 if
    unresolved PV variance is contaminating synoptic phase and cyclone
    steering.
  - `10m_u_component_of_wind` at days 3-15 through the coupled rotational and
    pressure-gradient trajectory, without changing its Richardson observer.
  - A plausible primary-score movement is `+0.002` to `+0.008` if the
    rotational cascade is a material remaining error source.
- Expected neutral metrics:
  - Day-1 fields and `2m_temperature` should remain close to incumbent because
    DFI, thermodynamics, surface exchange, and all screen observers are frozen.
- Possible regressions:
  - A one-step PV predictor may overdissipate developing fronts or interact
    poorly with existing horizontal diffusion.
  - The sigma-layer shallow-water PV proxy omits full Ertel-PV tilting and
    diabatic source terms; this can perturb useful baroclinic growth.

## Risks

- Numerical stability:
  - Moderate. APVM is dissipative in its intended invariant, but it changes
    both rotational and divergent momentum tendencies at every positive-time
    explicit stage. Exact finite fallback is required.
- Compute cost:
  - Moderate. It adds PV gradients and nodal products at each explicit stage,
    but no trajectory, grid, output, or evaluation expansion. This fits four
    L4 workers, 48 CPUs, and the reported memory and disk envelope.
- Data leakage:
  - None. It uses only the current forecast state, fixed sigma geometry, the
    physical Coriolis field, and the accepted inner step.
- Physical plausibility:
  - Moderate to high. APVM is established for vector-invariant geophysical
    flow, while the layerwise sigma-mass proxy is a reduced multilayer
    application rather than full three-dimensional Ertel PV.
- Rollback complexity:
  - Low to moderate. Remove one equation option/helper, one adapter route and
    factory, one export/registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_rskin_apv`.
  - Require finite forecasts, zero diagnostic issues, unchanged output schema,
    and no early sign of pressure/wind instability.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_rskin_apv --workers 4`.
  - Compare with the valid cached incumbent at
    `-0.07908852007250675`; require delta at least `+0.002`, clean diagnostics,
    and both fixed RMSE guardrails.
- Validation gate:
  - Run exactly once only after iteration promotion:
    `uv run dynamaxx-eval validation --model dino_rskin_apv --workers 4`.
  - Compare with incumbent `-0.07929026517101266`; require delta at least
    `+0.001` with the same fixed guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold iteration result, any coherent medium/late Z500,
    MSLP, or U10 regression, or an early balance guardrail failure shows that
    APVM does not improve the current rotational cascade. Scrap without
    changing the anticipation interval, adding masks/caps, or trying the
    scale-invariant-alpha family.

## Citations

- Sadourny, R. and Basdevant, C. 1985. Parameterization of subgrid scale
  barotropic and baroclinic eddies in quasi-geostrophic models: anticipated
  potential vorticity method. *Journal of the Atmospheric Sciences* 42,
  1353-1363.
  https://doi.org/10.1175/1520-0469(1985)042%3C1353:POSSBA%3E2.0.CO;2
- Chen, Q., Gunzburger, M., and Ringler, T. 2011. A scale-invariant
  formulation of the anticipated potential vorticity method. *Monthly Weather
  Review* 139, 2614-2629. https://doi.org/10.1175/MWR-D-10-05004.1
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP
  and climate models. *Journal of Computational Physics* 227, 3715-3730.
  https://doi.org/10.1016/j.jcp.2006.08.016
- Local source: `PrimitiveEquationsSigma.curl_and_div_tendencies` in
  `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` constructs the
  incumbent vector-invariant absolute-vorticity flux.
- Local negative evidence:
  `.logbook/history/2026-06-20_05-39-53_absolute-vorticity-flux-dealiasing/decision.md`
  and
  `.logbook/history/2026-07-07_03-46-45_rhines-band-barotropic-enstrophy-cap/decision.md`.

## Researcher Notes

Targeted searches found no prior `APVM`, `anticipated potential vorticity`, or
`upwinded potential vorticity` proposal or implementation. This is not the
scrapped `material-pv-residual-balance`: it does not diagnose a post-step
residual, edit theta, smooth low modes, or introduce masks and thresholds. It
is not staged `absolute-vorticity-hsl-momentum`: it performs no departure-point
remap and does not replace the incumbent rotational tendency. It is not an
Arakawa Jacobian, Leith viscosity, vorticity filter, product dealiaser, or
barotropic enstrophy cap. Its novel operation is the standard one-step
anticipated layer-PV value inside an additive, nodally work-neutral
vector-invariant flux.

## Evaluator Notes

### 2026-07-12T02:48:50Z

Decision: move to `ready`; ranked #1 and the only ready proposal in this
triage.

The literature supports the core mechanism, with an important scope limit.
Sadourny and Basdevant establish the anticipated-PV construction as formally
energy conserving and potential-enstrophy dissipating in a two-layer
quasi-geostrophic model. Chen, Gunzburger, and Ringler establish the analogous
work-neutral APVM correction in a vector-invariant, PV-conserving one-layer
shallow-water discretization. Those papers do not establish conservation for
this repository's vertically exchanging sigma layers or for its truncated
pseudo-spectral products. The experiment is ready only as a reduced
shallow-water-like layer closure; it must not be described as conserving full
Ertel PV or full-model energy.

The proposed dimensions and sign are consistent. With layer pressure mass
`m = p_s * delta_sigma` (the constant `1 / g` needed for mass per area cancels
from `m * delta_q`), `q = (zeta + f) / m` has inverse pressure-time units,
`dt * u dot grad(q)` has the same units, and
`m * (q_star - q) * k_cross_u` is an acceleration. For the idealized
shallow-water budget, `q_star - q = -dt * u dot grad(q)` gives a negative
potential-enstrophy contribution. In the incumbent sign convention, the
resulting `delta_eta = m * (q_star - q)` must be added to the existing
absolute-vorticity flux before the existing outer negative curl and
divergence. Pointwise work neutrality follows because the additive
acceleration is perpendicular to the same nodal wind. Since
`delta_sigma` is horizontally constant, it cancels algebraically from
`m * delta_q`; tests may verify that it enters the diagnostic `q`, but must not
claim that the final correction has independent layer-thickness weighting.

Implementation is frozen to the following repository-specific contract:

- Enable the option only on the positive-time rollout equation. The DFI
  equation remains byte-for-byte on the incumbent path.
- Preserve the incumbent Coriolis Strang split. Because rollout constructs the
  primitive equation with zero angular velocity, pass the physical nodal
  `f = 2 * Omega * sin(latitude)` from the unmodified physics specifications as
  a static equation input used only by this diagnostic.
- Use the adapter's nondimensionalized 900-second `step_seconds`; do not insert
  dimensional `900.0` into primitive-equation arithmetic.
- Form nodal `p_s` from the current modal log surface pressure, form nodal `q`,
  transform `q` to modal space, and use the existing `cos_lat_grad` operator.
  Contract that gradient with `aux_state.cos_lat_u` and `sec2_lat` exactly as
  `compute_diagnostic_state_sigma` contracts the log-pressure gradient.
- Set `delta_eta = -m * step_seconds * (u dot grad(q))`. Add nodal components
  `(-v * delta_eta * sec2_lat, u * delta_eta * sec2_lat)` beside the incumbent
  absolute-vorticity components before the existing modal transform,
  `curl_cos_lat`, and `div_cos_lat` calls. Preserve the existing final
  wavenumber clipping.
- Use one scalar all-diagnostics-valid predicate for the complete APVM curl and
  divergence pair. Nonpositive or nonfinite mass, a nonfinite intermediate,
  or a nonfinite transformed tendency selects the exact incumbent pair. Add no
  local partial fallback, cap, mask, coefficient, taper, retune, or second
  variant.

This is feasible under JAX: all geometry is static, the needed transforms and
metric contraction already execute under JIT, and no host eigensolver or new
dependency is required. It changes more arithmetic than the previously
rejected absolute-vorticity dealiaser and enstrophy cap, but tests a distinct
flux closure rather than retuning either failed neighborhood.

The strongest staged alternatives remain blocked. PPM flux-form vertical DSE
still lacks the advective/compressive balance and SIL3-stage reconstruction
contract; energy-neutral boundary-layer mixing remains a broad three-process
filter without incumbent materiality evidence; and omega-alpha coupling still
lacks a demonstrated discrete mismatch and frozen paired weights. APVM has the
clearest bounded implementation and highest learning value of the current set.
