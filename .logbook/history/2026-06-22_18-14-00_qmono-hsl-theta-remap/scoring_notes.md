# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_hsl_qmono`
  completed with `failed=False`, zero diagnostic issues, 120 records, and
  primary score `-0.38682576342658237`.
- Iteration promotion gate: failed. `uv run dynamaxx-eval iteration --model
  dino_hsl_qmono --workers 4` completed with clean diagnostics, but the
  candidate primary score was `-0.3714466304069767` versus cached incumbent
  `dino_hsl2_theta` score `-0.31282890543336245`, for delta
  `-0.05861772497361423`.
- Validation acceptance gate: not run. The candidate did not meet the
  `+0.002` iteration promotion threshold, so validation was correctly skipped.

## Measurement Lessons

- The bounded qmono theta remap did not improve the fixed iteration primary
  score. The regression is large enough that validation would only tune against
  held-out data, so the experiment should stop at iteration.
- Early lead guardrails also moved in the wrong direction. Mean RMSE over days
  1 to 5 regressed by `+4.741512494129507%` for 10 m zonal wind,
  `+4.456966573542065%` for 2 m temperature, `+2.4595069761556232%` for mean
  sea-level pressure, and `+2.1874468341543718%` for 500 hPa geopotential.
- The worst variable-lead RMSE regression was `+8.41085767071934%` for mean
  sea-level pressure at lead hour 360. This remains under the fixed 10% worst
  variable-lead guardrail but does not offset the failed primary-score and
  early-lead gates.
- The qmono remap was materially more expensive than the incumbent path. The
  fixed iteration run completed 229 chunks in about 3 hours 12 minutes, with
  all four GPU workers active for most of the run.

## Anomalies

- Cache reuse: incumbent iteration metrics were reused from
  `outputs/eval/iteration_dino_hsl2_theta.json` and
  `outputs/eval/iteration_dino_hsl2_theta.csv`. The leaderboard incumbent
  matched the requested incumbent, the artifacts were readable, primary score
  was finite, diagnostics were clean, and comparable model rows existed for all
  fixed target variables and leads. No incumbent rerun was performed.
- Resource limits: none exceeded. The run used 4 workers on 4 visible L4 GPUs,
  with memory and disk remaining inside protocol limits.
- Failed or restarted commands: none. The Scorer subagent stalled after
  candidate iteration completed, so the Orchestrator closed it and wrote these
  scoring artifacts from the completed fixed evaluation outputs.
- Nonfinite or unstable outputs: none observed. Fast and iteration diagnostics
  were clean.

## Recommendation To Orchestrator

Reject `dino_hsl_qmono`. The candidate passed fast diagnostics but failed the
iteration promotion gate with delta `-0.05861772497361423`, and validation was
not run.
