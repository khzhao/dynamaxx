# NeuralGCM Parity and Optimized-Dycore Ablation Plan

Status: approved experimental plan; implementation and production training have
not started

## 1. Objective

The project must answer one scientific question with a controlled experiment:

> At the same horizontal resolution, data, learned model, loss, optimizer,
> curriculum, and evaluation protocol, does the optimized DynaMaxx dynamical
> core produce forecasts that are better than NeuralGCM's core?

The current fixed-backbone experiment cannot answer that question. It shares
the Dinosaur numerical framework with NeuralGCM, but it does not reproduce the
published NeuralGCM model. It changes the vertical state, input variables,
encoder, decoder, neural architecture, loss, optimizer, curriculum, and
dynamical-core closures at the same time.

The work therefore has two required models:

1. **Parity control:** reproduce deterministic NeuralGCM 1.4 degree as closely
   as the public code, paper, supplement, and checkpoint allow.
2. **Optimized-dycore candidate:** start from the verified parity control and
   replace only the dynamical core with the optimized DynaMaxx core.

The first success gate is six-hour forecast quality. Longer rollouts do not
begin until the control reproduces NeuralGCM at six hours and the candidate
beats it at six hours under the frozen evaluation protocol.

The complete experiment must fit on one node with eight H100 GPUs. The
production primary training run, decoder fine-tuning, and required validation
must finish within seven days. Checkpoints, caches, forecasts, and evaluation
artifacts are stored under `/mnt/data`; Weights & Biases receives scalar
training statistics only.

## 2. Authoritative References

Implementation decisions must be traceable to the following sources:

- [NeuralGCM paper](https://www.nature.com/articles/s41586-024-07744-y)
- [NeuralGCM supplementary information](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-07744-y/MediaObjects/41586_2024_7744_MOESM1_ESM.pdf)
- [Official NeuralGCM repository](https://github.com/neuralgcm/neuralgcm)
- [Deterministic 1.4 degree configuration](https://github.com/neuralgcm/neuralgcm/blob/main/neuralgcm/reference_code/paper_configs/deterministic_1_4_deg.gin)

The public checkpoint and official configuration take precedence over
descriptive prose when they expose an exact shape or constant. Every inferred
or hardware-adapted value must be marked as such in the experiment manifest.

## 3. Why the Current Model Is Not NeuralGCM Parity

The [current fixed-backbone pipeline](neural-corrector-first-training-pipeline.md)
remains useful as a diagnostic, but it must not be presented as a NeuralGCM
reproduction.

| Axis | Current DynaMaxx experiment | Deterministic NeuralGCM 1.4 control |
| --- | --- | --- |
| Horizontal grid | 240 x 121 equiangular grid with poles; 80 longitudinal spectral slots | 256 x 128 Gaussian data grid; TL127 outer coordinates and the exact custom dycore grid from the official configuration, including 126 longitudinal wavenumbers |
| Vertical state | 13 inferred sigma layers | 32 equidistant sigma layers |
| Pressure-level inputs | 13 levels from 50 to 1000 hPa | 37 levels from 1 to 1000 hPa |
| Atmospheric inputs | geopotential, specific humidity, temperature, zonal wind, meridional wind, and four surface variables | the five atmospheric variables plus cloud ice, cloud liquid, SST, and sea ice |
| Trainable model | 20.69M generic corrector plus 0.59M residual observation decoder | 18.34M total: 9.02M encoder, 4.24M decoder, and 5.09M learned physics |
| Recurrent interface | fixed encoder and raw decoder; residual decoder never feeds the recurrent state | learned encoder, decoder, and physics optimized in the primary training phase |
| Learned-physics features | state, first horizontal derivatives, surface/static fields, location/time, and solar features | pressure features, first derivatives, Laplacians, orography derivatives, land/sea, learned location and surface embeddings, solar features, SST, sea ice, and clouds |
| Learned outputs | vorticity, divergence, temperature, humidity, and log-surface-pressure tendencies | wind-vector, temperature, humidity, cloud-liquid, and cloud-ice tendencies; wind is converted to divergence and vorticity |
| Output scaling | fixed hand-selected scales and a bounded normalized output | 0.01 times the one-hour ERA5 tendency standard deviation, implemented with the exact transforms and constants from the official configuration/checkpoint |
| Primary loss | physical grid-space state loss plus bias and spectrum terms; no native-state target | data-space and model-space filtered spectral MSE, spectrum loss, and mean spectral bias |
| Optimizer | AdamW, peak learning rate 2e-5, beta2 0.999, epsilon 1e-8, 200-step warmup, cosine decay, clipping at 1 | Adam, peak learning rate 0.002, beta2 0.95, epsilon 1e-6, 2,000-step warmup, plateau, then exponential decay |
| Curriculum | 6, 12, 24, 48, 96, 192, and 360 hours; truncated gradients after 24 hours | unrolls promoted through 12, 24, 36, 48, 60, and 72 hours with full extended BPTT |

The raw input used in an earlier local benchmark was first regridded
horizontally to 1.5 degrees and then to NeuralGCM's native 1.4 degree grid. That
made the horizontal input comparison fair, but NeuralGCM still received its
full 37-level state, clouds, and surface forcings. It did not receive the same
13-level state as the current DynaMaxx model.

At six hours on the existing fixed 256-initialization 2019 sample, the public
NeuralGCM checkpoint had RMSE values of 78.32 m^2 s^-2 for Z500, 0.512 K for
T850, 4.02e-4 kg kg^-1 for Q700, 0.997 m s^-1 for U850, and 0.990 m s^-1 for
V850.
The 20,000-update current model's ratios to NeuralGCM were 0.70, 2.02, 1.27,
1.66, and 1.71, respectively. The source summaries are stored at
`/mnt/data/dynamaxx-training-cache/benchmarks/neuralgcm/six-hour-1p4-on-1p5-input/2019-256/summary.json`
and
`/mnt/data/dynamaxx-training-cache/eval/six-hour-checkpoint-selection-2019-256/summary.json`.
This pattern is evidence of an interface and training-parity problem, not
evidence that the shared Dinosaur engine should already yield equal forecasts.

## 4. Frozen Experimental Protocol

The protocol is frozen before model-selection experiments. Changes to it
create a new experiment series and must not be used to retroactively select a
model.

### 4.1 Data split

- Train on ERA5 from 1979-01-01 through 2017-12-31, matching the published
  deterministic 1.4 degree setup.
- Use 2018 for development, checkpoint selection, and comparison with the
  published recipe.
- Use 2019 only as a pre-registered shadow confirmation set. Do not make model
  or hyperparameter choices from its results.
- Keep 2020 untouched until the architecture, checkpoint-selection rule, and
  evaluation code are frozen.
- Run the final 2020 evaluation from 00 UTC and 12 UTC initializations with the
  same 732-start convention used by the official evaluation protocol.

Both the parity control and optimized-dycore candidate use identical timestamps,
shuffle seeds, batches, normalization statistics, forcings, and targets.

### 4.2 State and resolution

The parity control uses the public deterministic 1.4 degree state without
reducing it to fit the hardware:

- 256 x 128 Gaussian input and output grid;
- TL127 outer coordinates and the exact custom spectral dycore grid from the
  official deterministic 1.4 degree configuration;
- 32 equidistant sigma layers;
- all 37 pressure levels in the public checkpoint configuration;
- geopotential, specific humidity, temperature, zonal wind, meridional wind,
  cloud ice, and cloud liquid;
- SST and sea ice forcings; and
- the same static fields, temporal features, solar forcing, and learned
  embeddings as the official model.

All coordinate transforms, pressure/sigma interpolation, units, clipping, and
missing-value behavior receive numerical tests against the public NeuralGCM
implementation or checkpoint.

### 4.3 Model

The parity control implements the published encoder-process-decoder model:

- 384 latent channels;
- five process blocks with three-layer width-384 MLPs;
- the published five-layer vertical CNN with 64 hidden and 32 output channels;
- the 32-dimensional learned location embedding at 1.4 degrees;
- the published feature and prediction masks;
- a learned encoder, learned decoder, and learned physics module trained
  jointly; and
- the memory features enabled by the official deterministic 1.4 degree
  configuration; and
- learned-physics output scaling equal to 0.01 times the one-hour ERA5 tendency
  standard deviation, using the configuration/checkpoint's exact transform
  constants.

Parameter-tree names, shapes, and total counts must match the public checkpoint
before any training run is accepted.

### 4.4 Loss

The parity control implements the published deterministic objective:

\[
L = 20M_{\mathrm{data}}
  + 0.1M_{\mathrm{data,spectrum}}
  + M_{\mathrm{model}}
  + 0.1M_{\mathrm{model,spectrum}}
  + 2M_{\mathrm{mean\ bias}}.
\]

This requires:

- filtered spectral MSE in pressure-level data space;
- filtered spectral MSE in sigma-level model space;
- pressure- and sigma-space spectral-power losses;
- mean spectral bias computed after averaging over batch and lead dimensions;
- the published pressure weighting and grid weighting;
- normalization from 24-hour temporal-difference statistics;
- the published variable balancing, including geopotential 2, humidity 0.66,
  log surface pressure 5, and cloud variables 0.05; and
- the published lead-time and spectral-loss decay functions.

These weights reproduce a published training objective; they are not tuned to
the five headline variables. Evaluation variables must never receive additional
training weight to improve the scorecard. The supplementary ablations report
that removing filtering, bias, or spectrum terms can modestly improve RMSE, so
those terms alone cannot explain the current large six-hour gap. They are
retained for faithful reproduction and for their effects on bias, spectra, and
stability.

The optimized-dycore candidate uses this exact loss and the exact same frozen
normalization files. A loss change and a dycore change may not appear in the
same ablation.

### 4.5 Optimizer and primary curriculum

The primary parity run uses the published deterministic 1.4 degree optimizer:

- Adam with beta1 0.9, beta2 0.95, and epsilon 1e-6;
- peak learning rate 0.002;
- linear warmup through step 2,000;
- constant peak learning rate through step 15,000;
- exponential decay with a 10,000-step half-life after step 15,000; and
- 26,000 total optimizer updates.

The unroll curriculum is 12, 24, 36, 48, 60, and 72 hours, with transitions at
the published boundaries 2,000, 5,656, 10,392, 16,000, and 22,360. The exact
scored lead set is taken from the reference implementation and recorded in the
manifest. The parity run uses full extended BPTT. The current 24-hour
stop-gradient rule is a separate efficiency ablation and is not used in the
parity control.

The reference setup uses one sample per data-parallel device. On eight H100s,
gradient accumulation of two microbatches preserves an effective batch of 16
without altering the optimizer-update schedule. If inspection of the official
configuration establishes a different effective batch, the manifest records
and uses the official value instead.

### 4.6 Decoder fine-tuning

After the 26,000-update primary phase:

- freeze the encoder and learned physics;
- fine-tune the decoder for 4,000 updates with the published traditional
  grid-space MSE objective;
- use the published 1,000-step warmup and decay schedule; and
- reproduce the 12- and 24-hour decoder fine-tuning setup used by the 1.4
  degree model.

The primary and fine-tuned checkpoints are both evaluated. Checkpoint choice is
made by the pre-registered 2018 selection rule, not by inspecting 2020.

### 4.7 Evaluation scorecard

The complete shared pressure-level scorecard contains geopotential,
temperature, specific humidity, zonal wind, and meridional wind at the 13
standard levels 50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, and
1000 hPa. Shared surface outputs are reported separately. Z500, T850, Q700,
U850, and V850 are a readable headline subset, not the model-selection loss.

All forecasts and ERA5 targets are conservatively regridded to one frozen 1.5
degree evaluation grid. The evaluation records latitude-area-weighted RMSE,
ACC, RMS bias, and spectral diagnostics at six hours and at each later scored
lead. The exact variable names, units, regridding weights, climatology, and
missing-value masks are checksummed in the manifest.

## 5. Single-Node Performance Contract

The parity state may not be reduced to satisfy the one-node constraint. Memory
and throughput work precedes production training.

The accepted eight-H100 execution path must:

- use BF16 for suitable neural matrix multiplications while retaining FP32 for
  numerically sensitive state, reductions, and loss calculations;
- stream prefetched batches from `/mnt/data` with parallel readers and no
  repeated pressure/sigma preprocessing in the training step;
- use compiled scans instead of Python rollout loops;
- rematerialize expensive activations where it lowers peak memory without
  excessive recomputation;
- keep steady-state memory below 75 GiB per GPU with no host swapping or OOM;
- overlap host input work with accelerator execution;
- compile each curriculum shape once and cache the executable; and
- report examples per second, update time, input wait, compile time, peak HBM,
  and an end-to-end wall-clock projection.

If replicated `pmap` state does not fit, parameter/optimizer-state sharding and
spatial/model sharding must be implemented before training. Lowering spectral
resolution, vertical resolution, feature count, or model width is not an
acceptable parity workaround.

The throughput gate passes only if measured smoke-test throughput projects the
26,000-update primary run, 4,000-update decoder phase, required validation, and
reasonable restart margin to at most seven days on the node.

## 6. Implementation and Training Phases

### Phase 0: lock the protocol and manifest

Create a versioned experiment manifest containing:

- source commit hashes for DynaMaxx, NeuralGCM, Dinosaur, and evaluation code;
- public checkpoint identity and checksum;
- exact data variables, levels, units, dates, and storage paths;
- grid and regridding definitions;
- architecture and parameter-shape manifest;
- loss constants, normalization checksums, optimizer, curriculum, and seeds;
- checkpoint-selection and early-termination rules; and
- evaluation initializations, metrics, regridding, and bootstrap procedure.

The manifest is immutable for the control/candidate pair.

### Phase 1: build reproducible data caches

Materialize the full 37-level atmospheric state, cloud fields, SST, sea ice,
static fields, forcings, and targets under `/mnt/data`. Derive normalization
statistics from the training split only. Record file checksums and verify at
least 100 randomly selected timestamps against the source data, including
units, level order, longitude convention, poles, and missing values.

### Phase 2: establish implementation parity

Before training, pass all of the following tests:

- every input, latent, prognostic, tendency, and output tensor has the expected
  named shape and units;
- trainable parameter shapes and counts match the public checkpoint;
- the public checkpoint can be loaded without silently dropping or reshaping
  parameters;
- encoder output, a single dycore step, learned tendency, decoder output, and
  each loss component match the reference on frozen examples within declared
  numerical tolerances;
- an encode/decode round trip meets the reference error tolerance;
- gradients reach the encoder, learned physics, and decoder; and
- eight-device reductions match a one-device calculation.

The fixed-backbone residual decoder is not substituted for the reference
learned encoder/decoder path.

### Phase 3: pass memory and throughput smoke tests

Run, in order:

1. initialization and one forward step on one H100;
2. forward/backward/update on one H100;
3. forward/backward/update on eight H100s;
4. 100 updates at the shortest unroll; and
5. representative compiled updates at every curriculum shape.

Each test records peak memory, numerical status, gradient norm, clipping
fraction, per-loss values, input wait, and throughput. The run is rejected for
non-finite state, loss, gradient, or optimizer values.

### Phase 4: overfit a fixed micro-dataset

Overfit 16 to 64 frozen training examples for 200 to 500 updates. Data-space
and model-space state loss, spectrum loss, and bias loss must all respond in the
expected direction. Inspect errors and gradients per variable and level. This
gate is designed to catch broken units, transforms, masks, output scaling, and
gradient paths before a production run.

### Phase 5: train the parity control

Run the complete 26,000-update primary curriculum, then the 4,000-update decoder
phase. Validate on the fixed 2018 subset at pre-registered intervals. Automatic
restart may resume only from a complete local checkpoint and must preserve the
data iterator, optimizer, random state, and curriculum position.

Weights & Biases logs scalar training and validation statistics only. Model
parameters, optimizer state, sample forecasts, normalization arrays, plots, and
evaluation tables remain under `/mnt/data`.

### Phase 6: pass the six-hour reproduction gate

Evaluate the parity control and public NeuralGCM 1.4 checkpoint with the exact
same 2018 initial states and evaluation pipeline. Regrid forecasts
conservatively to the common 1.5 degree grid before scoring.

The aggregate below is the unweighted macro-average of per-variable-level RMSE
ratios over the pre-registered shared scorecard. The control passes when:

- aggregate six-hour RMSE is within 1 percent of the public checkpoint;
- no pre-registered shared variable-level RMSE is worse by more than 3 percent;
- ACC, RMS bias, and spectral diagnostics show no systematic implementation
  mismatch; and
- the result is reproduced from a fresh process using the saved manifest and
  checkpoint.

If this gate fails, do not start the optimized-dycore candidate or extend the
forecast horizon.

### Phase 7: train the optimized-dycore candidate

Fork the verified control configuration and change exactly one experimental
axis: replace the reference dynamical core with the optimized DynaMaxx core.
Keep the learned architecture, parameter initialization policy, data, order,
seeds, normalization, loss, optimizer, batch size, curriculum, validation, and
checkpoint-selection rule fixed.

The candidate retains the control's TL127 coordinates, 32 sigma layers, and
one-hour model step. The optimized algorithms and closures are ported to that
state; the current 13-layer production configuration is not substituted into
the parity experiment.

Any required state-interface adaptation must be deterministic, documented, and
tested. It may not add trainable capacity available only to the candidate. If
the optimized core requires a materially different prognostic state or closure,
record that as the treatment being tested rather than describing the two cores
as identical.

Run multiple matched seeds if the seven-day compute budget permits. At minimum,
use paired data order and initialization seeds so uncertainty can be estimated
from forecast cases even when training-seed replication is limited.

### Phase 8: pass the six-hour superiority gate

On the frozen 2018 development protocol, the optimized-dycore candidate must
strictly improve six-hour RMSE over both the public NeuralGCM checkpoint and the
matched local control for every pre-registered headline variable: Z500, T850,
Q700, U850, and V850. It must also avoid material regressions across the
complete shared variable-level scorecard.

Report:

- latitude-area-weighted RMSE by variable, level, and lead;
- ACC by variable, level, and lead;
- RMS bias;
- zonal and spherical-harmonic power spectra;
- bootstrap confidence intervals over initialization times;
- stability and non-finite rates; and
- inference cost and wall-clock throughput.

A claim of beating NeuralGCM **on all variables** requires improvement over the
public checkpoint and the matched control for all pre-registered shared
variable-level RMSE metrics, with uncertainty reported. The five headline
metrics alone support only a five-variable claim.

### Phase 9: extend to longer forecasts

Only after the candidate passes the six-hour gate, train both control and
candidate through the same published 72-hour curriculum and evaluate through
15 days. Fifteen days is an evaluation horizon for the published deterministic
recipe, not a 360-hour training target.

Bounded BPTT, a longer training curriculum, ensemble training, alternative
attention architectures, and altered loss functions are subsequent experiments.
Each receives its own paired control and cannot be mixed into the optimized-core
ablation.

### Phase 10: final untouched evaluation

After the model, checkpoint-selection rule, and analysis code are frozen,
evaluate the selected control and candidate on the untouched 2020 set. Publish
all pre-registered metrics, including regressions. Do not tune, restart
training, or select another checkpoint after reading 2020 results.

## 7. Failure Diagnosis Order

If the reproduction gate fails, investigate in this order:

1. lead-zero encoder/decoder reconstruction by variable and level;
2. grid, spectral truncation, pressure/sigma interpolation, and units;
3. one-step dycore and learned-tendency agreement with the reference;
4. output-scale saturation and the fraction of updates dominated by gradient
   clipping;
5. individual loss terms and per-variable gradient magnitudes;
6. forcing timestamps, solar geometry, SST, sea ice, clouds, and static fields;
7. recurrent drift at 6, 12, and 24 hours; and
8. only after the above agree, model or loss changes as a new ablation.

The current run's frequent raw gradient norms above the clip threshold are a
warning that the existing hand-selected output scales and conservative
optimizer do not reproduce the published parameterization. They are not a
reason to tune headline-variable weights.

## 8. Required Experiment Matrix

| ID | Model | Purpose | May advance when |
| --- | --- | --- | --- |
| R0 | Public NeuralGCM 1.4 checkpoint | Frozen reference | Evaluation is reproducible |
| R1 | Faithful local NeuralGCM control | Validate implementation and training recipe | Six-hour reproduction gate passes |
| D1 | R1 with optimized DynaMaxx dycore only | Measure optimized-core causal effect | Six-hour superiority gate passes |
| R2 | R1 through published 72-hour curriculum | Long-range matched control | R1 passes |
| D2 | D1 through the same curriculum | Long-range optimized-core test | D1 passes |
| E1 | Bounded-BPTT variant of the stronger model | Efficiency experiment | R2/D2 comparison is complete |
| E2 | Deterministic architecture/data variants | Accuracy experiment | Each has a matched baseline |
| E3 | Ensemble/stochastic training | Probabilistic forecast experiment | Deterministic protocol is frozen |

R0, R1, and D1 are mandatory before any claim that the optimized dycore beats
NeuralGCM. Later experiments may improve the model, but they answer different
questions.

## 9. Completion Criteria

This plan is complete only when:

- the parity implementation matches the public checkpoint's state, parameter
  shapes, one-step behavior, and loss components;
- its primary and decoder training complete on eight H100s within the one-week
  wall-clock contract;
- the local parity control passes the six-hour reproduction gate;
- the optimized-dycore candidate is trained as a one-variable ablation;
- both models are evaluated on the frozen 2018 protocol and untouched 2020
  protocol;
- every claim is scoped to the metrics actually improved; and
- all non-W&B artifacts and enough provenance to reproduce the result are
  retained under `/mnt/data`.

The immediate next implementation target is R1, not another tuned version of
the current fixed-backbone model.
