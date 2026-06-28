---
schema_version: 1
slug: rossby-wave-source-vorticity-correction
title: Low-Mode Rossby-Wave-Source Vorticity Correction
status: scrap
created_at: 2026-06-25T01:38:28Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Low-Mode Rossby-Wave-Source Vorticity Correction

## Hypothesis

The dry incumbent may still misplace large-scale rotational response generated
by divergent tropical and subtropical outflow. A bounded Rossby-wave-source
(RWS) correction applied only to low-mode upper-tropospheric vorticity tendency
can improve planetary-wave phase and downstream `geopotential_500` /
`mean_sea_level_pressure` without damping balanced extratropical Rossby waves or
touching the accepted mass-DSE thermodynamic transport.

## Mechanism

Add one side-by-side candidate, for example `dino_hsl2_mass_dse_rws_vort`.
Inside the positive-time primitive-equation tendency, diagnose a reduced RWS
term from the forecast state:

`S = -v_chi dot grad(absolute_vorticity) - absolute_vorticity * divergence`,

where `v_chi` is the divergent wind reconstructed from the divergence component
only. Apply the correction only in an upper-tropospheric sigma envelope and a
tropical-to-subtropical latitude envelope, then project to low total
wavenumbers. Use it as a bounded correction to the vorticity tendency by
blending toward the low-mode RWS estimate for the divergent-vorticity source
while leaving rotational advection, divergence tendency, temperature tendency,
log-surface-pressure tendency, tracers, filters, and outputs unchanged.

The candidate must no-op for nondivergent flow, invalid wind reconstruction,
invalid absolute vorticity, or nonfinite source diagnostics. It should also cap
per-step vorticity increments and preserve the incumbent exact Coriolis split
and horizontal diffusion settings.

## Implementation Scope

- Expected files: add an opt-in RWS helper near vorticity tendency construction
  in `primitive_equations.py`, thread the selector through `adapter.py`, add a
  factory/registry entry, and add focused tests.
- Registry changes: add `dino_hsl2_mass_dse_rws_vort`.
- API changes: none to forecast inputs, outputs, target variables, lead times,
  or evaluation protocols.
- Tests to update: registry creation; disabled-flag incumbent equivalence;
  finite no-JIT smoke forecast; exact no-op for zero divergence; exact no-op
  outside the latitude/vertical masks; bounded low-mode response for a synthetic
  divergent outflow pattern; fallback on nonfinite diagnostics.

## Expected Metric Movement

- Expected improvements: `geopotential_500` and `mean_sea_level_pressure` at
  medium and late leads if tropical/subtropical divergent outflow is seeding
  planetary-wave phase errors in the dry rollout; possible secondary
  `10m_u_component_of_wind` improvement through better large-scale steering.
- Expected neutral metrics: `2m_temperature` should remain close to incumbent
  because no surface residual, ocean flux, humidity, or thermal tendency is
  changed.
- Possible regressions: the primitive equations already contain the formal
  absolute-vorticity stretching and advection terms, so the correction can
  double-count or distort real wave sources if the low-mode blend is too strong.

## Risks

- Numerical stability: moderate; vorticity forcing is dynamically sensitive and
  must be capped, low-mode, and mask-limited.
- Compute cost: low to moderate; reconstructing divergent wind and low-mode
  filtering add spectral transforms but no new solver.
- Data leakage: none; uses only forecast-state vorticity/divergence and fixed
  masks/constants.
- Physical plausibility: moderate; RWS is an established diagnostic for
  tropical-extratropical rotational response, but the proposed correction is a
  reduced numerical closure rather than a full convection/divergence
  parameterization.
- Rollback complexity: low; one selector, one helper, one factory, and focused
  tests.

## Evaluation Plan

- Fast gate: run fixed fast for `dino_hsl2_mass_dse_rws_vort`; reject on
  nonfinite diagnostics, excessive vorticity increments, or early mass/wind
  guardrail warnings.
- Iteration gate: run fixed iteration against cached `dino_hsl2_mass_dse`; the
  candidate must exceed `+0.002` primary-score improvement with clean guardrails.
- Validation gate: run fixed validation only after iteration promotion and
  require at least `+0.001` improvement.
- Outcome that would falsify the hypothesis: near-zero clean iteration movement
  would indicate the incumbent's existing vorticity tendency already captures
  enough RWS structure; wind or MSLP guardrail failures would indicate the
  correction is dynamically too invasive.

## Citations

- Sardeshmukh, P. D. and B. J. Hoskins, 1988: The generation of global
  rotational flow by steady idealized tropical divergence. Journal of the
  Atmospheric Sciences, 45, 1228-1251.
  https://doi.org/10.1175/1520-0469(1988)045%3C1228:TGOGRF%3E2.0.CO;2
- Hoskins, B. J. and D. J. Karoly, 1981: The steady linear response of a
  spherical atmosphere to thermal and orographic forcing. Journal of the
  Atmospheric Sciences, 38, 1179-1196.
  https://doi.org/10.1175/1520-0469(1981)038%3C1179:TSLROA%3E2.0.CO;2
- Qin, J. and W. A. Robinson, 1993: On the Rossby wave source and the steady
  linear response to tropical forcing. Journal of the Atmospheric Sciences, 50,
  1819-1823.
  https://doi.org/10.1175/1520-0469(1993)050%3C1819:OTRWSA%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of scrapped `barotropic-rossby-phase-split`, which
applied an analytic phase shift to barotropic vorticity modes. This proposal
does not prescribe a phase speed; it targets the divergent-flow source term
that generates rotational response. It is also not staged
`equatorial-gravity-wave-divergence-sponge`, which damps divergence and
log-pressure high modes in the equatorial waveguide. Here divergence is used
only diagnostically to correct low-mode upper-tropospheric vorticity tendency.

The proposal avoids the active momentum-advection and diffusion families:
`absolute-vorticity-hsl-momentum` changes broad momentum transport, while
`kinetic-energy-skew-momentum-advection` and diffusion ideas alter larger parts
of the horizontal dynamical operator. This candidate is narrower: one masked,
low-mode vorticity-source correction, leaving mass-DSE thermodynamics and
pressure continuity untouched. It is decorrelated from the thermal WTG and QG
frontogenesis proposals because it acts on rotational dynamics rather than
temperature.

## Evaluator Notes

### 2026-06-25T01:43:53Z

Decision: move to `scrap`; ranked 3 of 3 current proposals.

The Rossby-wave-source citation trail supports the diagnostic expression
involving divergent wind, absolute-vorticity gradients, and stretching as a way
to understand tropical-extratropical rotational response. That does not make it
a missing prognostic term for this incumbent. Source inspection shows
`PrimitiveEquationsSigma.curl_and_div_tendencies` already computes the
absolute-vorticity flux contribution from the current wind field, including the
divergent component encoded by the model's divergence control variable. The
proposal would add a second low-mode upper-tropospheric vorticity correction
derived from the same forecast divergence, while leaving divergence,
temperature, pressure, and mass continuity unchanged. That is more likely to
double-count or unbalance an existing primitive-equation term than to represent
missing convective outflow physics.

Local evidence argues against spending a fixed iteration slot on another
vorticity-only correction. Narrow absolute-vorticity flux dealiasing was clean
but far below promotion, Coriolis-centered HSL departure was effectively
neutral, Helmholtz momentum diffusion was effectively neutral, and the scrapped
barotropic Rossby phase and enstrophy-conserving vorticity-Jacobian proposals
document the risk of repeated prognostic vorticity edits without a specific
diagnosed error. The staged `absolute-vorticity-hsl-momentum` proposal already
covers a stronger, more coherent vorticity-transport hypothesis if the loop
later wants to revisit rotational dynamics.

Reject this proposal unless future diagnostics show a specific RWS-like bias
that is not already represented in the incumbent absolute-vorticity tendency
and cannot be tested by the staged momentum/vorticity candidates.
