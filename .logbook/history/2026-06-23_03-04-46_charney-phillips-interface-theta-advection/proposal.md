---
schema_version: 1
slug: charney-phillips-interface-theta-advection
title: Charney-Phillips Interface Theta Reconstruction in Vertical Transport
status: ready
created_at: 2026-06-23T02:30:00Z
author_role: Researcher
target_model: dino_hsl2_theta
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/sigma_coordinates.py
  - src/dynamaxx/dycore/models/dinosaur/vertical_interpolation.py
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

# Charney-Phillips Interface Theta Reconstruction in Vertical Transport

## Hypothesis

The core uses a **Lorenz vertical grid**: temperature/theta, winds, and
divergence all live at layer centers, while `sigma_dot` lives at internal layer
boundaries (`compute_diagnostic_state_sigma`). The Lorenz grid is well known to
carry a spurious vertical **computational mode** in the thermodynamic variable
that degrades baroclinic and lower-tropospheric thermal structure (Arakawa &
Moorthi 1988; Holdaway, Thuburn & Wood 2013). The incumbent's worst metric by far
is `2m_temperature` (~-1.01), with `mean_sea_level_pressure` also negative -- both
lower-tropospheric / thermal-structure dominated. The centered vertical-advection
stencil currently re-injects the 2-delta-sigma thermal mode each step. Sampling
theta at the **layer interfaces** (where `sigma_dot` already lives) purely inside
the vertical theta-transport flux gives that flux Charney-Phillips-like placement
and should suppress the computational mode, improving the thermal column without a
full prognostic re-staggering.

## Mechanism

Register a side-by-side candidate named `dino_hsl2_theta_cpvert`. Preserve every
incumbent setting; change only the **vertical** theta-transport operator.

In `PrimitiveEquationsSigma.temperature_tendency_potential_temperature_form`
(`primitive_equations.py`, the call to
`self._vertical_tendency(aux_state.sigma_dot_full, theta_anomaly)`), replace the
centered-center stencil for the candidate with an interface-flux form:

- reconstruct `theta_anomaly` at internal layer boundaries via a log-pressure /
  Exner-consistent interface interpolation, using the existing
  `cumulative_log_sigma_integral` / `vertical_interpolation.interp` helpers;
- form the vertical theta flux `sigma_dot_full * theta_interface` at internal
  boundaries (where `sigma_dot` natively lives -- no averaging of the velocity to
  centers);
- take the divergence of that flux back to centers as the padded
  boundary-flux difference over `layer_thickness` (the discrete operator already
  used in `compute_vertical_velocity_sigma` / `centered_difference`), with the
  fluxes zeroed at sigma=0 and sigma=1 exactly as today;
- gate behind one adapter flag; leave momentum/divergence vertical advection, the
  implicit operators, the horizontal semi-Lagrangian transport, and all
  diagnostics on the incumbent path;
- add a finite-fallback to the incumbent centered stencil if the reconstruction
  is nonfinite.

This is an **interface reconstruction of the advected scalar** (Charney-Phillips
placement), not an operator-family swap.

## Implementation Scope

- Expected files: `primitive_equations.py` (interface-flux theta tendency branch),
  `sigma_coordinates.py` / `vertical_interpolation.py` (interface reconstruction
  helper), `adapter.py` (flag), `__init__.py`, `registry.py`, tests.
- Registry changes: add only the side-by-side candidate.
- API changes: none.
- Tests to update: isothermal and linear-in-log-pressure theta profiles give the
  analytically correct (near-zero / exact) vertical tendency; boundary fluxes
  vanish at sigma=0,1; the flux divergence is mass-consistent with `sigma_dot_full`
  (no spurious source for a constant theta); nonfinite fallback reproduces the
  incumbent; momentum/divergence paths byte-unchanged; registry coverage and a
  finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements: `2m_temperature` (primary -- mode suppression in the
  lower troposphere); `mean_sea_level_pressure` modest via cleaner column
  thickness.
- Expected neutral metrics: `geopotential_500` neutral-to-slightly-positive;
  `10m_u_component_of_wind` ~neutral (momentum path unchanged).
- Possible regressions: interface reconstruction can add vertical diffusion
  (over-smoothing thermal gradients); if flux divergence is not exactly
  mass-consistent with `sigma_dot_full`, a slow thermal drift / early-lead
  regression.

## Risks

- Numerical stability: moderate -- vertical advection is stability-sensitive here
  (the suppression ablation went nonfinite at long lead), so the finite-fallback
  and the isothermal/linear-theta consistency test are mandatory.
- Compute cost: low -- one interface reconstruction and flux divergence per step.
- Data leakage: none.
- Physical plausibility: high -- Charney-Phillips placement of the thermodynamic
  variable is a recognized fix for the Lorenz computational mode.
- Rollback complexity: low (one tendency branch + helper + flag + registry).

## Evaluation Plan

- Fast gate: `uv run pytest`; `uv run dynamaxx-eval fast --model dino_hsl2_theta_cpvert`;
  finite forecasts, zero diagnostic issues.
- Iteration gate: `uv run dynamaxx-eval iteration --model dino_hsl2_theta_cpvert --workers 4`;
  support is primary delta >= +0.002, clean diagnostics, no early-lead or
  variable-by-lead RMSE guardrail failure.
- Validation gate: `uv run dynamaxx-eval validation --model dino_hsl2_theta_cpvert --workers 4`
  only after iteration promotion; require validation delta >= +0.001.
- Falsification: a clean near-zero or negative delta would show the Lorenz
  computational mode is not a material part of the lower-tropospheric thermal
  error under this forcing, or that the existing dissipation already controls it.

## Citations

- Citation or source:
  - Dynamaxx source: `primitive_equations.py` `compute_diagnostic_state_sigma`
    (Lorenz placement: theta at centers, `sigma_dot` at boundaries) and
    `temperature_tendency_potential_temperature_form` (centered vertical theta
    advection).
  - Arakawa, A. & Moorthi, S. 1988. Baroclinic instability in vertically discrete
    systems. J. Atmos. Sci. 45(11), 1688-1707.
    https://doi.org/10.1175/1520-0469(1988)045%3C1688:BIIVDS%3E2.0.CO;2
  - Holdaway, D., Thuburn, J. & Wood, N. 2013. Comparison of Lorenz and
    Charney-Phillips vertical discretisations. QJRMS 139(673), 1081-1098.
    https://doi.org/10.1002/qj.2016
  - Thuburn, J. & Woollings, T. J. 2005. Vertical discretizations giving optimal
    representation of normal modes. J. Comput. Phys. 203(2), 386-404.
    https://doi.org/10.1016/j.jcp.2004.08.018

## Researcher Notes

Authored at the operator's request through Claude Code on 2026-06-23 from a
fanned-out vertical-structure research pass. Highest-leverage orthogonal idea
found: it attacks the dominant `2m_temperature` error via a recognized physical
mechanism (the Lorenz computational mode), is small-to-medium implementation
surface, and is genuinely novel against every prior vertical-transport idea --
`semi-lagrangian-vertical-transport` (scrap, full-field remap),
`upwind-vertical-advection-rollout` / `theta-upwind-vertical-advection` (sign-aware
center stencil, still center-sampled theta), `smoothed-sigma-dot-vertical-advection`
(filters the velocity, not theta placement), `vertical-courant-limited-advection`
(caps sigma_dot), and `pressure-aware-sigma-layer-grid` (layer spacing). None of
these change *where theta is sampled in the vertical*; this is the only
Charney-Phillips-flavored idea. Honest success probability ~25-30%; clean-but-
negative is the modal loop outcome, but this targets the single dominant error.

## Evaluator Notes

### 2026-06-23T03:03:08Z

Decision: move to `ready`; ranked 1 of 4 current proposals.

This is the strongest next target for the Orchestrator. It attacks the current
incumbent's dominant negative variable, `2m_temperature`, through a recognized
vertical-grid mechanism rather than another small HSL-departure refinement or
lower-boundary residual. The key distinction from scrapped
`layer-interface-flux-form-vertical-advection` and staged vertical-advection
ideas is scope: this proposal changes only the theta vertical-transport flux
sampling, leaves momentum/divergence/continuity and the accepted horizontal HSL
theta path intact, and requires no new forecast inputs or evaluation support.

Recent history supports keeping the ready queue focused here. The accepted HSL
theta sequence produced large and then moderate gains, while follow-on qmono,
Picard, CFL-blend, and mean-neutral variants were either unstable, negative, or
subthreshold. That argues for a genuinely different thermodynamic error source.
The vertical-family history is cautionary, so implementation must be strictly
side-by-side with finite fallback to the incumbent centered stencil and tests
for constant/isothermal profiles, boundary flux zeros, and non-thermal path
identity. Still, among the four reviewed proposals this has the best ratio of
scientific mechanism, implementation surface, and expected score leverage under
the fixed gates.
