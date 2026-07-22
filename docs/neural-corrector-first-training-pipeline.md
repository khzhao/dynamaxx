# First Training Pipeline for a Dinosaur Neural Corrector

Status: proposed initial experiment

## Decision

The first model should be a minimal NeuralGCM-style hybrid:

- freeze the optimized `dino_rskin_apv` dynamical core;
- freeze the existing WeatherBench encoder and decoder;
- train one neural network that predicts additive tendencies for Dinosaur's
  prognostic variables;
- make both the dycore inner-step duration and neural-correction interval
  explicit configuration values;
- initially evaluate the network every 30 minutes and hold its tendency fixed
  until the next correction boundary;
- train end to end against decoded WeatherBench2 ERA5 states at the verified
  six-hour observation times;
- treat every dycore state and neural evaluation between observed lead times as
  latent, with no intermediate state target or loss;
- use exact six-hour backpropagation through time (BPTT) for the first
  supervised rollout;
- expose the network to its own forecast states using stopped-gradient prefixes
  that end on observed six-hour boundaries;
- use spectral accuracy, spectrum, and bias losses so that long-horizon
  training does not reward smoothing.

This experiment answers the first scientific question cleanly:

> How much forecast improvement remains learnable when the optimized Dinosaur
> backbone is fixed?

Learned encoder corrections, an additional WeatherBench-state branch, neural
memory, stochastic corrections, and non-local neural architectures should be
considered only after this baseline is measured.

## 1. Model Definition

Let:

- $X_t$ be a WeatherBench-style weather state;
- $S_t$ be Dinosaur's internal prognostic state;
- $A_t$ be any causal auxiliary state carried by the optimized model, such as
  surface or land-skin state;
- $B$ be static context such as orography, land fraction, and grid geometry;
- $E$ and $D$ be the fixed Dinosaur encoder and decoder;
- $F_{\mathrm{Dino}}$ be the fixed optimized Dinosaur tendency;
- $G_\theta$ be the trainable neural corrector.

The forecast is initialized once:

$$
S_{t_0} = E(X_{t_0}).
$$

The model then remains in Dinosaur's internal state space until an output is
requested. It must not decode and re-encode the forecast at every internal
step. The internal trajectory is a recurrent computational path, not a
supervision target.

### 1.1 Coupled tendency

Let $\Delta t_{\mathrm{D}}$ be the duration of one completed dycore inner step
and $\Delta t_{\mathrm{N}}$ be the neural-correction interval. At correction
times $t_k$, construct nodal neural features:

$$
Z_k = H(S_{t_k}, A_{t_k}, B, t_k),
$$

and evaluate the neural tendency once:

$$
Q_k = P\left(G_\theta(N(Z_k))\right).
$$

Here:

- $H$ converts the native prognostic state into useful nodal physical fields
  and appends causal context;
- $N$ applies fixed training-set normalization;
- $G_\theta$ is the column neural network;
- $P$ rescales and projects its nodal outputs into Dinosaur's native modal
  tendency representation.

For the next correction interval, the hybrid system is

$$
\frac{dS}{dt}
=
F_{\mathrm{Dino}}(S,t;A,B) + Q_k,
\qquad
t_k \leq t < t_k + \Delta t_{\mathrm{N}}.
$$

The neural network is not reevaluated at each SIL3 stage. A valid configuration
must satisfy

$$
n_{\mathrm{inner}}
=
\frac{\Delta t_{\mathrm{N}}}{\Delta t_{\mathrm{D}}}
\in \mathbb{N}.
$$

For a rollout of physical duration $T$, the operation counts are

$$
N_{\mathrm{D}}(T)=\frac{T}{\Delta t_{\mathrm{D}}},
\qquad
N_{\mathrm{N}}(T)=\frac{T}{\Delta t_{\mathrm{N}}}.
$$

These are configuration-dependent counts. The current `dino_rskin_apv`
adapter defaults to

$$
\Delta t_{\mathrm{D}}=900\ \mathrm{s}.
$$

With the proposed initial correction interval
$\Delta t_{\mathrm{N}}=1800\ \mathrm{s}$, one public hybrid step contains two
dycore steps. A six-hour rollout then contains 24 completed dycore steps and 12
neural evaluations. Those numbers describe the current configuration; they are
not part of the generic hybrid-model contract.

No loss is attached to any of those 24 intermediate dycore states or 12 neural
outputs. They are differentiated only because they influence a decoded forecast
at a real WeatherBench2 lead time.

The decoded forecast at a requested lead time is

$$
\widehat X_t = D(S_t, A_t).
$$

This is a hybrid neural ODE. The neural network is not a standalone replacement
for the ODE; it parameterizes the residual tendency missing from the frozen
backbone.

### 1.2 Time-aware model API

The public API should express physical time directly:

```python
hybrid_model = HybridModel(
    neural_model=neural_corrector,
    dycore_name="dino_rskin_apv",
    correction_interval_seconds=1800.0,
)

state = hybrid_model.initialize(weather_state, initial_time)
state = hybrid_model.step(parameters, state)
state = hybrid_model.advance(
    parameters,
    state,
    duration_seconds=6 * 3600,
)
forecast = hybrid_model.decode(state)
```

`step` advances exactly one configured correction interval. `advance` accepts a
physical duration and validates that it is an integer multiple of the
correction interval. The named dycore supplies its configured
`inner_step_seconds`; the hybrid validates the ratio above before running.

An API that accepts only an unqualified number of steps is ambiguous: the
caller cannot know whether a step means a dycore inner step, a neural-coupling
step, or a six-hour output interval. If a step count is supported for scan-based
code, it must be explicitly named `correction_steps`, and
`correction_interval_seconds` remains the conversion to physical time.

## 2. Neural Corrector

### 2.1 First architecture

Use a shared vertical-column residual MLP. The same network is applied at every
horizontal grid point, while all vertical levels in a column are presented
together.

The initial configuration should use:

- four residual MLP blocks;
- hidden width 256;
- SiLU activations;
- normalization of input features using training-set statistics;
- a zero-initialized output projection;
- fixed, per-output tendency scales.

The zero output initialization makes the initial hybrid forecast exactly the
frozen Dinosaur forecast. It also makes degradation or instability introduced
by training easy to identify.

A column model is appropriate for the first experiment because Dinosaur
already handles resolved horizontal transport. The corrector can focus on
local unresolved physics and systematic model error. A spherical convolution
or neural operator can later be tested against this controlled baseline.

### 2.2 Inputs

At each horizontal column, the initial neural input should contain nodal forms
of:

- vorticity at all sigma levels;
- divergence at all sigma levels;
- temperature variation at all sigma levels;
- specific humidity at all sigma levels;
- log surface pressure;
- horizontal gradients of the prognostic fields;
- relevant causal auxiliary surface state from `dino_rskin_apv`;
- surface geopotential or orography;
- land-sea information;
- latitude and periodic longitude encodings;
- periodic time-of-day and time-of-year encodings;
- incident solar forcing when available causally.

All time-varying inputs must be available during a free forecast. Future ERA5
or WeatherBench states must never be supplied as neural inputs.

The first model should not have a second branch containing the latest complete
WeatherBench state. That branch can be evaluated later as an explicit
ablation.

### 2.3 Outputs

The neural network should produce additive tendencies corresponding to the
native prognostic variables:

$$
G_\theta(Z_k)
=
\left(
\dot\zeta_\theta,
\dot\delta_\theta,
\dot T'_\theta,
\dot{\log p_s}_\theta,
\dot q_\theta
\right).
$$

The outputs are predicted in nodal space, multiplied by fixed channel scales,
transformed to modal space, clipped to Dinosaur's supported wavenumbers, and
added to the explicit tendency. Dinosaur's implicit operator remains
unchanged.

Output scaling is a numerical parameterization choice, not a tendency target.
Choose conservative fixed scales from the frozen dycore's prognostic tendency
magnitudes, then validate them through end-to-end WeatherBench2 forecast loss.
The correction norm should be monitored by variable and vertical level, but it
is not itself a supervised label.

## 3. Data and Sampling

### 3.1 Verified local data cadence

The active default dataset is:

```text
/home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/
processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative
```

This is a six-hourly dataset. This conclusion comes from the stored coordinate,
not only the directory name:

- `metadata.json` identifies the source as the 6-hour, 1.5-degree ERA5 store;
- the 65 yearly stores contain 93,544 timestamps from
  `1959-01-01T00:00` through `2023-01-10T18:00`;
- every consecutive timestamp difference across the full collection is exactly
  six hours;
- the available synoptic times are 00:00, 06:00, 12:00, and 18:00 UTC;
- 2018 contains 1,460 samples, exactly four samples per day for 365 days.

Therefore the observed-data interval for the current pipeline is

$$
\Delta t_{\mathrm{obs}}=6\ \mathrm{hours}=21600\ \mathrm{s}.
$$

There are no locally processed hourly targets. Hourly ERA5 may be processed as
a future data product, but this proposal does not assume that it exists.

The data cadence is independent of both integration cadences:

| Quantity | Meaning | Initial value |
| --- | --- | ---: |
| $\Delta t_{\mathrm{D}}$ | completed dycore inner step | 900 s for the current `dino_rskin_apv` configuration |
| $\Delta t_{\mathrm{N}}$ | neural-correction interval | proposed 1,800 s |
| $\Delta t_{\mathrm{obs}}$ | available target interval | verified 21,600 s |

The network may still be evaluated every 30 minutes. The six-hour cadence only
means that all 12 correction evaluations in that interval receive credit
jointly from the next observed endpoint.

### 3.2 Chronological split

Use the standard chronological split requested for the neural model:

- training: 1979–2018 inclusive;
- validation and checkpoint selection: 2019;
- untouched final test: 2020.

The repository's existing `iteration` protocol covers 2014–2018, so it overlaps
the neural training set under this split. Its dates and implementation do not
need to change, but its score is now an in-distribution training diagnostic for
the hybrid model, not held-out evidence. The existing `validation` protocol on
2019 and locked `golden` protocol on 2020 align with the validation and final
test split above. Do not inspect or tune against 2020 until final reporting.

The earlier 1959–1978 and later 2021–2023 data can be considered only in a
separate data-split experiment.

Every sampled rollout, including its target endpoint, must remain inside one
split. For example, the final training start must be early enough that its
target does not cross into 2019, and a validation rollout must not use a target
from 2020.

Compute all normalization, climatology, and spectral statistics from the
training split only. Sample initial times uniformly enough to cover seasons and
times of day. Batch sampling should not disproportionately favor long,
contiguous periods from a small number of years.

Each truth-start forecast is initialized by encoding the real WeatherBench2
state:

$$
S_t = E(X^*_t).
$$

At a supervised lead time, decode the model state and compare it directly with
the real WeatherBench2 state:

$$
\widehat X_{t+\tau}=D(\widehat S_{t+\tau},\widehat A_{t+\tau}),
\qquad
\mathcal L_\tau
=
\mathcal L_{\mathrm{WB2}}
\left(\widehat X_{t+\tau},X^*_{t+\tau}\right).
$$

Do not encode $X^*_{t+\tau}$ to create an internal-state target. The target is
the real WeatherBench2 state itself.

### 3.3 Consequence for gradient windows

With the current data, six hours is the shortest exact endpoint-supervised
forecast window. Stopping gradients after one hour would shorten the graph, but
there is no target at that boundary. Moving all six-hour error onto a final
one-hour suffix would train that suffix to repair five hours of detached model
error and would not estimate the intended local tendency.

The valid compute-saving choices are therefore:

1. use exact six-hour BPTT with activation rematerialization;
2. stop gradients only across prefixes that end at six-hour observation
   boundaries, while keeping the final six-hour interval differentiable;
3. create a separate hourly dataset if exact one-hour objectives are later
   required.

None of these choices adds supervision to an inner dycore state. Every neural
evaluation within a differentiable interval receives credit only through its
effect on decoded forecasts at real WeatherBench2 observation times.

## 4. Training Curriculum

### 4.1 Integration verification

Before production training:

1. Verify that a zero neural correction reproduces the frozen
   `dino_rskin_apv` trajectory to numerical tolerance.
2. Verify that `step` advances exactly `correction_interval_seconds` and that
   the simulation clock agrees after a six-hour `advance`.
3. Verify finite forward values and gradients through one complete six-hour
   window on a single example.
4. Verify that rematerialized and non-rematerialized six-hour gradients agree
   within the selected numerical tolerance.
5. Overfit a small fixed set of approximately 16 six-hour WeatherBench2 pairs
   using only decoded endpoint loss.
6. Confirm that every neural output channel affects its corresponding forecast
   variable.
7. Confirm that a checkpoint restart reproduces the next optimizer update.

These checks distinguish integration errors from optimization or modeling
failures.

### 4.2 Phase A: exact six-hour endpoint training

Start directly with the recurrent model. Encode the initial real state, advance
six hours, decode once, and compare with the next real state:

$$
S_t=E(X^*_t),
\qquad
\widehat S_{t+\Delta t_{\mathrm{obs}}}
=
\Phi_{\theta,\Delta t_{\mathrm{obs}}}(S_t),
$$

$$
\widehat X_{t+\Delta t_{\mathrm{obs}}}
=
D\left(
\widehat S_{t+\Delta t_{\mathrm{obs}}},
\widehat A_{t+\Delta t_{\mathrm{obs}}}
\right),
$$

$$
\mathcal L
=
\mathcal L_{\mathrm{WB2}}
\left(
\widehat X_{t+\Delta t_{\mathrm{obs}}},
X^*_{t+\Delta t_{\mathrm{obs}}}
\right).
$$

There is no loss against an encoded target and no loss at a 30-minute neural
boundary or 900-second dycore boundary. Do not teacher-force, decode and
re-encode, or replace the recurrent state anywhere inside the six-hour
interval.

For the initial timing configuration, each example evaluates the corrector 12
times and advances the dycore 24 completed inner steps. The backward pass must
differentiate through the dependence of every later dycore state on earlier
corrections. Freezing dycore parameters avoids dycore optimizer state, but it
does not remove these state activations from BPTT.

All 12 neural evaluations receive gradients from the same decoded six-hour
WeatherBench2 loss. Training is free to discover whatever latent internal
trajectory gives the best observed forecast; that trajectory does not need to
match an encoded ERA5 trajectory between endpoints.

Start with ERA5 truth starts only. Rematerialize correction blocks to control
memory, use the smallest stable per-device batch, and use gradient accumulation
for the desired effective batch size.

### 4.3 Phase B: model-state exposure with stopped prefixes

After truth-start training is stable, expose the corrector to model-generated
states. Sample an integer prefix length $p\geq1$ in units of the observation
interval and compute

$$
\widetilde S_{t+p\Delta t_{\mathrm{obs}}}
=
\operatorname{stopgrad}
\left(
\Phi_{\theta,p\Delta t_{\mathrm{obs}}}(E(X^*_t))
\right).
$$

Run this prefix without retaining activations. Then differentiate through one
complete observed interval:

$$
\widehat S_{t+(p+1)\Delta t_{\mathrm{obs}}}
=
\Phi_{\theta,\Delta t_{\mathrm{obs}}}
\left(\widetilde S_{t+p\Delta t_{\mathrm{obs}}}\right),
$$

Decode the endpoint and compare only with the real WeatherBench2 target at
$t+(p+1)\Delta t_{\mathrm{obs}}$. The forecast state remains numerically
continuous at the boundary; only its gradient history is cut. The detached
prefix and differentiable suffix contain no internal-state targets.

The prefix adds forward cost but the backward graph remains six hours. Begin
with $p=1$ and introduce longer prefixes only when correction norms and free
forecasts remain stable. Because the final interval inherits prefix error, keep
truth-start batches as the dominant source of clean temporal credit.

### 4.4 Phase C: optional longer credit assignment

Only after the six-hour model has converged should the project test full
12-hour BPTT. Decode at six and 12 hours and compare both forecasts with their
corresponding real WeatherBench2 states. Those are two observed lead-time
losses on one continuous rollout; the states between them remain latent. This
experiment answers whether credit across an observation boundary is worth the
additional memory and compute. Full-day or multi-day BPTT is not required for
the first baseline.

If an hourly ERA5 training product is created later, exact one-hour truth-start
and stopped-prefix suffixes become valid options. They should be treated as a
separate data-and-training ablation, not silently substituted into this
six-hour pipeline.

## 5. Loss Function

Pure, unfiltered long-horizon grid-space MSE should not be the objective. It
rewards averaging over uncertain small-scale structures and therefore produces
smooth forecasts.

Let $\mathcal T_{\mathrm{obs}}$ be the real WeatherBench2 lead times decoded in
the current rollout. Use the total loss

$$
\mathcal L_{\mathrm{WB2}}
=
\sum_{\tau\in\mathcal T_{\mathrm{obs}}}
\alpha_\tau
\left[
\mathcal L_{\mathrm{state}}(\tau)
+ \lambda_{\mathrm{spec}}\mathcal L_{\mathrm{spec}}(\tau)
+ \lambda_{\mathrm{bias}}\mathcal L_{\mathrm{bias}}(\tau)
\right].
$$

For the initial pipeline,
$\mathcal T_{\mathrm{obs}}=\{6\ \mathrm{hours}\}$. Every term is computed from
a decoded forecast and its corresponding real WeatherBench2 state. All terms
should be area-weighted and normalized by variable and level.

### 5.1 Lead-dependent spectral state loss

Let $a_{v\ell m}$ denote a spherical-harmonic coefficient of a decoded
WeatherBench2 variable and level, where $v$ identifies the decoded channel,
$\ell$ is total wavenumber, and $m$ is zonal wavenumber. Define

$$
\mathcal L_{\mathrm{state}}(\tau)
=
\sum_{v,\ell,m}
w_v M_{\tau\ell}
\frac{
\left|\widehat a_{v\ell m}(\tau)-a^*_{v\ell m}(\tau)\right|^2
}{
\sigma^2_{v\ell}+\epsilon
}.
$$

$M_{\tau\ell}$ is a smooth, lead-dependent spectral taper:

- retain all resolved scales at short lead times;
- progressively reduce the pointwise penalty on unpredictable high
  wavenumbers at longer lead times;
- do not remove those wavenumbers from the forecast itself.

This avoids penalizing a realistic small-scale feature twice merely because it
is slightly displaced.

For the initial truth-start updates,
$\tau=\Delta t_{\mathrm{obs}}=6\ \mathrm{hours}$. For a stopped-prefix update,
$\tau=(p+1)\Delta t_{\mathrm{obs}}$ is the absolute lead from the original ERA5
initial condition, not merely the length of the differentiable suffix. This
allows the loss to become less pointwise at later prefix times while the
spectrum and bias terms continue to constrain realism.

Compute this loss only for decoded channels with corresponding real
WeatherBench2 targets. Do not add a parallel loss on Dinosaur's native
sigma-level state. A WeatherBench2 channel that the decoder cannot yet produce
is excluded until a valid diagnostic or prognostic output exists.

### 5.2 Spectrum loss

For each variable and total wavenumber, define spectral power

$$
P_{v\ell}
=
\sum_m |a_{v\ell m}|^2.
$$

Then penalize normalized power error:

$$
\mathcal L_{\mathrm{spec}}
=
\sum_{v,\ell}
w_v
\frac{
\left(\widehat P_{v\ell}-P^*_{v\ell}\right)^2
}{
\overline P_{v\ell}^{\,2}+\epsilon
},
$$

where $\overline P_{v\ell}$ is training-set climatological power. Unlike the
state loss, the spectrum loss continues to constrain small-scale amplitude at
long lead times. This is the primary guard against smoothing in the first
deterministic model.

### 5.3 Batch bias loss

Penalize systematic modal error across the batch:

$$
\mathcal L_{\mathrm{bias}}
=
\sum_{v,\ell,m}
\frac{
\left|
\mathbb E_{b}
\left[
\widehat a^{(b)}_{v\ell m}-a^{*(b)}_{v\ell m}
\right]
\right|^2
}{
\sigma^2_{v\ell}+\epsilon
}.
$$

This distinguishes persistent model drift from unpredictable trajectory error.

### 5.4 Credit assignment through latent states

There is deliberately no data loss on $S_{t_k}$ or $Q_k$. For an observed
endpoint $T$, each neural evaluation receives gradient through the chain

$$
\frac{d\mathcal L_{\mathrm{WB2}}}{d\theta}
=
\sum_k
\frac{\partial\mathcal L_{\mathrm{WB2}}}{\partial\widehat X_T}
\frac{\partial\widehat X_T}{\partial S_T}
\frac{\partial S_T}{\partial Q_k}
\frac{\partial Q_k}{\partial\theta}.
$$

This is why the inner states must remain in the differentiable graph even
though their numerical accuracy is never scored. Correction norms, internal
state norms, and conservation diagnostics should be logged as stability
diagnostics, not added as supervised targets in the first baseline.

Initial normalized loss weights should be:

$$
\lambda_{\mathrm{spec}}=0.1,
\qquad
\lambda_{\mathrm{bias}}=0.1.
$$

These values are starting points. Each loss must first be normalized so its
magnitude and gradient norm are interpretable. Weight selection and checkpoint
selection use 2019 validation data. The untouched 2020 test data must not
influence these choices.

## 6. Optimization and Hardware Strategy

Use the following initial optimizer configuration:

- AdamW;
- learning rate $2\times10^{-4}$;
- linear warmup followed by cosine decay;
- global gradient-norm clipping at 1.0;
- small weight decay applied to hidden weights, not normalization parameters or
  output biases;
- exponential moving average of neural parameters for validation.

For eight H100 GPUs:

- use data parallelism over independent truth-start windows or stopped-prefix
  trajectories;
- begin with one training example per GPU;
- use gradient accumulation to reach an effective batch size of at least 16
  when required by the batch-bias loss;
- compile the exact six-hour endpoint update once and compile the optional
  12-hour update separately;
- execute stopped prefixes without retaining activations and apply
  `stop_gradient` before the differentiable suffix;
- reuse the exact six-hour compiled update after a stopped prefix;
- rematerialize each neural-correction block during six-hour BPTT when memory
  requires it;
- use BF16 for neural-network matrix operations where stable;
- keep the Dinosaur state, SIL3 integration, reductions, and spherical-harmonic
  transforms in FP32 initially.

Freezing Dinosaur parameters removes their optimizer state and parameter
gradients, but the dycore remains in the BPTT graph for every differentiated
window. It is absent from the backward graph only for an explicitly stopped
prefix. Rematerialization trades additional forward computation for lower
activation memory; it does not make six-hour BPTT computationally cheap. With
the current data there is no exact sub-six-hour loss that removes this cost.

Checkpoints should contain:

- neural parameters and exponential moving average;
- optimizer and learning-rate state;
- normalization and output-scaling statistics;
- curriculum phase and sampler state;
- random-number state;
- exact model and dataset configuration.

## 7. Validation and Model Selection

Every candidate must be compared with the frozen `dino_rskin_apv` backbone
using identical initial conditions. Use 2019 for validation and checkpoint
selection. Run the locked 2020 `golden` protocol only for final reporting. The
existing 2014–2018 `iteration` protocol can still provide a fast
in-distribution diagnostic, but it is not a held-out score because those years
are now part of training.

Track at least:

- area-weighted RMSE and bias at 6 hours, 1 day, 3 days, 5 days, 10 days, and
  15 days;
- anomaly correlation for headline variables;
- power spectra and spectral-power ratios by lead time;
- kinetic-energy and enstrophy spectra;
- gradient and increment distributions;
- humidity extrema and negative-humidity frequency;
- surface-pressure and global-mass drift;
- temperature and wind extrema;
- frequency of non-finite or unstable rollouts;
- neural-correction norms by variable, level, and lead time.

Checkpoint selection should require both forecast improvement and realism. A
checkpoint with lower RMSE but materially degraded spectra should not be
selected as the first successful hybrid.

The initial success criteria are:

1. zero-correction parity with the existing backbone;
2. statistically repeatable improvement at 6-hour to 3-day leads;
3. no systematic loss of resolved spectral power relative to the backbone;
4. stable free forecasts through the existing 15-day evaluation horizon;
5. neural tendencies that remain bounded and physically interpretable.

## 8. First Controlled Ablations

After the baseline completes, change one design choice at a time:

1. neural coupling cadence: 15, 30, and 60 minutes, subject to the integer
   inner-step constraint;
2. truth-start-only training versus adding stopped six-hour prefixes;
3. six-hour-only loss versus full 12-hour BPTT with losses at both real
   endpoints;
4. column-network width: 128 and 256;
5. with and without horizontal-gradient inputs;
6. with and without spectrum and bias losses;
7. agentic Dinosaur versus original Dinosaur using the same corrector and
   training budget.

Only after these ablations should the project evaluate:

- a second branch consuming a causal WeatherBench-like reference state;
- recurrent neural memory;
- learned encoder or decoder corrections;
- non-local spherical networks;
- stochastic tendencies trained with an ensemble proper score.

## 9. Rationale

NeuralGCM demonstrated three choices that are directly applicable here:

- a column network can produce additive prognostic tendencies while the
  dynamical core handles resolved transport;
- learned tendencies can be held for approximately 30 minutes to avoid neural
  evaluation at every ODE step;
- a curriculum from short to longer differentiable rollouts is important for
  accuracy and stability.

It also used separate spectral accuracy, spectrum, and bias objectives to avoid
turning long-range deterministic forecasting into a smoothing problem. The
proposed pipeline preserves those useful inductive biases while keeping the
optimized Dinosaur backbone and its encoder/decoder fixed.

The verified six-hour data cadence makes six hours the shortest supervised
rollout. Exact training therefore uses a decoded WeatherBench2 endpoint loss
and a six-hour gradient path. The intervening dycore states are latent and are
allowed to take whatever values best support accurate observed forecasts.
Stopped prefixes provide exposure to model-generated states without extending
the backward path; they cannot shorten it below six hours with the current
targets. Longer than six-hour BPTT is promoted only by controlled 2019
validation evidence.

Primary reference:

- Dmitrii Kochkov et al., [Neural general circulation models for weather and
  climate](https://www.nature.com/articles/s41586-024-07744-y), *Nature* 632,
  1060–1066 (2024).

The stopped-prefix phase additionally separates two benefits of recurrent
training: exposure to model-generated states and long-range temporal gradients.
That distinction is studied directly in:

- Bjoern List et al., [Differentiability in Unrolled Training of Neural Physics
  Simulators on Transient Dynamics](https://arxiv.org/abs/2402.12971) (2024).
