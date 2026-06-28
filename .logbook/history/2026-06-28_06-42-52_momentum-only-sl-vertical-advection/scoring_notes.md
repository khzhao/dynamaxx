# Scoring Notes

## Gate Status

- Fast gate: passed with clean diagnostics and primary score `-0.5760627913044538`.
- Iteration promotion gate: failed. The candidate fixed iteration score was the failure sentinel `-1.7976931348623157e+308`, below the cached incumbent score `-0.21299732605547173`.
- Validation acceptance gate: not run because the candidate did not promote from iteration.

## Measurement Lessons

- The focused tests and fast split were not sufficient to expose the full-rollout instability from the momentum-only vertical remap.
- The candidate failure was not a marginal score regression; it produced non-finite forecast values on the fixed iteration split.
- Keep future vertical-advection proposals more conservative, or require stronger boundedness tests that exercise long lead times and full-grid states before spending a full iteration run.

## Anomalies

- Cache reuse: incumbent iteration and validation scores were reused from `.logbook/leaderboard.json` and the existing `outputs/eval` artifacts. No incumbent rerun was performed.
- Resource limits: none observed; the iteration scorer completed across four workers.
- Failed or restarted commands: none. The iteration command exited `0` but produced failed diagnostics, which is an evaluation failure for the candidate.
- Nonfinite or unstable outputs: 152 `Forecast contains NaN or Inf values.` issues and 1 `Metric records contain NaN or Inf values.` issue.

## Recommendation To Orchestrator

Reject `momentum-only-sl-vertical-advection`. The candidate failed the fixed iteration gate with non-finite forecasts and cannot promote to validation.
