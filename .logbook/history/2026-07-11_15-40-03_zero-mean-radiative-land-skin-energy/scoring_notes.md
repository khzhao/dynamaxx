# Scoring Notes

## Identity

- Candidate:
  dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori_rskin
- Incumbent:
  dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori
- Scoring HEAD: b3acd8d84198fab11a43aa9b029f51087be4caa6
- Accepted incumbent source commit:
  ea124f2d1b43e8e9e54efcbe0abf05e80f6b8001
- Frozen candidate diff SHA-256:
  a84e6b7448200603fb42d5b213723c1e083956cd8057107a9a349c2413b62594
- Patch identity: saved candidate.diff and the live binary git diff matched
  the frozen hash before and after fast, iteration, and validation. Two
  additional preflight/pre-report checks matched. The six expected tracked
  source/test files remained the only tracked changes, and protected untracked
  gifs/ was untouched.

## Commands

| Command | Start (UTC) | Finish (UTC) | Exit | Status |
| --- | --- | --- | --- | --- |
| uv run pytest | provided record | provided record | 0 | Not rerun by the Scorer. Exact-patch evidence: Ruff passed; radiative tests 25 passed; related land-skin tests 58 passed; registry/dependency tests 75 passed; compiled multi-initial phase and missing-anchor regression passed; full suite 379 passed and 2 skipped in 8m26s; git diff --check passed. |
| uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori_rskin | 2026-07-11T16:31:40.405Z | 2026-07-11T16:38:26.410Z | 0 | One fresh chunk with one effective worker; clean; no retry. |
| uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori_rskin --workers 4 | 2026-07-11T16:38:53.307Z | 2026-07-11T20:12:43.894Z | 0 | 229 of 229 fresh chunks; four effective GPU workers; clean; no retry. |
| uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori_rskin --workers 4 | 2026-07-11T20:13:31.628Z | 2026-07-11T20:59:56.359Z | 0 | Single permitted validation run; 46 of 46 fresh chunks; four effective GPU workers; clean; no retry. |

Command counts were exactly one candidate fast, one candidate iteration, and
one candidate validation; zero incumbent iteration, zero incumbent validation,
zero golden, and zero pytest commands by the Scorer. No evaluation command
failed or restarted. Validation ran exactly once after every iteration
promotion condition passed.

## Cache Reuse

The requested incumbent exactly matches the leaderboard incumbent and accepted
source commit ea124f2d1b43e8e9e54efcbe0abf05e80f6b8001. Candidate source,
registry, and test edits do not touch evaluation code and do not invalidate the
accepted cache under roles/SCORER.md.

For both iteration and validation, authoritative cache checks confirmed:

- the exact WeatherBench2 path, target-variable list, 1..15 lead-day range,
  protocol membership, and compatible evaluation code;
- artifact existence and JSON/CSV readability;
- finite primary scores exactly matching the leaderboard;
- 120 JSON records and 120 CSV rows per protocol;
- 60 exact-incumbent records plus 60 persistence records;
- one finite RMSE row for all four targets at all 15 daily leads in JSON and
  CSV;
- clean incumbent diagnostics with zero issues;
- exact hash equality with immutable accepted history before and after all
  candidate runs;
- candidate output paths distinct from incumbent output paths.

Iteration cache reused without recomputation:

- JSON:
  outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori.json
- JSON SHA-256:
  6e6f1844ac6e6bbe5fcc067c61483b6f51393155b7cefaf9543f8bbf173c6a49
- CSV:
  outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori.csv
- CSV SHA-256:
  7437b08470d110f579539a57ac628f853ada64c5bfdd9617e1d8fcf04ea451dd
- Primary score: -0.08429962366251152

Validation cache reused without recomputation:

- JSON:
  outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori.json
- JSON SHA-256:
  920b91240fe66eec975d4b60abcc4bfa79e7efa1620c59e49d38de2ab4cbabe9
- CSV:
  outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori.csv
- CSV SHA-256:
  0e3a0e7e45c344981af31d61aae9ce9a82e618502cc827f5f43e95a5f6e01dbf
- Primary score: -0.08458916260281377

No incumbent evaluation command ran, and no incumbent artifact was overwritten,
regenerated, or modified.

## Gate Status

- Tests gate: passed from supplied exact-patch evidence. The Scorer did not
  rerun pytest.
- Fast gate: passed. Candidate primary score -0.08026418259210333;
  failed=false, zero issues, 120 records, 60 exact-candidate rows, 60
  persistence rows, and finite JSON/CSV metrics.
- Iteration promotion gate: passed. Candidate -0.07908852007250675 versus
  cached incumbent -0.08429962366251152 gives delta
  +0.005211103590004776. The required delta was +0.002, so the margin above
  threshold was +0.003211103590004776. Diagnostics and both RMSE guardrails
  passed.
- Validation measurement gate: passed. Candidate -0.07929026517101266 versus
  cached incumbent -0.08458916260281377 gives delta
  +0.005298897431801106. The required delta was +0.001, so the margin above
  threshold was +0.004298897431801106. Diagnostics and both RMSE guardrails
  passed.
- Golden gate: not run, as required for iterative selection.

## RMSE Guardrails

Positive percentages mean worse candidate RMSE; negative values mean
improvement. Each protocol evaluated all 60 variable/lead comparisons.

### Iteration Early Mean, Days 1-5

| Variable | Candidate mean RMSE | Incumbent mean RMSE | Regression | Gate |
| --- | ---: | ---: | ---: | --- |
| 2m_temperature | 4.462104028882228 | 4.46210474736082 | -1.6101786776778548e-05% | pass |
| mean_sea_level_pressure | 651.8563660857668 | 651.8563774120016 | -1.7375353229228658e-06% | pass |
| geopotential_500 | 560.6277991618872 | 560.6278186801441 | -3.481499885101013e-06% | pass |
| 10m_u_component_of_wind | 3.8618510935305643 | 3.8618505231548577 | +1.4769492067226862e-05% | pass |

No iteration target exceeded the 2% early-mean regression limit.

### Iteration Worst Variable/Lead

| Variable | Worst lead | Candidate RMSE | Incumbent RMSE | Regression | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| 2m_temperature | 24 h | 2.445959651671579 | 2.4459591452954803 | +2.070255751425492e-05% | pass |
| mean_sea_level_pressure | 24 h | 353.29854472172934 | 353.29848065934186 | +1.813265297959356e-05% | pass |
| geopotential_500 | 24 h | 239.8949550594291 | 239.8946890889713 | +0.00011086967319438674% | pass |
| 10m_u_component_of_wind | 120 h | 4.599534752886427 | 4.599533412320271 | +2.9145698828275212e-05% | pass |

The worst iteration comparison was geopotential_500 at 24 hours,
+0.00011086967319438674%. Zero of 60 comparisons exceeded the 10% limit.

### Validation Early Mean, Days 1-5

| Variable | Candidate mean RMSE | Incumbent mean RMSE | Regression | Gate |
| --- | ---: | ---: | ---: | --- |
| 2m_temperature | 4.458783503352858 | 4.458783573817496 | -1.5803556598328832e-06% | pass |
| mean_sea_level_pressure | 639.7771192539298 | 639.7770762566176 | +6.720670949762443e-06% | pass |
| geopotential_500 | 553.3176659062386 | 553.317497982029 | +3.0348617256722546e-05% | pass |
| 10m_u_component_of_wind | 3.8264199602586464 | 3.8264208589197772 | -2.348568450720263e-05% | pass |

No validation target exceeded the 2% early-mean regression limit.

### Validation Worst Variable/Lead

| Variable | Worst lead | Candidate RMSE | Incumbent RMSE | Regression | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| 2m_temperature | 24 h | 2.4542982921744416 | 2.4542978280158354 | +1.891207338077284e-05% | pass |
| mean_sea_level_pressure | 48 h | 537.3176511330872 | 537.3174060674135 | +4.560910757760361e-05% | pass |
| geopotential_500 | 24 h | 234.86711805215154 | 234.8665682470304 | +0.00023409254252607515% | pass |
| 10m_u_component_of_wind | 96 h | 4.3452324099095705 | 4.3452321741983315 | +5.424594809256432e-06% | pass |

The worst validation comparison was geopotential_500 at 24 hours,
+0.00023409254252607515%. Zero of 60 comparisons exceeded the 10% limit.

## Late Window

Days 6-15 isolate the period after the accepted 120-240 hour ramp begins to
activate the candidate skin-energy term.

### Iteration

| Variable | Candidate mean RMSE | Incumbent mean RMSE | Absolute change | Relative change |
| --- | ---: | ---: | ---: | ---: |
| 2m_temperature | 6.4784401045510505 | 6.585097242208891 | -0.1066571376578409 | -1.619674451793882% |
| mean_sea_level_pressure | 932.8820729080699 | 933.7505984459228 | -0.8685255378529746 | -0.09301472355664299% |
| geopotential_500 | 1022.3918631020667 | 1023.135729920046 | -0.7438668179792103 | -0.0727046076318086% |
| 10m_u_component_of_wind | 4.839060137091178 | 4.840557413217945 | -0.0014972761267664225 | -0.030931894799509287% |

### Validation

| Variable | Candidate mean RMSE | Incumbent mean RMSE | Absolute change | Relative change |
| --- | ---: | ---: | ---: | ---: |
| 2m_temperature | 6.446535893116815 | 6.553309374512959 | -0.10677348139614384 | -1.6293062831949578% |
| mean_sea_level_pressure | 911.2192070286453 | 912.0667494590414 | -0.8475424303960608 | -0.09292548280032675% |
| geopotential_500 | 1019.1472375361649 | 1019.9273311949715 | -0.7800936588066634 | -0.07648521957860338% |
| 10m_u_component_of_wind | 4.783574659664718 | 4.78512591099941 | -0.0015512513346918055 | -0.032418192614869244% |

## Artifacts

- Candidate fast JSON SHA-256:
  10c0c88dd0bd782faad3010a1a5ffb528aa4f301df2ca85943144501811af9fe
- Candidate fast CSV SHA-256:
  a22193d21ea25ad61c8a294aa1e7785416ae08454bf166de07ae23919795accc
- Candidate iteration JSON SHA-256:
  4097de3f1dfc95a978e85c45a9e77d4a15a46f7feead6260c945617c3e888471
- Candidate iteration CSV SHA-256:
  62cce8abb724e50a6ff2f75857aa51fb9eb1c5dd622bab5ff3e7c836b9dc943c
- Candidate validation JSON SHA-256:
  663ec458c764e4d169842f71d129da349fab52dc2dc735b3279c1e30e52cbecf
- Candidate validation CSV SHA-256:
  3d1cda55f61c2bec08f8ccb0900a4352b6385e8e2d83d73a72e53177d9d4cd08

Raw paths and both incumbent hash sets are recorded in scores.json.

## Measurement Lessons

- The candidate improved mean days 6-15 T2m RMSE by -1.619674451793882%
  on iteration and -1.6293062831949578% on validation. The sign and magnitude
  reproduced across both fixed splits, consistent with the proposal's late
  land-skin hypothesis.
- Early days 1-5 stayed at numerical-trajectory scale. The largest early mean
  regression was below 0.00004% on both protocols, consistent with the
  unchanged 120-hour inactive window.
- Mean skill improved for all four targets on both protocols. T2m supplied the
  dominant change (+0.01963504286938267 iteration,
  +0.01996424847878364 validation), while MSLP, Z500, and U10 also improved
  modestly after the skin term became active. The private lower-boundary
  evolution therefore affected the coupled late trajectory rather than only
  the output observer.
- All four days 6-15 variable means improved on both splits, diagnostics stayed
  clean, and the largest single variable/lead regression was only
  +0.00023409254252607515%. The fixed zero-mean radiative formulation produced
  no measured stability or guardrail cost.
- Iteration and validation primary deltas were closely aligned:
  +0.005211103590004776 and +0.005298897431801106. No coefficient, cap, ramp,
  mask, albedo, emissivity, or thermal-inertia retune was performed after
  scoring.

## Anomalies

- Cache reuse: both incumbent protocols passed all authoritative checks and
  were reused without recomputation.
- Resource limits: none reached. The recorded machine had 48 CPUs,
  186098622464 bytes available RAM, four idle NVIDIA L4 GPUs with 22566 MiB
  free each, and 4439639015424 bytes free disk. Fast used one effective worker;
  iteration and validation used four effective GPU workers.
- Failed or restarted evaluation commands: none. Every candidate command
  exited 0, all chunks were fresh, and no evaluator retry occurred.
- Nonfinite or unstable outputs: none. Candidate JSON and CSV primary/record
  metrics were finite, and fixed diagnostics reported zero issues.
- Validation discipline: validation ran exactly once, only after the iteration
  delta and all diagnostic/guardrail conditions passed.
- Repository scope: the Scorer modified only candidate outputs/eval artifacts
  and scores.json/scoring_notes.md. Source, tests, proposal, leaderboard,
  roles, evaluation code, git state, incumbent artifacts, and protected gifs/
  were not changed by the Scorer.

## Recommendation To Orchestrator

The candidate passed the measured fast, iteration-promotion, and validation
gates with clean diagnostics and no RMSE guardrail violation. Use these
measurements for the Orchestrator-owned terminal decision. This Scorer report
does not accept or reject the candidate.
