# 02 — Anatomy of the dycore you are about to correct

Everything below cites file:line in THIS worktree (pinned at commit
`7174848c`), so the anchors are stable. Read with the files open. The goal
is fluency in exactly the paths your corrector touches: state, transforms,
units, the step, the filter hook.

## The prognostic state

`primitive_equations.State` (`primitive_equations.py:76`):

```
vorticity              [L, *modal]   ζ, spectral
divergence             [L, *modal]   δ, spectral
temperature_variation  [L, *modal]   T − T_ref(layer), spectral
log_surface_pressure   [1, *modal]   ln p_s, spectral
tracers                dict          ADVECTED — never park state here
sim_time               scalar        model time, nondimensional
```

Five things to internalize:

- **It is spectral.** Fields live as real spherical-harmonic coefficients;
  physical-space ("nodal") views are produced on demand by
  `grid.to_nodal`. Production: T80 truncation on a 240×121
  equiangular-with-poles grid, L = 13 equidistant sigma layers mirroring
  the 13 ERA5 pressure levels (50…1000 hPa).
- **Winds are not state.** ζ/δ are; velocities come from
  `spherical_harmonic.vor_div_to_uv_nodal` (`spherical_harmonic.py:1184`),
  its inverse `uv_nodal_to_vor_div_modal` (`:1168`) is how your wind
  increments get back in. Both handle the cos-latitude weighting for you —
  do not add your own.
- **Temperature is an anomaly** about the per-layer reference
  (`adapter._reference_temperature`, `adapter.py:5699` — constant 250 K in
  this lineage). Decoding must add it back; encoding subtracts it.
- **Tracers are advected.** ERA5 humidity rides along as a passive tracer
  in production runs. The optimization loop's protocol screams about this
  for a reason: any per-column memory you are tempted to stash in
  `tracers` will be transported by the flow next step. Auxiliary state
  that must NOT advect lives outside `State` as an augmented scan carry —
  see the land-skin reservoir wiring at `adapter.py:752-776`.
- **`sim_time` is nondimensional model time**; the accepted features'
  ramps branch on it (`_land_skin_reservoir_forecast_time_ramp`,
  `adapter.py:2531` — exactly 0 through 120 h). Your corrector ignores
  time; keep passing `sim_time` through untouched.

Exercise (shape safari, 15 min): with the tiny fixture from
`tests/nncorr/conftest.py`, print `grid.nodal_shape`, `grid.modal_shape`,
every State leaf shape and dtype, and compute the total float count of one
T80/L13 state (build one with `data.build_grid_bundle()` if the dataset is
mounted — metadata only, no heavy reads). You need these numbers cold for
the chapter-5 memory math.

## Units: everything inside is nondimensional

`units.SimUnits.from_si()` defines the scaling; the adapter's idiom is
`_unit_factor(physics_specs, "kelvin")` (`adapter.py:6242`) — the
SI→nondimensional multiplier for that unit. Multiply to enter the model,
divide to leave. Time uses `_nondimensionalize_seconds` (`:6193`).
`corrector.decode_nodal_si` and `si_increments_to_modal` in this package
are the worked examples; every unit bug you will ever write here is one of
(forgot the factor, applied it twice, wrong direction). The tests catch
the T-scale ones; wind bugs show up as a corrector that trains but
saturates — remember that when it happens.

## The step: IMEX SIL3

The equation object is built by `_primitive_equation` (`adapter.py:5876`)
— an `ImplicitExplicitODE` (`time_integration.py:76`): fast linear
gravity-wave terms are implicit, advection and everything slow explicit.
`imex_rk_sil3(equation, dt, implicit_offcentering=0.05)`
(`time_integration.py:493`, tableau from Whitaker & Kar 2013) gives the
900 s step; the off-centered variant is wrapped in a nonfinite-guarded
fallback to the centered one (`:467`) — note the pattern, it is the same
finite-guard-with-fallback you ship in your filter.

You never modify any of this. The hybrid-model literature's lesson (and
NeuralGCM's) is that the network should not have to relearn integration.

## The hook: step filters

`step_with_filters(step_fn, filters)` (`time_integration.py:628`):

```python
u_next = step_fn(u)
for f in filters: u_next = f(u, u_next)     # signature (u_prev, u_next)
```

Filters run in order, each seeing the previous one's output. The free core
uses one: order-2 spectral hyperdiffusion
(`adapter._horizontal_diffusion_step_filter`, `adapter.py:6171`, with a
resolution-scaled default tau). **Your corrector is appended after it** —
`rollout.build_step_fn` in this package shows the three-line assembly.

## The hand-crafted corrector zoo (know your competition)

The incumbent `dino_rskin_apv` is the free core plus, roughly in order of
acceptance: scale-separated near-surface residual memory, analysis-offset
Held–Suarez equilibrium, ocean bulk sensible heat flux
(`adapter.py:6078`), semi-Lagrangian theta/DSE transport, tropical WTG
relaxation (`:1184`), coupled Ekman stress+pumping (`:1331`), orographic
lift (`:2559`), terrain-work drag heating (`:2801`), the late-ramped
land-skin reservoir with analyzed-T2m init and zero-mean radiative energy
(`:1943-2450`), Richardson screen-level observers (`:4253`, `:4753`), and
the anticipated-PV momentum flux. Skim three of them end to end — WTG,
Ekman, land-skin — and notice the shared skeleton your filter copies:

1. compute a bounded increment from the current state (+ static fields),
2. hard per-step caps ~0.05 K / 0.25 m/s,
3. exact-fallback (`jnp.where`) to the untouched state on any invalid
   input,
4. ramps that make early forecasts bit-exact with the parent model.

Your NN replaces the zoo's *hand-derived* increments with a learned one —
over the *free* core, so the comparison in chapter 6 is honest: 30 years
of ERA5 + one MLP vs. weeks of automated hand-crafting.

## In and out of the model

- Encode: `weather_state_to_dinosaur_state` (`adapter.py:3927`) — packed
  `[channel, lon, lat]` analysis → pressure-to-sigma interpolation (the
  incumbent lineage uses log-pressure + layer-mean hydrostatic init; the
  tutorial's `data.encode_analysis` matches) → spectral clip.
- Decode: `dinosaur_state_to_weather_state` (`adapter.py:4062`) — back to
  pressure levels and surface channels for scoring.
- Trajectories: `trajectory_from_step` (`time_integration.py:658`), inner
  scan = 24 × 900 s between outputs, outer scan over 6 h frames. DFI
  (`:811`) filters the initial state in production lineages; the tutorial
  core skips it (one fewer moving part; revisit as an extension when your
  day-1 scores look noisy).

## The judge

`uv run dynamaxx-eval <protocol> --model <name>` scores registered models
(`src/dynamaxx/dycore/registry.py`) on ERA5 at leads 1–15 d for T2m,
MSLP, Z500, U10; primary = mean skill vs persistence over all 60
variable×lead records (each variable therefore moves primary by ~Δ/4).
Protocols and their init years: `src/dynamaxx/eval/protocols.py:114-147`.
Chapter 6 wires your checkpoint into the registry and runs `fast`.
