# Scoring Notes

## Identity

- Candidate: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori
- Incumbent: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si
- Scoring HEAD: 6f4a63731b2dd7598ef9a6c3c085365ceed7aea9
- Frozen candidate diff SHA-256:
  3fedb24a90283f166c29ce487ea4d82f65f58195c75a17f0a441425dbb6a20e3
- Patch identity check: the live tracked diff matched the frozen hash before
  fast, after fast, after iteration, and after validation.

## Commands

| Command | Start (UTC) | Finish (UTC) | Exit | Status |
| --- | --- | --- | --- | --- |
| <code>uv run pytest</code> | provided record | provided record | 0 | Not rerun by the Scorer. Exact-patch evidence: focused Orchestrator run 13 passed and 273 deselected; Implementer full suite 352 passed and 2 skipped; related subset 33 passed; dependency/registry subset 73 passed; Ruff and git diff check passed. |
| <code>uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori</code> | 2026-07-11T06:19:48.667Z | 2026-07-11T06:26:39.272Z | 0 | One fresh serial chunk; clean. |
| <code>uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori --workers 4</code> | 2026-07-11T06:26:46.424Z | 2026-07-11T09:59:04.870Z | 0 | 229 of 229 fresh chunks; four effective GPU workers; no retry. |
| <code>uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori --workers 4</code> | 2026-07-11T09:59:10.861Z | 2026-07-11T10:45:34.884Z | 0 | Single permitted run; 46 of 46 fresh chunks; four effective GPU workers; no retry. |

Command counts were one candidate fast, one candidate iteration, one candidate
validation, zero incumbent iteration, zero incumbent validation, and zero
golden. No command was restarted.

## Cache Reuse

The requested incumbent exactly matches
.logbook/leaderboard.json.incumbent_model_name and accepted source commit
603f44a9b052557bd3bf3a16a9dcd9c05f343449. Current HEAD differs from that
source commit only by accepted logbook and leaderboard artifacts. Neither
committed nor working-tree changes touch the evaluation runner, fixed protocol,
data loader, metrics, CLI, or configuration. The candidate source, registry,
and test edits are not cache invalidation under roles/SCORER.md.

For both iteration and validation, cache validation confirmed:

- exact fixed WeatherBench2 path, target-variable list, 1..15 lead-day range,
  and protocol membership;
- artifact existence and JSON/CSV readability;
- finite primary score and exact score equality with the leaderboard;
- 120 JSON records and 120 CSV rows;
- 60 exact-incumbent records plus 60 persistence records;
- one finite RMSE row for every combination of four target variables and 15
  daily leads in both JSON and CSV;
- clean incumbent diagnostics with zero issues;
- exact artifact-hash equality with the immutable accepted history.

Iteration cache reused without recomputation:

- JSON:
  outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si.json
- JSON SHA-256:
  11f3ba30500d46991a97dcff649d28476d33d1bb76b35739cba35bcd177a11a9
- CSV:
  outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si.csv
- CSV SHA-256:
  b10cb3ba768ff9584bac7eb093069058dedf3c74dc780c32f188d9fa30d99e47
- Primary score: -0.08966691030501653

Validation cache reused without recomputation:

- JSON:
  outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si.json
- JSON SHA-256:
  f79511b3011a42fac75815b6e437eb54e976d9e0877c84e2dc43e581631858c7
- CSV:
  outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si.csv
- CSV SHA-256:
  66ba46c75cc706e008b2dcb6ccc258b24094872635382d0238fe2e9ae59991a7
- Primary score: -0.09015390068642175

## Gate Status

- Tests gate: passed from exact-patch evidence supplied by the Orchestrator and
  Implementer.
- Fast gate: passed. Candidate primary -0.08508207852031233; diagnostics
  failed=false, zero issues, 120 records, and all numeric metrics finite.
- Iteration promotion gate: passed. Candidate -0.08429962366251152 versus
  cached incumbent -0.08966691030501653; delta +0.005367286642505006,
  exceeding +0.002 by +0.003367286642505006. Diagnostics are clean, all
  early-mean guardrails pass, and no variable/lead exceeds the 10% limit.
- Validation acceptance gate: passed as measured. Candidate
  -0.08458916260281377 versus cached incumbent -0.09015390068642175; delta
  +0.005564738083607981, exceeding +0.001 by +0.004564738083607981.
  Diagnostics are clean and all early-mean guardrails pass.
- Golden gate: not run, as required for iterative selection.

## RMSE Guardrails

Positive regression percentages mean worse candidate RMSE; negative values mean
improvement. The worst-lead column is the maximum relative regression over all
15 daily leads for that protocol and variable.

| Protocol | Variable | Candidate early mean | Incumbent early mean | Early regression | Worst lead | Worst-lead regression |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| iteration | 2m_temperature | 4.46210474736082 | 4.462104892072657 | -0.000003243129% | 72 h | +0.000006118681% |
| iteration | mean_sea_level_pressure | 651.8563774120016 | 651.8563388558034 | +0.000005914831% | 96 h | +0.000026033760% |
| iteration | geopotential_500 | 560.6278186801441 | 560.628089529327 | -0.000048311740% | 240 h | -0.000017764069% |
| iteration | 10m_u_component_of_wind | 3.8618505231548577 | 3.861851763905954 | -0.000032128398% | 24 h | -0.000005913118% |
| validation | 2m_temperature | 4.458783573817496 | 4.458783792234554 | -0.000004898579% | 48 h | +0.000009178307% |
| validation | mean_sea_level_pressure | 639.7770762566176 | 639.7770691285048 | +0.000001114156% | 144 h | +0.000038483996% |
| validation | geopotential_500 | 553.317497982029 | 553.3175811459055 | -0.000015030044% | 240 h | +0.000056698269% |
| validation | 10m_u_component_of_wind | 3.8264208589197772 | 3.8264192627965583 | +0.000041713234% | 264 h | +0.000072217627% |

Iteration has zero greater-than-10% variable/lead violations. Validation also
has zero such violations as an additional reported diagnostic.

## Late Window

Leads 6-15 days isolate the period in which the accepted ramp can affect the
ocean observer.

| Protocol | Variable | Candidate mean RMSE | Incumbent mean RMSE | Absolute change | Relative change |
| --- | --- | ---: | ---: | ---: | ---: |
| iteration | 2m_temperature | 6.585097242208891 | 6.700298348364709 | -0.11520110615581736 | -1.7193429331983945% |
| iteration | mean_sea_level_pressure | 933.7505984459228 | 933.7506263673819 | -0.000027921459036406304 | -0.000002990248% |
| iteration | geopotential_500 | 1023.135729920046 | 1023.1361659163898 | -0.00043599634386737307 | -0.000042613716% |
| iteration | 10m_u_component_of_wind | 4.840557413217945 | 4.840558511766743 | -0.000001098548798594834 | -0.000022694670% |
| validation | 2m_temperature | 6.553309374512959 | 6.670681850664512 | -0.11737247615155333 | -1.7595274183232266% |
| validation | mean_sea_level_pressure | 912.0667494590414 | 912.0667540513205 | -0.000004592279083226458 | -0.000000503503% |
| validation | geopotential_500 | 1019.9273311949715 | 1019.9271994728506 | +0.0001317221209546915 | +0.000012914855% |
| validation | 10m_u_component_of_wind | 4.78512591099941 | 4.78512418061847 | +0.0000017303809398683256 | +0.000036161673% |

## Measurement Lessons

- The ocean-anchor observer improves late-window T2m mean RMSE by 1.7193% on
  iteration and 1.7595% on validation, reproducing the intended marine
  lower-boundary effect across both splits.
- The primary-score gains are similarly split-consistent:
  +0.005367286642505006 on iteration and +0.005564738083607981 on validation.
- Early leads remain effectively identical to the incumbent. The largest
  early-mean regression is only +0.000005914831% on iteration and
  +0.000041713234% on validation.
- Non-T2m late-window differences are at numerical-noise scale. Their largest
  absolute relative change is +0.000036161673%, consistent with the intended
  output-only isolation and far below fixed guardrails.

## Anomalies

- Cache reuse: both incumbent protocols passed every validation check and were
  reused. No incumbent recomputation was authorized or needed.
- Resource limits: the Orchestrator recorded about 174 GiB available RAM, four
  idle NVIDIA L4 GPUs with about 22 GiB free each, and about 4134 GiB free disk.
  Iteration and validation used four effective GPU workers; fast used the fixed
  command default of one.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none. All candidate primary scores and record
  metrics are finite; fixed diagnostics reported zero issues.
- Physical plausibility: no fixed diagnostic failure, instability, severe
  oversmoothing signal, or guardrail regression was measured. No additional
  qualitative field-plot protocol was authorized.
- Validation discipline: validation ran exactly once for this frozen
  implementation state.

## Recommendation To Orchestrator

All measured fixed gates pass with split-consistent primary-score gains, clean
diagnostics, complete cache-backed incumbent comparisons, and no RMSE guardrail
violation. Recommend proceeding to the Orchestrator's acceptance review. This
Scorer report does not accept, reject, modify, revert, or commit the candidate.
