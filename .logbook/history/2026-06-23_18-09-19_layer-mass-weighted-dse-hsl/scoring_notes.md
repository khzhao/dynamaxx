# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse` exited 0 with `failed=False`, `issues=0`, `records=120`, and primary score `-0.26345583017469487`.
- Iteration promotion gate: passed. Candidate primary score was `-0.2616483974683927`; cached incumbent primary score was `-0.26737373217433574`; signed delta was `+0.005725334705943053`, above the `+0.002` promotion threshold. Candidate diagnostics were clean. Early lead days 1-5 mean RMSE regressions were all far below 2%, and the worst individual variable/lead RMSE regression was `mean_sea_level_pressure` at lead day 5 with `+1.7141834768660351e-09` relative regression.
- Validation acceptance gate metrics: passed by fixed metric thresholds. Candidate primary score was `-0.2600180396322455`; cached incumbent primary score was `-0.2654819769882763`; signed delta was `+0.00546393735603079`, above the `+0.001` validation threshold. Candidate diagnostics were clean. Early lead days 1-5 mean RMSE regressions were all far below 2%, and the worst individual variable/lead RMSE regression was `mean_sea_level_pressure` at lead day 11 with `+6.492272688853867e-09` relative regression.

## Commands And Status

- Verified Orchestrator full pytest record, not rerun by Scorer: exit 0, `236 passed`, `2 skipped`.
- Confirmed registration with `uv run python - <<'PY' ... create_dycore_model(...) ... PY`: exit 0 for `dino_hsl2_mass_dse` and `dino_hsl2_theta_dse_hsl`.
- Validated incumbent iteration cache with `jq ... outputs/eval/iteration_dino_hsl2_theta_dse_hsl.json`: exit 0.
- Validated incumbent validation cache with `jq ... outputs/eval/validation_dino_hsl2_theta_dse_hsl.json`: exit 0.
- Ran `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse`: exit 0.
- Ran `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse --workers 4`: exit 0.
- Computed iteration guardrails with `uv run python - <<'PY' ... PY`: exit 0.
- Ran `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse --workers 4`: exit 0.
- Computed validation guardrails with `uv run python - <<'PY' ... PY`: exit 0.
- Golden was not run.

## Cache Reuse

- Iteration incumbent metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dino_hsl2_theta_dse_hsl.json` and `outputs/eval/iteration_dino_hsl2_theta_dse_hsl.csv`.
- Validation incumbent metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/validation_dino_hsl2_theta_dse_hsl.json` and `outputs/eval/validation_dino_hsl2_theta_dse_hsl.csv`.
- Cache validation checks: requested incumbent matched the leaderboard incumbent; `HEAD` matched leaderboard `eval_code_commit` `a274541cc57f593b8e5796e1df8307e8820c2d6b`; fixed data path, target variables, lead range, and protocols matched; artifacts were readable; primary scores were finite; records covered the four target variables at lead hours 24 through 360; incumbent diagnostics were clean.
- Candidate source edits did not invalidate the accepted incumbent cache under `roles/SCORER.md`.

## Guardrail Details

- Iteration early mean RMSE relative regressions over days 1-5: `10m_u_component_of_wind=-8.276378788601333e-11`, `2m_temperature=-3.1843015416864013e-10`, `geopotential_500=+1.443795392443651e-10`, `mean_sea_level_pressure=+2.1842902323888387e-10`.
- Iteration worst variable/lead RMSE regression: `mean_sea_level_pressure`, lead day 5, candidate RMSE `937.318746406913`, incumbent RMSE `937.3187448001767`, relative regression `+1.7141834768660351e-09`.
- Validation early mean RMSE relative regressions over days 1-5: `10m_u_component_of_wind=-2.6560500387822825e-09`, `2m_temperature=-2.915143490190406e-10`, `geopotential_500=+7.42160343243184e-10`, `mean_sea_level_pressure=-8.521831286286002e-10`.
- Validation worst variable/lead RMSE regression: `mean_sea_level_pressure`, lead day 11, candidate RMSE `974.4205879350974`, incumbent RMSE `974.4205816088933`, relative regression `+6.492272688853867e-09`.

## Artifacts

- Candidate fast: `outputs/eval/fast_dino_hsl2_mass_dse.json`, `outputs/eval/fast_dino_hsl2_mass_dse.csv`.
- Candidate iteration: `outputs/eval/iteration_dino_hsl2_mass_dse.json`, `outputs/eval/iteration_dino_hsl2_mass_dse.csv`.
- Candidate validation: `outputs/eval/validation_dino_hsl2_mass_dse.json`, `outputs/eval/validation_dino_hsl2_mass_dse.csv`.
- Incumbent iteration cache: `outputs/eval/iteration_dino_hsl2_theta_dse_hsl.json`, `outputs/eval/iteration_dino_hsl2_theta_dse_hsl.csv`.
- Incumbent validation cache: `outputs/eval/validation_dino_hsl2_theta_dse_hsl.json`, `outputs/eval/validation_dino_hsl2_theta_dse_hsl.csv`.
- Score artifacts written here: `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/scores.json` and `.logbook/history/2026-06-23_18-09-19_layer-mass-weighted-dse-hsl/scoring_notes.md`.

## Measurement Lessons

- The candidate improves both iteration and validation primary scores while keeping RMSE differences from the incumbent at numerical-noise scale for the fixed guardrails.
- The evaluation runtime was long but made steady chunk progress and produced complete artifacts without restarts.

## Anomalies

- Cache reuse: no anomaly; incumbent artifacts were valid and reused.
- Resource limits: no resource failure observed.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Recommendation To Orchestrator

The candidate meets the fixed scoring thresholds against the cached incumbent metrics, and validation ran exactly once after iteration promotion. This is a measurement recommendation only; the Scorer does not accept or reject the candidate.
