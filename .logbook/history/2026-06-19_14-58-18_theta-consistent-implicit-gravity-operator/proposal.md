---
schema_version: 1
slug: theta-consistent-implicit-gravity-operator
title: Use a Theta-Consistent Semi-Implicit Gravity-Wave Operator
status: ready
created_at: 2026-06-19T14:51:51Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
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

# Use a Theta-Consistent Semi-Implicit Gravity-Wave Operator

## Hypothesis

The incumbent now uses potential-temperature explicit thermodynamic transport,
rollout-only theta layer-mean recentering, and off-centered SIL3 time
integration. However, `PrimitiveEquationsSigma.implicit_terms` and
`implicit_inverse` still use the original temperature-form semi-implicit
linear gravity-wave operator through `get_temperature_implicit_sigma` and the
temperature/geopotential blocks in `_get_implicit_term_matrix_sigma`.

The accepted theta-form explicit tendency improved both iteration and
validation, while stronger theta recentering and DFI-theta variants were either
nonfinite, subthreshold, or slightly negative. That pattern argues for changing
the positive-time linearized thermodynamic operator, not for another
post-step recentering or DFI merge. A theta-consistent implicit operator should
reduce residual mass/thermal phase error while preserving the accepted
off-centered fast-mode damping.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_theta_implicit`.
Preserve all incumbent behavior except the opt-in semi-implicit
thermodynamic/gravity-wave linearization.

For the candidate:

- add an equation option such as `implicit_thermodynamic_variable="temperature"`
  by default and `"potential_temperature"` for the candidate;
- construct a fixed reference Exner profile from sigma centers and the same
  1000 hPa reference pressure already used by the theta tendency path;
- define the implicit thermal perturbation as a dry theta anomaly about the
  reference profile, but keep the state storage as `temperature_variation` so
  the public forecast contract and output code do not change;
- replace the temperature-form implicit divergence-to-thermal weights with
  theta-form weights scaled back to temperature tendency using the local
  reference Exner factor;
- replace the implicit inverse matrix blocks consistently so the solver inverts
  the same linear operator it applies in `implicit_terms`;
- keep explicit theta transport, theta mean recentering, weak-HS forcing,
  Coriolis splitting, horizontal diffusion, DFI span, and output interpolation
  unchanged;
- use the same theta-consistent implicit operator in DFI and positive-time
  rollout because the change is a linear balance operator, not a DFI-specific
  filter;
- fall back to the incumbent temperature-form operator for invalid sigma
  geometry, nonfinite reference Exner factors, or nonfinite matrix inverses.

This is not a duplicate of full-state theta explicit transport: it targets the
semi-implicit gravity-wave solve and its inverse matrix, leaving explicit
scalar advection formulas unchanged.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the candidate model name above.
- API changes:
  - None. `DycoreModel.forecast`, input variables, output variables, target
    variables, lead times, and protocols remain unchanged.
- Tests to update:
  - Unit-test finite reference Exner and reference theta construction on the
    incumbent sigma grid.
  - Verify the default temperature implicit path is unchanged.
  - Verify the theta implicit option changes `temperature_variation`,
    `divergence`, and `log_surface_pressure` implicit terms consistently while
    leaving vorticity and tracers on zero implicit tendencies.
  - Verify `implicit_inverse(implicit_terms(...))` shape compatibility and
    finite output for representative states.
  - Verify the candidate factory preserves every incumbent flag except the new
    implicit thermodynamic variable selector.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at early to medium leads if
    the remaining error is partly a mismatch between theta explicit transport
    and temperature-form gravity-wave linearization.
  - `2m_temperature` at medium leads if better thermal/mass phase reduces lower
    column drift after the accepted residual decays.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should remain close to incumbent because wind
    initialization, Richardson wind output, Coriolis splitting, and residual
    correction are unchanged.
- Possible regressions:
  - The current temperature-form implicit operator may be empirically matched to
    the Dinosaur sigma discretization even after theta explicit transport.
  - Inconsistent theta scaling inside the inverse matrix can destabilize fast
    gravity-wave modes or produce early MSLP/Z500 guardrail failures.

## Risks

- Numerical stability:
  - Moderate to high. The proposal touches the implicit operator and inverse
    used at every inner step. Strict finite fallbacks and focused matrix tests
    are required before fixed evaluation.
- Compute cost:
  - Low. Matrix dimensions and resolution are unchanged; only precomputed
    vertical weights and per-wavenumber inverse blocks change.
- Data leakage:
  - None. The mechanism uses only fixed sigma geometry and physical constants.
- Physical plausibility:
  - Moderate to high. The dry primitive equations conserve potential
    temperature materially in adiabatic motion, and semi-implicit methods depend
    on the consistency of the chosen linearized thermodynamic variable.
- Rollback complexity:
  - Low to moderate. Remove one primitive-equation option, alternate weight
    helpers, one factory/export, one registry entry, and focused tests if
    rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_theta_implicit`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_theta_implicit --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    clean diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and
    no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_theta_implicit --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A nonfinite fast run or an early MSLP/Z500 guardrail failure would show the
    theta implicit operator is not numerically compatible with the incumbent
    sigma discretization. A clean near-zero or negative iteration delta would
    show that the accepted theta gains do not extend to the implicit
    linearization.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  implements theta explicit transport through
  `TEMPERATURE_TENDENCY_FORMULATION_POTENTIAL_TEMPERATURE`, while the implicit
  operator still calls `get_temperature_implicit_sigma`.
- Local history:
  `.logbook/history/2026-06-18_18-48-01_potential-temperature-thermodynamic-tendency/decision.md`
  accepted theta-form explicit thermodynamics with iteration delta
  `+0.015447942083573918` and validation delta `+0.019234576988685914`.
- Local history:
  `.logbook/history/2026-06-19_11-55-13_dfi-theta-mean-recenter/decision.md`
  rejected DFI-theta recentering after a clean but negative iteration delta,
  motivating a positive-time operator change instead of another DFI routing
  variant.
- Whitaker, J. S. and Kar, S. K. 2013. "Implicit-Explicit Runge-Kutta Methods
  for Fast-Slow Wave Problems." Monthly Weather Review. The local SIL3 solver
  also cites this paper. https://doi.org/10.1175/MWR-D-13-00132.1
- ECMWF IFS Documentation CY36R1, Part III, "Dynamics and Numerical
  Procedures", cites semi-implicit primitive-equation integration and the
  Simmons-Burridge vertical finite-difference formulation:
  https://www.ecmwf.int/sites/default/files/elibrary/2010/9232-part-iii-dynamics-and-numerical-procedures.pdf
- Simmons, A. J. and Burridge, D. M. 1981. "An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates."
  Monthly Weather Review, 109, 758-766. ADS entry:
  https://ui.adsabs.harvard.edu/abs/1981MWRv..109..758S

## Researcher Notes

This proposal accounts for the recent theta negative evidence by not changing
DFI, post-step theta recentering, zonal means, or output diagnostics. It also
differs from active staged `full-state-theta-thermodynamic-tendency`, which
changes explicit theta transport. Here the explicit tendency remains exactly
the accepted path; only the semi-implicit linear gravity-wave operator becomes
theta-consistent.

The main risk is higher than output-only proposals because the implicit inverse
is central to stability. It is included because the incumbent's largest recent
gain was the off-centered semi-implicit gravity-wave change, and this proposal
targets the same high-leverage fast-mode/mass-field subsystem through a
different physical variable.

## Evaluator Notes

### 2026-06-19T14:56:55Z

Decision: move to `ready`; ranked 1 of 3 fresh proposals.

This is the strongest current recommendation, not a final implementation
choice. Source inspection supports the proposal's core claim: the incumbent
uses the accepted potential-temperature explicit thermodynamic tendency, but
`PrimitiveEquationsSigma.implicit_terms` still calls
`get_temperature_implicit_sigma`, and `_get_implicit_term_matrix_sigma` still
builds the temperature-form divergence/thermal/log-pressure blocks. Recent
accepted history also supports the target subsystem: theta-form explicit
thermodynamics cleared both gates, theta mean recentering cleared both gates,
and off-centered SIL3 produced a large mass-field gain. A theta-consistent
implicit operator is therefore a mechanistic follow-up that can plausibly move
MSLP, Z500, and T2m rather than only one output channel.

The risk is real because this touches the implicit operator and inverse used at
every inner step, and any shared `primitive_equations.py` or adapter edits will
invalidate incumbent cache reuse unless the Scorer can satisfy the
`roles/SCORER.md` conditions with immutable compatible artifacts. It is still
ready because the implementation can be kept side-by-side, the default
temperature-form path can remain unchanged, and local tests can directly check
operator/inverse consistency, finite Exner factors, shape compatibility, and
factory flag preservation. The Orchestrator should rank this ahead of the two
other fresh proposals but still compare it against existing staged alternatives
before selecting exactly one candidate.
