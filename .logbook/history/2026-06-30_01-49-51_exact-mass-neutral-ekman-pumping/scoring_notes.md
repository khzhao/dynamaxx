# Scoring Notes: exact-mass-neutral-ekman-pumping

## Gate Status

- Fast gate: passed by Implementer evidence and Scorer artifact verification. `outputs/eval/fast_dino_ri2m_ekman_massfix.json` has primary score `-0.1677264538865545`, `diagnostics.failed=false`, zero issues, and 120 records.
- Iteration promotion gate: failed. `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_massfix --workers 4` exited 0 and wrote clean diagnostics, but candidate primary score `-0.1650176080797289` was below cached incumbent iteration primary score `-0.16500618979404214`. The primary delta was `-0.000011418285686765062`, below the required `+0.002`.
- Validation acceptance gate: not run and not eligible. Validation is allowed only after iteration promotion; this candidate did not promote.

## Guardrails

- Candidate iteration diagnostics: `failed=false`, issue count `0`.
- Mean RMSE guardrail over leads 1-5 days: no failures. The largest mean early-lead regression was `2.1217290544558693e-8%` for 2 m temperature, far below the 2% limit.
- Variable/lead RMSE guardrail: no failures. The largest single variable-lead RMSE regression was `2.9305446061314134e-7%` for 500 hPa geopotential at 264 hours, far below the 10% limit.
- The failed gate is solely the primary-score threshold, not diagnostics or RMSE guardrails.

## Measurement Lessons

- The exact-mass-neutral correction is essentially neutral relative to the coupled Ekman incumbent at iteration scale. RMSE differences are near numerical roundoff, while the aggregate primary score moves slightly negative.
- Future mass-neutral Ekman variants should include a mechanism that changes the forecast skill materially, not only an exact neutrality correction that preserves the incumbent trajectory to roundoff.
- The cached incumbent comparison path remains valid even with candidate source edits present; accepted incumbent artifacts should continue to be reused unless fixed eval code, target variables, lead ranges, data path, or artifact integrity actually changes.

## Anomalies

- Cache reuse: incumbent iteration metrics were reused from `.logbook/leaderboard.json`; no incumbent reruns were performed. Iteration cache path was `outputs/eval/iteration_dino_ri2m_ekman_coupled.json` with primary score `-0.16500618979404214`.
- Validation cache: `outputs/eval/validation_dino_ri2m_ekman_coupled.json` was verified as available, finite, clean, and compatible, with primary score `-0.16591150807771451`, but it was not used for a candidate comparison because validation was skipped.
- Cache validation checks: requested incumbent matched leaderboard incumbent `dino_ri2m_ekman_coupled`; cached JSON/CSV files existed; cached JSON files were readable; primary scores were finite; diagnostics were clean; records contained incumbent model rows and guardrail fields; leaderboard fingerprint covered `iteration` and `validation`, target variables, lead days `1..15`, and the expected data path. Commits after leaderboard eval commit `d187308d30a242bf38aabe5b7eb530fca522a68f` were logbook/research metadata, not source or fixed evaluation code changes.
- Resource limits: worker count `4` was used exactly as requested. The candidate iteration run dispatched 4 effective GPU workers across 4 GPUs and completed 229 chunks.
- Failed or restarted commands: no Scorer-started command failed or was restarted.
- Nonfinite or unstable outputs: none observed in verified candidate fast or candidate iteration artifacts.
- Skipped commands: no golden run; no incumbent evaluations; no candidate validation.
- Unrelated untracked `gifs/` files were left untouched.

## Recommendation To Orchestrator

Report the measured gate status as iteration subthreshold. The candidate has clean diagnostics and no RMSE guardrail failures, but it does not qualify for validation because its iteration primary score did not improve over the cached incumbent by the required margin.
