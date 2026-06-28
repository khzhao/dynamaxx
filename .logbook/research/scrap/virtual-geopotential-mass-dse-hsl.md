---
schema_version: 1
slug: virtual-geopotential-mass-dse-hsl
title: Virtual-geopotential dry-static-energy HSL transport for humid-column thickness balance
status: scrap
created_at: 2026-06-24T08:38:37Z
author_role: Researcher
target_model: dino_hsl2_mass_dse
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/
expected_eval_protocols:
  - fixed_fast
  - fixed_iteration
  - fixed_validation
---

## Hypothesis

The accepted mass-DSE incumbent improves thermal transport by advecting a dry-static-energy anomaly, but the hydrostatic thickness part of that scalar is still dry. The rejected moist-static-energy candidate is evidence against adding latent-energy content to the transported scalar, while the output diagnostics still use humidity-aware geopotential when humidity is available. A constrained candidate that uses virtual-temperature geopotential only inside the DSE scalar may improve humid-column thickness consistency without introducing full moist dynamics or latent-energy transport.

## Mechanism

Add a candidate such as `dino_mass_dse_vgeo` derived from `dino_hsl2_mass_dse`.

The candidate would keep the incumbent layer-mass-weighted HSL machinery, displacement estimate, vertical theta transport, and adiabatic terms. The only changed scalar is the mass-weighted horizontal DSE anomaly:

1. Use the model's humidity tracer, when present and finite, to compute a virtual-temperature hydrostatic geopotential diagnostic on sigma levels.
2. Define the transported scalar as `s_vgeo = Cp * T + Phi_virtual`, not `Cp * T_v + Phi_virtual` and not moist static energy. This isolates the density/thickness effect of water vapor in the geopotential term without adding latent heat.
3. Remove the same kind of layer or horizontal mean anomaly as the incumbent DSE path, multiply by sigma-layer pressure thickness, and pass the result through the incumbent HSL transport routine.
4. Divide the transported tendency by safe layer pressure thickness and convert to temperature tendency with the same `/ Cp` conversion used by the accepted incumbent.
5. Fall back to the incumbent dry mass-DSE scalar when humidity is unavailable, outside broad physical bounds, or produces non-finite diagnostics.

This is not a pressure-gradient change. The proposal uses humidity only to define the scalar being horizontally transported in the already accepted mass-DSE branch.

## Implementation Scope

Add one opt-in primitive-equation flag and a side-by-side factory/registry entry. The helper should be localized beside `nodal_dry_static_energy_anomaly`, reusing existing geopotential and humidity utilities rather than adding a new thermodynamic state variable.

Focused tests should verify the dry fallback, finite output with representative humidity, and exact preservation of incumbent behavior when the flag is disabled.

## Expected Metric Movement

The expected upside is a small-to-moderate improvement in `Z500`, `MSLP`, and lower-tropospheric temperature in moist regions where dry hydrostatic thickness and humidity-aware diagnostic thickness diverge. The aggregate improvement is likely smaller than the accepted DSE-HSL step but potentially decorrelated from recent pressure-thickness and vertical-transport failures.

Guardrail risk is real for early `MSLP`, so the iteration review should look at day-1 and day-3 pressure behavior before any validation run.

## Risks

Humidity has been a difficult source of signal in this loop. Moist-static-energy HSL transport was essentially neutral to slightly negative, and bounded virtual-temperature dynamics were strongly negative. This candidate narrows the use of humidity to a diagnostic geopotential term inside an already accepted horizontal transport operator, but it can still perturb mass-pressure balance if the virtual geopotential anomaly is too noisy.

If humidity interpolation or passive humidity drift is the dominant error source, this candidate may add noise rather than useful thickness information. The finite dry fallback and physically broad humidity bounds are required.

## Evaluation Plan

Run fixed fast checks for finite values and shape preservation. Then run fixed iteration against the incumbent and compare the aggregate score, early `MSLP`, `Z500`, and humid-region temperature behavior. Proceed to fixed validation only if the candidate improves iteration score without the short-lead pressure guardrail pattern seen in the rejected vertical-DSE candidate.

Keep all evaluation protocols unchanged.

## Citations

- Wallace, J. M., and P. V. Hobbs, 2006: *Atmospheric Science: An Introductory Survey*, 2nd ed. Academic Press.
- Holton, J. R., and G. J. Hakim, 2013: *An Introduction to Dynamic Meteorology*, 5th ed. Academic Press.
- Simmons, A. J., and D. M. Burridge, 1981: An energy and angular-momentum conserving vertical finite-difference scheme and hybrid vertical coordinates. *Monthly Weather Review*, 109, 758-766. https://doi.org/10.1175/1520-0493(1981)109%3C0758:AEAAMC%3E2.0.CO;2
- Staniforth, A., and J. Cote, 1991: Semi-Lagrangian integration schemes for atmospheric models: A review. *Monthly Weather Review*, 119, 2206-2223. https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2

## Researcher Notes

This is deliberately not a retuned moist-static-energy proposal. The prior `moist-static-energy-hsl-transport` rejection argues against adding latent heat to the transported scalar. The prior virtual-temperature dynamics rejection argues against feeding humidity broadly into the momentum/pressure dynamics. This proposal uses humidity only to compute the hydrostatic geopotential component of the same DSE-like scalar that the incumbent already transports.

I did not find an active duplicate for virtual-geopotential mass-DSE HSL. Staged humidity ideas focus on passive humidity transport or output/geopotential diagnostics, while staged virtual-temperature ideas focus on pressure-gradient or analysis offsets. This proposal is a narrower side-by-side transport-scalar variant of the current incumbent.

## Evaluator Notes

### 2026-06-24T09:35:00Z

Decision: move to `scrap`; rank 3 of 3 new proposals, not recommended.

The proposal is physically recognizable, but the local evidence makes it a poor
use of the next scoring slot and weaker than existing staged humidity ideas.
It would feed passive humidity into the active thermodynamic transport scalar
on every step. That is narrower than full moist dynamics, but it is still an
active humidity-coupled thermal tendency, not merely a diagnostic output
interpretation.

Prior history is unfavorable for this neighborhood. Moist-static-energy HSL
transport was stable but effectively neutral to slightly negative against the
DSE-HSL incumbent, suggesting that adding humidity content to the transported
thermal invariant was not a useful score source. Bounded moist virtual-
temperature dynamics was strongly negative, and the earlier moist dynamics path
failed fast before bounds. The dry-geopotential diagnostic rejection does show
that humidity should remain in pressure-level geopotential output, but that is
evidence for the diagnostic path, not for adding passive humidity to active
DSE transport.

This also competes poorly with safer active staging. `virtual-temperature-
analysis-hs-offset` uses humidity once in a bounded initialization/forcing
offset; mass-DSE pressure-gradient and conservation probes are more directly
tied to the accepted incumbent without reopening moist coupling. The expected
upside here is likely subthreshold, while the main risk is early MSLP/Z500
imbalance from humidity noise in the scalar that drives temperature tendency.
Do not promote unless new diagnostics specifically show a dry-vs-virtual
geopotential mismatch inside the mass-DSE transport, not just in scored output.
