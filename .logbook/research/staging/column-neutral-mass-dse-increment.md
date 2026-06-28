---
schema_version: 1
slug: column-neutral-mass-dse-increment
title: Remove Column-Mean Heat from the Mass-DSE HSL Increment
status: staging
created_at: 2026-06-24T01:38:14Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/test_primitive_equations.py
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Remove Column-Mean Heat from the Mass-DSE HSL Increment

## Hypothesis

The accepted mass-DSE branch improved the fixed iteration and validation
scores, but the latest pressure-thickness product-rule correction degraded the
same incumbent broadly. That suggests the useful signal is the layer-mass
weighting of horizontal thermal structure, not a more aggressive coupling to
the pressure-thickness tendency.

A conservative follow-up is to keep the accepted mass-DSE HSL tendency but
remove only the local column-mass-weighted mean of the extra mass-DSE increment
relative to the unweighted DSE-HSL fallback. This preserves the vertical
redistribution and baroclinic structure introduced by mass-DSE HSL while
avoiding a direct net column heating or cooling increment that can project onto
MSLP and Z500.

## Mechanism

Register a side-by-side model such as `dino_mass_dse_colneutral` derived from
`dino_hsl2_mass_dse`.

For the candidate only:

- compute the unweighted DSE-HSL temperature tendency and the accepted
  layer-mass-weighted DSE-HSL temperature tendency already present in
  `temperature_tendency_potential_temperature_form`;
- diagnose nodal layer pressure thickness with the existing
  `nodal_sigma_layer_pressure_thickness` helper;
- form the nodal incremental thermal tendency
  `mass_dse_temperature_tendency - dse_temperature_tendency`;
- subtract the column-mass-weighted vertical mean of that increment at each
  horizontal grid point from all layers;
- add the column-neutralized increment back to the unweighted DSE-HSL fallback;
- fall back exactly to `dino_hsl2_mass_dse` if pressure thickness, the column
  mean, the adjusted increment, or selected modal tendency is nonfinite.

This is not a pressure-thickness product-rule correction. It never uses the
pressure-thickness time tendency and does not edit log-surface-pressure
continuity, momentum, forcing, output variables, or evaluation protocols.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests in `tests/dycore/models/dinosaur/test_primitive_equations.py`
    and `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory and registry key for
    `dino_mass_dse_colneutral`.
- API changes:
  - None.
- Tests to update:
  - Verify the candidate preserves all incumbent settings except the new
    selector and model name.
  - Verify the selected increment has zero column-mass-weighted mean on a
    synthetic finite field.
  - Verify an already column-neutral increment is unchanged.
  - Verify invalid pressure thickness or nonfinite adjusted tendencies fall back
    to the incumbent mass-DSE branch.
  - Verify registration and unchanged output variables.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` if part of the accepted
    mass-DSE increment's residual error is net column heat-content drift rather
    than vertical structure.
  - `2m_temperature` could improve at medium leads if the low-level thermal
    phase benefit remains after removing the column mean.
- Expected neutral metrics:
  - `10m_u_component_of_wind`, because momentum and the Richardson 10 m
    diagnostic remain unchanged.
- Possible regressions:
  - The accepted mass-DSE HSL improvement may depend on net column heating or
    cooling that this proposal removes.
  - Column-neutralizing a local increment can weaken broad lower-tropospheric
    thermal advection and reduce the accepted `2m_temperature` benefit.

## Risks

- Numerical stability:
  - Low to moderate. The correction is a bounded columnwise linear projection on
    an already finite tendency, but it acts every thermodynamic step.
- Compute cost:
  - Low. It adds one pressure-thickness-weighted vertical reduction and no new
    remaps, trajectories, or lead outputs.
- Data leakage:
  - None. It uses only current forecast state and fixed sigma geometry.
- Physical plausibility:
  - Moderate to high. Column energy neutrality is a standard balance guard, but
    it is a projection rather than a locally flux-form conservative transport.
- Rollback complexity:
  - Low. Remove one helper/selector, factory/export, registry key, and focused
    tests.

## Evaluation Plan

- Fast gate:
  - `uv run pytest`
  - `uv run dynamaxx-eval fast --model dino_mass_dse_colneutral`
  - Require finite forecasts and zero diagnostics.
- Iteration gate:
  - `uv run dynamaxx-eval iteration --model dino_mass_dse_colneutral --workers 4`
  - Support requires primary delta at least `+0.002`, clean diagnostics, and no
    fixed RMSE guardrail failure against cached `dino_hsl2_mass_dse`.
- Validation gate:
  - `uv run dynamaxx-eval validation --model dino_mass_dse_colneutral --workers 4`
    only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean near-zero or negative iteration delta would show that the accepted
    mass-DSE branch needs its column-mean increment. Any `2m_temperature`
    regression with neutral MSLP/Z500 would indicate the projection removed the
    useful lower-column thermal signal.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  contains the accepted unweighted DSE-HSL fallback and mass-DSE HSL branch used
  by this selector.
- Dynamaxx history:
  `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/decision.md`
  accepted the mass-DSE branch over unweighted DSE-HSL.
- Dynamaxx history:
  `.logbook/history/2026-06-23_08-53-50_ramped-column-neutral-theta-pressure-work/decision.md`
  found that a ramped column-neutral pressure-work correction was stable but
  neutral, so this proposal applies column neutrality only to the accepted
  mass-DSE increment rather than to a new pressure-work source.
- Simmons, A. J. and Burridge, D. M. 1981. An Energy and Angular-Momentum
  Conserving Vertical Finite-Difference Scheme and Hybrid Vertical Coordinates.
  Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Thuburn, J. 2008. Some Conservation Issues for the Dynamical Cores of NWP and
  Climate Models. Journal of Computational Physics.
  https://doi.org/10.1016/j.jcp.2006.08.016
- Staniforth, A. and Cote, J. 1991. Semi-Lagrangian Integration Schemes for
  Atmospheric Models: A Review. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2

## Researcher Notes

This is distinct from staged `area-neutral-mass-dse-hsl`, which removes the
horizontal area mean of the transported mass-DSE tendency in each layer. This
proposal removes a vertical column mean at each horizontal grid point from only
the incremental difference between mass-DSE HSL and unweighted DSE-HSL.

It is also distinct from staged `column-dry-static-energy-recentering`, which
is a post-step state filter. This candidate acts inside the accepted thermal
tendency branch and preserves the fixed forecast contract. The negative
pressure-work history is relevant caution: column-neutral projections can erase
signal. The reason to still test this variant is that the projected quantity is
the already accepted mass-DSE increment, not a newly added pressure-work term.

## Evaluator Notes

### 2026-06-24T01:43:04Z

Decision: move to `staging`; rank 2 of 3 new proposals.

This is plausible and cheap, but it is not the best next experiment. The
proposal targets only the incremental difference between the accepted mass-DSE
branch and the unweighted DSE-HSL fallback, so it is more focused than a
post-step column-energy filter and does not repeat the rejected
pressure-thickness product-rule mechanism. The operation is a bounded
columnwise projection with a clear fallback path and no forecast-contract
change.

Keep it staged because the expected signal is weaker and more ambiguous than
the hydrostatic inversion. Local history says conservative projections can be
safe yet subthreshold: `ramped-column-neutral-theta-pressure-work` was clean but
effectively neutral, and earlier zero-mode conservation refinements tended to
move less than the fixed `+0.002` iteration gate. This proposal could also
remove real net lower-column heating or cooling that was part of the accepted
mass-DSE validation gain. The staged `area-neutral-mass-dse-hsl` remains a
cleaner first conservation probe for layer-integral HSL drift; this column
projection is orthogonal but should not crowd ready.

Ranked recommendation: hold as a backup behind
`hydrostatic-inverted-mass-dse-hsl` and roughly behind the existing
`area-neutral-mass-dse-hsl` conservation probe. Promote only if diagnostics,
failed inversion evidence, or new score notes point to local column heat-content
drift rather than vertical DSE conversion error.
