# First Training Pipeline for a Dinosaur Neural Corrector

Status: production-scale deterministic training implemented; production run active

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
- use exact backpropagation through time (BPTT) through the 6-, 12-, and 24-hour
  stages;
- beyond 24 hours, keep the numerical rollout continuous but stop gradients at
  fixed 24-hour boundaries, retaining all previous lead losses and adding
  exactly one new loss at each promotion to 48, 96, 192, and 360 hours;
- use 2014–2018 for the first pipeline and stability pilot, while computing
  frozen statistics from 1979–2018 and expanding production training to that
  full period before the expensive multi-day stages;
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

The controlled pilot configuration used:

- four residual MLP blocks;
- hidden width 256;
- SiLU activations;
- normalization of input features using training-set statistics;
- a zero-initialized output projection;
- fixed, per-output tendency scales.

That pilot has exactly 1,111,605 trainable parameters for the active 172 input
and 53 tendency channels. The first production control uses width 384 and eight
residual blocks, for exactly 4,820,789 trainable parameters. This is close to
the 5,088,287 parameters in the learned-physics portion of the published
deterministic NeuralGCM-1.4 checkpoint. That checkpoint has 18,343,580 learned
parameters in total: 9,019,390 in its learned encoder, 4,235,903 in its learned
decoder, and 5,088,287 in learned physics.

The larger production candidate uses width 800 and eight residual blocks, for
exactly 20,692,853 trainable parameters. Width 800 remains aligned for BF16
matrix multiplication on H100 tensor cores. Dynamaxx still freezes its encoder
and decoder, so this count belongs entirely to the learned corrector. The
4.82M run remains the capacity control; throughput and forecast skill for the
20.69M candidate must be measured separately rather than inferred from the
smaller run.

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

The implemented zero-start baseline currently uses SI scales of
$10^{-10}\ \mathrm{s}^{-2}$ for vorticity and divergence, $10^{-5}\
\mathrm{K\,s}^{-1}$ for temperature variation, $10^{-9}\ \mathrm{s}^{-1}$
for specific humidity, and $10^{-7}\ \mathrm{s}^{-1}$ for log surface
pressure before conversion to Dinosaur units. These are conservative project
starting values, not published NeuralGCM constants. The zero output projection
makes them inactive at initialization; frozen-backbone tendency statistics and
the logged correction norms must validate them before production training.

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

Use this initial pilot and final chronological split:

- pipeline/stability pilot: 2014–2018 inclusive;
- production training: 1979–2018 inclusive;
- validation and checkpoint selection: 2019;
- untouched final test: 2020.

The repository's existing `iteration` protocol covers the pilot period exactly.
It is therefore an in-distribution training diagnostic for the hybrid model,
not held-out evidence. Use the pilot to complete the fixed-set overfit and the
6-, 12-, and at most 24-hour stages. Before spending the multi-day curriculum
budget, restart or deliberately warm-start a production run sampled across
1979–2018. A warm start must be recorded because it initially overweights the
recent pilot years. The existing `validation` protocol on 2019 and locked
`golden` protocol on 2020 align with the validation and final test split above.
Do not inspect or tune against 2020 until final reporting.

The earlier 1959–1978 and later 2021–2023 data can be considered only in a
separate data-split experiment.

Every sampled rollout, including its target endpoint, must remain inside one
split. For example, the final training start must be early enough that its
target does not cross into 2019, and a validation rollout must not use a target
from 2020.

Compute all normalization, climatology, and spectral statistics from the full
1979–2018 production-training split and freeze them, including during the
2014–2018 pilot. The implementation estimates these statistics from a
reproducible uniform sample and caches them locally; production runs should use
a sample count large enough to cover seasons and synoptic times. Batch sampling
should not disproportionately favor long, contiguous periods from a small
number of years.

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

The primary recipe therefore uses exact BPTT through 24 hours. At longer
horizons, it advances one continuous on-policy trajectory and detaches the
recurrent state after every 24-hour block. If a boundary is also supervised,
the model decodes and records that loss before detaching the state. Forecast
values, clocks, and latent state values are unchanged by the detach.

For example, the 48-hour loss differentiates through hours 24--48, while the
6-, 12-, and 24-hour losses retain their exact gradients within hours 0--24.
The 96-hour loss differentiates through hours 72--96. An intervening block with
no selected endpoint loss still supplies the on-policy state seen by the next
block, but receives no direct temporal gradient on that update. Because the
same corrector parameters are used in every block, all scored blocks update the
same network.

Full-horizon BPTT remains a controlled credit-assignment ablation. A separate
hourly dataset would be required if exact one-hour objectives are later needed;
the stopped-gradient boundaries do not invent new supervision.

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

### 4.3 Phase B: logarithmic rollout curriculum

After six-hour training is stable, promote the continuous rollout through the
following fixed horizons:

| Stage | Rollout horizon | Supervised lead times | Maximum gradient history |
| --- | ---: | --- | ---: |
| A | 6 h | 6 h | 6 h |
| B | 12 h | 6, 12 h | 12 h |
| C | 24 h | 6, 12, 24 h | 24 h |
| D | 48 h | 6, 12, 24, 48 h | 24 h |
| E | 96 h / 4 d | 6, 12, 24, 48, 96 h | 24 h |
| F | 192 h / 8 d | 6, 12, 24, 48, 96, 192 h | 24 h |
| G | 360 h / 15 d | 6, 12, 24, 48, 96, 192, 360 h | 24 h |

The final promotion ends at the required 15-day forecast horizon rather than
continuing the doubling sequence to 384 hours. Each stage retains every loss
from the preceding stage and adds exactly one new lead-time loss. This anchors
short-range accuracy while exposing the corrector to progressively later
on-policy states.

Promote to the next stage only after the current stage has finite gradients,
bounded correction norms, stable free rollouts through its horizon, and a
validation loss that has stopped improving materially. Promotion changes the
static rollout and loss schedule, so each stage has its own compiled training
step. The backward pass is exact for horizons at or below 24 hours and bounded
to one 24-hour block thereafter.

At every stage, the recurrent state remains continuous. The model is never
teacher-forced, decoded and re-encoded, or replaced at a supervised lead. A
decoded loss observes that state without modifying it, and all dycore and
neural states between the listed lead times remain latent.

### 4.4 Bounded BPTT on a continuous trajectory

The primary curriculum uses a configurable 24-hour BPTT window. Rollout events
are the union of supervised lead times and fixed 24-hour detach boundaries. At
each event, the dycore first reaches the exact boundary; the trainer records a
forecast if that lead is supervised, then applies `stop_gradient` to the
complete recurrent hybrid state when the event is a detach boundary. It never
teacher-forces, re-encodes ERA5, or changes the numerical state.

This bounds activation history and reverse-mode dycore work independently of
the 15-day forward exposure. It also deliberately changes temporal credit
assignment, so full-horizon BPTT is retained as an ablation rather than treated
as mathematically equivalent. The window is exposed as
`--bptt-window-hours`; its production default is 24.

## 5. Loss Function

Pure, unfiltered long-horizon grid-space MSE should not be the objective. It
rewards averaging over uncertain small-scale structures and therefore produces
smooth forecasts.

Let $\mathcal T_{\mathrm{obs}}(T)$ be the logarithmically spaced WeatherBench2
lead times decoded for a rollout horizon $T$. The curriculum defines

$$
\mathcal T_{\mathrm{obs}}(T)
=
\left\{6,12,24,48,96,192\right\}
\cap (0,T]
$$

in hours, with 360 hours appended when $T=360\ \mathrm{hours}$. Use the total
loss

$$
\mathcal L_{\mathrm{WB2}}
=
\sum_{\tau\in\mathcal T_{\mathrm{obs}}(T)}
\alpha_\tau
\left[
\mathcal L_{\mathrm{state}}(\tau)
+ \lambda_{\mathrm{spec}}\mathcal L_{\mathrm{spec}}(\tau)
+ \lambda_{\mathrm{bias}}\mathcal L_{\mathrm{bias}}(\tau)
\right].
$$

The lead weights must satisfy

$$
\sum_{\tau\in\mathcal T_{\mathrm{obs}}(T)}\alpha_\tau=1,
$$

so adding a lead time does not increase the total loss merely by adding another
term. Use uniform lead weights
$\alpha_\tau=1/|\mathcal T_{\mathrm{obs}}(T)|$ for the baseline. Initially
$\mathcal T_{\mathrm{obs}}(6\ \mathrm{h})=\{6\ \mathrm{h}\}$. Every term is
computed from a decoded forecast and its corresponding real WeatherBench2
state. All terms should be area-weighted and normalized by variable and level.

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

The implemented starting parameterization keeps full resolution through 24
hours, moves the fully weighted cutoff logarithmically to 25% of the resolved
wavenumber range by 360 hours, and uses a cosine transition spanning 15% of the
range. These three values are explicit project starting choices, not values
reported by NeuralGCM, and must be treated as controlled hyperparameters.

This avoids penalizing a realistic small-scale feature twice merely because it
is slightly displaced.

For the initial truth-start updates,
$\tau=\Delta t_{\mathrm{obs}}=6\ \mathrm{hours}$. Under bounded BPTT, $\tau$
remains the absolute lead from the original ERA5 initial condition, not the
length of the differentiable block containing that loss. This allows the loss
to become less pointwise at later forecast times while the spectrum and bias
terms continue to constrain realism.

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
The memory-safe implementation forms this expectation across the eight devices
for each device-local microbatch, then averages the two accumulated bias losses.
It does not run a separate forecast merely to form a sixteen-example bias
reference. State and spectrum gradients are still accumulated over all sixteen
examples. A single exact sixteen-example bias expectation can be used when two
examples per device fit simultaneously; that execution variant must first pass
the OOM gate.

### 5.4 Credit assignment through latent states

There is deliberately no data loss on $S_{t_k}$ or $Q_k$. Let $b(\tau)$ be the
start of the 24-hour gradient block containing the supervised endpoint
$\tau$, with an endpoint on a detach boundary assigned to the block that ends
there. Bounded BPTT computes

$$
\frac{d\mathcal L_{\mathrm{WB2}}}{d\theta}
=
\sum_{\tau\in\mathcal T_{\mathrm{obs}}(T)}
\alpha_\tau
\sum_{k:b(\tau)\leq t_k<\tau}
\frac{\partial\mathcal L_\tau}{\partial\widehat X_\tau}
\frac{\partial\widehat X_\tau}{\partial S_\tau}
\frac{\partial S_\tau}{\partial Q_k}
\frac{\partial Q_k}{\partial\theta}.
$$

Inner states within that block remain in the differentiable graph even though
their numerical accuracy is never scored. States in earlier blocks remain in
the forward trajectory but are detached from that endpoint loss. Correction
norms, internal state norms, and conservation diagnostics should be logged as
stability diagnostics, not added as supervised targets in the first baseline.

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

- use data parallelism over independent truth-start trajectories;
- begin with one training example per GPU;
- use gradient accumulation to reach an effective batch size of at least 16
  when required by the batch-bias loss;
- compile one static training step for each curriculum horizon and reuse it for
  every update within that stage;
- apply `stop_gradient` to the complete recurrent state every 24 forecast
  hours, after decoding any loss at the shared boundary;
- rematerialize neural-correction blocks during BPTT when memory requires it;
- use BF16 for neural-network matrix operations where stable;
- keep the Dinosaur state, SIL3 integration, reductions, and spherical-harmonic
  transforms in FP32 initially.

Freezing Dinosaur parameters removes their optimizer state and parameter
gradients, but the dycore remains in the BPTT graph inside each 24-hour gradient
window. Earlier blocks are absent from the backward graph after their recurrent
state is detached. Rematerialization trades additional forward computation for
lower activation memory inside a block. With the current data there is no exact
sub-six-hour loss that removes the initial six-hour gradient path.

At the configured 30-minute correction cadence and 15-minute dycore cadence,
the final 360-hour stage contains 720 neural evaluations and 1,440 completed
dycore steps per example. Its backward activation history is nevertheless
bounded to 48 neural evaluations and 96 dycore steps by the 24-hour BPTT
window. Treat memory, throughput, and gradient finiteness at each promotion as
measured gates.

Checkpoints should contain:

- neural parameters and exponential moving average;
- optimizer and learning-rate state;
- normalization and output-scaling statistics;
- curriculum phase and sampler state;
- random-number state;
- exact model and dataset configuration.

Checkpoints, training statistics, and run configuration are written only under
the configured local output directory. W&B receives scalar training and
validation statistics only. The logger disables code capture, Git metadata,
console capture, environment metadata, system monitoring, and requirement
capture; it never calls the W&B artifact API.
The local `best.json` manifest tracks the lowest finite 2019 validation loss
within a stage; scientific acceptance still requires the realism gates below,
so that manifest is a candidate selector rather than automatic acceptance.

Two deterministic performance caches are also stored locally. They are not
checkpoints and are never sent to W&B:

- the initialized-state cache stores the fixed
  WeatherBench-to-Dinosaur initialization for each timestamp, before any
  neural correction is evaluated;
- the modal-target cache stores the spherical-harmonic transform of each fixed
  ERA5 truth target used by the loss.

Both caches are fingerprinted by the dataset, variables, cache format, and
dycore configuration. The neural parameters are absent from both mappings, so
the caches remain valid while the corrector is trained and across curriculum
stages that use the same dycore and data. For a local dataset, the default cache
root is `dynamaxx-training-cache` beside the dataset. The 2014–2019 pilot cache
occupies roughly 42 GiB for initialized states and 29 GiB for modal targets.
The trainer preloads both into host memory, uses parallel host reads while
building them, prefetches one deterministic batch, and transfers already
sharded batches directly to the eight devices.

### 6.1 Running one stage

The executable trains one static horizon at a time. Its defaults use all local
JAX devices, one example per device, two accumulated microbatches, the
2014–2018 pilot interval, 2019 validation, and locally cached 1979–2018
statistics:

```bash
dynamaxx-train-hybrid \
  --dataset /mnt/data/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative \
  --output /mnt/data/dynamaxx-training-cache/checkpoints/hybrid-production-20m/6h \
  --hidden-size 800 \
  --residual-blocks 8 \
  --horizon-hours 6 \
  --bptt-window-hours 24
```

The first launch builds the deterministic caches automatically. They can be
built separately before opening a W&B run:

```bash
dynamaxx-train-hybrid \
  --dataset /mnt/data/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative \
  --output /mnt/data/dynamaxx-training-cache/checkpoints/hybrid-production-20m/6h \
  --horizon-hours 6 \
  --state-cache-only \
  --data-loader-workers 8 \
  --state-cache-workers 8 \
  --no-wandb
```

`--bptt-window-hours 24` is the default. It produces exact BPTT for the 6-,
12-, and 24-hour stages and fixed 24-hour gradient blocks for longer stages.
`--no-state-cache`, `--no-target-cache`, and `--no-prefetch` are diagnostic
fallbacks. `--per-device-batch-size` and `--gradient-accumulation-steps` allow
an equivalent global batch to be benchmarked with different device-local
execution, while `--no-rollout-rematerialization` is an explicit memory-for-
compute experiment that must pass an OOM smoke test before production use.
`--pack-gradient-accumulation` places the two configured microbatches in one
device-local execution. Their two eight-example bias groups, global batch,
averaged gradient, optimizer update, and checkpoint configuration remain
unchanged. For the 4.82M-parameter control model on eight H100s, sequential
accumulation takes approximately 2.55 seconds per six-hour update; packing the
same global batch of 16 takes approximately 2.06 seconds and sustains 7.66
examples per second. The packed update and its physical-metric validation both
complete without OOM. The curriculum runner tries packing first and falls back
to sequential accumulation if a longer horizon exceeds memory. These timings
do not yet describe the 20.69M candidate; it requires its own packed and
sequential OOM/throughput smoke tests.

Validation logs WeatherBench2-compatible physical metrics in addition to the
training objective. The scalar names are
`validation/weatherbench2/rmse/<channel>/<lead>h` and
`validation/weatherbench2/bias/<channel>/<lead>h`. RMSE uses physical units,
WeatherBench2 latitude-cell area weights, and the benchmark ordering of
averaging squared error across the globe and examples before taking the square
root. Headline channels are T2m, MSLP, Z500, T850, Q700, U850, V850, U10, and
V10. These random 2019 validation samples track training progress; final SOTA
reporting uses the fixed `weatherbench2` protocol with all 732 00/12 UTC starts
in 2020 and daily leads through day 15.

`WANDB_API_KEY` and, optionally, `WANDB_PROJECT` are read by W&B from the
environment. `--wandb-project` can set the project explicitly. Use `--no-wandb`
for a local-only run. `--resume` resumes the exact latest local checkpoint with
the same configuration and W&B run. `--stop-at-step N` bounds a run at an
absolute optimizer step while leaving the configured schedule and checkpoint
compatible with a later `--resume`. After promotion criteria are met, start the
next static horizon from the selected previous EMA without carrying optimizer
state:

```bash
dynamaxx-train-hybrid \
  --output /mnt/data/dynamaxx-training-cache/checkpoints/hybrid-production-20m/12h \
  --horizon-hours 12 \
  --initialize-from /mnt/data/dynamaxx-training-cache/checkpoints/hybrid-production-20m/6h/step_000100000.pkl
```

### 6.2 One-week full-curriculum budget

A flat optimizer-step count at every horizon is not viable: rollout work grows
approximately in proportion to horizon. The bounded production runner instead
holds simulated forecast-hours approximately constant across stages:

| Horizon | Maximum updates | Six-hour-equivalent updates |
| ---: | ---: | ---: |
| 6 h | 20,000 | 20,000 |
| 12 h | 10,000 | 20,000 |
| 24 h | 5,000 | 20,000 |
| 48 h | 2,500 | 20,000 |
| 96 h | 1,250 | 20,000 |
| 192 h | 625 | 20,000 |
| 360 h | 334 | 20,040 |

This is 39,709 optimizer updates across the complete curriculum. For context,
published NeuralGCM models used 25,000 updates at 0.7°, 26,000 at 1.4°,
38,000 at 2.8°, and 43,000 for the 1.4° stochastic ensemble. Those are total
training updates, not per-stage counts. The deterministic NeuralGCM curricula
ended at 60–72-hour unrolls and the ensemble curriculum ended at 120 hours;
their 15-day forecast evaluations did not use a 15-day training stage. See
[Supplementary Tables G4–G5](https://arxiv.org/pdf/2311.07222).

At the measured 4.82M control's packed six-hour rate of 2.06 seconds per update,
the linear rollout projection is 80.1 wall-clock compute-hours, or 3.3 days on the
same eight H100s. A factor-of-two allowance for longer-horizon inefficiency,
validation, and compilation keeps the plan within one week. These are stage
maxima, not evidence that every stage needs the same number of parameter
updates.

Run or resume the complete sequence with:

```bash
uv run dynamaxx-train-hybrid-curriculum \
  --output-root /mnt/data/dynamaxx-training-cache/checkpoints/hybrid-production-20m \
  --reference-6h-steps 20000 \
  --bptt-window-hours 24 \
  --wandb-project dynamaxx
```

The runner uses the existing configuration when a local stage checkpoint is
present, stops that stage at its horizon-weighted maximum, selects its local
best-validation EMA checkpoint, and starts the next horizon in a fresh JAX
process. It logs scalar statistics to a separate W&B run per horizon. Packed
accumulation is attempted first; a device-memory failure automatically retries
the same global batch with sequential accumulation. Any other failure stops
the sequence and leaves the latest local checkpoint resumable.

## 7. Validation and Model Selection

Every candidate must be compared with the frozen `dino_rskin_apv` backbone
using identical initial conditions. Use 2019 for validation and checkpoint
selection. Run the locked 2020 `golden` protocol only for final reporting. The
existing 2014–2018 `iteration` protocol can still provide a fast
in-distribution diagnostic, but it is not a held-out score because those years
are part of both the pilot and final production training periods.

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
2. 24-hour bounded BPTT versus full-horizon temporal credit assignment;
3. retaining all logarithmic lead losses versus supervising only the newest
   lead at each curriculum stage;
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
- a curriculum from short to longer on-policy rollouts is important for
  accuracy and stability.

It also used separate spectral accuracy, spectrum, and bias objectives to avoid
turning long-range deterministic forecasting into a smoothing problem. The
proposed pipeline preserves those useful inductive biases while keeping the
optimized Dinosaur backbone and its encoder/decoder fixed.

The verified six-hour data cadence makes six hours the shortest supervised
rollout. Training begins with that exact decoded endpoint loss, then doubles
the rollout horizon while retaining earlier logarithmic lead losses and adding
one new loss at 12, 24, 48, 96, and 192 hours before the final 360-hour lead.
The intervening dycore states are latent and are allowed to take whatever values
best support accurate observed forecasts. Exact temporal credit is retained
through 24 hours; later stages use fixed 24-hour gradient blocks while keeping
the full numerical trajectory continuous.

Primary reference:

- Dmitrii Kochkov et al., [Neural general circulation models for weather and
  climate](https://www.nature.com/articles/s41586-024-07744-y), *Nature* 632,
  1060–1066 (2024).

The bounded-BPTT ablation separates two benefits of recurrent training:
exposure to model-generated states and long-range temporal gradients. That
distinction is studied directly in:

- Bjoern List et al., [Differentiability in Unrolled Training of Neural Physics
  Simulators on Transient Dynamics](https://arxiv.org/abs/2402.12971) (2024).
