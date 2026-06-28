# Scoring Notes

## Scope

- Role: Scorer
- Proposal slug: `tropical-wtg-mass-dse-relaxation`
- Candidate model: `dino_hsl2_mass_dse_wtg`
- Incumbent model: `dino_hsl2_mass_dse`
- History directory: `.logbook/history/2026-06-25_01-45-51_tropical-wtg-mass-dse-relaxation`
- Worker count: 4
- Golden protocol: not run

## Protocol Inputs

Read and followed `roles/PROTOCOL.md`, `roles/SCORER.md`, and the repo-requested `roles/ORCHESTRATOR.md`. The history directory already existed. The candidate and incumbent models were confirmed registered and constructible with `create_dycore_model`.

The Orchestrator-provided completed gates were reused where allowed: full repo `uv run pytest` was recorded as `243 passed, 2 skipped in 246.47s`, and the Implementer fast artifact was verified instead of rerunning fast.

## Commands

| Command | Exit status | Notes |
| --- | ---: | --- |
| `python` registry probe using `list_models` | 1 | Scorer probe error: helper is not exported; not a candidate failure. |
| `python` registry probe using `AVAILABLE_MODELS` | 1 | Scorer probe error: helper is not exported; not a candidate failure. |
| `python` registry probe using `create_dycore_model` and `dycore_model_names` | 0 | Confirmed both models are registered. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg` | 0 | Run by Implementer; Scorer verified artifact readability and model match. |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg --workers 4` | 0 | Candidate iteration completed cleanly. |
| `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg --workers 4` | 0 | Run only after iteration gates passed; completed cleanly. |

## Fast Gate

- Candidate artifact: `outputs/eval/fast_dino_hsl2_mass_dse_wtg.json` and `outputs/eval/fast_dino_hsl2_mass_dse_wtg.csv`
- Candidate primary score: `-0.259781051518416`
- Diagnostics: `failed=False`, `issues=0`, `records=120`
- Gate status: passed

## Incumbent Cache Reuse

Reused leaderboard incumbent metrics for both iteration and validation. No incumbent rerun was performed.

Validation checks:

- Requested incumbent equals `.logbook/leaderboard.json.incumbent_model_name`: yes
- Leaderboard commit and eval code commit: `2c70bb5b77370a074330c2b46954f74f20771f12`
- Current `HEAD`: `2c70bb5b77370a074330c2b46954f74f20771f12`
- Dirty paths were candidate dycore/registry/tests plus untracked `gifs/`; no evaluation code or fixed protocol path was modified.
- Fingerprint includes data path `/home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative`, protocols `iteration` and `validation`, target variables `2m_temperature`, `mean_sea_level_pressure`, `geopotential_500`, `10m_u_component_of_wind`, and lead days `1..15`.
- Reused iteration artifact: `outputs/eval/iteration_dino_hsl2_mass_dse.json` / `outputs/eval/iteration_dino_hsl2_mass_dse.csv`
- Reused validation artifact: `outputs/eval/validation_dino_hsl2_mass_dse.json` / `outputs/eval/validation_dino_hsl2_mass_dse.csv`

## Iteration Results

- Candidate artifact: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg.json` / `outputs/eval/iteration_dino_hsl2_mass_dse_wtg.csv`
- Incumbent artifact: `outputs/eval/iteration_dino_hsl2_mass_dse.json` / `outputs/eval/iteration_dino_hsl2_mass_dse.csv`
- Candidate primary score: `-0.258512354938256`
- Incumbent primary score: `-0.261648397468393`
- Primary delta: `0.003136042530137`
- Diagnostics: `failed=False`, `issues=0`, `records=120`
- Promotion gate status: passed

Early-lead mean RMSE changes over leads 1-5 days:

| Variable | Candidate mean RMSE | Incumbent mean RMSE | Relative change |
| --- | ---: | ---: | ---: |
| `10m_u_component_of_wind` | 4.35102085978 | 4.37101683224 | -0.457467% |
| `2m_temperature` | 4.71925706834 | 4.72016739713 | -0.019286% |
| `geopotential_500` | 603.077786911 | 603.165092059 | -0.014475% |
| `mean_sea_level_pressure` | 780.7695161 | 782.518602654 | -0.223520% |

Worst single-lead RMSE regression: `geopotential_500` at 24 h, relative change `0.023163%`.

## Validation Results

- Candidate artifact: `outputs/eval/validation_dino_hsl2_mass_dse_wtg.json` / `outputs/eval/validation_dino_hsl2_mass_dse_wtg.csv`
- Incumbent artifact: `outputs/eval/validation_dino_hsl2_mass_dse.json` / `outputs/eval/validation_dino_hsl2_mass_dse.csv`
- Candidate primary score: `-0.257040331041166`
- Incumbent primary score: `-0.260018039632246`
- Primary delta: `0.002977708591080`
- Diagnostics: `failed=False`, `issues=0`, `records=120`
- Validation gate status by default thresholds: passed

Early-lead mean RMSE changes over leads 1-5 days:

| Variable | Candidate mean RMSE | Incumbent mean RMSE | Relative change |
| --- | ---: | ---: | ---: |
| `10m_u_component_of_wind` | 4.30970419452 | 4.32928039562 | -0.452181% |
| `2m_temperature` | 4.72753534967 | 4.72818922264 | -0.013829% |
| `geopotential_500` | 593.696248634 | 593.741014231 | -0.007540% |
| `mean_sea_level_pressure` | 761.431064484 | 763.07142679 | -0.214968% |

Worst single-lead RMSE regression: `geopotential_500` at 24 h, relative change `0.020035%`.

## Diagnostics And Anomalies

- Candidate fast, iteration, and validation all reported `failed=False` and `issues=0`.
- The two nonzero Python registration probes were scorer-side helper-name mistakes and were immediately corrected with the actual registry API; they did not run or modify dycore code.
- Iteration and validation stdout was sparse between chunk completions but showed steady progress and exited zero.
- No golden protocol was run.
- The Scorer did not modify dycore source, proposals, registry, tests, leaderboard, or commits.

## Measurement Lessons

- The candidate improves primary score by `0.003136` on iteration and `0.002978` on validation while keeping diagnostics clean.
- Early-lead mean RMSE changes are all neutral or favorable, with the clearest relative improvements in `10m_u_component_of_wind` and `mean_sea_level_pressure`.
- The largest single-lead RMSE regressions are tiny Z500 day-1 changes, far below the 10% guardrail, so future related proposals should focus on whether the WTG relaxation can produce larger thermodynamic gains without disturbing the nearly neutral Z500 behavior.
