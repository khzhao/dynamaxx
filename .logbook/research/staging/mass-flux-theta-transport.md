---
schema_version: 1
slug: mass-flux-theta-transport
title: Transport Potential Temperature with Sigma-Layer Mass Fluxes
status: staging
created_at: 2026-06-21T16:03:00Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Transport Potential Temperature with Sigma-Layer Mass Fluxes

## Hypothesis

The incumbent uses the accepted theta-form thermodynamic tendency plus
layer-mean theta recentering, but the scalar transport is still assembled as
advective tendencies of a nodal scalar. In terrain-following sigma coordinates,
dry potential temperature is materially conserved with the moving layer mass.
A flux-form theta tendency using sigma-layer mass thickness and the diagnosed
horizontal and vertical mass fluxes may reduce residual thermal drift without
adding a heat source, changing surface diagnostics, or retuning Held-Suarez
relaxation.

## Mechanism

Add an opt-in theta tendency formulation that keeps the incumbent primitive
equation, DFI, weak-HS analysis equilibrium, Coriolis split, off-centering, and
near-surface residuals unchanged, but replaces the explicit theta transport
calculation. For each step, diagnose local layer pressure thickness
`delta_sigma * surface_pressure`, compute dry theta from full temperature and
sigma pressure, form horizontal mass fluxes from the reconstructed wind and
layer mass, form vertical fluxes from `sigma_dot_full`, take the flux divergence
of layer-mass-weighted theta, and convert the resulting theta tendency back to
temperature with the local Exner factor.

The first implementation should be conservative and reversible: use finite
guards, preserve the incumbent theta tendency when mass thickness is nonpositive
or nonfinite, keep the accepted layer-mean theta recentering after the step, and
do not alter passive tracers, humidity dynamics, output packing, lead handling,
or evaluation protocols.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side incumbent-derived model with suffix `_mass_flux_theta`.
- API changes:
  - None. Forecast contract, target variables, splits, metrics, and protocols remain fixed.
- Tests to update:
  - Unit-test finite layer-mass diagnosis and zero-flow no-op behavior.
  - Verify the candidate changes only thermodynamic tendencies, not vorticity, divergence, log surface pressure, or tracer tendencies.
  - Verify nonfinite or nonpositive mass thickness falls back to the incumbent theta tendency.
  - Verify the candidate factory preserves all incumbent options except the new theta transport selector.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` at medium and late leads if residual lower-column thermal drift is caused by nonconservative theta transport.
  - `geopotential_500` and `mean_sea_level_pressure` if cleaner thermal mass transport improves hydrostatic thickness and pressure-gradient balance.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be mostly neutral because wind diagnostics, residual memory, and momentum equations are unchanged.
- Possible regressions:
  - Flux-form theta transport can be more diffusive or phase-shifted than the accepted advective theta tendency.
  - Any mismatch with the semi-implicit pressure-work split can perturb MSLP/Z500.

## Risks

- Numerical stability:
  - Moderate. The change touches thermodynamic tendencies in every inner step and must handle thin or low-pressure layers robustly.
- Compute cost:
  - Low to moderate. It adds local mass-flux algebra and existing transforms, with no extra rollout steps.
- Data leakage:
  - None. It uses only current forecast state and fixed grid geometry.
- Physical plausibility:
  - High. Flux-form thermodynamic transport is a standard way to keep scalar evolution consistent with mass continuity.
- Rollback complexity:
  - Low. Remove one formulation selector/helper, one factory/export, one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Support requires primary-score delta at least `+0.002`, clean diagnostics, and no early or variable-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4` only after iteration promotion.
  - Require validation primary delta at least `+0.001` with fixed guardrails passing.
- Outcome that would falsify the hypothesis:
  - A clean neutral/negative iteration delta would show the accepted theta tendency and recentering already capture the useful thermal-transport signal. Any early MSLP or Z500 guardrail failure would show flux-form theta disrupts pressure balance.

## Citations

- Citation or source:
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` contains the accepted theta tendency path, sigma-dot diagnostics, and log-surface-pressure continuity terms.
  - Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` enables the incumbent theta tendency and rollout-only theta mean recentering.
  - History: `.logbook/history/2026-06-18_18-48-01_potential-temperature-thermodynamic-tendency/decision.md` accepted theta-form thermodynamics; `.logbook/history/2026-06-21_06-24-25_mass-weighted-theta-recentering/decision.md` rejected a recentering-only mass-weighted follow-up, motivating a tendency-level mass-flux mechanism instead.
  - Lin, S.-J. 2004. A vertically Lagrangian finite-volume dynamical core for global models. Monthly Weather Review. https://doi.org/10.1175/1520-0493(2004)132%3C2293:AVLFDC%3E2.0.CO;2
  - Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum conserving vertical finite-difference scheme and hybrid vertical coordinates. Monthly Weather Review. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
  - Durran, D. R. 2010. Numerical Methods for Fluid Dynamics: With Applications to Geophysics, second edition. Springer. https://doi.org/10.1007/978-1-4419-6412-0

## Researcher Notes

This is not active staged `full-state-theta-thermodynamic-tendency`, which
changes the theta variable content, and it is not `theta-upwind-vertical-advection`,
which changes only vertical advection numerics. This proposal changes the
transport form so theta evolves with sigma-layer mass fluxes. It also differs
from the rejected `mass-weighted-theta-recentering`: that candidate applied a
post-step mean correction, while this proposal changes the local tendency that
creates thermal drift in the first place.

## Evaluator Notes

### 2026-06-21T16:04:40Z

Decision: move to `staging`; ranked 2 of 3 current proposals.

The physical motivation is sound enough to preserve. Flux-form transport of a
material scalar with layer mass is a standard dycore idea, and this proposal is
not a duplicate of the rejected `mass-weighted-theta-recentering`, which only
changed a post-step mean correction and regressed by `-0.0004984517871132743`.
It also differs from staged `full-state-theta-thermodynamic-tendency`,
`theta-upwind-vertical-advection`, and `skew-symmetric-horizontal-scalar-advection`
because it changes the conservative form of the theta tendency rather than the
theta variable content, vertical stencil, or horizontal scalar product identity.

Keep it staged rather than ready because it touches the thermodynamic tendency
and mass/continuity coupling every inner step. The accepted theta tendency was
a large win, but it already showed day-1 MSLP/Z500 sensitivity; the later
theta skew-symmetric scalar-advection follow-up was clean but negative, and
mass-weighted theta recentering was also clean but negative. A flux-form theta
rewrite could plausibly improve thermal drift, but it could also double-count
or misalign with the incumbent semi-implicit pressure-work split and pressure
thickness representation. That risk is materially higher than the localized
momentum-filter proposal selected for the small `ready` queue.

If promoted later, the candidate should be implemented as a strictly
side-by-side theta-transport option, with finite and nonpositive layer-mass
fallbacks to the accepted theta tendency, tests proving non-thermal tendencies
remain unchanged, and no changes to residual diagnostics or forecast outputs.
