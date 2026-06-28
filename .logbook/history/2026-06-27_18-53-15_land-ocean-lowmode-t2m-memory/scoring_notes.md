# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate primary score `-0.21873176048319332`; diagnostics `failed=false`, issue count `0`.
- Iteration promotion gate: passed. Candidate `-0.21638012219181893` versus cached incumbent `-0.2197104515448394`, delta `+0.003330329353020467`; required delta was `+0.002`. Candidate diagnostics were clean. Worst candidate-row variable-lead RMSE regression was `5.00510088952133e-6`, far below the `10%` guardrail. All day-1-through-day-5 mean RMSE regressions were far below `2%`.
- Validation acceptance gate: passed. Candidate `-0.21606470816567627` versus cached incumbent `-0.21940899263836755`, delta `+0.003344284472691278`; required delta was `+0.001`. Candidate diagnostics were clean. Worst candidate-row variable-lead RMSE regression was `8.760358627402098e-7`. All day-1-through-day-5 mean RMSE regressions were far below `2%`.

## Measurement Lessons

- The broad land/ocean low-mode T2m residual reservoir improved aggregate skill while leaving non-T2m guardrails effectively neutral. This supports additional proposals that target the weakest screen-temperature residual components without altering the forecast contract.
- Guardrail pairing must filter records by `model_name`; evaluation outputs also include input-aware persistence records with duplicate variable/lead keys.

## Anomalies

- Cache reuse: incumbent `iteration` and `validation` metrics were reused from the leaderboard artifacts. No incumbent rerun was performed.
- Resource limits: none. Validation used `--workers 4` on 4 L4 GPUs with sufficient memory.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none; diagnostics reported no issues.

## Recommendation To Orchestrator

Measured gates support acceptance. Update the leaderboard to `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`, retain the source changes, and begin the next iteration from this accepted incumbent.
