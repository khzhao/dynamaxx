# 03 — Designing the corrector (and the exercises that build it)

## What NeuralGCM actually does

Hybrid ODE: `dx/dt = D(x) + NN_θ(x)` — the resolved spectral dynamics `D`
plus a learned physics term, integrated together, trained by
differentiating multi-step rollouts against ERA5 with a horizon
curriculum (hours → days), small-tendency initialization, and heavy use
of remat. The network is deliberately humble: a **single-column** model —
each grid column's profile plus surface/astronomical context in, that
column's tendencies out, identical weights everywhere. All horizontal
structure comes from the dynamics. (Kochkov et al. 2024, arXiv:2311.07222.)

Why column-locality is the right bias, not just a simplification: it
matches the physics being replaced (radiation, boundary-layer turbulence,
convection are ~columnar), it makes parameters resolution-independent
(same weights at T21 and T80 — your cheap-dev/expensive-train workflow
depends on this), and it cannot hallucinate teleconnections — those must
be earned through the dynamics.

## The four design axes, and what we choose here

**1. Where to inject.** Options in this codebase:

- *Post-step state filter* — the `(u_prev, u_next) -> u_next` hook every
  accepted feature uses. Sees the fully stepped, filtered state; additive
  increment; trivially disabled; cannot destabilize the implicit solve
  (it acts after it).
- *Composed explicit tendency* — `time_integration.compose_equations`
  (`time_integration.py:148`) sums your `ExplicitODE.explicit_terms` into
  the equation, so the RK stages integrate the NN output. This is the
  NeuralGCM-faithful choice: corrections enter as physics, get tableau
  weighting and (dis)advantages of stage-coupling. Costs ~3 NN calls per
  step (one per explicit stage) and couples your term into stage
  stability.
- *Learned encoder/decoder corrections* — attack the interpolation error
  at t=0 and output time. Powerful, but changes the forecast contract;
  park it.

We take the filter. It is the repo's native idiom, one NN call per step,
and byte-exact-off. **Extension EX-8 (chapter 6): re-express the same
network as a composed tendency and measure whether stage-integration
matters at 900 s.** Note the subtlety when you do: a filter adds
`tendency × dt` once per step (effectively forward-Euler coupling of the
correction), so the two are NOT algebraically equivalent — that
difference is the experiment.

**2. What to correct.** T, u, v at all layers — yes. Surface pressure —
**no**: a ps increment is direct mass creation/destruction; mass evolution
belongs to continuity, and every hand-crafted feature that touched mass
paths died in the loop's history on drift or guardrails. Tracers — dry
core, nothing to correct. (NeuralGCM likewise corrects prognostics other
than ps.) If you later want the corrector to influence mass, do it the
physical way: through divergence, which you already output.

**3. What the column sees.** State: T(L), u(L), v(L), log(ps/1e5) —
standardized with climatological scalars (chapter 4). Statics: sin/cos of
lat/lon, orography/3000 m, land fraction (`features.static_features`).
Deliberately ABSENT for now: solar zenith (the single highest-value
extension — the radiative-skin accept proves diurnal phase carries real
skill here; `radiation.py` has the machinery, thread the per-sample time
the way `adapter.py:361-403` threads it — as a fixed-shape traced
argument, NOT a Python constant, or you will recompile per sample);
forecast lead time (legal, NeuralGCM omits it; a corrector that depends
on lead is admitting model-error growth it could instead reduce);
boundary-layer Richardson numbers and other derived stabilities (let the
MLP learn them from the raw column — measure later whether hand-features
help).

**4. Output scale and initialization.** The MLP's last layer is
zero-initialized (`mlp.init_mlp_params`): at step 0 the hybrid IS the
free core, bit for bit — the same "exact incumbent fallback" contract the
loop enforces on every candidate, arrived at independently by the hybrid
modeling community because it makes early training a small perturbation
of a stable system. Outputs are multiplied by fixed scales — 5 K/day and
5 (m/s)/day (`corrector.py` constants) — so |NN| ≤ O(1) maps to ≤ ~0.05 K
per 900 s step. Compare `_OCEAN_BULK_SHF_MAX_STEP_TEMPERATURE_INCREMENT_
KELVIN = 0.05` and the 0.25 m/s Ekman cap in `adapter.py:81,115`: the
loop's hand-tuned caps and your output scale are the same number because
it is the increment size this dycore is known to absorb. Fixed, not
learned: an optimizer that can raise its own output gain will do so the
moment it helps the short-horizon loss, then explode the long one.

**Spectral hygiene.** Nodal→modal of a pointwise NN output aliases; the
transforms clip to the truncation (`si_increments_to_modal` calls
`grid.clip_wavenumbers`, `spherical_harmonic.py:1035`), matching the
encode path. If trained increments come out high-wavenumber-heavy
(diagnose: energy spectrum of increments vs. layer), borrow the
`exponential_step_filter` (`time_integration.py:562`) as an extra smoother
— but measure first.

## Parameter budget

Spec: F = 3L+7 features, three hidden layers of 256, output 3L. At L=13:
F=46, output 39 → 46·256 + 256·256·2 + 256·39 + biases ≈ **0.16 M
params**, ~0.6 MB float32. Resolution-independent. For calibration,
NeuralGCM's learned physics is orders of magnitude larger — you are
deliberately starting at the small end where training is cheap and every
failure is legible. Compute the exact count in your head before calling
`mlp.parameter_count`; being able to do that arithmetic instantly is a
prerequisite for the chapter-5 memory math.

## The exercises

Read the docstring contracts first — they are the real spec; tests are
the acceptance criteria. Recommended order:

- **EX 1 `mlp.mlp_apply`** (`src/dynamaxx/nncorr/mlp.py`). Matmul on the
  trailing axis, gelu between, final affine. The test compares against a
  NumPy reference including the tanh-gelu — if you are off by ~1e-3
  everywhere, you used the erf gelu; read `jax.nn.gelu`'s signature.
- **EX 2 `features.assemble_features`**. Axis discipline: `[L,lon,lat]`
  blocks → `[lon,lat,F]`, standardize state blocks, log-ratio the
  pressure, concatenate statics unmodified. The test pins the exact
  feature order — so will your checkpoint's compatibility with chapter 6.
- **EX 3 `corrector.corrector_increments`**. Chain decode → features →
  MLP → split/moveaxis → scale by tendency-scale × Δt → modal. Then run
  the identity test and understand *why* it can demand bit-exactness:
  zero params ⇒ the MLP output is exactly 0.0 (not tiny — exactly), the
  scaled increments are exact zeros, transforms of zeros are zeros, and
  `x + 0.0` is exact in IEEE. Every link in that argument is a design
  decision you now recognize.

Checkpoint questions (answer before chapter 4 — to yourself, precisely):

1. Why does the corrector run on `u_next` and not `u_prev`? What would
   change if it ran on both (hint: what does `(u_prev, u_next)` give the
   hyperdiffusion filter that a state filter doesn't need)?
2. Your increments pass through `clip_wavenumbers`. The NN also *reads*
   nodal fields synthesized from clipped spectra. Where exactly can
   gridpoint-scale information still leak into the corrector's view, and
   why is that harmless here?
3. The 0.05 K/step anchor: derive what |NN output| would be needed to
   heat a column 5 K over day 6-to-15 (the late window the loop's
   features exploit). Is the scale generous or tight for a "learned land
   skin"?
