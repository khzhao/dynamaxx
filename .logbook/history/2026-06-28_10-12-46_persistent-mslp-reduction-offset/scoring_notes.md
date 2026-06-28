# Scoring Notes

## Gate Status

- Fast gate: passed with clean diagnostics and primary score `-0.21716794171320913`.
- Iteration promotion gate: failed. Candidate iteration primary score was `-0.21299743637019536`; cached incumbent iteration primary score was `-0.21299732605547173`; delta was `-1.1031472363365324e-7`, far below the required `+0.002`.
- Validation acceptance gate: not run because iteration did not promote.

## Measurement Lessons

- The persistent MSLP reduction factor was effectively neutral on the fixed iteration split.
- Mean MSLP skill moved by only `-6.565693981830378e-08`; all other channel movements were also numerical-noise scale.
- The result suggests the fixed WeatherBench2 initial data and current adapter path do not contain a useful persistent MSLP/surface-pressure ratio signal for this incumbent, or that the correction is too small to matter.

## Anomalies

- Cache reuse: incumbent iteration and validation metrics were reused from `.logbook/leaderboard.json`; no incumbent rerun was performed.
- Resource limits: none observed; `--workers 4` completed.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none.

## Recommendation To Orchestrator

Reject `persistent-mslp-reduction-offset`. It is stable and guardrail-clean, but it failed the iteration promotion gate by producing a near-zero, slightly negative primary-score delta.
