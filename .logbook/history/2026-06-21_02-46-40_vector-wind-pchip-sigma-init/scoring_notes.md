# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate score was `-0.5307081511868749` with clean diagnostics.
- Iteration promotion gate: failed. Candidate iteration score was `-0.5150613366089396`; cached incumbent iteration score was `-0.5150627015910243`; delta was `+0.0000013649820846950433`, below the `+0.002` promotion threshold.
- Validation acceptance gate: not run because the iteration promotion gate failed.

## Measurement Lessons

- The vector-wind PCHIP sigma initialization was numerically stable but effectively neutral under the fixed iteration protocol.
- RMSE guardrails were clean; the largest variable-lead RMSE increase was `0.001303832769859698%` at 500 hPa geopotential, 360 h.

## Anomalies

- Cache reuse: incumbent iteration metrics were reused from the valid cached incumbent artifacts. The incumbent was not rerun.
- Resource limits: no resource limit was encountered.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none detected.

## Recommendation To Orchestrator

Reject the candidate for insufficient iteration score improvement. Preserve the evaluation artifacts and history, remove the ready proposal, and revert the candidate implementation before starting the next iteration.
