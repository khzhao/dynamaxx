---
schema_version: 1
slug: momentum-only-sl-vertical-advection
title: Momentum-only semi-Lagrangian vertical advection
status: ready
created_at: 2026-06-28T02:51:54Z
author_role: Researcher
target_model: dinosaur
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

## Hypothesis

Replace only the vertical-advection contribution to horizontal momentum in the Dinosaur primitive-equation tendency with a conservative, bounded semi-Lagrangian vertical remap. Leave scalar, thermal, mass, humidity, WTG, T2m diagnostic, and output contracts unchanged.

The current incumbent already carries a good low-surface-area set of mass/DSE/WTG/vertical-DSE/T2m-memory/Richardson-T2m changes. This proposal targets a different failure channel: phase and amplitude errors in vertically sheared horizontal wind as `sigma_dot_full` advects `u` and `v` through the column. Cleaner vertical momentum transport should primarily affect U10 and balanced mass fields through the vorticity/divergence tendency, with T2m affected only through the evolved boundary-layer state rather than a final-output blend.

## Mechanism

`PrimitiveEquationsSigma.curl_and_div_tendencies` currently forms the vertical momentum terms as centered tendencies:

```python
sigma_dot_u = -self._vertical_tendency(d_sigma_dt, u)
sigma_dot_v = -self._vertical_tendency(d_sigma_dt, v)
```

Those terms feed the nodal momentum tendency before conversion back to curl/divergence. When vertical Courant numbers or vertical shear are locally large, centered vertical advection can create oscillatory shear errors that project into near-surface wind, divergence, and ultimately MSLP/Z500 evolution. This is distinct from the latest rejected lower-tropospheric air-mass T2m diagnostic, because it changes the dynamical rollout before forecast outputs are diagnosed.

The proposed mechanism is to compute a bounded vertical departure point for the horizontal wind components only, remap `u` and `v` along the sigma column, and use the remapped-minus-current wind as the vertical-momentum tendency. Scalar, thermal, mass, humidity, WTG, residual-memory, and output-diagnostic paths remain incumbent-equivalent.

## Implementation Scope

1. Add a Dinosaur model option, for example `use_momentum_only_semi_lagrangian_vertical_advection`, defaulting to `False`.
2. In `PrimitiveEquationsSigma.curl_and_div_tendencies`, branch only the `sigma_dot_u` and `sigma_dot_v` calculation when `include_vertical_advection` is enabled.
3. Compute a one-step vertical departure point for each sigma level using the existing `aux_state.sigma_dot_full`, the model timestep, and the native sigma-coordinate layer positions.
4. Interpolate `u` and `v` from the departure sigma positions back to arrival levels with a monotone or bounded column interpolation. Clamp departure points to the valid vertical domain and use the incumbent centered tendency as a fallback for non-finite values or excessive displacement.
5. Convert the remap into a tendency contribution:

   ```python
   semi_lagrangian_tendency = (remapped_wind - wind) / dt
   ```

   and substitute this for the current centered vertical-advection tendency only for horizontal wind.
6. Preserve all incumbent settings in the candidate factory derived from `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`, including HSL/DSE/WTG/vertical-DSE/T2m-memory/Richardson-T2m behavior.

Implementation should avoid a full new transport framework. The narrowest acceptable version is a helper that remaps one column field along sigma using existing Dinosaur coordinate arrays and JAX vectorization.

## Expected Metric Movement

- U10 should improve if vertical shear noise is currently contaminating near-surface momentum and Richardson-layer diagnostics.
- MSLP and Z500 may improve through cleaner vorticity/divergence tendencies and reduced spurious gravity-wave excitation.
- T2m should be mostly neutral to mildly positive through real boundary-layer state evolution. It should not resemble the rejected final-output lower-tropospheric T2m blend.

The expected gain is modest but plausible: an iteration improvement on the order of `+0.002` to `+0.006` if U10 and pressure fields benefit without reopening T2m regressions.

## Risks

- First-order semi-Lagrangian remap can be overly diffusive in strong shear and may degrade U10 extremes.
- Boundary clamping near the top or surface could introduce systematic wind bias if not conservative enough.
- If the current vertical momentum tendency is already well controlled by other filters, the change may be near-neutral while adding implementation complexity.
- A badly chosen displacement cap could hide the mechanism or create discontinuities.

## Evaluation Plan

Run the fixed protocols unchanged:

1. `fast` smoke/evaluation for non-finite checks, runtime, and obvious field regressions.
2. `iteration` with the standard worker count, keeping all splits, metrics, target variables, and golden data unchanged.
3. Promote to `validation` only if iteration beats the incumbent with no severe component regression.

Falsify the proposal if iteration is non-positive, if U10 worsens enough to explain a negative delta, or if T2m degrades in a way that suggests boundary-layer wind changes are destabilizing the existing Richardson-T2m diagnostic.

## Citations

- Dynamaxx source: `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` forms vertical momentum terms in `PrimitiveEquationsSigma.curl_and_div_tendencies` from `sigma_dot_full` and `_vertical_tendency`.
- Dynamaxx scrap: `.logbook/research/scrap/semi-lagrangian-vertical-transport.md` rejected a broad full-state operator-split remap; this proposal is restricted to horizontal momentum in the existing tendency path.
- Dynamaxx staging: `vertical-courant-limited-advection`, `upwind-vertical-advection-rollout`, `theta-upwind-vertical-advection`, `passive-humidity-upwind-vertical-transport`, and `smoothed-sigma-dot-vertical-advection` record related but broader or scalar/tracer-focused vertical-transport alternatives.
- Staniforth, A. and Cote, J. 1991. "Semi-Lagrangian Integration Schemes for Atmospheric Models: A Review." Monthly Weather Review. https://doi.org/10.1175/1520-0493(1991)119%3C2206:SLISFA%3E2.0.CO;2
- ECMWF. 2021. IFS Documentation CY47R3, Part III: Dynamics and Numerical Procedures. https://www.ecmwf.int/en/elibrary/81270-ifs-documentation-cy47r3-part-iii-dynamics-and-numerical-procedures
- Lin, S.-J. and Rood, R. B. 1996. "Multidimensional Flux-Form Semi-Lagrangian Transport Schemes." Monthly Weather Review. https://doi.org/10.1175/1520-0493(1996)124%3C2046:MFFSLT%3E2.0.CO;2

## Duplicate Check

This is not a duplicate of the staged or scrapped vertical-transport proposals:

- `.logbook/research/scrap/semi-lagrangian-vertical-transport.md` was a broader state-transport idea; this proposal changes only horizontal momentum vertical advection inside `curl_and_div_tendencies`.
- `vertical-courant-limited-advection`, `upwind-vertical-advection-rollout`, `theta-upwind-vertical-advection`, and `passive-humidity-upwind-vertical-transport` target scalar/full-state or Courant-limited incumbent operators rather than a momentum-only semi-Lagrangian remap.
- `smoothed-sigma-dot-vertical-advection` changes the diagnosed vertical velocity signal; this keeps `sigma_dot_full` unchanged and changes only how momentum follows it.
- `richardson-momentum-mixing` and `richardson-column-momentum-mixing` are turbulent mixing proposals, not replacement of the resolved vertical advection term.

## Researcher Notes

The latest rejected experiment is negative evidence against more final-output T2m blends. This candidate deliberately avoids posthoc T2m shaping and changes a dynamical tendency that can affect U10/MSLP/Z500 before diagnostics are produced. The surface area is limited to one primitive-equation branch and one registry candidate.

## Evaluator Notes

### 2026-06-28T02:56:36Z

Decision: move to `ready`; ranked first among this triage batch.

I repaired the proposal headings to satisfy the protocol body schema without changing the scientific idea: `Summary` became `Hypothesis`, `Motivation` became `Mechanism`, `Proposed Implementation` became `Implementation Scope`, `Expected Outcomes` became `Expected Metric Movement`, and a standalone `Citations` section was added from the existing references.

Promote only this proposal because it is the narrower of the two new non-output-only ideas. It changes one resolved-dynamics branch, the vertical momentum contribution inside `PrimitiveEquationsSigma.curl_and_div_tendencies`, while leaving scalar transport, DFI, filters, residual-memory output diagnostics, the WeatherState contract, and fixed protocols unchanged. Source inspection confirms the current momentum terms are localized as `sigma_dot_u` and `sigma_dot_v`, so a side-by-side guarded helper is plausible.

This is not risk-free. Active staged vertical-advection ideas and the scrapped full-state semi-Lagrangian vertical-transport proposal show that vertical numerics are a low-priority family unless the change is materially narrower. The latest history also argues against final-output T2m shaping. This proposal clears that bar because it is momentum-only and targets U10/MSLP/Z500 through rollout dynamics rather than a T2m blend. If implemented, keep the displacement cap and fallback fixed before scoring, and require tests proving scalar/thermal/mass/humidity paths are incumbent-equivalent when the option is disabled.
