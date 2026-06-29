# Scoring Notes

## Gate Status

- Fast gate: passed for `dino_ri2m_ekman_veered_10m` with clean diagnostics and primary score `-0.16790802095995314`.
- Iteration promotion gate: failed. Candidate primary score `-0.16517847120559984` was below cached incumbent score `-0.16500618979404214` by `-0.00017228141155770094`; the gate requires at least `+0.002`.
- Iteration diagnostics: clean. Candidate diagnostics reported `failed=False` with `0` issues.
- Iteration RMSE guardrails: clean. The largest day-1-through-day-5 mean RMSE regression was `+0.17816532076095485%` for `10m_u_component_of_wind`, below the `2%` limit. The largest single-lead RMSE regression was `+0.6395679979946111%` for `10m_u_component_of_wind` at `24` hours, below the `10%` limit.
- Validation acceptance gate: not evaluated. Validation was skipped because the iteration promotion gate did not pass.

## Measurement Lessons

- The output-only stability-veered 10 m wind diagnostic produced a small primary-score regression on iteration despite clean diagnostics and clean RMSE guardrails.
- The measurable RMSE impact was localized to 10 m zonal wind: early-lead mean RMSE regressed by `+0.17816532076095485%`, while the other three target variables were effectively unchanged or fractionally improved.
- The candidate did not show instability, nonfinite metrics, or broad-field degradation; its failure was the fixed primary-score promotion threshold.

## Anomalies

- Cache reuse: incumbent iteration metrics were reused from `.logbook/leaderboard.json` artifact `outputs/eval/iteration_dino_ri2m_ekman_coupled.json` with CSV `outputs/eval/iteration_dino_ri2m_ekman_coupled.csv`. The cache was readable, finite, clean, complete for the fixed target variables and lead range, and compatible with the fixed WeatherBench2 protocol. No incumbent rerun was performed.
- Validation cache: `outputs/eval/validation_dino_ri2m_ekman_coupled.json` and CSV were present and prechecked, but validation comparison was skipped because the candidate did not promote from iteration.
- Resource limits: none encountered. Iteration used 4 requested and 4 effective GPU workers over 229 chunks.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.

## Recommendation To Orchestrator

No accept/reject decision is made here. Measurements only: tests passed, fast passed, iteration completed cleanly, iteration primary score did not beat the cached incumbent, and validation was skipped under the fixed protocol.
