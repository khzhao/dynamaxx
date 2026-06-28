---
schema_version: 1
slug: passive-humidity-dfi-bypass
title: Preserve Passive Humidity Through Dry Digital Filter Initialization
status: ready
created_at: 2026-06-17T10:10:34Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init
expected_code_paths:
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

# Preserve Passive Humidity Through Dry Digital Filter Initialization

## Hypothesis

The incumbent is dynamically dry: `use_humidity_in_dynamics=False`, and the
weak Held-Suarez forcing is thermal-only. However, when pressure-level specific
humidity channels exist, the adapter still carries humidity as a passive tracer
and later uses it in virtual-temperature hydrostatic geopotential diagnostics.
The latest dry-consistent geopotential diagnostic rejection showed that removing
humidity from geopotential reconstruction damages day-1 Z500, so the passive
moisture diagnostic pathway is useful even though the dynamics are dry.

Digital filter initialization is meant to reduce high-frequency imbalance in
mass, wind, and temperature. Filtering passive humidity with the dry reversible
dynamics may unnecessarily diffuse or phase-shift the moisture field used only
for diagnostics, without improving dynamical balance. Preserving the incumbent
log-pressure-remapped passive humidity through DFI, while still DFI-filtering
vorticity, divergence, temperature, and log surface pressure, should protect the
useful analyzed moisture structure that feeds Z500 diagnostics without
reviving moist virtual-temperature dynamics.

## Mechanism

Register a side-by-side model such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass`.
Preserve all incumbent behavior except the DFI treatment of passive tracers.

During trajectory construction with DFI enabled:

- build the same initial Dinosaur state as the incumbent, including
  log-pressure-remapped passive humidity when available;
- apply the existing digital filter initializer to the state;
- if `use_humidity_in_dynamics=False`, replace only the filtered
  `specific_humidity` tracer leaf with the unfiltered initialized tracer from
  the pre-DFI state;
- leave vorticity, divergence, temperature variation, log surface pressure,
  DFI weights, filters, weak-HS relaxation, near-surface residuals, output
  interpolation, and all lead/output contracts unchanged.

Do not floor, clip, residual-correct, or retune humidity. This is a DFI
partitioning experiment for a passive diagnostic tracer, not a positivity
limiter or a moist-dynamics candidate.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add only
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass`.
- API changes:
  - None. Forecast inputs, outputs, target variables, lead times, and metrics
    remain unchanged.
- Tests to update:
  - Unit-test a helper that restores only `specific_humidity` from an unfiltered
    state while preserving filtered dynamic fields.
  - Verify the bypass is inactive when humidity is absent or
    `use_humidity_in_dynamics=True`.
  - Verify the candidate factory preserves the incumbent DFI span, weak-HS
    settings, log-pressure initialization, hydrostatic layer initialization, and
    near-surface residual correction.
  - Add registry coverage and a finite no-JIT smoke forecast with humidity
    channels if existing fixtures support it.

## Expected Metric Movement

- Expected improvements:
  - `geopotential_500` at short and medium leads if DFI currently distorts the
    passive humidity field used for virtual-temperature geopotential
    reconstruction.
  - Primary score may improve modestly without touching near-surface residuals
    or pressure-level temperature/wind output diagnostics directly.
- Expected neutral metrics:
  - `2m_temperature`, `10m_u_component_of_wind`, and MSLP should remain close to
    incumbent because the dry dynamic state after DFI is unchanged.
- Possible regressions:
  - The DFI-filtered dry mass/temperature state and unfiltered humidity tracer
    may be slightly less mutually consistent for hydrostatic virtual-temperature
    diagnostics.
  - If passive humidity DFI movement is already tiny, the candidate may be
    guardrail-clean but below the fixed primary threshold.

## Risks

- Numerical stability:
  - Low. The bypass changes the initial passive tracer only and does not feed
    moisture into the dry prognostic tendencies.
- Compute cost:
  - Low. It adds one pytree tracer replacement after initialization.
- Data leakage:
  - Low. It uses only same-time initialized fields already present in the
    incumbent state, and no target residuals, validation statistics, or future
    truth.
- Physical plausibility:
  - Moderate. It is defensible because DFI targets dynamical imbalance, while
    this humidity tracer is passive and diagnostic-only for the incumbent. The
    risk is that passive moisture should still be materially consistent with
    the filtered thermal field.
- Rollback complexity:
  - Low. The change can be isolated behind one adapter flag and one side-by-side
    factory.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`,
    clean diagnostics, no fixed RMSE guardrail failure, and improvement or
    neutrality in short-lead `geopotential_500`.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A clean near-zero iteration delta would show passive humidity DFI movement is
    not a meaningful remaining error source. Any short-lead Z500 guardrail
    failure would show that filtered humidity is more consistent with the
    filtered dry state than the unfiltered passive tracer.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/adapter.py` carries
  `specific_humidity` as a tracer when available while the incumbent keeps
  `use_humidity_in_dynamics=False`.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/time_integration.py`
  implements DFI as a tree-wide weighted average of forward and backward
  trajectories, so tracer leaves are filtered along with dynamical variables.
- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  uses specific humidity in `get_geopotential_on_sigma` through virtual
  temperature during output diagnostics.
- History: `.logbook/history/2026-06-16_21-13-22_passive-humidity-positivity-limiter/decision.md`
  rejected a diagnostic-time humidity floor with delta
  `-0.0000019440828125105725`; this proposal does not floor or clip humidity.
- History: `.logbook/history/2026-06-17_09-10-51_dry-consistent-geopotential-diagnostic/decision.md`
  rejected removing humidity from geopotential diagnostics after a 24 h Z500
  guardrail failure of `+19.566144167188776%`.
- Lynch, P. and Huang, X.-Y. 1992. Initialization of the HIRLAM Model Using a
  Digital Filter. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(1992)120%3C1019:IOTHMU%3E2.0.CO;2
- Peckham, S. E. et al. 2016. Implementation of a Digital Filter
  Initialization in the WRF Model and Its Application in the Rapid Refresh.
  Monthly Weather Review. https://doi.org/10.1175/MWR-D-15-0219.1
- Dee, D. P. and da Silva, A. M. 2003. The Choice of Variable for Atmospheric
  Moisture Analysis. Monthly Weather Review.
  https://doi.org/10.1175/1520-0493(2003)131%3C0155:TCOVFA%3E2.0.CO;2

## Researcher Notes

This is not a duplicate of rejected moist virtual-temperature dynamics. Moist
dynamics fed humidity back into vorticity, divergence, and temperature
tendencies and failed the fast gate with nonfinite forecasts. This proposal
keeps `use_humidity_in_dynamics=False` and changes only the post-DFI initial
passive tracer leaf.

It is also not the rejected passive-humidity positivity limiter, which applied a
diagnostic-time nonnegative floor and produced essentially zero score movement.
Here the mechanism is preservation of analyzed passive moisture structure
through a dry balance filter, motivated by the later evidence that humidity in
geopotential diagnostics is valuable. It is decorrelated from the
potential-temperature proposal because it does not alter initialized
temperature, winds, pressure, DFI weights, or thermodynamic interpolation.

## Evaluator Notes

2026-06-17T10:13:20Z - Move to `staging`; rank 2 of 5 active ideas.

This is a plausible follow-up but not the next ready candidate. The latest
dry-consistent geopotential diagnostic rejection is strong evidence that the
passive humidity diagnostic path should be preserved: removing humidity from
geopotential reconstruction regressed day-1 `geopotential_500` RMSE by
`+19.566144167188776%` and failed the variable+lead guardrail. Source inspection
also supports the proposed implementation: the adapter carries
`specific_humidity` as a tracer when available, calls DFI as a tree-wide
weighted state average, and later uses tracer humidity in
`get_geopotential_on_sigma` for virtual-temperature geopotential diagnostics.

The reason to stage rather than ready is effect-size and consistency
uncertainty. The rejected passive-humidity positivity limiter produced a clean
but essentially zero iteration delta of `-0.0000019440828125105725`, showing
that not every passive humidity diagnostic tweak matters. The rejected moist
virtual-temperature dynamics candidate failed the fast gate with nonfinite
forecasts, so humidity must remain out of dry tendencies. This proposal respects
that boundary, but restoring an unfiltered humidity tracer after filtering mass
and temperature may make the virtual-temperature diagnostic less balanced with
the DFI-adjusted dry state.

Keep this staged as the strongest fallback after potential-temperature
initialization. If promoted later, require a side-by-side factory, no clipping
or humidity retuning, bypass only when `use_humidity_in_dynamics=False`, and
strict short-lead Z500 guardrail scrutiny.

2026-06-17T11:23:24Z - Keep in `staging`; rank 2 of 6 active ideas.

The potential-temperature initialization candidate has now failed cleanly with
iteration delta `-0.0009134462392161868`, so this proposal becomes the strongest
fallback after the ready thermal limiter. The theta-init result lowers the rank
of additional thermodynamic-remap variants because its loss was broad and
guardrail-clean, while this humidity proposal changes a different pathway:
post-DFI treatment of a passive diagnostic tracer.

The evidence remains mixed enough to stage rather than ready. The
dry-consistent geopotential diagnostic rejection showed that humidity in
virtual-temperature geopotential diagnostics is important, with a day-1
`geopotential_500` guardrail failure when humidity was removed. Local source
also confirms DFI is a tree-wide state average and that `specific_humidity` can
be carried as a tracer while dry dynamics keep `use_humidity_in_dynamics=False`.
However, the earlier passive humidity positivity limiter produced essentially
zero score movement, and restoring unfiltered humidity after filtering mass and
temperature may reduce diagnostic consistency. If the ready thermal limiter
fails or is rejected, promote this as the next low-risk implementation target
with strict constraints: replace only the `specific_humidity` tracer leaf after
DFI, only for dry dynamics, with no clipping, floors, retuning, or metric
changes.

2026-06-17T12:28:50Z - Move to `ready`; rank 1 of 5 active staged ideas.

The ready queue is empty after two clean but negative iteration results:
`potential-temperature-logp-initialization` regressed primary by
`-0.0009134462392161868`, and `low-level-sparing-thermal-drift-limiter`
regressed primary by `-0.001517601128549373`. Those failures weaken additional
thermodynamic remap and thermal-drift controls for the next implementation.
Earlier pressure/remap experiments also remain risky, and the dry-consistent
geopotential diagnostic failure still provides the clearest actionable evidence:
removing passive humidity from virtual-temperature geopotential diagnostics
caused a short-lead `geopotential_500` guardrail failure of
`+19.566144167188776%`.

Promote this proposal as the sole ready candidate because it targets that
evidence without changing the forecast contract, the dry dynamic tendencies,
temperature initialization, pressure remapping, near-surface outputs, or fixed
evaluation protocols. The likely effect size is uncertain, but the
implementation is small, reversible, and scientifically distinct from the
recent failed thermal and pressure-coordinate families.

Implementation constraints for the selected candidate are strict: add a
side-by-side model only; bypass only passive `specific_humidity` after DFI when
`use_humidity_in_dynamics=False`; do not clip, floor, retune, or residual-correct
humidity; preserve dry dynamics, DFI weights, weak-HS forcing, near-surface
residuals, pressure/output paths, target variables, and the output contract;
and scrutinize short-lead `geopotential_500` before any promotion to
validation.
