# 06 — Evaluation: facing the fixed protocols

Training loss is your instrument; the repo's fixed evaluation is the
court. This chapter wires your checkpoint into the registry, scores it
with the same harness the optimization loop uses, and tells you how to
read the verdict.

## EX 7: a registered hybrid model

Write `src/dynamaxx/nncorr/model.py` (no test ships for this — the
acceptance check is the eval harness itself):

```python
@dataclasses.dataclass(frozen=True)
class NNCorrectedDinosaurModel:
    name: str = "dino_nncorr"
    checkpoint_path: str = "nncorr_params.npz"
    spectral_wavenumbers: int = 80
    def forecast(self, forecast_input: ForecastInput) -> WeatherState: ...
```

Mirror `DinosaurPrimitiveEquationsDycoreModel.forecast`
(`adapter.py:221-345`) but radically simpler — your model has no feature
zoo. The skeleton: infer pressure levels from the input channels, build
the grid (`data.build_grid_bundle` logic, but from `forecast_input`'s
lon/lat — reread how `adapter.py:226-234` does it and why you must NOT
assume the eval grid equals the training grid), load params once
(`checkpoint.load_pytree` against a template from `init_mlp_params` —
mismatched hidden dims fail loudly here, which is what you want), build
static features ON THE EVAL GRID, construct the NN filter, `build_step_fn`,
`trajectory_from_step(outer_steps=max(lead)+1, inner_steps=
step_seconds/900, start_with_input=True)`, loop initial conditions like
`adapter.py:326` does, decode with `dinosaur_state_to_weather_state`
(`adapter.py:4062`), select the requested lead steps.

Then register it: one factory + one dict entry in
`src/dynamaxx/dycore/registry.py` (pattern: any of the last entries, e.g.
`dino_rskin_apv` at line 342/472). This edit exists only on this branch —
the loop's registry in the main worktree never sees it, so there is no
collision with its candidates.

Two contract points that will bite otherwise:

- The eval calls `forecast` with `lead_steps` in 6 h units and expects
  output shaped `(lead, init, variable, lon, lat)` on the DATA grid
  (latitude possibly reversed relative to dinosaur order — the decode
  helper handles it if you pass `latitude_reversed` through honestly).
- Your filter needs static features per grid; cache them per (lon, lat)
  shape the way the adapter caches land-sea fractions
  (`adapter.py:150-152`), or eat a rebuild per chunk.

## Running the judge (etiquette applies — this uses a GPU for ~7 min)

```bash
# ONLY when nvidia-smi shows the loop idle:
cd ~/github/kzhao/dynamaxx-nncorr-tutorial
uv run dynamaxx-eval fast --model dino_nncorr
```

`fast` = 14 fixed 2018 inits, leads 1–15 d, writes
`outputs/eval/fast_dino_nncorr.{json,csv}` in THIS worktree. Baselines to
place yourself against (the first two you can regenerate here; the third
is cached in the main worktree's `outputs/eval/` — read it, don't rerun
it):

| model | fast primary (evidence) |
| --- | --- |
| `persistence` | 0 by construction (it is the skill reference) |
| `dinosaur` (free core) | run it once here; expect deeply negative |
| `dino_rskin_apv` (incumbent) | ≈ −0.075 iteration / −0.0749 fast |

Read the JSON: `primary_score`, then per-variable per-lead
`skill_vs_persistence` rows. The reading order that matters: (1) is
day-1–5 sane (your zero-init + bounded increments should make early leads
track the free core closely — a hybrid that wrecks day 2 has a training
bug, usually output scale); (2) where does skill diverge from the free
core — by variable and lead; (3) T2m specifically, because that is the
variable the whole hand-crafted chain was built around and the one where
persistence is still unbeaten (−0.363 for the incumbent).

`fast` is 14 samples — noisy. Treat differences < ~0.005 primary as
weather. `iteration` (1826 inits, ~4 h on all four GPUs) is the loop's
instrument; you have no business running it until fast looks interesting
AND the loop is paused with the user's blessing.

## Reading the physics out of the network

The point of beating-or-losing-to the incumbent is diagnosis, not a
scoreboard. Three experiments, in order of information per GPU-minute:

1. **Feature knockouts at eval time.** Zero the land-fraction feature
   (or orography, or the wind block) in a wrapper filter and re-run fast.
   If skill collapses over land at late leads, your MLP has learned a
   land-surface memory — the thing the loop needed five accepted
   candidates (`lateskin`→`rskin`) to hand-build. This is the single most
   direct comparison between learned and hand-crafted physics available
   anywhere in this repo.
2. **Increment climatology.** Run 20 forecasts dumping `corrector_
   increments` every 6 h; average dT by (land/sea × local solar time ×
   layer). A diurnal land heating dipole = it rediscovered the radiative
   skin. A low-level drag aligned against the wind = it rediscovered
   Ekman. Publish the maps in your notes either way — negative results
   here are as informative.
3. **Tendency-mode A/B (EX 8).** Re-express the corrector via
   `compose_equations` (chapter 3 sketched why they differ) and fast-eval
   both from the same checkpoint. This isolates the injection-point
   question with everything else held fixed — a genuinely publishable
   little experiment hiding in a tutorial.

## Where this road leads

- Solar zenith + per-sample time features (the highest-value input you
  deliberately skipped; thread the time like `adapter.py:361`).
- Humidity as an input (it rides the state as a tracer already;
  `include_humidity=True` in encode) — the dry core's biggest structural
  handicap vs. ERA5.
- Corrector ON TOP of the incumbent chain instead of the free core — the
  complementary experiment: does learning add skill the hand-crafted
  features missed, or have they saturated the correctable error?
- Learned encoder corrections; stochastic heads and CRPS training à la
  NeuralGCM-ENS; distilling the incumbent chain into the network.

A closing note on the house rules: if a trained corrector ever looks like
it belongs in the main loop, it does not go there by you merging this
branch. The loop's protocol requires training-based candidates to be
explicitly sanctioned (`roles/RESEARCHER.md`, "Prohibited Work"), and its
Researcher→Evaluator→Scorer pipeline owns promotion. What you have on
this branch is a laboratory. What the loop accepts is a different,
harder, colder question — you have watched it reject prettier ideas than
ours all week.
