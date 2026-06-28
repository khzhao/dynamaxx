# Scoring Notes

## Gate Status

- Fast gate: passed from reused Orchestrator artifact. Candidate fast primary `-0.3155237660265679`; diagnostics failed `False` with `0` issues. The Scorer did not rerun fast.
- Iteration promotion gate: passed. Candidate primary `-0.31282890543336245` versus cached incumbent `-0.32000443139324114`, delta `+0.0071755259598786925`. Candidate diagnostics failed `False` with `0` issues. Early day 1-5 mean RMSE regressions all passed the 2% guardrail; worst variable+lead RMSE regression was `0.00019278258826451713` for `10m_u_component_of_wind` at `24` hours.
- Validation support gate: passed by default scoring thresholds. Candidate primary `-0.3072374345999185` versus cached incumbent `-0.31443387067049233`, delta `+0.007196436070573853`. Candidate diagnostics failed `False` with `0` issues. Early day 1-5 mean RMSE regressions all passed the 2% guardrail; worst variable+lead RMSE regression was `0.00021800496629489555` for `10m_u_component_of_wind` at `24` hours.
- Scorer decision: no accept/reject decision made; control returns to Orchestrator.

## Commands Run

- Read required role files: `roles/PROTOCOL.md`, `roles/SCORER.md`, and `roles/ORCHESTRATOR.md`; exit 0.
- Verified registration with `uv run python - <<'PY' ... DYCORE_MODEL_FACTORIES ... PY`; exit 0. Both `dino_hsl2_theta` and `dino_hsl_theta` were registered.
- Verified Orchestrator-provided checks, not rerun: `uv run pytest` exit 0 with 223 passed and 2 skipped; focused pytest exit 0 with 157 passed; ruff check on changed files exit 0; `git diff --check` exit 0.
- Reused existing candidate fast artifact from `outputs/eval/fast_dino_hsl2_theta.json` and `.csv`; Orchestrator command `uv run dynamaxx-eval fast --model dino_hsl2_theta` exit 0.
- `uv run dynamaxx-eval iteration --model dino_hsl2_theta --workers 4`; exit 0. This was the only iteration evaluation launched by Scorer.
- `uv run dynamaxx-eval validation --model dino_hsl2_theta --workers 4`; exit 0. This was launched only after iteration passed the +0.002 promotion gate and guardrails.
- No incumbent `dynamaxx-eval` command was launched. Golden was not run.

## Cache Reuse

- Iteration incumbent cache reused from `outputs/eval/iteration_dino_hsl_theta.json` and `outputs/eval/iteration_dino_hsl_theta.csv`.
- Validation incumbent cache reused from `outputs/eval/validation_dino_hsl_theta.json` and `outputs/eval/validation_dino_hsl_theta.csv`.
- Cache checks passed: requested incumbent matched `.logbook/leaderboard.json`; leaderboard fingerprint included the scored protocols; target variables matched; lead range was 1..15 days; current HEAD matched leaderboard `eval_code_commit`; no `src/dynamaxx/eval/`, `pyproject.toml`, or `uv.lock` changes were present; artifacts were readable; primary scores and RMSE values were finite; model-specific rows were present.
- Candidate source edits were not treated as cache invalidation under `roles/SCORER.md`.

## Artifacts

- Candidate fast: `outputs/eval/fast_dino_hsl2_theta.json`, `outputs/eval/fast_dino_hsl2_theta.csv`.
- Candidate iteration: `outputs/eval/iteration_dino_hsl2_theta.json`, `outputs/eval/iteration_dino_hsl2_theta.csv`; run directory `outputs/eval/runs/iteration_dino_hsl2_theta`.
- Candidate validation: `outputs/eval/validation_dino_hsl2_theta.json`, `outputs/eval/validation_dino_hsl2_theta.csv`; run directory `outputs/eval/runs/validation_dino_hsl2_theta`.
- Incumbent iteration cache: `outputs/eval/iteration_dino_hsl_theta.json`, `outputs/eval/iteration_dino_hsl_theta.csv`.
- Incumbent validation cache: `outputs/eval/validation_dino_hsl_theta.json`, `outputs/eval/validation_dino_hsl_theta.csv`.

## Guardrail Details

- Iteration model-specific records: candidate `60`, incumbent `60`. Persistence rows were present in raw artifacts and excluded from guardrail comparisons.
- Iteration early mean RMSE relative regressions: 10m_u_component_of_wind=-0.0032209047507185894, 2m_temperature=-0.002600398352572694, geopotential_500=-0.005131339820513607, mean_sea_level_pressure=-0.006463453040351609.
- Iteration guardrail violations: early mean `0`, per-variable-lead `0`.
- Validation model-specific records: candidate `60`, incumbent `60`. Persistence rows were present in raw artifacts and excluded from guardrail comparisons.
- Validation early mean RMSE relative regressions: 10m_u_component_of_wind=-0.0032420148579568177, 2m_temperature=-0.0027306524801840788, geopotential_500=-0.005166358736096256, mean_sea_level_pressure=-0.006121381835476923.
- Validation guardrail violations: early mean `0`, per-variable-lead `0`.

## Anomalies

- None observed. Candidate iteration and validation completed normally, wrote official artifacts, and reported clean diagnostics.

## Lessons

- Evaluation artifacts include persistence baseline rows in addition to model rows; scorer guardrail logic must filter by `model_name` before comparing candidate and incumbent RMSE.
- Midpoint theta departure improved both iteration and validation primary score by about +0.0072 with no fixed guardrail regressions.
- Incumbent cache reuse worked as intended; candidate source edits alone did not justify rerunning the accepted incumbent baseline.
