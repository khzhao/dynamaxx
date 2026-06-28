# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_hsl2_theta_pw` exited 0 with `failed=False`, `issues=0`, and primary score `-0.22613547323004646`.
- Iteration promotion gate: failed. Candidate iteration score was `-0.22517062459723133` versus cached incumbent `-0.31282890543336245`, so the primary delta was `+0.08765828083613111` and passed the `+0.002` threshold. Diagnostics were clean, but guardrails failed: `geopotential_500` day-1-to-5 mean RMSE regressed by `+2.409417583035754%` against the `2%` limit, and the worst single variable/lead regression was `mean_sea_level_pressure` at 24h with `+26.501130746134606%` against the `10%` limit.
- Validation acceptance gate: not evaluated. Validation permission was contingent on iteration promotion, and the candidate did not promote. Golden was not run.

## Measurement Lessons

- The pressure-work candidate substantially improved the aggregate iteration primary score, but it introduced unacceptable short-lead pressure and geopotential RMSE regressions. Future variants should constrain the pressure-work conversion or add a short-lead balance limiter before spending validation compute.
- Metric JSON/CSV records include persistence reference rows. Scoring comparisons must filter records by the candidate and incumbent `model_name` values before calculating guardrails.

## Anomalies

- Cache reuse: reused `.logbook/leaderboard.json` incumbent artifacts for iteration and validation. The requested incumbent matched `dino_hsl2_theta`; `HEAD` matched the leaderboard `eval_code_commit` `72efada4e0afbd8e34e3184dbcef90cb91cc051c`; the fingerprint matched the requested data path, target variables, lead range, and protocols; artifacts were present, readable, finite, and contained required model rows. Candidate source edits in the current worktree were not treated as cache invalidation.
- Resource limits: no resource failures were observed. Iteration ran with `--workers 4`; evaluator reported GPU dispatch with `gpu_count=4`, `effective_workers=4`.
- Failed or restarted commands: the first registry probe failed because it attempted to import a non-existent `list_dycore_models` helper. The corrected `create_dycore_model` probe succeeded. No evaluation command was restarted.
- Nonfinite or unstable outputs: no nonfinite primary scores or diagnostic issues were observed in fast or iteration. The candidate failed guardrails due to finite RMSE regressions, not numerical diagnostic failure.

## Recommendation To Orchestrator

Report measured status as iteration-not-promoted. Do not run validation for this candidate under the stated gate because the short-lead guardrails failed despite the positive primary-score delta.
