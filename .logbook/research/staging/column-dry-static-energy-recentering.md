---
schema_version: 1
slug: column-dry-static-energy-recentering
title: Preserve Column-Mean Dry Static Energy During Rollout
status: staging
created_at: 2026-06-21T06:20:34Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Preserve Column-Mean Dry Static Energy During Rollout

## Hypothesis

The incumbent preserves layer-mean potential temperature with a rollout-only
zero-mode correction, but it does not directly preserve column-integrated dry
static energy. On a hydrostatic sigma grid, vertically redistributing a small
thermal zero-mode can change thickness and pressure diagnostics even if each
layer's area-mean theta drift is controlled. A column dry-static-energy
constraint should keep the accepted thermal-drift control while better
respecting the hydrostatic link between temperature, geopotential thickness,
MSLP, and Z500.

## Mechanism

Add an opt-in candidate that keeps the incumbent forecast path and appends one
rollout-only thermodynamic filter after the accepted positive-time step. The
filter diagnoses previous and next full temperature, sigma pressure, and
hydrostatic geopotential. It computes a mass-weighted column dry static energy
proxy and applies a horizontally uniform temperature increment with fixed
vertical weights so the next state's global column mean matches the previous
state. It changes only the modal zero component of `temperature_variation`,
uses finite and positive-pressure guards, and is excluded from time-reversed
DFI exactly like the accepted theta recentering.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side model suffix such as `_column_dse_recenter`.
- API changes:
  - None. Forecast inputs, output variables, lead times, metrics, and splits
    stay fixed.
- Tests to update:
  - Verify the helper preserves the chosen column DSE moment on synthetic
    fields.
  - Verify non-temperature state leaves and nonzero thermal modes are
    unchanged.
  - Verify finite fallback returns the incumbent next state.
  - Verify the factory preserves all incumbent options except the new selector.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` and `mean_sea_level_pressure` at medium leads if
    remaining thermal zero-mode drift projects onto hydrostatic thickness.
  - `2m_temperature` should remain close to incumbent because the accepted
    surface residual and weak-HS paths are unchanged.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be neutral except through balanced mass
    feedback.
- Possible regressions:
  - The extra zero-mode constraint may over-constrain the accepted theta
    recentering and remove useful thermodynamic adjustment.

## Risks

- Numerical stability:
  - Low to moderate. The correction is global and bounded by finite checks, but
    it changes thermal state every inner step.
- Compute cost:
  - Low. It adds reductions and no extra rollout steps.
- Data leakage:
  - None. It uses only previous and next forecast states.
- Physical plausibility:
  - Moderate to high. Dry static energy is a standard thermodynamic invariant,
    but this is a simplified hydrostatic-column constraint.
- Rollback complexity:
  - Low. The change can be removed as one option, helper, factory, registry
    entry, and tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model <candidate_model_name>`.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model <candidate_model_name> --workers 4`.
  - Compare to cached incumbent metrics and require primary-score delta at
    least `+0.002`, clean diagnostics, and fixed guardrails.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model <candidate_model_name> --workers 4`
    only after iteration promotion.
  - Require validation delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean subthreshold or negative iteration delta would show that the
    accepted theta recentering already captures the useful thermal zero mode or
    that column DSE is not the relevant remaining error.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` implements
  the incumbent rollout-only `_theta_layer_mean_recenter_step_filter`.
- Dynamaxx history:
  `.logbook/history/2026-06-19_00-02-28_theta-zero-mode-thermal-recentering/decision.md`
  accepted thermal zero-mode recentering with positive iteration and validation
  deltas.
- Thuburn, J. 2008. Some conservation issues for the dynamical cores of NWP
  and climate models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016
- Simmons, A. J. and Burridge, D. M. 1981. An energy and angular-momentum
  conserving vertical finite-difference scheme and hybrid vertical coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2

## Researcher Notes

This is not the existing staged `mass-weighted-theta-recentering`: that idea
changes the layerwise theta moment. This proposal tests a vertically integrated
dry-static-energy moment, so it is a different thermodynamic invariant with a
different expected pressure and Z500 signature. It is also not the rejected
global pressure anchor because it never edits `log_surface_pressure`.

## Evaluator Notes

### 2026-06-21T06:22:22Z

Decision: move to `staging`; ranked 2 of the currently reviewed ideas.

The scientific motivation is credible: the cited conservation literature
supports energy-aware vertical-coordinate dycore design, and a dry-static-energy
moment is more physical than directly anchoring surface pressure or a scored
diagnostic. It is also trajectory-level, rollout-only, and low-cost, which makes
it a plausible follow-up if the narrower theta-conservation path fails.

Do not make this the next ready candidate. The current incumbent already uses a
successful theta zero-mode recentering path, and this proposal stacks an
additional global column-energy constraint on top of that path. That raises a
real risk of over-constraining the thermal zero mode or removing empirically
useful adjustment. The staged `mass-weighted-theta-recentering` idea is a
cleaner first test because it replaces the accepted conserved moment with a
mass-weighted version rather than adding a second thermodynamic filter.
