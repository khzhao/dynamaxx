# Scoring Notes

## Gate Status

- Pytest gate: verified from Orchestrator record, `uv run pytest` exit 0 with 242 passed and 2 skipped. Scorer did not rerun full pytest.
- Fast gate: verified from existing candidate artifact and Orchestrator record. `uv run dynamaxx-eval fast --model dino_mass_dse_hydroinv` previously exited 0 with `failed=False`, `issues=0`, `records=120`, `primary_score=-0.297130911050922`.
- Iteration promotion gate: failed. Candidate iteration primary score was `-0.29185769674400885`; cached incumbent iteration primary score was `-0.2616483974683927`; delta was `-0.030209299275616164`, below the required `+0.002`.
- Iteration diagnostics: clean for candidate and incumbent, with `failed=False` and zero issues.
- Iteration early RMSE guardrail: failed. The largest mean 1-5 day RMSE regression by variable was `mean_sea_level_pressure` at `2.4455573339468595%`, above the `2%` limit.
- Iteration worst variable-lead RMSE guardrail: passed. Worst regression was `mean_sea_level_pressure` at 360 hours with `7.026815500932039%`, below the `10%` limit.
- Validation acceptance gate: not run. Validation was skipped because the iteration promotion gate failed.
- Golden: not run.

## Artifacts

- Candidate diff: `.logbook/history/2026-06-24_01-58-03_hydrostatic-inverted-mass-dse-hsl/candidate.diff`
- Candidate fast JSON: `outputs/eval/fast_dino_mass_dse_hydroinv.json`
- Candidate fast CSV: `outputs/eval/fast_dino_mass_dse_hydroinv.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dino_mass_dse_hydroinv.json`
- Candidate iteration CSV: `outputs/eval/iteration_dino_mass_dse_hydroinv.csv`
- Candidate iteration run directory: `outputs/eval/runs/iteration_dino_mass_dse_hydroinv`
- Cached incumbent iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse.json`
- Cached incumbent iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse.csv`
- Cached incumbent validation JSON: `outputs/eval/validation_dino_hsl2_mass_dse.json`
- Cached incumbent validation CSV: `outputs/eval/validation_dino_hsl2_mass_dse.csv`

## Cache Reuse

- Iteration incumbent metrics were reused from `.logbook/leaderboard.json`; the incumbent was not rerun.
- Validation incumbent metrics were checked and reusable from `.logbook/leaderboard.json`, but candidate validation was skipped after iteration failed.
- Cache checks performed: requested incumbent matched leaderboard incumbent `dino_hsl2_mass_dse`; fingerprint matched the supplied data path, target variables, lead range `1..15`, protocol list, and eval code commit `2c70bb5b77370a074330c2b46954f74f20771f12`; JSON/CSV files were present and readable; incumbent primary scores were finite; diagnostics were clean; required model rows were present.
- Candidate source edits in the dirty worktree were not treated as an incumbent cache invalidation, per `roles/SCORER.md`.

## Guardrails

| Channel | Lead range | Candidate RMSE | Incumbent RMSE | Regression | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| `10m_u_component_of_wind` | 1-5 days mean | 4.409501547905528 | 4.371016832235197 | 0.8804522413758511% | pass |
| `2m_temperature` | 1-5 days mean | 4.786294229247909 | 4.720167397134262 | 1.4009425206782782% | pass |
| `geopotential_500` | 1-5 days mean | 608.8047530017452 | 603.1650920588065 | 0.9350111631441764% | pass |
| `mean_sea_level_pressure` | 1-5 days mean | 801.655543730707 | 782.5186026540035 | 2.4455573339468595% | fail |

Worst variable-lead RMSE regression was `mean_sea_level_pressure` at 360 hours: candidate `1363.6671169131687`, incumbent `1274.1359354948697`, regression `7.026815500932039%`.

Guardrail calculations filtered eval records by `model_name`. Each JSON contains 60 evaluated-model rows and 60 `persistence` rows.

## Anomalies

- The first fast artifact verification command exited nonzero because it expected 60 total records. The eval artifact correctly contains 120 total records: 60 candidate rows plus 60 persistence reference rows. Corrected verification passed before scoring.
- Candidate iteration was a fresh run with `cached=0` chunks. Runtime was long but stable, with no failed chunks, nonfinite outputs, or diagnostic issues.
- No incumbent protocol was rerun, no evaluation command failed, and no source/proposal/leaderboard files were changed by Scorer.

## Measurement Lessons

- The hydrostatic-inverted mass-DSE HSL candidate substantially worsened the fixed iteration primary score relative to the cached incumbent.
- The failure is not only primary-score degradation: early mean sea-level-pressure RMSE also exceeded the fixed 2% guardrail.
- The worst individual variable-lead RMSE regression stayed below 10%, so the most important measured issue is broad early-pressure degradation rather than a single extreme spike.

## Recommendation To Orchestrator

Report the measured gate status as no promotion to validation. This is a measurement report only; Scorer does not accept or reject the candidate.
