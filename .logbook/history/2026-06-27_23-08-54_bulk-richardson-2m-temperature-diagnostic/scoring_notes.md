# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate primary score `-0.21716702092934806`; diagnostics `failed=false`, issue count `0`.
- Iteration promotion gate: passed. Candidate `-0.21299732605547173` versus cached incumbent `-0.21638012219181893`, delta `+0.0033827961363472048`; required delta was `+0.002`. Candidate diagnostics were clean. Worst candidate-row variable-lead RMSE regression was `0.00008104044154544354`, far below the `10%` guardrail. All day-1-through-day-5 mean RMSE regressions were far below `2%`.
- Validation acceptance gate: passed. Candidate `-0.21274255459898536` versus cached incumbent `-0.21606470816567627`, delta `+0.0033221535666909108`; required delta was `+0.001`. Candidate diagnostics were clean. Worst candidate-row variable-lead RMSE regression was `0.0002992156303169846`. All day-1-through-day-5 mean RMSE regressions were far below `2%`.

## Measurement Lessons

- A bounded raw 2 m temperature surface-layer diagnostic improves the dominant T2m weakness while leaving other target variables effectively neutral.
- Cache reuse worked as intended: the accepted incumbent artifacts were sufficient for primary-score and guardrail comparisons, so no incumbent rerun was needed.

## Anomalies

- Cache reuse: incumbent `iteration` and `validation` metrics were reused from the leaderboard artifacts.
- Resource limits: none. Iteration and validation used `--workers 4` on four L4 GPUs with sufficient memory.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none; diagnostics reported no issues.

## Recommendation To Orchestrator

Measured gates support acceptance. Update the leaderboard to `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`, retain the source changes, and begin the next iteration from this accepted incumbent.
