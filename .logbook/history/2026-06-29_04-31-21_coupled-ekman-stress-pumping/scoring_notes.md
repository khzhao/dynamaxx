# Scoring Notes

## Gate Status

- Fast gate: passed for `dino_ri2m_ekman_coupled` with clean diagnostics and primary score `-0.16771830165614882`.
- Iteration promotion gate: passed. Candidate primary score `-0.16500618979404214` beat cached incumbent score `-0.21299732605547173` by `+0.04799113626142959`, exceeding the `+0.002` promotion threshold.
- Validation acceptance gate: passed. Candidate primary score `-0.16591150807771451` beat cached incumbent score `-0.21274255459898536` by `+0.04683104652127085`, exceeding the `+0.001` acceptance threshold.

## Measurement Lessons

- The coupled bounded surface-stress and mass-neutral log-pressure proxy produced a large improvement across the fixed WeatherBench2 score without changing the forecast contract.
- The largest RMSE regressions were small late-lead 2 m temperature regressions: `+0.8994582411539229%` on iteration and `+0.7402305337001447%` on validation, both well below the `10%` guardrail.
- Day-1-through-day-5 mean RMSE improved for all four target variables on both iteration and validation.

## Anomalies

- Cache reuse: incumbent iteration and validation metrics were reused from `.logbook/leaderboard.json` artifacts. They were readable, finite, clean, and compatible with the fixed protocol; no incumbent rerun was performed.
- Resource limits: none encountered. Candidate iteration used 4 GPU workers over 229 chunks; validation used 4 GPU workers over 46 chunks.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by fast, iteration, or validation diagnostics.

## Recommendation To Orchestrator

Accept `dino_ri2m_ekman_coupled` as the new incumbent. The candidate passed tests, fast, iteration, validation, diagnostics, and RMSE guardrails while improving substantially over the cached incumbent.
