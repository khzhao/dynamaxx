# Scoring Notes

## Gate Status

- Fast gate: not run; infrastructure-only proposal was deferred before implementation.
- Iteration promotion gate: not run.
- Validation acceptance gate: not run.

## Measurement Lessons

- Infrastructure proposals that cannot improve the dycore score should not be
  implemented on the score-bearing branch unless the user explicitly approves a
  non-score commit policy.
- Cached incumbent metrics remained valid and did not require any incumbent
  rerun.

## Anomalies

- Cache reuse: incumbent cache was available and valid, but no candidate scoring
  was applicable.
- Resource limits: none.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none observed.

## Recommendation To Orchestrator

Keep the sidecar in research staging until a separate infrastructure policy
allows non-score source changes without breaking the latest-commit incumbent
invariant. Continue with a model-selection proposal.
