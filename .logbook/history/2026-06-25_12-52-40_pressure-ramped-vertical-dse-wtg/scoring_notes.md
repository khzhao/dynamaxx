# Scoring Notes

## Inputs

- Candidate: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Incumbent: `dino_hsl2_mass_dse_wtg`
- History directory: `.logbook/history/2026-06-25_12-52-40_pressure-ramped-vertical-dse-wtg`
- Worker count: 4
- Validation permission: validation allowed only after iteration promotion; iteration promoted, so validation was run.
- Golden: not run.

## Registry And Tests

Both candidate and incumbent constructed successfully through
`dynamaxx.dycore.registry.create_dycore_model`.

The Scorer did not rerun pytest because the Orchestrator supplied passing
pre-scoring records:

- `uv run pytest`: exit 0, `252 passed, 2 skipped in 275.58s`
- Targeted tests: exit 0, `10 passed, 176 deselected in 45.04s`

## Cache Reuse

The incumbent leaderboard cache was reused for both iteration and validation.
No incumbent rerun was performed.

Validation checks performed:

- Requested incumbent matched `.logbook/leaderboard.json.incumbent_model_name`.
- Leaderboard fingerprint included the scored protocols and matched the fixed
  data path, target variables, and lead range.
- Current HEAD was `d8561caebb78ca096263d8c412217570ff2d1f46`, matching
  `.logbook/leaderboard.json.evaluation_fingerprint.eval_code_commit`.
- Dirty files were candidate source/test/registry changes only; no fixed eval
  protocol or metric files were dirty.
- Cached incumbent artifacts existed, were readable, contained finite primary
  scores, had clean diagnostics, and had complete 4-variable x 15-lead records
  for guardrail comparisons.

Reused artifacts:

- Iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg.json`
- Iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg.csv`
- Validation JSON: `outputs/eval/validation_dino_hsl2_mass_dse_wtg.json`
- Validation CSV: `outputs/eval/validation_dino_hsl2_mass_dse_wtg.csv`

## Commands

Fixed evaluation commands:

- `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp`: exit 0
- `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp --workers 4`: exit 0
- `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp --workers 4`: exit 0

Other scorer verification commands exited 0, including protocol reads,
leaderboard inspection, registry construction, artifact validation, metric
comparison scripts, and non-invasive resource/progress checks.

## Fast

- Candidate primary score: `-0.22381094923130626`
- Diagnostics failed: `false`
- Diagnostic issue count: `0`
- Records: `120`
- Raw JSON: `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Raw CSV: `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`

## Iteration Gate

- Candidate primary score: `-0.2197104515448394`
- Cached incumbent primary score: `-0.25851235493825614`
- Primary delta: `+0.03880190339341674`
- Required delta: `+0.002`
- Candidate diagnostics failed: `false`
- Candidate diagnostic issue count: `0`

Early day 1-5 mean RMSE guardrail:

| Channel | Candidate | Incumbent | Relative regression |
| --- | ---: | ---: | ---: |
| `10m_u_component_of_wind` | 4.778312125062429 | 4.778312124424064 | 1.3359646722221896e-10 |
| `2m_temperature` | 2.7938222602375182 | 2.793822260063141 | 6.241540617679675e-11 |
| `geopotential_500` | 878.0844086667236 | 878.0844089154298 | -2.832372114625059e-10 |
| `mean_sea_level_pressure` | 817.7806714218246 | 817.7806709036296 | 6.336602353940179e-10 |

Worst variable+lead RMSE regression:

- Channel: `10m_u_component_of_wind`
- Lead hours: `192`
- Candidate RMSE: `5.339945540098171`
- Incumbent RMSE: `5.339945519167832`
- Relative regression: `3.9195791057267115e-09`

Iteration passed the primary threshold, diagnostics, early-day guardrail, and
worst variable+lead guardrail. Validation was therefore run.

## Validation Gate

- Candidate primary score: `-0.21940899263836755`
- Cached incumbent primary score: `-0.25704033104116597`
- Primary delta: `+0.03763133840279842`
- Required delta: `+0.001`
- Candidate diagnostics failed: `false`
- Candidate diagnostic issue count: `0`

Early day 1-5 mean RMSE guardrail:

| Channel | Candidate | Incumbent | Relative regression |
| --- | ---: | ---: | ---: |
| `10m_u_component_of_wind` | 4.763087388397052 | 4.7630873740229385 | 3.0178144427850384e-09 |
| `2m_temperature` | 2.7573063496716426 | 2.757306350905645 | -4.4753900585448037e-10 |
| `geopotential_500` | 872.2202557124486 | 872.2202546614259 | 1.2049969910776781e-09 |
| `mean_sea_level_pressure` | 809.1449325411452 | 809.1449307049517 | 2.269301191404338e-09 |

Worst variable+lead RMSE regression:

- Channel: `geopotential_500`
- Lead hours: `48`
- Candidate RMSE: `819.6245481926466`
- Incumbent RMSE: `819.624540671662`
- Relative regression: `9.176133852761836e-09`

Validation passed the primary threshold, diagnostics, early-day guardrail, and
worst variable+lead guardrail.

## Raw Artifacts

- Candidate iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Candidate iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Candidate validation JSON: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Candidate validation CSV: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Candidate iteration chunks: `outputs/eval/runs/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp`
- Candidate validation chunks: `outputs/eval/runs/validation_dino_hsl2_mass_dse_wtg_vdse_ramp`

## Anomalies And Lessons

- No scoring anomalies, nonfinite metrics, diagnostic failures, or resource
  failures were observed.
- The candidate's aggregate primary improvement is large, while fixed RMSE
  guardrail changes are near numerical noise against the incumbent. Future
  proposals should inspect which skill records improve without moving RMSE
  guardrails materially.
- The incumbent cache policy worked as intended: candidate source edits did not
  force an incumbent rerun because the leaderboard artifacts remained
  compatible and complete.
