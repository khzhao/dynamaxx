---
schema_version: 1
slug: coupled-surface-residual-vector-decay
title: Coupled Surface Residual Vector Decay
status: ready
created_at: 2026-06-26T07:37:35Z
author_role: Researcher
target_model: dino_hsl2_mass_dse_wtg_vdse_ramp
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

# Coupled Surface Residual Vector Decay

## Hypothesis

The incumbent still carries large negative `2m_temperature` skill at medium and
late leads, while the latest rejected roughness-aware wind diagnostic showed
that a static, wind-only output correction is too narrow. The near-surface
residual correction is nevertheless one of the historically accepted mechanisms
in this model family. A coupled residual-vector decay for `2m_temperature` and
`10m_u_component_of_wind` may preserve useful analyzed boundary-layer regime
information longer without changing the prognostic dycore or repeating the
failed static roughness adjustment.

The physical rationale is that low-level temperature and wind errors are not
independent in stable and weakly mixed boundary layers. Treating the initial
screen-temperature and 10 m wind residuals as a scaled vector can avoid
over-decaying one component while retaining the other, which can otherwise
produce internally inconsistent surface diagnostics.

## Mechanism

Add one side-by-side candidate, for example
`dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec`.

For this candidate only:

- keep the incumbent prognostic trajectory, pressure-ramped vertical-DSE path,
  WTG path, diffusion, DFI, surface heat flux, and output variables unchanged;
- replace only the post-trajectory near-surface residual correction for
  `2m_temperature` and `10m_u_component_of_wind`;
- compute the initial residual vector between raw lead-zero Dinosaur output and
  the input analysis, scaled by fixed physical scales such as 4 K and 4 m/s;
- use the existing lower-column stability proxy to choose a shared decay time
  for the vector amplitude, with stable columns decaying more slowly and
  well-mixed columns decaying faster;
- preserve vector direction during the shared decay, then apply small bounded
  component floors so one component cannot remain persistent after the other is
  effectively gone;
- retain the accepted scale-separated low-mode handling when it is enabled, but
  apply the vector decay within each retained scale band rather than using two
  independent scalar decays;
- fall back exactly to the incumbent residual correction if either residual
  channel, stability proxy, lead hours, scale split, or vector norm is nonfinite.

This proposal is output-only after the trajectory is produced. It should not
alter pressure-level temperature, winds, geopotential, MSLP, surface pressure,
humidity, or any inner-step dynamics.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - focused tests under `tests/dycore/models/dinosaur/`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one model key such as `dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec`.
- API changes:
  - None. `DycoreModel.forecast` and all fixed evaluation outputs are unchanged.
- Tests to update:
  - Verify the candidate factory is incumbent-identical except for the vector
    residual selector and candidate name.
  - Unit-test exact incumbent fallback for missing T2m or U10 channels.
  - Unit-test finite vector decay for synthetic paired residuals.
  - Verify stable-column decay is no faster than well-mixed-column decay.
  - Verify zero vector norm is a no-op and nonfinite vector diagnostics fall
    back to the scalar incumbent correction.
  - Add registry and finite smoke forecast coverage.

## Expected Metric Movement

- Expected improvements:
  - `2m_temperature` from days 3-15 if independent scalar residual decay is
    losing coherent boundary-layer regime information too quickly.
  - `10m_u_component_of_wind` may improve modestly where temperature and wind
    residuals are coupled by stable-layer mixing.
- Expected neutral metrics:
  - `mean_sea_level_pressure` and `geopotential_500` should be almost unchanged
    because the trajectory and pressure-level output path are untouched.
- Possible regressions:
  - U10 can regress if the vector decay preserves wind residuals in regions
    where the latest roughness experiment showed the static correction was
    harmful.
  - T2m can regress if the residual vector locks in an initial analysis
    discrepancy longer than persistence skill supports.

## Risks

- Numerical stability:
  - Low. This is post-trajectory output correction only, with exact incumbent
    fallback.
- Compute cost:
  - Low. It adds elementwise vector algebra and reuses existing residual and
    stability diagnostics.
- Data leakage:
  - Low. The correction uses only the same initial analysis already used by the
    incumbent residual correction, fixed scales, fixed lead times, and model
    trajectory outputs.
- Physical plausibility:
  - Moderate. Coupled surface-layer temperature and wind behavior is physically
    plausible, but this remains a diagnostic residual model rather than a
    prognostic boundary-layer scheme.
- Rollback complexity:
  - Low. Remove one residual-correction helper, one selector, one factory/export,
    one registry entry, and focused tests.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec`.
  - Require finite outputs and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002` against
    the cached incumbent, driven mainly by T2m or a paired T2m/U10 improvement,
    with MSLP and Z500 guardrails clean.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec --workers 4` only after iteration promotion.
- Outcome that would falsify the hypothesis:
  - A clean but subthreshold or negative iteration delta would show that the
    remaining score bottleneck is not independent scalar residual decay. Any U10
    regression resembling the roughness-aware diagnostic rejection would argue
    against further output-only wind-residual work.

## Citations

- Stull, R. B. 1988. *An Introduction to Boundary Layer Meteorology*. Springer.
  https://doi.org/10.1007/978-94-009-3027-8
- Beljaars, A. C. M. and Holtslag, A. A. M. 1991. Flux parameterization over
  land surfaces for atmospheric models. *Journal of Applied Meteorology*.
  https://doi.org/10.1175/1520-0450(1991)030%3C0327:FPOLSF%3E2.0.CO;2
- Monin, A. S. and Obukhov, A. M. 1954. Basic laws of turbulent mixing in the
  surface layer of the atmosphere. *Trudy Geofizicheskogo Instituta AN SSSR*.
- Dynamaxx history:
  `.logbook/history/2026-06-26_04-36-24_roughness-aware-surface-wind-diagnostic/decision.md`
  rejected a static wind-only diagnostic, motivating a coupled residual test
  rather than another roughness proxy.

## Researcher Notes

This proposal is intentionally decorrelated from the recent vertical-DSE
failures: it does not touch temperature tendencies, sigma-dot, DSE, WTG, mass
fields, pressure gradients, or the ramp. It is also distinct from the rejected
roughness-aware surface-wind diagnostic, which used static land/roughness inputs
to alter only U10. This candidate uses the incumbent's already accepted
near-surface residual mechanism, but couples T2m and U10 residual decay through
a bounded vector form.

Active staging contains several surface and residual ideas, including bulk
surface stress, bulk Richardson T2m diagnostics, geostrophic wind residuals, and
stability-bounded residual amplitudes. This proposal differs by leaving the
diagnostic formulas and dynamics alone and changing only the joint temporal
decay of the two accepted near-surface residual channels. Its risk is lower than
a prognostic boundary-layer scheme, but the roughness rejection means U10
movement should be watched closely.

## Evaluator Notes

### 2026-06-26T07:40:57Z

Decision: move to `ready`; ranked 1 of 2 in this proposal triage.

This is the best immediate implementation candidate among the current
proposals. It has the smallest source surface, is output-only after the
trajectory, preserves the incumbent mass, pressure-gradient, WTG, DFI,
vertical-DSE, and pressure-level output paths, and changes only the temporal
handling of two already accepted near-surface residual channels. That makes it
cleaner to implement and roll back than the virtual-geopotential proposal.

The recent roughness-aware wind diagnostic rejection is a caveat but not a
duplicate: that candidate used a static roughness/land-sea wind correction and
finished slightly negative (`-0.00023691303605483105` iteration delta), while
this proposal uses the incumbent residual machinery and couples `2m_temperature`
with `10m_u_component_of_wind` through a bounded shared decay. It is also
distinct from staged residual amplitude caps and one-channel surface
diagnostics because it leaves residual amplitudes and raw diagnostics alone.

Expected upside is concentrated in `2m_temperature`, with possible paired U10
benefit and near-neutral MSLP/Z500. Caveats for implementation: preserve
lead-zero exactness, use fixed physical scales and decay bounds before any
scoring, keep exact incumbent fallback for missing or nonfinite paired channels,
and watch U10 guardrails closely because output-only wind follow-ups have shown
limited aggregate leverage.
