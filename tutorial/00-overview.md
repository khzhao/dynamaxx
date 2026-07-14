# A NeuralGCM-style neural corrector for the dynamaxx dycore

You are going to build a hybrid model: this repository's spectral
primitive-equation core stepped by SIL3, with a learned column corrector
applied every 900 s step, trained end-to-end by differentiating through
multi-day rollouts against ERA5.

Two facts make this repo an unusually good place to learn this:

1. **The dycore here *is* the NeuralGCM dycore.** The vendored `dinosaur`
   package under `src/dynamaxx/dycore/models/dinosaur/` is the same
   differentiable JAX core Google built NeuralGCM on (Kochkov et al.,
   *Neural general circulation models for weather and climate*, Nature
   2024; arXiv:2311.07222). Nothing needs to be ported: encode, step,
   filters, and decode are already pure JAX functions.

2. **You have a hand-crafted baseline to beat that took a machine weeks to
   find.** The autonomous optimization loop in the main worktree has spent
   ~200 experiments evolving `dinosaur` into `dino_rskin_apv`: Ekman drag,
   orographic lift, terrain-work heating, a prognostic land-skin reservoir,
   radiative skin energy, tropical WTG relaxation, anticipated-PV flux —
   every one a *hand-designed corrector bolted onto the same hook you will
   use*. The scientific question of this tutorial: can one column MLP,
   trained on 30 years of ERA5, learn what that chain hand-codes? The fixed
   evaluation gives a number: incumbent iteration skill −0.0750; the free
   core you start from is far below it; persistence on T2m is the boss
   fight nobody has won yet (T2m skill −0.363).

## What you produce

- `src/dynamaxx/nncorr/` — a small pure-JAX package (no Flax, no optax; you
  build params-as-pytrees, the forward pass, Adam, and the training loop
  yourself — that is the point).
- A trained checkpoint and a registered model `dino_nncorr` you can score
  with the repo's own `uv run dynamaxx-eval fast --model ...`.
- The understanding to read `adapter.py` (6,200 lines of production JAX)
  fluently.

## Ground rules (read once, obey always)

- **This worktree is the sandbox.** You are on branch
  `kzhao--nncorr-tutorial`, pinned to the incumbent source commit
  `7174848c`. The main worktree at `~/github/kzhao/dynamaxx` belongs to the
  autonomous loop, which edits, evaluates, and reverts files there around
  the clock. Never write there; never `git checkout` branches there.
- **GPU etiquette.** The loop owns the four L4s during its eval phases
  (~4 h at a stretch), one worker per GPU, never oversubscribed — that is a
  standing rule on this box. Develop and run all tests with
  `JAX_PLATFORMS=cpu` (the test conftest forces it). Real training runs
  only when `nvidia-smi` shows zero compute processes;
  `train.assert_gpu_is_free()` enforces this and you will keep it in place.
- **The split law.** The fixed eval protocols initialize from 2014–2018
  (iteration), 2019 (validation), 2020 (golden). Training touches
  **1959–2013 only**. `data.sample_training_window` asserts this. Golden
  is never inspected, full stop — the loop's protocol treats that as
  radioactive and so do you.
- Dev loop: small first. T21 grid, 4 layers, CPU, minutes — the physics
  and the bugs are identical at toy scale; only the skill isn't.

## How to work

```bash
cd ~/github/kzhao/dynamaxx-nncorr-tutorial
JAX_PLATFORMS=cpu uv run pytest tests/nncorr -m "not exercise" -q   # must pass now
JAX_PLATFORMS=cpu uv run pytest tests/nncorr -m exercise -q        # your TODO list
```

The scaffold tests pass today. The exercise tests are your acceptance
criteria; they fail with `NotImplementedError` until you write the code,
then with real assertions until you write it correctly. No solutions are
provided anywhere in this branch. When stuck, the answer is in the
production code — every exercise names the file to imitate.

## Map

| Chapter | You learn | You write |
| --- | --- | --- |
| 01 JAX for PyTorch people | tracing, pytrees, scan, grad, the five bugs everyone writes | REPL probes |
| 02 Anatomy of the dycore | State, spectral transforms, SIL3, the filter hook, units | shape safari |
| 03 Designing the corrector | NeuralGCM's design axes mapped onto this repo | EX 1 MLP, EX 2 features, EX 3 corrector |
| 04 Data and loss | the zarr pipeline, split law, normalization, loss geometry | EX 4 (derivation) |
| 05 Training | checkpointed rollouts, Adam by hand, curricula, NaN forensics | EX 5 rollout loss, EX 6 optimizer |
| 06 Evaluation | registry wiring, fixed protocols, reading skill vs the incumbent | EX 7 model + experiments |

Success ladder, in increasing order of glory: (1) all exercise tests
green; (2) a T21 training run whose loss beats the free core at 6 h;
(3) a T80 checkpoint that beats the free core on the fast protocol at all
leads; (4) approach `dino_rskin_apv`'s −0.075; (5) positive T2m skill vs
persistence — which no model in this repository, hand-built or otherwise,
has achieved.
