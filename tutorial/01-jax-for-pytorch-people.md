# 01 — JAX for PyTorch people

You know PyTorch. The translation is not syntactic — it is a different
execution model, and fighting it produces the five classic bugs listed at
the end. Read this with a REPL open (`JAX_PLATFORMS=cpu uv run python`).

## The mental model

PyTorch: objects with state (`nn.Module`, optimizer, RNG), eager kernels,
autograd tape recorded as you go.

JAX: **pure functions over pytrees of arrays, transformed**. You write
`f(params, x)`; you get derivatives with `jax.grad(f)`, compilation with
`jax.jit(f)`, batching with `jax.vmap(f)`, loops with `jax.lax.scan`.
Transformations compose: `jit(grad(vmap(f)))` is ordinary code here. There
is no tape: `grad` traces your function symbolically and builds the
adjoint program. There are no in-place ops: every "mutation" returns a new
array (`x.at[3].set(v)`), and XLA makes it cheap by buffer reuse.

State — parameters, optimizer moments, PRNG — is *threaded explicitly
through function signatures*. What PyTorch hides in `self`, JAX makes an
argument and a return value. This is why the training step you will write
in chapter 5 has the shape

```python
params, moments = update(params, moments, batch, step)   # nothing mutates
```

## Tracing and jit — where PyTorch intuition breaks first

`jax.jit(f)` does not run `f` on your arrays. It runs `f` ONCE on abstract
tracers that carry only shape and dtype, records every jnp operation into
a graph, compiles it with XLA, and caches the compiled program keyed by
the (shape, dtype, pytree-structure) signature of the inputs.
Consequences:

- Python control flow on *traced values* is illegal (`if x > 0:` raises a
  `TracerBoolConversionError`). Use `jnp.where`, `lax.cond`, `lax.scan`.
  Python control flow on *static* values (layer counts, flags) is fine —
  it simply unrolls into the traced graph.
- New input shapes ⇒ silent recompilation. This is not academic: the
  optimization loop **lost a full candidate** (`topographic-solar-
  exposure-tendency`) because a per-initial-time Python value leaked into
  trajectory construction and every sample recompiled a multi-minute
  program. The fix pattern is in `adapter.py` around line 361: per-sample
  scalars enter as *fixed-shape traced arguments*
  (`radiative_trajectory_arguments`), never as Python constants.
- Printing inside jit prints tracers. Use `jax.debug.print("x={x}", x=x)`.

Probe it (do these, actually):

```python
import jax, jax.numpy as jnp
@jax.jit
def f(x):
    print("TRACING", x)          # runs once per signature
    return jnp.where(x > 0, x, -x)
f(jnp.arange(3.)); f(jnp.arange(3.) + 1)   # no retrace
f(jnp.arange(4.))                          # retrace: new shape
```

## Pytrees — the universal container

Any nested structure of dicts/lists/tuples/dataclasses-registered types
with array leaves. `params` in this tutorial is `list[dict[str, Array]]`.
The dycore state (`primitive_equations.State`,
`primitive_equations.py:76`) is a pytree via `@tree_math.struct`; the
repo's `WeatherState` (`src/dynamaxx/weather.py:12`) registers itself
manually with `tree_flatten`/`tree_unflatten` — read both, they are the
two idioms you will meet. Everything — jit, grad, scan carries, optimizer
states — operates on pytrees; `jax.tree_util.tree_map(f, tree, tree2)` is
the workhorse (your Adam in EX 6 is two `tree_map`s).

## Randomness

No global seed. `key = jax.random.PRNGKey(0)`; every draw consumes a key;
`jax.random.split(key, n)` derives independent ones. Reusing a key reuses
the randomness — deterministic by construction, which is why the loop can
demand bit-exact reproducibility from candidates.

## vmap, and when not to use it

`jax.vmap(f)` maps `f` over a leading axis *without* a Python loop, by
tracing `f` once with batched abstract values. It is the right tool for
"run this per-column function at every grid point" *conceptually* — but
note that your MLP needs no vmap at all: a matmul on the trailing feature
axis already broadcasts over `[lon, lat]`. Reaching for vmap when
broadcasting suffices is PyTorch muscle memory; it costs nothing here but
obscures the code. You WILL need vmap later to batch whole rollouts over
initial conditions (chapter 5): `jax.vmap(loss_fn, in_axes=(None, 0, 0))`
— params shared, states batched.

## scan — the loop that differentiates

`jax.lax.scan(f, carry, xs, length)` is the JAX `for` loop: `f(carry, x)
-> (carry, y)`, compiled once, executed `length` times, differentiable.
The dycore's whole trajectory machinery is two nested scans —
`time_integration.trajectory_from_step` (`time_integration.py:658`):
inner scan over unsaved 900 s steps, outer scan over saved 6 h frames.
An unrolled Python loop of 96 steps would compile 96 copies of the step;
scan compiles one. The catch for training: naive scan stores every
carry for the backward pass. The repo already ships the fix,
`nested_checkpoint_scan` (`time_integration.py:708`) — chapter 5 makes
you derive why its memory is O(max(nested_lengths)).

## grad — through the entire atmosphere

`jax.grad(f)` differentiates *whatever f computes* — including 96
SIL3 steps, spectral transforms, and your network, in one call. Three
things PyTorch users trip on:

1. `grad` differentiates w.r.t. argument 0 by default (`argnums`
   otherwise), and `f` must return a scalar (`value_and_grad` returns
   both loss and grads in one pass — always use it, the forward is free).
2. Closures are inputs: `jax.grad(lambda p: loss(build_filter(p), x))`
   differentiates through the filter you *rebuilt inside* the traced
   function. That is how params reach the corrector in chapter 3 — no
   `requires_grad`, no `.parameters()` registry.
3. There is no `.detach()`; use `jax.lax.stop_gradient` — you will want it
   the day you experiment with truncated backprop through time.

## Memory: remat and donation

`jax.checkpoint` (aka remat) marks a function whose intermediates are
*recomputed* during the backward pass instead of stored — trading one
extra forward for O(steps)→O(1) activation memory inside the marked
region. `donate_argnums` in jit lets XLA overwrite an input buffer with
an output (params → new params): irrelevant at your 1 MB of weights,
decisive for the 17 GB states the loop's evals push through these L4s.

## Debugging table

| Symptom | Tool |
| --- | --- |
| need to see values inside jit | `jax.debug.print`, or temporarily `with jax.disable_jit():` |
| NaNs appear somewhere | `JAX_DEBUG_NANS=1` (fails at the op that made the first NaN; slow), or bisect with the finite-guard idiom from `adapter.py` |
| timing lies (async dispatch) | `result.block_until_ready()` before `time.time()` |
| memory mystery | `jax.live_arrays()`, `jax.profiler.save_device_memory_profile` |
| unexpected recompiles | `jax.config.update("jax_log_compiles", True)` |

## The five bugs every PyTorch person writes here

1. **Python `if` on a traced value** → use `jnp.where`/`lax.cond`.
2. **Shape-varying inputs to a jitted function** → recompile storm; pad
   or fix shapes (the loop's dead candidate is your cautionary tale).
3. **In-place mutation** (`x[0] = 3`) → `x = x.at[0].set(3.)`, and notice
   it returns a *new* array.
4. **NumPy ops on traced arrays** (`np.moveaxis(traced)`) → TracerError;
   use `jnp.*` inside traced code, `np.*` only for host-side constants.
5. **Key reuse** → identical "random" draws; split keys, always.

## Exercise 0 (REPL, 20 minutes, nothing to submit)

a. Trace-count probe above; then add `static_argnums` and watch behavior
   change.
b. `jax.make_jaxpr(lambda x: jnp.sin(x) * 2)(jnp.ones(3))` — read the
   jaxpr. Then wrap in `jax.grad` and read that jaxpr. This is the tape
   you never see in PyTorch, made explicit.
c. Time `jax.jit(step)(state)` for the tiny-grid step from
   `tests/nncorr/conftest.py` twice; explain the two timings (compile vs
   run; async dispatch — use `block_until_ready`).
