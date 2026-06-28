# Scoring Notes

## Gate Status

- Pytest gate: verified from Orchestrator record, `uv run pytest` exit 0 with 243 passed and 2 skipped. Scorer did not rerun full pytest.
- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_mass_dse_fluxcorr` exited 0 with `failed=False`, `issues=0`, `records=120`, `primary_score=-0.2680857020215102`.
- Iteration promotion gate: failed. Candidate iteration primary score was `-0.2678206586319622`; cached incumbent iteration primary score was `-0.2616483974683927`; delta was `-0.006172261163569502`, below the required `+0.002`.
- Iteration diagnostics: clean for candidate and incumbent, with `failed=False` and zero issues.
- Iteration early RMSE guardrail: passed. Largest mean 1-5 day RMSE regression by variable was `mean_sea_level_pressure` at `0.4935870834249615%`, below the `2%` limit.
- Iteration worst variable-lead RMSE guardrail: passed. Worst regression was `mean_sea_level_pressure` at 360 hours with `1.4280541410196068%`, below the `10%` limit.
- Validation acceptance gate: not run. Validation was skipped because the iteration promotion gate failed.
- Golden: not run.

## Artifacts

- Candidate fast JSON: `outputs/eval/fast_dino_mass_dse_fluxcorr.json`
- Candidate fast CSV: `outputs/eval/fast_dino_mass_dse_fluxcorr.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dino_mass_dse_fluxcorr.json`
- Candidate iteration CSV: `outputs/eval/iteration_dino_mass_dse_fluxcorr.csv`
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

| Channel | Lead range | Candidate RMSE | Incumbent RMSE | Regression |
| --- | ---: | ---: | ---: | ---: |
| `10m_u_component_of_wind` | 1-5 days mean | 4.378427026529581 | 4.371016832235197 | 0.1695302163957592% |
| `2m_temperature` | 1-5 days mean | 4.7323452680470375 | 4.720167397134263 | 0.25799658970077477% |
| `geopotential_500` | 1-5 days mean | 601.772532602276 | 603.1650920588065 | -0.23087533991353149% |
| `mean_sea_level_pressure` | 1-5 days mean | 786.3810134021012 | 782.5186026540035 | 0.4935870834249615% |

Worst variable-lead RMSE regression was `mean_sea_level_pressure` at 360 hours: candidate `1292.3312864839231`, incumbent `1274.1359354948697`, regression `1.4280541410196068%`.

Guardrail calculations filtered eval records by `model_name`. Each JSON contains 60 evaluated-model rows and 60 `persistence` rows.

## Anomalies

- Two exploratory scorer inspection commands exited nonzero before corrected checks: one used a non-exported registry symbol, and one treated target variable descriptors as plain strings. Corrected checks passed before evaluation and before artifact writing.
- The first guardrail inspection pass accidentally compared unfiltered records that included persistence rows. Final `scores.json` and the table above use corrected model-row filtering.
- No evaluation command failed, no nonfinite outputs were reported, and no diagnostic issues were emitted.

## Measurement Lessons

- The candidate did not improve the fixed iteration primary score despite clean diagnostics and guardrails. The measured delta of `-0.006172261163569502` is far below the promotion threshold.
- The pressure-thickness corrected mass-DSE HSL mechanism does not appear promising in this implementation state for the fixed iteration metric. Future scoring utilities should explicitly filter eval records by `model_name` before guardrail comparison because persistence baselines are included in the same JSON.

## Recommendation To Orchestrator

Report the measured gate status as no promotion to validation. This is a measurement report only; Scorer does not accept or reject the candidate.
