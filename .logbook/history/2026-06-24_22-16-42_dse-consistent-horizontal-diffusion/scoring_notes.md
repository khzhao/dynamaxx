# Scoring Notes

## Gate Status

- Fast gate: passed from the Implementer-provided artifact after Scorer verification. `outputs/eval/fast_dino_mass_dse_diff.json` reports `failed=False`, `issues=0`, `records=120`, `model_rows=60`, and primary score `-0.2634112163380138`.
- Iteration promotion gate: did not pass. Candidate primary score was `-0.2616352238490598`; cached incumbent primary score was `-0.2616483974683927`; signed delta was `+1.3173619332895736e-05`, below the required `+0.002` threshold. Candidate diagnostics were clean with zero issues.
- Iteration RMSE guardrails: passed. All early lead days 1-5 mean RMSE regressions were below `+2%`; the worst variable/lead regression was `2m_temperature` at lead day `3` with relative regression `+5.6047926967922696e-05`. Variable+lead RMSE regressions over `+10%`: `0`.
- Validation acceptance gate: not evaluated. The fixed validation command was not run because validation is allowed only after the candidate passes the iteration promotion gate.
- Golden: not run; golden was prohibited by the task handoff.

## Commands And Status

- Read protocol files: `sed -n '1,240p' roles/PROTOCOL.md`, `sed -n '241,520p' roles/PROTOCOL.md`, `sed -n '1,260p' roles/SCORER.md`, and `sed -n '1,220p' roles/ORCHESTRATOR.md`; all exited `0`.
- Confirmed registration with `uv run python - <<'PY' ... create_dycore_model(...) ... PY`: exit `0` for `dino_mass_dse_diff` and `dino_hsl2_mass_dse`. An initial probe using nonexistent `available_models` exited `1` and was superseded without modifying files.
- Accepted Orchestrator pytest record without rerun: `uv run pytest` exited `0` with `244 passed`, `2 skipped` in `240.24s`.
- Verified reusable fast artifact instead of rerunning fast: `uv run dynamaxx-eval fast --model dino_mass_dse_diff` exit `0` from Implementer record, artifact readable and compatible.
- Checked fixed protocol diffs with `git diff --name-only src/dynamaxx/eval roles .logbook/leaderboard.json`: exit `0`, no output.
- Ran candidate iteration: `uv run dynamaxx-eval iteration --model dino_mass_dse_diff --workers 4` exited `0` with `failed=False`, `issues=0`, `records=120`, and primary score `-0.2616352238490598`.
- Computed guardrails with `uv run python - <<'PY' ... compute iteration primary delta and RMSE guardrails ... PY`: exit `0`.
- Did not run `uv run dynamaxx-eval validation --model dino_mass_dse_diff --workers 4` because iteration did not promote.

## Cache Reuse

- Candidate fast was reused from `outputs/eval/fast_dino_mass_dse_diff.json` and `outputs/eval/fast_dino_mass_dse_diff.csv` after verifying model name, finite primary score, clean diagnostics, 120 raw records, 60 candidate rows, target variables, and lead hours 24 through 360.
- Incumbent iteration metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dino_hsl2_mass_dse.json` and `outputs/eval/iteration_dino_hsl2_mass_dse.csv`. Checks passed: requested incumbent matched leaderboard incumbent, current HEAD matched leaderboard eval code commit `2c70bb5b77370a074330c2b46954f74f20771f12`, fixed fingerprint matched, artifacts were readable, primary score was finite, records covered the expected variables/leads, and diagnostics were clean.
- Incumbent validation cache was not used for comparison because candidate validation was not run. The available cached validation artifact `outputs/eval/validation_dino_hsl2_mass_dse.json` was readable with primary score `-0.2600180396322455`, but no validation delta was computed.
- Candidate source edits and side-by-side registry additions did not invalidate the accepted incumbent cache under `roles/SCORER.md`.

## Guardrail Details

- Early day 1-5 mean RMSE relative regressions: `2m_temperature=+5.3138785348541514e-05`, `mean_sea_level_pressure=-1.8786018010399212e-05`, `geopotential_500=-1.2202741400393016e-05`, `10m_u_component_of_wind=-6.190680259667544e-05`.
- Worst variable/lead RMSE regression: `2m_temperature`, lead day `3`, candidate RMSE `5.0053404752405655`, incumbent RMSE `5.005059952005905`, relative regression `+5.6047926967922696e-05`.
- Per-variable+lead RMSE regressions over `+10%`: none.

## Artifacts

- Candidate fast: `outputs/eval/fast_dino_mass_dse_diff.json`, `outputs/eval/fast_dino_mass_dse_diff.csv`.
- Candidate iteration: `outputs/eval/iteration_dino_mass_dse_diff.json`, `outputs/eval/iteration_dino_mass_dse_diff.csv`.
- Candidate validation: not run.
- Incumbent iteration cache: `outputs/eval/iteration_dino_hsl2_mass_dse.json`, `outputs/eval/iteration_dino_hsl2_mass_dse.csv`.
- Incumbent validation cache available but not used: `outputs/eval/validation_dino_hsl2_mass_dse.json`, `outputs/eval/validation_dino_hsl2_mass_dse.csv`.
- Score artifacts written here: `.logbook/history/2026-06-24_22-16-42_dse-consistent-horizontal-diffusion/scores.json` and `.logbook/history/2026-06-24_22-16-42_dse-consistent-horizontal-diffusion/scoring_notes.md`.

## Measurement Lessons

- DSE-consistent horizontal diffusion gave a tiny positive iteration primary-score delta but not a promotion-scale improvement.
- Guardrails and diagnostics were clean, so the limiting result is insufficient primary-score movement rather than instability or a localized RMSE regression.
- The candidate iteration was much slower than the fast sanity signal implied; future DSE-diffusion proposals should consider lower-cost approximations or stronger expected effect size before spending full iteration compute.

## Anomalies

- Cache reuse: no cache invalidation found; incumbent iteration metrics were reused.
- Resource limits: no resource failure observed. The run used 4 workers, observed 4 GPUs at 100% utilization, 172 GiB available RAM, and 4.1 TiB free disk.
- Failed or restarted commands: no scoring command failed after the superseded registration helper probe; iteration completed without restart.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.

## Recommendation To Orchestrator

Report the measured gate status above. The candidate did not promote to validation under the fixed iteration gate; the Scorer does not accept or reject the candidate.
