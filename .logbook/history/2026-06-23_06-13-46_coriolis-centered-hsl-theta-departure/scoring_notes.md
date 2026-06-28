# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_hsl_corcen` exited 0 with `failed=False`, `issues=0`, and primary score `-0.3155322000430237`.
- Iteration promotion gate: failed. Candidate iteration score was `-0.3128234541629607` versus cached incumbent `-0.31282890543336245`, so the primary delta was `5.4512704017462e-06` and failed the `+0.002` threshold. Diagnostics were clean. Guardrails passed: the largest day-1-to-5 mean RMSE regression was `0.001225365959976717%` against the `2%` limit, and the worst single variable/lead RMSE regression was `mean_sea_level_pressure` at `24h` with `0.006187473340578273%` against the `10%` limit.
- Validation acceptance gate: not evaluated. Validation permission was contingent on iteration promotion, and the candidate did not promote. Golden was not run.

## Measurement Lessons

- The centered-Coriolis HSL theta-departure candidate was effectively neutral against the incumbent on iteration primary score. It improved neither enough to justify validation nor badly enough to indicate an instability.
- RMSE guardrails remained comfortably within limits, so future variants should target measurable primary-score movement rather than guardrail repair for this mechanism.

## Anomalies

- Cache reuse: reused `.logbook/leaderboard.json` incumbent artifacts for iteration and checked validation cache for reporting. The requested incumbent matched `dino_hsl2_theta`; `HEAD` matched the leaderboard `eval_code_commit` `72efada4e0afbd8e34e3184dbcef90cb91cc051c`; the fingerprint matched the requested data path, target variables, lead range, and protocols; artifacts were present, readable, finite, and contained required model rows. Candidate source edits in the current worktree were not treated as cache invalidation.
- Resource limits: no resource failures were observed. Iteration ran with `--workers 4`; evaluator reported GPU dispatch with `gpu_count=4`, `effective_workers=4`.
- Failed or restarted commands: no scoring command failed or was restarted.
- Nonfinite or unstable outputs: no nonfinite primary scores or diagnostic issues were observed in fast or iteration.

## Recommendation To Orchestrator

Report measured status as iteration-not-promoted. Do not run validation for this candidate under the stated gate because the primary-score delta failed the promotion threshold, despite clean diagnostics and passing RMSE guardrails.
