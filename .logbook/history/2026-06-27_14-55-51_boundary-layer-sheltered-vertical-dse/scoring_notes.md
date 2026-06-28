# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate `fast` completed with `failed=False`, `issues=0`, and primary score `-0.22864775066430187`.
- Iteration promotion gate: failed. Candidate iteration score was `-0.2252107539770965` versus cached incumbent `-0.2197104515448394`, for delta `-0.005500302432257104`, below the required `+0.002`.
- Validation acceptance gate: not run. Validation is not allowed when iteration does not promote.

## Guardrails

- Early day 1-5 mean RMSE guardrail: failed. The largest mean relative regression was `+0.6689371902001219` for `2m_temperature`, above the `+0.02` threshold.
- Worst variable-lead RMSE guardrail: failed. The largest relative regression was `+1.1236482423343757` for `2m_temperature` at `288h`, above the `+0.10` threshold.
- Diagnostics: clean. Candidate fast and iteration both reported `failed=False` and `issues=0`.

## Measurement Lessons

- Boundary-layer sheltering of the accepted vertical-DSE increment gives back too much of the incumbent's near-surface thermal behavior and severely damages `2m_temperature`.
- The candidate improved early `geopotential_500` and `10m_u_component_of_wind` relative RMSE, but the primary score and severe T2m guardrail failure dominate the decision.
- Future vertical-DSE follow-ups should avoid strong lower-layer damping of the accepted increment unless paired with an explicitly separate surface-temperature mechanism proposal.

## Anomalies

- Cache reuse: incumbent iteration metrics were reused from `.logbook/leaderboard.json` artifacts. No incumbent evaluation was run.
- Resource limits: none. Candidate iteration used `--workers 4`.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by fixed diagnostics.

## Recommendation To Orchestrator

Reject the candidate. It passed tests, lint, fast, and iteration diagnostics, but failed the primary iteration threshold and both fixed RMSE guardrails. Keep the raw evaluation outputs and history record, revert candidate implementation changes, do not update the leaderboard, and continue the optimization loop with a new proposal.
