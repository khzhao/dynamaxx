# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate score was `-0.5347320929667674` with clean diagnostics.
- Iteration promotion gate: failed. Candidate iteration score was `-0.5191155612061304`; cached incumbent iteration score was `-0.5150627015910243`; delta was `-0.0040528596151061524`, below the required `+0.002`.
- Validation acceptance gate: not run because the iteration promotion gate failed.

## Measurement Lessons

- Fixed-pressure Held-Suarez equilibrium was numerically stable but degraded the fixed iteration primary score.
- Guardrails remained clean: the largest day 1-5 mean RMSE increase was `0.12843851494942854%` for mean sea level pressure, and the largest variable-lead RMSE increase was `0.7481300673656195%` for 2 m temperature at 360 h.
- Removing local surface-pressure dependence from the weak-HS equilibrium appears to remove a compensating behavior that helps the accepted analysis-offset model.

## Anomalies

- Cache reuse: incumbent iteration metrics were reused from the valid leaderboard artifacts. The incumbent was not rerun.
- Resource limits: no resource limit was encountered. Iteration ran with `--workers 4`.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none detected.

## Recommendation To Orchestrator

Reject the candidate for a negative iteration delta. Preserve the raw candidate metrics and history, remove the ready proposal, and revert the candidate source/test changes before starting the next iteration.
