# 04 — Data and loss: what "truth" means for a hybrid model

## The dataset you already have

`/home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/processed-
era5-1p5deg-6h-240x121-equiangular-with-poles-conservative/` — processed
ERA5, 6-hourly, 1959→2023-01-10, 82 packed channels: 4 surface (T2m, U10,
V10, MSLP) + 6 upper-air variables (T, u, v, z, q, ω) × 13 pressure
levels. Layout: `years/<year>.zarr` (state), `constants.zarr`
(orography, land-sea mask, soil type), `stats/<year>.zarr` (per-year,
per-gridpoint temporal mean/std/sample_count — your normalization source).

Access goes through `WeatherBench2Source`
(`src/dynamaxx/data/weatherbench2.py:27`): `read_state_times(times)` →
`[time, channel, lon, lat]` float32, `state_channel_names()`,
`read_constants(...)`, `spatial_coordinates(...)`, `area_weights(...)`,
`prefetch_years(...)` for the training loop. It validates exact-time hits
and handles year-file boundaries; do not hand-roll xarray reads.

## The split law (this section is not optional)

`src/dynamaxx/eval/protocols.py:114-147`: **fast** = 14 fixed 2018 dates;
**iteration** = daily 2014–2018; **validation** = daily 2019; **golden** =
daily 2020, locked. Therefore:

- Train on **1959–2013**. `data.sample_training_window` asserts
  `last_year <= 2013`; leave the assertion in. If you ever "just quickly"
  fine-tune on 2016 because the curve looked nice, every fast/iteration
  number you produce afterwards is fiction, silently.
- Carve your own dev set out of the training era for early stopping and
  hyperparameter picks — e.g. train 1959–2009, dev 2010–2013. Touch the
  repo's protocols only for final, infrequent scoring.
- Golden (2020) does not exist for you. The loop's own roles are forbidden
  from looking at it mid-development; inherit that discipline.
- Normalization statistics are data too: `pooled_channel_stats` over
  training years only.

One subtlety worth thinking through: training *targets* at t0+6h…t0+Nd are
future analyses — that is supervised truth, not leakage, because the
*years* are disjoint from evaluation. Leakage in this setup means
information from eval years or from post-initialization observations of
the *evaluated* forecasts reaching the model or its statistics.

## Sampling windows

`data.sample_training_window(source, rng, target_count=K)` draws a random
00Z init in a random training year and reads `[t0, t0+6h, …, t0+K·6h]` in
one call. Defaults start at 1980 (satellite-era analyses are better
constrained); widening to 1959 doubles your data at some quality cost —
that is a measurable experiment, not a belief. Batch by stacking windows
and `vmap`-ing the loss (chapter 5); with ~12k training days × 4 daily
inits available, one pass at batch 4 is ~3k updates — you will be
epochs-limited by compute, not samples.

## Targets: encode-then-compare, and why

You must choose the space where "error" is measured. The tutorial's
choice: **encode each target analysis into the model's own T80/L13 sigma
representation (`data.encode_analysis`), decode both forecast and target
to nodal SI (`corrector.decode_nodal_si`), and compare there.**

The argument, which you should be able to reproduce: the model can only
represent T80-truncated, 13-layer states. A raw 1.5° pressure-level
target contains variance the model cannot express (finer vertical
structure, wavenumbers > 80 on the 240×121 grid, below-terrain
extrapolation artifacts). Comparing against it adds an irreducible floor
to the loss and — worse for training — a gradient component pointing at
unreachable states. Encoding the target through the same truncation makes
the loss measure exactly the error the corrector could, in principle,
remove. The cost: your loss is blind to encode/decode error itself, and
the fixed evaluation (chapter 6) scores pressure-level fields — so
expect a gap between training loss and eval skill; if it is large,
encode/decode error is the next thing to attack (the "learned encoder
corrections" extension).

Practical wrinkle: `encode_analysis` runs DFI-free and returns spectral
states; decode targets ONCE on the host (before the training loop) and
feed nodal SI dicts to the loss — do not re-decode targets inside every
jitted step.

## The loss

Per field f ∈ {T, u, v, ps}, per target window k:

    L = mean_k  Σ_f  w_f · Σ_columns a(φ) · ( x̂_f − x_f )² / σ_f²

- `a(φ)`: cos-latitude area weights (`normalize.cos_latitude_weights`, or
  `source.area_weights` — check its orientation against the dinosaur grid
  before mixing them; a flipped latitude axis in the WEIGHTS is the bug
  the shapes won't catch).
- `σ_f`: climatological std per field/level from the pooled stats — this
  is what makes 1 K of temperature error commensurate with 1 Pa of
  pressure error. With standardization in place, start with all
  `w_f = 1`; move weights only in response to evidence (e.g. ps loss
  dominated by tides you cannot correct anyway).
- Sum over layers inside each field, standardized per layer — a 1 K error
  at 50 hPa (σ small) then matters more than at 850 hPa (σ large). Decide
  whether you endorse that or want per-layer weights; NeuralGCM-class
  models weight levels deliberately. Write your choice down in the
  training log; you will otherwise re-litigate it every bad run.

## Normalization statistics

`normalize.pooled_channel_stats(path, years)` pools the shipped per-year
moments exactly (count-weighted two-moment identity) and reduces over
space with the *total-variance* convention: σ² = area-mean(temporal σ²) +
area-variance(temporal mean). For T1000 the spatial term dominates (pole–
tropics ≫ day-to-day); for feature scaling that is the honest scale.
`feature_stats_from_channels` then maps channel stats → the (3L+1) feature
vectors, using pressure-level stats for sigma layers — an approximation
that is fine for normalization and would be wrong for physics; the
docstring says so and chapter 6's ablations give you a chance to test
whether it matters.

**EX 4 (derivation, on paper).** (a) Prove the pooling identity
implemented in `pool_yearly_moments` from the definition of population
variance over a concatenated sample. (b) Show that if every year had
equal counts and equal means, it reduces to the RMS of the yearly stds.
(c) The dataset stores `std_ddof: 0`; explain why pooling with ddof=1
stds through the same identity would be subtly wrong, and bound the error
for n≈1460 samples/year. The scaffold test
`test_pool_yearly_moments_matches_bruteforce` is the numerical check of
(a) — your derivation is the reason it HAD to pass.
