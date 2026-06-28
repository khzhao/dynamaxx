# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate fast score was `-0.829528377822946`; diagnostics reported `failed=False` and zero issues.
- Iteration promotion gate: failed. Candidate iteration score was `-0.8018895586779444`; cached incumbent iteration score was `-0.532053269893688`; delta was `-0.2698362887842565`, below the required `+0.002`.
- Validation acceptance gate: not run because iteration did not promote.

## Measurement Lessons

- Replacing positive-time offcentered SIL3 with the existing CN-RK3 routine preserved finite forecasts and RMSE guardrails, but substantially harmed the fixed primary score.
- The accepted offcentered SIL3 rollout path appears important for the current score even when raw RMSE differences are near machine-level in the standard guardrail summaries.
- Future solver-swap proposals should retain the accepted offcentered damping mechanism or provide a narrow infrastructure analysis explaining how primary score movement can diverge from the current RMSE guardrails.

## Anomalies

- Cache reuse: incumbent iteration and validation artifacts were reused from `.logbook/leaderboard.json`. The requested incumbent matched the leaderboard incumbent, artifacts were readable, primary scores were finite, records were complete, and the evaluation fingerprint remained compatible. No incumbent command was run.
- Resource limits: none. Resources before scoring were 48 CPUs, about 173 GiB available RAM, four NVIDIA L4 GPUs with about 22566 MiB free each, and about 4.1 TiB free disk. Iteration used `--workers 4`.
- Failed or restarted commands: none. The prior scorer subagent was terminated before scoring restarted in the main process; no eval process was active at restart.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Recommendation To Orchestrator

Reject the candidate. It is cleanly reversible, does not qualify for validation, and should not update the leaderboard.
