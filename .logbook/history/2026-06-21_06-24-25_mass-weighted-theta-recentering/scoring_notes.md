# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate score was `-0.5313481378897001` with clean diagnostics.
- Iteration promotion gate: failed. Candidate iteration score was `-0.5155611533781376`; cached incumbent iteration score was `-0.5150627015910243`; delta was `-0.0004984517871132743`, below the required `+0.002`.
- Validation acceptance gate: not run because the iteration promotion gate failed.

## Measurement Lessons

- The mass-weighted theta recentering candidate was numerically stable but slightly worse than the incumbent under the fixed iteration primary score.
- Guardrails remained clean: the largest day 1-5 mean RMSE increase was `0.023261464893778377%` for 10 m zonal wind, and the largest variable-lead RMSE increase was `0.14231331515548704%` for 10 m zonal wind at 336 h.
- Changing the accepted theta recentering from an area-weighted moment to a mass-weighted moment did not improve the fixed benchmark, suggesting the accepted geometric layer-mean correction is better aligned with the current sigma-grid and residual-memory stack.

## Anomalies

- Cache reuse: incumbent iteration metrics were reused from the valid leaderboard artifacts. The incumbent was not rerun.
- Resource limits: no resource limit was encountered. Iteration ran with `--workers 4` on four L4 GPUs.
- Failed or restarted commands: none during scoring. The Scorer subagent stalled before starting evaluation, so scoring was simulated in the main agent.
- Nonfinite or unstable outputs: none detected.

## Recommendation To Orchestrator

Reject the candidate for a negative iteration delta. Preserve the raw candidate metrics and history, remove the ready proposal, and revert the candidate source/test changes before starting the next iteration.
