# Scoring Notes: skew-adjoint-vertical-momentum-advection

## Gate Status

- Fast gate: failed. `outputs/eval/fast_dino_ri2m_skewvadv.json` has primary score `-1.7976931348623157e+308`, `diagnostics.failed=true`, and two issues: `nonfinite_forecast` and `nonfinite_metric`.
- Iteration promotion gate: not run and not eligible. The candidate failed the fast diagnostic gate, so `uv run dynamaxx-eval iteration --model dino_ri2m_skewvadv --workers 4` was not run.
- Validation acceptance gate: not run and not eligible. Validation is allowed only after iteration promotion; candidate iteration was gated off by the fast failure.

## Measurement Lessons

- The skew-adjoint vertical momentum advection candidate is numerically unstable under the fixed fast protocol: the forecast contains nonfinite values and every candidate fast metric row is nonfinite-derived.
- Future vertical-advection proposals should include a stronger boundedness or damping argument before full implementation, because this failure appears before any iteration-scale comparison can be made.
- The cached incumbent comparison path remains valid even when candidate source edits are present; accepted incumbent artifacts should continue to be reused unless fixed eval code, target variables, lead ranges, data path, or artifact integrity actually changes.

## Anomalies

- Cache reuse: incumbent iteration and validation metrics were reused from `.logbook/leaderboard.json`; no incumbent reruns were performed. Iteration cache path was `outputs/eval/iteration_dino_ri2m_ekman_coupled.json` with primary score `-0.16500618979404214`. Validation cache path was `outputs/eval/validation_dino_ri2m_ekman_coupled.json` with primary score `-0.16591150807771451`.
- Cache validation checks: requested incumbent matched leaderboard incumbent `dino_ri2m_ekman_coupled`; cached JSON/CSV files existed; cached JSON files were readable; primary scores were finite; diagnostics were clean; records contained the incumbent model rows and finite RMSE/MAE/bias/skill values; leaderboard fingerprint covered `iteration` and `validation`, target variables, lead days `1..15`, and the expected data path.
- Resource limits: no new long evaluation was started during scoring. Worker count `4` was therefore not used.
- Failed or restarted commands: no scorer-started evaluation commands failed or were restarted. The Implementer-provided fast command exited 0 but produced failed diagnostics.
- Nonfinite or unstable outputs: candidate fast diagnostics reported `nonfinite_forecast` with value `400752000` and `nonfinite_metric` with value `240`; the candidate fast CSV contains `nan` metrics.
- Skipped commands: no golden run; no incumbent evaluations; no candidate iteration; no candidate validation.
- Unrelated untracked `gifs/` files were left untouched.

## Recommendation To Orchestrator

Report the measured gate status as fast failed. The candidate has no valid iteration or validation comparison because protocol gating stopped after the fast diagnostic failure.
