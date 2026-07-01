# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth` exited 0 with `failed=False`, `issues=0`, and primary score `-0.1369589966316166`.
- Iteration promotion gate: passed. Candidate iteration score was `-0.13590520069778708` versus cached incumbent `-0.16500618979404214`, so the primary delta was `0.029100989096255053` and exceeded the `+0.002` threshold. Diagnostics were clean. The largest day-1-to-5 mean RMSE regression was `-1.1698100179414292%`, and the worst single variable/lead RMSE regression was `2m_temperature` at `360h` with `1.1898982135831615%` against the `10%` limit.
- Validation acceptance gate for reporting: passed. Candidate validation score was `-0.13767474868567484` versus cached incumbent `-0.16591150807771451`, so the primary delta was `0.02823675939203968` and exceeded the `+0.001` threshold. Diagnostics were clean. The largest day-1-to-5 mean RMSE regression was `-1.2853329000007707%`, and the worst single variable/lead RMSE regression was `2m_temperature` at `288h` with `0.9255849240232976%`.

## Primary Scores

- Candidate fast: `-0.1369589966316166`.
- Candidate iteration: `-0.13590520069778708`.
- Cached incumbent iteration: `-0.16500618979404214`.
- Iteration delta: `0.029100989096255053`.
- Candidate validation: `-0.13767474868567484`.
- Cached incumbent validation: `-0.16591150807771451`.
- Validation delta: `0.02823675939203968`.

## Guardrails

- Iteration day-1-to-5 mean RMSE regression by variable: `[('10m_u_component_of_wind', -4.592744211718053), ('2m_temperature', -1.1698100179414292), ('geopotential_500', -2.846920422611859), ('mean_sea_level_pressure', -6.396316228863914)]`.
- Iteration worst single RMSE regression: `{'channel_name': '2m_temperature', 'lead_hours': 360, 'candidate_rmse': 7.834159265551044, 'incumbent_rmse': 7.742036906703233, 'rmse_regression_percent': 1.1898982135831615}`.
- Validation day-1-to-5 mean RMSE regression by variable: `[('10m_u_component_of_wind', -4.574314845089853), ('2m_temperature', -1.2853329000007707), ('geopotential_500', -2.685855345260633), ('mean_sea_level_pressure', -6.139401179229821)]`.
- Validation worst single RMSE regression: `{'channel_name': '2m_temperature', 'lead_hours': 288, 'candidate_rmse': 7.599843630457525, 'incumbent_rmse': 7.530145736761082, 'rmse_regression_percent': 0.9255849240232976}`.

## Cache Reuse

- Iteration incumbent metrics were reused from `outputs/eval/iteration_dino_ri2m_ekman_coupled.json` and `outputs/eval/iteration_dino_ri2m_ekman_coupled.csv`.
- Validation incumbent metrics were reused from `outputs/eval/validation_dino_ri2m_ekman_coupled.json` and `outputs/eval/validation_dino_ri2m_ekman_coupled.csv`.
- Cache checks: requested incumbent matched `.logbook/leaderboard.json`; data path, target variables, lead range, and protocol list matched; no fixed evaluation, metric, CLI, pyproject, or protocol code changes were present relative to leaderboard `eval_code_commit` `d187308d30a242bf38aabe5b7eb530fca522a68f`; cached JSON artifacts were readable, finite, diagnostics-clean, and contained 60 incumbent model rows for guardrails.
- Candidate source edits were not treated as cache invalidation. The incumbent was not rerun.

## Commands

- `uv run python - <<'PY' ... registration check ... PY`: exit 0 after retrying with the actual registry API.
- `uv run python - <<'PY' ... incumbent cache validation ... PY`: exit 0.
- `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth`: exit 0.
- `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth --workers 4`: exit 0.
- `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth --workers 4`: exit 0.
- `uv run python - <<'PY' ... final model-row comparison and artifact write ... PY`: exit 0.

## Anomalies

- A first registration helper attempted to import `get_model` from `dynamaxx.dycore.registry` and exited 1 because that helper does not exist. The actual registry API check succeeded and this was not a candidate failure.
- Evaluation JSON contains persistence reference rows in addition to model rows. A preliminary scratch comparison using duplicate channel/lead keys under-reported RMSE movement by overwriting model rows with persistence rows. The final `scores.json` and this note use only rows whose `model_name` matches the candidate or incumbent.
- No scoring command failed or was restarted. No nonfinite primary scores, diagnostic issues, or resource failures were observed.

## Measurement Lessons

- The candidate improved primary score substantially in both iteration and validation while keeping diagnostics clean.
- Early-lead RMSE improved for every target variable in both protocols; mean sea level pressure had the largest day-1-to-5 mean improvement.
- The only positive worst single-lead regressions were small later-lead `2m_temperature` regressions, below fixed guardrail limits.

## Recommendation To Orchestrator

Report the measured gate status and caveats. The Scorer does not accept or reject the candidate.
