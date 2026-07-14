# 05 — Training: differentiating through the atmosphere without drowning

## The shape of the whole thing

```
window ── encode t0 ──► state₀ ─┐
                                │  24 × 900 s hybrid steps   (scan, remat)
targets ─ encode+decode ──► ŷ₁  ◄─ decode ── state₁ ─┐
                                │            ... K blocks ...
loss = Σ standardized, area-weighted MSE     state_K
grads = jax.value_and_grad(loss)(params)     ← through EVERYTHING
params, moments = adam(params, grads, moments)
```

One jitted function computes loss+grads+update. Params enter the filter
by closure, rebuilt inside the traced function — that is the whole
"how do gradients reach the network" story (chapter 1).

## EX 5a first: the memory arithmetic (paper, 15 minutes)

From your chapter-2 shape safari: bytes per state B = 4 bytes × (3L+1) ×
prod(modal_shape) (plus small change). Naive scan over N=24 steps stores
O(N) states *plus per-step transform intermediates* for the backward
pass; with K=12 windows (3-day horizon) that is O(288) states before
XLA's own working set. Now read `nested_checkpoint_scan`
(`time_integration.py:708`): with `nested_lengths=(6, 4)` the backward
stores ~O(6+4) block boundaries and recomputes inside blocks — memory
O(max(lengths)), cost one extra forward per nesting level. Write the
actual megabyte numbers for T21/L4 and T80/L13 into your notes; then
verify empirically (`jax.profiler.save_device_memory_profile`, or crash
into it once on purpose at T80 on CPU RAM and read the OOM message like a
bill). This arithmetic — not the optimizer — is what decides whether a
3-day curriculum fits one L4.

## EX 5: `rollout.rollout_loss`

The docstring is the contract; the test demands finite, nonzero grads
through 2 windows × 4 tiny-grid steps. Traps worth failing into:

- Rebuild the step function (and NN filter) from `params` INSIDE the
  loss. Build it outside and your gradients are silently zero — the test
  message tells you this because everyone does it once.
- `nested_lengths` must multiply to `inner_steps`. Assert it; a silent
  mismatch reshapes your scan into nonsense.
- Python loop over the K windows (unrolls, K is small), scan inside each
  window (never unroll 24 SIL3 steps — compile times will teach you why
  if you try).
- Accumulate loss as float32 scalars in the carry or per-window list —
  either is fine at K≤12; don't stack decoded fields across windows
  "for later", that is your memory budget walking out the door.

## EX 6: the optimizer you were never allowed to see

`train.adam_update` and `clip_by_global_norm`, each two-or-three
`tree_map`s. The test drives two steps against a NumPy reference — bias
correction with a *traced* step counter is the JAX content here (t = step
+ 1 computed with jnp on an int32 scalar; no Python arithmetic on it
inside jit). When it passes, wrap loss→clip→adam in one `jax.jit` with
`donate_argnums` for (params, moments) and reflect (chapter 1) on why
donation is a no-op at 0.6 MB and existential at 7 GB.

Then, and only then, consider whether you want optax on this branch for
schedules and AdamW — you have now earned the right to a library, and you
will be able to read its source.

## Curriculum: horizons are a schedule, not a setting

`TrainConfig.curriculum = ((0, 1), (1000, 4), (3000, 12))` — one 6 h
window until the loss drops, then 1 day, then 3 days. Why not start long:
early in training the corrector is noise; 288 applications of noise
before the first loss term is variance with no signal ("exposure" — the
model must first survive its own short-horizon corrections). Why not stay
short: 6 h optimization overfits fast processes and learns increments
whose 10-day integral drifts — the precise failure mode the loop's
gray-radiation candidate died of (−0.144 primary from a *late* blowup
that day-1 metrics never saw; that autopsy is
`.logbook/history/2026-07-13_13-48-27_.../decision.md` in the main
worktree — read it, it is the best free lesson this repo has produced).
Expect a loss JUMP at each transition (the objective changed); log
per-horizon losses separately or you will misread every curve.

Shape discipline at transitions: `target_count` changes → new shapes →
one recompile per phase. Three phases, three compiles: fine. A `for k in
range(K)` python loop with K as an untraced per-call value: a compile per
distinct K forever — the loop's dead-candidate recompile story again.

## Stability kit (deploy in this order)

1. Zero-init final layer + fixed output scales (already yours).
2. Gradient clip at 1.0 global norm — rollout gradients through
   near-resonant dynamics have heavy tails; clipping is load-bearing, not
   hygiene.
3. EMA of params (`train.ema_update`, decay 0.999) — evaluate the EMA,
   train the raw; rollout losses are noisy enough that this is ~free
   skill.
4. Warmup+cosine LR (`learning_rate_at`, host-side float argument).
5. If (when) you see slow spectral blowup at long horizons: first
   diagnostic is the increment energy spectrum by layer; first remedies
   are lower output scale or an exponential filter on the increment —
   each is a physics decision; write it down. Your in-filter finite guard
   means a NaN step degrades to "free core step", so NaNs show up as
   *loss plateaus*, not crashes — grep your logs for the guard firing
   (add a `jax.debug.print` counter when you get there).

## NaN forensics, when the plateau comes

`JAX_DEBUG_NANS=1` on the tiny grid reproduces most explosions in
seconds. Bisect horizons (1 window OK? 4? 12?), then bisect steps within
a window by returning early. The usual culprits, in prior probability
order: unit factor applied twice (increments 6 orders too big — check
against the 0.05 K anchor), a `std` of ~0 in your feature stats
(standardize-by-zero), forgetting the guard passes `u_next` (not
`u_prev`) on fallback.

## Running for real (GPU etiquette is binding)

- `train.assert_gpu_is_free()` stays in `main()`. The optimization loop
  runs ~4 h evals on all four L4s at unpredictable times; you train in
  the gaps or not at all. One process per GPU, no fractional sharing —
  house rule (an eval OOM caused by your training job is not a
  hypothetical, it is a -$400 GPU-day and a corrupted candidate score).
- `CUDA_VISIBLE_DEVICES=0 XLA_PYTHON_CLIENT_MEM_FRACTION=0.85 uv run
  python -m dynamaxx.nncorr.train` once wired.
- Throughput calibration from the loop's own artifacts: the fast eval
  advances 14 ICs × 15 days × 96 steps ≈ 20k model-steps in ~430 s on one
  L4 ⇒ ~21 ms/step forward. Training ≈ forward × (1 + backward ≈ 2–3×) ×
  (1 + remat re-forwards) ⇒ a 1-day-horizon update ≈ 8–12 s, a 3-day
  update ≈ 25–40 s. A 5k-step curriculum is a weekend of L4 gaps, not an
  afternoon — plan checkpoint cadence (`checkpoint_every=500` and on
  SIGTERM) so the loop reclaiming its GPUs never costs you more than 500
  steps. Verify these numbers on your first real run and correct this
  paragraph in your notes; estimates that survive contact with hardware
  are the exception.
