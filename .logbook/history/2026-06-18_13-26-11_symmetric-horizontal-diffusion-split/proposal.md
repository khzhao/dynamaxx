---
schema_version: 1
slug: symmetric-horizontal-diffusion-split
title: Apply the Existing Horizontal Diffusion as a Symmetric Split
status: ready
created_at: 2026-06-18T06:01:43Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/time_integration.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Apply the Existing Horizontal Diffusion as a Symmetric Split

## Hypothesis

The incumbent applies the horizontal diffusion filter after each IMEX step,
then wraps the accepted symmetric Coriolis rotation around that filtered
non-Coriolis step. The diffusion strength and order are reasonable enough to be
stable, but a first-order post-step placement can introduce splitting error in
the nonlinear dynamics and in the interaction with the accepted Strang
Coriolis split.

Applying the same total diffusion as two half filters around each non-Coriolis
step should preserve the accepted damping amount while reducing operator-order
bias. This is a lower-surface-area numerical split experiment, not another
diffusion-strength or hyperdiffusion tuning proposal.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion`.
Preserve the incumbent grid, inner step, diffusion order, diffusion timescale,
DFI, weak-HS forcing, log-pressure and hydrostatic initialization, near-surface
residuals, and exact Strang Coriolis split.

Replace the positive-time step composition:

- build a half-step horizontal diffusion filter with the same modal operator and
  `0.5 * step_seconds`;
- apply the half filter to the incoming state before the IMEX non-Coriolis
  dynamics step;
- apply the second half filter to the outgoing state before the final half
  Coriolis rotation;
- keep DFI on the incumbent filter placement for the first candidate, so this
  experiment isolates positive-time rollout split ordering.

The total modal damping over a complete step remains close to the incumbent
for linear diffusion, but its placement relative to nonlinear tendencies is
second-order symmetric.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/time_integration.py` if a reusable
    pre/post filter wrapper is cleaner than adapter-local code
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only the side-by-side candidate named above.
- API changes:
  - None. Forecast inputs, outputs, variables, lead times, and protocols are
    unchanged.
- Tests to update:
  - Verify the candidate preserves incumbent physical flags, DFI behavior, and
    changes only positive-time diffusion placement.
  - Unit-test that two half diffusion filters equal one full diffusion filter
    on a static modal state to roundoff.
  - Verify the step wrapper is shape-preserving and finite in a non-JIT smoke
    forecast.
  - Add registry coverage.

## Expected Metric Movement

- Expected improvements:
  - `10m_u_component_of_wind` and `geopotential_500` at medium leads if
    nonlinear/filter splitting error contributes to phase or amplitude drift.
  - Primary score may improve modestly without spending guardrail margin on a
    stronger damping curve.
- Expected neutral metrics:
  - Early `2m_temperature` and MSLP should be close to neutral because no
    physical forcing, initialization, or diagnostic output path changes.
- Possible regressions:
  - If the current post-step filter placement is empirically compensating for
    nonlinear errors, symmetric placement may be slightly worse.
  - The effect size may be too small to clear the iteration promotion threshold.

## Risks

- Numerical stability:
  - Low to moderate. Total diffusion strength is unchanged, but pre-filtering
    can alter nonlinear tendency inputs.
- Compute cost:
  - Low. One full filter is replaced by two half filters, each a cheap modal
    tree multiplication compared with the spectral dynamics.
- Data leakage:
  - None. No fitted parameters, truth data, validation artifacts, or metric
    changes are used.
- Physical plausibility:
  - Moderate to high as an operator-splitting improvement. It does not claim
    new physics and does not tune diffusion strength.
- Rollback complexity:
  - Low. Remove one split option, one factory/export, one registry entry, and
    focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    diagnostics clean, no early day 1-5 RMSE guardrail failure, and no
    variable+lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean negative or near-zero iteration delta would show that the current
    post-step filter placement is not a material remaining error source. A 10 m
    wind or Z500 guardrail failure would show that moving the same diffusion
    disrupts the accepted balance.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` builds a
  horizontal diffusion step filter and applies it after each IMEX step.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/filtering.py` implements
  horizontal diffusion as an exponential modal scaling, making half-step filter
  composition straightforward to test.
- History: `.logbook/history/2026-06-16_08-53-07_scale-selective-hyperdiffusion/decision.md`
  rejected a changed diffusion curve, so this proposal keeps the incumbent
  diffusion order and timescale.
- History: `.logbook/history/2026-06-17_21-16-05_nonlinear-tendency-exponential-dealiasing/decision.md`
  found a clean but sub-threshold gain from numerical tendency cleanup,
  motivating a similarly narrow but distinct split-order test.
- Strang, G. 1968. On the Construction and Comparison of Difference Schemes.
  SIAM Journal on Numerical Analysis. https://doi.org/10.1137/0705041
- Canuto, C., Hussaini, M. Y., Quarteroni, A., and Zang, T. A. 2007. Spectral
  Methods: Evolution to Complex Geometries and Applications to Fluid Dynamics.
  Springer. https://doi.org/10.1007/978-3-540-30728-0
- Gottlieb, D. and Shu, C.-W. 1997. On the Gibbs Phenomenon and Its Resolution.
  SIAM Review. https://doi.org/10.1137/S0036144596301390

## Researcher Notes

This is not a duplicate of rejected hyperdiffusion, divergence damping, the
600-second inner-step candidate, or staged RK4. It keeps the same total
diffusion operator, same time step, same solver, and same accepted Strang
Coriolis rollout, changing only where the existing diffusion operator sits
within one step. It is intentionally low-to-moderate surface area and uses
prior diffusion failures as evidence against changing damping strength.

## Evaluator Notes

### 2026-06-18T06:07:51Z

Decision: move to `staging`; rank below the DFI-Coriolis consistency proposal.

The proposal is distinct from rejected damping-strength candidates. Source
inspection confirms the incumbent currently builds one horizontal diffusion
step filter and applies it after each SIL3 step, while the filter itself is an
exponential modal scaling, so two half-duration filters should compose to the
same linear damping over a full step. That makes the scientific question
reasonably isolated: split placement relative to nonlinear tendencies, not a
new diffusion curve.

Keep staged rather than ready. Prior diffusion and damping history is mixed to
negative: scale-selective hyperdiffusion failed badly with early 10 m wind
regression, divergence-selective damping was slightly negative, and conservative
nonlinear-tendency dealiasing was clean but sub-threshold. This symmetric
placement is safer than those because total damping is unchanged, but the likely
effect size is smaller than the current Coriolis/DFI mismatch and should wait
behind the top ready idea.

### 2026-06-18T07:28:25Z

Decision: keep in `staging`.

The DFI-Coriolis consistency test has now failed promotion with a clean
`+0.0008926584240389612` iteration delta, so this diffusion-placement idea no
longer sits behind that specific ready item. It is still not the best next
experiment: prior diffusion and damping changes are mostly negative, and the
expected effect of moving the same exponential modal filter into two half
steps is likely smaller than the sigma-native hydrostatic initialization
candidate.

Keep it staged because it remains a clean operator-splitting test that
preserves total linear damping and the accepted Strang Coriolis rollout. If it
is later promoted, DFI should remain on incumbent filter placement for the
first run so the experiment isolates positive-time diffusion ordering.

### 2026-06-18T08:53:53Z

Decision: keep in `staging`.

The new residual, scalar-advection, and sigma-operator proposals do not
duplicate this idea. It remains a clean split-order test because the existing
horizontal diffusion filter is an exponential modal scaling and two half
filters should preserve total linear damping over one step.

The reason it stays staged rather than ready is expected effect size. Prior
diffusion and damping changes are mostly negative or sub-threshold, and this
proposal changes only filter placement relative to the non-Coriolis step. It is
safer than changing diffusion strength, but the ready wind-residual candidate
has a clearer route to moving a scored channel without altering the trajectory.

### 2026-06-18T10:25:42Z

Decision: keep in `staging`; current staged rank 2.

The accepted symmetric Coriolis split is positive evidence that operator
ordering can still matter for this incumbent, and this proposal has a small,
well-isolated surface because the existing horizontal diffusion is an
exponential modal filter whose half steps should compose to the same linear
damping. It also avoids the rejected surface-wind-residual family entirely.

Keep it behind the hypsometric fallback and the ready initialization candidate
because expected effect size is probably small. The DFI-Coriolis consistency
experiment was clean but subthreshold at `+0.0008926584240389612`, and prior
diffusion/damping changes were mostly negative or below promotion. If selected
later, it should continue to isolate positive-time diffusion placement and keep
DFI on the incumbent filter ordering for the first run.

### 2026-06-18T11:49:28Z

Decision: move to `ready`, ready rank 2 behind
`flux-form-surface-pressure-continuity`.

Promote this as the backup ready item because it has the smallest clean
implementation surface among the active staged numerical proposals and is now
supported by accepted split-order evidence: the symmetric Coriolis rotation
split improved both iteration and validation while preserving the fixed
forecast contract. This candidate similarly preserves total linear horizontal
diffusion and tests only positive-time filter ordering around the non-Coriolis
step.

Keep it behind flux-form continuity because prior diffusion and damping
experiments were mostly negative or subthreshold, so the expected effect size
is probably small. If selected, it should keep DFI on incumbent filter
placement and verify that two half filters compose to the full incumbent modal
filter on a static state.

### 2026-06-18T13:22:44Z

Decision: keep in `ready`, ready rank 1 and the strongest current selection.

The `flux-form-surface-pressure-continuity` experiment has now been rejected
with a clean but large negative iteration delta
(`-0.015126833559440334`), so direct surface-pressure continuity/product-rule
corrections should not remain ahead of this split-order test. This proposal
still has mixed prior diffusion evidence, but it preserves total linear
diffusion and changes only positive-time filter placement around the
non-Coriolis step. The accepted symmetric Coriolis split remains positive
evidence that carefully isolated operator ordering can still move this
incumbent without changing physics or output contracts.
