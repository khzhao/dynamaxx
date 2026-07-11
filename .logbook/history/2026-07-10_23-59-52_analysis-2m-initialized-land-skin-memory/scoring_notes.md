# Scoring Notes

## Identity

- Candidate: `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si`
- Incumbent: `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri`
- Scoring HEAD: `07cf68b922784894415df64e36368a60f2df5080`
- Frozen candidate diff SHA-256: `efba29f26b4ed4145ca6b5b137d52aaff0f9f885c1f528a65500eb6d76bbdef1`
- Patch identity check: the live tracked diff matched the frozen hash before scoring and again after validation.

## Commands

| Command | Start (UTC) | Finish (UTC) | Exit | Status |
| --- | --- | --- | --- | --- |
| `uv run pytest` | provided record | provided record | `0` | Not rerun by Scorer. Exact-patch evidence: focused Orchestrator run `15 passed, 259 deselected`; Implementer full suite `340 passed, 2 skipped`. |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si` | `2026-07-11T00:47:37.577Z` | `2026-07-11T00:54:17.209Z` | `0` | One fresh serial chunk; clean. |
| `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si --workers 4` | `2026-07-11T00:54:51.035Z` | `2026-07-11T04:26:30.432Z` | `0` | `229/229` fresh chunks; four effective GPU workers; no retry. |
| `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si --workers 4` | `2026-07-11T04:27:16.506Z` | `2026-07-11T05:12:54.405Z` | `0` | Single permitted run; `46/46` fresh chunks; four effective GPU workers; no retry. |

No incumbent command and no `golden` command was run.

## Cache Reuse

The requested incumbent exactly matches `.logbook/leaderboard.json.incumbent_model_name`. The leaderboard points to accepted source commit `3fb32ff048b00b779d7e16a2c72e728866a4f4ba`. Current HEAD differs from that source commit only through accepted logbook and leaderboard artifacts, and there is no committed or working-tree change under the evaluation runner, protocol, data, CLI, or fixed-path code. Candidate source, registry, and test edits are not cache invalidation under `roles/SCORER.md`.

For both `iteration` and `validation`, the cache checks confirmed:

- exact fixed WeatherBench2 path, target-variable list, `1..15` lead-day range, and protocol membership;
- artifact existence, JSON/CSV readability, finite primary score, and exact equality with the leaderboard score;
- `120` JSON records and `120` CSV rows;
- `60` exact-incumbent records plus `60` persistence records;
- one finite RMSE guardrail record for every combination of four target variables and 15 daily leads;
- clean incumbent diagnostics with zero issues.

Iteration cache reused without recomputation:

- JSON: `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri.json`
- JSON SHA-256: `6897a9281a61a9255c1b3df6bbe6e29a8151f3106e84ca16f8ed1f4b8c24775f`
- CSV: `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri.csv`
- CSV SHA-256: `04038ee2f49e0e49b46284aab7726549c1715247ca5f1b3f1e0553fc80c0478a`
- Primary score: `-0.10655439732760863`

Validation cache reused without recomputation:

- JSON: `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri.json`
- JSON SHA-256: `6c2933bc7822572b5f88058f7408f211f618d0492ae7800bdbd6f27da66d77e4`
- CSV: `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri.csv`
- CSV SHA-256: `8c3dd3f9f1f6edfae59f050ddbf7945d62adbc25629c7b0388c5b71c88888664`
- Primary score: `-0.10736873851248371`

## Gate Status

- Tests gate: **passed** from exact-patch evidence supplied by the Orchestrator and Implementer.
- Fast gate: **passed**. Candidate primary `-0.09029033536393984`; diagnostics `failed=false`, zero issues, `120` records, all numeric metrics finite.
- Iteration promotion gate: **passed**. Candidate `-0.08966691030501653` versus cached incumbent `-0.10655439732760863`; delta `+0.0168874870225921`, exceeding `+0.002` by `+0.0148874870225921`. Diagnostics are clean, every early-mean guardrail passes, and no variable/lead exceeds the `10%` regression limit.
- Validation acceptance gate: **passed as measured**. Candidate `-0.09015390068642175` versus cached incumbent `-0.10736873851248371`; delta `+0.017214837826061966`, exceeding `+0.001` by `+0.016214837826061966`. Diagnostics are clean and every early-mean guardrail passes.
- Golden gate: **not run**, as required for iterative selection.

## RMSE Guardrails

Positive regression percentages mean worse candidate RMSE; negative values mean improvement. The worst-lead column is the maximum relative regression over all 15 daily leads for that protocol and variable.

| Protocol | Variable | Candidate early mean | Incumbent early mean | Early regression | Worst lead | Worst-lead regression |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| iteration | `2m_temperature` | `4.462104892072657` | `4.4621043137314516` | `+0.000012961176%` | `72 h` | `+0.000024248811%` |
| iteration | `mean_sea_level_pressure` | `651.8563388558034` | `651.8563674102227` | `-0.000004380477%` | `72 h` | `+0.000018742199%` |
| iteration | `geopotential_500` | `560.628089529327` | `560.628379572417` | `-0.000051735356%` | `48 h` | `+0.000003239844%` |
| iteration | `10m_u_component_of_wind` | `3.861851763905954` | `3.8618499043591386` | `+0.000048151711%` | `96 h` | `+0.000067672210%` |
| validation | `2m_temperature` | `4.458783792234554` | `4.45878269308482` | `+0.000024651341%` | `120 h` | `+0.000056047679%` |
| validation | `mean_sea_level_pressure` | `639.7770691285048` | `639.7770656996028` | `+0.000000535953%` | `72 h` | `+0.000027876577%` |
| validation | `geopotential_500` | `553.3175811459055` | `553.3175356603272` | `+0.000008220520%` | `96 h` | `+0.000031311241%` |
| validation | `10m_u_component_of_wind` | `3.8264192627965583` | `3.826420627329381` | `-0.000035660816%` | `120 h` | `-0.000009792258%` |

Iteration has zero `>10%` variable/lead violations. Validation also has zero such violations as an additional reported diagnostic.

## Measurement Lessons

- The candidate preserves the incumbent almost exactly through the guarded 1–5 day window, matching its intended late activation. The largest early-mean regression is only `+0.000048151711%` in iteration and `+0.000024651341%` in validation.
- Over leads 6–15 days, mean T2m RMSE improves by `0.3489504894295097` (`4.950179763248361%`) on iteration and `0.3492895696561842` (`4.975655152171936%`) on validation.
- The late window also improves rather than trades off the other targets: iteration mean RMSE changes are `-0.164101%` MSLP, `-0.183929%` Z500, and `-0.042819%` U10; validation changes are `-0.195712%`, `-0.182523%`, and `-0.037746%`, respectively.
- The primary-score gains reproduce closely across splits: `+0.0168874870225921` on iteration and `+0.017214837826061966` on validation.

## Anomalies

- Cache reuse: both incumbent protocols passed every validation check and were reused. No incumbent recomputation was authorized or needed.
- Resource limits: the Orchestrator recorded about `173 GiB` available RAM, four idle NVIDIA L4 GPUs, and about `4135 GiB` free disk. Iteration and validation used four effective GPU workers; fast used the fixed command's default single worker.
- Failed or restarted commands: none. Candidate parallel runs started with zero cached chunks and completed without retry.
- Nonfinite or unstable outputs: none. All candidate primary scores and record metrics are finite; fixed diagnostics reported zero issues.
- Physical plausibility: no obvious fixed-diagnostic failure, instability, severe oversmoothing signal, or guardrail regression was measured. No additional qualitative field-plot protocol was authorized.
- Validation discipline: validation ran exactly once for this frozen implementation state.

## Recommendation To Orchestrator

All measured fixed gates pass with substantial and split-consistent primary-score gains, clean diagnostics, and no RMSE guardrail violation. Recommend proceeding to the Orchestrator's acceptance review. This Scorer report does not accept, reject, modify, revert, or commit the candidate.
